from typing import Optional

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.sorting import apply_sort


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self, params: Params, sort: list[str] | None, search: str | None
    ) -> Page[Permission]:
        query = select(Permission).where(Permission.deleted_at.is_(None))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Permission.name.ilike(search_pattern),
                    Permission.title.ilike(search_pattern),
                )
            )
        if sort:
            query = apply_sort(
                query,
                Permission,
                sort,
                {"id", "name", "title"},
            )
        else:
            query = query.order_by(Permission.id)
        return paginate(self.db, query, params)

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
        self.db.flush()
        self.db.refresh(permission)
        return permission
