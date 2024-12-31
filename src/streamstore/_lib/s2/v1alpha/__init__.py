# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: protos/s2/v1alpha/s2.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AsyncIterable,
    AsyncIterator,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
)

import betterproto
import betterproto.lib.google.protobuf as betterproto_lib_google_protobuf
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase


if TYPE_CHECKING:
    import grpclib.server
    from betterproto.grpc.grpclib_client import MetadataLike
    from grpclib.metadata import Deadline


class StorageClass(betterproto.Enum):
    """Storage class for recent writes."""

    UNSPECIFIED = 0
    """
    Unspecified, which is currently overridden to `STORAGE_CLASS_EXPRESS`.
    """

    STANDARD = 1
    """Standard, which offers end-to-end latencies under 500 ms."""

    EXPRESS = 2
    """Express, which offers end-to-end latencies under 50 ms."""


class BasinState(betterproto.Enum):
    """Current state of the basin."""

    UNSPECIFIED = 0
    """Unspecified."""

    ACTIVE = 1
    """Basin is active."""

    CREATING = 2
    """Basin is being created."""

    DELETING = 3
    """Basin is being deleted."""


@dataclass(eq=False, repr=False)
class ListBasinsRequest(betterproto.Message):
    """List basins request."""

    prefix: str = betterproto.string_field(1)
    """List basin names that begin with this prefix."""

    start_after: str = betterproto.string_field(2)
    """
    Only return basins names that lexicographically start after this name.
     This can be the last basin name seen in a previous listing, to continue from there.
     It must be greater than or equal to the prefix if specified.
    """

    limit: Optional[int] = betterproto.uint64_field(3, optional=True)
    """Number of results, up to a maximum of 1000."""


@dataclass(eq=False, repr=False)
class ListBasinsResponse(betterproto.Message):
    """List basins response."""

    basins: List["BasinInfo"] = betterproto.message_field(1)
    """Matching basins."""

    has_more: bool = betterproto.bool_field(2)
    """
    If set, indicates there are more results that can be listed with `start_after`.
    """


@dataclass(eq=False, repr=False)
class CreateBasinRequest(betterproto.Message):
    """Create basin request."""

    basin: str = betterproto.string_field(1)
    """
    Basin name, which must be globally unique. It can be omitted to let the service assign a unique name.
     The name must be between 8 and 48 characters, comprising lowercase letters, numbers and hyphens.
     It cannot begin or end with a hyphen.
    """

    config: "BasinConfig" = betterproto.message_field(2)
    """Basin configuration."""

    scope: str = betterproto.string_field(3, group="assignment")
    """
    Basin scope. It should be formatted as "{cloud}:{region}", e.g. "aws:us-east-1".
    """

    cell: str = betterproto.string_field(4, group="assignment")
    """Explicit cell assignment, if it is owned by the account."""


@dataclass(eq=False, repr=False)
class CreateBasinResponse(betterproto.Message):
    """Create basin response."""

    info: "BasinInfo" = betterproto.message_field(1)
    """Information about the newly created basin."""


@dataclass(eq=False, repr=False)
class DeleteBasinRequest(betterproto.Message):
    """Delete basin request."""

    basin: str = betterproto.string_field(1)
    """Name of the basin to delete."""


@dataclass(eq=False, repr=False)
class DeleteBasinResponse(betterproto.Message):
    """Delete basin response."""

    pass


@dataclass(eq=False, repr=False)
class GetBasinConfigRequest(betterproto.Message):
    """Get basin configuration request."""

    basin: str = betterproto.string_field(1)
    """Basin name."""


@dataclass(eq=False, repr=False)
class GetBasinConfigResponse(betterproto.Message):
    """Get basin configuration response."""

    config: "BasinConfig" = betterproto.message_field(1)
    """Basin configuration."""


@dataclass(eq=False, repr=False)
class ReconfigureBasinRequest(betterproto.Message):
    """Reconfigure basin request."""

    basin: str = betterproto.string_field(1)
    """Basin name."""

    config: "BasinConfig" = betterproto.message_field(2)
    """Basin configuration."""

    mask: "betterproto_lib_google_protobuf.FieldMask" = betterproto.message_field(3)
    """
    Specifies the pieces of configuration being updated.
     See https://protobuf.dev/reference/protobuf/google.protobuf/#field-mask
    """


