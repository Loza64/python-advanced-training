from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.sorting import apply_sort
from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Category]:
        query = select(Category).where(Category.deleted_at.is_(None))
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(Category.name.ilike(search_pattern), Category.description.ilike(search_pattern))
            )
        if sort:
            query = apply_sort(
                query,
                Category,
                sort,
                {"id", "name", "description"},
            )
        else:
            query = query.order_by(Category.id)
        return paginate(self.session, query, params)

    def get(self, category_id: int) -> Category | None:
        return self.session.scalar(
            select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))
        )

    def get_by_name(self, name: str) -> Category | None:
        return self.session.scalar(
            select(Category).where(Category.name.ilike(name), Category.deleted_at.is_(None))
        )

    def add(self, category: Category) -> Category:
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def save(self, category: Category) -> Category:
        self.session.commit()
        self.session.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        """Borrado lógico: marca deleted_at en vez de eliminar la fila."""
        category.deleted_at = datetime.now(timezone.utc)
        self.session.commit()

    def restore(self, category_id: int) -> Category | None:
        """Revierte un borrado lógico. Devuelve None si no existe o si no
        estaba borrada."""
        category = self.session.scalar(select(Category).where(Category.id == category_id))
        if category is None or category.deleted_at is None:
            return None
        category.deleted_at = None
        self.session.commit()
        self.session.refresh(category)
        return category
