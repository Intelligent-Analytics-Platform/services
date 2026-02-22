"""Data access layer for the identity service."""

from common.repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import Session

from identity.models import Company, User


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: Session):
        super().__init__(session, Company)

    def list_all_companies(self) -> list[Company]:
        return list(self.session.scalars(select(Company)).all())


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    def find_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.session.scalars(stmt).first()

    def list_users(
        self,
        name: str | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[User]:
        stmt = select(User).where(User.disabled == False)  # noqa: E712
        if name:
            stmt = stmt.where(User.username.like(f"%{name}%"))
        if company_id is not None:
            stmt = stmt.where(User.company_id == company_id)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())
