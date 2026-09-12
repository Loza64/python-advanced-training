from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params) -> Page[Product]:
        query = select(Product).order_by(Product.id)
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