from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class BasinScope(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BASIN_SCOPE_UNSPECIFIED: _ClassVar[BasinScope]
    BASIN_SCOPE_AWS_US_EAST_1: _ClassVar[BasinScope]

class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OPERATION_UNSPECIFIED: _ClassVar[Operation]
    OPERATION_LIST_BASINS: _ClassVar[Operation]
    OPERATION_CREATE_BASIN: _ClassVar[Operation]
    OPERATION_DELETE_BASIN: _ClassVar[Operation]
    OPERATION_RECONFIGURE_BASIN: _ClassVar[Operation]
    OPERATION_GET_BASIN_CONFIG: _ClassVar[Operation]
    OPERATION_ISSUE_ACCESS_TOKEN: _ClassVar[Operation]
    OPERATION_REVOKE_ACCESS_TOKEN: _ClassVar[Operation]
    OPERATION_LIST_ACCESS_TOKENS: _ClassVar[Operation]
    OPERATION_LIST_STREAMS: _ClassVar[Operation]
    OPERATION_CREATE_STREAM: _ClassVar[Operation]
    OPERATION_DELETE_STREAM: _ClassVar[Operation]
    OPERATION_GET_STREAM_CONFIG: _ClassVar[Operation]
    OPERATION_RECONFIGURE_STREAM: _ClassVar[Operation]
    OPERATION_CHECK_TAIL: _ClassVar[Operation]
    OPERATION_APPEND: _ClassVar[Operation]
    OPERATION_READ: _ClassVar[Operation]
    OPERATION_TRIM: _ClassVar[Operation]
    OPERATION_FENCE: _ClassVar[Operation]
    OPERATION_ACCOUNT_METRICS: _ClassVar[Operation]
    OPERATION_BASIN_METRICS: _ClassVar[Operation]
    OPERATION_STREAM_METRICS: _ClassVar[Operation]

class StorageClass(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STORAGE_CLASS_UNSPECIFIED: _ClassVar[StorageClass]
    STORAGE_CLASS_STANDARD: _ClassVar[StorageClass]
    STORAGE_CLASS_EXPRESS: _ClassVar[StorageClass]

class TimestampingMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TIMESTAMPING_MODE_UNSPECIFIED: _ClassVar[TimestampingMode]
    TIMESTAMPING_MODE_CLIENT_PREFER: _ClassVar[TimestampingMode]
    TIMESTAMPING_MODE_CLIENT_REQUIRE: _ClassVar[TimestampingMode]
    TIMESTAMPING_MODE_ARRIVAL: _ClassVar[TimestampingMode]

class BasinState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BASIN_STATE_UNSPECIFIED: _ClassVar[BasinState]
    BASIN_STATE_ACTIVE: _ClassVar[BasinState]
    BASIN_STATE_CREATING: _ClassVar[BasinState]
    BASIN_STATE_DELETING: _ClassVar[BasinState]

BASIN_SCOPE_UNSPECIFIED: BasinScope
BASIN_SCOPE_AWS_US_EAST_1: BasinScope
OPERATION_UNSPECIFIED: Operation
OPERATION_LIST_BASINS: Operation
OPERATION_CREATE_BASIN: Operation
OPERATION_DELETE_BASIN: Operation
OPERATION_RECONFIGURE_BASIN: Operation
OPERATION_GET_BASIN_CONFIG: Operation
OPERATION_ISSUE_ACCESS_TOKEN: Operation
OPERATION_REVOKE_ACCESS_TOKEN: Operation
OPERATION_LIST_ACCESS_TOKENS: Operation
OPERATION_LIST_STREAMS: Operation
OPERATION_CREATE_STREAM: Operation
OPERATION_DELETE_STREAM: Operation
OPERATION_GET_STREAM_CONFIG: Operation
OPERATION_RECONFIGURE_STREAM: Operation
OPERATION_CHECK_TAIL: Operation
OPERATION_APPEND: Operation
OPERATION_READ: Operation
OPERATION_TRIM: Operation
OPERATION_FENCE: Operation
OPERATION_ACCOUNT_METRICS: Operation
OPERATION_BASIN_METRICS: Operation
OPERATION_STREAM_METRICS: Operation
STORAGE_CLASS_UNSPECIFIED: StorageClass
STORAGE_CLASS_STANDARD: StorageClass
STORAGE_CLASS_EXPRESS: StorageClass
TIMESTAMPING_MODE_UNSPECIFIED: TimestampingMode
TIMESTAMPING_MODE_CLIENT_PREFER: TimestampingMode
TIMESTAMPING_MODE_CLIENT_REQUIRE: TimestampingMode
TIMESTAMPING_MODE_ARRIVAL: TimestampingMode
BASIN_STATE_UNSPECIFIED: BasinState
BASIN_STATE_ACTIVE: BasinState
BASIN_STATE_CREATING: BasinState
BASIN_STATE_DELETING: BasinState

class ListBasinsRequest(_message.Message):
    __slots__ = ("prefix", "start_after", "limit")
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    START_AFTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    prefix: str
    start_after: str
    limit: int
    def __init__(
        self,
        prefix: _Optional[str] = ...,
        start_after: _Optional[str] = ...,
        limit: _Optional[int] = ...,
    ) -> None: ...

class ListBasinsResponse(_message.Message):
    __slots__ = ("basins", "has_more")
    BASINS_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    basins: _containers.RepeatedCompositeFieldContainer[BasinInfo]
    has_more: bool
    def __init__(
        self,
        basins: _Optional[_Iterable[_Union[BasinInfo, _Mapping]]] = ...,
        has_more: bool = ...,
    ) -> None: ...

class CreateBasinRequest(_message.Message):
    __slots__ = ("basin", "config", "scope")
    BASIN_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    basin: str
    config: BasinConfig
    scope: BasinScope
    def __init__(
        self,
        basin: _Optional[str] = ...,
        config: _Optional[_Union[BasinConfig, _Mapping]] = ...,
        scope: _Optional[_Union[BasinScope, str]] = ...,
    ) -> None: ...

class CreateBasinResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: BasinInfo
    def __init__(self, info: _Optional[_Union[BasinInfo, _Mapping]] = ...) -> None: ...

class DeleteBasinRequest(_message.Message):
    __slots__ = ("basin",)
    BASIN_FIELD_NUMBER: _ClassVar[int]
    basin: str
    def __init__(self, basin: _Optional[str] = ...) -> None: ...

class DeleteBasinResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetBasinConfigRequest(_message.Message):
    __slots__ = ("basin",)
    BASIN_FIELD_NUMBER: _ClassVar[int]
    basin: str
    def __init__(self, basin: _Optional[str] = ...) -> None: ...

class GetBasinConfigResponse(_message.Message):
    __slots__ = ("config",)
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: BasinConfig
    def __init__(
        self, config: _Optional[_Union[BasinConfig, _Mapping]] = ...
    ) -> None: ...

class ReconfigureBasinRequest(_message.Message):
    __slots__ = ("basin", "config", "mask")
    BASIN_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    MASK_FIELD_NUMBER: _ClassVar[int]
    basin: str
    config: BasinConfig
    mask: _field_mask_pb2.FieldMask
    def __init__(
        self,
        basin: _Optional[str] = ...,
        config: _Optional[_Union[BasinConfig, _Mapping]] = ...,
        mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...,
    ) -> None: ...

class ReconfigureBasinResponse(_message.Message):
    __slots__ = ("config",)
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: BasinConfig
    def __init__(
        self, config: _Optional[_Union[BasinConfig, _Mapping]] = ...
    ) -> None: ...

class IssueAccessTokenRequest(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: AccessTokenInfo
    def __init__(
        self, info: _Optional[_Union[AccessTokenInfo, _Mapping]] = ...
    ) -> None: ...

class ReadWritePermissions(_message.Message):
    __slots__ = ("read", "write")
    READ_FIELD_NUMBER: _ClassVar[int]
    WRITE_FIELD_NUMBER: _ClassVar[int]
    read: bool
    write: bool
    def __init__(self, read: bool = ..., write: bool = ...) -> None: ...

class PermittedOperationGroups(_message.Message):
    __slots__ = ("account", "basin", "stream")
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    BASIN_FIELD_NUMBER: _ClassVar[int]
    STREAM_FIELD_NUMBER: _ClassVar[int]
    account: ReadWritePermissions
    basin: ReadWritePermissions
    stream: ReadWritePermissions
    def __init__(
        self,
        account: _Optional[_Union[ReadWritePermissions, _Mapping]] = ...,
        basin: _Optional[_Union[ReadWritePermissions, _Mapping]] = ...,
        stream: _Optional[_Union[ReadWritePermissions, _Mapping]] = ...,
    ) -> None: ...

class RevokeAccessTokenRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class RevokeAccessTokenResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: AccessTokenInfo
    def __init__(
        self, info: _Optional[_Union[AccessTokenInfo, _Mapping]] = ...
    ) -> None: ...

class ListAccessTokensRequest(_message.Message):
    __slots__ = ("prefix", "start_after", "limit")
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    START_AFTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    prefix: str
    start_after: str
    limit: int
    def __init__(
        self,
        prefix: _Optional[str] = ...,
        start_after: _Optional[str] = ...,
        limit: _Optional[int] = ...,
    ) -> None: ...

class ListAccessTokensResponse(_message.Message):
    __slots__ = ("access_tokens", "has_more")
    ACCESS_TOKENS_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    access_tokens: _containers.RepeatedCompositeFieldContainer[AccessTokenInfo]
    has_more: bool
    def __init__(
        self,
        access_tokens: _Optional[_Iterable[_Union[AccessTokenInfo, _Mapping]]] = ...,
        has_more: bool = ...,
    ) -> None: ...

class AccessTokenInfo(_message.Message):
    __slots__ = ("id", "expires_at", "auto_prefix_streams", "scope")
    ID_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    AUTO_PREFIX_STREAMS_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    id: str
    expires_at: int
    auto_prefix_streams: bool
    scope: AccessTokenScope
    def __init__(
        self,
        id: _Optional[str] = ...,
        expires_at: _Optional[int] = ...,
        auto_prefix_streams: bool = ...,
        scope: _Optional[_Union[AccessTokenScope, _Mapping]] = ...,
    ) -> None: ...

class AccessTokenScope(_message.Message):
    __slots__ = ("basins", "streams", "access_tokens", "op_groups", "ops")
    BASINS_FIELD_NUMBER: _ClassVar[int]
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKENS_FIELD_NUMBER: _ClassVar[int]
    OP_GROUPS_FIELD_NUMBER: _ClassVar[int]
    OPS_FIELD_NUMBER: _ClassVar[int]
    basins: ResourceSet
    streams: ResourceSet
    access_tokens: ResourceSet
    op_groups: PermittedOperationGroups
    ops: _containers.RepeatedScalarFieldContainer[Operation]
    def __init__(
        self,
        basins: _Optional[_Union[ResourceSet, _Mapping]] = ...,
        streams: _Optional[_Union[ResourceSet, _Mapping]] = ...,
        access_tokens: _Optional[_Union[ResourceSet, _Mapping]] = ...,
        op_groups: _Optional[_Union[PermittedOperationGroups, _Mapping]] = ...,
        ops: _Optional[_Iterable[_Union[Operation, str]]] = ...,
    ) -> None: ...

class ResourceSet(_message.Message):
    __slots__ = ("exact", "prefix")
    EXACT_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    exact: str
    prefix: str
    def __init__(
        self, exact: _Optional[str] = ..., prefix: _Optional[str] = ...
    ) -> None: ...

class IssueAccessTokenResponse(_message.Message):
    __slots__ = ("access_token",)
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    access_token: str
    def __init__(self, access_token: _Optional[str] = ...) -> None: ...

class StreamInfo(_message.Message):
    __slots__ = ("name", "created_at", "deleted_at")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    DELETED_AT_FIELD_NUMBER: _ClassVar[int]
    name: str
    created_at: int
    deleted_at: int
    def __init__(
        self,
        name: _Optional[str] = ...,
        created_at: _Optional[int] = ...,
        deleted_at: _Optional[int] = ...,
    ) -> None: ...

class ListStreamsRequest(_message.Message):
    __slots__ = ("prefix", "start_after", "limit")
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    START_AFTER_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    prefix: str
    start_after: str
    limit: int
    def __init__(
        self,
        prefix: _Optional[str] = ...,
        start_after: _Optional[str] = ...,
        limit: _Optional[int] = ...,
    ) -> None: ...

class ListStreamsResponse(_message.Message):
    __slots__ = ("streams", "has_more")
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[StreamInfo]
    has_more: bool
    def __init__(
        self,
        streams: _Optional[_Iterable[_Union[StreamInfo, _Mapping]]] = ...,
        has_more: bool = ...,
    ) -> None: ...

class CreateStreamRequest(_message.Message):
    __slots__ = ("stream", "config")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    stream: str
    config: StreamConfig
    def __init__(
        self,
        stream: _Optional[str] = ...,
        config: _Optional[_Union[StreamConfig, _Mapping]] = ...,
    ) -> None: ...

class CreateStreamResponse(_message.Message):
    __slots__ = ("info",)
    INFO_FIELD_NUMBER: _ClassVar[int]
    info: StreamInfo
    def __init__(self, info: _Optional[_Union[StreamInfo, _Mapping]] = ...) -> None: ...

class DeleteStreamRequest(_message.Message):
    __slots__ = ("stream",)
    STREAM_FIELD_NUMBER: _ClassVar[int]
    stream: str
    def __init__(self, stream: _Optional[str] = ...) -> None: ...

class DeleteStreamResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetStreamConfigRequest(_message.Message):
    __slots__ = ("stream",)
    STREAM_FIELD_NUMBER: _ClassVar[int]
    stream: str
    def __init__(self, stream: _Optional[str] = ...) -> None: ...

class GetStreamConfigResponse(_message.Message):
    __slots__ = ("config",)
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: StreamConfig
    def __init__(
        self, config: _Optional[_Union[StreamConfig, _Mapping]] = ...
    ) -> None: ...

class ReconfigureStreamRequest(_message.Message):
    __slots__ = ("stream", "config", "mask")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    MASK_FIELD_NUMBER: _ClassVar[int]
    stream: str
    config: StreamConfig
    mask: _field_mask_pb2.FieldMask
    def __init__(
        self,
        stream: _Optional[str] = ...,
        config: _Optional[_Union[StreamConfig, _Mapping]] = ...,
        mask: _Optional[_Union[_field_mask_pb2.FieldMask, _Mapping]] = ...,
    ) -> None: ...

class ReconfigureStreamResponse(_message.Message):
    __slots__ = ("config",)
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    config: StreamConfig
    def __init__(
        self, config: _Optional[_Union[StreamConfig, _Mapping]] = ...
    ) -> None: ...

class CheckTailRequest(_message.Message):
    __slots__ = ("stream",)
    STREAM_FIELD_NUMBER: _ClassVar[int]
    stream: str
    def __init__(self, stream: _Optional[str] = ...) -> None: ...

class CheckTailResponse(_message.Message):
    __slots__ = ("next_seq_num", "last_timestamp")
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    LAST_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    next_seq_num: int
    last_timestamp: int
    def __init__(
        self, next_seq_num: _Optional[int] = ..., last_timestamp: _Optional[int] = ...
    ) -> None: ...

class AppendInput(_message.Message):
    __slots__ = ("stream", "records", "match_seq_num", "fencing_token")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    MATCH_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    stream: str
    records: _containers.RepeatedCompositeFieldContainer[AppendRecord]
    match_seq_num: int
    fencing_token: str
    def __init__(
        self,
        stream: _Optional[str] = ...,
        records: _Optional[_Iterable[_Union[AppendRecord, _Mapping]]] = ...,
        match_seq_num: _Optional[int] = ...,
        fencing_token: _Optional[str] = ...,
    ) -> None: ...

class AppendOutput(_message.Message):
    __slots__ = (
        "start_seq_num",
        "start_timestamp",
        "end_seq_num",
        "end_timestamp",
        "next_seq_num",
        "last_timestamp",
    )
    START_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    START_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    END_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    END_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    LAST_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    start_seq_num: int
    start_timestamp: int
    end_seq_num: int
    end_timestamp: int
    next_seq_num: int
    last_timestamp: int
    def __init__(
        self,
        start_seq_num: _Optional[int] = ...,
        start_timestamp: _Optional[int] = ...,
        end_seq_num: _Optional[int] = ...,
        end_timestamp: _Optional[int] = ...,
        next_seq_num: _Optional[int] = ...,
        last_timestamp: _Optional[int] = ...,
    ) -> None: ...

class AppendRequest(_message.Message):
    __slots__ = ("input",)
    INPUT_FIELD_NUMBER: _ClassVar[int]
    input: AppendInput
    def __init__(
        self, input: _Optional[_Union[AppendInput, _Mapping]] = ...
    ) -> None: ...

class AppendResponse(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: AppendOutput
    def __init__(
        self, output: _Optional[_Union[AppendOutput, _Mapping]] = ...
    ) -> None: ...

class AppendSessionRequest(_message.Message):
    __slots__ = ("input",)
    INPUT_FIELD_NUMBER: _ClassVar[int]
    input: AppendInput
    def __init__(
        self, input: _Optional[_Union[AppendInput, _Mapping]] = ...
    ) -> None: ...

class AppendSessionResponse(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: AppendOutput
    def __init__(
        self, output: _Optional[_Union[AppendOutput, _Mapping]] = ...
    ) -> None: ...

class ReadOutput(_message.Message):
    __slots__ = ("batch", "next_seq_num")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    batch: SequencedRecordBatch
    next_seq_num: int
    def __init__(
        self,
        batch: _Optional[_Union[SequencedRecordBatch, _Mapping]] = ...,
        next_seq_num: _Optional[int] = ...,
    ) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = (
        "stream",
        "seq_num",
        "timestamp",
        "tail_offset",
        "limit",
        "until",
        "clamp",
    )
    STREAM_FIELD_NUMBER: _ClassVar[int]
    SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TAIL_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    UNTIL_FIELD_NUMBER: _ClassVar[int]
    CLAMP_FIELD_NUMBER: _ClassVar[int]
    stream: str
    seq_num: int
    timestamp: int
    tail_offset: int
    limit: ReadLimit
    until: int
    clamp: bool
    def __init__(
        self,
        stream: _Optional[str] = ...,
        seq_num: _Optional[int] = ...,
        timestamp: _Optional[int] = ...,
        tail_offset: _Optional[int] = ...,
        limit: _Optional[_Union[ReadLimit, _Mapping]] = ...,
        until: _Optional[int] = ...,
        clamp: bool = ...,
    ) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: ReadOutput
    def __init__(
        self, output: _Optional[_Union[ReadOutput, _Mapping]] = ...
    ) -> None: ...

class ReadLimit(_message.Message):
    __slots__ = ("count", "bytes")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    BYTES_FIELD_NUMBER: _ClassVar[int]
    count: int
    bytes: int
    def __init__(
        self, count: _Optional[int] = ..., bytes: _Optional[int] = ...
    ) -> None: ...

class ReadSessionRequest(_message.Message):
    __slots__ = (
        "stream",
        "seq_num",
        "timestamp",
        "tail_offset",
        "limit",
        "heartbeats",
        "until",
        "clamp",
    )
    STREAM_FIELD_NUMBER: _ClassVar[int]
    SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TAIL_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    HEARTBEATS_FIELD_NUMBER: _ClassVar[int]
    UNTIL_FIELD_NUMBER: _ClassVar[int]
    CLAMP_FIELD_NUMBER: _ClassVar[int]
    stream: str
    seq_num: int
    timestamp: int
    tail_offset: int
    limit: ReadLimit
    heartbeats: bool
    until: int
    clamp: bool
    def __init__(
        self,
        stream: _Optional[str] = ...,
        seq_num: _Optional[int] = ...,
        timestamp: _Optional[int] = ...,
        tail_offset: _Optional[int] = ...,
        limit: _Optional[_Union[ReadLimit, _Mapping]] = ...,
        heartbeats: bool = ...,
        until: _Optional[int] = ...,
        clamp: bool = ...,
    ) -> None: ...

class ReadSessionResponse(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: ReadOutput
    def __init__(
        self, output: _Optional[_Union[ReadOutput, _Mapping]] = ...
    ) -> None: ...

class StreamConfig(_message.Message):
    __slots__ = ("storage_class", "age", "infinite", "timestamping", "delete_on_empty")
    class Timestamping(_message.Message):
        __slots__ = ("mode", "uncapped")
        MODE_FIELD_NUMBER: _ClassVar[int]
        UNCAPPED_FIELD_NUMBER: _ClassVar[int]
        mode: TimestampingMode
        uncapped: bool
        def __init__(
            self,
            mode: _Optional[_Union[TimestampingMode, str]] = ...,
            uncapped: bool = ...,
        ) -> None: ...

    class DeleteOnEmpty(_message.Message):
        __slots__ = ("min_age_secs",)
        MIN_AGE_SECS_FIELD_NUMBER: _ClassVar[int]
        min_age_secs: int
        def __init__(self, min_age_secs: _Optional[int] = ...) -> None: ...

    class InfiniteRetention(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...

    STORAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    AGE_FIELD_NUMBER: _ClassVar[int]
    INFINITE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPING_FIELD_NUMBER: _ClassVar[int]
    DELETE_ON_EMPTY_FIELD_NUMBER: _ClassVar[int]
    storage_class: StorageClass
    age: int
    infinite: StreamConfig.InfiniteRetention
    timestamping: StreamConfig.Timestamping
    delete_on_empty: StreamConfig.DeleteOnEmpty
    def __init__(
        self,
        storage_class: _Optional[_Union[StorageClass, str]] = ...,
        age: _Optional[int] = ...,
        infinite: _Optional[_Union[StreamConfig.InfiniteRetention, _Mapping]] = ...,
        timestamping: _Optional[_Union[StreamConfig.Timestamping, _Mapping]] = ...,
        delete_on_empty: _Optional[_Union[StreamConfig.DeleteOnEmpty, _Mapping]] = ...,
    ) -> None: ...

class BasinConfig(_message.Message):
    __slots__ = (
        "default_stream_config",
        "create_stream_on_append",
        "create_stream_on_read",
    )
    DEFAULT_STREAM_CONFIG_FIELD_NUMBER: _ClassVar[int]
    CREATE_STREAM_ON_APPEND_FIELD_NUMBER: _ClassVar[int]
    CREATE_STREAM_ON_READ_FIELD_NUMBER: _ClassVar[int]
    default_stream_config: StreamConfig
    create_stream_on_append: bool
    create_stream_on_read: bool
    def __init__(
        self,
        default_stream_config: _Optional[_Union[StreamConfig, _Mapping]] = ...,
        create_stream_on_append: bool = ...,
        create_stream_on_read: bool = ...,
    ) -> None: ...

class BasinInfo(_message.Message):
    __slots__ = ("name", "scope", "state")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    scope: BasinScope
    state: BasinState
    def __init__(
        self,
        name: _Optional[str] = ...,
        scope: _Optional[_Union[BasinScope, str]] = ...,
        state: _Optional[_Union[BasinState, str]] = ...,
    ) -> None: ...

class Header(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: bytes
    value: bytes
    def __init__(
        self, name: _Optional[bytes] = ..., value: _Optional[bytes] = ...
    ) -> None: ...

class AppendRecord(_message.Message):
    __slots__ = ("timestamp", "headers", "body")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    headers: _containers.RepeatedCompositeFieldContainer[Header]
    body: bytes
    def __init__(
        self,
        timestamp: _Optional[int] = ...,
        headers: _Optional[_Iterable[_Union[Header, _Mapping]]] = ...,
        body: _Optional[bytes] = ...,
    ) -> None: ...

class SequencedRecord(_message.Message):
    __slots__ = ("seq_num", "timestamp", "headers", "body")
    SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    seq_num: int
    timestamp: int
    headers: _containers.RepeatedCompositeFieldContainer[Header]
    body: bytes
    def __init__(
        self,
        seq_num: _Optional[int] = ...,
        timestamp: _Optional[int] = ...,
        headers: _Optional[_Iterable[_Union[Header, _Mapping]]] = ...,
        body: _Optional[bytes] = ...,
    ) -> None: ...

class SequencedRecordBatch(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[SequencedRecord]
    def __init__(
        self, records: _Optional[_Iterable[_Union[SequencedRecord, _Mapping]]] = ...
    ) -> None: ...
