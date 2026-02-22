"""Business logic for the identity service."""

from datetime import timedelta

from common.auth import create_access_token, get_password_hash, verify_password
from common.exceptions import AuthenticationError, EntityNotFoundError

from identity.config import settings
from identity.models import Company, User
from identity.repository import CompanyRepository, UserRepository
from identity.schemas import (
    CompanyCreate,
    CompanyUpdate,
    UserRegisterData,
    UserSchema,
    UserUpdate,
    UserWithToken,
)


class CompanyService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    def get_all_companies(self) -> list[Company]:
        return self.repo.list_all_companies()

    def get_company_by_id(self, company_id: int) -> Company:
        company = self.repo.get_by_id(company_id)
        if not company:
            raise EntityNotFoundError("Company", company_id)
        return company

    def create_company(self, data: CompanyCreate) -> Company:
        company = Company(**data.model_dump())
        self.repo.create(company)

        return company

    def update_company(self, company_id: int, data: CompanyUpdate) -> Company:
        company = self.get_company_by_id(company_id)
        self.repo.update(company, data.model_dump(exclude_unset=True))

        return company

    def delete_company(self, company_id: int) -> Company:
        company = self.get_company_by_id(company_id)
        self.repo.delete(company)

        return company


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_user_by_id(self, user_id: int) -> User:
        user = self.repo.get_or_raise(user_id)
        if user.disabled:
            raise EntityNotFoundError("User", user_id)
        return user

    def get_user_list(
        self,
        name: str | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[dict]:
        users = self.repo.list_users(name, company_id, offset, limit)
        return [UserSchema.model_validate(u).model_dump() for u in users]

    def create_user(self, data: UserRegisterData) -> User:
        user = User(
            username=data.username,
            hashed_password=get_password_hash(data.password),
            phone=data.phone,
            company_id=data.company_id,
            is_admin=False,
            is_system_admin=False,
            disabled=False,
        )
        self.repo.create(user)

        return user

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        self.repo.update(user, data.model_dump(exclude_unset=True))

        return user

    def delete_user(self, user_id: int) -> User:
        """Soft-delete by marking as disabled."""
        user = self.get_user_by_id(user_id)
        user.disabled = True

        return user

    def authenticate_user(self, username: str, password: str) -> User:
        user = self.repo.find_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("用户名或密码错误")
        return user

    def login(self, username: str, password: str) -> UserWithToken:
        user = self.authenticate_user(username, password)
        token = create_access_token(
            data={"sub": str(user.id)},
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
        )
        return UserWithToken(**UserSchema.model_validate(user).model_dump(), token=token)
