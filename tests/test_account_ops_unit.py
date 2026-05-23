import json
from typing import Any, cast

import pytest

from s2_sdk import S2, EnsureStatus
from s2_sdk._client import Response


class _FakeAccountClient:
    def __init__(self, response: Response) -> None:
        self.response = response
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def unary_request(self, method: str, path: str, **kwargs: Any) -> Response:
        self.calls.append((method, path, kwargs))
        return self.response


def _basin_response(*, headers: tuple[tuple[str, str], ...] = ()) -> Response:
    return Response(
        200,
        json.dumps(
            {
                "name": "test-basin",
                "created_at": "2026-05-22T00:00:00+00:00",
                "deleted_at": None,
                "location": "aws:us-east-1",
            }
        ).encode(),
        headers,
    )


@pytest.mark.asyncio
async def test_create_basin_sends_location() -> None:
    s2 = S2("token")
    client = _FakeAccountClient(_basin_response())
    cast(Any, s2)._account_client = client

    try:
        info = await s2.create_basin("test-basin", location="aws:us-east-1")
    finally:
        await s2.close()

    assert info.location == "aws:us-east-1"
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    assert method == "POST"
    assert path == "/v1/basins"
    assert kwargs["json"] == {
        "basin": "test-basin",
        "location": "aws:us-east-1",
    }
    assert "s2-request-token" in kwargs["headers"]


@pytest.mark.asyncio
async def test_ensure_basin_sends_location() -> None:
    s2 = S2("token")
    client = _FakeAccountClient(
        _basin_response(headers=(("s2-provision-result", "created"),))
    )
    cast(Any, s2)._account_client = client

    try:
        info = await s2.ensure_basin("test-basin", location="aws:us-east-1")
    finally:
        await s2.close()

    assert info.status is EnsureStatus.CREATED
    assert info.basin.location == "aws:us-east-1"
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    assert method == "PUT"
    assert path == "/v1/basins/test-basin"
    assert kwargs["json"] == {"location": "aws:us-east-1"}
