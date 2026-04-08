"""Documentation examples for Account and Basins page.

These snippets are extracted by the docs build script.

Run with: python examples/docs/account_and_basins.py
Requires: S2_ACCESS_TOKEN, S2_BASIN environment variables

Note: These examples create resources with hardcoded names.
They may fail on repeated runs if resources already exist.
"""

import asyncio
import os
from datetime import datetime, timezone

from s2_sdk import (
    S2,
    AccessTokenScope,
    OperationGroupPermissions,
    Permission,
    PrefixMatch,
)

access_token = os.environ["S2_ACCESS_TOKEN"]
basin_name = os.environ["S2_BASIN"]


async def main():
    async with S2(access_token) as client:
        # ANCHOR: basin-operations
        # List basins
        basins = await client.list_basins()

        # Create a basin
        await client.create_basin("my-events")

        # Get configuration
        config = await client.get_basin_config("my-events")

        # Delete
        await client.delete_basin("my-events")
        # ANCHOR_END: basin-operations
        print(f"Basins: {len(basins.items)} found, config: {config}")

        basin = client.basin(basin_name)

        # ANCHOR: stream-operations
        # List streams
        streams = await basin.list_streams(prefix="user-")

        # Create a stream
        await basin.create_stream(
            "user-actions",
            # config=StreamConfig(...)  # optional
        )

        # Get configuration
        config = await basin.get_stream_config("user-actions")

        # Delete
        await basin.delete_stream("user-actions")
        # ANCHOR_END: stream-operations
        print(f"Streams: {len(streams.items)} found, config: {config}")

        # ANCHOR: access-token-basic
        # List tokens (returns metadata, not the secret)
        tokens = await client.list_access_tokens()

        # Issue a token scoped to streams under "users/1234/"
        issued_token = await client.issue_access_token(
            "user-1234-rw-token",
            scope=AccessTokenScope(
                basins=PrefixMatch(""),  # all basins
                streams=PrefixMatch("users/1234/"),
                op_groups=OperationGroupPermissions(
                    stream=Permission.READ_WRITE,
                ),
            ),
            expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        )

        # Revoke a token
        await client.revoke_access_token("user-1234-rw-token")
        # ANCHOR_END: access-token-basic
        print(f"Tokens: {len(tokens.items)} found, issued: {bool(issued_token)}")

        # ANCHOR: pagination
        # Iterate through all streams with automatic pagination
        async for stream in basin.list_all_streams():
            print(stream.name)
        # ANCHOR_END: pagination

        # ANCHOR: pagination-filtering
        # List streams with a prefix filter
        async for stream in basin.list_all_streams(prefix="events/"):
            print(stream.name)
        # ANCHOR_END: pagination-filtering

        # ANCHOR: pagination-deleted
        # Include streams that are being deleted
        async for stream in basin.list_all_streams(include_deleted=True):
            print(stream.name, stream.deleted_at)
        # ANCHOR_END: pagination-deleted

    print("Account and basins examples completed")


if __name__ == "__main__":
    asyncio.run(main())
