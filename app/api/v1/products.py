from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints
from fastapi_pagination import Params
from app.api.deps import get_product_service
from app.mappers.product_mapper import ProductMapper
from app.schemas.pagination import PaginatedResponse, PaginationMeta
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, service: ProductService = Depends(get_product_service)):
    return ProductMapper.to_response(service.create(data))


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    params: Params = Depends(),
    sort: list[SortItem] | None = Query(None, min_length=1),
    service: ProductService = Depends(get_product_service),
):
    page = service.list(params, sort)
    return PaginatedResponse(
        data=ProductMapper.to_responses(page.items),
        pagination=PaginationMeta(
            page=page.page,
            pageSize=page.size,
            pageCount=page.pages,
            total=page.total,
        ),
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    product = service.get(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductMapper.to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, service: ProductService = Depends(get_product_service)):
    product = service.update(product_id, data)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductMapper.to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, service: ProductService = Depends(get_product_service)) -> None:
    if not service.delete(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")