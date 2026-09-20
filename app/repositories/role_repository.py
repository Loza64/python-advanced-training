from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, role_id: int, with_permissions: bool = False) -> Optional[Role]:
        query = self.db.query(Role).filter(Role.id == role_id, Role.deleted_at.is_(None))
        return self._apply_loading(query, with_permissions).first()

    def get_by_name(self, name: str, with_permissions: bool = False) -> Optional[Role]:
        query = self.db.query(Role).filter(Role.name == name, Role.deleted_at.is_(None))
        return self._apply_loading(query, with_permissions).first()

    def list_all(self, with_permissions: bool = False) -> list[Role]:
        query = self.db.query(Role).filter(Role.deleted_at.is_(None)).order_by(Role.id)
        return self._apply_loading(query, with_permissions).all()

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return self._get_with_permissions(role.id)

    def save(self, role: Role) -> Role:
        self.db.flush()
        return self._get_with_permissions(role.id)

    def delete(self, role: Role) -> None:
        role.deleted_at = datetime.now(timezone.utc)
        self.db.flush()

    def restore(self, role_id: int) -> Optional[Role]:
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if role is None or role.deleted_at is None:
            return None
        role.deleted_at = None
        self.db.flush()
        return self._get_with_permissions(role_id)

    def _apply_loading(self, query, with_permissions: bool):
        if with_permissions:
            return query.options(joinedload(Role.permissions))
        return query

    def _get_with_permissions(self, role_id: int) -> Role:
        query = self.db.query(Role).filter(Role.id == role_id)
        return self._apply_loading(query, with_permissions=True).one()
