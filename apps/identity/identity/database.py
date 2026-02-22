"""Database engine and session setup for the identity service."""

from collections.abc import Generator

from common.database import create_engine_from_url, create_session_factory
from sqlalchemy.orm import Session

from identity.config import settings

engine = create_engine_from_url(settings.database_url, echo=settings.debug)
SessionLocal = create_session_factory(engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
