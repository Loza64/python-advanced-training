from app.models.user import User
from app.schemas.user import ProfileResponse, UserResponse


class UserMapper:
    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    @staticmethod
    def to_responses(users: list[User]) -> list[UserResponse]:
        return [UserMapper.to_response(user) for user in users]

    @staticmethod
    def to_profile_response(user: User) -> ProfileResponse:
        """Para GET /auth/me: sin campos de auditoría, a diferencia de to_response()."""
        return ProfileResponse.model_validate(user)
