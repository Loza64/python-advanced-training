from typing import List
from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseEntity
from app.models.associations import role_permissions
from app.models.permission import Permission


class Role(BaseEntity):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("name", name="uq_roles_name"),)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # raise_on_sql: nunca se dispara un SELECT lazy implícito para cargar
    # permissions (evita N+1 y el patrón "olvidé el eager load"). Cualquier
    # código que necesite permissions debe pedirlo explícitamente vía
    # `joinedload(Role.permissions)` en el repositorio.
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_permissions, lazy="raise_on_sql"
    )
