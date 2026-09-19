"""Orquestación de seeders. La lógica de cada seeder vive en su servicio
correspondiente (PermissionService, RoleService, UserService); este módulo
solo construye las dependencias (repositorios -> servicios, igual que
app/api/deps.py) y los llama en el orden correcto. Todo el proceso es
idempotente y se ejecuta en cada arranque de la app (ver app/main.py)."""

import logging

from sqlalchemy.orm import Session

from app.core.constants import ADMIN_ROLE_NAME, CLIENT_ROLE_NAME, SUPER_ADMIN_ROLE_NAME
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

DEFAULT_PERMISSIONS: list[tuple[str, str]] = [
    ("users:list", "Listar usuarios"),
    ("users:read", "Ver detalle de un usuario"),
    ("users:create", "Crear usuarios"),
    ("users:update", "Actualizar usuarios"),
    ("users:delete", "Eliminar usuarios"),
    ("roles:list", "Listar roles"),
    ("roles:read", "Ver detalle de un rol"),
    ("roles:create", "Crear roles"),
    ("roles:update", "Actualizar roles"),
    ("roles:delete", "Eliminar roles"),
    ("permissions:list", "Listar permisos"),
    ("permissions:read", "Ver detalle de un permiso"),
    ("permissions:update", "Actualizar el titulo de un permiso"),
    ("products:list", "Listar productos"),
    ("products:read", "Ver detalle de un producto"),
    ("products:create", "Crear productos"),
    ("products:update", "Actualizar productos"),
    ("products:delete", "Eliminar productos"),
    ("categories:list", "Listar categorias"),
    ("categories:read", "Ver detalle de una categoria"),
    ("categories:create", "Crear categorias"),
    ("categories:update", "Actualizar categorias"),
    ("categories:delete", "Eliminar categorias"),
]

# Permisos por rol de sistema. `None` significa "todos los permisos existentes"
# (y se recalcula así en cada arranque, para que super_admin nunca se quede
# atrás si en el futuro se agregan más permisos al sistema).
ROLE_PERMISSIONS: dict[str, list[str] | None] = {
    SUPER_ADMIN_ROLE_NAME: None,
    ADMIN_ROLE_NAME: [
        "users:list",
        "users:read",
        "users:create",
        "users:update",
        "users:delete",
        "products:list",
        "products:read",
        "products:create",
        "products:update",
        "products:delete",
        "categories:list",
        "categories:read",
        "categories:create",
        "categories:update",
        "categories:delete",
    ],
    CLIENT_ROLE_NAME: [
        "products:list",
        "products:read",
        "categories:list",
        "categories:read",
    ],
}


def run_seeders(db: Session) -> None:
    """Ejecuta, en orden, los seeders de permisos, roles y super_admin.
    Cada seeder es un método del servicio correspondiente; aquí solo se
    conectan (repositorio -> servicio) y se invocan, igual que en deps.py."""
    permission_service = PermissionService(PermissionRepository(db))
    role_service = RoleService(RoleRepository(db), PermissionRepository(db))
    user_service = UserService(UserRepository(db), RoleRepository(db))

    permissions = permission_service.seed_defaults(DEFAULT_PERMISSIONS)
    roles = role_service.seed_system_roles(permissions, ROLE_PERMISSIONS)

    super_admin = user_service.seed_super_admin(roles[SUPER_ADMIN_ROLE_NAME])
    if super_admin is not None:
        logger.warning(
            "Usuario super_admin inicial creado (username=%s). "
            "La contraseña es la definida en SUPER_ADMIN_PASSWORD; cámbiala si usaste el valor por defecto.",
            super_admin.username,
        )
