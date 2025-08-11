import asyncio
import time
from typing import AsyncIterable

import pytest

from streamstore import Stream
from streamstore.schemas import (
    AppendInput,
    ReadLimit,
    Record,
    SeqNum,
    Tail,
    TailOffset,
    Timestamp,
)
from streamstore.utils import metered_bytes


@pytest.mark.stream
class TestStreamOperations:
    async def test_check_tail_empty_stream(self, stream: Stream):
        tail = await stream.check_tail()

        assert tail.next_seq_num == 0
        assert tail.last_timestamp == 0

    async def test_append_single_record(self, stream: Stream):
        input = AppendInput(records=[Record(body=b"record-0")])
        output = await stream.append(input)

        assert output.start_seq_num == 0
        assert output.end_seq_num == 1
        assert output.next_seq_num == 1
        assert output.start_timestamp > 0
        assert output.end_timestamp > 0
        assert output.last_timestamp > 0

    async def test_append_multiple_records(self, stream: Stream):
        input = AppendInput(
            records=[
                Record(body=f"record-{i}".encode(), headers=[(b"key", b"value")])
                for i in range(3)
            ]
        )
        output = await stream.append(input)

        assert output.start_seq_num == 0
        assert output.end_seq_num == 3
        assert output.next_seq_num == 3

    async def test_append_with_match_seq_num(self, stream: Stream):
        input_0 = AppendInput(records=[Record(body=b"record-0")])
        output_0 = await stream.append(input_0)

        input_1 = AppendInput(
            records=[Record(body=b"record-1")], match_seq_num=output_0.next_seq_num
        )
        output_1 = await stream.append(input_1)

        assert output_1.start_seq_num == 1
        assert output_1.end_seq_num == 2
        assert output_1.next_seq_num == 2

    async def test_append_with_timestamp(self, stream: Stream):
        timestamp_0 = int(time.time())
        await asyncio.sleep(0.1)
        timestamp_1 = int(time.time())

        input = AppendInput(
            records=[
                Record(body=b"record-0", timestamp=timestamp_0),
                Record(body=b"record-1", timestamp=timestamp_1),
            ]
        )
        output = await stream.append(input)

        assert output.start_seq_num == 0
        assert output.start_timestamp == timestamp_0
        assert output.end_seq_num == 2
        assert output.end_timestamp == timestamp_1
        assert output.next_seq_num == 2
        assert output.last_timestamp == timestamp_1

    async def test_read_from_seq_num_zero(self, stream: Stream):
        await stream.append(
            AppendInput(records=[Record(body=f"record-{i}".encode()) for i in range(3)])
        )

        records = await stream.read(start=SeqNum(0))

        assert isinstance(records, list)
        assert len(records) == 3

        for i, record in enumerate(records):
            assert record.seq_num == i
            assert record.body == f"record-{i}".encode()

    async def test_read_with_limit(self, stream: Stream):
        await stream.append(
            AppendInput(records=[Record(body=f"record-{i}".encode()) for i in range(5)])
        )

        records = await stream.read(start=SeqNum(0), limit=ReadLimit(count=2))

        assert isinstance(records, list)
        assert len(records) == 2

        records = await stream.read(start=SeqNum(0), limit=ReadLimit(bytes=20))

        assert isinstance(records, list)
        total_bytes = sum(metered_bytes([r]) for r in records)
        assert total_bytes <= 20

    async def test_read_from_timestamp(self, stream: Stream):
        output = await stream.append(AppendInput(records=[Record(body=b"record-0")]))

        records = await stream.read(start=Timestamp(output.start_timestamp))

        assert isinstance(records, list)
        assert len(records) == 1

    async def test_read_from_tail_offset(self, stream: Stream):
        await stream.append(
            AppendInput(records=[Record(body=f"record-{i}".encode()) for i in range(5)])
        )

        records = await stream.read(start=TailOffset(2))

        assert isinstance(records, list)
        assert len(records) == 2
        assert records[0].body == b"record-3"
        assert records[1].body == b"record-4"

    async def test_read_until_timestamp(self, stream: Stream):
        timestamp_0 = int(time.time() * 1000)
        await asyncio.sleep(0.2)
        timestamp_1 = int(time.time() * 1000)
        await asyncio.sleep(0.2)
        timestamp_2 = int(time.time() * 1000)

        await stream.append(
            AppendInput(
                records=[
                    Record(body=b"record-0", timestamp=timestamp_0),
                    Record(body=b"record-1", timestamp=timestamp_1),
                    Record(body=b"record-2", timestamp=timestamp_2),
                ]
            )
        )

        records = await stream.read(start=Timestamp(timestamp_0), until=timestamp_2)
        assert isinstance(records, list)
        assert len(records) == 2
        assert records[0].timestamp == timestamp_0
        assert records[1].timestamp == timestamp_1

    async def test_read_beyond_tail(self, stream: Stream):
        await stream.append(
            AppendInput(records=[Record(body=f"record-{i}".encode()) for i in range(5)])
        )

        tail = await stream.read(start=SeqNum(100))

        assert isinstance(tail, Tail)
        assert tail.next_seq_num == 5

    async def test_append_session(self, stream: Stream):
        async def inputs_gen() -> AsyncIterable[AppendInput]:
            for i in range(3):
                records = [
                    Record(body=f"batch-{i}-record-{j}".encode()) for j in range(2)
                ]
                yield AppendInput(records=records)

        outputs = []
        async for output in stream.append_session(inputs_gen()):
            outputs.append(output)

        assert len(outputs) == 3

        exp_seq_num = 0
        for output in outputs:
            assert output.start_seq_num == exp_seq_num
            exp_seq_num = output.end_seq_num

    async def test_read_session_termination(self, stream: Stream):
        await stream.append(
            AppendInput(records=[Record(body=f"record-{i}".encode()) for i in range(5)])
        )

        outputs = []
        async for output in stream.read_session(
            start=SeqNum(0), limit=ReadLimit(count=2)
        ):
            outputs.append(output)

        assert len(outputs) == 1

        assert isinstance(outputs[0], list)
        assert len(outputs[0]) == 2

    async def test_read_session_tailing(self, stream: Stream):
        tail = await stream.check_tail()

        async def producer():
            await asyncio.sleep(0.5)
            await stream.append(AppendInput(records=[Record(body=b"record-0")]))

        producer_task = asyncio.create_task(producer())

        try:
            async for output in stream.read_session(
                start=SeqNum(tail.next_seq_num), clamp=True
            ):
                if isinstance(output, list) and len(output) > 0:
                    assert output[0].body == b"record-0"
                    break
        finally:
            producer_task.cancel()
