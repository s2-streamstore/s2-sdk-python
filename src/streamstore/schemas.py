__all__ = [
    "Record",
    "AppendInput",
    "AppendOutput",
    "Tail",
    "SeqNum",
    "Timestamp",
    "TailOffset",
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
    "TimestampingMode",
    "Timestamping",
    "StreamConfig",
    "BasinConfig",
    "ResourceMatchOp",
    "ResourceMatchRule",
    "Permission",
    "OperationGroupPermissions",
    "Operation",
    "AccessTokenScope",
    "AccessTokenInfo",
    "Cloud",
    "Endpoints",
]

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

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
    #: Timestamp for this record.
    #:
    #: Precise semantics depend on :attr:`.StreamConfig.timestamping`.
    timestamp: int | None = None


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
    fencing_token: str | None = None


@dataclass(slots=True)
class AppendOutput:
    """
    Returned from :meth:`.Stream.append`.

    (or)

    Yielded from :meth:`.Stream.append_session`.
    """

    #: Sequence number of the first appended record.
    start_seq_num: int
    #: Timestamp of the first appended record.
    start_timestamp: int
    #: Sequence number of the last appended record + 1.
    #: ``end_seq_num - start_seq_num`` will be the number of records in the batch.
    end_seq_num: int
    #: Timestamp of the last appended record.
    end_timestamp: int
    #: Sequence number of the last durable record on the stream + 1.
    #: This can be greater than ``end_seq_num`` in case of concurrent appends.
    next_seq_num: int
    #: Timestamp of the last durable record on the stream.
    last_timestamp: int


@dataclass(slots=True)
class Tail:
    """
    Tail of a stream.
    """

    #: Sequence number of the last durable record on the stream + 1.
    next_seq_num: int
    #: Timestamp of the last durable record on the stream.
    last_timestamp: int


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

    #: Sequence number assigned to this record.
    seq_num: int
    #: Body of this record.
    body: bytes
    #: Series of name-value pairs for this record.
    headers: list[tuple[bytes, bytes]]
    #: Timestamp for this record.
    timestamp: int


@dataclass(slots=True)
class SeqNum:
    value: int


@dataclass(slots=True)
class Timestamp:
    value: int


@dataclass(slots=True)
class TailOffset:
    """
    Number of records before the tail.
    """

    value: int


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
    #: If ``True``, it means that there are more pages.
    has_more: bool


class BasinScope(DocEnum):
    """
    Scope of a basin.
    """

    UNSPECIFIED = 0, "``UNSPECIFIED`` defaults to ``AWS_US_EAST_1``."
    AWS_US_EAST_1 = 1, "AWS ``us-east-1`` region."


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

    STANDARD = 1, "Offers end-to-end latencies under 500 ms."
    EXPRESS = 2, "Offers end-to-end latencies under 50 ms."


class TimestampingMode(DocEnum):
    """
    Timestamping mode.

    Note:
        The arrival time is always in milliseconds since Unix epoch.
    """

    UNSPECIFIED = 0, "Defaults to ``CLIENT_PREFER``."
    CLIENT_PREFER = (
        1,
        "Prefer client-specified timestamp if present, otherwise use arrival time.",
    )
    CLIENT_REQUIRE = (
        2,
        "Require a client-specified timestamp and reject the append if it is absent.",
    )
    ARRIVAL = 3, "Use the arrival time and ignore any client-specified timestamp."


@dataclass(slots=True)
class Timestamping:
    """
    Timestamping behavior.
    """

    #: Timestamping mode.
    #:
    #: If not specified, the default is  :attr:`.TimestampingMode.CLIENT_PREFER`.
    mode: TimestampingMode | None = None
    #: Allow client-specified timestamps to exceed the arrival time.
    uncapped: bool | None = None