@dataclass(eq=False, repr=False)
class ReconfigureBasinResponse(betterproto.Message):
    """Reconfigure basin response."""

    config: "BasinConfig" = betterproto.message_field(1)
    """Basin configuration."""


@dataclass(eq=False, repr=False)
class StreamInfo(betterproto.Message):
    """Stream information."""

    name: str = betterproto.string_field(1)
    """Stream name."""

    created_at: int = betterproto.uint32_field(2)
    """Creation time in seconds since Unix epoch."""

    deleted_at: Optional[int] = betterproto.uint32_field(3, optional=True)
    """
    Deletion time in seconds since Unix epoch, if the stream is being deleted.
    """


@dataclass(eq=False, repr=False)
class ListStreamsRequest(betterproto.Message):
    """List streams request."""

    prefix: str = betterproto.string_field(1)
    """List stream names that begin with this prefix."""

    start_after: str = betterproto.string_field(2)
    """
    Only return stream names that lexicographically start after this name.
     This can be the last stream name seen in a previous listing, to continue from there.
     It must be greater than or equal to the prefix if specified.
    """

    limit: Optional[int] = betterproto.uint64_field(3, optional=True)
    """Number of results, up to a maximum of 1000."""


@dataclass(eq=False, repr=False)
class ListStreamsResponse(betterproto.Message):
    """List streams response."""

    streams: List["StreamInfo"] = betterproto.message_field(1)
    """Matching streams."""

    has_more: bool = betterproto.bool_field(2)
    """
    If set, indicates there are more results that can be listed with `start_after`.
    """


@dataclass(eq=False, repr=False)
class CreateStreamRequest(betterproto.Message):
    """Create stream request."""

    stream: str = betterproto.string_field(1)
    """
    Stream name, which must be unique within the basin.
     It can be an arbitrary string upto 512 characters.
     Backslash (`/`) is recommended as a delimiter for hierarchical naming.
    """

    config: "StreamConfig" = betterproto.message_field(2)
    """Configuration for the new stream."""


@dataclass(eq=False, repr=False)
class CreateStreamResponse(betterproto.Message):
    """Create stream response."""

    info: "StreamInfo" = betterproto.message_field(1)
    """Information about the newly created stream."""


@dataclass(eq=False, repr=False)
class DeleteStreamRequest(betterproto.Message):
    """Delete stream request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""


@dataclass(eq=False, repr=False)
class DeleteStreamResponse(betterproto.Message):
    """Delete stream response."""

    pass


@dataclass(eq=False, repr=False)
class GetStreamConfigRequest(betterproto.Message):
    """Get stream configuration request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""


@dataclass(eq=False, repr=False)
class GetStreamConfigResponse(betterproto.Message):
    """Get stream configuration response."""

    config: "StreamConfig" = betterproto.message_field(1)
    """Stream configuration."""


@dataclass(eq=False, repr=False)
class ReconfigureStreamRequest(betterproto.Message):
    """Reconfigure stream request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""

    config: "StreamConfig" = betterproto.message_field(2)
    """Stream configuration with updated values."""

    mask: "betterproto_lib_google_protobuf.FieldMask" = betterproto.message_field(3)
    """
    Specifies the pieces of configuration being updated.
     See https://protobuf.dev/reference/protobuf/google.protobuf/#field-mask
    """


@dataclass(eq=False, repr=False)
class ReconfigureStreamResponse(betterproto.Message):
    """Reconfigure stream response."""

    config: "StreamConfig" = betterproto.message_field(1)
    """Stream configuration."""


@dataclass(eq=False, repr=False)
class CheckTailRequest(betterproto.Message):
    """Check tail request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""


@dataclass(eq=False, repr=False)
class CheckTailResponse(betterproto.Message):
    """Check tail response."""

    next_seq_num: int = betterproto.uint64_field(1)
    """
    Sequence number that will be assigned to the next record on the stream.
    """


