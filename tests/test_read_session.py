import asyncio
from collections.abc import AsyncIterator

import pytest

from s2_sdk import ReadSessionClosedError, S2ClientError
from s2_sdk._read_session import ReadSession, _ReadSessionUpdate
from s2_sdk._s2s._read_session import _read_session_update
from s2_sdk._types import ReadBatch, SequencedRecord, StreamPosition


def _record(seq_num: int, *, command: bool = False) -> SequencedRecord:
    return SequencedRecord(
        seq_num=seq_num,
        body=b"command" if command else b"record",
        headers=[(b"", b"fence")] if command else [],
        timestamp=1,
    )


async def _updates(*updates: _ReadSessionUpdate) -> AsyncIterator[_ReadSessionUpdate]:
    for update in updates:
        yield update


async def test_caught_up_follows_batch_delivery():
    tail = StreamPosition(2, 1)
    batch = ReadBatch([_record(0), _record(1)], tail)
    session = ReadSession(_updates(_ReadSessionUpdate(batch, tail)))
    pending = session.caught_up()

    await asyncio.sleep(0)
    assert not session.is_caught_up()
    assert isinstance(pending, asyncio.Future)
    assert not pending.done()

    assert await anext(session) == batch
    assert session.is_caught_up()
    assert await pending == tail
    assert await session.caught_up() == tail
    await session.close()


async def test_heartbeat_waits_for_queued_batch():
    tail = StreamPosition(2, 1)
    batch = ReadBatch([_record(0), _record(1)])
    session = ReadSession(
        _updates(
            _ReadSessionUpdate(batch),
            _ReadSessionUpdate(ReadBatch([], tail), tail),
        )
    )
    pending = session.caught_up()

    await asyncio.sleep(0)
    assert not session.is_caught_up()
    assert await anext(session) == batch
    assert not session.is_caught_up()

    assert await pending == tail
    assert session.is_caught_up()
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_filtered_command_counts_toward_caught_up():
    tail = StreamPosition(2, 1)
    update = _read_session_update(
        ReadBatch([_record(0), _record(1, command=True)], tail),
        ignore_command_records=True,
    )
    session = ReadSession(_updates(update))
    pending = session.caught_up()

    batch = await anext(session)
    assert [record.seq_num for record in batch.records] == [0]
    assert session.is_caught_up()
    assert await pending == tail
    await session.close()


async def test_caught_up_wait_survives_reconnect():
    resume = asyncio.Event()
    tail = StreamPosition(3, 1)

    async def reconnecting() -> AsyncIterator[_ReadSessionUpdate]:
        yield _ReadSessionUpdate()
        await resume.wait()
        yield _ReadSessionUpdate(ReadBatch([], tail), tail)

    session = ReadSession(reconnecting())
    pending = session.caught_up()
    await asyncio.sleep(0)

    assert not session.is_caught_up()
    assert isinstance(pending, asyncio.Future)
    assert not pending.done()
    resume.set()
    assert await pending == tail
    assert session.is_caught_up()
    await session.close()


async def test_caught_up_wait_fails_when_session_ends():
    session = ReadSession(_updates())

    with pytest.raises(ReadSessionClosedError):
        await session.caught_up()
    with pytest.raises(StopAsyncIteration):
        await anext(session)
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_close_stops_the_read():
    stopped = asyncio.Event()

    async def updates() -> AsyncIterator[_ReadSessionUpdate]:
        try:
            yield _ReadSessionUpdate(ReadBatch([_record(0)]))
            await asyncio.Event().wait()
        finally:
            stopped.set()

    session = ReadSession(updates())
    async with session:
        await asyncio.sleep(0)

    assert stopped.is_set()


async def test_close_before_read_starts():
    session = ReadSession(_updates())
    aiter(session)

    await session.close()

    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_cancelled_caught_up_wait_is_removed():
    resume = asyncio.Event()
    tail = StreamPosition(1, 1)

    async def updates() -> AsyncIterator[_ReadSessionUpdate]:
        await resume.wait()
        yield _ReadSessionUpdate(ReadBatch([], tail), tail)

    session = ReadSession(updates())
    pending = session.caught_up()
    assert isinstance(pending, asyncio.Future)
    pending.cancel()
    await asyncio.sleep(0)

    assert not session._waiters
    next_caught_up = session.caught_up()
    resume.set()
    assert await next_caught_up == tail
    await session.close()


async def test_close_propagates_caller_cancellation():
    close_started = asyncio.Event()

    class Updates:
        def __aiter__(self) -> "Updates":
            return self

        async def __anext__(self) -> _ReadSessionUpdate:
            await asyncio.Event().wait()
            raise StopAsyncIteration

        async def aclose(self) -> None:
            close_started.set()
            await asyncio.Event().wait()

    session = ReadSession(Updates())
    aiter(session)
    await asyncio.sleep(0)
    closing = asyncio.create_task(session.close())
    await close_started.wait()
    closing.cancel()

    with pytest.raises(asyncio.CancelledError):
        await closing
    with pytest.raises(StopAsyncIteration):
        await anext(session)


async def test_read_error_rejects_wait_and_iteration():
    async def updates() -> AsyncIterator[_ReadSessionUpdate]:
        raise ValueError("read failed")
        yield _ReadSessionUpdate()

    session = ReadSession(updates())
    caught_up = session.caught_up()

    with pytest.raises(S2ClientError, match="read failed") as wait_error:
        await caught_up
    with pytest.raises(S2ClientError, match="read failed") as read_error:
        await anext(session)

    assert read_error.value is wait_error.value
