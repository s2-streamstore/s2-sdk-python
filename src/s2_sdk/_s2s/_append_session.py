import asyncio
import logging
from collections import deque
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

import s2_sdk._generated.s2.v1.s2_pb2 as pb
from s2_sdk._client import HttpClient
from s2_sdk._exceptions import ReadTimeoutError, S2ClientError
from s2_sdk._frame_signal import FrameSignal
from s2_sdk._mappers import append_ack_from_proto, append_input_to_proto
from s2_sdk._retrier import Attempt, compute_backoff, is_safe_to_retry_session
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
        inflight_inputs: deque[_InflightInput] = deque()
        max_retries = retry._max_retries()
        min_base_delay = retry.min_base_delay.total_seconds()
        max_base_delay = retry.max_base_delay.total_seconds()
        attempt = Attempt(0)
        try:
            while True:
                try:
                    resend_inputs = tuple(inflight_inputs)
                    if frame_signal is not None:
                        frame_signal.reset()
                    await _run_attempt(
                        client,
                        stream_name,
                        attempt,
                        inflight_inputs,
                        input_queue,
                        ack_queue,
                        resend_inputs,
                        compression,
                        frame_signal,
                        ack_timeout,
                        encryption_key,
                    )
                    return
                except Exception as e:
                    if attempt.value < max_retries and is_safe_to_retry_session(
                        e,
                        retry.append_retry_policy,
                        bool(inflight_inputs),
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
    inflight_inputs: deque[_InflightInput],
    input_queue: asyncio.Queue[AppendInput | None],
    ack_queue: asyncio.Queue[AppendAck | None],
    resend_inputs: tuple[_InflightInput, ...],
    compression: Compression,
    frame_signal: FrameSignal | None,
    ack_timeout: float,
    encryption_key: str | None = None,
) -> None:
    headers = {
        "content-type": "s2s/proto",
        "accept": "s2s/proto",
    }
    if encryption_key is not None:
        headers[_S2_ENCRYPTION_KEY_HEADER] = encryption_key

    ack_deadline_armed = asyncio.Event()
    for resend_inp in resend_inputs:
        resend_inp.ack_deadline = None

    async with client.streaming_request(
        "POST",
        _stream_records_path(stream_name),
        headers=headers,
        content=_body_gen(
            inflight_inputs,
            input_queue,
            resend_inputs,
            compression,
            ack_deadline_armed,
            ack_timeout,
        ),
        frame_signal=frame_signal,
    ) as response:
        if response.status_code != 200:
            body = await response.aread()
            raise parse_error_info(body, response.status_code)

        prev_ack_end: int | None = None
        resend_remaining = len(resend_inputs)

        messages = read_messages(response.aiter_bytes())
        while True:
            try:
                ack = await _read_ack(
                    messages,
                    inflight_inputs,
                    ack_deadline_armed,
                )
            except StopAsyncIteration:
                break

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


async def _read_ack(
    messages: AsyncIterator[bytes],
    inflight_inputs: deque[_InflightInput],
    deadline_armed: asyncio.Event,
) -> pb.AppendAck:
    def parse_ack(msg_body: bytes) -> pb.AppendAck:
        ack = pb.AppendAck()
        ack.ParseFromString(msg_body)
        return ack

    next_msg_task: asyncio.Task[Any] | None = None
    deadline_armed_waiter_task: asyncio.Task[Any] | None = None
    try:
        while True:
            deadline = inflight_inputs[0].ack_deadline if inflight_inputs else None
            if deadline is not None:
                try:
                    async with asyncio.timeout_at(deadline):
                        if next_msg_task is not None:
                            msg_body = await next_msg_task
                        else:
                            msg_body = await messages.__anext__()
                        return parse_ack(msg_body)
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
        if next_msg_task is not None and not next_msg_task.done():
            next_msg_task.cancel()
            with suppress(asyncio.CancelledError):
                await next_msg_task
        if (
            deadline_armed_waiter_task is not None
            and not deadline_armed_waiter_task.done()
        ):
            deadline_armed_waiter_task.cancel()
            with suppress(asyncio.CancelledError):
                await deadline_armed_waiter_task


async def _body_gen(
    inflight_inputs: deque[_InflightInput],
    input_queue: asyncio.Queue[AppendInput | None],
    resend_inputs: tuple[_InflightInput, ...],
    compression: Compression,
    ack_deadline_armed: asyncio.Event,
    ack_timeout: float,
) -> AsyncGenerator[bytes]:
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
        inp = await input_queue.get()
        if inp is None:
            await input_queue.put(None)
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
