from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditFieldsMixin
from app.schemas.permission import PermissionResponse


class RoleReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0)


class RoleBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    active: bool = True


class RoleCreate(RoleBase):
    permissions: list[RoleReference] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    active: bool | None = None
    permissions: list[RoleReference] | None = None


class RoleSummaryResponse(RoleBase, AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RoleResponse(RoleSummaryResponse):
    permissions: list[PermissionResponse] = Field(default_factory=list)
