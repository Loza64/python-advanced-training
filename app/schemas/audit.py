from datetime import datetime

from pydantic import BaseModel, Field


class AuditFieldsMixin(BaseModel):
    """Campos de auditoría compartidos por los recursos administrables
    (categorías, productos, roles, usuarios, permisos). Se exponen en
    camelCase en la respuesta (createdAt/updatedAt/deletedAt) aunque el
    modelo ORM los tenga en snake_case, gracias a serialization_alias +
    el response_model_by_alias=True por defecto de FastAPI.

    No se usa en el endpoint de "mi perfil" (GET /auth/me): ese devuelve
    ProfileResponse, sin estos campos.
    """

    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    deleted_at: datetime | None = Field(default=None, serialization_alias="deletedAt")
