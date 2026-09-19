import logging

from fastapi_pagination import Page, Params

from app.core.config import settings
from app.core.constants import SUPER_ADMIN_ROLE_NAME
from app.core.exceptions import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    SuperAdminAlreadyExistsError,
    SuperAdminCannotBeDeletedError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)
from app.core.ports import RoleRepositoryProtocol, UserRepositoryProtocol
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository: UserRepositoryProtocol, role_repository: RoleRepositoryProtocol) -> None:
        self.repository = repository
        self.role_repository = role_repository

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[User]:
        return self.repository.list(params, sort, search)

    def get(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def create(self, data: UserCreate) -> User:
        if self.repository.get_by_username(data.username) is not None:
            raise UsernameAlreadyExistsError(data.username)
        if self.repository.get_by_email(data.email) is not None:
            raise EmailAlreadyExistsError(data.email)

        if data.role_id is not None:
            role = self.role_repository.get_by_id(data.role_id)
            if role is None:
                raise RoleNotFoundError(data.role_id)
            if self._is_super_admin_role_id(role.id) and self.repository.exists_with_role(role.id):
                raise SuperAdminAlreadyExistsError()

        user = User(
            username=data.username,
            name=data.name,
            surname=data.surname,
            email=data.email,
            password=hash_password(data.password),
            role_id=data.role_id,
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

        if data.role_id is not None:
            role = self.role_repository.get_by_id(data.role_id)
            if role is None:
                raise RoleNotFoundError(data.role_id)
            if self._is_super_admin_role_id(role.id) and self.repository.exists_with_role(
                role.id, exclude_user_id=user_id
            ):
                raise SuperAdminAlreadyExistsError()
            user.role_id = data.role_id

        if data.name is not None:
            user.name = data.name
        if data.surname is not None:
            user.surname = data.surname
        if data.blocked is not None:
            user.blocked = data.blocked
        if data.password:
            user.password = hash_password(data.password)

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
        """Único punto de verdad para identificar el rol super_admin: se
        resuelve su id (el nombre está protegido y nunca cambia, ver
        RoleService.update) y se compara solo por id, no por strings
        repetidos en cada validación."""
        super_admin_role = self.role_repository.get_by_name(SUPER_ADMIN_ROLE_NAME)
        return super_admin_role is not None and super_admin_role.id == role_id

    def seed_super_admin(self, super_admin_role: Role) -> User | None:
        """Crea el usuario super_admin inicial (único) con los datos
        definidos en el .env. Es idempotente: no crea un segundo super_admin.
        La validación de unicidad la aplica `create()`, que es la misma ruta
        usada por la API (única fuente de verdad para esa regla)."""
        if self.repository.exists_with_role(super_admin_role.id):
            return None  # ya existe un usuario con rol super_admin

        try:
            return self.create(
                UserCreate(
                    username=settings.SUPER_ADMIN_USERNAME,
                    name=settings.SUPER_ADMIN_NAME,
                    surname=settings.SUPER_ADMIN_SURNAME,
                    email=settings.SUPER_ADMIN_EMAIL,
                    password=settings.SUPER_ADMIN_PASSWORD,
                    role_id=super_admin_role.id,
                )
            )
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError, SuperAdminAlreadyExistsError) as exc:
            logger.warning(
                "No se creó el super_admin (username='%s', email='%s'): %s. "
                "Asígnale el rol super_admin manualmente si es correcto, o cambia "
                "SUPER_ADMIN_USERNAME/SUPER_ADMIN_EMAIL en el .env.",
                settings.SUPER_ADMIN_USERNAME,
                settings.SUPER_ADMIN_EMAIL,
                exc,
            )
            return None
