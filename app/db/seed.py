import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ADMIN_ROLE_NAME, CLIENT_ROLE_NAME, SUPER_ADMIN_ROLE_NAME
from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

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
    ],
    CLIENT_ROLE_NAME: [],
}


def seed_permissions(db: Session) -> list[Permission]:
    """Crea (si no existen) los permisos base del sistema. Idempotente."""
    permissions: list[Permission] = []
    for name, title in DEFAULT_PERMISSIONS:
        permission = db.query(Permission).filter(Permission.name == name).first()
        if permission is None:
            permission = Permission(name=name, title=title)
            db.add(permission)
            db.flush()
        permissions.append(permission)
    db.commit()
    return permissions


def seed_roles(db: Session, permissions: list[Permission]) -> dict[str, Role]:
    """Crea (si no existen) los 3 roles de sistema: super_admin, admin, client.
    Idempotente. super_admin siempre queda con TODOS los permisos, incluso
    si se agregan permisos nuevos en corridas futuras."""
    permissions_by_name = {permission.name: permission for permission in permissions}
    roles: dict[str, Role] = {}

    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role_permissions = (
            list(permissions_by_name.values())
            if permission_names is None
            else [permissions_by_name[name] for name in permission_names if name in permissions_by_name]
        )

        role = db.query(Role).filter(Role.name == role_name).first()
        if role is None:
            role = Role(name=role_name, active=True, permissions=role_permissions)
            db.add(role)
            db.flush()
        elif permission_names is None:
            # super_admin: siempre sincronizado con todos los permisos actuales
            role.permissions = role_permissions

        roles[role_name] = role

    db.commit()
    return roles


def seed_super_admin(db: Session) -> None:
    """Crea los permisos, los 3 roles de sistema, y el usuario super_admin
    inicial (único) con los datos definidos en el .env. Es idempotente:
    no crea un segundo super_admin ni duplica roles/permisos."""
    permissions = seed_permissions(db)
    roles = seed_roles(db, permissions)
    super_admin_role = roles[SUPER_ADMIN_ROLE_NAME]

    if db.query(User).filter(User.role_id == super_admin_role.id).first() is not None:
        return  # ya existe un usuario con rol super_admin

    existing_user = (
        db.query(User)
        .filter(
            (User.username == settings.SUPER_ADMIN_USERNAME)
            | (User.email == settings.SUPER_ADMIN_EMAIL)
        )
        .first()
    )
    if existing_user is not None:
        logger.warning(
            "No se creó el super_admin: ya existe un usuario con username='%s' o email='%s'. "
            "Asígnale el rol super_admin manualmente si es correcto, o cambia SUPER_ADMIN_USERNAME/"
            "SUPER_ADMIN_EMAIL en el .env.",
            settings.SUPER_ADMIN_USERNAME,
            settings.SUPER_ADMIN_EMAIL,
        )
        return

    super_admin_user = User(
        username=settings.SUPER_ADMIN_USERNAME,
        name=settings.SUPER_ADMIN_NAME,
        surname=settings.SUPER_ADMIN_SURNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password=hash_password(settings.SUPER_ADMIN_PASSWORD),
        blocked=False,
        role_id=super_admin_role.id,
    )
    db.add(super_admin_user)
    db.commit()

    logger.warning(
        "Usuario super_admin inicial creado (username=%s). "
        "La contraseña es la definida en SUPER_ADMIN_PASSWORD; cámbiala si usaste el valor por defecto.",
        settings.SUPER_ADMIN_USERNAME,
    )
