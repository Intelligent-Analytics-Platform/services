"""Data access layer for VesselDataUpload (SQLAlchemy / SQLite)."""

from common.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import Session

from data.models import VesselDataUpload


class UploadRepository(BaseRepository[VesselDataUpload]):
    def __init__(self, session: Session):
        super().__init__(session, VesselDataUpload)

    def list_by_vessel(
        self, vessel_id: int, *, offset: int = 0, limit: int = 10
    ) -> list[VesselDataUpload]:
        stmt = (
            select(VesselDataUpload)
            .where(VesselDataUpload.vessel_id == vessel_id)
            .order_by(VesselDataUpload.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())
