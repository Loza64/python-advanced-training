from app.models.user import User
from app.schemas.user import UserResponse


class UserMapper:
    @staticmethod
    def to_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    @staticmethod
    def to_responses(users: list[User]) -> list[UserResponse]:
        return [UserMapper.to_response(user) for user in users]
