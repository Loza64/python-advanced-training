from app.models.product import Product
from fastapi_pagination import Page, Params
from app.core.exceptions import CategoryNotFoundError, ProductNotFoundError
from app.core.ports import CategoryRepositoryPort, ProductRepositoryPort
from app.mappers.product_mapper import ProductMapper
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(
        self,
        repository: ProductRepositoryPort,
        category_repository: CategoryRepositoryPort,
    ) -> None:
        self.repository = repository
        self.category_repository = category_repository

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Product]:
        return self.repository.list(params, sort, search)

    def get(self, product_id: int) -> Product:
        product = self.repository.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def create(self, data: ProductCreate) -> Product:
        self._ensure_category_exists(data.category.id)
        return self.repository.add(ProductMapper.to_model(data))

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.repository.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        self._ensure_category_exists(data.category.id)
        values = data.model_dump(exclude={"category"})
        values["category_id"] = data.category.id
        for field, value in values.items():
            setattr(product, field, value)
        return self.repository.save(product)

    def delete(self, product_id: int) -> None:
        product = self.repository.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        self.repository.delete(product)

    def restore(self, product_id: int) -> Product:
        product = self.repository.restore(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def _ensure_category_exists(self, category_id: int) -> None:
        if self.category_repository.get(category_id) is None:
            raise CategoryNotFoundError(category_id)
