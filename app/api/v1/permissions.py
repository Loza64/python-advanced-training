from fastapi import APIRouter, Depends, Query

from app.api.auth_deps import require_permissions
from app.api.deps import get_permission_service
from app.api.v1.categories import SortItem
from app.core.permissions import LIST_PERMISSIONS, READ_PERMISSION, UPDATE_PERMISSION
from app.mappers.permission_mapper import PermissionMapper
from app.schemas.permission import PermissionResponse, PermissionUpdate
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "",
    response_model=PaginatedResponse[PermissionResponse],
    dependencies=[Depends(require_permissions(LIST_PERMISSIONS))],
)
def list_permissions(
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
    service: PermissionService = Depends(get_permission_service),
):
    page = service.list(params, sort, search)
    return PaginatedResponse(
        data=PermissionMapper.to_responses(page.items),
        pagination=PaginationMeta(
            page=page.page,
            pageSize=page.size,
            pageCount=page.pages,
            total=page.total,
        ),
    )


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permissions(READ_PERMISSION))],
)
def get_permission(
    permission_id: int, service: PermissionService = Depends(get_permission_service)
):
    return PermissionMapper.to_response(service.get(permission_id))


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permissions(UPDATE_PERMISSION))],
)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
):
    return PermissionMapper.to_response(service.update(permission_id, data))
