"""Pydantic request/response schemas for the data service."""

from datetime import date, datetime

from pydantic import BaseModel

# ── Upload ───────────────────────────────────────────────────────────────────


class UploadAccepted(BaseModel):
    upload_id: int
    message: str = "上传成功，后台处理中"


class UploadStatusSchema(BaseModel):
    id: int
    vessel_id: int
    file_path: str
    date_start: date | None
    date_end: date | None
    status: str
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# ── Daily data ───────────────────────────────────────────────────────────────


class DailyDataSchema(BaseModel):
    vessel_id: int
    date: date
    speed_ground: float | None
    speed_water: float | None
    me_shaft_power: float | None
    me_rpm: float | None
    me_fuel_consumption_nmile: float | None
    me_hfo_act_cons: float | None
    me_mgo_act_cons: float | None
    blr_hfo_act_cons: float | None
    blr_mgo_act_cons: float | None
    dg_hfo_act_cons: float | None
    dg_mgo_act_cons: float | None
    slip_ratio: float | None
    draft: float | None
    wind_speed: float | None
    cii_temp: float
    cii: float
