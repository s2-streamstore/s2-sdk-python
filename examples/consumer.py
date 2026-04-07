import asyncio
import logging
import os

from s2_sdk import S2, Endpoints, SeqNum

logging.basicConfig(level=logging.INFO)
logging.getLogger("s2_sdk").setLevel(
    getattr(logging, os.getenv("S2_LOG_LEVEL", "INFO").upper(), logging.INFO)
)
logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.environ["S2_ACCESS_TOKEN"]
BASIN = os.environ["S2_BASIN"]
STREAM = os.environ["S2_STREAM"]
ACCOUNT_ENDPOINT = os.getenv("S2_ACCOUNT_ENDPOINT")
BASIN_ENDPOINT = os.getenv("S2_BASIN_ENDPOINT")


async def consumer():
    endpoints = (
        Endpoints(account=ACCOUNT_ENDPOINT, basin=BASIN_ENDPOINT)
        if ACCOUNT_ENDPOINT and BASIN_ENDPOINT
        else None
    )
    async with S2(ACCESS_TOKEN, endpoints=endpoints) as s2:
        stream = s2[BASIN][STREAM]
        tail = await stream.check_tail()
        logger.info("reading from tail: %s", tail)
        total_num_records = 0
        async for batch in stream.read_session(start=SeqNum(tail.seq_num)):
            total_num_records += len(batch.records)
            logger.info("read %d now, %d so far", len(batch.records), total_num_records)


if __name__ == "__main__":
    asyncio.run(consumer())
