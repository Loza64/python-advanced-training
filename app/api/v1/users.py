from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints

from app.api.deps import get_user_service, require_permissions
from app.core.exceptions import EmailAlreadyExistsError, RoleNotFoundError, UsernameAlreadyExistsError
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
    dependencies=[Depends(require_permissions("users:create"))],
)
def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    try:
        return UserMapper.to_response(service.create(data))
    except (UsernameAlreadyExistsError, EmailAlreadyExistsError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    dependencies=[Depends(require_permissions("users:list"))],
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
    dependencies=[Depends(require_permissions("users:read"))],
)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    user = service.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserMapper.to_response(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions("users:update"))],
)
def update_user(user_id: int, data: UserUpdate, service: UserService = Depends(get_user_service)):
    try:
        user = service.update(user_id, data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserMapper.to_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("users:delete"))],
)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)) -> None:
    if not service.delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
