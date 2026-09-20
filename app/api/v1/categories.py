from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import StringConstraints
from app.api.auth_deps import require_permissions
from app.api.deps import get_category_service
from app.core.permissions import (
    CREATE_CATEGORY,
    DELETE_CATEGORY,
    LIST_CATEGORIES,
    READ_CATEGORY,
    UPDATE_CATEGORY,
)
from app.mappers.category_mapper import CategoryMapper
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(CREATE_CATEGORY))],
)
def create_category(data: CategoryCreate, service: CategoryService = Depends(get_category_service)):
    return CategoryMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    dependencies=[Depends(require_permissions(LIST_CATEGORIES))],
)
def list_categories(
    params: PaginationParams = Depends(),
    sort: list[SortItem] | None = Query(
        None,
        min_length=1,
        description="Orden de resultados. Usa campo,direccion y repite sort para varios campos.",
        openapi_examples={
            "name_asc": {"summary": "Nombre A-Z", "value": ["name,asc"]},
            "name_desc": {"summary": "Nombre Z-A", "value": ["name,desc"]},
        },
    ),
    search: str | None = Query(
        None,
        min_length=1,
        description="Texto que se buscará en el nombre y la descripción de la categoría.",
        examples=["electronics"],
    ),
    service: CategoryService = Depends(get_category_service),
):
    page = service.list(params, sort, search)
    return PaginatedResponse(
        data=CategoryMapper.to_responses(page.items),
        pagination=PaginationMeta(
            page=page.page,
            pageSize=page.size,
            pageCount=page.pages,
            total=page.total,
        ),
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permissions(READ_CATEGORY))],
)
def get_category(category_id: int, service: CategoryService = Depends(get_category_service)):
    return CategoryMapper.to_response(service.get(category_id))


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permissions(UPDATE_CATEGORY))],
)
def update_category(category_id: int, data: CategoryUpdate, service: CategoryService = Depends(get_category_service)):
    return CategoryMapper.to_response(service.update(category_id, data))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(DELETE_CATEGORY))],
)
def delete_category(category_id: int, service: CategoryService = Depends(get_category_service)) -> None:
    service.delete(category_id)


@router.post(
    "/{category_id}/restore",
    response_model=CategoryResponse,
    dependencies=[Depends(require_permissions(DELETE_CATEGORY))],
)
def restore_category(category_id: int, service: CategoryService = Depends(get_category_service)):
    return CategoryMapper.to_response(service.restore(category_id))
