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

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    name: str
    address: str
    contact_person: str
    contact_phone: str
    contact_email: str


class CompanyUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


# --- User ---


class UserSchema(BaseModel):
    id: int
    username: str
    phone: str
    company_id: int
    is_admin: bool
    is_system_admin: bool
    disabled: bool

    model_config = {"from_attributes": True}


class UserLoginData(BaseModel):
    username: str
    password: str


class UserRegisterData(BaseModel):
    username: str
    password: str
    phone: str
    company_id: int


class UserUpdate(BaseModel):
    phone: str | None = None


class UserWithToken(UserSchema):
    token: str
