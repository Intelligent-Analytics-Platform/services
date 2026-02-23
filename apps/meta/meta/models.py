"""SQLAlchemy models for the meta service."""

from common.models import Base
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class FuelType(Base):
    __tablename__ = "fuel_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_cn: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(100))
    name_abbr: Mapped[str] = mapped_column(String(20))
    cf: Mapped[float] = mapped_column(Float)


class ShipType(Base):
    __tablename__ = "ship_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_cn: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(20))
    cii_related_tone: Mapped[str] = mapped_column(String(20))


class TimeZone(Base):
    __tablename__ = "time_zone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_cn: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(100))
    explaination: Mapped[str] = mapped_column(String(100))
