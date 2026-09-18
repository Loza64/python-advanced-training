from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, role_id: int) -> Optional[Role]:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.id == role_id, Role.deleted_at.is_(None))
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Role]:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.name == name, Role.deleted_at.is_(None))
            .first()
        )

    def list_all(self) -> list[Role]:
        return (
            self.db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.deleted_at.is_(None))
            .order_by(Role.id)
            .all()
        )

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def save(self, role: Role) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        """Borrado lógico: marca deleted_at en vez de eliminar la fila."""
        role.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def restore(self, role_id: int) -> Optional[Role]:
        """Revierte un borrado lógico. Devuelve None si no existe o si no
        estaba borrado."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if role is None or role.deleted_at is None:
            return None
        role.deleted_at = None
        self.db.commit()
        self.db.refresh(role)
        return role
