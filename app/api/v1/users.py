from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import StringConstraints

from app.api.auth_deps import require_permissions
from app.api.deps import get_user_service
from app.core.permissions import (
    CREATE_USER,
    DELETE_USER,
    LIST_USERS,
    READ_USER,
    UPDATE_USER,
)
from app.mappers.user_mapper import UserMapper
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(CREATE_USER))],
)
def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    return UserMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    dependencies=[Depends(require_permissions(LIST_USERS))],
)
def list_users(
    params: PaginationParams = Depends(),
    sort: list[SortItem] | None = Query(
        None,
        min_length=1,
        description="Orden de resultados. Usa campo,direccion y repite sort para varios campos.",
    ),
    search: str | None = Query(
        None,
        min_length=1,
        description="Texto que se buscara en username, nombre, apellido o email.",
    ),
    service: UserService = Depends(get_user_service),
):
    page = service.list(params, sort, search)
    return PaginatedResponse(
        data=UserMapper.to_responses(page.items),
        pagination=PaginationMeta(page=page.page, pageSize=page.size, pageCount=page.pages, total=page.total),
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(READ_USER))],
)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return UserMapper.to_response(service.get(user_id))


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(UPDATE_USER))],
)
def update_user(user_id: int, data: UserUpdate, service: UserService = Depends(get_user_service)):
    return UserMapper.to_response(service.update(user_id, data))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(DELETE_USER))],
)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)) -> None:
    service.delete(user_id)


@router.post(
    "/{user_id}/restore",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(DELETE_USER))],
)
def restore_user(user_id: int, service: UserService = Depends(get_user_service)):
    return UserMapper.to_response(service.restore(user_id))
