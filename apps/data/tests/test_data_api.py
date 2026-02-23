"""Tests for the data service API."""

import io

from tests.conftest import SAMPLE_CSV


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["data"]["service"] == "data"


# ── Upload endpoints ─────────────────────────────────────────────────────────


def test_upload_returns_202(client):
    files = {"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    r = client.post("/upload/vessel/1/standard", files=files)
    assert r.status_code == 202
    body = r.json()
    assert body["data"]["upload_id"] > 0
    assert "后台处理" in body["message"]


def test_upload_creates_record(client):
    files = {"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    r = client.post("/upload/vessel/1/standard", files=files)
    upload_id = r.json()["data"]["upload_id"]

    status_r = client.get(f"/upload/{upload_id}/status")
    assert status_r.status_code == 200
    data = status_r.json()["data"]
    assert data["id"] == upload_id
    assert data["vessel_id"] == 1
    # Status is pending or processing (background task may have finished)
    assert data["status"] in ("pending", "processing", "done", "failed")


def test_upload_empty_file_400(client):
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    r = client.post("/upload/vessel/1/standard", files=files)
    assert r.status_code == 400


def test_upload_non_csv_400(client):
    files = {"file": ("data.xlsx", io.BytesIO(b"fake content"), "application/vnd.ms-excel")}
    r = client.post("/upload/vessel/1/standard", files=files)
    assert r.status_code == 400


# ── History ──────────────────────────────────────────────────────────────────


def test_get_history_empty(client):
    r = client.get("/upload/vessel/99/history")
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_get_history_after_upload(client):
    files = {"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
    client.post("/upload/vessel/2/standard", files=files)
    client.post("/upload/vessel/2/standard", files={"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")})

    r = client.get("/upload/vessel/2/history")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 2


def test_get_history_pagination(client):
    for _ in range(5):
        files = {"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")}
        client.post("/upload/vessel/3/standard", files=files)

    r = client.get("/upload/vessel/3/history?limit=2&offset=0")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 2


# ── Status ───────────────────────────────────────────────────────────────────


def test_status_not_found_404(client):
    r = client.get("/upload/99999/status")
    assert r.status_code == 404


# ── Daily data ───────────────────────────────────────────────────────────────


def test_get_daily_empty(client):
    r = client.get("/daily/vessel/999")
    assert r.status_code == 200
    assert r.json()["data"] == []


# ── Pipeline unit tests ───────────────────────────────────────────────────────


def test_get_cf_hfo():
    from data.pipeline import get_cf

    assert get_cf("me_hfo_act_cons") == 3.114


def test_get_cf_mgo():
    from data.pipeline import get_cf

    assert get_cf("blr_mgo_act_cons") == 3.206


def test_get_cf_unknown():
    from data.pipeline import get_cf

    assert get_cf("unknown_col") == 0.0


def test_data_preparation_returns_dataframe(tmp_path):
    import pandas as pd

    from data.pipeline import data_preparation

    # Build a minimal valid dataframe
    row = {
        "speed_ground": 12.0,
        "speed_water": 11.5,
        "heel": 0.5,
        "trim": 0.2,
        "draught_astern": 8.5,
        "draught_bow": 7.2,
        "draught_mid_left": 8.0,
        "draught_mid_right": 8.0,
        "me_rpm": 80.0,
        "wind_speed": 5.0,
        "wind_direction": 90.0,
        "me_fuel_consumption_nmile": 10.0,
        "me_fuel_consumption_kwh": 1.0,
        "me_shaft_power": 5000.0,
        "me_torque": 60000.0,
        "me_hfo_act_cons": 2.5,
        "dg_hfo_act_cons": 0.3,
        "blr_hfo_act_cons": 0.5,
        "speed_water": 11.5,
    }
    df = pd.DataFrame([row] * 5)
    result = data_preparation(df)
    assert isinstance(result, pd.DataFrame)


def test_data_preparation_empty_on_all_filtered(tmp_path):
    import pandas as pd

    from data.pipeline import data_preparation

    # All rows will fail the me_shaft_power > 0 filter
    df = pd.DataFrame([{"me_shaft_power": 0, "speed_water": 1}])
    result = data_preparation(df)
    assert result.empty
