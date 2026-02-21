"""Data access layer for the meta service."""

from common.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import Session

from meta.models import FuelType, ShipType, TimeZone


class MetaRepository(BaseRepository[FuelType]):
    def __init__(self, session: Session):
        super().__init__(session, FuelType)

    def get_all_fuel_types(self) -> list[FuelType]:
        return list(self.session.scalars(select(FuelType)).all())

    def get_all_ship_types(self) -> list[ShipType]:
        return list(self.session.scalars(select(ShipType)).all())

    def get_all_time_zones(self) -> list[TimeZone]:
        return list(self.session.scalars(select(TimeZone)).all())
