"""Test fixtures for the identity service."""

import pytest
from common.auth import get_password_hash
from common.models import Base
from fastapi.testclient import TestClient
from identity.app import create_app
from identity.database import get_db
from identity.models import Company, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


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
def session(engine):
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sess = factory()
    yield sess
    sess.close()


@pytest.fixture
def seed_data(session: Session):
    """Insert seed data for testing."""
    companies = [
        Company(
            id=1,
            name="测试公司A",
            address="上海市浦东新区",
            contact_person="张三",
            contact_phone="13800000001",
            contact_email="a@test.com",
        ),
        Company(
            id=2,
            name="测试公司B",
            address="北京市朝阳区",
            contact_person="李四",
            contact_phone="13800000002",
            contact_email="b@test.com",
        ),
    ]
    users = [
        User(
            id=1,
            username="admin",
            hashed_password=get_password_hash("admin123"),
            phone="13900000001",
            company_id=1,
            is_admin=True,
            is_system_admin=False,
            disabled=False,
        ),
        User(
            id=2,
            username="user1",
            hashed_password=get_password_hash("user123"),
            phone="13900000002",
            company_id=1,
            is_admin=False,
            is_system_admin=False,
            disabled=False,
        ),
        User(
            id=3,
            username="disabled_user",
            hashed_password=get_password_hash("pass123"),
            phone="13900000003",
            company_id=2,
            is_admin=False,
            is_system_admin=False,
            disabled=True,
        ),
    ]
    session.add_all(companies + users)
    session.commit()


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
