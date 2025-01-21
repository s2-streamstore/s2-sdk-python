__all__ = [
    "Record",
    "AppendInput",
    "AppendOutput",
    "ReadLimit",
    "SequencedRecord",
    "FirstSeqNum",
    "NextSeqNum",
    "Page",
    "BasinState",
    "BasinInfo",
    "StreamInfo",
    "StorageClass",
    "StreamConfig",
    "BasinConfig",
    "Cloud",
]

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")

ONE_MIB = 1024 * 1024


class DocEnum(Enum):
    def __new__(cls, value, doc=None):
        self = object.__new__(cls)
        self._value_ = value
        if doc is not None:
            self.__doc__ = doc
        return self


@dataclass(slots=True)
class Record:
    """
    Record to be appended to a stream.
    """

    #: Body of this record.
    body: bytes
    #: Series of name-value pairs for this record.
    headers: list[tuple[bytes, bytes]] = field(default_factory=list)


@dataclass(slots=True)
class AppendInput:
    """
    Used in the parameters to :meth:`.Stream.append` and :meth:`.Stream.append_session`.
    """

    #: Batch of records to append atomically, which must contain at least one record,
    #: and no more than 1000. The size of the batch must not exceed 1MiB of :func:`.metered_bytes`.
    records: list[Record]
    #: Enforce that the sequence number issued to the first record in the batch matches this value.
    match_seq_num: int | None = None
    #: Enforce a fencing token, which must have been previously set by a ``fence`` command record.
    fencing_token: bytes | None = None


@dataclass(slots=True)
class AppendOutput:
    """
    Returned from :meth:`.Stream.append`.

    (or)

    Yielded from :meth:`.Stream.append_session`.
    """

    #: Sequence number of first record appended.
    start_seq_num: int
    #: Sequence number of last record appended + 1.
    #: ``end_seq_num - start_seq_num`` will be the number of records in the batch.
    end_seq_num: int
    #: Sequence number of last durable record on the stream + 1.
    #: This can be greater than ``end_seq_num`` in case of concurrent appends.
    next_seq_num: int


@dataclass(slots=True)
class ReadLimit:
    """
    Used in the parameters to :meth:`.Stream.read` and :meth:`.Stream.read_session`.

    If both ``count`` and ``bytes`` are specified, either limit may be hit.
    """

    #: Number of records.
    count: int | None = None
    #: Cumulative size of records calculated using :func:`.metered_bytes`.
    bytes: int | None = None


@dataclass(slots=True)
class SequencedRecord:
    """
    Record read from a stream.
    """

    #: Sequence number for this record.
    seq_num: int
    #: Body of this record.
    body: bytes
    #: Series of name-value pairs for this record.
    headers: list[tuple[bytes, bytes]]


@dataclass(slots=True)
class FirstSeqNum:
    value: int


@dataclass(slots=True)
class NextSeqNum:
    value: int


@dataclass(slots=True)
class Page(Generic[T]):
    """
    Page of items.
    """

    #: List of items of any type T.
    items: list[T]
    #: If True, it means that there are more pages.
    has_more: bool


class BasinState(DocEnum):
    """
    Current state of a basin.
    """

    UNSPECIFIED = 0
    ACTIVE = 1
    CREATING = 2
    DELETING = 3


@dataclass(slots=True)
class BasinInfo:
    """
    Basin information.
    """

    #: Basin name.
    name: str
    #: Basin scope.
    scope: str
    #: Cell assignment.
    cell: str
    #: Basin state.
    state: BasinState


@dataclass(slots=True)
class StreamInfo:
    """
    Stream information.
    """

    #: Stream name.
    name: str
    #: Creation time.
    created_at: datetime
    #: Deletion time, if this stream is being deleted.
    deleted_at: datetime | None


class StorageClass(DocEnum):
    """
    Storage class for recent appends.
    """

    UNSPECIFIED = 0, "``UNSPECIFIED`` gets overridden to ``EXPRESS``."
    STANDARD = 1, "Offers end-to-end latencies under 500 ms."
    EXPRESS = 2, "Offers end-to-end latencies under 50 ms."


@dataclass(slots=True)
class StreamConfig:
    """
    Current configuration of a stream.
    """

    #: Storage class for this stream.
    storage_class: StorageClass
    #: Thresold for automatic trimming of records in this stream.
    retention_age: timedelta


@dataclass(slots=True)
class BasinConfig:
    """
    Current configuration of a basin.
    """

    #: Default configuration for streams in this basin.
    default_stream_config: StreamConfig


class Cloud(DocEnum):
    """
    Cloud in which the S2 service runs.
    """

    AWS = 1
