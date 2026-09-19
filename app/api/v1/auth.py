from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.mappers.user_mapper import UserMapper
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, SignupRequest
from app.schemas.user import ProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, service: AuthService = Depends(get_auth_service)):
    return service.signup(data)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return service.login(data)


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    return service.refresh(data.refreshToken)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, service: AuthService = Depends(get_auth_service)) -> None:
    service.logout(data.refreshToken)


@router.get("/me", response_model=ProfileResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserMapper.to_profile_response(current_user)
