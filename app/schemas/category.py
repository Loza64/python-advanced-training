from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditFieldsMixin


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase, AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)
    id: int
    