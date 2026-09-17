import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import add_pagination
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.v1 import categories, products
from app.core.config import settings
from app.core.exceptions import AppError, CategoryNotFoundError, DuplicateCategoryNameError, ProductCategoryValidationError
from app.core.logging import configure_logging
from app.db.session import engine
from app.middleware.product_category import ProductCategoryMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

openapi_tags = [
    {
        "name": "Products",
        "description": "Create, search, sort, paginate and manage products.",
    },
    {
        "name": "Categories",
        "description": "Create, search, sort, paginate and manage product categories.",
    },
    {
        "name": "Health",
        "description": "Application and database health checks.",
    },
]

app = FastAPI(
    title=settings.project_name,
    summary="Product and category management API",
    description=(
        "## Products API\n\n"
        "A REST API for managing products and categories.\n\n"
        "Use `page` and `size` for pagination, `search` for text filtering, "
        "and repeat `sort` to combine ordering fields."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
        "syntaxHighlight": {"theme": "arta"},
    },
)


app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ProductCategoryMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exception: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exception.errors()})


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exception: AppError):
    status_code = 400
    if isinstance(exception, DuplicateCategoryNameError):
        status_code = 409
    elif isinstance(exception, CategoryNotFoundError):
        status_code = 404
    elif isinstance(exception, ProductCategoryValidationError):
        status_code = 422

    return JSONResponse(status_code=status_code, content={"detail": str(exception)})


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_: Request, exception: SQLAlchemyError):
    logger.exception("Database error: %s", exception)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, exception: Exception):
    logger.exception("Unhandled application error: %s", exception)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(categories.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
add_pagination(app)


@app.get("/")
def read_root():
    return {"message": f"{settings.project_name} is running"}


@app.get("/health/live", tags=["Health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}