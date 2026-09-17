from fastapi_pagination import Page, Params

from app.core.exceptions import EmailAlreadyExistsError, RoleNotFoundError, UsernameAlreadyExistsError
from app.core.ports import RoleRepositoryProtocol, UserRepositoryProtocol
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepositoryProtocol, role_repository: RoleRepositoryProtocol) -> None:
        self.repository = repository
        self.role_repository = role_repository

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[User]:
        return self.repository.list(params, sort, search)

    def get(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def create(self, data: UserCreate) -> User:
        if self.repository.get_by_username(data.username) is not None:
            raise UsernameAlreadyExistsError(data.username)
        if self.repository.get_by_email(data.email) is not None:
            raise EmailAlreadyExistsError(data.email)
        if data.role_id is not None and self.role_repository.get_by_id(data.role_id) is None:
            raise RoleNotFoundError(data.role_id)

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

    def update(self, user_id: int, data: UserUpdate) -> User | None:
        user = self.repository.get_by_id(user_id)
        if user is None:
            return None

        if data.email is not None and data.email != user.email:
            existing = self.repository.get_by_email(data.email)
            if existing is not None and existing.id != user_id:
                raise EmailAlreadyExistsError(data.email)
            user.email = data.email

        if data.role_id is not None:
            if self.role_repository.get_by_id(data.role_id) is None:
                raise RoleNotFoundError(data.role_id)
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

    def delete(self, user_id: int) -> bool:
        user = self.repository.get_by_id(user_id)
        if user is None:
            return False
        self.repository.delete(user)
        return True
