from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable, AsyncIterator, Awaitable
from dataclasses import dataclass, field
from typing import Self

from s2_sdk._exceptions import ReadSessionClosedError, normalize_exception
from s2_sdk._types import ReadBatch, StreamPosition


@dataclass(slots=True)
class _ReadSessionUpdate:
    batch: ReadBatch | None = None
    caught_up_tail: StreamPosition | None = None


@dataclass(slots=True)
class _ReadDelivery:
    batch: ReadBatch
    caught_up_tail: StreamPosition | None
    consumed: asyncio.Event = field(default_factory=asyncio.Event)


class _End:
    pass


_END = _End()


class ReadSession(AsyncIterator[ReadBatch]):
    """A continuous read returned by :meth:`S2Stream.read_session`.

    Use as an async context manager or call :meth:`close`.
    """

    __slots__ = (
        "_caught_up_tail",
        "_closed",
        "_deliveries",
        "_error",
        "_error_raised",
        "_is_caught_up",
        "_task",
        "_updates",
        "_waiters",
    )

    def __init__(self, updates: AsyncIterable[_ReadSessionUpdate]) -> None:
        self._updates = updates
        self._deliveries: asyncio.Queue[_ReadDelivery | _End] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._closed = False
        self._error: BaseException | None = None
        self._error_raised = False
        self._is_caught_up = False
        self._caught_up_tail: StreamPosition | None = None
        self._waiters: set[asyncio.Future[StreamPosition]] = set()

    def is_caught_up(self) -> bool:
        """Return whether all records through the latest reported tail were delivered.

        A later batch that does not reach a reported tail or a reconnect resets it.
        Filtered command records count toward progress. Use
        :meth:`S2Stream.check_tail` for the current stream tail.
        """
        return self._is_caught_up

    def caught_up(self) -> Awaitable[StreamPosition]:
        """Return an awaitable for the next caught-up tail.

        It resolves immediately if already caught up and remains pending across
        retries. Keep consuming batches while waiting. Call again after falling
        behind.

        Raises:
            ReadSessionClosedError: The session ended before catching up.
            S2Error: The read failed before catching up.
        """
        loop = asyncio.get_running_loop()
        waiter: asyncio.Future[StreamPosition] = loop.create_future()
        if self._is_caught_up and self._caught_up_tail is not None:
            waiter.set_result(_copy_position(self._caught_up_tail))
        elif self._closed:
            waiter.set_exception(self._error or _session_closed_error())
        else:
            self._waiters.add(waiter)
            waiter.add_done_callback(self._waiters.discard)
            self._ensure_started()
        return waiter

    async def close(self) -> None:
        """Close the session."""
        if self._closed:
            return
        if self._task is None:
            self._finish()
            self._signal_end()
            return
        current = asyncio.current_task()
        cancellation_count = current.cancelling() if current is not None else 0
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            if not self._closed:
                self._finish()
                self._signal_end()
        if current is not None and current.cancelling() > cancellation_count:
            raise asyncio.CancelledError

    async def aclose(self) -> None:
        """Close the session."""
        await self.close()

    def __aiter__(self) -> Self:
        self._ensure_started()
        return self

    async def __anext__(self) -> ReadBatch:
        self._ensure_started()
        try:
            item = await self._deliveries.get()
        except asyncio.CancelledError:
            await self.close()
            raise

        if isinstance(item, _End):
            self._deliveries.put_nowait(_END)
            if self._error is not None and not self._error_raised:
                self._error_raised = True
                raise self._error
            raise StopAsyncIteration

        if item.caught_up_tail is not None:
            self._mark_caught_up(item.caught_up_tail)
        item.consumed.set()
        return item.batch

    async def __aenter__(self) -> Self:
        self._ensure_started()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False

    def _ensure_started(self) -> None:
        if self._task is None and not self._closed:
            self._task = asyncio.get_running_loop().create_task(self._run())

    async def _run(self) -> None:
        error: BaseException | None = None
        cancelled = False
        updates = aiter(self._updates)
        try:
            async for update in updates:
                self._mark_behind()
                batch = update.batch
                if batch is None or not batch.records:
                    if update.caught_up_tail is not None:
                        self._mark_caught_up(update.caught_up_tail)
                    continue

                delivery = _ReadDelivery(batch, update.caught_up_tail)
                await self._deliveries.put(delivery)
                await delivery.consumed.wait()
        except asyncio.CancelledError:
            cancelled = True
        except BaseException as exc:
            error = normalize_exception(exc)
        finally:
            close = getattr(updates, "aclose", None)
            if close is not None:
                try:
                    await close()
                except BaseException as exc:
                    if error is None and not cancelled:
                        error = normalize_exception(exc)
            self._finish(error)
            self._signal_end()

    def _mark_caught_up(self, tail: StreamPosition) -> None:
        if self._closed:
            return
        self._is_caught_up = True
        self._caught_up_tail = _copy_position(tail)
        waiters = tuple(self._waiters)
        self._waiters.clear()
        for waiter in waiters:
            if not waiter.done():
                waiter.set_result(_copy_position(tail))

    def _mark_behind(self) -> None:
        if not self._closed:
            self._is_caught_up = False

    def _finish(self, error: BaseException | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        self._error = error
        if error is not None:
            self._is_caught_up = False
        waiters = tuple(self._waiters)
        self._waiters.clear()
        rejection = error or _session_closed_error()
        for waiter in waiters:
            if not waiter.done():
                waiter.set_exception(rejection)

    def _signal_end(self) -> None:
        while not self._deliveries.empty():
            self._deliveries.get_nowait()
        self._deliveries.put_nowait(_END)


def _copy_position(position: StreamPosition) -> StreamPosition:
    return StreamPosition(position.seq_num, position.timestamp)


def _session_closed_error() -> ReadSessionClosedError:
    return ReadSessionClosedError("Read session ended before catching up")
