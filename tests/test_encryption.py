from collections.abc import AsyncIterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import s2_sdk._generated.s2.v1.s2_pb2 as pb
from s2_sdk import (
    AppendInput,
    BasinConfig,
    Compression,
    EncryptionAlgorithm,
    EncryptionKey,
    ReadLimit,
    Record,
    Retry,
    S2Basin,
    S2ClientError,
    SeqNum,
)
from s2_sdk._client import HttpClient, Response
from s2_sdk._mappers import (
    basin_config_from_json,
    basin_config_to_json,
    stream_info_from_json,
)
from s2_sdk._s2s._append_session import run_append_session
from s2_sdk._s2s._protocol import Message, frame_message
from s2_sdk._s2s._read_session import run_read_session

KEY_B64 = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA="
KEY_BYTES = bytes(range(1, 33))


def _append_ack_response() -> Response:
    ack = pb.AppendAck(
        start=pb.StreamPosition(seq_num=0, timestamp=10),
        end=pb.StreamPosition(seq_num=1, timestamp=10),
        tail=pb.StreamPosition(seq_num=1, timestamp=10),
    )
    return Response(200, ack.SerializeToString())


def _read_batch_response() -> Response:
    batch = pb.ReadBatch(
        tail=pb.StreamPosition(seq_num=1, timestamp=10),
    )
    return Response(200, batch.SerializeToString())


class _StaticStreamResponse:
    def __init__(
        self, messages: list[bytes], content: AsyncIterator[bytes] | None
    ) -> None:
        self.status_code = 200
        self._messages = messages
        self._content = content

    async def __aenter__(self):
        if self._content is not None:
            async for _ in self._content:
                pass
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def aread(self) -> bytes:
        return b""

    async def aiter_bytes(self):
        for message in self._messages:
            yield message


class _HeaderStreamingClient:
    def __init__(self, response_messages: list[bytes]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._response_messages = response_messages

    def streaming_request(
        self, method: str, path: str, **kwargs
    ) -> _StaticStreamResponse:
        self.calls.append({"method": method, "path": path, "kwargs": kwargs})
        return _StaticStreamResponse(self._response_messages, kwargs.get("content"))


def _ack_message() -> bytes:
    ack = pb.AppendAck(
        start=pb.StreamPosition(seq_num=0, timestamp=10),
        end=pb.StreamPosition(seq_num=1, timestamp=10),
        tail=pb.StreamPosition(seq_num=1, timestamp=10),
    )
    return frame_message(
        Message(ack.SerializeToString(), terminal=False, compression=Compression.NONE)
    )


async def _append_inputs() -> AsyncIterator[AppendInput]:
    yield AppendInput(records=[Record(body=b"payload")])


def test_encryption_key_normalizes_string_and_bytes():
    assert EncryptionKey(f"  {KEY_B64}\n") == EncryptionKey(KEY_B64)
    assert EncryptionKey(KEY_BYTES) == EncryptionKey(KEY_B64)


def test_encryption_key_raises_client_error_for_invalid_length():
    with pytest.raises(S2ClientError, match="length 0 is out of range"):
        EncryptionKey("   ")

    with pytest.raises(S2ClientError, match="length 34 is out of range"):
        EncryptionKey(bytes(range(34)))


def test_basin_config_maps_stream_cipher():
    encoded = basin_config_to_json(
        BasinConfig(stream_cipher=EncryptionAlgorithm.AEGIS_256)
    )
    assert encoded == {"stream_cipher": "aegis-256"}

    decoded = basin_config_from_json({"stream_cipher": "aes-256-gcm"})
    assert decoded.stream_cipher == EncryptionAlgorithm.AES_256_GCM


def test_stream_info_maps_cipher():
    info = stream_info_from_json(
        {
            "name": "events",
            "created_at": "2025-01-01T00:00:00",
            "cipher": "aegis-256",
        }
    )
    assert info.cipher == EncryptionAlgorithm.AEGIS_256


@pytest.mark.asyncio
async def test_basin_stream_injects_unary_encryption_header():
    client = MagicMock()
    client.unary_request = AsyncMock(
        side_effect=[_append_ack_response(), _read_batch_response()]
    )
    basin = S2Basin(
        "test-basin",
        client,
        retry=Retry(max_attempts=1),
        compression=Compression.NONE,
    )

    stream = basin.stream("events", encryption_key=EncryptionKey(KEY_BYTES))
    await stream.append(AppendInput(records=[Record(body=b"payload")]))
    await stream.read(start=SeqNum(0), limit=ReadLimit(count=1))

    append_headers = client.unary_request.call_args_list[0].kwargs["headers"]
    read_headers = client.unary_request.call_args_list[1].kwargs["headers"]
    assert append_headers["s2-encryption-key"] == KEY_B64
    assert read_headers["s2-encryption-key"] == KEY_B64


def test_stream_append_session_and_producer_propagate_encryption_key():
    client = MagicMock()
    basin = S2Basin(
        "test-basin",
        client,
        retry=Retry(max_attempts=1),
        compression=Compression.NONE,
    )
    encrypted_stream = basin.stream("events", encryption_key=EncryptionKey(KEY_BYTES))

    with patch("s2_sdk._ops.AppendSession") as append_session:
        encrypted_stream.append_session()
    assert append_session.call_args.kwargs["encryption_key"] == EncryptionKey(KEY_BYTES)

    with patch("s2_sdk._ops.Producer") as producer:
        encrypted_stream.producer()
    assert producer.call_args.kwargs["encryption_key"] == EncryptionKey(KEY_BYTES)


@pytest.mark.asyncio
async def test_stream_read_session_propagates_encryption_key():
    client = MagicMock()
    basin = S2Basin(
        "test-basin",
        client,
        retry=Retry(max_attempts=1),
        compression=Compression.NONE,
    )
    encrypted_stream = basin.stream("events", encryption_key=EncryptionKey(KEY_BYTES))
    calls: list[dict[str, Any]] = []

    async def _fake_run_read_session(*args, **kwargs):
        calls.append(kwargs)
        if False:
            yield

    with patch("s2_sdk._ops.run_read_session", new=_fake_run_read_session):
        async for _ in encrypted_stream.read_session(
            start=SeqNum(0),
            limit=ReadLimit(count=1),
        ):
            pass

    assert calls[0]["encryption_key"] == EncryptionKey(KEY_BYTES)


@pytest.mark.asyncio
async def test_run_append_session_sets_encryption_header():
    client = _HeaderStreamingClient([_ack_message()])

    outputs = []
    async for output in run_append_session(
        cast(HttpClient, client),
        "events",
        _append_inputs(),
        retry=Retry(max_attempts=1),
        compression=Compression.NONE,
        encryption_key=EncryptionKey(KEY_BYTES),
    ):
        outputs.append(output)

    assert len(outputs) == 1
    headers = client.calls[0]["kwargs"]["headers"]
    assert headers["s2-encryption-key"] == KEY_B64


@pytest.mark.asyncio
async def test_run_read_session_sets_encryption_header():
    client = _HeaderStreamingClient([])

    outputs = []
    async for output in run_read_session(
        cast(HttpClient, client),
        "events",
        SeqNum(0),
        ReadLimit(count=1),
        None,
        False,
        0,
        False,
        Retry(max_attempts=1),
        encryption_key=EncryptionKey(KEY_BYTES),
    ):
        outputs.append(output)

    assert outputs == []
    headers = client.calls[0]["kwargs"]["headers"]
    assert headers["s2-encryption-key"] == KEY_B64
