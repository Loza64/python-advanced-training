import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenReuseDetectedError,
    UserBlockedError,
    UsernameAlreadyExistsError,
)
from app.core.ports import RefreshTokenRepositoryProtocol, UserRepositoryProtocol
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest


class AuthService:
    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository

    @staticmethod
    def _permissions_for(user: User) -> list[str]:
        if user.role and user.role.active:
            return [permission.name for permission in user.role.permissions]
        return []

    def _issue_tokens(self, user: User, family_id: str | None = None) -> tuple[str, str]:
        permissions = self._permissions_for(user)
        access_token = create_access_token(user.id, permissions)

        raw_refresh_token = secrets.token_urlsafe(64)
        refresh_token = RefreshToken(
            token=hash_token(raw_refresh_token),
            family_id=family_id or str(uuid.uuid4()),
            used=False,
            revoked=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            user_id=user.id,
        )
        self.refresh_token_repository.create(refresh_token)
        return access_token, raw_refresh_token

    def _build_response(self, user: User, access_token: str, raw_refresh_token: str) -> AuthResponse:
        data = json.dumps(
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "role": user.role.name if user.role else None,
                "permissions": self._permissions_for(user),
            }
        )
        return AuthResponse(token=access_token, refreshToken=raw_refresh_token, data=data)

    def signup(self, payload: SignupRequest) -> AuthResponse:
        if self.user_repository.get_by_username(payload.username) is not None:
            raise UsernameAlreadyExistsError(payload.username)
        if self.user_repository.get_by_email(payload.email) is not None:
            raise EmailAlreadyExistsError(payload.email)

        user = User(
            username=payload.username,
            name=payload.name,
            surname=payload.surname,
            email=payload.email,
            password=hash_password(payload.password),
            blocked=False,
        )
        user = self.user_repository.create(user)

        access_token, raw_refresh_token = self._issue_tokens(user)
        return self._build_response(user, access_token, raw_refresh_token)

    def login(self, payload: LoginRequest) -> AuthResponse:
        user = self.user_repository.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.password):
            raise InvalidCredentialsError("Invalid username or password")
        if user.blocked:
            raise UserBlockedError("User is blocked")

        access_token, raw_refresh_token = self._issue_tokens(user)
        return self._build_response(user, access_token, raw_refresh_token)

    def refresh(self, raw_refresh_token: str) -> AuthResponse:
        token_hash = hash_token(raw_refresh_token)
        stored = self.refresh_token_repository.get_by_token_hash(token_hash)

        if stored is None or stored.revoked:
            raise InvalidRefreshTokenError("Invalid refresh token")

        if stored.used:
            # Reuso detectado: alguien está reutilizando un refresh token ya
            # consumido. Se revoca toda la family por seguridad.
            self.refresh_token_repository.revoke_family(stored.family_id)
            raise RefreshTokenReuseDetectedError("Refresh token reuse detected")

        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Refresh token expired")

        user = stored.user
        if user.blocked:
            raise UserBlockedError("User is blocked")

        stored.used = True
        self.refresh_token_repository.save(stored)

        access_token, new_raw_refresh_token = self._issue_tokens(user, family_id=stored.family_id)
        return self._build_response(user, access_token, new_raw_refresh_token)

    def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        stored = self.refresh_token_repository.get_by_token_hash(token_hash)
        if stored is not None:
            self.refresh_token_repository.revoke_family(stored.family_id)
