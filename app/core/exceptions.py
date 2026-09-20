class AppError(Exception):
    pass


class DomainError(AppError):
    pass


class CategoryNotFoundError(DomainError):
    def __init__(self, category_id: int) -> None:
        self.category_id = category_id
        super().__init__(f"Category {category_id} not found")


class DuplicateCategoryNameError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Category '{name}' already exists")


class ProductCategoryValidationError(DomainError):
    def __init__(self, message: str = "category.id must be an integer") -> None:
        super().__init__(message)


class ProductNotFoundError(DomainError):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id
        super().__init__(f"Product {product_id} not found")


class InvalidCredentialsError(AppError):
    pass


class InvalidAccessTokenError(AppError):
    pass


class InvalidRefreshTokenError(AppError):
    pass


class RefreshTokenReuseDetectedError(AppError):
    pass


class UserBlockedError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass


class UserNotFoundError(DomainError):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class UsernameAlreadyExistsError(DomainError):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Username '{username}' already exists")


class EmailAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email '{email}' already exists")


class RoleNotFoundError(DomainError):
    def __init__(self, role_id: int) -> None:
        self.role_id = role_id
        super().__init__(f"Role {role_id} not found")


class DuplicateRoleNameError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Role '{name}' already exists")


class SystemRoleProtectedError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Role '{name}' is a protected system role")


class SuperAdminAlreadyExistsError(DomainError):
    def __init__(self) -> None:
        super().__init__("A super_admin user already exists; only one is allowed")


class SuperAdminCannotBeDeletedError(DomainError):
    def __init__(self) -> None:
        super().__init__("The super_admin user can never be deleted")


class PermissionNotFoundError(DomainError):
    def __init__(self, permission_id: int) -> None:
        self.permission_id = permission_id
        super().__init__(f"Permission {permission_id} not found")
