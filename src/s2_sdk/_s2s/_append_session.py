import asyncio
import logging
from collections import deque
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, NamedTuple

import s2_sdk._generated.s2.v1.s2_pb2 as pb
from s2_sdk._client import HttpClient
from s2_sdk._exceptions import ReadTimeoutError, S2ClientError
from s2_sdk._frame_signal import FrameSignal
from s2_sdk._mappers import append_ack_from_proto, append_input_to_proto
from s2_sdk._retrier import (
    AdvisedReconnectLimiter,
    Attempt,
    compute_backoff,
    is_safe_to_retry_session,
    requires_reconnect,
)
from s2_sdk._s2s import _stream_records_path
from s2_sdk._s2s._protocol import (
    Message,
    frame_message,
    maybe_compress,
    parse_error_info,
    read_messages,
)
from s2_sdk._types import (
    _S2_ENCRYPTION_KEY_HEADER,
    AppendAck,
    AppendInput,
    AppendRetryPolicy,
    Compression,
    Retry,
)

logger = logging.getLogger(__name__)

_QUEUE_MAX_SIZE = 100


@dataclass(slots=True)
class _InflightInput:
    num_records: int
    encoded: bytes
    ack_deadline: float | None = None


@dataclass(slots=True)
class _AppendSessionState:
    inflight_inputs: deque[_InflightInput] = field(default_factory=deque)
    inputs_exhausted: bool = False


class _AttemptOutcome(Enum):
    COMPLETE = auto()
    RECONNECT_ADVISED = auto()


class _ReadAck(NamedTuple):
    ack: pb.AppendAck
    reconnect_advised: bool


async def run_append_session(
    client: HttpClient,
    stream_name: str,
    inputs: AsyncIterable[AppendInput],
    retry: Retry,
    compression: Compression,
    ack_timeout: float,
    encryption_key: str | None = None,
) -> AsyncIterable[AppendAck]:
    input_queue: asyncio.Queue[AppendInput | None] = asyncio.Queue(
        maxsize=_QUEUE_MAX_SIZE
    )
    ack_queue: asyncio.Queue[AppendAck | None] = asyncio.Queue(maxsize=_QUEUE_MAX_SIZE)

    frame_signal: FrameSignal | None = None
    if retry.append_retry_policy == AppendRetryPolicy.NO_SIDE_EFFECTS:
        frame_signal = FrameSignal()

    async def pipe_inputs():
        try:
            async for inp in inputs:
                await input_queue.put(inp)
        finally:
            await input_queue.put(None)

    async def retrying_inner():
        session_state = _AppendSessionState()
        max_retries = retry._max_retries()
        min_base_delay = retry.min_base_delay.total_seconds()
        max_base_delay = retry.max_base_delay.total_seconds()
        attempt = Attempt(0)
        reconnect_limiter = AdvisedReconnectLimiter()
        try:
            while True:
                try:
                    resend_inputs = tuple(session_state.inflight_inputs)
                    if frame_signal is not None:
                        frame_signal.reset()
                    outcome = await _run_attempt(
                        client,
                        stream_name,
                        attempt,
                        session_state,
                        input_queue,
                        ack_queue,
                        resend_inputs,
                        compression,
                        frame_signal,
                        ack_timeout,
                        reconnect_limiter,
                        encryption_key,
                    )
                    if (
                        outcome is _AttemptOutcome.RECONNECT_ADVISED
                        and not session_state.inputs_exhausted
                    ):
                        logger.debug("reconnecting append session on server advice")
                        continue
                    return
                except Exception as e:
                    reconnect_required = requires_reconnect(e)
                    if (
                        reconnect_required
                        and session_state.inputs_exhausted
                        and not session_state.inflight_inputs
                    ):
                        return
                    if reconnect_required:
                        reconnect_limiter.record_reconnect()
                        logger.debug("reconnecting append session while server drains")
                        continue
                    if attempt.value < max_retries and is_safe_to_retry_session(
                        e,
                        retry.append_retry_policy,
                        bool(session_state.inflight_inputs),
                        frame_signal,
                    ):
                        backoff = compute_backoff(
                            attempt.value,
                            min_base_delay=min_base_delay,
                            max_base_delay=max_base_delay,
                        )
                        logger.debug(
                            "retrying append session: error=%s backoff=%.3fs retries_remaining=%d",
                            e,
                            backoff,
                            max_retries - attempt.value - 1,
                        )
                        await asyncio.sleep(backoff)
                        attempt.value += 1
                    else:
                        logger.debug(
                            "not retrying append session: error=%s retries_exhausted=%s",
                            e,
                            attempt.value >= max_retries,
                        )
                        raise
        finally:
            await ack_queue.put(None)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(retrying_inner())
        tg.create_task(pipe_inputs())
        while True:
            ack = await ack_queue.get()
            if ack is None:
                break
            yield ack


