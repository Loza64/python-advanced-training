from fastapi import APIRouter, Depends

from app.api.auth_deps import require_permissions
from app.api.deps import get_permission_service
from app.core.permissions import LIST_PERMISSIONS, READ_PERMISSION, UPDATE_PERMISSION
from app.mappers.permission_mapper import PermissionMapper
from app.schemas.permission import PermissionResponse, PermissionUpdate
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permissions(LIST_PERMISSIONS))],
)
def list_permissions(service: PermissionService = Depends(get_permission_service)):
    return PermissionMapper.to_responses(service.list())


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permissions(READ_PERMISSION))],
)
def get_permission(permission_id: int, service: PermissionService = Depends(get_permission_service)):
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
