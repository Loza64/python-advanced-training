from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.sorting import apply_sort
from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None) -> Page[Category]:
        query = select(Category)
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
        return self.session.get(Category, category_id)

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
        self.session.delete(category)
        self.session.commit()