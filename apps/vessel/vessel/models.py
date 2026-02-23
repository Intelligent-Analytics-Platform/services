"""SQLAlchemy models for the vessel service."""

from datetime import date

from common.models import Base, IntIDMixin, TimestampMixin
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Vessel(IntIDMixin, TimestampMixin, Base):
    __tablename__ = "vessel"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    mmsi: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    build_date: Mapped[date] = mapped_column(Date, nullable=False)
    gross_tone: Mapped[float] = mapped_column(Float, nullable=False)
    dead_weight: Mapped[float] = mapped_column(Float, nullable=False)
    new_vessel: Mapped[bool] = mapped_column(default=False)
    pitch: Mapped[float] = mapped_column(Float, default=6.058)

    hull_clean_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    engine_overhaul_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    newly_paint_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    propeller_polish_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Cross-service references – stored as plain integers, no FK constraint
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ship_type: Mapped[int] = mapped_column(Integer, nullable=False)
    time_zone: Mapped[int] = mapped_column(Integer, default=1)

    equipments: Mapped[list["Equipment"]] = relationship(
        back_populates="vessel", cascade="all, delete-orphan"
    )
    curves: Mapped[list["PowerSpeedCurve"]] = relationship(
        back_populates="vessel", cascade="all, delete-orphan"
    )


class Equipment(IntIDMixin, Base):
    __tablename__ = "equipment"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # me / dg / blr
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessel.id"), nullable=False)

    vessel: Mapped["Vessel"] = relationship(back_populates="equipments")
    fuel_entries: Mapped[list["EquipmentFuel"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )


class EquipmentFuel(Base):
    __tablename__ = "equipment_fuel"

    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), primary_key=True)
    # fuel_type_id references the meta service – no FK constraint
    fuel_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    equipment: Mapped["Equipment"] = relationship(back_populates="fuel_entries")


class PowerSpeedCurve(IntIDMixin, Base):
    __tablename__ = "power_speed_curve"

    curve_name: Mapped[str] = mapped_column(String(100), nullable=False)
    draft_astern: Mapped[float] = mapped_column(Float, nullable=False)
    draft_bow: Mapped[float] = mapped_column(Float, nullable=False)
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessel.id"), nullable=False)

    vessel: Mapped["Vessel"] = relationship(back_populates="curves")
    curve_data: Mapped[list["CurveData"]] = relationship(
        back_populates="curve",
        cascade="all, delete-orphan",
        order_by="CurveData.speed_water",
    )


class CurveData(IntIDMixin, Base):
    __tablename__ = "curve_data"

    speed_water: Mapped[float] = mapped_column(Float, nullable=False)
    me_power: Mapped[float] = mapped_column(Float, nullable=False)
    power_speed_curve_id: Mapped[int] = mapped_column(
        ForeignKey("power_speed_curve.id"), nullable=False
    )

    curve: Mapped["PowerSpeedCurve"] = relationship(back_populates="curve_data")
