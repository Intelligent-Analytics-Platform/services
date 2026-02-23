"""Test fixtures for the analytics service."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from unittest.mock import patch

import duckdb
import pytest
from fastapi.testclient import TestClient

# ── Temp DuckDB with minimal schema ──────────────────────────────────────────

_CREATE_PER_DAY = """
CREATE TABLE vessel_data_per_day (
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
    blr_hfo_act_cons DOUBLE,
    blr_mgo_act_cons DOUBLE,
    dg_hfo_act_cons  DOUBLE,
    dg_mgo_act_cons  DOUBLE,
    ship_nmile     DOUBLE,
    cii_temp DOUBLE DEFAULT 0.0,
    cii      DOUBLE DEFAULT 0.0,
    PRIMARY KEY (vessel_id, date)
);
"""

_CREATE_STD = """
CREATE TABLE vessel_standard_data (
    id BIGINT PRIMARY KEY,
    vessel_id INTEGER NOT NULL,
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
    ship_nmile DOUBLE,
    date DATE NOT NULL,
    time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@pytest.fixture(scope="session")
def duck_db_path() -> Generator[str, None, None]:
    """Create a temporary DuckDB with seed data for the test session."""
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, "test_analytics.duckdb")
    # Note: do NOT pre-create the file — DuckDB initialises it on first connect.

    conn = duckdb.connect(path)
    conn.execute(_CREATE_PER_DAY)
    conn.execute(_CREATE_STD)

    # Seed vessel_data_per_day
    conn.execute(
        """
        INSERT INTO vessel_data_per_day VALUES
        (1, '2023-01-01', 12.0, 11.5, 7.0, 0.1, 0.5, 6.8, 7.2, NULL, NULL,
         120.0, 8.0, 180.0, 5.0, 45.0, 220.0, 3200.0, 500.0,
         20.0, 0.0, 2.0, 0.0, 1.5, 0.0, 10.0, 5.0, 3.0),
        (1, '2023-01-02', 11.5, 11.0, 7.1, 0.2, 0.6, 6.9, 7.3, NULL, NULL,
         118.0, 9.0, 190.0, 4.5, 44.0, 215.0, 3100.0, 490.0,
         18.0, 0.0, 1.8, 0.0, 1.4, 0.0, 9.5, 4.8, 2.8)
        """
    )
    # Seed vessel_standard_data
    conn.execute(
        """
        INSERT INTO vessel_standard_data
        (id, vessel_id, speed_ground, speed_water, draft, heel, trim,
         draught_astern, draught_bow, draught_mid_left, draught_mid_right,
         me_rpm, wind_speed, wind_direction, slip_ratio,
         me_fuel_consumption_nmile, me_fuel_consumption_kwh, me_shaft_power,
         me_torque, latitude, longitude, ship_nmile, date, time)
        VALUES
        (1, 1, 12.0, 11.5, 7.0, 0.1, 0.5, 6.8, 7.2, NULL, NULL,
         120.0, 8.0, 180.0, 5.0, 45.0, 220.0, 3200.0, 500.0,
         '37.5N', '121.3E', 10.0, '2023-01-01', '08:00:00'),
        (2, 1, 11.5, 11.0, 7.1, 0.2, 0.6, 6.9, 7.3, NULL, NULL,
         118.0, 9.0, 190.0, 4.5, 44.0, 215.0, 3100.0, 490.0,
         '37.6N', '121.4E', 9.5, '2023-01-02', '08:00:00')
        """
    )
    conn.close()

    yield path

    import shutil

    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture()
def client(duck_db_path: str) -> Generator[TestClient, None, None]:
    """FastAPI test client with DuckDB path patched."""
    from analytics.app import create_app

    with (
        patch("analytics.config.settings.duck_db_path", duck_db_path),
        patch("analytics.database.settings.duck_db_path", duck_db_path),
    ):
        app = create_app()
        yield TestClient(app)
