import asyncio
import os

from s2_sdk import S2


async def main():
    async with S2(os.environ["S2_ACCESS_TOKEN"]) as client:
        for location in await client.list_locations():
            print(
                location.name,
                location.storage_classes,
                location.default_storage_class,
            )


if __name__ == "__main__":
    asyncio.run(main())
