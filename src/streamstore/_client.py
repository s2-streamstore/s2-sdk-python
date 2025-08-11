import asyncio
import re
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from typing import AsyncIterable, Self, cast

from anyio import create_memory_object_stream, create_task_group
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from google.protobuf.field_mask_pb2 import FieldMask
from grpc import Compression, StatusCode, ssl_channel_credentials
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
    IssueAccessTokenRequest,
    ListAccessTokensRequest,
    ListBasinsRequest,
    ListStreamsRequest,
    ReadSessionRequest,
    ReconfigureBasinRequest,
    ReconfigureStreamRequest,
    RevokeAccessTokenRequest,
    StreamConfig,
)
from streamstore._lib.s2.v1alpha.s2_pb2_grpc import (
    AccountServiceStub,
    BasinServiceStub,
    StreamServiceStub,
)
from streamstore._mappers import (
    access_token_info_message,
    access_token_info_schema,
    append_input_message,
    append_output_schema,
    basin_config_message,
    basin_config_schema,
    basin_info_schema,
    read_request_message,
    read_session_request_message,
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
        request.seq_num = last_read_batch[-1].seq_num + 1
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
        access_token: Access token generated from `S2 dashboard <https://s2.dev/dashboard>`_.
        endpoints: S2 endpoints. If not specified, public endpoints for S2 service running in AWS cloud will be used.
        request_timeout: Timeout for requests made by the client. Default value is ``5`` seconds.
        max_retries: Maximum number of retries for a request. Default value is ``3``.
        enable_append_retries: Enable retries for appends i.e for both :meth:`.Stream.append` and
            :meth:`.Stream.append_session`. Default value is ``True``.
        enable_compression: Enable compression (Gzip) for :meth:`.Stream.append`, :meth:`.Stream.append_session`,
            :meth:`.Stream.read`, and :meth:`.Stream.read_session`. Default value is ``False``.
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
        access_token: str,
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
                metadata=[("authorization", f"Bearer {access_token}")],
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
        config: schemas.BasinConfig | None = None,
    ) -> schemas.BasinInfo:
        """
        Create a basin.

        Args:
            name: Name of the basin.
            config: Configuration for the basin.

        Note:
            ``name`` must be globally unique and must be between 8 and 48 characters, comprising lowercase
            letters, numbers and hyphens. It cannot begin or end with a hyphen.
        """
        _validate_basin(name)
        request = CreateBasinRequest(
            basin=name,
            config=cast(
                BasinConfig,
                basin_config_message(config),
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
        limit: int = 1000,
    ) -> schemas.Page[schemas.BasinInfo]:
        """
        List basins.

        Args:
            prefix: Filter to basins whose name begins with this prefix.
            start_after: Filter to basins whose name starts lexicographically after this value.
            limit: Number of items to return per page, up to a maximum of 1000.
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
        config: schemas.BasinConfig,
    ) -> schemas.BasinConfig:
        """
        Modify the configuration of a basin.

        Args:
            name: Name of the basin.
            config: Configuration for the basin.

        Note:
            Modifiying the :attr:`.BasinConfig.default_stream_config` doesn't affect already
            existing streams; it only applies to new streams created hereafter.
        """
        basin_config, mask_paths = cast(
            tuple[BasinConfig, list[str]],
            basin_config_message(
                config,
                return_mask_paths=True,
            ),
        )
        request = ReconfigureBasinRequest(
            basin=name, config=basin_config, mask=FieldMask(paths=mask_paths)
        )
        response = await self._retrier(
            self._stub.ReconfigureBasin,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return basin_config_schema(response.config)

    @fallible
    async def issue_access_token(
        self,
        id: str,
        scope: schemas.AccessTokenScope,
        expires_at: int | None = None,
        auto_prefix_streams: bool = False,
    ) -> str:
        """
        Issue a new access token.

        Args:
            id: Access token ID.
            scope: Access token scope.
            expires_at: Expiration time in seconds since Unix epoch. If not specified, expiration
                time of ``access_token`` passed to :class:`.S2` will be used.
            auto_prefix_streams: Enable auto-prefixing: the specified prefix in
              :attr:`.AccessTokenScope.streams` will be added to stream names in requests and stripped
              from stream names in responses.

        Note:
            ``id`` must be unique to the account and between 1 and 96 bytes in length.
        """
        request = IssueAccessTokenRequest(
            info=access_token_info_message(id, scope, auto_prefix_streams, expires_at)
        )
        response = await self._retrier(
            self._stub.IssueAccessToken,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return response.access_token

    @fallible
    async def list_access_tokens(
        self, prefix: str = "", start_after: str = "", limit: int = 1000
    ) -> schemas.Page[schemas.AccessTokenInfo]:
        """
        List access tokens.

        Args:
            prefix: Filter to access tokens whose ID begins with this prefix.
            start_after: Filter to access tokens whose ID starts lexicographically after this value.
            limit: Number of items to return per page, up to a maximum of 1000.
        """
        request = ListAccessTokensRequest(
            prefix=prefix, start_after=start_after, limit=limit
        )
        response = await self._retrier(
            self._stub.ListAccessTokens,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return schemas.Page(
            items=[access_token_info_schema(info) for info in response.access_tokens],
            has_more=response.has_more,
        )

    @fallible
    async def revoke_access_token(self, id: str) -> schemas.AccessTokenInfo:
        """
        Revoke an access token.

        Args:
            id: Access token ID.
        """
        request = RevokeAccessTokenRequest(id=id)
        response = await self._retrier(
            self._stub.RevokeAccessToken,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return access_token_info_schema(response.info)


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
        config: schemas.StreamConfig | None = None,
    ) -> schemas.StreamInfo:
        """
        Create a stream.

        Args:
            name: Name of the stream.
            config: Configuration for the stream.

        Note:
            ``name`` must be unique within the basin. It can be an arbitrary string upto 512 characters.
            Backslash (``/``) is recommended as a delimiter for hierarchical naming.
        """
        request = CreateStreamRequest(
            stream=name,
            config=cast(
                StreamConfig,
                stream_config_message(config),
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
        limit: int = 1000,
    ) -> schemas.Page[schemas.StreamInfo]:
        """
        List streams.

        Args:
            prefix: Filter to streams whose name begins with this prefix.
            start_after: Filter to streams whose name starts lexicographically after this value.
            limit: Number of items to return per page, up to a maximum of 1000.
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
        config: schemas.StreamConfig,
    ) -> schemas.StreamConfig:
        """
        Modify the configuration of a stream.

        Args:
            name: Name of the stream.
            config: Configuration for the stream.

        Note:
            Modifying :attr:`.StreamConfig.storage_class` will take effect only when this stream has
            been inactive for 10 minutes. This will become a live migration in future.
        """
        stream_config, mask_paths = cast(
            tuple[StreamConfig, list[str]],
            stream_config_message(config, return_mask_paths=True),
        )
        request = ReconfigureStreamRequest(
            stream=name, config=stream_config, mask=FieldMask(paths=mask_paths)
        )
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
    async def check_tail(self) -> schemas.Tail:
        """
        Check the tail of a stream.
        """
        request = CheckTailRequest(stream=self.name)
        response = await self._retrier(
            self._stub.CheckTail,
            request,
            timeout=self._config.rpc.timeout,
            metadata=self._config.rpc.metadata,
        )
        return schemas.Tail(response.next_seq_num, response.last_timestamp)

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
        start: schemas.SeqNum | schemas.Timestamp | schemas.TailOffset,
        limit: schemas.ReadLimit | None = None,
        until: int | None = None,
        ignore_command_records: bool = False,
    ) -> list[schemas.SequencedRecord] | schemas.Tail:
        """
        Read a batch of records from a stream.

        Args:
            start: Inclusive start position.
            limit: Number of records to return, up to a maximum of 1000 or 1MiB of :func:`.metered_bytes`.
            until: Exclusive timestamp to read until. It is applied as an additional constraint on
              top of the ``limit`` and guarantees that all returned records have timestamps less
              than this timestamp.
            ignore_command_records: Filters out command records if present from the batch.

        Returns:
            Batch of sequenced records. It can be empty only if ``limit`` and/or ``until`` were provided
            and no records satisfy those constraints.

            (or)

            Tail of the stream. It will be returned only if ``start`` equals or exceeds the tail of
            the stream.
        """
        request = read_request_message(self.name, start, limit, until)
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
            case "next_seq_num":
                # TODO: use correct last_timestamp when migrating to v1 API.
                return schemas.Tail(output.next_seq_num, 0)
            case _:
                raise RuntimeError(
                    "Read output doesn't match any of the expected values"
                )

    @fallible
    async def read_session(
        self,
        start: schemas.SeqNum | schemas.Timestamp | schemas.TailOffset,
        limit: schemas.ReadLimit | None = None,
        until: int | None = None,
        clamp: bool = False,
        ignore_command_records: bool = False,
    ) -> AsyncIterable[list[schemas.SequencedRecord] | schemas.Tail]:
        """
        Read batches of records from a stream continuously.

        Args:
            start: Inclusive start position.
            limit: Number of records to return, up to a maximum of 1000 or 1MiB of :func:`.metered_bytes`.
            until: Exclusive timestamp to read until. It is applied as an additional constraint on
              top of the ``limit`` and guarantees that all returned records have timestamps less
              than this timestamp.
            clamp: Clamp the ``start`` position to the stream's tail when it exceeds the tail.
            ignore_command_records: Filters out command records if present from the batch.

        Note:
            With a session, you are able to read in a streaming fashion. If ``limit`` and/or ``until``
            were not provided and the tail of the stream is reached, the session goes into
            real-time tailing mode and will yield records as they are appended to the stream.

        Yields:
            Batch of sequenced records.

            (or)

            Tail of the stream. It will be yielded only if ``start`` exceeds the tail and ``clamp``
            was ``False``.

        Returns:
            If ``limit`` and/or ``until`` were provided, and if there are no further records that
            satisfy those constraints.

            (or)

            If the previous yield was the tail of the stream.
        """
        request = read_session_request_message(self.name, start, limit, until, clamp)
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
                        case "next_seq_num":
                            # TODO: use correct last_timestamp when migrating to v1 API.
                            yield schemas.Tail(output.next_seq_num, 0)
                            return
                        case _:
                            raise RuntimeError(
                                "Read output doesn't match any of the expected values"
                            )
                return
            except Exception as e:
                if attempt < max_attempts and _grpc_retry_on(e):
                    await asyncio.sleep(backoffs[attempt])
                    attempt += 1
                else:
                    raise e
