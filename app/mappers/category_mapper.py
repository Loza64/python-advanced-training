from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse


class CategoryMapper:
    @staticmethod
    def to_model(data: CategoryCreate) -> Category:
        return Category(**data.model_dump())

    @staticmethod
    def to_response(category: Category) -> CategoryResponse:
        return CategoryResponse.model_validate(category)

    @staticmethod
    def to_responses(categories: list[Category]) -> list[CategoryResponse]:
        return [CategoryMapper.to_response(category) for category in categories]