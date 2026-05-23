import json
from typing import Any, cast

import pytest

from s2_sdk import S2, EnsureStatus, Operation
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


def _location_response(
    name: str = "aws:us-east-1", is_private: bool = False
) -> dict[str, Any]:
    return {"name": name, "is_private": is_private}


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


@pytest.mark.asyncio
async def test_list_locations() -> None:
    s2 = S2("token")
    client = _FakeAccountClient(
        Response(
            200,
            json.dumps(
                [
                    _location_response("aws:us-east-1"),
                    _location_response("private-a", is_private=True),
                ]
            ).encode(),
        )
    )
    cast(Any, s2)._account_client = client

    try:
        locations = await s2.list_locations()
    finally:
        await s2.close()

    assert [loc.name for loc in locations] == ["aws:us-east-1", "private-a"]
    assert [loc.is_private for loc in locations] == [False, True]
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    assert method == "GET"
    assert path == "/v1/locations"
    assert kwargs == {}


@pytest.mark.asyncio
async def test_get_default_location() -> None:
    s2 = S2("token")
    client = _FakeAccountClient(
        Response(200, json.dumps(_location_response("aws:us-west-2")).encode())
    )
    cast(Any, s2)._account_client = client

    try:
        location = await s2.get_default_location()
    finally:
        await s2.close()

    assert location.name == "aws:us-west-2"
    assert location.is_private is False
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    assert method == "GET"
    assert path == "/v1/locations/default"
    assert kwargs == {}


@pytest.mark.asyncio
async def test_set_default_location() -> None:
    s2 = S2("token")
    client = _FakeAccountClient(
        Response(200, json.dumps(_location_response("aws:us-west-2")).encode())
    )
    cast(Any, s2)._account_client = client

    try:
        location = await s2.set_default_location("aws:us-west-2")
    finally:
        await s2.close()

    assert location.name == "aws:us-west-2"
    assert location.is_private is False
    assert len(client.calls) == 1
    method, path, kwargs = client.calls[0]
    assert method == "PUT"
    assert path == "/v1/locations/default"
    assert kwargs["json"] == "aws:us-west-2"


def test_location_operations_are_available() -> None:
    assert Operation.LIST_LOCATIONS.value == "list-locations"
    assert Operation.GET_DEFAULT_LOCATION.value == "get-default-location"
    assert Operation.SET_DEFAULT_LOCATION.value == "set-default-location"
