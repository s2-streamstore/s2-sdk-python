import asyncio
import os
import random
from typing import AsyncIterable
import logging

from streamstore import S2
from streamstore.schemas import AppendInput, Record, Endpoints

AUTH_TOKEN = os.getenv("S2_AUTH_TOKEN")
MY_BASIN = os.getenv("MY_BASIN")
MY_STREAM = os.getenv("MY_STREAM")

logging.basicConfig(level=logging.DEBUG)


async def append_inputs_gen() -> AsyncIterable[AppendInput]:
    num_inputs = random.randint(20, 21)
    for input_idx in range(num_inputs):
        num_records = random.randint(1, 100)
        records = []
        for _ in range(num_records):
            body_size = random.randint(1, 1024)
            records.append(Record(body=os.urandom(body_size)))
        input = AppendInput(records)
        if random.random() < 0.5:
            logging.info(f"waiting before yielding input {input_idx}")
            await asyncio.sleep(random.random() * 60.0)
        # if input_idx % 10000 == 0:
        #     logging.info(f"yielding input {input_idx}")
        yield input


async def producer():
    async with S2(
        auth_token=AUTH_TOKEN, endpoints=Endpoints._from_env(), max_retries=5
    ) as s2:
        stream = s2[MY_BASIN][MY_STREAM]
        async for output in stream.append_session(append_inputs_gen()):
            num_appended_records = output.end_seq_num - output.start_seq_num
            logging.info(
                f"appended {num_appended_records} records, num_tasks: {len(asyncio.all_tasks())}, all_tasks: {asyncio.all_tasks()}"
            )
            logging.info(f"appended {num_appended_records} records")


# async def check_tail():
#     async with S2(auth_token=AUTH_TOKEN, endpoints=Endpoints._from_env()) as s2:
#         stream = s2[MY_BASIN][MY_STREAM]
#         print(await stream.check_tail())


if __name__ == "__main__":
    asyncio.run(producer(), debug=True)
    # asyncio.run(check_tail(), debug=True)
