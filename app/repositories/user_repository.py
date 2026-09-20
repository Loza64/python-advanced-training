from datetime import datetime, timezone
from typing import Optional

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.repositories.sorting import apply_sort
from app.models.role import Role
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self, user_id: int, with_role: bool = False, with_permissions: bool = False
    ) -> Optional[User]:
        query = self.db.query(User).filter(User.id == user_id, User.deleted_at.is_(None))
        return self._apply_loading(query, with_role, with_permissions).first()

    def get_by_username(
        self, username: str, with_role: bool = False, with_permissions: bool = False
    ) -> Optional[User]:
        query = self.db.query(User).filter(User.username == username, User.deleted_at.is_(None))
        return self._apply_loading(query, with_role, with_permissions).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.email == email, User.deleted_at.is_(None))
            .first()
        )

    def exists_with_role(self, role_id: int, exclude_user_id: Optional[int] = None) -> bool:
        query = self.db.query(User.id).filter(User.role_id == role_id, User.deleted_at.is_(None))
        if exclude_user_id is not None:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def list(
        self,
        params: Params,
        sort: list[str] | None,
        search: str | None,
        with_role: bool = False,
    ) -> Page[User]:
        query = select(User).where(User.deleted_at.is_(None))
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.username.ilike(pattern),
                    User.name.ilike(pattern),
                    User.surname.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if sort:
            query = apply_sort(
                query,
                User,
                sort,
                {"id", "username", "name", "surname", "email", "blocked"},
            )
        else:
            query = query.order_by(User.id)
        if with_role:
            query = query.options(joinedload(User.role))
        return paginate(self.db, query, params)

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return self._get_with_role_and_permissions(user.id)

    def save(self, user: User) -> User:
        self.db.flush()
        return self._get_with_role_and_permissions(user.id)

    def delete(self, user: User) -> None:
        user.deleted_at = datetime.now(timezone.utc)
        self.db.flush()

    def restore(self, user_id: int) -> Optional[User]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None or user.deleted_at is None:
            return None
        user.deleted_at = None
        self.db.flush()
        return self._get_with_role_and_permissions(user_id)

    def _apply_loading(self, query, with_role: bool, with_permissions: bool):
        if with_permissions:
            return query.options(joinedload(User.role).joinedload(Role.permissions))
        if with_role:
            return query.options(joinedload(User.role))
        return query

    def _get_with_role_and_permissions(self, user_id: int) -> User:
        query = self.db.query(User).filter(User.id == user_id)
        return self._apply_loading(query, with_role=True, with_permissions=True).one()
