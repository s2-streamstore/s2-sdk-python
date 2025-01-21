from google.protobuf import field_mask_pb2 as _field_mask_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class StorageClass(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STORAGE_CLASS_UNSPECIFIED: _ClassVar[StorageClass]
    STORAGE_CLASS_STANDARD: _ClassVar[StorageClass]
    STORAGE_CLASS_EXPRESS: _ClassVar[StorageClass]

class BasinState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BASIN_STATE_UNSPECIFIED: _ClassVar[BasinState]
    BASIN_STATE_ACTIVE: _ClassVar[BasinState]
    BASIN_STATE_CREATING: _ClassVar[BasinState]
    BASIN_STATE_DELETING: _ClassVar[BasinState]

STORAGE_CLASS_UNSPECIFIED: StorageClass
STORAGE_CLASS_STANDARD: StorageClass
STORAGE_CLASS_EXPRESS: StorageClass
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
    __slots__ = ("basin", "config", "scope", "cell")
    BASIN_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CELL_FIELD_NUMBER: _ClassVar[int]
    basin: str
    config: BasinConfig
    scope: str
    cell: str
    def __init__(
        self,
        basin: _Optional[str] = ...,
        config: _Optional[_Union[BasinConfig, _Mapping]] = ...,
        scope: _Optional[str] = ...,
        cell: _Optional[str] = ...,
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
    __slots__ = ("next_seq_num",)
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    next_seq_num: int
    def __init__(self, next_seq_num: _Optional[int] = ...) -> None: ...

class AppendInput(_message.Message):
    __slots__ = ("stream", "records", "match_seq_num", "fencing_token")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    MATCH_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    FENCING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    stream: str
    records: _containers.RepeatedCompositeFieldContainer[AppendRecord]
    match_seq_num: int
    fencing_token: bytes
    def __init__(
        self,
        stream: _Optional[str] = ...,
        records: _Optional[_Iterable[_Union[AppendRecord, _Mapping]]] = ...,
        match_seq_num: _Optional[int] = ...,
        fencing_token: _Optional[bytes] = ...,
    ) -> None: ...

class AppendOutput(_message.Message):
    __slots__ = ("start_seq_num", "end_seq_num", "next_seq_num")
    START_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    END_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    start_seq_num: int
    end_seq_num: int
    next_seq_num: int
    def __init__(
        self,
        start_seq_num: _Optional[int] = ...,
        end_seq_num: _Optional[int] = ...,
        next_seq_num: _Optional[int] = ...,
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
    __slots__ = ("batch", "first_seq_num", "next_seq_num")
    BATCH_FIELD_NUMBER: _ClassVar[int]
    FIRST_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    NEXT_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    batch: SequencedRecordBatch
    first_seq_num: int
    next_seq_num: int
    def __init__(
        self,
        batch: _Optional[_Union[SequencedRecordBatch, _Mapping]] = ...,
        first_seq_num: _Optional[int] = ...,
        next_seq_num: _Optional[int] = ...,
    ) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ("stream", "start_seq_num", "limit")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    START_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    stream: str
    start_seq_num: int
    limit: ReadLimit
    def __init__(
        self,
        stream: _Optional[str] = ...,
        start_seq_num: _Optional[int] = ...,
        limit: _Optional[_Union[ReadLimit, _Mapping]] = ...,
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
    __slots__ = ("stream", "start_seq_num", "limit")
    STREAM_FIELD_NUMBER: _ClassVar[int]
    START_SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    stream: str
    start_seq_num: int
    limit: ReadLimit
    def __init__(
        self,
        stream: _Optional[str] = ...,
        start_seq_num: _Optional[int] = ...,
        limit: _Optional[_Union[ReadLimit, _Mapping]] = ...,
    ) -> None: ...

class ReadSessionResponse(_message.Message):
    __slots__ = ("output",)
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    output: ReadOutput
    def __init__(
        self, output: _Optional[_Union[ReadOutput, _Mapping]] = ...
    ) -> None: ...

class StreamConfig(_message.Message):
    __slots__ = ("storage_class", "age")
    STORAGE_CLASS_FIELD_NUMBER: _ClassVar[int]
    AGE_FIELD_NUMBER: _ClassVar[int]
    storage_class: StorageClass
    age: int
    def __init__(
        self,
        storage_class: _Optional[_Union[StorageClass, str]] = ...,
        age: _Optional[int] = ...,
    ) -> None: ...

class BasinConfig(_message.Message):
    __slots__ = ("default_stream_config",)
    DEFAULT_STREAM_CONFIG_FIELD_NUMBER: _ClassVar[int]
    default_stream_config: StreamConfig
    def __init__(
        self, default_stream_config: _Optional[_Union[StreamConfig, _Mapping]] = ...
    ) -> None: ...

class BasinInfo(_message.Message):
    __slots__ = ("name", "scope", "cell", "state")
    NAME_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    CELL_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    scope: str
    cell: str
    state: BasinState
    def __init__(
        self,
        name: _Optional[str] = ...,
        scope: _Optional[str] = ...,
        cell: _Optional[str] = ...,
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
    __slots__ = ("headers", "body")
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    headers: _containers.RepeatedCompositeFieldContainer[Header]
    body: bytes
    def __init__(
        self,
        headers: _Optional[_Iterable[_Union[Header, _Mapping]]] = ...,
        body: _Optional[bytes] = ...,
    ) -> None: ...

class SequencedRecord(_message.Message):
    __slots__ = ("seq_num", "headers", "body")
    SEQ_NUM_FIELD_NUMBER: _ClassVar[int]
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    seq_num: int
    headers: _containers.RepeatedCompositeFieldContainer[Header]
    body: bytes
    def __init__(
        self,
        seq_num: _Optional[int] = ...,
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
