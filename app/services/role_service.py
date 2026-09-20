from __future__ import annotations

from app.core.constants import SUPER_ADMIN_ROLE_NAME, SYSTEM_ROLE_NAMES
from app.core.exceptions import (
    DuplicateRoleNameError,
    PermissionNotFoundError,
    RoleNotFoundError,
    SystemRoleProtectedError,
)
from app.core.ports import PermissionRepositoryProtocol, RoleRepositoryProtocol
from app.models.permission import Permission
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(
        self,
        repository: RoleRepositoryProtocol,
        permission_repository: PermissionRepositoryProtocol,
    ) -> None:
        self.repository = repository
        self.permission_repository = permission_repository

    def list(self) -> list[Role]:
        return self.repository.list_all()

    def get(self, role_id: int) -> Role:
        role = self.repository.get_by_id(role_id, with_permissions=True)
        if role is None:
            raise RoleNotFoundError(role_id)
        return role

    def create(self, data: RoleCreate) -> Role:
        name = data.name.strip()
        if self.repository.get_by_name(name) is not None:
            raise DuplicateRoleNameError(name)

        role = Role(
            name=name,
            active=data.active,
            permissions=self._get_permissions_by_references(data.permissions),
        )
        return self.repository.create(role)

    def update(self, role_id: int, data: RoleUpdate) -> Role:
        role = self.repository.get_by_id(role_id, with_permissions=True)
        if role is None:
            raise RoleNotFoundError(role_id)

        if role.name == SUPER_ADMIN_ROLE_NAME:
            raise SystemRoleProtectedError(role.name)

        if data.name is not None:
            candidate = data.name.strip()
            if role.name in SYSTEM_ROLE_NAMES and candidate != role.name:
                raise SystemRoleProtectedError(role.name)
            
            existing = self.repository.get_by_name(candidate)
            if existing is not None and existing.id != role_id:
                raise DuplicateRoleNameError(candidate)
            role.name = candidate

        if data.active is not None:
            role.active = data.active

        if data.permissions is not None:
            role.permissions = self._get_permissions_by_references(data.permissions)

        return self.repository.save(role)

    def delete(self, role_id: int) -> None:
        role = self.repository.get_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        if role.name in SYSTEM_ROLE_NAMES:
            raise SystemRoleProtectedError(role.name)
        self.repository.delete(role)

    def restore(self, role_id: int) -> Role:
        role = self.repository.restore(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        return role

    def seed_system_roles(
        self,
        permissions: list[Permission],
        role_permissions: dict[str, list[str] | None],
    ) -> dict[str, Role]:
        permissions_by_name = {permission.name: permission for permission in permissions}
        roles: dict[str, Role] = {}

        for role_name, permission_names in role_permissions.items():
            if permission_names is None:
                role_perms = list(permissions_by_name.values())
            else:
                role_perms = [
                    permissions_by_name[name]
                    for name in permission_names
                    if name in permissions_by_name
                ]

            role = self.repository.get_by_name(role_name, with_permissions=True)
            if role is None:
                role = self.repository.create(
                    Role(name=role_name, active=True, permissions=role_perms)
                )
            elif permission_names is None:
                role.permissions = role_perms
                role = self.repository.save(role)

            roles[role_name] = role

        return roles

    def _get_permissions_by_references(self, references: list) -> list[Permission]:
        ids = [ref.id for ref in references]
        return self._get_permissions_by_ids(ids)

    def _get_permissions_by_ids(self, ids: list[int]) -> list[Permission]:
        unique_ids = list(dict.fromkeys(ids))
        permissions = self.permission_repository.get_by_ids(unique_ids)

        found_ids = {permission.id for permission in permissions}
        for permission_id in unique_ids:
            if permission_id not in found_ids:
                raise PermissionNotFoundError(permission_id)

        return permissions