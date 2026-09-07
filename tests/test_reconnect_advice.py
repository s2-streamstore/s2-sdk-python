from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast

import s2_sdk._generated.s2.v1.s2_pb2 as pb
from s2_sdk._client import HttpClient
from s2_sdk._read_session import _ReadSessionBatch, _ReadSessionRetrying
from s2_sdk._s2s._append_session import run_append_session
from s2_sdk._s2s._protocol import Message, frame_message
from s2_sdk._s2s._read_session import run_read_session
from s2_sdk._types import (
    AppendInput,
    Compression,
    ReadLimit,
    Record,
    Retry,
    SeqNum,
)


@dataclass(slots=True)
class _Attempt:
    frames: tuple[bytes, ...]
    inputs_to_consume: int = 0


class _Response:
    status_code = 200

    def __init__(self, frames: tuple[bytes, ...]) -> None:
        self.frames = frames
        self.poisoned = False

    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        for frame in self.frames:
            yield frame

    def poison_connection(self) -> None:
        self.poisoned = True


class _Client:
    _request_timeout = 1.0

    def __init__(self, attempts: list[_Attempt]) -> None:
        self.attempts = attempts
        self.requests: list[dict[str, Any]] = []
        self.responses: list[_Response] = []

    @asynccontextmanager
    async def streaming_request(
        self,
        *args: Any,
        params: dict[str, Any] | None = None,
        content: AsyncIterator[bytes] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[_Response]:
        attempt = self.attempts.pop(0)
        self.requests.append(dict(params or {}))
        content_iter = content.__aiter__() if content is not None else None
        if content_iter is not None:
            for _ in range(attempt.inputs_to_consume):
                await content_iter.__anext__()
        response = _Response(attempt.frames)
        self.responses.append(response)
        try:
            yield response
        finally:
            if content_iter is not None:
                close = getattr(content_iter, "aclose", None)
                if close is not None:
                    await close()


def _frame(message: Any, *, reconnect_advised: bool = False) -> bytes:
    framed = bytearray(
        frame_message(
            Message(message.SerializeToString(), False, Compression.NONE),
        )
    )
    if reconnect_advised:
        framed[3] |= 0x10
    return bytes(framed)


def _append_ack(start: int, *, reconnect_advised: bool = False) -> bytes:
    return _frame(
        pb.AppendAck(
            start=pb.StreamPosition(seq_num=start, timestamp=1),
            end=pb.StreamPosition(seq_num=start + 1, timestamp=1),
            tail=pb.StreamPosition(seq_num=start + 1, timestamp=1),
        ),
        reconnect_advised=reconnect_advised,
    )


def _read_batch(seq_num: int, *, reconnect_advised: bool = False) -> bytes:
    return _frame(
        pb.ReadBatch(
            records=[pb.SequencedRecord(seq_num=seq_num, timestamp=1, body=b"x")],
        ),
        reconnect_advised=reconnect_advised,
    )


async def _append_inputs() -> AsyncIterator[AppendInput]:
    yield AppendInput(records=[Record(body=b"a")])
    yield AppendInput(records=[Record(body=b"b")])


async def test_append_drains_inflight_before_budget_free_reconnect() -> None:
    client = _Client(
        [
            _Attempt(
                (_append_ack(0, reconnect_advised=True), _append_ack(1)),
                inputs_to_consume=2,
            ),
            _Attempt(()),
        ]
    )

    acks = [
        ack
        async for ack in run_append_session(
            cast(HttpClient, client),
            "stream",
            _append_inputs(),
            Retry(max_attempts=1),
            Compression.NONE,
            ack_timeout=1.0,
        )
    ]

    assert [ack.end.seq_num for ack in acks] == [1, 2]
    assert len(client.requests) == 2
    assert client.responses[0].poisoned


async def test_read_resumes_and_declines_repeated_advice() -> None:
    client = _Client(
        [
            _Attempt((_read_batch(10, reconnect_advised=True),)),
            _Attempt((_read_batch(11, reconnect_advised=True), _read_batch(12))),
        ]
    )

    events = [
        event
        async for event in run_read_session(
            cast(HttpClient, client),
            "stream",
            SeqNum(10),
            ReadLimit(count=3),
            until_timestamp=None,
            clamp_to_tail=False,
            wait=None,
            retry=Retry(max_attempts=1),
        )
    ]

    assert isinstance(events[0], _ReadSessionBatch)
    assert isinstance(events[1], _ReadSessionRetrying)
    assert isinstance(events[2], _ReadSessionBatch)
    assert isinstance(events[3], _ReadSessionBatch)
    assert events[0].batch.records[0].seq_num == 10
    assert events[2].batch.records[0].seq_num == 11
    assert events[3].batch.records[0].seq_num == 12
    assert client.requests[1] == {"seq_num": 11, "count": 2}
    assert len(client.requests) == 2
    assert client.responses[0].poisoned
    assert client.responses[1].poisoned
