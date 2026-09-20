from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse


class ProductMapper:
    @staticmethod
    def to_model(data: ProductCreate) -> Product:
        values = data.model_dump(exclude={"category"})
        values["category_id"] = data.category.id
        return Product(**values)

    @staticmethod
    def to_response(product: Product) -> ProductResponse:
        return ProductResponse.model_validate(product)

    @staticmethod
    def to_responses(products: list[Product]) -> list[ProductResponse]:
        return [ProductMapper.to_response(product) for product in products]
