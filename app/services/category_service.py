from app.models.category import Category
from fastapi_pagination import Page, Params
from app.core.exceptions import CategoryNotFoundError, DuplicateCategoryNameError
from app.core.ports import CategoryRepositoryPort
from app.mappers.category_mapper import CategoryMapper
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, repository: CategoryRepositoryPort) -> None:
        self.repository = repository

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Category]:
        return self.repository.list(params, sort, search)

    def get(self, category_id: int) -> Category:
        category = self.repository.get(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        return category

    def create(self, data: CategoryCreate) -> Category:
        existing = self.repository.get_by_name(data.name.strip())
        if existing is not None:
            raise DuplicateCategoryNameError(data.name)
        return self.repository.add(CategoryMapper.to_model(data))

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.repository.get(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)

        candidate_name = data.name.strip()
        if candidate_name and candidate_name.lower() != category.name.lower():
            existing = self.repository.get_by_name(candidate_name)
            if existing is not None and existing.id != category_id:
                raise DuplicateCategoryNameError(candidate_name)

        for field, value in data.model_dump().items():
            setattr(category, field, value)
        return self.repository.save(category)

    def delete(self, category_id: int) -> None:
        category = self.repository.get(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        self.repository.delete(category)

    def restore(self, category_id: int) -> Category:
        category = self.repository.restore(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        return category
