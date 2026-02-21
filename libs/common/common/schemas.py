"""Shared Pydantic schemas used across services."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

Data = TypeVar("Data")


class ResponseModel(BaseModel, Generic[Data]):
    """Unified API response wrapper."""

    code: int = Field(default=200)
    data: Data
    message: str = Field(default="success")