async def _run_attempt(
    client: HttpClient,
    stream_name: str,
    attempt: Attempt,
    session_state: _AppendSessionState,
    input_queue: asyncio.Queue[AppendInput | None],
    ack_queue: asyncio.Queue[AppendAck | None],
    resend_inputs: tuple[_InflightInput, ...],
    compression: Compression,
    frame_signal: FrameSignal | None,
    ack_timeout: float,
    reconnect_limiter: AdvisedReconnectLimiter,
    encryption_key: str | None = None,
) -> _AttemptOutcome:
    inflight_inputs = session_state.inflight_inputs
    headers = {
        "content-type": "s2s/proto",
        "accept": "s2s/proto",
    }
    if encryption_key is not None:
        headers[_S2_ENCRYPTION_KEY_HEADER] = encryption_key

    ack_deadline_armed = asyncio.Event()
    advised_reconnect = asyncio.Event()
    for resend_inp in resend_inputs:
        resend_inp.ack_deadline = None

    async with client.streaming_request(
        "POST",
        _stream_records_path(stream_name),
        headers=headers,
        content=_body_gen(
            session_state,
            input_queue,
            resend_inputs,
            compression,
            ack_deadline_armed,
            ack_timeout,
            advised_reconnect,
        ),
        frame_signal=frame_signal,
    ) as response:
        if response.status_code != 200:
            body = await response.aread()
            raise parse_error_info(body, response.status_code)

        prev_ack_end: int | None = None
        resend_remaining = len(resend_inputs)
        reconnect_advice_seen = False

        messages = read_messages(response.aiter_bytes())
        while True:
            try:
                read_ack_coro = _read_ack(messages, inflight_inputs, ack_deadline_armed)
                if advised_reconnect.is_set() and not inflight_inputs:
                    read_ack = await asyncio.wait_for(
                        read_ack_coro, timeout=ack_timeout
                    )
                else:
                    read_ack = await read_ack_coro
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                raise ReadTimeoutError("Append session ack timeout") from None

            ack, reconnect_advised = read_ack
            if reconnect_advised and not reconnect_advice_seen:
                reconnect_advice_seen = True
                response.retire_connection()
                if reconnect_limiter.try_acquire_advised_reconnect():
                    advised_reconnect.set()

            if attempt.value > 0:
                attempt.value = 0
            if ack.end.seq_num < ack.start.seq_num:
                raise S2ClientError("Invalid ack: end < start")
            if prev_ack_end is not None and ack.end.seq_num <= prev_ack_end:
                raise S2ClientError("Invalid ack: not monotonically increasing")
            prev_ack_end = ack.end.seq_num

            if not inflight_inputs:
                raise S2ClientError("Invalid ack: no inflight append")
            num_records_sent = inflight_inputs.popleft().num_records
            num_records_ackd = ack.end.seq_num - ack.start.seq_num
            if num_records_sent != num_records_ackd:
                raise S2ClientError(
                    "Number of records sent doesn't match the number of acknowledgements received"
                )
            await ack_queue.put(append_ack_from_proto(ack))

            if resend_remaining > 0:
                resend_remaining -= 1
                if (
                    resend_remaining == 0
                    and frame_signal is not None
                    and not inflight_inputs
                ):
                    frame_signal.reset()

        if inflight_inputs:
            raise S2ClientError(
                f"Append session response stream closed with {len(inflight_inputs)} "
                "unacknowledged batches"
            )
        if advised_reconnect.is_set():
            return _AttemptOutcome.RECONNECT_ADVISED
        return _AttemptOutcome.COMPLETE


