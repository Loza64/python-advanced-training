import uuid
from datetime import datetime, timedelta, timezone

from app.core.exceptions import InvalidRefreshTokenError, RefreshTokenReuseDetectedError
from app.core.ports import OpaqueTokenPort, RefreshTokenRepositoryProtocol
from app.models.refresh_token import RefreshToken


class RefreshTokenService:
    def __init__(
        self,
        repository: RefreshTokenRepositoryProtocol,
        tokens: OpaqueTokenPort,
        ttl: timedelta,
    ) -> None:
        self.repository = repository
        self.tokens = tokens
        self.ttl = ttl

    def issue(self, user_id: int, family_id: str | None = None) -> str:
        raw_token = self.tokens.generate()
        self.repository.create(
            RefreshToken(
                token=self.tokens.hash(raw_token),
                family_id=family_id or str(uuid.uuid4()),
                used=False,
                revoked=False,
                expires_at=datetime.now(timezone.utc) + self.ttl,
                user_id=user_id,
            )
        )
        return raw_token

    def get_valid(self, raw_token: str, with_user_permissions: bool = False) -> RefreshToken:
        stored = self.repository.get_by_token_hash(
            self.tokens.hash(raw_token), with_user_permissions=with_user_permissions
        )

        if stored is None or stored.revoked:
            raise InvalidRefreshTokenError("Invalid refresh token")

        if stored.used:
            self.repository.revoke_family(stored.family_id)
            self.repository.commit()
            raise RefreshTokenReuseDetectedError("Refresh token reuse detected")

        if self._is_expired(stored):
            raise InvalidRefreshTokenError("Refresh token expired")

        return stored

    def mark_as_used(self, refresh_token: RefreshToken) -> None:
        refresh_token.used = True
        self.repository.save(refresh_token)

    def revoke_session(self, raw_token: str) -> None:
        stored = self.repository.get_by_token_hash(self.tokens.hash(raw_token))
        if stored is not None:
            self.repository.revoke_family(stored.family_id)

    @staticmethod
    def _is_expired(refresh_token: RefreshToken) -> bool:
        expires_at = refresh_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at < datetime.now(timezone.utc)
