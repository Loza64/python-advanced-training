from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditFieldsMixin


class PermissionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)


class PermissionResponse(AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    title: str | None = None
