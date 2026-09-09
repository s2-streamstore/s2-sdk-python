from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import patch

import s2_sdk._generated.s2.v1.s2_pb2 as pb
import s2_sdk._s2s._append_session as append_session
from s2_sdk._client import HttpClient
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
        ((), 0),
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
