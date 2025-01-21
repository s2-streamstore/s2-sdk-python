import asyncio
import os
import random
from typing import AsyncIterable

from streamstore import S2
from streamstore.schemas import AppendInput, Record

AUTH_TOKEN = os.getenv("S2_AUTH_TOKEN")
MY_BASIN = os.getenv("MY_BASIN")
MY_STREAM = os.getenv("MY_STREAM")


async def append_inputs_gen() -> AsyncIterable[AppendInput]:
    num_inputs = random.randint(1, 100)
    for _ in range(num_inputs):
        num_records = random.randint(1, 100)
        records = []
        for _ in range(num_records):
            body_size = random.randint(1, 1024)
            records.append(Record(body=os.urandom(body_size)))
        input = AppendInput(records)
        if random.random() < 0.5:
            await asyncio.sleep(random.random() * 2.5)
        yield input


async def producer():
    async with S2(auth_token=AUTH_TOKEN) as s2:
        stream = s2[MY_BASIN][MY_STREAM]
        async for output in stream.append_session(append_inputs_gen()):
            num_appended_records = output.end_seq_num - output.start_seq_num
            print(f"appended {num_appended_records} records")


if __name__ == "__main__":
    asyncio.run(producer())
