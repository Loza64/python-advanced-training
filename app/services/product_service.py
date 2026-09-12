from app.models.product import Product
from fastapi_pagination import Page, Params
from app.core.ports import ProductRepositoryPort
from app.mappers.product_mapper import ProductMapper
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, repository: ProductRepositoryPort) -> None:
        self.repository = repository

    def list(self, params: Params, sort: list[str] | None) -> Page[Product]:
        return self.repository.list(params, sort)

    def get(self, product_id: int) -> Product | None:
        return self.repository.get(product_id)

    def create(self, data: ProductCreate) -> Product:
        return self.repository.add(ProductMapper.to_model(data))

    def update(self, product_id: int, data: ProductUpdate) -> Product | None:
        product = self.repository.get(product_id)
        if product is None:
            return None
        values = data.model_dump(exclude={"category"})
        values["category_id"] = data.category.id
        for field, value in values.items():
            setattr(product, field, value)
        return self.repository.save(product)

    def delete(self, product_id: int) -> bool:
        product = self.repository.get(product_id)
        if product is None:
            return False
        self.repository.delete(product)
        return True