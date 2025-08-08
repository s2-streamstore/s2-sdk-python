import asyncio
import os

from streamstore import S2
from streamstore.schemas import SeqNum

ACCESS_TOKEN = os.getenv("S2_ACCESS_TOKEN")
MY_BASIN = os.getenv("MY_BASIN")
MY_STREAM = os.getenv("MY_STREAM")


async def consumer():
    async with S2(access_token=ACCESS_TOKEN) as s2:
        stream = s2[MY_BASIN][MY_STREAM]
        tail = await stream.check_tail()
        print(f"reading from tail: {tail}")
        total_num_records = 0
        async for output in stream.read_session(start=SeqNum(tail.next_seq_num)):
            match output:
                case list(records):
                    total_num_records += len(records)
                    print(f"read {len(records)} now, {total_num_records} so far")
                case _:
                    raise RuntimeError(
                        "Records not received, which is unexpected as we start from the tail of the stream"
                    )


if __name__ == "__main__":
    asyncio.run(consumer())
