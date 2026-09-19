from fastapi import APIRouter, Depends, status

from app.api.deps import get_role_service, require_permissions
from app.mappers.role_mapper import RoleMapper
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("roles:create"))],
)
def create_role(data: RoleCreate, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=list[RoleResponse],
    dependencies=[Depends(require_permissions("roles:list"))],
)
def list_roles(service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_responses(service.list())


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions("roles:read"))],
)
def get_role(role_id: int, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.get(role_id))


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions("roles:update"))],
)
def update_role(role_id: int, data: RoleUpdate, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.update(role_id, data))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("roles:delete"))],
)
def delete_role(role_id: int, service: RoleService = Depends(get_role_service)) -> None:
    service.delete(role_id)


@router.post(
    "/{role_id}/restore",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions("roles:delete"))],
)
def restore_role(role_id: int, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.restore(role_id))
