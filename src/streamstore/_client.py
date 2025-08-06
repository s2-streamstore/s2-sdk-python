import asyncio
import re
import uuid
from collections import deque
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import timedelta
from typing import Self, cast

from anyio import create_memory_object_stream, create_task_group
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from google.protobuf.field_mask_pb2 import FieldMask
from grpc import StatusCode, ssl_channel_credentials, Compression
from grpc.aio import AioRpcError, Channel, secure_channel

from streamstore import schemas
from streamstore._exceptions import fallible
from streamstore._lib.s2.v1alpha.s2_pb2 import (
    AppendRequest,
    AppendSessionRequest,
    BasinConfig,
    CheckTailRequest,
    CreateBasinRequest,
    CreateStreamRequest,
    DeleteBasinRequest,
    DeleteStreamRequest,
    GetBasinConfigRequest,
    GetStreamConfigRequest,
    ListBasinsRequest,
    ListStreamsRequest,
    ReadRequest,
    ReadSessionRequest,
    ReconfigureBasinRequest,
    ReconfigureStreamRequest,
    StreamConfig,
)
from streamstore._lib.s2.v1alpha.s2_pb2_grpc import (
    AccountServiceStub,
    BasinServiceStub,
    StreamServiceStub,
)
from streamstore._mappers import (
    append_input_message,
    append_output_schema,
    basin_config_message,
    basin_config_schema,
    basin_info_schema,
    read_limit_message,
    sequenced_records_schema,
    stream_config_message,
    stream_config_schema,
    stream_info_schema,
)
from streamstore._retrier import Attempt, Retrier, compute_backoffs
from streamstore.utils import metered_bytes

_BASIN_NAME_REGEX = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_MEMORY_STREAM_MAX_BUF_SIZE = 100


def _grpc_retry_on(e: Exception) -> bool:
    if isinstance(e, AioRpcError) and e.code() in (
        StatusCode.DEADLINE_EXCEEDED,
        StatusCode.UNAVAILABLE,
        StatusCode.UNKNOWN,
    ):
        return True
    return False


def _validate_basin(name: str) -> None:
    if (
        isinstance(name, str)
        and (8 <= len(name) <= 48)
        and _BASIN_NAME_REGEX.match(name)
    ):
        return
    raise ValueError(f"Invalid basin name: {name}")


def _s2_request_token() -> str:
    return uuid.uuid4().hex


def _validate_append_input(input: schemas.AppendInput) -> None:
    num_bytes = metered_bytes(input.records)
    num_records = len(input.records)
    if 1 <= num_records <= 1000 and num_bytes <= schemas.ONE_MIB:
        return
    raise ValueError(
        f"Invalid append input: num_records={num_records}, metered_bytes={num_bytes}"
    )


async def _pipe_append_inputs(
    inputs: AsyncIterable[schemas.AppendInput],
    input_tx: MemoryObjectSendStream[schemas.AppendInput],
):
    async with input_tx:
        async for input in inputs:
            _validate_append_input(input)
            await input_tx.send(input)


async def _append_session_request_aiter(
    stream: str,
    inputs: AsyncIterable[schemas.AppendInput],
) -> AsyncIterable[AppendSessionRequest]:
    async for input in inputs:
        _validate_append_input(input)
        yield AppendSessionRequest(input=append_input_message(stream, input))


def _prepare_read_session_request_for_retry(
    request: ReadSessionRequest, last_read_batch: list[schemas.SequencedRecord]
) -> None:
    if len(last_read_batch) > 0:
        request.start_seq_num = last_read_batch[-1].seq_num + 1
        if request.limit.count is not None and request.limit.count != 0:
            request.limit.count = max(request.limit.count - len(last_read_batch), 0)
        if request.limit.bytes is not None and request.limit.bytes != 0:
            request.limit.bytes = max(
                request.limit.bytes - metered_bytes(last_read_batch),
                0,
            )


@dataclass(slots=True)
class _RpcConfig:
    timeout: float
    metadata: list[tuple[str, str]]
    compression: Compression


@dataclass(slots=True)
class _Config:
    max_retries: int
    enable_append_retries: bool
    rpc: _RpcConfig


