"""Pydantic response schemas for the analytics service."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

# ── Attribute analysis ───────────────────────────────────────────────────────


class AttributeFrequency(BaseModel):
    attribute_value: float
    frequency: int
    percentage: float


class AttributeValue(BaseModel):
    date: date
    value: float | None


class AttributeRelation(BaseModel):
    value1: float | None
    value2: float | None


# ── Vessel statistics ────────────────────────────────────────────────────────


class VesselDataPerDayAverage(BaseModel):
    speed_water: float = 0.0
    me_fuel_consumption_nmile: float = 0.0


class VesselCiiData(BaseModel):
    cii: float | None
    cii_temp: float | None
    date: date
    rating: str
    superior: float
    lower: float
    upper: float
    inferior: float


class ConsumptionStatistic(BaseModel):
    total: float = 0.0
    me: float = 0.0
    dg: float = 0.0
    blr: float = 0.0
    real_start_date: str = ""
    real_end_date: str = ""


class VesselStandardDataInfo(BaseModel):
    speed_ground: float | None = None
    speed_water: float | None = None
    draft: float | None = None
    heel: float | None = None
    trim: float | None = None
    draught_astern: float | None = None
    draught_bow: float | None = None
    draught_mid_left: float | None = None
    draught_mid_right: float | None = None
    me_rpm: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None
    slip_ratio: float | None = None
    me_fuel_consumption_nmile: float | None = None
    me_fuel_consumption_kwh: float | None = None
    me_shaft_power: float | None = None
    me_torque: float | None = None
    latitude: str | None = None
    longitude: str | None = None
    date: date
    time: str | None = None
    ship_nmile: float | None = None


# ── Optimisation ─────────────────────────────────────────────────────────────


class OptimizationValues(BaseModel):
    gross_ton: float
    speed_water: float
    cii: float
    cii_rating: str


class TrimDataPoint(BaseModel):
    date: date
    trim: float


class TrimDataAverages(BaseModel):
    trim: float
    draft: float
    speed_water: float
    me_fuel_consumption_nmile: float
    cii: float
    cii_rating: str


class TrimDataResponse(BaseModel):
    trim_values: list[TrimDataPoint]
    averages: TrimDataAverages
