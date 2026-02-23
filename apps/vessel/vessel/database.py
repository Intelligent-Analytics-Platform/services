"""Database engine and session dependency for the vessel service."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vessel.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

_SessionFactory = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)


def get_db():
    """FastAPI dependency that yields a database session."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
