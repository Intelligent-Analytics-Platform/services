"""Tests for authentication utilities."""

from datetime import timedelta

import pytest
from common.auth import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from common.exceptions import AuthenticationError

SECRET = "test-secret-key"


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed)

    def test_wrong_password(self):
        hashed = get_password_hash("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("secret")
        assert hashed != "secret"


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token({"sub": "42"}, secret_key=SECRET)
        payload = decode_token(token, secret_key=SECRET)
        assert payload["sub"] == "42"
        assert "exp" in payload

    def test_custom_algorithm(self):
        token = create_access_token({"sub": "1"}, secret_key=SECRET, algorithm="HS256")
        payload = decode_token(token, secret_key=SECRET, algorithm="HS256")
        assert payload["sub"] == "1"

    def test_custom_expiry(self):
        delta = timedelta(hours=2)
        token = create_access_token({"sub": "1"}, secret_key=SECRET, expires_delta=delta)
        payload = decode_token(token, secret_key=SECRET)
        assert payload["sub"] == "1"

    def test_expired_token(self):
        token = create_access_token(
            {"sub": "1"}, secret_key=SECRET, expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(AuthenticationError):
            decode_token(token, secret_key=SECRET)

    def test_invalid_token(self):
        with pytest.raises(AuthenticationError):
            decode_token("not-a-valid-token", secret_key=SECRET)

    def test_wrong_secret(self):
        token = create_access_token({"sub": "1"}, secret_key=SECRET)
        with pytest.raises(AuthenticationError):
            decode_token(token, secret_key="wrong-key")
