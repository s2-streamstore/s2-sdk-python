__all__ = [
    "Record",
    "CommandRecord",
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
    "metered_bytes",
]

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Generic, Iterable, TypeVar

from streamstore._exceptions import S2Error

T = TypeVar("T")

_ONE_MIB = 1024 * 1024


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


class CommandRecord:
    """
    Helper class for creating command records.
    """

    FENCE = b"fence"
    TRIM = b"trim"

    @staticmethod
    def fence(token: bytes) -> Record:
        """
        Create a fence command record.
        """
        if len(token) > 16:
            raise ValueError("fencing token cannot be greater than 16 bytes")
        return Record(body=token, headers=[(bytes(), CommandRecord.FENCE)])

    @staticmethod
    def trim(desired_first_seq_num: int) -> Record:
        """
        Create a trim command record.
        """
        return Record(
            body=desired_first_seq_num.to_bytes(8),
            headers=[(bytes(), CommandRecord.TRIM)],
        )


@dataclass(slots=True)
class AppendInput:
    """
    Used in the parameters to :meth:`.Stream.append` and :meth:`.Stream.append_session`.
    """

    #: Batch of records to append atomically, which must contain at least one record,
    #: and no more than 1000. The total size of the batch must not exceed 1MiB of :func:`.metered_bytes`.
    records: list[Record]
    #: Enforce that the sequence number issued to the first record in the batch matches this value.
    match_seq_num: int | None = None
    #: Enforce a fencing token, which must have been previously set by a ``fence`` command record.
    fencing_token: bytes | None = None

    def __post_init__(self):
        num_bytes = metered_bytes(self.records)
        num_records = len(self.records)
        if 1 <= num_records <= 1000 and num_bytes <= _ONE_MIB:
            return
        raise S2Error(
            f"Invalid append input: num_records={num_records}, metered_bytes={num_bytes}"
        )


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
    Used in the parameters to :meth:`.Stream.read` and :meth:`.Stream.read_session`

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


def metered_bytes(records: Iterable[Record | SequencedRecord]) -> int:
    """
    Each record is metered using the following formula:

    .. code-block:: python

        8 + 2 * len(headers)
        + sum((len(name) + len(value)) for (name, value) in headers)
        + len(body)

    """
    return sum(
        (
            8
            + 2 * len(record.headers)
            + sum((len(name) + len(value)) for (name, value) in record.headers)
            + len(record.body)
        )
        for record in records
    )
