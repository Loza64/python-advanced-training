from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import ProfileResponse


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    surname: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refreshToken: str


class AuthResponse(BaseModel):
    token: str
    refreshToken: str
    data: ProfileResponse
