from datetime import datetime
from typing import Literal, cast

from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

import streamstore._lib.s2.v1alpha.s2_pb2 as msgs
from streamstore.schemas import (
    AccessTokenInfo,
    AccessTokenScope,
    AppendInput,
    AppendOutput,
    BasinConfig,
    BasinInfo,
    BasinScope,
    BasinState,
    Operation,
    OperationGroupPermissions,
    Permission,
    ReadLimit,
    Record,
    ResourceMatchOp,
    ResourceMatchRule,
    SeqNum,
    SequencedRecord,
    StorageClass,
    StreamConfig,
    StreamInfo,
    TailOffset,
    Timestamp,
    Timestamping,
    TimestampingMode,
)

_ReadStart = SeqNum | Timestamp | TailOffset


def append_record_message(record: Record) -> msgs.AppendRecord:
    headers = [msgs.Header(name=name, value=value) for (name, value) in record.headers]
    return msgs.AppendRecord(
        timestamp=record.timestamp, headers=headers, body=record.body
    )


def append_input_message(stream: str, input: AppendInput) -> msgs.AppendInput:
    records = [append_record_message(r) for r in input.records]
    return msgs.AppendInput(
        stream=stream,
        records=records,
        match_seq_num=input.match_seq_num,
        fencing_token=input.fencing_token,
    )


def read_request_message(
    stream: str,
    start: _ReadStart,
    limit: ReadLimit | None,
    until: int | None,
) -> msgs.ReadRequest:
    seq_num, timestamp, tail_offset = _read_start_pos(start)
    return msgs.ReadRequest(
        stream=stream,
        seq_num=seq_num,
        timestamp=timestamp,
        tail_offset=tail_offset,
        limit=_read_limit_message(limit),
        until=until,
    )


def read_session_request_message(
    stream: str,
    start: _ReadStart,
    limit: ReadLimit | None,
    until: int | None,
    clamp: bool = False,
) -> msgs.ReadSessionRequest:
    seq_num, timestamp, tail_offset = _read_start_pos(start)
    return msgs.ReadSessionRequest(
        stream=stream,
        seq_num=seq_num,
        timestamp=timestamp,
        tail_offset=tail_offset,
        limit=_read_limit_message(limit),
        until=until,
        clamp=clamp,
    )


def _read_start_pos(start: _ReadStart) -> tuple[int | None, int | None, int | None]:
    seq_num = None
    timestamp = None
    tail_offset = None
    if isinstance(start, SeqNum):
        seq_num = start.value
    elif isinstance(start, Timestamp):
        timestamp = start.value
    elif isinstance(start, TailOffset):
        tail_offset = start.value
    else:
        raise ValueError("start doesn't match any of the expected types")
    return (
        seq_num,
        timestamp,
        tail_offset,
    )


def basin_info_schema(info: msgs.BasinInfo) -> BasinInfo:
    return BasinInfo(info.name, BasinScope(info.scope), BasinState(info.state))


def stream_info_schema(info: msgs.StreamInfo) -> StreamInfo:
    return StreamInfo(
        info.name,
        datetime.fromtimestamp(info.created_at),
        datetime.fromtimestamp(info.deleted_at) if info.deleted_at != 0 else None,
    )


def stream_config_message(
    config: StreamConfig | None = None,
    return_mask_paths: bool = False,
    mask_path_prefix: str = "",
) -> msgs.StreamConfig | tuple[msgs.StreamConfig, list[str]]:
    paths = []
    stream_config = msgs.StreamConfig()
    if config:
        storage_class = config.storage_class
        retention_policy = config.retention_policy
        timestamping = config.timestamping
        delete_on_empty_min_age = config.delete_on_empty_min_age
        if storage_class is not None:
            paths.append(f"{mask_path_prefix}storage_class")
            stream_config.storage_class = storage_class.value
        if retention_policy is not None:
            paths.append(f"{mask_path_prefix}retention_policy")
            if retention_policy == "infinite":
                stream_config.infinite.CopyFrom(msgs.StreamConfig.InfiniteRetention())
            else:
                stream_config.age = retention_policy
        if timestamping is not None:
            paths.append(f"{mask_path_prefix}timestamping")
            if timestamping.mode is not None:
                paths.append(f"{mask_path_prefix}timestamping.mode")
                stream_config.timestamping.mode = timestamping.mode.value
            if timestamping.uncapped is not None:
                paths.append(f"{mask_path_prefix}timestamping.uncapped")
                stream_config.timestamping.uncapped = timestamping.uncapped
        if delete_on_empty_min_age is not None:
            paths.append(f"{mask_path_prefix}delete_on_empty.min_age_secs")
            stream_config.delete_on_empty.min_age_secs = delete_on_empty_min_age
    if return_mask_paths:
        return (stream_config, paths)
    return stream_config


def basin_config_message(
    config: BasinConfig | None = None,
    return_mask_paths: bool = False,
) -> msgs.BasinConfig | tuple[msgs.BasinConfig, list[str]]:
    paths = []
    basin_config = msgs.BasinConfig()
    if config:
        if return_mask_paths:
            default_stream_config, deep_paths = cast(
                tuple[msgs.StreamConfig, list[str]],
                stream_config_message(
                    config.default_stream_config,
                    return_mask_paths,
                    mask_path_prefix="default_stream_config.",
                ),
            )
            paths.extend(deep_paths)
        else:
            default_stream_config = cast(
                msgs.StreamConfig, stream_config_message(config.default_stream_config)
            )
        basin_config.default_stream_config.CopyFrom(default_stream_config)
        if config.create_stream_on_append is not None:
            basin_config.create_stream_on_append = config.create_stream_on_append
            paths.append("create_stream_on_append")
    if return_mask_paths:
        return (basin_config, paths)
    return basin_config


