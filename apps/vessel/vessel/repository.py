"""Data access layer for the vessel service."""

from common.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import Session

from vessel.models import Vessel


class VesselRepository(BaseRepository[Vessel]):
    def __init__(self, session: Session):
        super().__init__(session, Vessel)

    def list_vessels(
        self,
        name: str | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[Vessel]:
        stmt = select(Vessel)
        if name:
            stmt = stmt.where(Vessel.name.like(f"%{name}%"))
        if company_id is not None:
            stmt = stmt.where(Vessel.company_id == company_id)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())
