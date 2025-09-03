import pytest

from streamstore import Basin, Stream
from streamstore.schemas import (
    StorageClass,
    StreamConfig,
    Timestamping,
    TimestampingMode,
)


@pytest.mark.basin
class TestBasinOperations:
    async def test_create_stream(self, shared_basin: Basin, stream_name: str):
        basin = shared_basin

        stream_info = await basin.create_stream(name=stream_name)
        try:
            assert stream_info.name == stream_name
            assert stream_info.created_at is not None
            assert stream_info.deleted_at is None

        finally:
            await basin.delete_stream(stream_name)

    async def test_create_stream_with_config(
        self, shared_basin: Basin, stream_name: str
    ):
        basin = shared_basin

        config = StreamConfig(
            storage_class=StorageClass.STANDARD,
            retention_policy=86400 * 3,
            timestamping=Timestamping(
                mode=TimestampingMode.ARRIVAL,
                uncapped=False,
            ),
            delete_on_empty_min_age=7200,
        )

        stream_info = await basin.create_stream(name=stream_name, config=config)
        try:
            assert stream_info.name == stream_name

            retrieved_config = await basin.get_stream_config(stream_name)
            assert retrieved_config == config

        finally:
            await basin.delete_stream(stream_name)

    async def test_default_stream_config(self, shared_basin: Basin, stream: Stream):
        basin = shared_basin

        config = await basin.get_stream_config(stream.name)
        assert config.storage_class == StorageClass.EXPRESS
        assert config.retention_policy == 86400 * 7

    async def test_reconfigure_stream(self, shared_basin: Basin, stream: Stream):
        basin = shared_basin
        config = StreamConfig(
            storage_class=StorageClass.STANDARD,
            retention_policy="infinite",
            timestamping=Timestamping(
                mode=TimestampingMode.CLIENT_REQUIRE, uncapped=True
            ),
            delete_on_empty_min_age=1800,
        )

        updated_config = await basin.reconfigure_stream(stream.name, config)
        assert updated_config == config

        config = StreamConfig(
            storage_class=StorageClass.EXPRESS,
            retention_policy=86400 * 90,
            timestamping=Timestamping(
                mode=TimestampingMode.CLIENT_PREFER, uncapped=False
            ),
            delete_on_empty_min_age=3600,
        )
        updated_config = await basin.reconfigure_stream(stream.name, config)
        assert updated_config == config

    async def test_list_streams(self, shared_basin: Basin, stream_names: list[str]):
        basin = shared_basin

        stream_infos = []
        try:
            for stream_name in stream_names:
                stream_info = await basin.create_stream(name=stream_name)
                stream_infos.append(stream_info)

            page = await basin.list_streams()

            retrieved_stream_names = [s.name for s in page.items]
            assert set(stream_names).issubset(retrieved_stream_names)

        finally:
            for stream_info in stream_infos:
                await basin.delete_stream(stream_info.name)

    async def test_list_streams_with_limit(
        self, shared_basin: Basin, stream_names: list[str]
    ):
        basin = shared_basin

        stream_infos = []
        try:
            for stream_name in stream_names:
                stream_info = await basin.create_stream(name=stream_name)
                stream_infos.append(stream_info)

            page = await basin.list_streams(limit=1)

            assert len(page.items) == 1

        finally:
            for stream_info in stream_infos:
                await basin.delete_stream(stream_info.name)

    async def test_list_streams_with_prefix(
        self, shared_basin: Basin, stream_name: str
    ):
        basin = shared_basin

        await basin.create_stream(name=stream_name)

        try:
            prefix = stream_name[:5]
            page = await basin.list_streams(prefix=prefix)

            stream_names = [s.name for s in page.items]
            assert stream_name in stream_names

            for name in stream_names:
                assert name.startswith(prefix)

        finally:
            await basin.delete_stream(stream_name)