@dataclass(eq=False, repr=False)
class AppendInput(betterproto.Message):
    """Input for append requests."""

    stream: str = betterproto.string_field(1)
    """Stream name. Optional for subsequent requests in the session."""

    records: List["AppendRecord"] = betterproto.message_field(2)
    """
    Batch of records to append atomically, which must contain at least one record, and no more than 1000.
     The total size of a batch of records may not exceed 1MiB of metered bytes.
    """

    match_seq_num: Optional[int] = betterproto.uint64_field(3, optional=True)
    """Enforce that the sequence number issued to the first record matches."""

    fencing_token: Optional[bytes] = betterproto.bytes_field(4, optional=True)
    """
    Enforce a fencing token which must have been previously set by a `fence` command record.
    """


@dataclass(eq=False, repr=False)
class AppendOutput(betterproto.Message):
    """Output from append response."""

    start_seq_num: int = betterproto.uint64_field(1)
    """Sequence number of first record appended."""

    end_seq_num: int = betterproto.uint64_field(2)
    """
    Sequence number of last record appended + 1.
     `end_seq_num - start_seq_num` will be the number of records in the batch.
    """

    next_seq_num: int = betterproto.uint64_field(3)
    """
    Sequence number of last durable record on the stream + 1.
     This can be greater than `end_seq_num` in case of concurrent appends.
    """


@dataclass(eq=False, repr=False)
class AppendRequest(betterproto.Message):
    """Append request."""

    input: "AppendInput" = betterproto.message_field(1)
    """Request parameters for an append."""


@dataclass(eq=False, repr=False)
class AppendResponse(betterproto.Message):
    """Append response."""

    output: "AppendOutput" = betterproto.message_field(1)
    """Response details for an append."""


@dataclass(eq=False, repr=False)
class AppendSessionRequest(betterproto.Message):
    """Append session request."""

    input: "AppendInput" = betterproto.message_field(1)
    """Request parameters for an append."""


@dataclass(eq=False, repr=False)
class AppendSessionResponse(betterproto.Message):
    """Append session response."""

    output: "AppendOutput" = betterproto.message_field(1)
    """Response details for an append."""


@dataclass(eq=False, repr=False)
class ReadOutput(betterproto.Message):
    """Output from read response."""

    batch: "SequencedRecordBatch" = betterproto.message_field(1, group="output")
    """
    Batch of records.
     This batch can be empty only if a `ReadLimit` was provided in the associated read request, but the first record
     that could have been returned would violate the limit.
    """

    first_seq_num: int = betterproto.uint64_field(2, group="output")
    """
    Sequence number for the first record on this stream, in case the requested `start_seq_num` is smaller.
     If returned in a streaming read session, this will be a terminal reply, to signal that there is uncertainty about whether some records may be omitted.
     The client can re-establish the session starting at this sequence number.
    """

    next_seq_num: int = betterproto.uint64_field(3, group="output")
    """
    Sequence number for the next record on this stream, in case the requested `start_seq_num` was larger.
     If returned in a streaming read session, this will be a terminal reply.
    """


