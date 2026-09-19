from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import StringConstraints
from app.api.deps import get_product_service, require_permissions
from app.mappers.product_mapper import ProductMapper
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("products:create"))],
)
def create_product(data: ProductCreate, service: ProductService = Depends(get_product_service)):
    return ProductMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    dependencies=[Depends(require_permissions("products:list"))],
)
def list_products(
    params: PaginationParams = Depends(),
    sort: list[SortItem] | None = Query(
        None,
        min_length=1,
        description="Orden de resultados. Usa campo,direccion y repite sort para varios campos.",
        openapi_examples={
            "name_asc": {"summary": "Nombre A-Z", "value": ["name,asc"]},
            "price_desc": {"summary": "Precio mayor a menor", "value": ["price,desc"]},
        },
    ),
    search: str | None = Query(
        None,
        min_length=1,
        description="Texto que se buscará en el nombre y la descripción del producto.",
        examples=["laptop"],
    ),
    service: ProductService = Depends(get_product_service),
):
    page = service.list(params, sort, search)
    return PaginatedResponse(
        data=ProductMapper.to_responses(page.items),
        pagination=PaginationMeta(
            page=page.page,
            pageSize=page.size,
            pageCount=page.pages,
            total=page.total,
        ),
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permissions("products:read"))],
)
def get_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return ProductMapper.to_response(service.get(product_id))


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permissions("products:update"))],
)
def update_product(product_id: int, data: ProductUpdate, service: ProductService = Depends(get_product_service)):
    return ProductMapper.to_response(service.update(product_id, data))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("products:delete"))],
)
def delete_product(product_id: int, service: ProductService = Depends(get_product_service)) -> None:
    service.delete(product_id)


@router.post(
    "/{product_id}/restore",
    response_model=ProductResponse,
    dependencies=[Depends(require_permissions("products:delete"))],
)
def restore_product(product_id: int, service: ProductService = Depends(get_product_service)):
    return ProductMapper.to_response(service.restore(product_id))
