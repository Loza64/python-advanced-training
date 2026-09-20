from __future__ import annotations

from app.core.exceptions import PermissionNotFoundError
from app.core.ports import PermissionRepositoryProtocol
from app.models.permission import Permission
from app.schemas.permission import PermissionUpdate


class PermissionService:
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
        return [self.repository.get_or_create(name, title) for name, title in definitions]
