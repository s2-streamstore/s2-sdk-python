import asyncio
import random
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class Attempt:
    value: int


def compute_backoffs(
    attempts: int,
    wait_min: float = 0.1,
    wait_max: float = 5.0,
) -> list[float]:
    backoffs = []
    for attempt in range(attempts):
        backoffs.append(random.uniform(wait_min, min(wait_max, 2**attempt)))
    return backoffs


class Retrier:
    def __init__(
        self,
        should_retry_on: Callable[[Exception], bool],
        max_attempts: int,
    ):
        self.should_retry_on = should_retry_on
        self.max_attempts = max_attempts

    async def __call__(self, f: Callable, *args, **kwargs):
        backoffs = compute_backoffs(attempts=self.max_attempts)
        attempt = 0
        while True:
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_attempts and self.should_retry_on(e):
                    await asyncio.sleep(backoffs[attempt])
                    attempt += 1
                else:
                    raise e
