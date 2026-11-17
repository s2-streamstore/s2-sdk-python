from __future__ import annotations

import asyncio
from functools import wraps
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import TYPE_CHECKING, Any, NamedTuple, Never, overload

if TYPE_CHECKING:
    from s2_sdk._types import StreamPosition


def set_and_retrieve_future_exception(
    future: asyncio.Future[Any], exception: BaseException
) -> None:
    """Set an exception and immediately retrieve it.

    This prevents `Future.__del__` from reporting
    "Future exception was never retrieved" when the `Future` is finalized.
    """
    if not future.done():
        future.set_exception(exception)
        future.exception()


def retrieve_task_exception_if_present(task: asyncio.Task[Any]) -> None:
    """Retrieve an exception, if present.

    This prevents `Future.__del__` from reporting
    "Task exception was never retrieved" when the `Task` is finalized.
    """
    if not task.cancelled():
        task.exception()


class S2Error(Exception):
    """Base class for all S2 related exceptions."""


class S2ClientError(S2Error):
    """Error originating from the client."""


UNKNOWN_CODE = "unknown"


class _ErrorCodeInfo(NamedTuple):
    status: int
    retryable: bool
    no_side_effects: bool


# Error codes documented at https://s2.dev/docs/api/error-codes.
_ERROR_CODES: dict[str, _ErrorCodeInfo] = {
    "access_token_not_found": _ErrorCodeInfo(404, False, True),
    "authn": _ErrorCodeInfo(401, False, True),
    "bad_frame": _ErrorCodeInfo(400, False, True),
    "bad_header": _ErrorCodeInfo(400, False, True),
    "bad_json": _ErrorCodeInfo(400, False, True),
    "bad_path": _ErrorCodeInfo(400, False, True),
    "bad_proto": _ErrorCodeInfo(400, False, True),
    "bad_query": _ErrorCodeInfo(400, False, True),
    "basin_deletion_pending": _ErrorCodeInfo(409, False, True),
    "basin_not_found": _ErrorCodeInfo(404, False, True),
    "client_hangup": _ErrorCodeInfo(499, False, False),
    "decryption_failed": _ErrorCodeInfo(400, False, True),
    "hot_server": _ErrorCodeInfo(502, True, True),
    "invalid": _ErrorCodeInfo(422, False, True),
    "not_implemented": _ErrorCodeInfo(501, False, True),
    "other": _ErrorCodeInfo(500, True, False),
    "permission_denied": _ErrorCodeInfo(403, False, True),
    "quota_exhausted": _ErrorCodeInfo(403, False, True),
    "rate_limited": _ErrorCodeInfo(429, True, True),
    "request_timeout": _ErrorCodeInfo(408, True, False),
    "resource_already_exists": _ErrorCodeInfo(409, False, True),
    "server_draining": _ErrorCodeInfo(503, True, True),
    "storage": _ErrorCodeInfo(500, True, False),
    "stream_deletion_pending": _ErrorCodeInfo(409, False, True),
    "stream_not_found": _ErrorCodeInfo(404, False, True),
    "transaction_conflict": _ErrorCodeInfo(409, True, True),
    "unavailable": _ErrorCodeInfo(503, True, False),
    "upstream_timeout": _ErrorCodeInfo(504, True, False),
}
_RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


