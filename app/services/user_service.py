import logging

from fastapi_pagination import Page, Params

from app.core.constants import SUPER_ADMIN_ROLE_NAME
from app.core.exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    SuperAdminAlreadyExistsError,
    SuperAdminCannotBeDeletedError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)
from app.core.ports import PasswordHasherPort, RoleRepositoryProtocol, UserRepositoryProtocol
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleReference
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        repository: UserRepositoryProtocol,
        role_repository: RoleRepositoryProtocol,
        password_hasher: PasswordHasherPort,
    ) -> None:
        self.repository = repository
        self.role_repository = role_repository
        self.password_hasher = password_hasher

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[User]:
        return self.repository.list(params, sort, search, with_role=True)

    def get(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id, with_role=True)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def find_by_id(self, user_id: int, with_permissions: bool = False) -> User | None:
        return self.repository.get_by_id(user_id, with_permissions=with_permissions)

    def find_by_username(self, username: str, with_permissions: bool = False) -> User | None:
        return self.repository.get_by_username(username, with_permissions=with_permissions)

    def create(self, data: UserCreate) -> User:
        if self.repository.get_by_username(data.username) is not None:
            raise UsernameAlreadyExistsError(data.username)
        if self.repository.get_by_email(data.email) is not None:
            raise EmailAlreadyExistsError(data.email)

        role_id = data.role.id if data.role is not None else None
        if role_id is not None:
            role = self.role_repository.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError(role_id)
            if self._is_super_admin_role_id(role.id) and self.repository.exists_with_role(role.id):
                raise SuperAdminAlreadyExistsError()

        user = User(
            username=data.username,
            name=data.name,
            surname=data.surname,
            email=data.email,
            password=self.password_hasher.hash(data.password),
            role_id=role_id,
            blocked=False,
        )
        return self.repository.create(user)

    def update(self, user_id: int, data: UserUpdate) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if data.email is not None and data.email != user.email:
            existing = self.repository.get_by_email(data.email)
            if existing is not None and existing.id != user_id:
                raise EmailAlreadyExistsError(data.email)
            user.email = data.email

        if data.role is not None:
            role = self.role_repository.get_by_id(data.role.id)
            if role is None:
                raise RoleNotFoundError(data.role.id)
            if self._is_super_admin_role_id(role.id) and self.repository.exists_with_role(
                role.id, exclude_user_id=user_id
            ):
                raise SuperAdminAlreadyExistsError()
            user.role_id = role.id

        if data.name is not None:
            user.name = data.name
        if data.surname is not None:
            user.surname = data.surname
        if data.blocked is not None:
            user.blocked = data.blocked
        if data.password:
            user.password = self.password_hasher.hash(data.password)

        return self.repository.save(user)

    def delete(self, user_id: int) -> None:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if user.role_id is not None and self._is_super_admin_role_id(user.role_id):
            raise SuperAdminCannotBeDeletedError()
        self.repository.delete(user)

    def restore(self, user_id: int) -> User:
        user = self.repository.restore(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def _is_super_admin_role_id(self, role_id: int) -> bool:
        super_admin_role = self.role_repository.get_by_name(SUPER_ADMIN_ROLE_NAME)
        return super_admin_role is not None and super_admin_role.id == role_id

    def seed_super_admin(self, super_admin_role: Role, data: UserCreate) -> User | None:
        if self.repository.exists_with_role(super_admin_role.id):
            return None

        try:
            return self.create(data.model_copy(update={"role": RoleReference(id=super_admin_role.id)}))
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError, SuperAdminAlreadyExistsError) as exc:
            logger.warning(
                "No se creó el super_admin (username='%s', email='%s'): %s. "
                "Asígnale el rol super_admin manualmente si es correcto, o cambia "
                "SUPER_ADMIN_USERNAME/SUPER_ADMIN_EMAIL en el .env.",
                data.username,
                data.email,
                exc,
            )
            return None
