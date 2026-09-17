import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService


class ProductCategoryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not self._is_product_write(request):
            return await call_next(request)

        body = await request.body()

        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        request._receive = receive  # noqa: SLF001

        try:
            payload = json.loads(body)
            category_id = payload["category"]["id"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return JSONResponse(
                status_code=422,
                content={"detail": "category.id must be an integer"},
            )

        if type(category_id) is not int:
            return JSONResponse(
                status_code=422,
                content={"detail": "category.id must be an integer"},
            )

        with SessionLocal() as db:
            category = CategoryService(CategoryRepository(db)).get(category_id)

        if category is None:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Category {category_id} not found"},
            )

        return await call_next(request)

    @staticmethod
    def _is_product_write(request: Request) -> bool:
        products_path = f"{settings.api_v1_prefix}/products"
        is_create = request.method == "POST" and request.url.path == products_path
        is_update = request.method == "PUT" and request.url.path.startswith(f"{products_path}/")
        return is_create or is_update
