import os
import uuid
from typing import AsyncGenerator, Final

import pytest
import pytest_asyncio

from streamstore import S2, Basin, Stream

pytest_plugins = ["pytest_asyncio"]


BASIN_PREFIX: Final[str] = "test-py-sdk"


@pytest.fixture(scope="session")
def access_token() -> str:
    token = os.getenv("S2_ACCESS_TOKEN")
    if not token:
        pytest.fail("S2_ACCESS_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def basin_prefix() -> str:
    return BASIN_PREFIX


@pytest_asyncio.fixture(scope="session")
async def s2(access_token: str) -> AsyncGenerator[S2, None]:
    async with S2(access_token=access_token) as client:
        yield client


@pytest.fixture
def basin_name() -> str:
    return _basin_name()


@pytest.fixture
def basin_names() -> list[str]:
    return [_basin_name() for _ in range(3)]


@pytest.fixture
def stream_name() -> str:
    return _stream_name()


@pytest.fixture
def stream_names() -> list[str]:
    return [_stream_name() for _ in range(3)]


@pytest.fixture
def token_id() -> str:
    return f"token-{uuid.uuid4().hex[:8]}"


@pytest_asyncio.fixture
async def basin(s2: S2, basin_name: str) -> AsyncGenerator[Basin, None]:
    await s2.create_basin(
        name=basin_name,
    )

    try:
        yield s2.basin(basin_name)
    finally:
        await s2.delete_basin(basin_name)


@pytest_asyncio.fixture(scope="class")
async def shared_basin(s2: S2) -> AsyncGenerator[Basin, None]:
    basin_name = _basin_name()
    await s2.create_basin(name=basin_name)

    try:
        yield s2.basin(basin_name)
    finally:
        await s2.delete_basin(basin_name)


@pytest_asyncio.fixture
async def stream(shared_basin: Basin, stream_name: str) -> AsyncGenerator[Stream, None]:
    basin = shared_basin
    await basin.create_stream(name=stream_name)

    try:
        yield basin.stream(stream_name)
    finally:
        await basin.delete_stream(stream_name)


def _basin_name() -> str:
    return f"{BASIN_PREFIX}-{uuid.uuid4().hex[:8]}"


def _stream_name() -> str:
    return f"stream-{uuid.uuid4().hex[:8]}"
