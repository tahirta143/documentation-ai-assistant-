"""
Unit tests for security utilities (password hashing & JWT).
"""

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    plain = "my_secure_password"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_encoding_decoding():
    user_id = 42
    token = create_access_token(subject=user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)
    assert "exp" in payload


def test_jwt_invalid_token():
    invalid = "invalid.jwt.token.string"
    payload = decode_access_token(invalid)
    assert payload is None
