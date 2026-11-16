from s2_sdk import Operation, Unknown
from s2_sdk._mappers import access_token_info_from_json, access_token_info_to_json


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
    assert isinstance(info.scope.basins, Unknown)
    assert info.scope.basins.kind == "some-future-match"
    assert info.scope.ops[0] is Operation.READ
    # Unknown values are sent back as received; the service decides.
    body = access_token_info_to_json(info.id, info.scope, False, None)
    assert body["scope"]["basins"] == {"some-future-match": "x"}
    assert body["scope"]["ops"] == ["read", "some-future-op"]
