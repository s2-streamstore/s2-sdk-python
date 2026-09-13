import json
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast
from unittest.mock import patch

import s2_sdk._generated.s2.v1.s2_pb2 as pb
import s2_sdk._s2s._append_session as s2s_append_session
import s2_sdk._s2s._read_session as s2s_read_session
from s2_sdk._client import HttpClient
from s2_sdk._mappers import stream_config_header
from s2_sdk._ops import S2Stream
from s2_sdk._s2s._protocol import Message
from s2_sdk._types import (
    AppendInput,
    Compression,
    ReadLimit,
    Record,
    Retry,
    SeqNum,
    StorageClass,
    StreamConfig,
    Timestamping,
    TimestampingMode,
)

_CONFIG = StreamConfig(retention_policy=3600, delete_on_empty_min_age=300)
_HEADER = "s2-stream-config"


def _ack() -> pb.AppendAck:
    return pb.AppendAck(
        start=pb.StreamPosition(seq_num=0, timestamp=1),
        end=pb.StreamPosition(seq_num=1, timestamp=1),
        tail=pb.StreamPosition(seq_num=1, timestamp=1),
    )


def _batch() -> pb.ReadBatch:
    return pb.ReadBatch(records=[pb.SequencedRecord(seq_num=0, timestamp=1, body=b"a")])


def _response_body(method: str) -> bytes:
    proto = _ack() if method == "POST" else _batch()
    return proto.SerializeToString()


@dataclass(slots=True)
class _Response:
    content: bytes
    status_code: int = 200

    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        message = Message(
            self.content,
            terminal=False,
            compression=Compression.NONE,
            reconnect_advised=False,
        )
        yield cast(bytes, message)

    def retire_connection(self) -> None:
        pass


@dataclass(slots=True)
class _Client:
    headers: list[dict[str, str] | None] = field(default_factory=list)
    _request_timeout: float = 1.0

    async def unary_request(self, method: str, path: str, **kwargs: Any) -> _Response:
        self.headers.append(kwargs.get("headers"))
        return _Response(_response_body(method))

    @asynccontextmanager
    async def streaming_request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        content: AsyncGenerator[bytes, None] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[_Response, None]:
        self.headers.append(headers)
        if content is not None:
            async for _ in content:
                pass
        yield _Response(_response_body(method))


def _decoded_messages(stream: AsyncIterator[bytes]) -> AsyncIterator[Message]:
    return cast(AsyncIterator[Message], stream)


def _stream(client: _Client, encryption_key: str | None = None) -> S2Stream:
    return S2Stream(
        "stream",
        cast(HttpClient, client),
        retry=Retry(max_attempts=1),
        compression=Compression.NONE,
        encryption_key=encryption_key,
    )


def test_stream_config_header_uses_api_field_names() -> None:
    config = StreamConfig(
        storage_class=StorageClass.EXPRESS,
        retention_policy="infinite",
        timestamping=Timestamping(mode=TimestampingMode.CLIENT_REQUIRE, uncapped=True),
        delete_on_empty_min_age=300,
    )
    assert json.loads(stream_config_header(config)) == {
        "storage_class": "express",
        "retention_policy": {"infinite": {}},
        "timestamping": {"mode": "client-require", "uncapped": True},
        "delete_on_empty": {"min_age_secs": 300},
    }
    assert stream_config_header(StreamConfig()) == "{}"


async def test_unary_append_and_read_send_header() -> None:
    client = _Client()
    stream = _stream(client, encryption_key="key")

    await stream.append(AppendInput(records=[Record(body=b"a")], stream_config=_CONFIG))
    await stream.read(start=SeqNum(0), stream_config=_CONFIG)

    assert len(client.headers) == 2
    for headers in client.headers:
        assert headers is not None
        assert headers["s2-encryption-key"] == "key"
        assert json.loads(headers[_HEADER]) == {
            "retention_policy": {"age": 3600},
            "delete_on_empty": {"min_age_secs": 300},
        }


async def test_unary_append_and_read_omit_header_when_unset() -> None:
    client = _Client()
    stream = _stream(client)

    await stream.append(AppendInput(records=[Record(body=b"a")]))
    await stream.read(start=SeqNum(0))

    assert all(_HEADER not in (headers or {}) for headers in client.headers)


async def test_read_session_sends_header() -> None:
    client = _Client()

    with patch.object(s2s_read_session, "read_messages", new=_decoded_messages):
        async for _ in s2s_read_session.run_read_session(
            cast(HttpClient, client),
            "stream",
            SeqNum(0),
            ReadLimit(count=1),
            until_timestamp=None,
            clamp_to_tail=False,
            wait=None,
            retry=Retry(max_attempts=1),
            stream_config=_CONFIG,
        ):
            pass

    assert client.headers == [
        {"content-type": "s2s/proto", _HEADER: stream_config_header(_CONFIG)}
    ]


async def test_append_session_sends_header() -> None:
    client = _Client()

    async def inputs() -> AsyncIterator[AppendInput]:
        yield AppendInput(records=[Record(body=b"a")])

    with patch.object(s2s_append_session, "read_messages", new=_decoded_messages):
        async for _ in s2s_append_session.run_append_session(
            cast(HttpClient, client),
            "stream",
            inputs(),
            Retry(max_attempts=1),
            Compression.NONE,
            ack_timeout=1.0,
            stream_config=_CONFIG,
        ):
            pass

    assert client.headers == [
        {
            "content-type": "s2s/proto",
            "accept": "s2s/proto",
            _HEADER: stream_config_header(_CONFIG),
        }
    ]
