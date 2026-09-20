import logging

from sqlalchemy.orm import Session

from app.adapters.security import BcryptPasswordHasher
from app.core.config import settings
from app.core.constants import ADMIN_ROLE_NAME, CLIENT_ROLE_NAME, SUPER_ADMIN_ROLE_NAME
from app.core.permissions import (
    CREATE_CATEGORY,
    CREATE_PRODUCT,
    CREATE_USER,
    DELETE_CATEGORY,
    DELETE_PRODUCT,
    DELETE_USER,
    LIST_CATEGORIES,
    LIST_PRODUCTS,
    LIST_USERS,
    PERMISSION_TITLES,
    READ_CATEGORY,
    READ_PRODUCT,
    READ_USER,
    UPDATE_CATEGORY,
    UPDATE_PRODUCT,
    UPDATE_USER,
)
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.schemas.user import UserCreate
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

DEFAULT_PERMISSIONS: list[tuple[str, str]] = list(PERMISSION_TITLES.items())

ROLE_PERMISSIONS: dict[str, list[str] | None] = {
    SUPER_ADMIN_ROLE_NAME: None,
    ADMIN_ROLE_NAME: [
        LIST_USERS,
        READ_USER,
        CREATE_USER,
        UPDATE_USER,
        DELETE_USER,
        LIST_PRODUCTS,
        READ_PRODUCT,
        CREATE_PRODUCT,
        UPDATE_PRODUCT,
        DELETE_PRODUCT,
        LIST_CATEGORIES,
        READ_CATEGORY,
        CREATE_CATEGORY,
        UPDATE_CATEGORY,
        DELETE_CATEGORY,
    ],
    CLIENT_ROLE_NAME: [
        LIST_PRODUCTS,
        READ_PRODUCT,
        LIST_CATEGORIES,
        READ_CATEGORY,
    ],
}


def run_seeders(db: Session) -> None:
    permission_service = PermissionService(PermissionRepository(db))
    role_service = RoleService(RoleRepository(db), PermissionRepository(db))
    user_service = UserService(UserRepository(db), RoleRepository(db), BcryptPasswordHasher())

    permissions = permission_service.seed_defaults(DEFAULT_PERMISSIONS)
    roles = role_service.seed_system_roles(permissions, ROLE_PERMISSIONS)

    super_admin = user_service.seed_super_admin(
        roles[SUPER_ADMIN_ROLE_NAME],
        UserCreate(
            username=settings.SUPER_ADMIN_USERNAME,
            name=settings.SUPER_ADMIN_NAME,
            surname=settings.SUPER_ADMIN_SURNAME,
            email=settings.SUPER_ADMIN_EMAIL,
            password=settings.SUPER_ADMIN_PASSWORD,
        ),
    )
    if super_admin is not None:
        logger.warning(
            "Usuario super_admin inicial creado (username=%s). "
            "La contraseña es la definida en SUPER_ADMIN_PASSWORD; cámbiala si usaste el valor por defecto.",
            super_admin.username,
        )
