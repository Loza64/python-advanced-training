from typing import Optional
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity
from app.models.role import Role


class User(BaseEntity):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[Optional["Role"]] = relationship(lazy="raise_on_sql")

    @property
    def permission_names(self) -> list[str]:
        if self.role is None or not self.role.active:
            return []
        return [permission.name for permission in self.role.permissions]

    def has_permissions(self, *required_permissions: str) -> bool:
        return set(required_permissions).issubset(self.permission_names)
