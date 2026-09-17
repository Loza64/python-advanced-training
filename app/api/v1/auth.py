from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_auth_service, get_current_user
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenReuseDetectedError,
    UserBlockedError,
    UsernameAlreadyExistsError,
)
from app.mappers.user_mapper import UserMapper
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, SignupRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.signup(data)
    except (UsernameAlreadyExistsError, EmailAlreadyExistsError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.login(data)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return service.refresh(data.refreshToken)
    except (InvalidRefreshTokenError, RefreshTokenReuseDetectedError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> None:
    service.logout(data.refreshToken)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserMapper.to_response(current_user)
