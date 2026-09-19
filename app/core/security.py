import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def hash_token(raw_token: str) -> str:
    """sha256 del refresh token, tal como especifica la entidad RefreshToken."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(subject: int) -> str:
    """El access token solo carga el id del usuario (sub) — nada de
    permisos ni otros datos de perfil. El RBAC (require_permissions) ya
    resuelve los permisos consultando el rol del usuario en cada request,
    así que no hay necesidad de "cachearlos" en el token, y evita que
    queden permisos obsoletos válidos hasta que expire el token si el rol
    cambia mientras tanto."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])