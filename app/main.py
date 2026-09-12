import logging
import time

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import add_pagination
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.v1 import categories, products
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.project_name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exception: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exception.errors()})


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