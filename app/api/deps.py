from datetime import timedelta
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.security import BcryptPasswordHasher, JwtAccessTokenProvider, Sha256OpaqueTokenProvider
from app.core.config import settings
from app.core.ports import AccessTokenPort, OpaqueTokenPort, PasswordHasherPort
from app.db.session import get_db
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
from app.services.refresh_token_service import RefreshTokenService
from app.services.role_service import RoleService
from app.services.user_service import UserService


@lru_cache
def get_password_hasher() -> PasswordHasherPort:
    return BcryptPasswordHasher()


@lru_cache
def get_access_token_provider() -> AccessTokenPort:
    return JwtAccessTokenProvider(
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@lru_cache
def get_opaque_token_provider() -> OpaqueTokenPort:
    return Sha256OpaqueTokenProvider()


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


def get_category_service(repository: CategoryRepository = Depends(get_category_repository)) -> CategoryService:
    return CategoryService(repository)


def get_product_service(
    repository: ProductRepository = Depends(get_product_repository),
    category_repository: CategoryRepository = Depends(get_category_repository),
) -> ProductService:
    return ProductService(repository, category_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    role_repository: RoleRepository = Depends(get_role_repository),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
) -> UserService:
    return UserService(user_repository, role_repository, password_hasher)


def get_role_service(
    role_repository: RoleRepository = Depends(get_role_repository),
    permission_repository: PermissionRepository = Depends(get_permission_repository),
) -> RoleService:
    return RoleService(role_repository, permission_repository)


def get_permission_service(
    permission_repository: PermissionRepository = Depends(get_permission_repository),
) -> PermissionService:
    return PermissionService(permission_repository)


def get_refresh_token_service(
    repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
    tokens: OpaqueTokenPort = Depends(get_opaque_token_provider),
) -> RefreshTokenService:
    return RefreshTokenService(
        repository,
        tokens,
        ttl=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
    access_tokens: AccessTokenPort = Depends(get_access_token_provider),
) -> AuthService:
    return AuthService(user_service, refresh_token_service, password_hasher, access_tokens)
