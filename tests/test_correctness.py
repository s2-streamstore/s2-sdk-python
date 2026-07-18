import asyncio
import sys

import pytest

from s2_sdk import (
    AppendInput,
    Batching,
    Record,
    Retry,
    S2Stream,
    SeqNum,
    SequencedRecord,
    TailOffset,
)

_NUM_RECORDS = 1024
_RECORD_IDX_HEADER = b"record-idx"


@pytest.fixture(scope="session")
def retry() -> Retry:
    return Retry(max_attempts=sys.maxsize)


@pytest.fixture(scope="session")
def basin_prefix() -> str:
    return "python-correctness"


@pytest.mark.correctness
@pytest.mark.asyncio
async def test_gapless_seq_nums_and_record_order_during_concurrent_append_and_read(
    stream: S2Stream,
):
    async def read_records() -> None:
        next_record_idx = 0
        last_seq_num: int | None = None
        num_records_read = 0

        async with stream.read_session(start=SeqNum(0), wait=60) as session:
            async for batch in session:
                for record in batch.records:
                    seq_num = record.seq_num
                    if last_seq_num is None:
                        assert seq_num == 0
                    else:
                        assert seq_num == last_seq_num + 1
                    last_seq_num = seq_num

                    record_idx = _record_idx(record)
                    assert 0 <= record_idx < _NUM_RECORDS
                    assert record_idx <= next_record_idx

                    if record_idx == next_record_idx:
                        next_record_idx = record_idx + 1
                    num_records_read += 1

                    if next_record_idx == _NUM_RECORDS:
                        assert last_seq_num + 1 == num_records_read
                        assert num_records_read >= _NUM_RECORDS
                        return

        pytest.fail(
            "read session ended before all records were read: "
            f"next_record_idx={next_record_idx}, "
            f"num_records_read={num_records_read}"
        )

    async def append_records() -> None:
        async with stream.producer(batching=Batching(max_records=16)) as producer:
            tickets = []
            for idx in range(_NUM_RECORDS):
                ticket = await producer.submit(_indexed_record(idx))
                tickets.append(ticket)

            for ticket in tickets:
                await ticket

    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(read_records())
        task_group.create_task(append_records())


@pytest.mark.correctness
@pytest.mark.asyncio
async def test_read_session_reports_caught_up_after_delivering_tail(stream: S2Stream):
    await stream.append(
        AppendInput(records=[Record(body=b"first"), Record(body=b"second")])
    )

    async with stream.read_session(start=TailOffset(2), wait=60) as session:
        caught_up = session.caught_up()
        records = []

        assert not session.is_caught_up()
        while not session.is_caught_up():
            records.extend((await anext(session)).records)

        tail = await caught_up
        assert [record.seq_num for record in records] == [
            tail.seq_num - 2,
            tail.seq_num - 1,
        ]


def _indexed_record(idx: int) -> Record:
    return Record(
        body=b"",
        headers=[(_RECORD_IDX_HEADER, str(idx).encode())],
    )


def _record_idx(record: SequencedRecord) -> int:
    values = [value for key, value in record.headers if key == _RECORD_IDX_HEADER]
    assert len(values) == 1
    return int(values[0])
