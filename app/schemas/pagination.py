from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ItemT = TypeVar("ItemT")


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int
    page_size: int = Field(serialization_alias="pageSize", validation_alias="pageSize")
    page_count: int = Field(serialization_alias="pageCount", validation_alias="pageCount")
    total: int


class PaginatedResponse(BaseModel, Generic[ItemT]):
    data: list[ItemT]
    pagination: PaginationMeta