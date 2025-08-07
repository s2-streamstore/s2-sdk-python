from datetime import datetime, timedelta

from google.protobuf.field_mask_pb2 import FieldMask
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
    SequencedRecord,
    StorageClass,
    StreamConfig,
    StreamInfo,
)


def append_record_message(record: Record) -> msgs.AppendRecord:
    headers = [msgs.Header(name=name, value=value) for (name, value) in record.headers]
    return msgs.AppendRecord(headers=headers, body=record.body)


def append_input_message(stream: str, input: AppendInput) -> msgs.AppendInput:
    records = [append_record_message(r) for r in input.records]
    return msgs.AppendInput(
        stream=stream,
        records=records,
        match_seq_num=input.match_seq_num,
        fencing_token=input.fencing_token,
    )


def read_limit_message(limit: ReadLimit | None) -> msgs.ReadLimit:
    return (
        msgs.ReadLimit(count=limit.count, bytes=limit.bytes)
        if limit
        else msgs.ReadLimit()
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
    storage_class: StorageClass | None,
    retention_age: timedelta | None = None,
    return_mask: bool = False,
) -> msgs.StreamConfig | tuple[msgs.StreamConfig, FieldMask]:
    paths = []
    stream_config = msgs.StreamConfig()
    if storage_class is not None:
        paths.append("storage_class")
        stream_config.storage_class = storage_class.value
    if retention_age is not None:
        paths.append("retention_policy")
        stream_config.age = int(retention_age.total_seconds())
    if return_mask:
        return (stream_config, FieldMask(paths=paths))
    return stream_config


def basin_config_message(
    default_stream_storage_class: StorageClass | None,
    default_stream_retention_age: timedelta | None = None,
    create_stream_on_append: bool = False,
    return_mask: bool = False,
) -> msgs.BasinConfig | tuple[msgs.BasinConfig, FieldMask]:
    paths = []
    stream_config = msgs.StreamConfig()
    if default_stream_storage_class is not None:
        paths.append("default_stream_config.storage_class")
        stream_config.storage_class = default_stream_storage_class.value
    if default_stream_retention_age is not None:
        paths.append("default_stream_config.retention_policy")
        stream_config.age = int(default_stream_retention_age.total_seconds())
    if create_stream_on_append is True:
        paths.append("create_stream_on_append")
    basin_config = msgs.BasinConfig(
        default_stream_config=stream_config,
        create_stream_on_append=create_stream_on_append,
    )
    if return_mask:
        return (basin_config, FieldMask(paths=paths))
    return basin_config


def stream_config_schema(config: msgs.StreamConfig) -> StreamConfig:
    return StreamConfig(
        StorageClass(config.storage_class),
        timedelta(seconds=config.age),
    )


def basin_config_schema(config: msgs.BasinConfig) -> BasinConfig:
    return BasinConfig(
        stream_config_schema(config.default_stream_config),
        config.create_stream_on_append,
    )


def append_output_schema(output: msgs.AppendOutput) -> AppendOutput:
    return AppendOutput(output.start_seq_num, output.end_seq_num, output.next_seq_num)


def sequenced_records_schema(
    batch: msgs.SequencedRecordBatch, ignore_command_records: bool = False
) -> list[SequencedRecord]:
    if ignore_command_records:
        return [
            SequencedRecord(
                sr.seq_num, sr.body, [(h.name, h.value) for h in sr.headers]
            )
            for sr in batch.records
            if _not_a_command_record(sr.headers)
        ]
    return [
        SequencedRecord(sr.seq_num, sr.body, [(h.name, h.value) for h in sr.headers])
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
        return msgs.ReadWritePermissions(read, write)

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
            tokens=resource_set(scope.access_tokens),
            op_groups=permitted_op_groups(scope.op_group_perms),
            ops=(msgs.Operation(op.value) for op in scope.ops) if scope.ops else None,
        ),
    )


def access_token_info_schema(info: msgs.AccessTokenInfo) -> AccessTokenInfo:
    def resource_match_rule(resource_set: msgs.ResourceSet) -> ResourceMatchRule:
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
            access_tokens=resource_match_rule(info.scope.tokens),
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


def _not_a_command_record(
    headers: RepeatedCompositeFieldContainer[msgs.Header],
) -> bool:
    if len(headers) == 1 and headers[0].name == b"":
        return False
    return True
