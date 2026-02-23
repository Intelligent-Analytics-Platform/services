"""Pydantic request/response schemas for the vessel service."""

from datetime import date, datetime

from pydantic import BaseModel

# ── Equipment ──────────────────────────────────────────────────────────────────


class EquipmentCreate(BaseModel):
    name: str
    type: str  # me / dg / blr
    fuel_type_ids: list[int] = []


class EquipmentSchema(BaseModel):
    name: str
    type: str
    fuel_type_ids: list[int]

    model_config = {"from_attributes": True}


# ── Power-speed curve ──────────────────────────────────────────────────────────


class CurveDataCreate(BaseModel):
    speed_water: float
    me_power: float


class CurveDataSchema(BaseModel):
    id: int
    speed_water: float
    me_power: float

    model_config = {"from_attributes": True}


class PowerSpeedCurveCreate(BaseModel):
    curve_name: str
    draft_astern: float
    draft_bow: float
    curve_data: list[CurveDataCreate] = []


class PowerSpeedCurveSchema(BaseModel):
    id: int
    curve_name: str
    draft_astern: float
    draft_bow: float
    curve_data: list[CurveDataSchema]

    model_config = {"from_attributes": True}


# ── Vessel ─────────────────────────────────────────────────────────────────────


class VesselCreate(BaseModel):
    name: str
    mmsi: str
    ship_type: int
    build_date: date
    gross_tone: float
    dead_weight: float
    new_vessel: bool = False
    pitch: float = 6.058
    hull_clean_date: date | None = None
    engine_overhaul_date: date | None = None
    newly_paint_date: date | None = None
    propeller_polish_date: date | None = None
    time_zone: int = 1
    company_id: int
    equipments: list[EquipmentCreate] = []
    curves: list[PowerSpeedCurveCreate] = []


class VesselUpdate(BaseModel):
    name: str | None = None
    mmsi: str | None = None
    ship_type: int | None = None
    build_date: date | None = None
    gross_tone: float | None = None
    dead_weight: float | None = None
    new_vessel: bool | None = None
    pitch: float | None = None
    hull_clean_date: date | None = None
    engine_overhaul_date: date | None = None
    newly_paint_date: date | None = None
    propeller_polish_date: date | None = None
    time_zone: int | None = None
    company_id: int | None = None
    # Equipment and curves are replaced entirely when provided
    equipments: list[EquipmentCreate] = []
    curves: list[PowerSpeedCurveCreate] = []


class VesselSchema(BaseModel):
    id: int
    name: str
    mmsi: str
    ship_type: int
    build_date: date
    gross_tone: float
    dead_weight: float
    new_vessel: bool
    pitch: float
    hull_clean_date: date | None
    engine_overhaul_date: date | None
    newly_paint_date: date | None
    propeller_polish_date: date | None
    time_zone: int
    company_id: int
    created_at: datetime
    equipments: list[EquipmentSchema]
    curves: list[PowerSpeedCurveSchema]

    model_config = {"from_attributes": True}
