"""Pydantic request/response schemas for the meta service."""

from pydantic import BaseModel


class FuelTypeSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    name_abbr: str
    cf: float

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 11,
                    "name_cn": "液化天然气 (LNG)",
                    "name_en": "Liquefied Natural Gas (LNG)",
                    "name_abbr": "LNG",
                    "cf": 2.75,
                }
            ]
        },
    }


class ShipTypeSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    code: str
    cii_related_tone: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 4,
                    "name_cn": "集装箱船",
                    "name_en": "Container ship",
                    "code": "I004",
                    "cii_related_tone": "dwt",
                }
            ]
        },
    }


class TimeZoneSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    explaination: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 9,
                    "name_cn": "东八区",
                    "name_en": "UTC+8",
                    "explaination": "东八区 112.5° E～127.5° E 120° E",
                }
            ]
        },
    }


class AttributeMapping(BaseModel):
    attribute: str
    description: str

    model_config = {
        "json_schema_extra": {"examples": [{"attribute": "speed_water", "description": "对水航速"}]}
    }


class AttributeMappings(BaseModel):
    attribute_left: AttributeMapping
    attribute_right: AttributeMapping

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "attribute_left": {"attribute": "speed_water", "description": "对水航速"},
                    "attribute_right": {"attribute": "me_shaft_power", "description": "主机功率"},
                }
            ]
        }
    }


class LabelValue(BaseModel):
    label: str
    value: str

    model_config = {"json_schema_extra": {"examples": [{"label": "液化天然气", "value": "lng"}]}}


