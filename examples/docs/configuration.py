"""Documentation examples for Configuration page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/configuration.py
Requires: S2_ACCESS_TOKEN environment variable
"""

import asyncio
import os
from datetime import timedelta

from s2_sdk import S2, Endpoints, Retry, Timeout


async def main():
    # ANCHOR: custom-endpoints
    client = S2(
        "local-token",
        endpoints=Endpoints(
            account="http://localhost:8080",
            basin="http://localhost:8080",
        ),
    )
    # ANCHOR_END: custom-endpoints
    await client.close()

    access_token = os.environ["S2_ACCESS_TOKEN"]

    # ANCHOR: retry-config
    client = S2(
        access_token,
        retry=Retry(
            max_attempts=5,
            min_base_delay=timedelta(milliseconds=100),
            max_base_delay=timedelta(seconds=2),
        ),
    )
    # ANCHOR_END: retry-config
    await client.close()

    # ANCHOR: timeout-config
    client = S2(
        access_token,
        timeout=Timeout(
            connection=timedelta(seconds=5),
            request=timedelta(seconds=10),
        ),
    )
    # ANCHOR_END: timeout-config
    await client.close()

    print("Configuration examples loaded")


if __name__ == "__main__":
    asyncio.run(main())
