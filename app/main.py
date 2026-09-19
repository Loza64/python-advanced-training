import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import add_pagination
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.v1 import auth, categories, permissions, products, roles, users
from app.core.config import settings
from app.core.exceptions import (
    AppError,
    CategoryNotFoundError,
    DuplicateCategoryNameError,
    DuplicateRoleNameError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PermissionDeniedError,
    PermissionNotFoundError,
    ProductCategoryValidationError,
    ProductNotFoundError,
    RefreshTokenReuseDetectedError,
    RoleNotFoundError,
    SuperAdminAlreadyExistsError,
    SuperAdminCannotBeDeletedError,
    SystemRoleProtectedError,
    UserBlockedError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.seed import run_seeders
from app.db.session import SessionLocal, engine
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
    {
        "name": "Auth",
        "description": "Signup, login, JWT access tokens and refresh token rotation.",
    },
    {
        "name": "Users",
        "description": "CRUD de usuarios (protegido por RBAC).",
    },
    {
        "name": "Roles",
        "description": "CRUD de roles, cada uno con su conjunto de permisos (protegido por RBAC).",
    },
    {
        "name": "Permissions",
        "description": "Consulta de permisos y actualización de su título (sin creación ni borrado).",
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


@app.on_event("startup")
def run_seed() -> None:
    """Ejecuta los seeders al arrancar la app (permisos, roles de sistema y
    super_admin inicial). Es idempotente: no duplica permisos ni roles
    existentes, y no crea un segundo super_admin. Usa su propia sesión (no
    pasa por get_db), así que hace su propio commit/rollback."""
    db = SessionLocal()
    try:
        run_seeders(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exception: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exception.errors()})


_NOT_FOUND_ERRORS = (
    CategoryNotFoundError,
    ProductNotFoundError,
    UserNotFoundError,
    RoleNotFoundError,
    PermissionNotFoundError,
)
_CONFLICT_ERRORS = (
    DuplicateCategoryNameError,
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    DuplicateRoleNameError,
    SuperAdminAlreadyExistsError,
)
_UNAUTHORIZED_ERRORS = (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenReuseDetectedError,
)
_FORBIDDEN_ERRORS = (
    UserBlockedError,
    PermissionDeniedError,
    SystemRoleProtectedError,
    SuperAdminCannotBeDeletedError,
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exception: AppError):
    status_code = 400
    if isinstance(exception, _CONFLICT_ERRORS):
        status_code = 409
    elif isinstance(exception, _NOT_FOUND_ERRORS):
        status_code = 404
    elif isinstance(exception, ProductCategoryValidationError):
        status_code = 422
    elif isinstance(exception, _UNAUTHORIZED_ERRORS):
        status_code = 401
    elif isinstance(exception, _FORBIDDEN_ERRORS):
        status_code = 403

    return JSONResponse(status_code=status_code, content={"detail": str(exception)})


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_: Request, exception: SQLAlchemyError):
    logger.exception("Database error: %s", exception)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, exception: Exception):
    logger.exception("Unhandled application error: %s", exception)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(roles.router, prefix=settings.api_v1_prefix)
app.include_router(permissions.router, prefix=settings.api_v1_prefix)
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