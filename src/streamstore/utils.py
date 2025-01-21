__all__ = ["CommandRecord", "metered_bytes", "append_inputs_gen"]

from asyncio import Queue, Task, create_task, sleep
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import AsyncIterable, Iterable, Self

from streamstore.schemas import ONE_MIB, AppendInput, Record, SequencedRecord


class CommandRecord:
    """
    Factory class for creating `command records <https://s2.dev/docs/stream#command-records>`_.
    """

    FENCE = b"fence"
    TRIM = b"trim"

    @staticmethod
    def fence(token: bytes) -> Record:
        """
        Create a fence command record.

        Args:
            token: `Fencing token <https://s2.dev/docs/stream#fencing-token>`_. Cannot exceed 16 bytes. If empty, clears the previously set token.
        """
        if len(token) > 16:
            raise ValueError("fencing token cannot be greater than 16 bytes")
        return Record(body=token, headers=[(bytes(), CommandRecord.FENCE)])

    @staticmethod
    def trim(desired_first_seq_num: int) -> Record:
        """
        Create a trim command record.

        Args:
            desired_first_seq_num: Sequence number for the first record to exist after trimming
                preceeding records in the stream.

        Note:
            If **desired_first_seq_num** was smaller than the sequence number for the first existing
            record in the stream, trimming doesn't happen.
        """
        return Record(
            body=desired_first_seq_num.to_bytes(8),
            headers=[(bytes(), CommandRecord.TRIM)],
        )


def metered_bytes(records: Iterable[Record | SequencedRecord]) -> int:
    """
    Each record is metered using the following formula:

    .. code-block:: python

        8 + 2 * len(headers)
        + sum((len(name) + len(value)) for (name, value) in headers)
        + len(body)

    """
    return sum(
        (
            8
            + 2 * len(record.headers)
            + sum((len(name) + len(value)) for (name, value) in record.headers)
            + len(record.body)
        )
        for record in records
    )


@dataclass(slots=True)
class _AutoBatcher:
    _next_batch_idx: int = field(init=False)
    _next_batch: list[Record] = field(init=False)
    _next_batch_count: int = field(init=False)
    _next_batch_bytes: int = field(init=False)
    _linger_queue: Queue[tuple[int, datetime]] | None = field(init=False)
    _linger_handler_task: Task | None = field(init=False)
    _limits_handler_task: Task | None = field(init=False)

    append_input_queue: Queue[AppendInput | None]
    match_seq_num: int | None
    fencing_token: bytes | None
    max_records_per_batch: int
    max_bytes_per_batch: int
    max_linger_per_batch: timedelta | None

    def __post_init__(self) -> None:
        self._next_batch_idx = 0
        self._next_batch = []
        self._next_batch_count = 0
        self._next_batch_bytes = 0
        self._linger_queue = Queue() if self.max_linger_per_batch is not None else None
        self._linger_handler_task = None
        self._limits_handler_task = None

    def _accumulate(self, record: Record) -> None:
        self._next_batch.append(record)
        self._next_batch_count += 1
        self._next_batch_bytes += metered_bytes([record])

    def _next_append_input(self) -> AppendInput:
        append_input = AppendInput(
            records=list(self._next_batch),
            match_seq_num=self.match_seq_num,
            fencing_token=self.fencing_token,
        )
        self._next_batch.clear()
        self._next_batch_count = 0
        self._next_batch_bytes = 0
        self._next_batch_idx += 1
        if self.match_seq_num is not None:
            self.match_seq_num = self.match_seq_num + len(append_input.records)
        return append_input

    async def linger_handler(self) -> None:
        if self.max_linger_per_batch is None:
            return
        if self._linger_queue is None:
            return
        linger_duration = self.max_linger_per_batch.total_seconds()
        prev_linger_start = None
        while True:
            batch_idx, linger_start = await self._linger_queue.get()
            if batch_idx < self._next_batch_idx:
                continue
            if prev_linger_start is None:
                prev_linger_start = linger_start
            missed_duration = (linger_start - prev_linger_start).total_seconds()
            await sleep(max(linger_duration - missed_duration, 0))
            if batch_idx == self._next_batch_idx:
                append_input = self._next_append_input()
                await self.append_input_queue.put(append_input)
            prev_linger_start = linger_start

    def _limits_met(self, record: Record) -> bool:
        if (
            self._next_batch_count + 1 <= self.max_records_per_batch
            and self._next_batch_bytes + metered_bytes([record])
            <= self.max_bytes_per_batch
        ):
            return False
        return True

    async def limits_handler(self, records: AsyncIterable[Record]) -> None:
        async for record in records:
            if self._limits_met(record):
                append_input = self._next_append_input()
                await self.append_input_queue.put(append_input)
            self._accumulate(record)
            if self._linger_queue is not None and len(self._next_batch) == 1:
                await self._linger_queue.put((self._next_batch_idx, datetime.now()))
        if len(self._next_batch) != 0:
            append_input = self._next_append_input()
            await self.append_input_queue.put(append_input)
        await self.append_input_queue.put(None)

    def run(self, records: AsyncIterable[Record]) -> None:
        if self.max_linger_per_batch is not None:
            self._linger_handler_task = create_task(self.linger_handler())
        self._limits_handler_task = create_task(self.limits_handler(records))

    def cancel(self) -> None:
        if self._linger_handler_task is not None:
            self._linger_handler_task.cancel()
        if self._limits_handler_task is not None:
            self._limits_handler_task.cancel()


@dataclass(slots=True)
class _AppendInputAsyncIterator:
    append_input_queue: Queue[AppendInput | None]

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> AppendInput:
        append_input = await self.append_input_queue.get()
        if append_input is None:
            raise StopAsyncIteration
        return append_input


async def append_inputs_gen(
    records: AsyncIterable[Record],
    match_seq_num: int | None = None,
    fencing_token: bytes | None = None,
    max_records_per_batch: int = 1000,
    max_bytes_per_batch: int = ONE_MIB,
    max_linger_per_batch: timedelta | None = None,
) -> AsyncIterable[AppendInput]:
    """
    Generator function for batching records and yielding :class:`.AppendInput`.

    Returned generator object can be used as the parameter to :meth:`.Stream.append_session`.

    Yields:
        :class:`.AppendInput`

    Args:
        records: Records that have to be appended to a stream.
        match_seq_num: If it is not ``None``, it is used in the first yield of :class:`.AppendInput`
            and is automatically advanced for subsequent yields.
        fencing_token: Used in each yield of :class:`.AppendInput`.
        max_records_per_batch: Maximum number of records in each batch.
        max_bytes_per_batch: Maximum size of each batch calculated using :func:`.metered_bytes`.
        max_linger_per_batch: Maximum duration for each batch to accumulate records before yielding.

    Note:
        If **max_linger_per_batch** is ``None``, :class:`.AppendInput` will be yielded only
        when **max_records_per_batch** or **max_bytes_per_batch** is reached.
    """
    append_input_queue: Queue[AppendInput | None] = Queue()
    append_input_aiter = _AppendInputAsyncIterator(append_input_queue)
    batcher = _AutoBatcher(
        append_input_queue,
        match_seq_num,
        fencing_token,
        max_records_per_batch,
        max_bytes_per_batch,
        max_linger_per_batch,
    )
    batcher.run(records)
    try:
        async for input in append_input_aiter:
            yield input
    finally:
        batcher.cancel()