async def _read_ack(
    messages: AsyncIterator[Message],
    inflight_inputs: deque[_InflightInput],
    deadline_armed: asyncio.Event,
) -> _ReadAck:
    def parse_ack(message: Message) -> _ReadAck:
        ack = pb.AppendAck()
        ack.ParseFromString(message.body)
        return _ReadAck(ack, message.reconnect_advised)

    next_msg_task: asyncio.Task[Any] | None = None
    deadline_armed_waiter_task: asyncio.Task[Any] | None = None
    try:
        while True:
            deadline = inflight_inputs[0].ack_deadline if inflight_inputs else None
            if deadline is not None:
                try:
                    async with asyncio.timeout_at(deadline):
                        if next_msg_task is not None:
                            message = await next_msg_task
                        else:
                            message = await messages.__anext__()
                        return parse_ack(message)
                except TimeoutError:
                    raise ReadTimeoutError("Append session ack timeout") from None

            if next_msg_task is None:
                next_msg_task = asyncio.ensure_future(messages.__anext__())
            deadline_armed.clear()
            deadline_armed_waiter_task = asyncio.create_task(deadline_armed.wait())
            done, _ = await asyncio.wait(
                {next_msg_task, deadline_armed_waiter_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if deadline_armed_waiter_task not in done:
                deadline_armed_waiter_task.cancel()
                with suppress(asyncio.CancelledError):
                    await deadline_armed_waiter_task
            if next_msg_task in done:
                return parse_ack(next_msg_task.result())
    finally:
        tasks = tuple(
            task
            for task in (next_msg_task, deadline_armed_waiter_task)
            if task is not None
        )
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _body_gen(
    session_state: _AppendSessionState,
    input_queue: asyncio.Queue[AppendInput | None],
    resend_inputs: tuple[_InflightInput, ...],
    compression: Compression,
    ack_deadline_armed: asyncio.Event,
    ack_timeout: float,
    advised_reconnect: asyncio.Event,
) -> AsyncGenerator[bytes]:
    inflight_inputs = session_state.inflight_inputs
    loop = asyncio.get_running_loop()
    if resend_inputs:
        logger.debug(
            "resending unacknowledged appends: count=%d bytes=%d",
            len(resend_inputs),
            sum(len(inp.encoded) for inp in resend_inputs),
        )
        for resend_inp in resend_inputs:
            resend_inp.ack_deadline = loop.time() + ack_timeout
            ack_deadline_armed.set()
            yield resend_inp.encoded
        logger.debug("finished resending unacknowledged appends")

    while True:
        if advised_reconnect.is_set():
            return
        try:
            inp = input_queue.get_nowait()
        except asyncio.QueueEmpty:
            input_task = asyncio.create_task(input_queue.get())
            advised_reconnect_task = asyncio.create_task(advised_reconnect.wait())
            try:
                await asyncio.wait(
                    {input_task, advised_reconnect_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not input_task.done():
                    return
                inp = input_task.result()
            finally:
                input_task.cancel()
                advised_reconnect_task.cancel()
                await asyncio.gather(
                    input_task, advised_reconnect_task, return_exceptions=True
                )
        if inp is None:
            await input_queue.put(None)
            session_state.inputs_exhausted = True
            return
        encoded = _encode_input(inp, compression)
        ack_deadline = loop.time() + ack_timeout
        inflight_inputs.append(
            _InflightInput(
                num_records=len(inp.records),
                encoded=encoded,
                ack_deadline=ack_deadline,
            )
        )
        ack_deadline_armed.set()
        yield encoded


def _encode_input(inp: AppendInput, compression: Compression) -> bytes:
    proto = append_input_to_proto(inp)
    body = proto.SerializeToString()
    body, compression = maybe_compress(body, compression)
    return frame_message(Message(body, terminal=False, compression=compression))
