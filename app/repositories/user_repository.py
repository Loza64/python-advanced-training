from datetime import datetime, timezone
from typing import Optional

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.sorting import apply_sort
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.username == username, User.deleted_at.is_(None))
            .first()
        )

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

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[User]:
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
        return paginate(self.db, query, params)

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Borrado lógico: marca deleted_at en vez de eliminar la fila."""
        user.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def restore(self, user_id: int) -> Optional[User]:
        """Revierte un borrado lógico. Devuelve None si no existe o si no
        estaba borrado."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None or user.deleted_at is None:
            return None
        user.deleted_at = None
        self.db.commit()
        self.db.refresh(user)
        return user
