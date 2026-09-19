from app.security.jwt import create_access_token, decode_token


def test_access_token_contains_expected_claims():
    token = create_access_token(42, ["ADMIN"])
    payload = decode_token(token, "access")

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert payload["roles"] == ["ADMIN"]
    assert payload["jti"]
