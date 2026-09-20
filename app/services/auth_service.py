from dataclasses import dataclass

from app.core.exceptions import InvalidAccessTokenError, InvalidCredentialsError, UserBlockedError
from app.core.ports import AccessTokenPort, PasswordHasherPort
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest
from app.schemas.user import UserCreate
from app.services.refresh_token_service import RefreshTokenService
from app.services.user_service import UserService


@dataclass(frozen=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        user_service: UserService,
        refresh_token_service: RefreshTokenService,
        password_hasher: PasswordHasherPort,
        access_tokens: AccessTokenPort,
    ) -> None:
        self.user_service = user_service
        self.refresh_token_service = refresh_token_service
        self.password_hasher = password_hasher
        self.access_tokens = access_tokens

    def signup(self, payload: SignupRequest) -> AuthResult:
        user = self.user_service.create(UserCreate.model_validate(payload.model_dump()))
        return self._start_session(user)

    def login(self, payload: LoginRequest) -> AuthResult:
        user = self._authenticate(payload.username, payload.password)
        return self._start_session(user)

    def refresh(self, raw_refresh_token: str) -> AuthResult:
        stored = self.refresh_token_service.get_valid(
            raw_refresh_token,
            with_user_permissions=True,
        )

        user = stored.user
        if user.blocked:
            raise UserBlockedError("User is blocked")

        self.refresh_token_service.mark_as_used(stored)
        return self._start_session(user, family_id=stored.family_id)

    def logout(self, raw_refresh_token: str) -> None:
        self.refresh_token_service.revoke_session(raw_refresh_token)

    def get_user_from_access_token(self, access_token: str) -> User:
        user_id = self.access_tokens.decode(access_token)

        user = self.user_service.find_by_id(user_id, with_permissions=True)
        if user is None:
            raise InvalidAccessTokenError("User not found")
        if user.blocked:
            raise UserBlockedError("User is blocked")

        return user

    def _authenticate(self, username: str, password: str) -> User:
        user = self.user_service.find_by_username(username, with_permissions=True)
        if user is None or not self.password_hasher.verify(password, user.password):
            raise InvalidCredentialsError("Invalid username or password")
        if user.blocked:
            raise UserBlockedError("User is blocked")
        return user

    def _start_session(self, user: User, family_id: str | None = None) -> AuthResult:
        return AuthResult(
            user=user,
            access_token=self.access_tokens.create(user.id),
            refresh_token=self.refresh_token_service.issue(user.id, family_id),
        )
