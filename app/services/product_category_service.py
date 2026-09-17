from typing import Any

from app.core.exceptions import CategoryNotFoundError, ProductCategoryValidationError
from app.core.ports import CategoryRepositoryPort


class ProductCategoryService:
    def __init__(self, category_repository: CategoryRepositoryPort) -> None:
        self.category_repository = category_repository

    def validate_payload(self, payload: Any) -> int:
        try:
            category_id = payload["category"]["id"]
        except (KeyError, TypeError, IndexError) as exc:
            raise ProductCategoryValidationError() from exc

        if type(category_id) is not int:
            raise ProductCategoryValidationError()

        self.validate_exists(category_id)
        return category_id

    def validate_exists(self, category_id: int) -> None:
        if self.category_repository.get(category_id) is None:
            raise CategoryNotFoundError(category_id)
