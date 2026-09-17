from app.models.role import Role
from app.schemas.role import RoleResponse


class RoleMapper:
    @staticmethod
    def to_response(role: Role) -> RoleResponse:
        return RoleResponse.model_validate(role)

    @staticmethod
    def to_responses(roles: list[Role]) -> list[RoleResponse]:
        return [RoleMapper.to_response(role) for role in roles]
