"""Documentation examples for Streams page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/streams.py
Requires: S2_ACCESS_TOKEN, S2_BASIN environment variables
"""

import asyncio
import os
import time
from datetime import timedelta

from s2_sdk import (
    S2,
    AppendInput,
    Batching,
    ReadLimit,
    Record,
    SeqNum,
    TailOffset,
    Timestamp,
)

access_token = os.environ["S2_ACCESS_TOKEN"]
basin_name = os.environ["S2_BASIN"]


async def main():
    async with S2(access_token) as client:
        basin = client.basin(basin_name)
        stream_name = f"docs-streams-{int(time.time())}"

        # Ensure stream exists
        try:
            await basin.create_stream(stream_name)
        except Exception:
            pass

        # ANCHOR: simple-append
        stream = basin.stream(stream_name)
        ack = await stream.append(
            AppendInput(
                records=[
                    Record(body=b"first event"),
                    Record(body=b"second event"),
                ]
            )
        )

        # ack tells us where the records landed
        print(f"Wrote records {ack.start.seq_num} through {ack.end.seq_num - 1}")
        # ANCHOR_END: simple-append

        # ANCHOR: simple-read
        batch = await stream.read(
            start=SeqNum(0),
            limit=ReadLimit(count=100),
        )

        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
        # ANCHOR_END: simple-read

        await append_session_example(stream)
        await producer_example(stream)
        await check_tail_example(stream)

        # Cleanup
        await basin.delete_stream(stream_name)

    print("Streams examples completed")


async def append_session_example(stream):
    # ANCHOR: append-session
    async with stream.append_session() as session:
        # Submit a batch — this enqueues it and returns a ticket
        ticket = await session.submit(
            AppendInput(
                records=[
                    Record(body=b"event-1"),
                    Record(body=b"event-2"),
                ]
            )
        )

        # The ticket resolves when the batch is durable
        ack = await ticket
        print(f"Durable at seq_num {ack.start.seq_num}")
    # ANCHOR_END: append-session


async def producer_example(stream):
    # ANCHOR: producer
    async with stream.producer(
        batching=Batching(linger=timedelta(milliseconds=5)),
    ) as producer:
        # Submit individual records
        ticket = await producer.submit(Record(body=b"my event"))

        # Get the exact sequence number for this record
        ack = await ticket
        print(f"Record durable at seq_num {ack.seq_num}")
    # ANCHOR_END: producer


async def check_tail_example(stream):
    # ANCHOR: check-tail
    tail = await stream.check_tail()
    print(f"Stream has {tail.seq_num} records")
    # ANCHOR_END: check-tail


async def read_session_example(stream):
    # ANCHOR: read-session
    async for batch in stream.read_session(start=SeqNum(0)):
        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
    # ANCHOR_END: read-session


async def read_session_tail_offset(stream):
    # ANCHOR: read-session-tail-offset
    # Start reading from 10 records before the current tail
    async for batch in stream.read_session(start=TailOffset(10)):
        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
    # ANCHOR_END: read-session-tail-offset


async def read_session_timestamp(stream):
    # ANCHOR: read-session-timestamp
    # Start reading from a specific timestamp
    one_hour_ago_ms = int((time.time() - 3600) * 1000)
    async for batch in stream.read_session(start=Timestamp(one_hour_ago_ms)):
        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
    # ANCHOR_END: read-session-timestamp


async def read_session_until(stream):
    # ANCHOR: read-session-until
    # Read records until a specific timestamp
    one_hour_ago_ms = int((time.time() - 3600) * 1000)
    async for batch in stream.read_session(
        start=SeqNum(0),
        until_timestamp=one_hour_ago_ms,
    ):
        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
    # ANCHOR_END: read-session-until


async def read_session_wait(stream):
    # ANCHOR: read-session-wait
    # Read all available records, then wait up to 30 seconds for new ones
    async for batch in stream.read_session(
        start=SeqNum(0),
        wait=30,
    ):
        for record in batch.records:
            print(f"[{record.seq_num}] {record.body}")
    # ANCHOR_END: read-session-wait


if __name__ == "__main__":
    asyncio.run(main())
