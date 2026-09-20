from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.audit import AuditFieldsMixin
from app.schemas.role import RoleReference, RoleResponse, RoleSummaryResponse


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: RoleReference | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    surname: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: RoleReference | None = None
    blocked: bool | None = None


class UserResponse(UserBase, AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blocked: bool
    role: RoleSummaryResponse | None = None


class ProfileResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blocked: bool
    role: RoleResponse | None = None
