from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.sorting import apply_sort
from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Product]:
        query = select(Product).where(Product.deleted_at.is_(None))
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
            select(Product).where(Product.id == product_id, Product.deleted_at.is_(None))
        )

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def save(self, product: Product) -> Product:
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        """Borrado lógico: marca deleted_at en vez de eliminar la fila."""
        product.deleted_at = datetime.now(timezone.utc)
        self.session.commit()

    def restore(self, product_id: int) -> Product | None:
        """Revierte un borrado lógico. Devuelve None si no existe o si no
        estaba borrado."""
        product = self.session.scalar(select(Product).where(Product.id == product_id))
        if product is None or product.deleted_at is None:
            return None
        product.deleted_at = None
        self.session.commit()
        self.session.refresh(product)
        return product
