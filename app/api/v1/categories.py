from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints
from fastapi_pagination import Params
from app.api.deps import get_category_service
from app.mappers.category_mapper import CategoryMapper
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.pagination import PaginatedResponse, PaginationMeta
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, service: CategoryService = Depends(get_category_service)):
    return CategoryMapper.to_response(service.create(data))


@router.get("", response_model=PaginatedResponse[CategoryResponse])
def list_categories(
    params: Params = Depends(),
    sort: list[SortItem] | None = Query(None, min_length=1),
    service: CategoryService = Depends(get_category_service),
):
    page = service.list(params, sort)
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
    category = service.update(category_id, data)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryMapper.to_response(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, service: CategoryService = Depends(get_category_service)) -> None:
    if not service.delete(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")