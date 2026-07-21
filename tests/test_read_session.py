import asyncio
from collections.abc import AsyncGenerator

import pytest

from s2_sdk import S2ClientError
from s2_sdk._read_session import (
    ReadSession,
    _ReadSessionBatch,
    _ReadSessionEvent,
    _ReadSessionHeartbeat,
    _ReadSessionRetrying,
)
from s2_sdk._types import ReadBatch, SequencedRecord, StreamPosition


def _record(seq_num: int, *, command: bool = False) -> SequencedRecord:
    return SequencedRecord(
        seq_num=seq_num,
        body=b"command" if command else b"record",
        headers=[(b"", b"fence")] if command else [],
        timestamp=1,
    )


async def _events(
    *events: _ReadSessionEvent,
) -> AsyncGenerator[_ReadSessionEvent, None]:
    for event in events:
        yield event


async def test_batch_with_tail_marks_caught_up():
    tail = StreamPosition(2, 1)
    batch = ReadBatch([_record(0), _record(1)], tail)
    session = ReadSession(_events(_ReadSessionBatch(batch)))
    caught_up = session.caught_up()

    await asyncio.sleep(0)
    assert not session.is_caught_up()

    assert await anext(session) == batch
    assert session.is_caught_up()
    assert await caught_up == tail
    assert await session.caught_up() == tail
    await session.close()


async def test_heartbeat_marks_caught_up_after_batch_without_tail():
    tail = StreamPosition(2, 1)
    batch = ReadBatch([_record(0), _record(1)])
    session = ReadSession(
        _events(
            _ReadSessionBatch(batch),
            _ReadSessionHeartbeat(tail),
        )
    )
    caught_up = session.caught_up()

    await asyncio.sleep(0)
    assert not session.is_caught_up()

    assert await anext(session) == batch
    assert not session.is_caught_up()
    assert await caught_up == tail
    assert session.is_caught_up()
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_filtered_command_record_still_counts_toward_caught_up():
    tail = StreamPosition(2, 1)
    batch = ReadBatch([_record(0), _record(1, command=True)], tail)
    session = ReadSession(
        _events(_ReadSessionBatch(batch)), ignore_command_records=True
    )
    caught_up = session.caught_up()

    batch = await anext(session)
    assert [record.seq_num for record in batch.records] == [0]
    assert session.is_caught_up()
    assert await caught_up == tail
    await session.close()


async def test_caught_up_resolves_after_session_retry():
    allow_heartbeat = asyncio.Event()
    tail = StreamPosition(3, 1)

    async def retry_then_heartbeat() -> AsyncGenerator[_ReadSessionEvent, None]:
        yield _ReadSessionRetrying()
        await allow_heartbeat.wait()
        yield _ReadSessionHeartbeat(tail)

    session = ReadSession(retry_then_heartbeat())
    caught_up = session.caught_up()

    await asyncio.sleep(0)
    assert not session.is_caught_up()

    allow_heartbeat.set()

    assert await caught_up == tail
    assert session.is_caught_up()
    await session.close()


async def test_caught_up_fails_when_session_ends():
    session = ReadSession(_events())

    with pytest.raises(S2ClientError, match="ReadSession is closed"):
        await session.caught_up()
    with pytest.raises(StopAsyncIteration):
        await anext(session)
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_context_exit_stops_read_events():
    stopped = asyncio.Event()

    async def read_events_until_stopped() -> AsyncGenerator[_ReadSessionEvent, None]:
        try:
            yield _ReadSessionBatch(ReadBatch([_record(0)]))
            await asyncio.Event().wait()
        finally:
            stopped.set()

    session = ReadSession(read_events_until_stopped())
    async with session:
        await asyncio.sleep(0)

    assert stopped.is_set()


async def test_close_before_read_starts():
    session = ReadSession(_events())

    await session.close()

    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_cancelled_caught_up_await_does_not_affect_other_awaits():
    allow_heartbeat = asyncio.Event()
    tail = StreamPosition(1, 1)

    async def delayed_heartbeat() -> AsyncGenerator[_ReadSessionEvent, None]:
        await allow_heartbeat.wait()
        yield _ReadSessionHeartbeat(tail)

    session = ReadSession(delayed_heartbeat())
    caught_up_1 = asyncio.ensure_future(session.caught_up())
    caught_up_2 = asyncio.ensure_future(session.caught_up())
    await asyncio.sleep(0)
    caught_up_1.cancel()

    with pytest.raises(asyncio.CancelledError):
        await caught_up_1

    allow_heartbeat.set()
    assert await caught_up_2 == tail
    await session.close()


async def test_close_does_not_swallow_caller_cancellation():
    read_cleanup_started = asyncio.Event()

    async def blocked_read_events() -> AsyncGenerator[_ReadSessionEvent, None]:
        try:
            await asyncio.Event().wait()
        finally:
            read_cleanup_started.set()
            await asyncio.Event().wait()
        yield _ReadSessionRetrying()

    session = ReadSession(blocked_read_events())
    aiter(session)
    await asyncio.sleep(0)

    close_task = asyncio.create_task(session.close())
    await read_cleanup_started.wait()
    close_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await close_task
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_read_error_fails_caught_up_and_iteration():
    async def failing_read_events() -> AsyncGenerator[_ReadSessionEvent, None]:
        raise ValueError("read failed")
        yield _ReadSessionRetrying()

    session = ReadSession(failing_read_events())
    caught_up = session.caught_up()

    with pytest.raises(S2ClientError, match="read failed") as caught_up_error:
        await caught_up
    with pytest.raises(S2ClientError, match="read failed") as read_error:
        await anext(session)

    assert read_error.value is caught_up_error.value
