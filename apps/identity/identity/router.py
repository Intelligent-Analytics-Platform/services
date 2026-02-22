"""API routes for the identity service."""

from common.schemas import ResponseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from identity.database import get_db
from identity.repository import CompanyRepository, UserRepository
from identity.schemas import (
    CompanyCreate,
    CompanySchema,
    CompanyUpdate,
    UserLoginData,
    UserRegisterData,
    UserSchema,
    UserUpdate,
    UserWithToken,
)
from identity.service import CompanyService, UserService

# --- Company Router ---

company_router = APIRouter(prefix="/company", tags=["公司"])


def get_company_service(session: Session = Depends(get_db)) -> CompanyService:
    return CompanyService(CompanyRepository(session))


@company_router.get("", summary="获取所有公司")
def get_companies(
    service: CompanyService = Depends(get_company_service),
) -> ResponseModel[list[CompanySchema]]:
    companies = service.get_all_companies()
    data = [CompanySchema.model_validate(c) for c in companies]
    return ResponseModel(data=data, message="获取公司列表成功")


@company_router.post("", summary="创建公司")
def create_company(
    body: CompanyCreate,
    service: CompanyService = Depends(get_company_service),
) -> ResponseModel[CompanySchema]:
    company = service.create_company(body)
    return ResponseModel(data=CompanySchema.model_validate(company), message="公司创建成功")


@company_router.get("/{company_id}", summary="获取单个公司详情")
def get_company(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
) -> ResponseModel[CompanySchema]:
    company = service.get_company_by_id(company_id)
    return ResponseModel(data=CompanySchema.model_validate(company), message="获取公司信息成功")


@company_router.put("/{company_id}", summary="更新公司信息")
def update_company(
    company_id: int,
    body: CompanyUpdate,
    service: CompanyService = Depends(get_company_service),
) -> ResponseModel[CompanySchema]:
    company = service.update_company(company_id, body)
    return ResponseModel(data=CompanySchema.model_validate(company), message="公司信息更新成功")


@company_router.delete("/{company_id}", summary="删除公司")
def delete_company(
    company_id: int,
    service: CompanyService = Depends(get_company_service),
) -> ResponseModel[CompanySchema]:
    company = service.delete_company(company_id)
    return ResponseModel(data=CompanySchema.model_validate(company), message="公司删除成功")


# --- User Router ---

user_router = APIRouter(prefix="/user", tags=["用户"])


def get_user_service(session: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


@user_router.get("", summary="获取用户列表")
def get_user_list(
    name: str | None = Query(None, description="用户名(模糊搜索)"),
    company_id: int | None = Query(None, description="公司ID"),
    offset: int = Query(0, description="偏移量"),
    limit: int = Query(10, description="每页数量"),
    service: UserService = Depends(get_user_service),
) -> ResponseModel[list[UserSchema]]:
    users = service.get_user_list(name, company_id, offset, limit)
    return ResponseModel(data=users, message="获取成功")


@user_router.post("/register", summary="注册用户")
def register_user(
    body: UserRegisterData,
    service: UserService = Depends(get_user_service),
) -> ResponseModel[UserSchema]:
    user = service.create_user(body)
    return ResponseModel(data=UserSchema.model_validate(user), message="注册成功")


@user_router.post("/login", summary="用户登录")
def login(
    body: UserLoginData,
    service: UserService = Depends(get_user_service),
) -> ResponseModel[UserWithToken]:
    result = service.login(body.username, body.password)
    return ResponseModel(data=result, message="登录成功")


@user_router.get("/{user_id}", summary="获取用户信息")
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> ResponseModel[UserSchema]:
    user = service.get_user_by_id(user_id)
    return ResponseModel(data=UserSchema.model_validate(user), message="获取成功")


@user_router.put("/{user_id}", summary="更新用户信息")
def update_user(
    user_id: int,
    body: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> ResponseModel[UserSchema]:
    user = service.update_user(user_id, body)
    return ResponseModel(data=UserSchema.model_validate(user), message="更新成功")


@user_router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> ResponseModel[UserSchema]:
    user = service.delete_user(user_id)
    return ResponseModel(data=UserSchema.model_validate(user), message="删除成功")
