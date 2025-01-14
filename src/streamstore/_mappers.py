from datetime import datetime, timedelta

from google.protobuf.field_mask_pb2 import FieldMask
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

import streamstore._lib.s2.v1alpha.s2_pb2 as msgs
from streamstore.schemas import (
    AppendInput,
    AppendOutput,
    BasinConfig,
    BasinInfo,
    BasinState,
    ReadLimit,
    Record,
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
    return BasinInfo(info.name, info.scope, info.cell, BasinState(info.state))


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
    basin_config = msgs.BasinConfig(default_stream_config=stream_config)
    if return_mask:
        return (basin_config, FieldMask(paths=paths))
    return basin_config


def stream_config_schema(config: msgs.StreamConfig) -> StreamConfig:
    return StreamConfig(
        StorageClass(config.storage_class),
        timedelta(seconds=config.age),
    )


def basin_config_schema(config: msgs.BasinConfig) -> BasinConfig:
    return BasinConfig(stream_config_schema(config.default_stream_config))


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


def _not_a_command_record(
    headers: RepeatedCompositeFieldContainer[msgs.Header],
) -> bool:
    if len(headers) == 1 and headers[0].name == b"":
        return False
    return True
