"""Test fixtures for the data service."""

import io

import duckdb
import pytest
from common.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from data.app import create_app
from data.config import Settings
from data.database import get_db, init_duck_db


# ── Minimal valid CSV for upload tests ──────────────────────────────────────

_HEADER = (
    "speed_ground,speed_water,heel,trim,draught_astern,draught_bow,draught_mid_left,"
    "draught_mid_right,me_rpm,wind_speed,wind_direction,slip_ratio,"
    "me_fuel_consumption_nmile,me_fuel_consumption_kwh,me_shaft_power,me_torque,"
    "latitude,longitude,me_hfo_act_cons,me_mgo_act_cons,me_hfo_acc_cons,"
    "blr_hfo_act_cons,blr_mgo_act_cons,dg_hfo_act_cons,dg_mgo_act_cons,"
    "dg_hfo_acc_cons,dg_mgo_acc_cons,fcm_fo_density,blr_fo_density,blr_mgo_density,"
    "dg_fo_density,dg_mgo_density,me_fo_in_temp,blr_fo_in_temp,blr_mgo_in_temp,"
    "dg_fo_in_temp,dg_mgo_in_temp,dg1_power,dg2_power,dg3_power,ship_nmile,"
    "true_h,total_distance,water_depth,rudder_angle,water_temp,swell_height,date,time"
)

_ROW_TEMPLATE = (
    "12.0,11.5,0.5,0.2,8.5,7.2,8.0,8.0,"
    "80.0,5.0,90.0,5.0,10.0,1.0,"
    "5000.0,60000.0,31.2345N,121.4567E,2.5,0.0,100.0,"
    "0.5,0.0,0.3,0.0,50.0,0.0,"
    "980.0,980.0,850.0,980.0,850.0,"
    "80.0,80.0,80.0,80.0,80.0,"
    "200.0,200.0,0.0,0.3,0.0,500.0,50.0,"
    "2.0,20.0,0.5,{date},10:00:00"
)

SAMPLE_CSV = "\n".join(
    [_HEADER]
    + [_ROW_TEMPLATE.format(date=f"2024/01/1{i}") for i in range(5, 8)]
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_duck_path(tmp_path):
    """Temp DuckDB file, pre-initialized with schema."""
    path = str(tmp_path / "test.duckdb")
    import data.database as db_module

    orig = db_module.settings
    db_module.settings = Settings(duck_db_path=path)
    init_duck_db()
    db_module.settings = orig
    return path


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
def client(engine, tmp_duck_path, tmp_path):
    """TestClient with in-memory SQLite + temp DuckDB.

    Patches background-task helpers so process_upload uses test DB:
    - data.database.settings  → DuckDB → tmp file
    - data.service._SessionFactory → SQLite → in-memory
    - data.service.get_duck_conn → DuckDB → tmp file
    - data.router.settings     → upload_dir → tmp_path
    """
    import data.database as db_module
    import data.router as router_module
    import data.service as svc_module

    test_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    test_duck_settings = Settings(duck_db_path=tmp_duck_path)

    orig_db_settings = db_module.settings
    orig_svc_factory = svc_module._SessionFactory
    orig_svc_duck = svc_module.get_duck_conn
    orig_router_settings = router_module.settings

    db_module.settings = test_duck_settings
    svc_module._SessionFactory = test_factory
    svc_module.get_duck_conn = lambda: duckdb.connect(tmp_duck_path)
    router_module.settings = Settings(
        duck_db_path=tmp_duck_path,
        upload_dir=str(tmp_path / "uploads"),
    )

    def override_get_db():
        sess = test_factory()
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

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    db_module.settings = orig_db_settings
    svc_module._SessionFactory = orig_svc_factory
    svc_module.get_duck_conn = orig_svc_duck
    router_module.settings = orig_router_settings
