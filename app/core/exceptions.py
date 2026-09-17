class AppError(Exception):
    """Base class for application-level business errors."""


class DomainError(AppError):
    """Base class for business/domain validation errors."""


class CategoryNotFoundError(DomainError):
    def __init__(self, category_id: int) -> None:
        self.category_id = category_id
        super().__init__(f"Category {category_id} not found")


class DuplicateCategoryNameError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Category '{name}' already exists")


class ProductCategoryValidationError(DomainError):
    def __init__(self, message: str = "category.id must be an integer") -> None:
        super().__init__(message)
