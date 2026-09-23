from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import patch

import pytest

import s2_sdk._generated.s2.v1.s2_pb2 as pb
import s2_sdk._s2s._append_session as append_session
from s2_sdk._client import HttpClient
from s2_sdk._exceptions import AppendIndefiniteFailureError, S2ServerError
from s2_sdk._s2s._protocol import Message
from s2_sdk._types import AppendInput, Compression, Record, Retry


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


def _ack(start: int, *, reconnect_advised: bool = False) -> Message:
    ack = pb.AppendAck(
        start=pb.StreamPosition(seq_num=start, timestamp=1),
        end=pb.StreamPosition(seq_num=start + 1, timestamp=1),
        tail=pb.StreamPosition(seq_num=start + 1, timestamp=1),
    )
    return Message(
        ack.SerializeToString(),
        terminal=False,
        compression=Compression.NONE,
        reconnect_advised=reconnect_advised,
    )


async def test_inflight_acks_drained_before_reconnect() -> None:
    def decoded_messages(stream: AsyncIterator[bytes]) -> AsyncIterator[Message]:
        return cast(AsyncIterator[Message], stream)

    attempts = [
        ((_ack(0, reconnect_advised=True), _ack(1)), 2),
        ((), None),
    ]
    responses: list[_Response] = []

    class _Client:
        @asynccontextmanager
        async def streaming_request(
            self,
            *args: Any,
            content: AsyncGenerator[bytes, None] | None = None,
            **kwargs: Any,
        ) -> AsyncGenerator[_Response, None]:
            messages, inputs_to_consume = attempts.pop(0)
            if content is not None:
                if inputs_to_consume is None:
                    async for _ in content:
                        pass
                else:
                    for _ in range(inputs_to_consume):
                        await content.__anext__()
            response = _Response(messages)
            responses.append(response)
            try:
                yield response
            finally:
                if content is not None:
                    await content.aclose()

    async def inputs() -> AsyncIterator[AppendInput]:
        yield AppendInput(records=[Record(body=b"a")])
        yield AppendInput(records=[Record(body=b"b")])

    with patch.object(append_session, "read_messages", new=decoded_messages):
        acks = [
            ack
            async for ack in append_session.run_append_session(
                cast(HttpClient, _Client()),
                "stream",
                inputs(),
                Retry(max_attempts=1),
                Compression.NONE,
                ack_timeout=1.0,
            )
        ]

    assert [ack.end.seq_num for ack in acks] == [1, 2]
    assert len(responses) == 2
    assert responses[0].retired


@pytest.mark.parametrize(
    ("first_code", "first_status", "want_wrapped"),
    [
        ("unavailable", 503, True),
        ("rate_limited", 429, False),
    ],
)
async def test_terminal_definite_error_preserves_prior_uncertainty(
    first_code: str, first_status: int, want_wrapped: bool
) -> None:
    errors = [
        S2ServerError(code=first_code, message=first_code, status_code=first_status),
        S2ServerError(code="rate_limited", message="rate_limited", status_code=429),
    ]
    final = errors[-1]

    class _Client:
        @asynccontextmanager
        async def streaming_request(
            self,
            *args: Any,
            content: AsyncGenerator[bytes, None] | None = None,
            **kwargs: Any,
        ) -> AsyncGenerator[_Response, None]:
            assert content is not None
            try:
                # Consume one input so it becomes inflight, then fail.
                await content.__anext__()
                raise errors.pop(0)
            finally:
                await content.aclose()
            yield _Response(())  # pragma: no cover

    async def inputs() -> AsyncIterator[AppendInput]:
        yield AppendInput(records=[Record(body=b"a")])

    with (
        patch.object(append_session, "compute_backoff", new=lambda *a, **k: 0.0),
        pytest.raises(BaseException) as exc_info,
    ):
        async for _ in append_session.run_append_session(
            cast(HttpClient, _Client()),
            "stream",
            inputs(),
            Retry(max_attempts=2),
            Compression.NONE,
            ack_timeout=1.0,
        ):
            pass

    err: BaseException = exc_info.value
    while isinstance(err, BaseExceptionGroup):
        err = err.exceptions[0]
    if want_wrapped:
        assert isinstance(err, AppendIndefiniteFailureError)
        assert err.final_attempt_error is final
    else:
        assert err is final
