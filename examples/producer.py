import asyncio
import logging
import os
import random

from s2_sdk import S2, Endpoints, Record

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


async def main():
    endpoints = (
        Endpoints(account=ACCOUNT_ENDPOINT, basin=BASIN_ENDPOINT)
        if ACCOUNT_ENDPOINT and BASIN_ENDPOINT
        else None
    )
    async with S2(ACCESS_TOKEN, endpoints=endpoints) as s2:
        stream = s2[BASIN][STREAM]
        async with stream.producer() as producer:
            # Pipeline submits without waiting for acks for high throughput.
            tickets = []
            for _ in range(100000):
                body_size = random.randint(1, 1024)
                ticket = await producer.submit(Record(body=os.urandom(body_size)))
                tickets.append(ticket)

            # Wait for all acks after submitting everything.
            for ticket in tickets:
                ack = await ticket
                logger.info("ack rcvd, seq_num=%d", ack.seq_num)


if __name__ == "__main__":
    asyncio.run(main())
