import sys

import pytest

from s2_sdk._retrier import compute_backoff


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