@dataclass(slots=True)
class StreamConfig:
    """
    Stream configuration.
    """

    #: Storage class for this stream.
    #:
    #: If not specified, the default is :attr:`.StorageClass.EXPRESS`.
    storage_class: StorageClass | None = None
    #: Retention policy for records in this stream.
    #:
    #: Retention duration in seconds to automatically trim records older than this duration.
    #:
    #: ``'infinite'`` to retain records indefinitely.
    #: (While S2 is in public preview, this is capped at 28 days. Let us know if you'd like the cap removed.)
    #:
    #: If not specified, the default is to retain records for 7 days.
    retention_policy: int | Literal["infinite"] | None = None
    #: Timestamping behavior for appends to this stream, which influences how timestamps are handled.
    timestamping: Timestamping | None = None
    #: Minimum age in seconds before this stream can be automatically deleted if empty.
    #:
    #: If not specified or set to ``0``, this stream will not be automatically deleted.
    delete_on_empty_min_age: int | None = None


@dataclass(slots=True)
class BasinConfig:
    """
    Basin configuration.
    """

    #: Default configuration for streams in this basin.
    default_stream_config: StreamConfig | None = None
    #: Create stream on append if it doesn't exist, using the default stream configuration.
    create_stream_on_append: bool | None = None


class ResourceMatchOp(DocEnum):
    """
    Resource match operator.
    """

    EXACT = (
        1,
        "Match only the resource with the exact value. Use an empty string to match no resources.",
    )
    PREFIX = (
        2,
        "Match all resources that start with the prefix value. Use an empty string to match all resources.",
    )


@dataclass(slots=True)
class ResourceMatchRule:
    """
    Resource match rule.
    """

    #: Match operator.
    match_op: ResourceMatchOp
    #: Value to match.
    value: str


class Permission(DocEnum):
    """
    Permission.
    """

    UNSPECIFIED = 0
    READ = 1
    WRITE = 2
    READ_WRITE = 3


@dataclass(slots=True)
class OperationGroupPermissions:
    """
    Operation group permissions.
    """

    #: Permission for account operations.
    account: Permission = Permission.UNSPECIFIED
    #: Permission for basin operations.
    basin: Permission = Permission.UNSPECIFIED
    #: Permission for stream operations.
    stream: Permission = Permission.UNSPECIFIED


class Operation(DocEnum):
    """
    Operation.
    """

    UNSPECIFIED = 0
    LIST_BASINS = 1
    CREATE_BASIN = 2
    DELETE_BASIN = 3
    RECONFIGURE_BASIN = 4
    GET_BASIN_CONFIG = 5
    ISSUE_ACCESS_TOKEN = 6
    REVOKE_ACCESS_TOKEN = 7
    LIST_ACCESS_TOKENS = 8
    LIST_STREAMS = 9
    CREATE_STREAM = 10
    DELETE_STREAM = 11
    GET_STREAM_CONFIG = 12
    RECONFIGURE_STREAM = 13
    CHECK_TAIL = 14
    APPEND = 15
    READ = 16


@dataclass(slots=True)
class AccessTokenScope:
    """
    Access token scope.
    """

    #: Allowed basins.
    basins: ResourceMatchRule | None = None
    #: Allowed streams.
    streams: ResourceMatchRule | None = None
    #: Allowed access token IDs.
    access_tokens: ResourceMatchRule | None = None
    #: Permissions at operation group level.
    op_group_perms: OperationGroupPermissions | None = None
    #: Allowed operations.
    #:
    #: Note:
    #:  A union of allowed operations and groups is used as the effective set of allowed operations.
    ops: list[Operation] = field(default_factory=list)


@dataclass(slots=True)
class AccessTokenInfo:
    """
    Access token information.
    """

    #: Access token ID.
    id: str
    #: Access token scope.
    scope: AccessTokenScope
    #: Expiration time in seconds since Unix epoch.
    expires_at: int | None
    #: Whether auto-prefixing is enabled for streams in scope.
    auto_prefix_streams: bool


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
