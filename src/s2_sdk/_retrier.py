import asyncio
import logging
import math
import random
import time
from dataclasses import dataclass
from typing import Callable

from s2_sdk._exceptions import (
    AppendIndefiniteFailureError,
    ConnectionRetiredError,
    S2ServerError,
    ServerDrainingError,
    TransportError,
    UnprocessedRequestError,
)
from s2_sdk._frame_signal import FrameSignal
from s2_sdk._types import AppendRetryPolicy

logger = logging.getLogger(__name__)

_RECONNECT_COUNT_THRESHOLD = 1
_RECONNECT_RECENCY_THRESHOLD = 60.0


class Retrier:
    def __init__(
        self,
        should_retry_on: Callable[[Exception], bool],
        max_retries: int,
        min_base_delay: float = 0.1,
        max_base_delay: float = 1.0,
        track_append_uncertainty: bool = False,
    ):
        self.should_retry_on = should_retry_on
        self.max_retries = max_retries
        self.min_base_delay = min_base_delay
        self.max_base_delay = max_base_delay
        self.track_append_uncertainty = track_append_uncertainty

    async def __call__(self, f: Callable, *args, **kwargs):
        max_retries = self.max_retries
        attempt = 0
        prior_uncertainty = False
        while True:
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries and self.should_retry_on(e):
                    if self.track_append_uncertainty and not has_no_side_effects(e):
                        prior_uncertainty = True
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
                    if self.track_append_uncertainty:
                        wrapped = with_prior_uncertainty(e, prior_uncertainty)
                        if wrapped is not e:
                            raise wrapped
                    raise e


@dataclass(slots=True)
class Attempt:
    value: int


@dataclass(slots=True)
class AdvisedReconnectLimiter:
    count: int = 0
    last_reconnect_at: float | None = None

    def try_acquire_advised_reconnect(self) -> bool:
        if (
            self._last_reconnect_is_recent()
            and self.count >= _RECONNECT_COUNT_THRESHOLD
        ):
            return False
        self.record_reconnect()
        return True

    def record_reconnect(self) -> None:
        if not self._last_reconnect_is_recent():
            self.count = 0
        self.last_reconnect_at = time.monotonic()
        self.count += 1

    def _last_reconnect_is_recent(self) -> bool:
        return (
            self.last_reconnect_at is not None
            and time.monotonic() - self.last_reconnect_at
            <= _RECONNECT_RECENCY_THRESHOLD
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


def requires_reconnect(e: Exception) -> bool:
    return isinstance(e, (ConnectionRetiredError, ServerDrainingError))


def http_retry_on(e: Exception) -> bool:
    if isinstance(e, S2ServerError):
        if e.status_code in (408, 429, 500, 502, 503, 504):
            return True
        if e.status_code == 409 and e.code == "transaction_conflict":
            return True
    if isinstance(e, TransportError):
        return True
    return False


# Error codes the S2 API guarantees had no side effects, with their HTTP status.
# See https://s2.dev/docs/api/error-codes.
_NO_SIDE_EFFECT_CODES: dict[str, int] = {
    "access_token_not_found": 404,
    "authn": 401,
    "bad_frame": 400,
    "bad_header": 400,
    "bad_json": 400,
    "bad_path": 400,
    "bad_proto": 400,
    "bad_query": 400,
    "basin_deletion_pending": 409,
    "basin_not_found": 404,
    "decryption_failed": 400,
    "hot_server": 502,
    "invalid": 422,
    "not_implemented": 501,
    "permission_denied": 403,
    "quota_exhausted": 403,
    "rate_limited": 429,
    "resource_already_exists": 409,
    "server_draining": 503,
    "stream_deletion_pending": 409,
    "stream_not_found": 404,
    "transaction_conflict": 409,
}


def has_no_side_effects(e: Exception) -> bool:
    if isinstance(e, UnprocessedRequestError):
        return True
    if isinstance(e, S2ServerError):
        # 412 is only used for append condition failures, which reject the append.
        return (
            e.status_code == 412 or _NO_SIDE_EFFECT_CODES.get(e.code) == e.status_code
        )
    return False


def with_prior_uncertainty(e: Exception, prior_uncertainty: bool) -> Exception:
    """Wrap a definite final error if an earlier attempt may have taken effect.

    Already indefinite errors are returned unchanged.
    """
    if prior_uncertainty and has_no_side_effects(e):
        return AppendIndefiniteFailureError(e)
    return e


def attempt_may_have_side_effects(
    e: Exception, frame_signal: FrameSignal | None
) -> bool:
    """Whether this attempt may have taken effect, accounting for unsent request data.

    Without a frame signal, assume the request may have been sent.
    """
    return not has_no_side_effects(e) and (
        frame_signal is None or frame_signal.is_signalled()
    )
