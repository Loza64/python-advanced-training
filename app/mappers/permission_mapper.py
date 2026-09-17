from app.models.permission import Permission
from app.schemas.permission import PermissionResponse


class PermissionMapper:
    @staticmethod
    def to_response(permission: Permission) -> PermissionResponse:
        return PermissionResponse.model_validate(permission)

    @staticmethod
    def to_responses(permissions: list[Permission]) -> list[PermissionResponse]:
        return [PermissionMapper.to_response(permission) for permission in permissions]
