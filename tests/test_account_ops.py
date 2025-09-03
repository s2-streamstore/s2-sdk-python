import time

import pytest

from streamstore import S2, Basin
from streamstore.schemas import (
    AccessTokenScope,
    BasinConfig,
    BasinScope,
    BasinState,
    Operation,
    OperationGroupPermissions,
    Permission,
    ResourceMatchOp,
    ResourceMatchRule,
    StorageClass,
    StreamConfig,
    Timestamping,
    TimestampingMode,
)


@pytest.mark.account
class TestAccountOperations:
    async def test_create_basin(self, s2: S2, basin_name: str):
        basin_info = await s2.create_basin(name=basin_name)

        try:
            assert basin_info.name == basin_name
            assert basin_info.scope == BasinScope.AWS_US_EAST_1
            assert basin_info.state in (BasinState.ACTIVE, BasinState.CREATING)
        finally:
            await s2.delete_basin(basin_name)

    async def test_create_basin_with_config(self, s2: S2, basin_name: str):
        config = BasinConfig(
            default_stream_config=StreamConfig(
                storage_class=StorageClass.STANDARD,
                retention_policy=86400 * 7,
                timestamping=Timestamping(
                    mode=TimestampingMode.CLIENT_REQUIRE,
                    uncapped=True,
                ),
                delete_on_empty_min_age=3600,
            ),
            create_stream_on_append=True,
        )

        basin_info = await s2.create_basin(name=basin_name, config=config)

        try:
            assert basin_info.name == basin_name

            retrieved_config = await s2.get_basin_config(basin_name)
            assert config == retrieved_config
        finally:
            await s2.delete_basin(basin_name)

    async def test_reconfigure_basin(self, s2: S2, basin: Basin):
        config = BasinConfig(
            default_stream_config=StreamConfig(
                storage_class=StorageClass.STANDARD,
                retention_policy=3600,
            ),
            create_stream_on_append=True,
        )

        updated_config = await s2.reconfigure_basin(basin.name, config)

        assert config.default_stream_config is not None
        assert (
            updated_config.default_stream_config.storage_class
            == config.default_stream_config.storage_class
        )
        assert (
            updated_config.default_stream_config.retention_policy
            == config.default_stream_config.retention_policy
        )
        assert updated_config.create_stream_on_append == config.create_stream_on_append

        assert (
            updated_config.default_stream_config.timestamping.mode
            == TimestampingMode.UNSPECIFIED
        )

        assert updated_config.default_stream_config.delete_on_empty_min_age == 0

    async def test_list_basins(self, s2: S2, basin_names: list[str]):
        basin_infos = []
        try:
            for basin_name in basin_names:
                stream_info = await s2.create_basin(name=basin_name)
                basin_infos.append(stream_info)

            page = await s2.list_basins()

            retrieved_basin_names = [b.name for b in page.items]
            assert set(basin_names).issubset(retrieved_basin_names)

        finally:
            for basin_info in basin_infos:
                await s2.delete_basin(basin_info.name)

    async def test_list_basins_with_limit(self, s2: S2, basin_names: list[str]):
        basin_infos = []
        try:
            for basin_name in basin_names:
                stream_info = await s2.create_basin(name=basin_name)
                basin_infos.append(stream_info)

            page = await s2.list_basins(limit=1)

            assert len(page.items) == 1

        finally:
            for basin_info in basin_infos:
                await s2.delete_basin(basin_info.name)

    async def test_list_basins_with_prefix(self, s2: S2, basin_name: str):
        await s2.create_basin(name=basin_name)

        try:
            prefix = basin_name[:5]
            page = await s2.list_basins(prefix=prefix)

            basin_names = [b.name for b in page.items]
            assert basin_name in basin_names

            for name in basin_names:
                assert name.startswith(prefix)

        finally:
            await s2.delete_basin(basin_name)

    async def test_issue_access_token(self, s2: S2, token_id: str, basin_prefix: str):
        scope = AccessTokenScope(
            basins=ResourceMatchRule(
                match_op=ResourceMatchOp.PREFIX, value=basin_prefix
            ),
            streams=ResourceMatchRule(match_op=ResourceMatchOp.PREFIX, value=""),
            op_group_perms=OperationGroupPermissions(
                basin=Permission.READ,
                stream=Permission.READ,
            ),
        )

        token = await s2.issue_access_token(id=token_id, scope=scope)

        try:
            assert isinstance(token, str)
            assert len(token) > 0
        finally:
            token_info = await s2.revoke_access_token(token_id)
            assert token_info.scope == scope

    async def test_issue_access_token_with_expiry(self, s2: S2, token_id: str):
        expires_at = int(time.time()) + 3600

        scope = AccessTokenScope(
            streams=ResourceMatchRule(match_op=ResourceMatchOp.PREFIX, value=""),
            ops=[Operation.READ, Operation.CHECK_TAIL],
        )

        token = await s2.issue_access_token(
            id=token_id,
            scope=scope,
            expires_at=expires_at,
        )

        try:
            assert isinstance(token, str)
            assert len(token) > 0

            page = await s2.list_access_tokens(prefix=token_id)

            token_info = next((t for t in page.items if t.id == token_id), None)
            assert token_info is not None
            assert token_info.expires_at == expires_at
            assert token_info.scope.streams == scope.streams
            assert set(token_info.scope.ops) == set(scope.ops)

        finally:
            await s2.revoke_access_token(token_id)

    async def test_issue_access_token_with_auto_prefix(self, s2: S2, token_id: str):
        scope = AccessTokenScope(
            streams=ResourceMatchRule(match_op=ResourceMatchOp.PREFIX, value="prefix/"),
            op_group_perms=OperationGroupPermissions(stream=Permission.READ_WRITE),
        )

        token = await s2.issue_access_token(
            id=token_id,
            scope=scope,
            auto_prefix_streams=True,
        )

        try:
            assert isinstance(token, str)
            assert len(token) > 0

            page = await s2.list_access_tokens(prefix=token_id, limit=1)

            assert len(page.items) == 1

            token_info = page.items[0]
            assert token_info is not None
            assert token_info.scope == scope
            assert token_info.auto_prefix_streams is True

        finally:
            await s2.revoke_access_token(token_id)
