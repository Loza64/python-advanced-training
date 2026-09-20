from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.repositories.sorting import apply_sort
from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Product]:
        query = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.deleted_at.is_(None))
        )
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(Product.name.ilike(search_pattern), Product.description.ilike(search_pattern))
            )
        if sort:
            query = apply_sort(
                query,
                Product,
                sort,
                {"id", "name", "description", "price", "in_stock", "category_id"},
            )
        else:
            query = query.order_by(Product.id)
        return paginate(self.session, query, params)

    def get(self, product_id: int) -> Product | None:
        return self.session.scalar(
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return self.get(product.id)

    def save(self, product: Product) -> Product:
        self.session.flush()
        return self.get(product.id)

    def delete(self, product: Product) -> None:
        product.deleted_at = datetime.now(timezone.utc)
        self.session.flush()

    def restore(self, product_id: int) -> Product | None:
        product = self.session.scalar(select(Product).where(Product.id == product_id))
        if product is None or product.deleted_at is None:
            return None
        product.deleted_at = None
        self.session.flush()
        return self.get(product_id)
