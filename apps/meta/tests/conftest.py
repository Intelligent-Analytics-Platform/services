"""Test fixtures for the meta service."""

from pathlib import Path

import pytest
from common.models import Base
from fastapi.testclient import TestClient
from meta.app import create_app
from meta.database import get_db
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_SEED_SQL = Path(__file__).parent.parent / "meta" / "seed.sql"


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def seed_data(engine):
    """Seed reference data by executing the same SQL file used in production."""
    with engine.connect() as conn:
        for stmt in _SEED_SQL.read_text().split(";"):
            if stmt.strip():
                conn.execute(text(stmt.strip()))
        conn.commit()


@pytest.fixture
def client(engine, seed_data):
    """Create a test client with an in-memory database."""
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        sess = factory()
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
