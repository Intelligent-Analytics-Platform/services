"""Database engine and session utilities."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_from_url(url: str, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine from a database URL."""
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, echo=echo, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
