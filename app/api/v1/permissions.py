from fastapi import APIRouter, Depends

from app.api.deps import get_permission_service, require_permissions
from app.mappers.permission_mapper import PermissionMapper
from app.schemas.permission import PermissionResponse, PermissionUpdate
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])

# Nota: los permisos no se crean ni se eliminan vía API (no hay POST/DELETE),
# y tampoco soportan restore. Solo se listan, se consultan por id, y se
# actualiza su 'title'. 'name' identifica al permiso y nunca es editable.


@router.get(
    "",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permissions("permissions:list"))],
)
def list_permissions(service: PermissionService = Depends(get_permission_service)):
    return PermissionMapper.to_responses(service.list())


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permissions("permissions:read"))],
)
def get_permission(permission_id: int, service: PermissionService = Depends(get_permission_service)):
    return PermissionMapper.to_response(service.get(permission_id))


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permissions("permissions:update"))],
)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
):
    return PermissionMapper.to_response(service.update(permission_id, data))
