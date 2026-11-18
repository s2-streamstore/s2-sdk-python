from s2_sdk import Operation, Unknown
from s2_sdk._mappers import (
    access_token_info_from_json,
    access_token_info_to_json,
    location_info_from_json,
    network_policy_info_from_json,
)


def test_unknown_values_survive_parsing():
    # A newer service can return values this SDK version does not know.
    info = access_token_info_from_json(
        {
            "id": "t",
            "scope": {
                "basins": {"some-future-match": "x"},
                "ops": ["read", "some-future-op"],
            },
        }
    )
    assert info.scope.basins == Unknown("some-future-match")
    assert info.scope.ops[0] is Operation.READ
    # An unknown operation is sent back by name; the service decides.
    body = access_token_info_to_json(info.id, info.scope, False, None)
    assert body["scope"]["ops"] == ["read", "some-future-op"]
    policy = network_policy_info_from_json(
        {
            "id": "p.abc",
            "slug": "p",
            "created_at": "2026-01-01T00:00:00Z",
            "policy": {
                "public_net": {"some-future-kind": {}},
                "private_net": {"aws": {"vpce_ids": ["vpce-0123456789abcdef0"]}},
            },
        }
    ).policy
    assert policy.public_net == Unknown("some-future-kind")
    location = location_info_from_json(
        {
            "name": "gcp:us-east4",
            "is_private": False,
            "private_net": {"some-future-kind": {}},
        }
    )
    assert location.private_net == Unknown("some-future-kind")
