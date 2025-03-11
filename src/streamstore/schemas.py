__all__ = [
    "Record",
    "AppendInput",
    "AppendOutput",
    "ReadLimit",
    "SequencedRecord",
    "FirstSeqNum",
    "NextSeqNum",
    "Page",
    "BasinScope",
    "BasinState",
    "BasinInfo",
    "StreamInfo",
    "StorageClass",
    "StreamConfig",
    "BasinConfig",
    "Cloud",
    "Endpoints",
]

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Generic, TypeVar

from streamstore._exceptions import fallible

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


class BasinScope(DocEnum):
    """
    Scope of a basin.
    """

    UNSPECIFIED = 0, "``UNSPECIFIED`` defaults to ``AWS_US_EAST_1``."
    AWS_US_EAST_1 = 1, "AWS ``us-east-1`` region."


@dataclass(slots=True)
class BasinInfo:
    """
    Basin information.
    """

    #: Basin name.
    name: str
    #: Basin scope.
    scope: BasinScope
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


class Endpoints:
    """
    `S2 endpoints <https://s2.dev/docs/endpoints>`_.
    """

    __slots__ = ("_account_authority", "_basin_base_authority")

    _account_authority: str
    _basin_base_authority: str

    def __init__(self, account_authority: str, basin_base_authority: str):
        self._account_authority = account_authority
        self._basin_base_authority = basin_base_authority

    @classmethod
    @fallible
    def for_cloud(cls, cloud: Cloud) -> "Endpoints":
        """
        Construct S2 endpoints for the given cloud.

        Args:
            cloud: Cloud in which the S2 service runs.
        """
        return cls(
            _account_authority(cloud),
            _basin_authority(cloud),
        )

    @classmethod
    @fallible
    def _from_env(cls) -> "Endpoints":
        account_authority = os.getenv("S2_ACCOUNT_ENDPOINT")
        basin_authority = os.getenv("S2_BASIN_ENDPOINT")
        if (
            account_authority
            and basin_authority
            and basin_authority.startswith("{basin}.")
        ):
            basin_base_authority = basin_authority.removeprefix("{basin}.")
            return cls(account_authority, basin_base_authority)
        raise ValueError("Invalid S2_ACCOUNT_ENDPOINT and/or S2_BASIN_ENDPOINT")

    def _account(self) -> str:
        return self._account_authority

    def _basin(self, basin_name: str) -> str:
        return f"{basin_name}.{self._basin_base_authority}"


def _account_authority(cloud: Cloud) -> str:
    match cloud:
        case Cloud.AWS:
            return "aws.s2.dev"
        case _:
            raise ValueError(f"Invalid cloud: {cloud}")


def _basin_authority(cloud: Cloud) -> str:
    match cloud:
        case Cloud.AWS:
            return "b.aws.s2.dev"
        case _:
            raise ValueError(f"Invalid cloud: {cloud}")
