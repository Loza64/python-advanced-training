from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.permission_service import PermissionService
from app.services.product_service import ProductService
from app.services.role_service import RoleService
from app.services.user_service import UserService

# tokenUrl solo se usa para poblar el boton "Authorize" en /docs.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)


# --- Repositorios ---

def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)


def get_permission_repository(db: Session = Depends(get_db)) -> PermissionRepository:
    return PermissionRepository(db)


def get_refresh_token_repository(db: Session = Depends(get_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


# --- Servicios ---

def get_category_service(repository: CategoryRepository = Depends(get_category_repository)) -> CategoryService:
    return CategoryService(repository)


def get_product_service(
    repository: ProductRepository = Depends(get_product_repository),
    category_repository: CategoryRepository = Depends(get_category_repository),
) -> ProductService:
    return ProductService(repository, category_repository)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_token_repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(user_repository, refresh_token_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
) -> UserService:
    return UserService(user_repository, role_repository)


def get_role_service(
    role_repository: RoleRepository = Depends(get_role_repository),
    permission_repository: PermissionRepository = Depends(get_permission_repository),
) -> RoleService:
    return RoleService(role_repository, permission_repository)


def get_permission_service(
    permission_repository: PermissionRepository = Depends(get_permission_repository),
) -> PermissionService:
    return PermissionService(permission_repository)


# --- Auth / RBAC ---

def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_error

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc

    if payload.get("type") != "access":
        raise credentials_error

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise credentials_error from exc

    user = user_repository.get_by_id(user_id)
    if user is None:
        raise credentials_error

    if user.blocked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")

    return user


def require_permissions(*required_permissions: str) -> Callable[..., User]:
    """Dependencia de RBAC: exige que el usuario autenticado tenga, a traves
    de su rol activo, todos los permisos indicados."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        has_active_role = current_user.role is not None and current_user.role.active
        user_permissions = (
            {permission.name for permission in current_user.role.permissions} if has_active_role else set()
        )

        if not set(required_permissions).issubset(user_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

        return current_user

    return checker
