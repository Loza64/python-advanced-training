from app.schemas.auth import AuthResponse
from app.schemas.user import ProfileResponse
from app.services.auth_service import AuthResult


class AuthMapper:
    @staticmethod
    def to_response(result: AuthResult) -> AuthResponse:
        data = ProfileResponse.model_validate(result.user)
        return AuthResponse(token=result.access_token, refreshToken=result.refresh_token, data=data)
