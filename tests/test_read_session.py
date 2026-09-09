import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import patch

import pytest

import s2_sdk._generated.s2.v1.s2_pb2 as pb
import s2_sdk._s2s._read_session as s2s_read_session
from s2_sdk import S2ClientError
from s2_sdk._client import HttpClient
from s2_sdk._read_session import (
    ReadSession,
    _ReadSessionBatch,
    _ReadSessionEvent,
    _ReadSessionHeartbeat,
    _ReadSessionRetrying,
)
from s2_sdk._s2s._protocol import Message
from s2_sdk._types import (
    Compression,
    ReadBatch,
    ReadLimit,
    Retry,
    SeqNum,
    SequencedRecord,
    StreamPosition,
)


@dataclass(slots=True)
class _Response:
    messages: tuple[Message, ...]
    status_code: int = 200
    retired: bool = False

    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        for message in self.messages:
            yield cast(bytes, message)

    def retire_connection(self) -> None:
        self.retired = True


class _Client:
    def __init__(self, attempts: list[tuple[Message, ...]]) -> None:
        self.attempts = attempts
        self.requests: list[dict[str, Any]] = []
        self.responses: list[_Response] = []

    @asynccontextmanager
    async def streaming_request(
        self,
        *args: Any,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[_Response, None]:
        self.requests.append(dict(params or {}))
        response = _Response(self.attempts.pop(0))
        self.responses.append(response)
        yield response


def _batch_message(seq_num: int, *, reconnect_advised: bool = False) -> Message:
    batch = pb.ReadBatch(
        records=[pb.SequencedRecord(seq_num=seq_num, timestamp=1, body=b"x")]
    )
    return Message(
        batch.SerializeToString(),
        terminal=False,
        compression=Compression.NONE,
        reconnect_advised=reconnect_advised,
    )


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


def _decoded_messages(stream: AsyncIterator[bytes]) -> AsyncIterator[Message]:
    return cast(AsyncIterator[Message], stream)


async def _run_s2s_read(client: _Client, count: int) -> list[_ReadSessionEvent]:
    return [
        event
        async for event in s2s_read_session.run_read_session(
            cast(HttpClient, client),
            "stream",
            SeqNum(10),
            ReadLimit(count=count),
            until_timestamp=None,
            clamp_to_tail=False,
            wait=None,
            retry=Retry(max_attempts=1),
        )
    ]


async def test_advised_reconnect_resumes_from_next_seq_num() -> None:
    client = _Client(
        [
            (_batch_message(10, reconnect_advised=True),),
            (_batch_message(11),),
        ]
    )

    with patch.object(s2s_read_session, "read_messages", new=_decoded_messages):
        events = await _run_s2s_read(client, count=2)

    assert isinstance(events[0], _ReadSessionBatch)
    assert isinstance(events[1], _ReadSessionRetrying)
    assert isinstance(events[2], _ReadSessionBatch)
    assert events[0].batch.records[0].seq_num == 10
    assert events[2].batch.records[0].seq_num == 11
    assert client.requests[1] == {"seq_num": 11, "count": 1}
    assert client.responses[0].retired


async def test_repeated_reconnect_advice_does_not_reconnect_again() -> None:
    client = _Client(
        [
            (_batch_message(10, reconnect_advised=True),),
            (_batch_message(11, reconnect_advised=True), _batch_message(12)),
        ]
    )

    with patch.object(s2s_read_session, "read_messages", new=_decoded_messages):
        events = await _run_s2s_read(client, count=3)

    batches = [event for event in events if isinstance(event, _ReadSessionBatch)]
    assert [batch.batch.records[0].seq_num for batch in batches] == [10, 11, 12]
    assert len(client.requests) == 2
    assert client.responses[1].retired
