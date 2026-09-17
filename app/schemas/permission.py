from pydantic import BaseModel, ConfigDict, Field


class PermissionUpdate(BaseModel):
    """Solo se permite modificar 'title'. 'name' identifica al permiso y no es editable."""

    title: str | None = Field(default=None, max_length=500)


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    title: str | None = None
