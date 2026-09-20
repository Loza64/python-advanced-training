from app.models.role import Role
from app.schemas.role import RoleResponse, RoleSummaryResponse


class RoleMapper:
    @staticmethod
    def to_response(role: Role) -> RoleResponse:
        return RoleResponse.model_validate(role)

    @staticmethod
    def to_summary(role: Role) -> RoleSummaryResponse:
        return RoleSummaryResponse.model_validate(role)

    @staticmethod
    def to_summaries(roles: list[Role]) -> list[RoleSummaryResponse]:
        return [RoleMapper.to_summary(role) for role in roles]