class S2ServerError(S2Error):
    """Error originating from the server.

    Attributes:
        code: Error code from the server. See `error codes <https://s2.dev/docs/api/error-codes#standard-errors>`_ for possible values.
        message: Human-readable error message.
        status_code: HTTP status code.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self._retry_after: float | None = None
        super().__init__(message)

    def _is_retryable(self) -> bool:
        info = _ERROR_CODES.get(self.code)
        if info is None:
            return self.status_code in _RETRYABLE_STATUSES
        return info.status == self.status_code and info.retryable

    def _has_no_side_effects(self) -> bool:
        # 412 is only used for append condition failures, which reject the append.
        if self.status_code == 412:
            return True
        info = _ERROR_CODES.get(self.code)
        return (
            info is not None
            and info.status == self.status_code
            and info.no_side_effects
        )


class ServerDrainingError(S2ServerError):
    """The server is draining, so the associated connection should be retired."""


class AppendIndefiniteFailureError(S2Error):
    """The final append attempt failed definitively, but an earlier attempt may have
    taken effect, so the entire append operation is indefinite.

    Attributes:
        final_attempt_error: The definite error raised by the final attempt.
    """

    def __init__(self, final_attempt_error: Exception):
        self.final_attempt_error = normalize_exception(final_attempt_error)
        super().__init__(
            "append may have taken effect in an earlier attempt; "
            f"final attempt failed: {final_attempt_error}"
        )
        self.__cause__ = self.final_attempt_error


class AppendConditionError(S2ServerError):
    """Append condition was not met."""


class FencingTokenMismatchError(AppendConditionError):
    """Fencing token did not match.

    Attributes:
        expected_fencing_token: The fencing token the server expected.
    """

    def __init__(
        self, code: str, message: str, status_code: int, expected_fencing_token: str
    ):
        self.expected_fencing_token = expected_fencing_token
        super().__init__(code, message, status_code)


class SeqNumMismatchError(AppendConditionError):
    """Sequence number did not match.

    Attributes:
        expected_seq_num: The sequence number the server expected.
    """

    def __init__(
        self, code: str, message: str, status_code: int, expected_seq_num: int
    ):
        self.expected_seq_num = expected_seq_num
        super().__init__(code, message, status_code)


class ReadUnwrittenError(S2ServerError):
    """Read from an unwritten position.

    Attributes:
        tail: The tail position of the stream.
    """

    def __init__(self, code: str, message: str, status_code: int, tail: StreamPosition):
        self.tail = tail
        super().__init__(code, message, status_code)


def raise_for_412(body: dict, code: str) -> Never:
    if "fencing_token_mismatch" in body:
        info = body["fencing_token_mismatch"]
        expected = (
            info if isinstance(info, str) else info.get("expected_fencing_token", "")
        )
        raise FencingTokenMismatchError(
            code,
            f"Fencing token mismatch: {info}",
            412,
            expected_fencing_token=str(expected),
        )
    elif "seq_num_mismatch" in body:
        info = body["seq_num_mismatch"]
        expected = info if isinstance(info, int) else info.get("expected_seq_num", 0)
        raise SeqNumMismatchError(
            code,
            f"Sequence number mismatch: {info}",
            412,
            expected_seq_num=int(expected),
        )
    raise AppendConditionError(code, str(body), 412)


def raise_for_416(body: dict, code: str) -> Never:
    from s2_sdk._types import StreamPosition

    tail = body.get("tail", {})
    raise ReadUnwrittenError(
        code,
        "Read from unwritten position",
        416,
        tail=StreamPosition(
            seq_num=tail.get("seq_num", 0),
            timestamp=tail.get("timestamp", 0),
        ),
    )


def raise_for_503(message: str, code: str) -> Never:
    if code == "server_draining":
        raise ServerDrainingError(code, message, 503)
    raise S2ServerError(code, message, 503)


S2Error.__module__ = "s2_sdk"
S2ClientError.__module__ = "s2_sdk"
S2ServerError.__module__ = "s2_sdk"
AppendConditionError.__module__ = "s2_sdk"
FencingTokenMismatchError.__module__ = "s2_sdk"
SeqNumMismatchError.__module__ = "s2_sdk"
ReadUnwrittenError.__module__ = "s2_sdk"
AppendIndefiniteFailureError.__module__ = "s2_sdk"


class TransportError(Exception):
    """Network-level error (connection reset, timeout, protocol)."""


class UnprocessedRequestError(TransportError):
    """The server did not process the request, so it had no side effects."""


class ConnectError(UnprocessedRequestError):
    """Could not get a connection ready for a request. No request bytes were sent."""


class ReadTimeoutError(TransportError):
    """Timed out waiting for data."""


class ConnectionClosedError(TransportError):
    """Connection closed unexpectedly."""


class ConnectionRetiredError(UnprocessedRequestError):
    """A retired connection cannot accept a new stream."""


class ProtocolError(TransportError):
    """HTTP/2 protocol error (RST_STREAM, GOAWAY)."""


def _maybe_unwrap_exception_group(e: BaseException) -> BaseException:
    while isinstance(e, BaseExceptionGroup) and len(e.exceptions) == 1:
        e = e.exceptions[0]
    return e


@overload
def normalize_exception(e: Exception) -> S2Error: ...
@overload
def normalize_exception(e: BaseException) -> BaseException: ...
def normalize_exception(e: BaseException) -> BaseException:
    e = _maybe_unwrap_exception_group(e)

    if not isinstance(e, Exception):
        return e
    if isinstance(e, S2Error):
        return e

    client_error = S2ClientError(e)
    client_error.__cause__ = e
    return client_error


def _raise_normalized_exception(e: Exception):
    normalized = normalize_exception(e)
    if normalized is e:
        raise
    raise normalized from e


def fallible(f):
    @wraps(f)
    def sync_wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            _raise_normalized_exception(e)

    @wraps(f)
    async def async_gen_wrapper(*args, **kwargs):
        try:
            async for val in f(*args, **kwargs):
                yield val
        except Exception as e:
            _raise_normalized_exception(e)

    @wraps(f)
    async def coro_wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            _raise_normalized_exception(e)

    if iscoroutinefunction(f):
        return coro_wrapper
    elif isasyncgenfunction(f):
        return async_gen_wrapper
    else:
        return sync_wrapper
