from __future__ import annotations

from base64 import b64encode
from typing import TypeAlias

from s2_sdk._exceptions import S2ClientError

S2_ENCRYPTION_KEY_HEADER = "s2-encryption-key"
MAX_ENCRYPTION_KEY_HEADER_VALUE_LEN = 44


class EncryptionKeyLengthError(S2ClientError):
    """Encryption key material length is outside the accepted bounds."""

    def __init__(self, length: int):
        self.length = length
        super().__init__(
            f"invalid encryption key: key material length {length} is out of range"
        )


BytesLike: TypeAlias = bytes | bytearray | memoryview


class EncryptionKey:
    """Base64-encoded encryption key material for append/read operations.

    Args:
        value: Base64-encoded key material as ``str``, or raw bytes-like key
            material which will be base64-encoded automatically.
    """

    __slots__ = ("_encoded",)

    def __init__(self, value: str | BytesLike):
        if isinstance(value, str):
            encoded = value.strip()
            key_material_length = len(encoded)
        else:
            raw = bytes(value)
            encoded = b64encode(raw).decode("ascii")
            key_material_length = len(raw)

        if len(encoded) == 0 or len(encoded) > MAX_ENCRYPTION_KEY_HEADER_VALUE_LEN:
            raise EncryptionKeyLengthError(key_material_length)

        self._encoded = encoded

    @classmethod
    def from_bytes(cls, value: BytesLike) -> "EncryptionKey":
        """Construct an :class:`EncryptionKey` from raw key material."""
        return cls(value)

    def to_base64(self) -> str:
        """Return the normalized base64-encoded form accepted by S2."""
        return self._encoded

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EncryptionKey):
            return NotImplemented
        return self._encoded == other._encoded

    def __hash__(self) -> int:
        return hash(self._encoded)

    def __repr__(self) -> str:
        return "EncryptionKey(<redacted>)"

    __str__ = __repr__


def resolve_encryption_key(value: EncryptionKeyInput | None) -> EncryptionKey | None:
    if value is None:
        return None
    if isinstance(value, EncryptionKey):
        return value
    return EncryptionKey(value)


EncryptionKeyInput: TypeAlias = str | BytesLike | EncryptionKey


EncryptionKey.__module__ = "s2_sdk"
EncryptionKeyLengthError.__module__ = "s2_sdk"
