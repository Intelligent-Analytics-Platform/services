"""FastAPI dependencies for authentication."""

from typing import Annotated

from common.auth import decode_token
from common.exceptions import AuthenticationError, EntityNotFoundError
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from identity.config import settings
from identity.database import get_db
from identity.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login", auto_error=False)


def _get_token(
    bearer_token: str | None = Depends(oauth2_scheme),
    token_header: str | None = Header(None, alias="Token"),
) -> str:
    """Accept tokens via Authorization: Bearer or a custom Token header."""
    token = bearer_token or token_header
    if not token:
        raise AuthenticationError("Not authenticated")
    return token


def get_current_user(
    token: Annotated[str, Depends(_get_token)],
    session: Session = Depends(get_db),
) -> User:
    """Resolve the currently authenticated user from the JWT token."""
    payload = decode_token(
        token, secret_key=settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    user_id = int(payload["sub"])
    user = session.get(User, user_id)
    if not user:
        raise EntityNotFoundError("User", user_id)
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the current user is not disabled."""
    if current_user.disabled:
        raise EntityNotFoundError("User", current_user.id)
    return current_user
