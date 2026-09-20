from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import get_auth_service
from app.core.exceptions import InvalidAccessTokenError, PermissionDeniedError
from app.models.user import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise _credentials_error()

    try:
        return auth_service.get_user_from_access_token(credentials.credentials)
    except InvalidAccessTokenError as exc:
        raise _credentials_error() from exc


def require_permissions(*required_permissions: str) -> Callable[..., User]:
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permissions(*required_permissions):
            raise PermissionDeniedError("Not enough permissions")
        return current_user

    return checker