class S2:
    """
    Async client for interacting with `s2.dev <https://s2.dev/>`_.

    Args:
        auth_token: Authentication token generated from `S2 dashboard <https://s2.dev/dashboard>`_.
        endpoints: S2 endpoints. If None, public endpoints for S2 service running in AWS cloud will be used.
        request_timeout: Timeout for requests made by the client. Default value is 5 seconds.
        max_retries: Maximum number of retries for a request. Default value is 3.
        enable_append_retries: Enable retries for appends i.e for both :meth:`.Stream.append` and
            :meth:`.Stream.append_session`. Default value is True.
        enable_compression: Enable compression (Gzip) for :meth:`.Stream.append`, :meth:`.Stream.append_session`,
            :meth:`.Stream.read`, and :meth:`.Stream.read_session`. Default value is False.
    """

    __slots__ = (
        "_endpoints",
        "_account_channel",
        "_basin_channels",
        "_config",
        "_stub",
        "_retrier",
    )

    @fallible
    def __init__(
        self,
        auth_token: str,
        endpoints: schemas.Endpoints | None = None,
        request_timeout: timedelta = timedelta(seconds=5.0),
        max_retries: int = 3,
        enable_append_retries: bool = True,
        enable_compression: bool = False,
    ) -> None:
        self._endpoints = (
            endpoints
            if endpoints is not None
            else schemas.Endpoints.for_cloud(schemas.Cloud.AWS)
        )
        self._account_channel = secure_channel(
            target=self._endpoints._account(),
            credentials=ssl_channel_credentials(),
        )
        self._basin_channels: dict[str, Channel] = {}
        self._config = _Config(
            max_retries=max_retries,
            enable_append_retries=enable_append_retries,
            rpc=_RpcConfig(
                timeout=request_timeout.total_seconds(),
                metadata=[("authorization", f"Bearer {auth_token}")],
                compression=Compression.Gzip
                if enable_compression
                else Compression.NoCompression,
            ),
        )
        self._stub = AccountServiceStub(self._account_channel)
        self._retrier = Retrier(
            should_retry_on=_grpc_retry_on,
            max_attempts=max_retries,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        await self.close()
        if exc_type is None and exc_value is None and traceback is None:
            return True
        return False

    def __getitem__(self, name: str) -> "Basin":
        return self.basin(name)

    async def close(self) -> None:
        """
        Close all open connections to S2 service endpoints.

        Tip:
            ``S2`` supports async context manager protocol, so you can also do the following instead of
            explicitly closing:

            .. code-block:: python

                async with S2(..) as s2:
                    ..

        """

        await self._account_channel.close(None)
        for basin_channel in self._basin_channels.values():
            await basin_channel.close(None)

    @fallible
    async def create_basin(
        self,
        name: str,
        default_stream_storage_class: schemas.StorageClass | None = None,
        default_stream_retention_age: timedelta | None = None,
        create_stream_on_append: bool = False,
    ) -> schemas.BasinInfo:
        """
        Create a basin.

        Args:
            name: Name of the basin.
            default_stream_storage_class: Default storage class for streams of this basin.
            default_stream_retention_age: Default threshold for automatic trimming of records in the
                streams of this basin. If not specified, streams will have infinite retention.
            create_stream_on_append: Create stream on append if it doesn't exist.

        Note:
            **name** must be globally unique and must be between 8 and 48 characters, comprising lowercase
            letters, numbers and hyphens. It cannot begin or end with a hyphen.
        """
        _validate_basin(name)
        request = CreateBasinRequest(
            basin=name,
            config=cast(
                BasinConfig,
                basin_config_message(
                    default_stream_storage_class,
                    default_stream_retention_age,
                    create_stream_on_append,
                ),
            ),
        )
        metadata = self._config.rpc.metadata + [
            ("s2-request-token", _s2_request_token())
        ]
        response = await self._retrier(
            self._stub.CreateBasin,
            request,
            timeout=self._config.rpc.timeout,
            metadata=metadata,
        )
        return basin_info_schema(response.info)

    def basin(self, name: str) -> "Basin":
        """
        Get a Basin object that can be used for performing basin operations.

        Args:
            name: Name of the basin.

        Note:
            The basin must have been created already, else the operations will fail.

        Tip:
            .. code-block:: python

                async with S2(..) as s2:
                    basin = s2.basin("your-basin-name")

            :class:`.S2` implements the ``getitem`` magic method, so you can also do the following instead:

            .. code-block:: python

                async with S2(..) as s2:
                    basin = s2["your-basin-name"]
        """
        _validate_basin(name)
        if name not in self._basin_channels:
            self._basin_channels[name] = secure_channel(
                target=self._endpoints._basin(name),
                credentials=ssl_channel_credentials(),
            )
        return Basin(name, self._basin_channels[name], self._config)

    @fallible
    async def list_basins(
        self,
        prefix: str = "",
        start_after: str = "",
        limit: int | None = None,
    ) -> schemas.Page[schemas.BasinInfo]:
        """
        List basins.

        Args:
            prefix: List only those that begin with this value.
            start_after: List only those that lexicographically start after this value,
                which can be the name of the last item from previous page, to continue from there.
                It must be greater than or equal to the prefix if specified.
            limit: Number of items to return in one page. Maximum number of items that can be
                returned in one page is 1000.
        """
        request = ListBasinsRequest(prefix=prefix, start_after=start_after, limit=limit)
        response = await self._retrier(
            self._stub.ListBasins,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return schemas.Page(
            items=[basin_info_schema(b) for b in response.basins],
            has_more=response.has_more,
        )

    @fallible
    async def delete_basin(self, name: str) -> None:
        """
        Delete a basin.

        Args:
            name: Name of the basin.

        Note:
            Basin deletion is asynchronous, and may take a few minutes to complete.
        """
        request = DeleteBasinRequest(basin=name)
        await self._retrier(
            self._stub.DeleteBasin,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )

    @fallible
    async def get_basin_config(self, name: str) -> schemas.BasinConfig:
        """
        Get the current configuration of a basin.

        Args:
            name: Name of the basin.
        """
        request = GetBasinConfigRequest(basin=name)
        response = await self._retrier(
            self._stub.GetBasinConfig,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return basin_config_schema(response.config)

    @fallible
    async def reconfigure_basin(
        self,
        name: str,
        default_stream_storage_class: schemas.StorageClass | None = None,
        default_stream_retention_age: timedelta | None = None,
        create_stream_on_append: bool = False,
    ) -> schemas.BasinConfig:
        """
        Modify the configuration of a basin.

        Args:
            name: Name of the basin.
            default_stream_storage_class: Default storage class for streams of this basin.
            default_stream_retention_age: Default threshold for automatic trimming of records in the
                streams of this basin. If not specified, streams will have infinite retention.
            create_stream_on_append: Create stream on append if it doesn't exist.

        Note:
            Modifiying the default stream-related configuration doesn't affect already existing streams;
            it only applies to new streams created hereafter.
        """
        basin_config, mask = cast(
            tuple[BasinConfig, FieldMask],
            basin_config_message(
                default_stream_storage_class,
                default_stream_retention_age,
                create_stream_on_append,
                return_mask=True,
            ),
        )
        request = ReconfigureBasinRequest(basin=name, config=basin_config, mask=mask)
        response = await self._retrier(
            self._stub.ReconfigureBasin,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return basin_config_schema(response.config)


class Basin:
    """
    Caution:
        Returned by :meth:`.S2.basin`. Do not instantiate directly.
    """

    __slots__ = (
        "_channel",
        "_config",
        "_retrier",
        "_stub",
        "_name",
    )

    @fallible
    def __init__(
        self,
        name: str,
        channel: Channel,
        config: _Config,
    ) -> None:
        self._channel = channel
        self._config = config
        self._retrier = Retrier(
            should_retry_on=_grpc_retry_on,
            max_attempts=config.max_retries,
        )
        self._stub = BasinServiceStub(self._channel)
        self._name = name

    def __repr__(self) -> str:
        return f"Basin(name={self.name})"

    def __getitem__(self, name: str) -> "Stream":
        return self.stream(name)

    @property
    def name(self) -> str:
        """Basin name."""
        return self._name

    @fallible
    async def create_stream(
        self,
        name: str,
        storage_class: schemas.StorageClass | None = None,
        retention_age: timedelta | None = None,
    ) -> schemas.StreamInfo:
        """
        Create a stream.

        Args:
            name: Name of the stream.
            storage_class: Storage class for this stream.
            retention_age: Thresold for automatic trimming of records in this stream. If not specified,
                the stream will have infinite retention.

        Note:
            **name** must be unique within the basin. It can be an arbitrary string upto 512 characters.
            Backslash (`/`) is recommended as a delimiter for hierarchical naming.
        """
        request = CreateStreamRequest(
            stream=name,
            config=cast(
                StreamConfig, stream_config_message(storage_class, retention_age)
            ),
        )
        metadata = self._config.rpc.metadata + [
            ("s2-request-token", _s2_request_token())
        ]
        response = await self._retrier(
            self._stub.CreateStream,
            request,
            timeout=self._config.rpc.timeout,
            metadata=metadata,
        )
        return stream_info_schema(response.info)

    def stream(self, name: str) -> "Stream":
        """
        Get a Stream object that can be used for performing stream operations.

        Args:
            name: Name of the stream.

        Note:
            The stream must have been created already, else the operations will fail.

        Tip:
            .. code-block:: python

                async with S2(..) as s2:
                    stream = s2.basin("your-basin-name").stream("your-stream-name")

            :class:`.Basin` implements the ``getitem`` magic method, so you can also do the following instead:

            .. code-block:: python

                async with S2(..) as s2:
                    stream = s2["your-basin-name"]["your-stream-name"]

        """
        return Stream(name, self._channel, self._config)

    @fallible
    async def list_streams(
        self,
        prefix: str = "",
        start_after: str = "",
        limit: int | None = None,
    ) -> schemas.Page[schemas.StreamInfo]:
        """
        List streams.

        Args:
            prefix: List only those that begin with this value.
            start_after: List only those that lexicographically start after this value,
                which can be the name of the last item from previous page, to continue from there.
                It must be greater than or equal to the prefix if specified.
            limit: Number of items to return in one page. Maximum number of items that can be
                returned in one page is 1000.
        """
        request = ListStreamsRequest(
            prefix=prefix, start_after=start_after, limit=limit
        )
        response = await self._retrier(
            self._stub.ListStreams,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return schemas.Page(
            items=[stream_info_schema(s) for s in response.streams],
            has_more=response.has_more,
        )

    @fallible
    async def delete_stream(self, name: str) -> None:
        """
        Delete a stream.

        Args:
            name: Name of the stream.

        Note:
            Stream deletion is asynchronous, and may take a few minutes to complete.
        """
        request = DeleteStreamRequest(stream=name)
        await self._retrier(
            self._stub.DeleteStream,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )

    @fallible
    async def get_stream_config(self, name: str) -> schemas.StreamConfig:
        """
        Get the current configuration of a stream.

        Args:
            name: Name of the stream.
        """
        request = GetStreamConfigRequest(stream=name)
        response = await self._retrier(
            self._stub.GetStreamConfig,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return stream_config_schema(response.config)

    @fallible
    async def reconfigure_stream(
        self,
        name: str,
        storage_class: schemas.StorageClass | None = None,
        retention_age: timedelta | None = None,
    ) -> schemas.StreamConfig:
        """
        Modify the configuration of a stream.

        Args:
            name: Name of the stream.
            storage_class: Storage class for this stream.
            retention_age: Thresold for automatic trimming of records in this stream. If not specified,
                the stream will have infinite retention.

        Note:
            Modifying **storage_class** will take effect only when this stream has been inactive for 10 minutes.
            This will become a live migration in future.
        """
        stream_config, mask = cast(
            tuple[StreamConfig, FieldMask],
            stream_config_message(storage_class, retention_age, return_mask=True),
        )
        request = ReconfigureStreamRequest(stream=name, config=stream_config, mask=mask)
        response = await self._retrier(
            self._stub.ReconfigureStream,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return stream_config_schema(response.config)


class Stream:
    """
    Caution:
        Returned by :meth:`.Basin.stream`. Do not instantiate directly.
    """

    __slots__ = (
        "_name",
        "_config",
        "_retrier",
        "_stub",
    )

    def __init__(self, name: str, channel: Channel, config: _Config) -> None:
        self._name = name
        self._config = config
        self._retrier = Retrier(
            should_retry_on=_grpc_retry_on,
            max_attempts=config.max_retries,
        )
        self._stub = StreamServiceStub(channel)

    def __repr__(self) -> str:
        return f"Stream(name={self.name})"

    @property
    def name(self) -> str:
        """Stream name."""
        return self._name

    @fallible
    async def check_tail(self) -> int:
        """
        Returns:
            Sequence number that will be assigned to the next record on a stream.
        """
        request = CheckTailRequest(stream=self.name)
        response = await self._retrier(
            self._stub.CheckTail,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return response.next_seq_num

    @fallible
    async def append(self, input: schemas.AppendInput) -> schemas.AppendOutput:
        """
        Append a batch of records to a stream.
        """
        _validate_append_input(input)
        request = AppendRequest(input=append_input_message(self.name, input))
        response = (
            await self._retrier(
                self._stub.Append,
                request,
                timeout=self._config.rpc.timeout,
                metadata=self._config.rpc.metadata,
                compression=self._config.rpc.compression,
            )
            if self._config.enable_append_retries
            else await self._stub.Append(
                request,
                timeout=self._config.rpc.timeout,
                metadata=self._config.rpc.metadata,
                compression=self._config.rpc.compression,
            )
        )
        return append_output_schema(response.output)

    async def _append_session(
        self,
        attempt: Attempt,
        inflight_inputs: deque[schemas.AppendInput],
        request_rx: MemoryObjectReceiveStream[AppendSessionRequest],
        output_tx: MemoryObjectSendStream[schemas.AppendOutput],
    ):
        async for response in self._stub.AppendSession(
            request_rx,
            metadata=self._config.rpc.metadata,
            compression=self._config.rpc.compression,
        ):
            if attempt.value > 0:
                attempt.value = 0
            output = response.output
            corresponding_input = inflight_inputs.popleft()
            num_records_sent = len(corresponding_input.records)
            num_records_ackd = output.end_seq_num - output.start_seq_num
            if num_records_sent == num_records_ackd:
                await output_tx.send(append_output_schema(response.output))
            else:
                raise RuntimeError(
                    "Number of records sent doesn't match the number of acknowledgements received"
                )

    async def _retrying_append_session_inner(
        self,
        input_rx: MemoryObjectReceiveStream[schemas.AppendInput],
        output_tx: MemoryObjectSendStream[schemas.AppendOutput],
    ):
        inflight_inputs: deque[schemas.AppendInput] = deque()
        max_attempts = self._config.max_retries
        backoffs = compute_backoffs(max_attempts)
        attempt = Attempt(value=0)
        async with output_tx:
            while True:
                request_tx, request_rx = create_memory_object_stream[
                    AppendSessionRequest
                ](max_buffer_size=_MEMORY_STREAM_MAX_BUF_SIZE)
                try:
                    async with create_task_group() as tg:
                        tg.start_soon(
                            self._append_session,
                            attempt,
                            inflight_inputs,
                            request_rx,
                            output_tx,
                        )
                        async with request_tx:
                            if len(inflight_inputs) > 0:
                                for input in list(inflight_inputs):
                                    await request_tx.send(
                                        AppendSessionRequest(
                                            input=append_input_message(self.name, input)
                                        )
                                    )
                            async for input in input_rx:
                                inflight_inputs.append(input)
                                await request_tx.send(
                                    AppendSessionRequest(
                                        input=append_input_message(self.name, input)
                                    )
                                )
                    return
                except* AioRpcError as eg:
                    if attempt.value < max_attempts and any(
                        _grpc_retry_on(e) for e in eg.exceptions
                    ):
                        await asyncio.sleep(backoffs[attempt.value])
                        attempt.value += 1
                    else:
                        raise eg

    async def _retrying_append_session(
        self,
        inputs: AsyncIterable[schemas.AppendInput],
    ) -> AsyncIterable[schemas.AppendOutput]:
        input_tx, input_rx = create_memory_object_stream[schemas.AppendInput](
            max_buffer_size=_MEMORY_STREAM_MAX_BUF_SIZE
        )
        output_tx, output_rx = create_memory_object_stream[schemas.AppendOutput](
            max_buffer_size=_MEMORY_STREAM_MAX_BUF_SIZE
        )
        async with create_task_group() as tg:
            tg.start_soon(
                self._retrying_append_session_inner,
                input_rx,
                output_tx,
            )
            tg.start_soon(_pipe_append_inputs, inputs, input_tx)
            async with output_rx:
                async for output in output_rx:
                    yield output

    @fallible
    async def append_session(
        self, inputs: AsyncIterable[schemas.AppendInput]
    ) -> AsyncIterable[schemas.AppendOutput]:
        """
        Append batches of records to a stream continuously, while guaranteeing pipelined inputs are
        processed in order.

        Tip:
            You can use :func:`.append_inputs_gen` for automatic batching of records instead of explicitly
            preparing and providing batches of records.

        Yields:
            :class:`.AppendOutput` for each corresponding :class:`.AppendInput`.

        Returns:
            If ``enable_append_retries=False`` in :class:`.S2`, and if processing any of the
            :class:`.AppendInput` fails.

            (or)

            If ``enable_append_retries=True`` in :class:`.S2`, and if retry budget gets exhausted after
            trying to recover from failures.
        """
        if self._config.enable_append_retries:
            async for output in self._retrying_append_session(inputs):
                yield output
        else:
            async for response in self._stub.AppendSession(
                _append_session_request_aiter(self.name, inputs),
                metadata=self._config.rpc.metadata,
                compression=self._config.rpc.compression,
            ):
                yield append_output_schema(response.output)

    @fallible
    async def read(
        self,
        start_seq_num: int,
        limit: schemas.ReadLimit | None = None,
        ignore_command_records: bool = False,
    ) -> list[schemas.SequencedRecord] | schemas.FirstSeqNum | schemas.NextSeqNum:
        """
        Read a batch of records from a stream.

        Args:
            start_seq_num: Starting sequence number (inclusive).
            limit: Number of records to return, up to a maximum of 1000 or 1MiB of :func:`.metered_bytes`.
            ignore_command_records: Filters out command records if present from the batch.

        Returns:
            Batch of sequenced records. It can be empty only if **limit** was provided,
            and the first record that could have been returned violated the limit.

            (or)

            Sequence number for the first record on this stream, if the provided
            **start_seq_num** was smaller.

            (or)

            Sequence number for the next record on this stream, if the provided
            **start_seq_num** was larger.
        """
        request = ReadRequest(
            stream=self.name,
            start_seq_num=start_seq_num,
            limit=read_limit_message(limit),
        )
        response = await self._retrier(
            self._stub.Read,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
            compression=self._config.rpc.compression,
        )
        output = response.output
        match output.WhichOneof("output"):
            case "batch":
                return sequenced_records_schema(output.batch, ignore_command_records)
            case "first_seq_num":
                return schemas.FirstSeqNum(output.first_seq_num)
            case "next_seq_num":
                return schemas.NextSeqNum(output.next_seq_num)
            case _:
                raise RuntimeError(
                    "Read output doesn't match any of the expected values"
                )

    @fallible
    async def read_session(
        self,
        start_seq_num: int,
        limit: schemas.ReadLimit | None = None,
        ignore_command_records: bool = False,
    ) -> AsyncIterable[
        list[schemas.SequencedRecord] | schemas.FirstSeqNum | schemas.NextSeqNum
    ]:
        """
        Read batches of records from a stream continuously.

        Args:
            start_seq_num: Starting sequence number (inclusive).
            limit: Number of records to return, up to a maximum of 1000 or 1MiB of :func:`.metered_bytes`.
            ignore_command_records: Filters out command records if present from the batch.

        Note:
            With a session, you are able to read in a streaming fashion. If a **limit** was not provided
            and the end of the stream is reached, the session goes into real-time tailing mode and
            will yield records as they are appended to the stream.

        Yields:
            Batch of sequenced records. It can be empty only if **limit** was provided,
            and the first record that could have been returned violated the limit.

            (or)

            Sequence number for the first record on this stream, if the provided
            **start_seq_num** was smaller.

            (or)

            Sequence number for the next record on this stream, if the provided
            **start_seq_num** was larger.

        Returns:
            If **limit** was provided, and if it was met or the end of the stream was reached
            before meeting it.

            (or)

            If previous yield was not a batch of sequenced records.
        """
        request = ReadSessionRequest(
            stream=self.name,
            start_seq_num=start_seq_num,
            limit=read_limit_message(limit),
        )
        max_attempts = self._config.max_retries
        backoffs = compute_backoffs(max_attempts)
        attempt = 0
        while True:
            try:
                async for response in self._stub.ReadSession(
                    request,
                    metadata=self._config.rpc.metadata,
                    compression=self._config.rpc.compression,
                ):
                    if attempt > 0:
                        attempt = 0
                    output = response.output
                    match output.WhichOneof("output"):
                        case "batch":
                            records = sequenced_records_schema(
                                output.batch, ignore_command_records
                            )
                            _prepare_read_session_request_for_retry(request, records)
                            yield records
                        case "first_seq_num":
                            yield schemas.FirstSeqNum(output.first_seq_num)
                            return
                        case "next_seq_num":
                            yield schemas.NextSeqNum(output.next_seq_num)
                            return
                        case _:
                            raise RuntimeError(
                                "Read output doesn't match any of the expected values"
                            )
            except Exception as e:
                if attempt < max_attempts and _grpc_retry_on(e):
                    await asyncio.sleep(backoffs[attempt])
                    attempt += 1
                else:
                    raise e
