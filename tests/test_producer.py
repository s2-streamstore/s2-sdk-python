import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from datetime import timedelta
from typing import TypeVar
from unittest.mock import MagicMock, patch

import pytest

from s2_sdk import (
    AppendAck,
    AppendInput,
    Batching,
    BatchSubmitTicket,
    Compression,
    Producer,
    Record,
    RecordSubmitTicket,
    Retry,
    S2ClientError,
    S2Error,
    SeqNumMismatchError,
    StreamPosition,
)

_TEST_TIMEOUT = 1
_T = TypeVar("_T")


@dataclass(slots=True)
class _PendingAppend:
    append_input: AppendInput
    ack_fut: asyncio.Future[AppendAck]

    def resolve(self, ack: AppendAck) -> None:
        self.ack_fut.set_result(ack)

    def reject(self, error: BaseException) -> None:
        self.ack_fut.set_exception(error)


class _TestAppendSession:
    def __init__(
        self,
        *,
        fail_on_submit: int | None = None,
        submit_error: BaseException | None = None,
    ) -> None:
        self.pending_appends: asyncio.Queue[_PendingAppend] = asyncio.Queue()
        self._fail_on_submit = fail_on_submit
        self._submit_error = submit_error
        self._submit_count = 0
        self._closed = False

    async def submit(self, append_input: AppendInput) -> BatchSubmitTicket:
        if self._closed:
            raise S2ClientError("AppendSession is closed")
        self._submit_count += 1
        if self._submit_count == self._fail_on_submit:
            assert self._submit_error is not None
            raise self._submit_error

        ack_fut: asyncio.Future[AppendAck] = asyncio.get_running_loop().create_future()
        self.pending_appends.put_nowait(_PendingAppend(append_input, ack_fut))
        return BatchSubmitTicket(ack_fut)

    async def close(self) -> None:
        self._closed = True


def _producer(
    session: _TestAppendSession,
    *,
    batching: Batching,
) -> Producer:
    with patch("s2_sdk._producer.AppendSession", return_value=session):
        return Producer(
            client=MagicMock(),
            stream_name="test-stream",
            retry=Retry(),
            compression=Compression.NONE,
            fencing_token=None,
            match_seq_num=None,
            max_unacked_bytes=5 * 1024 * 1024,
            batching=batching,
        )


async def _next_append(session: _TestAppendSession) -> _PendingAppend:
    async with asyncio.timeout(_TEST_TIMEOUT):
        return await session.pending_appends.get()


async def _wait_for(awaitable: Awaitable[_T]) -> _T:
    async with asyncio.timeout(_TEST_TIMEOUT):
        return await awaitable


def _make_ack(start_seq_num: int, record_count: int) -> AppendAck:
    end_seq_num = start_seq_num + record_count
    return AppendAck(
        start=StreamPosition(seq_num=start_seq_num, timestamp=1),
        end=StreamPosition(seq_num=end_seq_num, timestamp=1),
        tail=StreamPosition(seq_num=end_seq_num, timestamp=1),
    )


async def test_flush_emits_partial_batch_and_waits_for_prior_acks():
    session = _TestAppendSession()
    producer = _producer(
        session,
        batching=Batching(max_records=2, linger=timedelta(hours=1)),
    )

    tickets = [
        await producer.submit(Record(body=body)) for body in (b"one", b"two", b"three")
    ]

    cancelled_waiter = asyncio.ensure_future(tickets[2])
    await asyncio.sleep(0)
    cancelled_waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await cancelled_waiter

    flush_task = asyncio.create_task(producer.flush())

    full_append = await _next_append(session)
    partial_append = await _next_append(session)
    assert [
        len(full_append.append_input.records),
        len(partial_append.append_input.records),
    ] == [2, 1]

    full_ack = _make_ack(41, 2)
    full_append.resolve(full_ack)
    first_ack, second_ack = await asyncio.gather(*tickets[:2])
    assert not flush_task.done()

    partial_ack = _make_ack(43, 1)
    partial_append.resolve(partial_ack)
    await _wait_for(flush_task)
    third_ack = await tickets[2]

    assert [first_ack.seq_num, second_ack.seq_num, third_ack.seq_num] == [41, 42, 43]
    assert first_ack.batch is full_ack
    assert second_ack.batch is full_ack
    assert third_ack.batch is partial_ack
    await producer.close()


async def test_flush_is_reusable_and_excludes_later_submissions():
    session = _TestAppendSession()
    producer = _producer(
        session,
        batching=Batching(max_records=100, linger=timedelta(hours=1)),
    )

    await _wait_for(asyncio.create_task(producer.flush()))
    assert session.pending_appends.empty()

    first_ticket = await producer.submit(Record(body=b"before"))
    first_flush_task = asyncio.create_task(producer.flush())
    first_append = await _next_append(session)

    later_submit_task = asyncio.create_task(producer.submit(Record(body=b"after")))
    await asyncio.sleep(0)
    first_flush_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first_flush_task
    assert not later_submit_task.done()

    first_append.resolve(_make_ack(0, 1))
    later_ticket = await _wait_for(later_submit_task)
    assert session.pending_appends.empty()

    second_flush_task = asyncio.create_task(producer.flush())
    second_append = await _next_append(session)
    second_append.resolve(_make_ack(1, 1))
    await _wait_for(second_flush_task)

    assert (await first_ticket).seq_num == 0
    assert (await later_ticket).seq_num == 1
    await producer.close()


@pytest.mark.parametrize("failure_phase", ["submit", "ack"])
async def test_flush_propagates_terminal_failure_to_pending_tickets(
    failure_phase: str,
):
    error = (
        SeqNumMismatchError(
            "seq_num_mismatch",
            "expected sequence number 7",
            412,
            expected_seq_num=7,
        )
        if failure_phase == "submit"
        else S2ClientError("connection closed before acknowledgement")
    )
    session = _TestAppendSession(
        fail_on_submit=2 if failure_phase == "submit" else None,
        submit_error=error,
    )
    producer = _producer(
        session,
        batching=Batching(
            max_records=2 if failure_phase == "submit" else 1,
            linger=timedelta(hours=1),
        ),
    )

    tickets: list[RecordSubmitTicket] = []
    tickets.append(await producer.submit(Record(body=b"one")))
    tickets.append(await producer.submit(Record(body=b"two")))
    first_append = await _next_append(session)
    close_task: asyncio.Task[None] | None = None

    if failure_phase == "submit":
        tickets.append(await producer.submit(Record(body=b"three")))
        flush_task = asyncio.create_task(producer.flush())
    else:
        await _next_append(session)
        flush_task = asyncio.create_task(producer.flush())
        await asyncio.sleep(0)
        assert not flush_task.done()
        close_task = asyncio.create_task(producer.close())
        await asyncio.sleep(0)
        assert not close_task.done()
        first_append.reject(error)

    with pytest.raises(S2Error) as flush_exc:
        await _wait_for(flush_task)
    assert flush_exc.value is error

    for ticket in tickets:
        with pytest.raises(S2Error) as ticket_exc:
            await ticket
        assert ticket_exc.value is error

    with pytest.raises(S2Error) as repeated_flush_exc:
        await producer.flush()
    assert repeated_flush_exc.value is error

    with pytest.raises(S2Error) as submit_exc:
        await producer.submit(Record(body=b"rejected"))
    assert submit_exc.value is error

    if failure_phase == "submit":
        first_append.resolve(_make_ack(0, 2))
        close_task = asyncio.create_task(producer.close())
    assert close_task is not None
    with pytest.raises(S2Error) as close_exc:
        await _wait_for(close_task)
    assert close_exc.value is error
