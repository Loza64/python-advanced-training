from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.sorting import apply_sort
from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None) -> Page[Product]:
        query = select(Product)
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
        return self.session.get(Product, product_id)

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
        self.session.delete(product)
        self.session.commit()