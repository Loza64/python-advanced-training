LIST_USERS = "users:list"
READ_USER = "users:read"
CREATE_USER = "users:create"
UPDATE_USER = "users:update"
DELETE_USER = "users:delete"

LIST_ROLES = "roles:list"
READ_ROLE = "roles:read"
CREATE_ROLE = "roles:create"
UPDATE_ROLE = "roles:update"
DELETE_ROLE = "roles:delete"

LIST_PERMISSIONS = "permissions:list"
READ_PERMISSION = "permissions:read"
UPDATE_PERMISSION = "permissions:update"

LIST_PRODUCTS = "products:list"
READ_PRODUCT = "products:read"
CREATE_PRODUCT = "products:create"
UPDATE_PRODUCT = "products:update"
DELETE_PRODUCT = "products:delete"

LIST_CATEGORIES = "categories:list"
READ_CATEGORY = "categories:read"
CREATE_CATEGORY = "categories:create"
UPDATE_CATEGORY = "categories:update"
DELETE_CATEGORY = "categories:delete"

PERMISSION_TITLES: dict[str, str] = {
    LIST_USERS: "Listar usuarios",
    READ_USER: "Ver detalle de un usuario",
    CREATE_USER: "Crear usuarios",
    UPDATE_USER: "Actualizar usuarios",
    DELETE_USER: "Eliminar usuarios",
    LIST_ROLES: "Listar roles",
    READ_ROLE: "Ver detalle de un rol",
    CREATE_ROLE: "Crear roles",
    UPDATE_ROLE: "Actualizar roles",
    DELETE_ROLE: "Eliminar roles",
    LIST_PERMISSIONS: "Listar permisos",
    READ_PERMISSION: "Ver detalle de un permiso",
    UPDATE_PERMISSION: "Actualizar el titulo de un permiso",
    LIST_PRODUCTS: "Listar productos",
    READ_PRODUCT: "Ver detalle de un producto",
    CREATE_PRODUCT: "Crear productos",
    UPDATE_PRODUCT: "Actualizar productos",
    DELETE_PRODUCT: "Eliminar productos",
    LIST_CATEGORIES: "Listar categorias",
    READ_CATEGORY: "Ver detalle de una categoria",
    CREATE_CATEGORY: "Crear categorias",
    UPDATE_CATEGORY: "Actualizar categorias",
    DELETE_CATEGORY: "Eliminar categorias",
}
