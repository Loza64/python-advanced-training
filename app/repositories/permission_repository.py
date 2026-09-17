from typing import Optional

from sqlalchemy.orm import Session

from app.models.permission import Permission


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Permission]:
        return self.db.query(Permission).order_by(Permission.id).all()

    def get_by_id(self, permission_id: int) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_name(self, name: str) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.name == name).first()

    def get_by_ids(self, ids: list[int]) -> list[Permission]:
        if not ids:
            return []
        return self.db.query(Permission).filter(Permission.id.in_(ids)).all()

    def get_or_create(self, name: str, title: str | None = None) -> Permission:
        perm = self.get_by_name(name)
        if perm is None:
            perm = Permission(name=name, title=title)
            self.db.add(perm)
            self.db.flush()
        return perm

    def save(self, permission: Permission) -> Permission:
        self.db.commit()
        self.db.refresh(permission)
        return permission
