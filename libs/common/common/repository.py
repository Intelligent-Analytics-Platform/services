"""Generic base repository with common CRUD operations."""

import logging
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.exceptions import EntityNotFoundError

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Base repository providing standard CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: Session):
                super().__init__(session, User)
    """

    def __init__(self, session: Session, model: type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, id: int) -> T | None:
        return self.session.get(self.model, id)

    def get_or_raise(self, id: int) -> T:
        entity = self.get_by_id(id)
        if not entity:
            raise EntityNotFoundError(self.model.__name__, id)
        return entity

    def list_all(self, *, offset: int = 0, limit: int = 100) -> list[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: T, update_data: dict) -> T:
        for key, value in update_data.items():
            setattr(entity, key, value)
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()
