"""SQLAlchemy declarative base and common mixins."""

from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class IntIDMixin:
    """Mixin that adds an auto-increment integer primary key."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(default=None, onupdate=func.now())
