"""Pydantic request/response schemas for the identity service."""

from pydantic import BaseModel

# --- Company ---


class CompanySchema(BaseModel):
    id: int
    name: str
    address: str
    contact_person: str
    contact_phone: str
    contact_email: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "远洋航运有限公司",
                    "address": "上海市浦东新区张江高科技园区",
                    "contact_person": "张三",
                    "contact_phone": "13800000001",
                    "contact_email": "contact@shipping.com",
                }
            ]
        },
    }


class CompanyCreate(BaseModel):
    name: str
    address: str
    contact_person: str
    contact_phone: str
    contact_email: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "远洋航运有限公司",
                    "address": "上海市浦东新区张江高科技园区",
                    "contact_person": "张三",
                    "contact_phone": "13800000001",
                    "contact_email": "contact@shipping.com",
                }
            ]
        }
    }


class CompanyUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None

    model_config = {"json_schema_extra": {"examples": [{"address": "北京市朝阳区建国路88号"}]}}


# --- User ---


class UserSchema(BaseModel):
    id: int
    username: str
    phone: str
    company_id: int
    is_admin: bool
    is_system_admin: bool
    disabled: bool

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "username": "captain_zhang",
                    "phone": "13900000001",
                    "company_id": 1,
                    "is_admin": False,
                    "is_system_admin": False,
                    "disabled": False,
                }
            ]
        },
    }


class UserLoginData(BaseModel):
    username: str
    password: str

    model_config = {
        "json_schema_extra": {"examples": [{"username": "captain_zhang", "password": "mypassword"}]}
    }


class UserRegisterData(BaseModel):
    username: str
    password: str
    phone: str
    company_id: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "captain_zhang",
                    "password": "mypassword",
                    "phone": "13900000001",
                    "company_id": 1,
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    phone: str | None = None

    model_config = {"json_schema_extra": {"examples": [{"phone": "13988888888"}]}}


class UserWithToken(UserSchema):
    token: str
