from fastapi import APIRouter, Depends, status

from app.api.auth_deps import require_permissions
from app.api.deps import get_role_service
from app.core.permissions import (
    CREATE_ROLE,
    DELETE_ROLE,
    LIST_ROLES,
    READ_ROLE,
    UPDATE_ROLE,
)
from app.mappers.role_mapper import RoleMapper
from app.schemas.role import RoleCreate, RoleResponse, RoleSummaryResponse, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(CREATE_ROLE))],
)
def create_role(data: RoleCreate, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=list[RoleSummaryResponse],
    dependencies=[Depends(require_permissions(LIST_ROLES))],
)
def list_roles(service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_summaries(service.list())


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions(READ_ROLE))],
)
def get_role(role_id: int, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.get(role_id))


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions(UPDATE_ROLE))],
)
def update_role(role_id: int, data: RoleUpdate, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.update(role_id, data))


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(DELETE_ROLE))],
)
def delete_role(role_id: int, service: RoleService = Depends(get_role_service)) -> None:
    service.delete(role_id)


@router.post(
    "/{role_id}/restore",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions(DELETE_ROLE))],
)
def restore_role(role_id: int, service: RoleService = Depends(get_role_service)):
    return RoleMapper.to_response(service.restore(role_id))
