"""Pydantic request/response schemas for the vessel service."""

from datetime import date, datetime

from pydantic import BaseModel

# ── Equipment ──────────────────────────────────────────────────────────────────


class EquipmentCreate(BaseModel):
    name: str
    type: str  # me / dg / blr
    fuel_type_ids: list[int] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "主机", "type": "me", "fuel_type_ids": [1]},
            ]
        }
    }


class EquipmentSchema(BaseModel):
    name: str
    type: str
    fuel_type_ids: list[int]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {"name": "主机", "type": "me", "fuel_type_ids": [1]},
            ]
        },
    }


# ── Power-speed curve ──────────────────────────────────────────────────────────


class CurveDataCreate(BaseModel):
    speed_water: float
    me_power: float

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"speed_water": 12.0, "me_power": 4500.0},
            ]
        }
    }


class CurveDataSchema(BaseModel):
    id: int
    speed_water: float
    me_power: float

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {"id": 1, "speed_water": 12.0, "me_power": 4500.0},
            ]
        },
    }


class PowerSpeedCurveCreate(BaseModel):
    curve_name: str
    draft_astern: float
    draft_bow: float
    curve_data: list[CurveDataCreate] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "curve_name": "满载",
                    "draft_astern": 10.5,
                    "draft_bow": 9.8,
                    "curve_data": [
                        {"speed_water": 10.0, "me_power": 2800.0},
                        {"speed_water": 12.0, "me_power": 4500.0},
                        {"speed_water": 14.0, "me_power": 7200.0},
                        {"speed_water": 15.5, "me_power": 9800.0},
                    ],
                }
            ]
        }
    }


class PowerSpeedCurveSchema(BaseModel):
    id: int
    curve_name: str
    draft_astern: float
    draft_bow: float
    curve_data: list[CurveDataSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "curve_name": "满载",
                    "draft_astern": 10.5,
                    "draft_bow": 9.8,
                    "curve_data": [
                        {"id": 1, "speed_water": 10.0, "me_power": 2800.0},
                        {"id": 2, "speed_water": 12.0, "me_power": 4500.0},
                        {"id": 3, "speed_water": 14.0, "me_power": 7200.0},
                        {"id": 4, "speed_water": 15.5, "me_power": 9800.0},
                    ],
                }
            ]
        },
    }


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "八打雁",
                    "mmsi": "477401900",
                    "ship_type": 4,
                    "build_date": "2019-11-01",
                    "gross_tone": 26771.0,
                    "dead_weight": 35337.0,
                    "new_vessel": False,
                    "pitch": 6.058,
                    "hull_clean_date": "2023-06-15",
                    "engine_overhaul_date": "2022-03-01",
                    "newly_paint_date": "2023-06-15",
                    "propeller_polish_date": "2023-06-15",
                    "time_zone": 1,
                    "company_id": 1,
                    "equipments": [
                        {"name": "主机", "type": "me", "fuel_type_ids": [1]},
                        {"name": "副机", "type": "dg", "fuel_type_ids": [1, 7]},
                        {"name": "锅炉", "type": "blr", "fuel_type_ids": [1, 7]},
                    ],
                    "curves": [
                        {
                            "curve_name": "满载",
                            "draft_astern": 10.5,
                            "draft_bow": 9.8,
                            "curve_data": [
                                {"speed_water": 10.0, "me_power": 2800.0},
                                {"speed_water": 12.0, "me_power": 4500.0},
                                {"speed_water": 14.0, "me_power": 7200.0},
                                {"speed_water": 15.5, "me_power": 9800.0},
                            ],
                        },
                        {
                            "curve_name": "压载",
                            "draft_astern": 6.2,
                            "draft_bow": 5.5,
                            "curve_data": [
                                {"speed_water": 11.0, "me_power": 2600.0},
                                {"speed_water": 13.0, "me_power": 4200.0},
                                {"speed_water": 15.0, "me_power": 6800.0},
                            ],
                        },
                    ],
                }
            ]
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "八打雁",
                    "mmsi": "477401900",
                    "ship_type": 4,
                    "build_date": "2019-11-01",
                    "gross_tone": 26771.0,
                    "dead_weight": 35337.0,
                    "new_vessel": False,
                    "pitch": 6.058,
                    "hull_clean_date": "2024-01-10",
                    "engine_overhaul_date": "2023-09-01",
                    "newly_paint_date": "2024-01-10",
                    "propeller_polish_date": "2024-01-10",
                    "time_zone": 1,
                    "company_id": 1,
                    "equipments": [
                        {"name": "主机", "type": "me", "fuel_type_ids": [1]},
                        {"name": "副机", "type": "dg", "fuel_type_ids": [1, 7]},
                        {"name": "锅炉", "type": "blr", "fuel_type_ids": [1, 7]},
                    ],
                    "curves": [
                        {
                            "curve_name": "满载",
                            "draft_astern": 10.5,
                            "draft_bow": 9.8,
                            "curve_data": [
                                {"speed_water": 10.0, "me_power": 2800.0},
                                {"speed_water": 12.0, "me_power": 4500.0},
                                {"speed_water": 14.0, "me_power": 7200.0},
                                {"speed_water": 15.5, "me_power": 9800.0},
                            ],
                        }
                    ],
                }
            ]
        }
    }


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

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "八打雁",
                    "mmsi": "477401900",
                    "ship_type": 4,
                    "build_date": "2019-11-01",
                    "gross_tone": 26771.0,
                    "dead_weight": 35337.0,
                    "new_vessel": False,
                    "pitch": 6.058,
                    "hull_clean_date": "2023-06-15",
                    "engine_overhaul_date": "2022-03-01",
                    "newly_paint_date": "2023-06-15",
                    "propeller_polish_date": "2023-06-15",
                    "time_zone": 1,
                    "company_id": 1,
                    "created_at": "2024-01-15T08:30:00",
                    "equipments": [
                        {"name": "主机", "type": "me", "fuel_type_ids": [1]},
                        {"name": "副机", "type": "dg", "fuel_type_ids": [1, 7]},
                        {"name": "锅炉", "type": "blr", "fuel_type_ids": [1, 7]},
                    ],
                    "curves": [
                        {
                            "id": 1,
                            "curve_name": "满载",
                            "draft_astern": 10.5,
                            "draft_bow": 9.8,
                            "curve_data": [
                                {"id": 1, "speed_water": 10.0, "me_power": 2800.0},
                                {"id": 2, "speed_water": 12.0, "me_power": 4500.0},
                                {"id": 3, "speed_water": 14.0, "me_power": 7200.0},
                                {"id": 4, "speed_water": 15.5, "me_power": 9800.0},
                            ],
                        }
                    ],
                }
            ]
        },
    }
