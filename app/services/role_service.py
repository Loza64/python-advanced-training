from app.core.exceptions import DuplicateRoleNameError
from app.core.ports import PermissionRepositoryProtocol, RoleRepositoryProtocol
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, repository: RoleRepositoryProtocol, permission_repository: PermissionRepositoryProtocol) -> None:
        self.repository = repository
        self.permission_repository = permission_repository

    def list(self) -> list[Role]:
        return self.repository.list_all()

    def get(self, role_id: int) -> Role | None:
        return self.repository.get_by_id(role_id)

    def create(self, data: RoleCreate) -> Role:
        name = data.name.strip()
        if self.repository.get_by_name(name) is not None:
            raise DuplicateRoleNameError(name)

        role = Role(
            name=name,
            active=data.active,
            permissions=self.permission_repository.get_by_ids(data.permission_ids),
        )
        return self.repository.create(role)

    def update(self, role_id: int, data: RoleUpdate) -> Role | None:
        role = self.repository.get_by_id(role_id)
        if role is None:
            return None

        if data.name is not None:
            candidate = data.name.strip()
            existing = self.repository.get_by_name(candidate)
            if existing is not None and existing.id != role_id:
                raise DuplicateRoleNameError(candidate)
            role.name = candidate

        if data.active is not None:
            role.active = data.active

        if data.permission_ids is not None:
            role.permissions = self.permission_repository.get_by_ids(data.permission_ids)

        return self.repository.save(role)

    def delete(self, role_id: int) -> bool:
        role = self.repository.get_by_id(role_id)
        if role is None:
            return False
        self.repository.delete(role)
        return True
