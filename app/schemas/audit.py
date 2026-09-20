from datetime import datetime

from pydantic import BaseModel, Field


class AuditFieldsMixin(BaseModel):
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    deleted_at: datetime | None = Field(default=None, serialization_alias="deletedAt")
