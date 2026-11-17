import sys

import pytest

from s2_sdk import AppendIndefiniteFailureError, S2ClientError, S2ServerError
from s2_sdk._exceptions import ConnectError, UnprocessedRequestError
from s2_sdk._retrier import (
    Retrier,
    compute_backoff,
    has_no_side_effects,
    http_retry_on,
    is_safe_to_retry_unary,
    with_prior_uncertainty,
)
from s2_sdk._types import AppendRetryPolicy


def _server_error(status_code: int, code: str) -> S2ServerError:
    return S2ServerError(code=code, message=code, status_code=status_code)


@pytest.mark.parametrize(
    ("e", "retryable", "no_side_effects"),
    [
        (ConnectError("Connection to host:443 timed out"), True, True),
        (UnprocessedRequestError("GOAWAY received"), True, True),
        (_server_error(409, "transaction_conflict"), True, True),
        (_server_error(404, "stream_not_found"), False, True),
        (_server_error(412, "unknown"), False, True),
        (_server_error(503, "unavailable"), True, False),
        (_server_error(499, "client_hangup"), False, False),
        (_server_error(500, "rate_limited"), False, False),
        (_server_error(503, "code_from_newer_server"), True, False),
        (_server_error(400, "code_from_newer_server"), False, False),
    ],
)
def test_error_classification(e: Exception, retryable: bool, no_side_effects: bool):
    assert http_retry_on(e) is retryable
    assert has_no_side_effects(e) is no_side_effects
    assert is_safe_to_retry_unary(e, AppendRetryPolicy.NO_SIDE_EFFECTS) is (
        retryable and no_side_effects
    )


class TestWithPriorUncertainty:
    def test_definite_error_unchanged_without_prior_uncertainty(self):
        e = _server_error(429, "rate_limited")
        assert with_prior_uncertainty(e, False) is e

    def test_indefinite_error_not_wrapped(self):
        e = _server_error(503, "unavailable")
        assert with_prior_uncertainty(e, True) is e

    def test_definite_error_wrapped(self):
        e = _server_error(429, "rate_limited")
        wrapped = with_prior_uncertainty(e, True)
        assert isinstance(wrapped, AppendIndefiniteFailureError)
        assert wrapped.final_attempt_error is e
        assert wrapped.__cause__ is e
        assert not has_no_side_effects(wrapped)
        assert with_prior_uncertainty(wrapped, True) is wrapped

    def test_transport_error_normalized(self):
        e = ConnectError("timed out")
        wrapped = with_prior_uncertainty(e, True)
        assert isinstance(wrapped, AppendIndefiniteFailureError)
        assert isinstance(wrapped.final_attempt_error, S2ClientError)
        assert wrapped.final_attempt_error.__cause__ is e
        assert wrapped.__cause__ is wrapped.final_attempt_error


class TestRetrierAppendUncertainty:
    def _retrier(self) -> Retrier:
        return Retrier(
            should_retry_on=lambda e: is_safe_to_retry_unary(e, AppendRetryPolicy.ALL),
            max_retries=2,
            min_base_delay=0.001,
            max_base_delay=0.001,
            track_append_uncertainty=True,
        )

    async def _run(self, responses: list[Exception | str]):
        it = iter(responses)

        async def f():
            r = next(it)
            if isinstance(r, Exception):
                raise r
            return r

        return await self._retrier()(f)

    async def test_indefinite_then_definite_is_wrapped(self):
        final = _server_error(429, "rate_limited")
        with pytest.raises(AppendIndefiniteFailureError) as exc_info:
            await self._run([_server_error(503, "unavailable"), final, final])
        assert exc_info.value.final_attempt_error is final

    async def test_definite_then_definite_is_not_wrapped(self):
        final = _server_error(429, "rate_limited")
        with pytest.raises(S2ServerError) as exc_info:
            await self._run([_server_error(429, "rate_limited"), final, final])
        assert exc_info.value is final

    async def test_indefinite_then_indefinite_is_not_wrapped(self):
        final = _server_error(503, "unavailable")
        with pytest.raises(S2ServerError) as exc_info:
            await self._run([_server_error(503, "unavailable"), final, final])
        assert exc_info.value is final

    async def test_success_after_indefinite(self):
        assert await self._run([_server_error(503, "unavailable"), "ok"]) == "ok"


class TestComputeBackoff:
    @pytest.mark.parametrize(
        ("attempt", "expected_min", "expected_max"),
        [
            (0, 0.1, 0.2),
            (1, 0.2, 0.4),
            (2, 0.4, 0.8),
            (3, 0.8, 1.6),
            (4, 1.0, 2.0),
            (5, 1.0, 2.0),
        ],
    )
    def test_backoff_range(self, attempt, expected_min, expected_max):
        backoff = compute_backoff(attempt, min_base_delay=0.1, max_base_delay=1.0)
        assert expected_min <= backoff <= expected_max

    def test_backoff_caps_for_max_int_attempt(self):
        backoff = compute_backoff(sys.maxsize, min_base_delay=0.1, max_base_delay=1.0)
        assert 1.0 <= backoff <= 2.0
