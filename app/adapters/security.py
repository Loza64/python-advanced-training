import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.exceptions import InvalidAccessTokenError

ACCESS_TOKEN_TYPE = "access"


class BcryptPasswordHasher:
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._context.verify(password, hashed)


class JwtAccessTokenProvider:
    def __init__(self, secret: str, algorithm: str, expire_minutes: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create(self, user_id: int) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
            "type": ACCESS_TOKEN_TYPE,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            token_type = payload.get("type")
            user_id = int(payload["sub"])
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
            raise InvalidAccessTokenError("Invalid access token") from exc

        if token_type != ACCESS_TOKEN_TYPE:
            raise InvalidAccessTokenError("Invalid access token type")

        return user_id


class Sha256OpaqueTokenProvider:
    def __init__(self, nbytes: int = 64) -> None:
        self._nbytes = nbytes

    def generate(self) -> str:
        return secrets.token_urlsafe(self._nbytes)

    def hash(self, raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
