"""Documentation examples for Encryption page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/encryption.py
Requires: S2_ACCESS_TOKEN, S2_BASIN, S2_ENCRYPTION_KEY environment variables
"""

import asyncio
import os
import time

from s2_sdk import (
    AppendInput,
    BasinConfig,
    EncryptionAlgorithm,
    EncryptionKey,
    ReadLimit,
    Record,
    S2,
    SeqNum,
)

access_token = os.environ["S2_ACCESS_TOKEN"]
basin_name = os.environ["S2_BASIN"]


async def main():
    if "S2_ENCRYPTION_KEY" not in os.environ:
        raise RuntimeError("S2_ENCRYPTION_KEY is required")

    async with S2(access_token) as client:
        basin = client.basin(basin_name)
        stream_name = f"docs-encryption-{int(time.time())}"

        # ANCHOR: basin-cipher
        try:
            await client.create_basin(
                basin_name,
                config=BasinConfig(stream_cipher=EncryptionAlgorithm.AEGIS_256),
            )
        except Exception:
            pass

        await client.reconfigure_basin(
            basin_name,
            config=BasinConfig(stream_cipher=EncryptionAlgorithm.AES_256_GCM),
        )
        # ANCHOR_END: basin-cipher
        
        try:
            await basin.create_stream(stream_name)
        except Exception:
            pass

        # ANCHOR: append-read
        stream = basin.stream(
            stream_name,
            encryption_key=EncryptionKey(os.environ["S2_ENCRYPTION_KEY"]),
        )

        await stream.append(
            AppendInput(
                records=[
                    Record(body=b"top secret"),
                ]
            )
        )

        batch = await stream.read(
            start=SeqNum(0),
            limit=ReadLimit(count=10),
        )
        # ANCHOR_END: append-read
        print("Encryption examples ok", len(batch.records))

        # Cleanup
        await basin.delete_stream(stream_name)

    print("Encryption examples completed")


if __name__ == "__main__":
    asyncio.run(main())
