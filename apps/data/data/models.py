"""SQLAlchemy models for the data service.

Only VesselDataUpload lives in SQLite (via SQLAlchemy).
Analytics tables (original/standard/per-day data) live in DuckDB.
"""

from datetime import date, datetime

from common.models import Base, IntIDMixin, TimestampMixin
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class VesselDataUpload(IntIDMixin, TimestampMixin, Base):
    __tablename__ = "vessel_data_upload"

    vessel_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    date_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    # pending | processing | done | failed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
