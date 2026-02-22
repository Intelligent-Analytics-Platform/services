"""Authentication utilities: password hashing and JWT token management."""

from datetime import UTC, datetime, timedelta

import bcrypt
from jwt import InvalidTokenError, decode, encode

from common.exceptions import AuthenticationError


def get_password_hash(password: str) -> str:
    """Return the bcrypt hash of a password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the hashed password."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    data: dict,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT with an expiration claim."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return encode(to_encode, secret_key, algorithm=algorithm)


def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> dict:
    """Decode and verify a JWT, returning its payload.

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    try:
        return decode(token, secret_key, algorithms=[algorithm])
    except InvalidTokenError as err:
        raise AuthenticationError("Could not validate credentials") from err
