import logging

from sqlalchemy.orm import Session

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

DEFAULT_ADMIN_USERNAME = "loza.dev"
DEFAULT_ADMIN_PASSWORD = "passW1234-"


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


def seed_admin(db: Session) -> None:
    """Crea un rol 'admin' con todos los permisos y un usuario admin inicial,
    únicamente si todavía no existe ningún usuario en la base de datos."""
    permissions = seed_permissions(db)

    if db.query(User).count() > 0:
        return

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role is None:
        admin_role = Role(name="admin", active=True, permissions=permissions)
        db.add(admin_role)
        db.flush()

    admin_user = User(
        username=DEFAULT_ADMIN_USERNAME,
        name="Admin",
        surname="Root",
        email="admin@example.com",
        password=hash_password(DEFAULT_ADMIN_PASSWORD),
        blocked=False,
        role_id=admin_role.id,
    )
    db.add(admin_user)
    db.commit()

    logger.warning(
        "Usuario admin inicial creado (username=%s, password=%s). "
        "Cambia esta contraseña en cuanto inicies sesión.",
        DEFAULT_ADMIN_USERNAME,
        DEFAULT_ADMIN_PASSWORD,
    )
