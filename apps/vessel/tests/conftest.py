"""Test fixtures for the vessel service."""

from datetime import date

import pytest
from common.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from vessel.app import create_app
from vessel.database import get_db
from vessel.models import CurveData, Equipment, EquipmentFuel, PowerSpeedCurve, Vessel


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
def seed_data(session):
    """Insert one vessel with 2 equipment and 1 power-speed curve."""
    vessel = Vessel(
        id=1,
        name="测试船舶",
        mmsi="123456789",
        build_date=date(2020, 1, 1),
        gross_tone=5000.0,
        dead_weight=3000.0,
        new_vessel=True,
        pitch=6.058,
        company_id=1,
        ship_type=1,
        time_zone=1,
    )
    session.add(vessel)
    session.flush()

    eq1 = Equipment(id=1, name="主机", type="me", vessel_id=1)
    eq2 = Equipment(id=2, name="辅机1", type="dg", vessel_id=1)
    session.add_all([eq1, eq2])
    session.flush()

    session.add_all(
        [
            EquipmentFuel(equipment_id=1, fuel_type_id=1),
            EquipmentFuel(equipment_id=1, fuel_type_id=2),
            EquipmentFuel(equipment_id=2, fuel_type_id=1),
        ]
    )

    curve = PowerSpeedCurve(
        id=1, curve_name="设计吃水", draft_astern=8.5, draft_bow=8.5, vessel_id=1
    )
    session.add(curve)
    session.flush()

    session.add_all(
        [
            CurveData(speed_water=10.0, me_power=5000.0, power_speed_curve_id=1),
            CurveData(speed_water=12.0, me_power=8000.0, power_speed_curve_id=1),
            CurveData(speed_water=14.0, me_power=12000.0, power_speed_curve_id=1),
        ]
    )
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
