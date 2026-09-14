from typing import Generic, TypeVar

from fastapi import Query
from fastapi_pagination import Params
from pydantic import BaseModel, ConfigDict, Field

ItemT = TypeVar("ItemT")


class PaginationParams(Params):
    page: int = Query(
        1,
        ge=1,
        description="Número de página que quieres consultar. Empieza en 1.",
        examples=[1, 2],
    )
    size: int = Query(
        50,
        ge=1,
        le=100,
        description="Cantidad de elementos por página. Valores permitidos: de 1 a 100.",
        examples=[10, 50],
    )


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page: int
    page_size: int = Field(serialization_alias="pageSize", validation_alias="pageSize")
    page_count: int = Field(serialization_alias="pageCount", validation_alias="pageCount")
    total: int


class PaginatedResponse(BaseModel, Generic[ItemT]):
    data: list[ItemT]
    pagination: PaginationMeta