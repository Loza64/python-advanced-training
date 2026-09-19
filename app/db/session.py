from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    """Sesión por request con un único límite de transacción: los
    repositorios solo hacen flush() (para obtener ids/defaults del server y
    dejar los cambios visibles dentro de la misma transacción), y aquí se
    hace commit una sola vez si el request termina bien, o rollback si algo
    lanza una excepción. Así una operación que toca varios repositorios
    (p. ej. AuthService.signup: crear usuario + crear refresh token) es
    atómica en vez de ser dos commits independientes."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


__all__ = ["engine", "SessionLocal", "get_db"]