from s2_sdk import Operation
from s2_sdk._mappers import access_token_info_from_json, access_token_info_to_json


def test_unknown_operation_survives_round_trip():
    # A newer service can return operations this SDK version does not know.
    info = access_token_info_from_json(
        {"id": "t", "scope": {"ops": ["read", "some-future-op"]}}
    )
    assert info.scope.ops[0] is Operation.READ
    body = access_token_info_to_json(info.id, info.scope, False, None)
    assert body["scope"]["ops"] == ["read", "some-future-op"]
