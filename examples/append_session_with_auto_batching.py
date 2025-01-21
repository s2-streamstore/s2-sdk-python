import asyncio
import os
import random
from datetime import timedelta
from typing import AsyncIterable

from streamstore import S2
from streamstore.schemas import Record
from streamstore.utils import append_inputs_gen

AUTH_TOKEN = os.getenv("S2_AUTH_TOKEN")
MY_BASIN = os.getenv("MY_BASIN")
MY_STREAM = os.getenv("MY_STREAM")


async def records_gen() -> AsyncIterable[Record]:
    num_records = random.randint(1, 100)
    for _ in range(num_records):
        body_size = random.randint(1, 1024)
        if random.random() < 0.5:
            await asyncio.sleep(random.random() * 2.5)
        yield Record(body=os.urandom(body_size))


async def producer():
    async with S2(auth_token=AUTH_TOKEN) as s2:
        stream = s2[MY_BASIN][MY_STREAM]
        async for output in stream.append_session(
            append_inputs_gen(
                records=records_gen(),
                max_records_per_batch=10,
                max_linger_per_batch=timedelta(milliseconds=5),
            )
        ):
            num_appended_records = output.end_seq_num - output.start_seq_num
            print(f"appended {num_appended_records} records")


if __name__ == "__main__":
    asyncio.run(producer())
