"""Test fixtures for the meta service."""

import pytest
from common.models import Base
from fastapi.testclient import TestClient
from meta.app import create_app
from meta.database import get_db
from meta.models import FuelType, ShipType, TimeZone
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
    fuel_types = [
        FuelType(
            id=1,
            name_cn="液化天然气",
            name_en="Liquefied Natural Gas",
            name_abbr="LNG",
            cf=2.75,
        ),
        FuelType(
            id=2,
            name_cn="重油",
            name_en="Heavy Fuel Oil",
            name_abbr="HFO",
            cf=3.114,
        ),
    ]
    ship_types = [
        ShipType(
            id=1,
            name_cn="集装箱船",
            name_en="Container Ship",
            code="I1004",
            cii_related_tone="DWT",
        ),
        ShipType(
            id=2,
            name_cn="散货船",
            name_en="Bulk Carrier",
            code="I1001",
            cii_related_tone="DWT",
        ),
    ]
    time_zones = [
        TimeZone(id=1, name_cn="中国标准时间", name_en="China Standard Time", explaination="UTC+8"),
        TimeZone(id=2, name_cn="日本标准时间", name_en="Japan Standard Time", explaination="UTC+9"),
    ]

    session.add_all(fuel_types + ship_types + time_zones)
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
