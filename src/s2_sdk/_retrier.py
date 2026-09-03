import asyncio
import logging
import math
import random
import time
from dataclasses import dataclass
from typing import Callable

from s2_sdk._exceptions import (
    ConnectError,
    ReconnectAdvisedError,
    S2ServerError,
    TransportError,
    is_server_draining,
)
from s2_sdk._frame_signal import FrameSignal
from s2_sdk._types import AppendRetryPolicy

logger = logging.getLogger(__name__)

_MAX_ADVISED_RECONNECTS = 1
_ADVISED_RECONNECT_IDLE = 60.0


class Retrier:
    def __init__(
        self,
        should_retry_on: Callable[[Exception], bool],
        max_retries: int,
        min_base_delay: float = 0.1,
        max_base_delay: float = 1.0,
    ):
        self.should_retry_on = should_retry_on
        self.max_retries = max_retries
        self.min_base_delay = min_base_delay
        self.max_base_delay = max_base_delay

    async def __call__(self, f: Callable, *args, **kwargs):
        max_retries = self.max_retries
        attempt = 0
        while True:
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries and self.should_retry_on(e):
                    delay = compute_backoff(
                        attempt,
                        min_base_delay=self.min_base_delay,
                        max_base_delay=self.max_base_delay,
                    )
                    retry_after = getattr(e, "_retry_after", None)
                    if retry_after is not None:
                        delay = max(delay, retry_after)
                    logger.debug(
                        "retrying request: error=%s backoff=%.3fs retries_remaining=%d",
                        e,
                        delay,
                        max_retries - attempt - 1,
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    logger.debug(
                        "not retrying request: error=%s is_retryable=%s retries_exhausted=%s",
                        e,
                        self.should_retry_on(e),
                        attempt >= max_retries,
                    )
                    raise e


@dataclass(slots=True)
class Attempt:
    value: int


@dataclass(slots=True)
class AdvisedReconnects:
    count: int = 0
    last: float | None = None

    def record(self) -> None:
        if not self._is_recent():
            self.count = 0
        self.last = time.monotonic()
        self.count += 1

    def should_reconnect(self) -> bool:
        return not self._is_recent() or self.count < _MAX_ADVISED_RECONNECTS

    def _is_recent(self) -> bool:
        return (
            self.last is not None
            and time.monotonic() - self.last <= _ADVISED_RECONNECT_IDLE
        )


def compute_backoff(
    attempt: int,
    min_base_delay: float = 0.1,
    max_base_delay: float = 1.0,
) -> float:
    try:
        base_delay = min(math.ldexp(min_base_delay, attempt), max_base_delay)
    except OverflowError:
        base_delay = max_base_delay
    jitter = random.uniform(0, base_delay)
    return base_delay + jitter


def is_safe_to_retry_unary(
    e: Exception,
    policy: AppendRetryPolicy | None,
) -> bool:
    match policy:
        case None | AppendRetryPolicy.ALL:
            policy_compliant = True
        case AppendRetryPolicy.NO_SIDE_EFFECTS:
            policy_compliant = has_no_side_effects(e)
    return policy_compliant and http_retry_on(e)


def is_safe_to_retry_session(
    e: Exception,
    policy: AppendRetryPolicy,
    has_inflight: bool,
    frame_signal: FrameSignal | None,
) -> bool:
    match policy:
        case AppendRetryPolicy.ALL:
            policy_compliant = True
        case AppendRetryPolicy.NO_SIDE_EFFECTS:
            not_signalled = frame_signal is not None and not frame_signal.is_signalled()
            policy_compliant = (
                not has_inflight or not_signalled or has_no_side_effects(e)
            )
    return policy_compliant and http_retry_on(e)


def is_planned_reconnect(e: Exception) -> bool:
    return isinstance(e, ReconnectAdvisedError) or is_server_draining(e)


def http_retry_on(e: Exception) -> bool:
    if isinstance(e, S2ServerError):
        if e.status_code in (408, 429, 500, 502, 503, 504):
            return True
        if e.status_code == 409 and e.code == "transaction_conflict":
            return True
    if isinstance(e, TransportError):
        return True
    return False


def has_no_side_effects(e: Exception) -> bool:
    if isinstance(e, S2ServerError):
        return (
            (e.status_code == 429 and e.code == "rate_limited")
            or (e.status_code == 502 and e.code == "hot_server")
            or is_server_draining(e)
        )
    if isinstance(e, ReconnectAdvisedError):
        return True
    if isinstance(e, ConnectError):
        cause = e.__cause__
        while cause is not None:
            if isinstance(cause, ConnectionRefusedError):
                return True
            cause = cause.__cause__
        return False
    return False
