from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse


class ProductMapper:
    @staticmethod
    def to_model(data: ProductCreate) -> Product:
        return Product(**data.model_dump())

    @staticmethod
    def to_response(product: Product) -> ProductResponse:
        return ProductResponse.model_validate(product)

    @staticmethod
    def to_responses(products: list[Product]) -> list[ProductResponse]:
        return [ProductMapper.to_response(product) for product in products]