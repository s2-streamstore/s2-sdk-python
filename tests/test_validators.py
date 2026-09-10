import pytest

from s2_sdk import CommandRecord, Record, S2ClientError
from s2_sdk._types import metered_bytes
from s2_sdk._validators import (
    validate_access_token_id,
    validate_append_input,
    validate_location,
    validate_stream,
)


def test_append_record_batch_rejects_empty():
    with pytest.raises(S2ClientError):
        validate_append_input(0, 0)


def test_append_record_batch_rejects_too_many_records():
    records = [Record(body=b"a") for _ in range(1001)]
    with pytest.raises(S2ClientError):
        validate_append_input(len(records), metered_bytes(records))


def test_append_record_rejects_too_large():
    record = Record(body=b"a" * (1024 * 1024 + 1))
    with pytest.raises(S2ClientError):
        validate_append_input(1, metered_bytes([record]))


def test_fencing_token_rejects_too_long():
    with pytest.raises(S2ClientError):
        CommandRecord.fence("a" * 37)


def test_location_accepts_name():
    validate_location("aws:us-east-1")


def test_location_rejects_empty():
    with pytest.raises(S2ClientError):
        validate_location("")


def test_location_rejects_too_long():
    with pytest.raises(S2ClientError):
        validate_location("a" * 65)


def test_stream_accepts_name():
    validate_stream("my/stream\tname \u00e9\U0001f600")


def test_stream_accepts_max_length():
    validate_stream("\u00e9" * 256)


def test_stream_rejects_empty():
    with pytest.raises(S2ClientError):
        validate_stream("")


def test_stream_rejects_too_long():
    with pytest.raises(S2ClientError):
        validate_stream("\u00e9" * 257)


def test_stream_rejects_nul_byte():
    with pytest.raises(S2ClientError):
        validate_stream("a\0b")


def test_access_token_id_accepts_max_length():
    validate_access_token_id("a" * 96)


def test_access_token_id_rejects_empty():
    with pytest.raises(S2ClientError):
        validate_access_token_id("")


def test_access_token_id_rejects_too_long():
    with pytest.raises(S2ClientError):
        validate_access_token_id("a" * 97)


def test_access_token_id_rejects_nul_byte():
    with pytest.raises(S2ClientError):
        validate_access_token_id("a\0b")