@dataclass(eq=False, repr=False)
class ReadRequest(betterproto.Message):
    """Read request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""

    start_seq_num: int = betterproto.uint64_field(2)
    """Starting sequence number (inclusive)."""

    limit: "ReadLimit" = betterproto.message_field(3)
    """
    Limit on how many records can be returned upto a maximum of 1000, or 1MiB of metered bytes.
    """


@dataclass(eq=False, repr=False)
class ReadResponse(betterproto.Message):
    """Read response."""

    output: "ReadOutput" = betterproto.message_field(1)
    """Response details for a read."""


@dataclass(eq=False, repr=False)
class ReadLimit(betterproto.Message):
    """If both count and bytes are specified, either limit may be hit."""

    count: Optional[int] = betterproto.uint64_field(1, optional=True)
    """Record count limit."""

    bytes: Optional[int] = betterproto.uint64_field(2, optional=True)
    """Metered bytes limit."""


@dataclass(eq=False, repr=False)
class ReadSessionRequest(betterproto.Message):
    """Read session request."""

    stream: str = betterproto.string_field(1)
    """Stream name."""

    start_seq_num: int = betterproto.uint64_field(2)
    """Starting sequence number (inclusive)."""

    limit: "ReadLimit" = betterproto.message_field(3)
    """
    Limit on how many records can be returned. When a limit is specified, the session will be terminated as soon as
     the limit is met, or when the current tail of the stream is reached -- whichever occurs first.
     If no limit is specified, the session will remain open after catching up to the tail, and continue tailing as
     new messages are written to the stream.
    """


@dataclass(eq=False, repr=False)
class ReadSessionResponse(betterproto.Message):
    """Read session response."""

    output: "ReadOutput" = betterproto.message_field(1)
    """Response details for a read."""


@dataclass(eq=False, repr=False)
class StreamConfig(betterproto.Message):
    """Stream configuration."""

    storage_class: "StorageClass" = betterproto.enum_field(1)
    """
    Storage class for recent writes. This is the main cost:performance knob in S2.
    """

    age: int = betterproto.uint64_field(2, group="retention_policy")
    """
    Age in seconds for automatic trimming of records older than this threshold.
     If set to 0, the stream will have infinite retention.
    """


@dataclass(eq=False, repr=False)
class BasinConfig(betterproto.Message):
    """Basin configuration."""

    default_stream_config: "StreamConfig" = betterproto.message_field(1)
    """Default stream configuration."""


@dataclass(eq=False, repr=False)
class BasinInfo(betterproto.Message):
    """Basin information."""

    name: str = betterproto.string_field(1)
    """Basin name."""

    scope: str = betterproto.string_field(2)
    """Basin scope."""

    cell: str = betterproto.string_field(3)
    """Cell assignment."""

    state: "BasinState" = betterproto.enum_field(4)
    """Basin state."""


@dataclass(eq=False, repr=False)
class Header(betterproto.Message):
    """Headers add structured information to a record as name-value pairs."""

    name: bytes = betterproto.bytes_field(1)
    """
    Header name blob.
     The name cannot be empty, with the exception of an S2 command record.
    """

    value: bytes = betterproto.bytes_field(2)
    """Header value blob."""


@dataclass(eq=False, repr=False)
class AppendRecord(betterproto.Message):
    """Record to be appended to a stream."""

    headers: List["Header"] = betterproto.message_field(1)
    """Series of name-value pairs for this record."""

    body: bytes = betterproto.bytes_field(2)
    """Body of this record."""


@dataclass(eq=False, repr=False)
class SequencedRecord(betterproto.Message):
    """Record retrieved from a stream."""

    seq_num: int = betterproto.uint64_field(1)
    """Sequence number for this record."""

    headers: List["Header"] = betterproto.message_field(2)
    """Series of name-value pairs for this record."""

    body: bytes = betterproto.bytes_field(3)
    """Body of this record."""


@dataclass(eq=False, repr=False)
class SequencedRecordBatch(betterproto.Message):
    """A batch of sequenced records."""

    records: List["SequencedRecord"] = betterproto.message_field(1)
    """Batch of sequenced records."""


class AccountServiceStub(betterproto.ServiceStub):
    async def list_basins(
        self,
        list_basins_request: "ListBasinsRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "ListBasinsResponse":
        return await self._unary_unary(
            "/s2.v1alpha.AccountService/ListBasins",
            list_basins_request,
            ListBasinsResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def create_basin(
        self,
        create_basin_request: "CreateBasinRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "CreateBasinResponse":
        return await self._unary_unary(
            "/s2.v1alpha.AccountService/CreateBasin",
            create_basin_request,
            CreateBasinResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def delete_basin(
        self,
        delete_basin_request: "DeleteBasinRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "DeleteBasinResponse":
        return await self._unary_unary(
            "/s2.v1alpha.AccountService/DeleteBasin",
            delete_basin_request,
            DeleteBasinResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def reconfigure_basin(
        self,
        reconfigure_basin_request: "ReconfigureBasinRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "ReconfigureBasinResponse":
        return await self._unary_unary(
            "/s2.v1alpha.AccountService/ReconfigureBasin",
            reconfigure_basin_request,
            ReconfigureBasinResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_basin_config(
        self,
        get_basin_config_request: "GetBasinConfigRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetBasinConfigResponse":
        return await self._unary_unary(
            "/s2.v1alpha.AccountService/GetBasinConfig",
            get_basin_config_request,
            GetBasinConfigResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )


class BasinServiceStub(betterproto.ServiceStub):
    async def list_streams(
        self,
        list_streams_request: "ListStreamsRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "ListStreamsResponse":
        return await self._unary_unary(
            "/s2.v1alpha.BasinService/ListStreams",
            list_streams_request,
            ListStreamsResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def create_stream(
        self,
        create_stream_request: "CreateStreamRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "CreateStreamResponse":
        return await self._unary_unary(
            "/s2.v1alpha.BasinService/CreateStream",
            create_stream_request,
            CreateStreamResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def delete_stream(
        self,
        delete_stream_request: "DeleteStreamRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "DeleteStreamResponse":
        return await self._unary_unary(
            "/s2.v1alpha.BasinService/DeleteStream",
            delete_stream_request,
            DeleteStreamResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def get_stream_config(
        self,
        get_stream_config_request: "GetStreamConfigRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "GetStreamConfigResponse":
        return await self._unary_unary(
            "/s2.v1alpha.BasinService/GetStreamConfig",
            get_stream_config_request,
            GetStreamConfigResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def reconfigure_stream(
        self,
        reconfigure_stream_request: "ReconfigureStreamRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "ReconfigureStreamResponse":
        return await self._unary_unary(
            "/s2.v1alpha.BasinService/ReconfigureStream",
            reconfigure_stream_request,
            ReconfigureStreamResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )


class StreamServiceStub(betterproto.ServiceStub):
    async def check_tail(
        self,
        check_tail_request: "CheckTailRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "CheckTailResponse":
        return await self._unary_unary(
            "/s2.v1alpha.StreamService/CheckTail",
            check_tail_request,
            CheckTailResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def append(
        self,
        append_request: "AppendRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "AppendResponse":
        return await self._unary_unary(
            "/s2.v1alpha.StreamService/Append",
            append_request,
            AppendResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def append_session(
        self,
        append_session_request_iterator: Union[
            AsyncIterable[AppendSessionRequest], Iterable[AppendSessionRequest]
        ],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> AsyncIterator[AppendSessionResponse]:
        async for response in self._stream_stream(
            "/s2.v1alpha.StreamService/AppendSession",
            append_session_request_iterator,
            AppendSessionRequest,
            AppendSessionResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        ):
            yield response

    async def read(
        self,
        read_request: "ReadRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "ReadResponse":
        return await self._unary_unary(
            "/s2.v1alpha.StreamService/Read",
            read_request,
            ReadResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def read_session(
        self,
        read_session_request: "ReadSessionRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> AsyncIterator[ReadSessionResponse]:
        async for response in self._unary_stream(
            "/s2.v1alpha.StreamService/ReadSession",
            read_session_request,
            ReadSessionResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        ):
            yield response


class AccountServiceBase(ServiceBase):

    async def list_basins(
        self, list_basins_request: "ListBasinsRequest"
    ) -> "ListBasinsResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def create_basin(
        self, create_basin_request: "CreateBasinRequest"
    ) -> "CreateBasinResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def delete_basin(
        self, delete_basin_request: "DeleteBasinRequest"
    ) -> "DeleteBasinResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def reconfigure_basin(
        self, reconfigure_basin_request: "ReconfigureBasinRequest"
    ) -> "ReconfigureBasinResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_basin_config(
        self, get_basin_config_request: "GetBasinConfigRequest"
    ) -> "GetBasinConfigResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_list_basins(
        self, stream: "grpclib.server.Stream[ListBasinsRequest, ListBasinsResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.list_basins(request)
        await stream.send_message(response)

    async def __rpc_create_basin(
        self, stream: "grpclib.server.Stream[CreateBasinRequest, CreateBasinResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.create_basin(request)
        await stream.send_message(response)

    async def __rpc_delete_basin(
        self, stream: "grpclib.server.Stream[DeleteBasinRequest, DeleteBasinResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.delete_basin(request)
        await stream.send_message(response)

    async def __rpc_reconfigure_basin(
        self,
        stream: "grpclib.server.Stream[ReconfigureBasinRequest, ReconfigureBasinResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.reconfigure_basin(request)
        await stream.send_message(response)

    async def __rpc_get_basin_config(
        self,
        stream: "grpclib.server.Stream[GetBasinConfigRequest, GetBasinConfigResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_basin_config(request)
        await stream.send_message(response)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/s2.v1alpha.AccountService/ListBasins": grpclib.const.Handler(
                self.__rpc_list_basins,
                grpclib.const.Cardinality.UNARY_UNARY,
                ListBasinsRequest,
                ListBasinsResponse,
            ),
            "/s2.v1alpha.AccountService/CreateBasin": grpclib.const.Handler(
                self.__rpc_create_basin,
                grpclib.const.Cardinality.UNARY_UNARY,
                CreateBasinRequest,
                CreateBasinResponse,
            ),
            "/s2.v1alpha.AccountService/DeleteBasin": grpclib.const.Handler(
                self.__rpc_delete_basin,
                grpclib.const.Cardinality.UNARY_UNARY,
                DeleteBasinRequest,
                DeleteBasinResponse,
            ),
            "/s2.v1alpha.AccountService/ReconfigureBasin": grpclib.const.Handler(
                self.__rpc_reconfigure_basin,
                grpclib.const.Cardinality.UNARY_UNARY,
                ReconfigureBasinRequest,
                ReconfigureBasinResponse,
            ),
            "/s2.v1alpha.AccountService/GetBasinConfig": grpclib.const.Handler(
                self.__rpc_get_basin_config,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetBasinConfigRequest,
                GetBasinConfigResponse,
            ),
        }


class BasinServiceBase(ServiceBase):

    async def list_streams(
        self, list_streams_request: "ListStreamsRequest"
    ) -> "ListStreamsResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def create_stream(
        self, create_stream_request: "CreateStreamRequest"
    ) -> "CreateStreamResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def delete_stream(
        self, delete_stream_request: "DeleteStreamRequest"
    ) -> "DeleteStreamResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def get_stream_config(
        self, get_stream_config_request: "GetStreamConfigRequest"
    ) -> "GetStreamConfigResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def reconfigure_stream(
        self, reconfigure_stream_request: "ReconfigureStreamRequest"
    ) -> "ReconfigureStreamResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_list_streams(
        self, stream: "grpclib.server.Stream[ListStreamsRequest, ListStreamsResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.list_streams(request)
        await stream.send_message(response)

    async def __rpc_create_stream(
        self, stream: "grpclib.server.Stream[CreateStreamRequest, CreateStreamResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.create_stream(request)
        await stream.send_message(response)

    async def __rpc_delete_stream(
        self, stream: "grpclib.server.Stream[DeleteStreamRequest, DeleteStreamResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.delete_stream(request)
        await stream.send_message(response)

    async def __rpc_get_stream_config(
        self,
        stream: "grpclib.server.Stream[GetStreamConfigRequest, GetStreamConfigResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.get_stream_config(request)
        await stream.send_message(response)

    async def __rpc_reconfigure_stream(
        self,
        stream: "grpclib.server.Stream[ReconfigureStreamRequest, ReconfigureStreamResponse]",
    ) -> None:
        request = await stream.recv_message()
        response = await self.reconfigure_stream(request)
        await stream.send_message(response)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/s2.v1alpha.BasinService/ListStreams": grpclib.const.Handler(
                self.__rpc_list_streams,
                grpclib.const.Cardinality.UNARY_UNARY,
                ListStreamsRequest,
                ListStreamsResponse,
            ),
            "/s2.v1alpha.BasinService/CreateStream": grpclib.const.Handler(
                self.__rpc_create_stream,
                grpclib.const.Cardinality.UNARY_UNARY,
                CreateStreamRequest,
                CreateStreamResponse,
            ),
            "/s2.v1alpha.BasinService/DeleteStream": grpclib.const.Handler(
                self.__rpc_delete_stream,
                grpclib.const.Cardinality.UNARY_UNARY,
                DeleteStreamRequest,
                DeleteStreamResponse,
            ),
            "/s2.v1alpha.BasinService/GetStreamConfig": grpclib.const.Handler(
                self.__rpc_get_stream_config,
                grpclib.const.Cardinality.UNARY_UNARY,
                GetStreamConfigRequest,
                GetStreamConfigResponse,
            ),
            "/s2.v1alpha.BasinService/ReconfigureStream": grpclib.const.Handler(
                self.__rpc_reconfigure_stream,
                grpclib.const.Cardinality.UNARY_UNARY,
                ReconfigureStreamRequest,
                ReconfigureStreamResponse,
            ),
        }


class StreamServiceBase(ServiceBase):

    async def check_tail(
        self, check_tail_request: "CheckTailRequest"
    ) -> "CheckTailResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def append(self, append_request: "AppendRequest") -> "AppendResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def append_session(
        self, append_session_request_iterator: AsyncIterator[AppendSessionRequest]
    ) -> AsyncIterator[AppendSessionResponse]:
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)
        yield AppendSessionResponse()

    async def read(self, read_request: "ReadRequest") -> "ReadResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def read_session(
        self, read_session_request: "ReadSessionRequest"
    ) -> AsyncIterator[ReadSessionResponse]:
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)
        yield ReadSessionResponse()

    async def __rpc_check_tail(
        self, stream: "grpclib.server.Stream[CheckTailRequest, CheckTailResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.check_tail(request)
        await stream.send_message(response)

    async def __rpc_append(
        self, stream: "grpclib.server.Stream[AppendRequest, AppendResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.append(request)
        await stream.send_message(response)

    async def __rpc_append_session(
        self,
        stream: "grpclib.server.Stream[AppendSessionRequest, AppendSessionResponse]",
    ) -> None:
        request = stream.__aiter__()
        await self._call_rpc_handler_server_stream(
            self.append_session,
            stream,
            request,
        )

    async def __rpc_read(
        self, stream: "grpclib.server.Stream[ReadRequest, ReadResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.read(request)
        await stream.send_message(response)

    async def __rpc_read_session(
        self, stream: "grpclib.server.Stream[ReadSessionRequest, ReadSessionResponse]"
    ) -> None:
        request = await stream.recv_message()
        await self._call_rpc_handler_server_stream(
            self.read_session,
            stream,
            request,
        )

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/s2.v1alpha.StreamService/CheckTail": grpclib.const.Handler(
                self.__rpc_check_tail,
                grpclib.const.Cardinality.UNARY_UNARY,
                CheckTailRequest,
                CheckTailResponse,
            ),
            "/s2.v1alpha.StreamService/Append": grpclib.const.Handler(
                self.__rpc_append,
                grpclib.const.Cardinality.UNARY_UNARY,
                AppendRequest,
                AppendResponse,
            ),
            "/s2.v1alpha.StreamService/AppendSession": grpclib.const.Handler(
                self.__rpc_append_session,
                grpclib.const.Cardinality.STREAM_STREAM,
                AppendSessionRequest,
                AppendSessionResponse,
            ),
            "/s2.v1alpha.StreamService/Read": grpclib.const.Handler(
                self.__rpc_read,
                grpclib.const.Cardinality.UNARY_UNARY,
                ReadRequest,
                ReadResponse,
            ),
            "/s2.v1alpha.StreamService/ReadSession": grpclib.const.Handler(
                self.__rpc_read_session,
                grpclib.const.Cardinality.UNARY_STREAM,
                ReadSessionRequest,
                ReadSessionResponse,
            ),
        }
