from __future__ import annotations

from app.core.exceptions import PermissionNotFoundError
from app.core.ports import PermissionRepositoryProtocol
from app.models.permission import Permission
from app.schemas.permission import PermissionUpdate


class PermissionService:
    """Los permisos no se crean ni se eliminan vía API: solo se listan,
    se consultan y se actualiza su 'title' (el 'name' identifica al permiso
    y no es editable). Tampoco se soportan borrado lógico ni restore."""

    def __init__(self, repository: PermissionRepositoryProtocol) -> None:
        self.repository = repository

    def list(self) -> list[Permission]:
        return self.repository.list_all()

    def get(self, permission_id: int) -> Permission:
        permission = self.repository.get_by_id(permission_id)
        if permission is None:
            raise PermissionNotFoundError(permission_id)
        return permission

    def update(self, permission_id: int, data: PermissionUpdate) -> Permission:
        permission = self.repository.get_by_id(permission_id)
        if permission is None:
            raise PermissionNotFoundError(permission_id)
        permission.title = data.title
        return self.repository.save(permission)

    def seed_defaults(self, definitions: list[tuple[str, str]]) -> list[Permission]:
        """Crea (si no existen) los permisos base del sistema. Idempotente:
        cada permiso se busca por 'name' y solo se crea si no existe."""
        return [self.repository.get_or_create(name, title) for name, title in definitions]
