"""Documentation examples for Metrics page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/metrics.py
Requires: S2_ACCESS_TOKEN environment variable
"""

import asyncio
import os
import time

from s2_sdk import (
    S2,
    AccountMetricSet,
    BasinMetricSet,
    StreamMetricSet,
    TimeseriesInterval,
)

access_token = os.environ["S2_ACCESS_TOKEN"]


async def main():
    async with S2(access_token) as client:
        # ANCHOR: metrics
        now = int(time.time())
        thirty_days_ago = now - 30 * 24 * 3600
        six_hours_ago = now - 6 * 3600
        hour_ago = now - 3600

        # Account-level: active basins over the last 30 days
        account_metrics = await client.account_metrics(
            set=AccountMetricSet.ACTIVE_BASINS,
            start=thirty_days_ago,
            end=now,
        )

        # Basin-level: storage usage with hourly resolution
        basin_metrics = await client.basin_metrics(
            "events",
            set=BasinMetricSet.STORAGE,
            start=six_hours_ago,
            end=now,
            interval=TimeseriesInterval.HOUR,
        )

        # Stream-level: storage for a specific stream
        stream_metrics = await client.stream_metrics(
            "events",
            "user-actions",
            set=StreamMetricSet.STORAGE,
            start=hour_ago,
            end=now,
            interval=TimeseriesInterval.MINUTE,
        )
        # ANCHOR_END: metrics

        print(account_metrics, basin_metrics, stream_metrics)


if __name__ == "__main__":
    asyncio.run(main())
