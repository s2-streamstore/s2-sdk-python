import asyncio
import sys

import pytest

from s2_sdk import Batching, ReadLimit, Record, Retry, S2Stream, SeqNum

TOTAL_RECORDS = 1024


@pytest.fixture(scope="session")
def retry() -> Retry:
    return Retry(max_attempts=sys.maxsize)


@pytest.fixture(scope="session")
def basin_prefix() -> str:
    return "python-correctness"


@pytest.mark.correctness
@pytest.mark.asyncio
async def test_concurrent_producer_and_consumer_remain_gapless(stream: S2Stream):
    async def read_records() -> None:
        highest_contiguous_index = -1
        last_seq_num: int | None = None
        observed_records = 0

        async for batch in stream.read_session(
            start=SeqNum(0), limit=ReadLimit(count=TOTAL_RECORDS), wait=60
        ):
            for record in batch.records:
                assert observed_records < TOTAL_RECORDS

                seq_num = record.seq_num
                if last_seq_num is None:
                    assert seq_num == 0
                else:
                    assert seq_num == last_seq_num + 1
                last_seq_num = seq_num

                body = record.body.decode()
                index = int(body)
                assert 0 <= index < TOTAL_RECORDS
                assert index <= highest_contiguous_index + 1

                if index == highest_contiguous_index + 1:
                    highest_contiguous_index = index
                observed_records += 1

        assert highest_contiguous_index == TOTAL_RECORDS - 1
        assert last_seq_num == TOTAL_RECORDS - 1
        assert observed_records == TOTAL_RECORDS

    async def append_records() -> None:
        async with stream.producer(batching=Batching(max_records=16)) as producer:
            tickets = []
            for i in range(TOTAL_RECORDS):
                ticket = await producer.submit(Record(body=str(i).encode()))
                tickets.append(ticket)

            for ticket in tickets:
                ack = await ticket
                assert ack.seq_num >= 0

    async with asyncio.TaskGroup() as task_group:
        task_group.create_task(read_records())
        task_group.create_task(append_records())
