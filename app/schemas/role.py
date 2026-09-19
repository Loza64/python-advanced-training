from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditFieldsMixin
from app.schemas.permission import PermissionResponse


class RoleBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    active: bool = True


class RoleCreate(RoleBase):
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    active: bool | None = None
    permission_ids: list[int] | None = None


class RoleResponse(RoleBase, AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int
    permissions: list[PermissionResponse] = Field(default_factory=list)