def stream_config_schema(config: msgs.StreamConfig) -> StreamConfig:
    retention_policy: int | Literal["infinite"]
    match config.WhichOneof("retention_policy"):
        case "age":
            retention_policy = config.age
        case "infinite":
            retention_policy = "infinite"
        case _:
            raise RuntimeError(
                "StreamConfig retention_policy doesn't match any of the expected values"
            )
    return StreamConfig(
        StorageClass(config.storage_class),
        retention_policy,
        Timestamping(
            mode=TimestampingMode(config.timestamping.mode),
            uncapped=config.timestamping.uncapped,
        ),
        config.delete_on_empty.min_age_secs,
    )


def basin_config_schema(config: msgs.BasinConfig) -> BasinConfig:
    return BasinConfig(
        stream_config_schema(config.default_stream_config),
        config.create_stream_on_append,
    )


def append_output_schema(output: msgs.AppendOutput) -> AppendOutput:
    return AppendOutput(
        output.start_seq_num,
        output.start_timestamp,
        output.end_seq_num,
        output.end_timestamp,
        output.next_seq_num,
        output.last_timestamp,
    )


def sequenced_records_schema(
    batch: msgs.SequencedRecordBatch, ignore_command_records: bool = False
) -> list[SequencedRecord]:
    if ignore_command_records:
        return [
            SequencedRecord(
                sr.seq_num,
                sr.body,
                [(h.name, h.value) for h in sr.headers],
                sr.timestamp,
            )
            for sr in batch.records
            if _not_a_command_record(sr.headers)
        ]
    return [
        SequencedRecord(
            sr.seq_num, sr.body, [(h.name, h.value) for h in sr.headers], sr.timestamp
        )
        for sr in batch.records
    ]


def access_token_info_message(
    id: str, scope: AccessTokenScope, auto_prefix_streams: bool, expires_at: int | None
) -> msgs.AccessTokenInfo:
    def resource_set(rule: ResourceMatchRule | None) -> msgs.ResourceSet | None:
        if rule is None:
            return None
        match rule.match_op:
            case ResourceMatchOp.EXACT:
                return msgs.ResourceSet(exact=rule.value)
            case ResourceMatchOp.PREFIX:
                return msgs.ResourceSet(prefix=rule.value)
            case _:
                raise ValueError(
                    "ResourceMatchOp doesn't match any of the expected values"
                )

    def permissions(perm: Permission) -> msgs.ReadWritePermissions:
        read = False
        write = False
        match perm:
            case Permission.UNSPECIFIED:
                pass
            case Permission.READ:
                read = True
            case Permission.WRITE:
                write = True
            case Permission.READ_WRITE:
                read = True
                write = True
        return msgs.ReadWritePermissions(read=read, write=write)

    def permitted_op_groups(
        op_group_perms: OperationGroupPermissions | None,
    ) -> msgs.PermittedOperationGroups | None:
        if op_group_perms is None:
            return None
        return msgs.PermittedOperationGroups(
            account=permissions(op_group_perms.account),
            basin=permissions(op_group_perms.basin),
            stream=permissions(op_group_perms.stream),
        )

    return msgs.AccessTokenInfo(
        id=id,
        expires_at=expires_at,
        auto_prefix_streams=auto_prefix_streams,
        scope=msgs.AccessTokenScope(
            basins=resource_set(scope.basins),
            streams=resource_set(scope.streams),
            access_tokens=resource_set(scope.access_tokens),
            op_groups=permitted_op_groups(scope.op_group_perms),
            ops=(op.value for op in scope.ops),
        ),
    )


def access_token_info_schema(info: msgs.AccessTokenInfo) -> AccessTokenInfo:
    def resource_match_rule(resource_set: msgs.ResourceSet) -> ResourceMatchRule | None:
        if not resource_set.HasField("matching"):
            return None
        match resource_set.WhichOneof("matching"):
            case "exact":
                return ResourceMatchRule(ResourceMatchOp.EXACT, resource_set.exact)
            case "prefix":
                return ResourceMatchRule(ResourceMatchOp.PREFIX, resource_set.prefix)
            case _:
                raise RuntimeError(
                    "ResourceSet matching doesn't match any of the expected values"
                )

    def permission(perms: msgs.ReadWritePermissions) -> Permission:
        if perms.read and perms.write:
            return Permission.READ_WRITE
        elif perms.read:
            return Permission.READ
        elif perms.write:
            return Permission.WRITE
        else:
            return Permission.UNSPECIFIED

    return AccessTokenInfo(
        id=info.id,
        scope=AccessTokenScope(
            basins=resource_match_rule(info.scope.basins),
            streams=resource_match_rule(info.scope.streams),
            access_tokens=resource_match_rule(info.scope.access_tokens),
            op_group_perms=OperationGroupPermissions(
                account=permission(info.scope.op_groups.account),
                basin=permission(info.scope.op_groups.basin),
                stream=permission(info.scope.op_groups.stream),
            ),
            ops=[Operation(op) for op in info.scope.ops],
        ),
        auto_prefix_streams=info.auto_prefix_streams,
        expires_at=info.expires_at if info.HasField("expires_at") else None,
    )


def _read_limit_message(limit: ReadLimit | None) -> msgs.ReadLimit:
    return (
        msgs.ReadLimit(count=limit.count, bytes=limit.bytes)
        if limit
        else msgs.ReadLimit()
    )


def _not_a_command_record(
    headers: RepeatedCompositeFieldContainer[msgs.Header],
) -> bool:
    if len(headers) == 1 and headers[0].name == b"":
        return False
    return True
