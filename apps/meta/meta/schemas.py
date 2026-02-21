"""Pydantic request/response schemas for the meta service."""

from enum import StrEnum

from pydantic import BaseModel


class FuelTypeSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    name_abbr: str
    cf: float

    model_config = {"from_attributes": True}


class ShipTypeSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    code: str
    cii_related_tone: str

    model_config = {"from_attributes": True}


class TimeZoneSchema(BaseModel):
    id: int
    name_cn: str
    name_en: str
    explaination: str

    model_config = {"from_attributes": True}


class AttributeMapping(BaseModel):
    attribute: str
    description: str


class AttributeMappings(BaseModel):
    attribute_left: AttributeMapping
    attribute_right: AttributeMapping


class LabelValue(BaseModel):
    label: str
    value: str


class ConsumptionType(StrEnum):
    total = "total"
    nmile = "nmile"
