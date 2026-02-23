"""Database connections for the data service.

Two databases are used:
- SQLite (via SQLAlchemy): VesselDataUpload upload records
- DuckDB: VesselOriginalData, VesselStandardData, VesselDataPerDay (columnar analytics)
"""

from collections.abc import Generator

import duckdb
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from data.config import settings

# ── SQLite (upload records) ─────────────────────────────────────────────────

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

_SessionFactory = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── DuckDB (analytics tables) ────────────────────────────────────────────────

_TELEMETRY_COLS = """
    vessel_id   INTEGER NOT NULL,
    speed_ground DOUBLE,
    speed_water  DOUBLE,
    draft        DOUBLE,
    heel         DOUBLE,
    trim         DOUBLE,
    draught_astern    DOUBLE,
    draught_bow       DOUBLE,
    draught_mid_left  DOUBLE,
    draught_mid_right DOUBLE,
    me_rpm                    DOUBLE,
    wind_speed                DOUBLE,
    wind_direction            DOUBLE,
    slip_ratio                DOUBLE,
    me_fuel_consumption_nmile DOUBLE,
    me_fuel_consumption_kwh   DOUBLE,
    me_shaft_power            DOUBLE,
    me_torque                 DOUBLE,
    latitude  VARCHAR,
    longitude VARCHAR,
    me_hfo_act_cons  DOUBLE,
    me_mgo_act_cons  DOUBLE,
    me_hfo_acc_cons  DOUBLE,
    blr_hfo_act_cons DOUBLE,
    blr_mgo_act_cons DOUBLE,
    dg_hfo_act_cons  DOUBLE,
    dg_mgo_act_cons  DOUBLE,
    dg_hfo_acc_cons  DOUBLE,
    dg_mgo_acc_cons  DOUBLE,
    fcm_fo_density   DOUBLE,
    blr_fo_density   DOUBLE,
    blr_mgo_density  DOUBLE,
    dg_fo_density    DOUBLE,
    dg_mgo_density   DOUBLE,
    me_fo_in_temp    DOUBLE,
    blr_fo_in_temp   DOUBLE,
    blr_mgo_in_temp  DOUBLE,
    dg_fo_in_temp    DOUBLE,
    dg_mgo_in_temp   DOUBLE,
    dg1_power DOUBLE,
    dg2_power DOUBLE,
    dg3_power DOUBLE,
    ship_nmile     DOUBLE,
    true_h         DOUBLE DEFAULT 0.0,
    total_distance DOUBLE DEFAULT 0.0,
    water_depth    DOUBLE DEFAULT 0.0,
    rudder_angle   DOUBLE DEFAULT 0.0,
    water_temp     DOUBLE DEFAULT 0.0,
    swell_height   DOUBLE DEFAULT 0.0,
    date DATE NOT NULL,
    time TIME
"""

_CREATE_ORIGINAL = f"""
CREATE SEQUENCE IF NOT EXISTS vessel_original_data_seq;
CREATE TABLE IF NOT EXISTS vessel_original_data (
    id BIGINT DEFAULT nextval('vessel_original_data_seq') PRIMARY KEY,
    {_TELEMETRY_COLS},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_orig_vessel_date
    ON vessel_original_data (vessel_id, date);
"""

_CREATE_STANDARD = f"""
CREATE SEQUENCE IF NOT EXISTS vessel_standard_data_seq;
CREATE TABLE IF NOT EXISTS vessel_standard_data (
    id BIGINT DEFAULT nextval('vessel_standard_data_seq') PRIMARY KEY,
    {_TELEMETRY_COLS},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_std_vessel_date
    ON vessel_standard_data (vessel_id, date);
"""

_CREATE_PER_DAY = """
CREATE TABLE IF NOT EXISTS vessel_data_per_day (
    vessel_id INTEGER NOT NULL,
    date      DATE    NOT NULL,
    speed_ground DOUBLE,
    speed_water  DOUBLE,
    draft        DOUBLE,
    heel         DOUBLE,
    trim         DOUBLE,
    draught_astern    DOUBLE,
    draught_bow       DOUBLE,
    draught_mid_left  DOUBLE,
    draught_mid_right DOUBLE,
    me_rpm                    DOUBLE,
    wind_speed                DOUBLE,
    wind_direction            DOUBLE,
    slip_ratio                DOUBLE,
    me_fuel_consumption_nmile DOUBLE,
    me_fuel_consumption_kwh   DOUBLE,
    me_shaft_power            DOUBLE,
    me_torque                 DOUBLE,
    me_hfo_act_cons  DOUBLE,
    me_mgo_act_cons  DOUBLE,
    me_hfo_acc_cons  DOUBLE,
    blr_hfo_act_cons DOUBLE,
    blr_mgo_act_cons DOUBLE,
    dg_hfo_act_cons  DOUBLE,
    dg_mgo_act_cons  DOUBLE,
    dg_hfo_acc_cons  DOUBLE,
    dg_mgo_acc_cons  DOUBLE,
    fcm_fo_density   DOUBLE,
    blr_fo_density   DOUBLE,
    blr_mgo_density  DOUBLE,
    dg_fo_density    DOUBLE,
    dg_mgo_density   DOUBLE,
    me_fo_in_temp    DOUBLE,
    blr_fo_in_temp   DOUBLE,
    blr_mgo_in_temp  DOUBLE,
    dg_fo_in_temp    DOUBLE,
    dg_mgo_in_temp   DOUBLE,
    dg1_power DOUBLE,
    dg2_power DOUBLE,
    dg3_power DOUBLE,
    ship_nmile     DOUBLE,
    true_h         DOUBLE DEFAULT 0.0,
    total_distance DOUBLE DEFAULT 0.0,
    water_depth    DOUBLE DEFAULT 0.0,
    rudder_angle   DOUBLE DEFAULT 0.0,
    water_temp     DOUBLE DEFAULT 0.0,
    swell_height   DOUBLE DEFAULT 0.0,
    cii_temp DOUBLE DEFAULT 0.0,
    cii      DOUBLE DEFAULT 0.0,
    PRIMARY KEY (vessel_id, date)
);
"""


def get_duck_conn() -> duckdb.DuckDBPyConnection:
    """Return a new DuckDB connection (caller responsible for closing)."""
    return duckdb.connect(settings.duck_db_path)


def init_duck_db() -> None:
    """Create DuckDB tables if they don't exist."""
    with duckdb.connect(settings.duck_db_path) as conn:
        for stmt in _CREATE_ORIGINAL.split(";"):
            if stmt.strip():
                conn.execute(stmt)
        for stmt in _CREATE_STANDARD.split(";"):
            if stmt.strip():
                conn.execute(stmt)
        for stmt in _CREATE_PER_DAY.split(";"):
            if stmt.strip():
                conn.execute(stmt)
