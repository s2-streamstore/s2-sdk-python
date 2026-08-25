from s2_sdk._s2s._protocol import (
    Message,
    frame_message,
    maybe_compress,
)
from s2_sdk._types import Compression


class TestMessageFraming:
    def test_message_length_encoding(self):
        # Verify 3-byte length prefix covers flag + body
        body = b"x" * 256
        data = frame_message(
            Message(body, terminal=False, compression=Compression.NONE)
        )

        # First 3 bytes are length (big-endian), includes 1 byte flag + body
        length = int.from_bytes(data[0:3], "big")
        assert length == 257  # 1 (flag) + 256 (body)


class TestMaybeCompress:
    def test_below_threshold(self):
        body = b"small"
        compressed, comp_code = maybe_compress(body, Compression.ZSTD)
        assert compressed == body
        assert comp_code == Compression.NONE

    def test_above_threshold(self):
        body = b"x" * 2048
        compressed, comp_code = maybe_compress(body, Compression.ZSTD)
        assert comp_code == Compression.ZSTD
        assert len(compressed) < len(body)

    def test_no_compression_requested(self):
        body = b"x" * 2048
        compressed, comp_code = maybe_compress(body, compression=Compression.NONE)
        assert compressed == body
        assert comp_code == Compression.NONE
