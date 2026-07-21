from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Self

from s2_sdk._exceptions import S2ClientError, normalize_exception
from s2_sdk._types import ReadBatch, StreamPosition


class _ReadSessionRetrying:
    pass


@dataclass(frozen=True, slots=True)
class _ReadSessionHeartbeat:
    tail: StreamPosition


@dataclass(frozen=True, slots=True)
class _ReadSessionBatch:
    batch: ReadBatch


_ReadSessionEvent = _ReadSessionRetrying | _ReadSessionHeartbeat | _ReadSessionBatch


@dataclass(slots=True)
class _ReadDelivery:
    batch: ReadBatch
    caught_up_tail: StreamPosition | None
    delivered: asyncio.Event = field(default_factory=asyncio.Event)


class ReadSession(AsyncIterator[ReadBatch]):
    """Async iterator that yields :class:`ReadBatch` values and tracks caught-up state.

    Use it as an async context manager, or call :meth:`close` explicitly to close the session.

    Caution:
        Returned by :meth:`S2Stream.read_session`. Do not instantiate directly.
    """

    __slots__ = (
        "_caught_up_tail",
        "_closed",
        "_delivery_queue",
        "_error",
        "_ignore_command_records",
        "_task",
        "_events",
        "_caught_up_futs",
    )

    def __init__(
        self,
        events: AsyncGenerator[_ReadSessionEvent, None],
        *,
        ignore_command_records: bool = False,
    ) -> None:
        self._events = events
        self._ignore_command_records = ignore_command_records
        self._delivery_queue: asyncio.Queue[_ReadDelivery | BaseException | None] = (
            asyncio.Queue(maxsize=1)
        )
        self._task: asyncio.Task[None] | None = None
        self._closed = False
        self._error: BaseException | None = None
        self._caught_up_tail: StreamPosition | None = None
        self._caught_up_futs: set[asyncio.Future[StreamPosition]] = set()

    def is_caught_up(self) -> bool:
        """Whether this session has yielded all records with sequence numbers less than
        the sequence number of the last observed tail position.

        The stream's tail may have advanced since this session last observed it.
        Use :meth:`S2Stream.check_tail` if you need the current tail.
        """
        return self._caught_up_tail is not None

    def caught_up(self) -> Awaitable[StreamPosition]:
        """Return an awaitable that resolves to a tail position once this session is caught up to it.

        See :meth:`is_caught_up` for the semantics of caught up.

        This awaitable only signals that the session is caught up. To yield batches, continue
        iterating over the session.
        """
        loop = asyncio.get_running_loop()
        caught_up_fut: asyncio.Future[StreamPosition] = loop.create_future()
        if self._caught_up_tail is not None:
            caught_up_fut.set_result(_copy_position(self._caught_up_tail))
        elif self._closed:
            caught_up_fut.set_exception(
                self._error if self._error is not None else _session_closed_error()
            )
        else:
            self._caught_up_futs.add(caught_up_fut)
            caught_up_fut.add_done_callback(self._caught_up_futs.discard)
            self._ensure_started()
        return caught_up_fut

    async def close(self) -> None:
        """Close the session."""
        if self._closed:
            return
        if self._task is None:
            self._finish()
            return
        current = asyncio.current_task()
        cancellation_count = current.cancelling() if current is not None else 0
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        if not self._closed:
            self._finish()
        if current is not None and current.cancelling() > cancellation_count:
            raise asyncio.CancelledError

    def __aiter__(self) -> Self:
        self._ensure_started()
        return self

    async def __anext__(self) -> ReadBatch:
        session = self.__aiter__()
        try:
            delivery = await session._delivery_queue.get()
        except asyncio.CancelledError:
            await self.close()
            raise

        if delivery is None:
            self._delivery_queue.put_nowait(None)
            raise StopAsyncIteration
        if isinstance(delivery, BaseException):
            self._delivery_queue.put_nowait(None)
            raise delivery

        if delivery.caught_up_tail is not None:
            self._mark_caught_up(delivery.caught_up_tail)
        delivery.delivered.set()
        return delivery.batch

    async def __aenter__(self) -> Self:
        return self.__aiter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False

    def _ensure_started(self) -> None:
        if self._task is None and not self._closed:
            self._task = asyncio.get_running_loop().create_task(self._run())

    async def _run(self) -> None:
        error: BaseException | None = None
        cancelled = False
        events = self._events
        try:
            async for event in events:
                await self._handle_event(event)
        except asyncio.CancelledError:
            cancelled = True
        except BaseException as exc:
            error = normalize_exception(exc)
        finally:
            try:
                await events.aclose()
            except BaseException as exc:
                if error is None and not cancelled:
                    error = normalize_exception(exc)
            self._finish(error)

    async def _handle_event(self, event: _ReadSessionEvent) -> None:
        if isinstance(event, _ReadSessionRetrying):
            self._mark_not_caught_up()
        elif isinstance(event, _ReadSessionHeartbeat):
            self._mark_caught_up(event.tail)
        else:
            batch = event.batch
            caught_up_tail = (
                batch.tail
                if batch.tail is not None
                and batch.records[-1].seq_num + 1 == batch.tail.seq_num
                else None
            )

            if self._ignore_command_records:
                batch = ReadBatch(
                    records=[r for r in batch.records if not r.is_command_record()],
                    tail=batch.tail,
                )

            if batch.records:
                self._mark_not_caught_up()
                delivery = _ReadDelivery(batch, caught_up_tail)
                await self._delivery_queue.put(delivery)
                await delivery.delivered.wait()
            elif caught_up_tail is not None:
                self._mark_caught_up(caught_up_tail)
            else:
                self._mark_not_caught_up()

    def _mark_caught_up(self, tail: StreamPosition) -> None:
        if self._closed:
            return
        self._caught_up_tail = _copy_position(tail)
        caught_up_futs = tuple(self._caught_up_futs)
        self._caught_up_futs.clear()
        for caught_up_fut in caught_up_futs:
            if not caught_up_fut.done():
                caught_up_fut.set_result(_copy_position(tail))

    def _mark_not_caught_up(self) -> None:
        if not self._closed:
            self._caught_up_tail = None

    def _finish(self, error: BaseException | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        self._error = error
        if self._error is not None:
            self._caught_up_tail = None
        caught_up_futs = tuple(self._caught_up_futs)
        self._caught_up_futs.clear()
        for caught_up_fut in caught_up_futs:
            if not caught_up_fut.done():
                caught_up_fut.set_exception(
                    self._error if self._error is not None else _session_closed_error()
                )

        while not self._delivery_queue.empty():
            self._delivery_queue.get_nowait()
        self._delivery_queue.put_nowait(self._error)


def _copy_position(position: StreamPosition) -> StreamPosition:
    return StreamPosition(position.seq_num, position.timestamp)


def _session_closed_error() -> S2ClientError:
    return S2ClientError("ReadSession is closed")
