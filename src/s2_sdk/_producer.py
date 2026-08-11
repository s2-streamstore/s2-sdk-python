from __future__ import annotations

import asyncio
from collections import deque
from contextlib import suppress
from dataclasses import dataclass
from typing import Self

from s2_sdk._append_session import AppendSession, BatchSubmitTicket
from s2_sdk._batching import BatchAccumulator
from s2_sdk._client import HttpClient
from s2_sdk._exceptions import S2ClientError, fallible, normalize_exception
from s2_sdk._types import (
    AppendAck,
    AppendInput,
    Batching,
    Compression,
    IndexedAppendAck,
    Record,
    Retry,
)


@dataclass(slots=True)
class _UnackedBatch:
    ticket: BatchSubmitTicket
    indexed_ack_futs: tuple[asyncio.Future[IndexedAppendAck], ...]


def _retrieve_task_exception(task: asyncio.Task[None]) -> None:
    with suppress(asyncio.CancelledError):
        task.exception()


class Producer:
    """High-level interface for submitting individual records.

    Handles batching into :class:`AppendInput` automatically and uses an
    append session internally.

    Use it as an async context manager, or call :meth:`close` explicitly to close the producer.

    Caution:
        Returned by :meth:`S2Stream.producer`. Do not instantiate directly.
    """

    __slots__ = (
        "_accumulator",
        "_indexed_ack_futs",
        "_batch_ready",
        "_closed",
        "_drain_task",
        "_error",
        "_final_flush_done",
        "_fencing_token",
        "_linger_task",
        "_match_seq_num",
        "_operation_lock",
        "_pending_ack_futs",
        "_unacked",
        "_session",
    )

    def __init__(
        self,
        client: HttpClient,
        stream_name: str,
        retry: Retry,
        compression: Compression,
        fencing_token: str | None,
        match_seq_num: int | None,
        max_unacked_bytes: int,
        batching: Batching,
        encryption_key: str | None = None,
    ) -> None:
        self._session = AppendSession(
            client=client,
            stream_name=stream_name,
            retry=retry,
            compression=compression,
            max_unacked_bytes=max_unacked_bytes,
            max_unacked_batches=None,
            encryption_key=encryption_key,
        )
        self._fencing_token = fencing_token
        self._match_seq_num = match_seq_num
        self._accumulator = BatchAccumulator(batching)

        self._indexed_ack_futs: list[asyncio.Future[IndexedAppendAck]] = []
        self._operation_lock = asyncio.Lock()
        self._pending_ack_futs: set[asyncio.Future[IndexedAppendAck]] = set()
        self._linger_task: asyncio.Task[None] | None = None
        self._unacked: deque[_UnackedBatch] = deque()
        self._batch_ready = asyncio.Event()
        self._drain_task = asyncio.get_running_loop().create_task(self._drain_acks())
        self._closed = False
        self._final_flush_done = False
        self._error: BaseException | None = None

    @fallible
    async def submit(self, record: Record) -> RecordSubmitTicket:
        """Submit a record for appending.

        Waits when backpressure limits are reached. Await the returned ticket
        for this record's acknowledgement, or call :meth:`flush` to wait for
        all previously submitted records.
        """
        async with self._operation_lock:
            self._check_ready()

            loop = asyncio.get_running_loop()
            ack_fut: asyncio.Future[IndexedAppendAck] = loop.create_future()
            self._indexed_ack_futs.append(ack_fut)
            self._pending_ack_futs.add(ack_fut)
            ack_fut.add_done_callback(self._pending_ack_futs.discard)

            first_in_batch = self._accumulator.is_empty()
            self._accumulator.add(record)
            if self._accumulator.is_full():
                await self._flush_current_batch()
            elif first_in_batch and self._accumulator.linger > 0:
                self._linger_task = loop.create_task(self._flush_after_linger())

            return RecordSubmitTicket(ack_fut)

    @fallible
    async def flush(self) -> None:
        """Flush pending records and wait for prior submissions to become durable.

        Records submitted before this operation are included. Concurrent
        submissions may fall on either side of the flush boundary.

        An empty flush returns immediately. A successful flush leaves the
        producer open for further submissions. An append failure is terminal,
        and subsequent calls to :meth:`submit`, :meth:`flush`, and
        :meth:`close` raise the same error. Canceling the caller's wait does not
        cancel the flush operation or the submitted records.
        """
        flush_task = asyncio.create_task(self._flush_and_wait())
        try:
            await asyncio.shield(flush_task)
        except asyncio.CancelledError:
            flush_task.add_done_callback(_retrieve_task_exception)
            raise

    async def _flush_and_wait(self) -> None:
        async with self._operation_lock:
            self._check_ready()
            ack_futs_to_wait = tuple(self._pending_ack_futs)
            await self._flush_current_batch()

            if self._error is not None:
                raise self._error
            if not ack_futs_to_wait:
                return

            results = await asyncio.shield(
                asyncio.gather(*ack_futs_to_wait, return_exceptions=True)
            )
            for result in results:
                if isinstance(result, BaseException):
                    raise result

    @fallible
    async def close(self) -> None:
        """Close the producer and wait for all submitted records to become durable."""
        async with self._operation_lock:
            if self._closed:
                if self._error is not None:
                    raise self._error
                return
            self._closed = True
            try:
                if self._error is None:
                    try:
                        await self._flush_current_batch()
                    except BaseException as e:
                        self._fail(e)
                try:
                    await self._session.close()
                except BaseException as e:
                    self._fail(e)
            finally:
                self._final_flush_done = True
                self._batch_ready.set()
                try:
                    await self._drain_task
                except BaseException as e:
                    self._fail(e)
            if self._error is not None:
                raise self._error

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False

    def _check_ready(self) -> None:
        if self._error is not None:
            raise self._error
        if self._closed:
            raise S2ClientError("Producer is closed")

    async def _flush_current_batch(self) -> None:
        await self._cancel_linger_task()
        await self._submit_accumulated_records()

    async def _submit_accumulated_records(self) -> None:
        if self._accumulator.is_empty():
            return

        records = self._accumulator.take()
        indexed_ack_futs = tuple(self._indexed_ack_futs)
        self._indexed_ack_futs.clear()

        batch = AppendInput(
            records=records,
            fencing_token=self._fencing_token,
            match_seq_num=self._match_seq_num,
        )
        if self._match_seq_num is not None:
            self._match_seq_num += len(records)

        try:
            ticket = await self._session.submit(batch)
        except BaseException as e:
            error = self._fail(e)
            for ack_fut in indexed_ack_futs:
                # Suppress "Future exception was never retrieved" for the
                # record whose submit call raised before returning its ticket.
                ack_fut.exception()
            raise error

        self._unacked.append(
            _UnackedBatch(ticket=ticket, indexed_ack_futs=indexed_ack_futs)
        )
        self._batch_ready.set()

    async def _cancel_linger_task(self) -> None:
        linger_task = self._linger_task
        if linger_task is None:
            return
        self._linger_task = None
        if linger_task is asyncio.current_task():
            return
        linger_task.cancel()
        with suppress(asyncio.CancelledError):
            await linger_task

    async def _drain_acks(self) -> None:
        """Single background task that resolves batches in FIFO order."""
        while True:
            while not self._unacked:
                if self._closed and self._final_flush_done:
                    return
                self._batch_ready.clear()
                if self._unacked:
                    break
                await self._batch_ready.wait()

            unacked = self._unacked.popleft()
            try:
                ack: AppendAck = await unacked.ticket  # type: ignore[assignment]
                for i, ack_fut in enumerate(unacked.indexed_ack_futs):
                    if not ack_fut.done():
                        ack_fut.set_result(
                            IndexedAppendAck(
                                seq_num=ack.start.seq_num + i,
                                batch=ack,
                            )
                        )
            except BaseException as e:
                self._fail(e)
                self._unacked.clear()
                return

    async def _flush_after_linger(self) -> None:
        assert self._accumulator.linger is not None
        await asyncio.sleep(self._accumulator.linger)
        async with self._operation_lock:
            if self._linger_task is not asyncio.current_task():
                return
            self._linger_task = None
            if self._closed or self._error is not None:
                return
            try:
                await self._submit_accumulated_records()
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._fail(e)

    def _fail(self, cause: BaseException) -> BaseException:
        if self._error is None:
            self._error = normalize_exception(cause)
        error = self._error

        linger_task = self._linger_task
        self._linger_task = None
        if linger_task is not None and linger_task is not asyncio.current_task():
            linger_task.cancel()

        self._accumulator.take()
        self._indexed_ack_futs.clear()
        for ack_fut in tuple(self._pending_ack_futs):
            if not ack_fut.done():
                ack_fut.set_exception(error)

        return error


class RecordSubmitTicket:
    """Awaitable that resolves to an :class:`IndexedAppendAck` once the record is durable."""

    __slots__ = ("_ack_fut",)

    def __init__(self, ack_fut: asyncio.Future[IndexedAppendAck]) -> None:
        self._ack_fut = ack_fut

    def __await__(self):
        return asyncio.shield(self._ack_fut).__await__()
