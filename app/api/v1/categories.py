from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints
from app.api.deps import get_category_service
from app.mappers.category_mapper import CategoryMapper
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.services.category_service import CategoryService, DuplicateCategoryNameError

router = APIRouter(prefix="/categories", tags=["Categories"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, service: CategoryService = Depends(get_category_service)):
    try:
        return CategoryMapper.to_response(service.create(data))
    except DuplicateCategoryNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[CategoryResponse])
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


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, service: CategoryService = Depends(get_category_service)):
    category = service.get(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryMapper.to_response(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, service: CategoryService = Depends(get_category_service)):
    try:
        category = service.update(category_id, data)
    except DuplicateCategoryNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryMapper.to_response(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, service: CategoryService = Depends(get_category_service)) -> None:
    if not service.delete(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")