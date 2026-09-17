from typing import Any

from app.core.ports import CategoryRepositoryPort, ProductRepositoryPort
from app.models.category import Category
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate
from app.services.category_service import CategoryService
from app.services.product_service import ProductService


class FakeCategoryRepository(CategoryRepositoryPort):
    def __init__(self, existing: list[Category] | None = None):
        self._items = existing or []

    def list(self, params: Any, sort: list[str] | None, search: str | None):
        return []

    def get(self, category_id: int) -> Category | None:
        return next((item for item in self._items if item.id == category_id), None)

    def get_by_name(self, name: str) -> Category | None:
        return next((item for item in self._items if item.name.lower() == name.lower()), None)

    def add(self, category: Category) -> Category:
        self._items.append(category)
        return category

    def save(self, category: Category) -> Category:
        return category

    def delete(self, category: Category) -> None:
        self._items = [item for item in self._items if item.id != category.id]


class FakeProductRepository(ProductRepositoryPort):
    def __init__(self):
        self.items: list[Any] = []

    def list(self, params: Any, sort: list[str] | None, search: str | None):
        return []

    def get(self, product_id: int):
        return None

    def add(self, product: Any):
        self.items.append(product)
        return product

    def save(self, product: Any):
        return product

    def delete(self, product: Any) -> None:
        self.items = [item for item in self.items if item.id != product.id]


def test_category_service_rejects_duplicate_name() -> None:
    existing = Category(id=1, name="Electronics", description="Existing")
    repository = FakeCategoryRepository([existing])
    service = CategoryService(repository)

    try:
        service.create(CategoryCreate(name="electronics", description="new"))
        assert False, "Expected duplicate-name validation to raise"
    except Exception as exc:  # noqa: BLE001
        assert "already exists" in str(exc).lower()


def test_product_service_requires_existing_category() -> None:
    category_repository = FakeCategoryRepository([])
    product_repository = FakeProductRepository()
    service = ProductService(product_repository, category_repository)

    payload = ProductCreate(
        name="Mouse",
        description="Wireless mouse",
        price=29.99,
        in_stock=True,
        category={"id": 99},
    )

    try:
        service.create(payload)
        assert False, "Expected missing category validation to raise"
    except Exception as exc:  # noqa: BLE001
        assert "not found" in str(exc).lower()
