# Products API

API REST para gestión de productos y categorías con autenticación JWT y control de acceso por roles y permisos (RBAC). Construida con FastAPI, SQLAlchemy, PostgreSQL, Alembic y Pydantic.

Este proyecto es un monolito modular con **arquitectura hexagonal** (puertos y adaptadores): la lógica de negocio vive en servicios que dependen de puertos (interfaces), y la base de datos, el hash de contraseñas, los JWT y HTTP son adaptadores que se conectan a esos puertos desde una única raíz de composición.

## Arquitectura actual

```text
app/
  adapters/
    security.py             Adaptadores de salida: BcryptPasswordHasher, JwtAccessTokenProvider, Sha256OpaqueTokenProvider
  api/
    auth_deps.py            Autenticación y RBAC: get_current_user, require_permissions
    deps.py                 Raíz de composición: conecta adaptadores, repositorios y servicios
    v1/
      auth.py               Signup, login, refresh, logout, me
      categories.py         Router de categorías
      permissions.py        Router de permisos
      products.py           Router de productos
      roles.py              Router de roles
      users.py              Router de usuarios
  core/
    config.py               Configuración y variables de entorno
    constants.py            Nombres de los roles de sistema
    exceptions.py           Errores de dominio y negocio
    logging.py              Logging compartido
    permissions.py          Constantes de permisos (UPDATE_PRODUCT, ...) y sus títulos
    ports/
      repositories.py       Puertos de salida: un Protocol por repositorio
      security.py           Puertos de salida: PasswordHasherPort, AccessTokenPort, OpaqueTokenPort
    relations.py            Tipo Relations y constantes (USER_WITH_PERMISSIONS)
  db/
    base.py                 Base declarativa, BaseEntity y borrado lógico
    seed.py                 Seeders: permisos, roles de sistema y super_admin
    session.py              Engine y sesión de la base de datos
  middleware/
    product_category.py     Intercepta POST/PUT de productos y delega en ProductCategoryService
    request_logging.py      Logging de requests
  models/
    associations.py         Tabla intermedia role_permissions
    category.py             Entidad Category
    permission.py           Entidad Permission
    product.py              Entidad Product
    refresh_token.py        Entidad RefreshToken
    role.py                 Entidad Role
    user.py                 Entidad User (permission_names, has_permissions)
  mappers/
    auth_mapper.py          AuthResult -> AuthResponse
    category_mapper.py
    permission_mapper.py
    product_mapper.py
    role_mapper.py
    user_mapper.py
  repositories/
    category_repository.py
    permission_repository.py
    product_repository.py
    refresh_token_repository.py
    relations.py            apply_relations: traduce relations a opciones de SQLAlchemy
    role_repository.py
    sorting.py              apply_sort: ordenamiento reutilizable
    user_repository.py
  schemas/
    audit.py                Campos de auditoría compartidos (createdAt, updatedAt, deletedAt)
    auth.py
    category.py
    pagination.py
    permission.py
    product.py
    role.py
    user.py
  services/
    auth_service.py         Casos de uso de autenticación: signup, login, refresh, logout, usuario desde token
    category_service.py
    permission_service.py
    product_category_service.py   Validación de relación producto-categoría
    product_service.py
    refresh_token_service.py   Entidad RefreshToken: emitir, validar, rotar, revocar
    role_service.py
    user_service.py
  main.py                   Aplicación FastAPI y manejo global de errores
alembic/
  versions/
  env.py
  script.py.mako

docs/
  engineering-standards.md

tests/
  test_health.py
  test_business_rules.py
  test_auth_services.py     AuthService y RefreshTokenService con puertos falsos, sin base de datos
  test_architecture.py      Verifica la regla de dependencias de la arquitectura hexagonal
  test_cors.py              Preflight y orígenes permitidos de CORS
```

## Arquitectura hexagonal

```text
                     ┌──────────────── ADAPTADORES DE ENTRADA ────────────────┐
                     │  api/v1/*  ·  api/auth_deps.py  ·  middleware/  ·  seed │
                     └───────────────────────────┬────────────────────────────┘
                                                 │ llaman
                     ┌───────────────────────────▼────────────────────────────┐
                     │                    NÚCLEO (hexágono)                    │
                     │  services/   casos de uso y reglas de negocio           │
                     │  models/ schemas/ mappers/   entidades y DTOs           │
                     │  core/exceptions · permissions · constants · ports/     │
                     └───────────────────────────▲────────────────────────────┘
                                                 │ implementan los puertos
                     ┌───────────────────────────┴────────────────────────────┐
                     │                ADAPTADORES DE SALIDA                    │
                     │  repositories/ (SQLAlchemy)  ·  adapters/ (bcrypt, JWT) │
                     └─────────────────────────────────────────────────────────┘
```

Las dependencias siempre apuntan hacia el núcleo. Un servicio nunca importa un adaptador: pide un puerto en su constructor, y `api/deps.py` (la raíz de composición) le entrega la implementación concreta.

| Puerto (`core/ports/`)           | Lo que ofrece al núcleo                    | Adaptador                                          |
|----------------------------------|--------------------------------------------|----------------------------------------------------|
| `*RepositoryPort/Protocol`       | Acceso a datos de cada entidad             | `repositories/*_repository.py` (SQLAlchemy)        |
| `PasswordHasherPort`             | `hash`, `verify`                           | `BcryptPasswordHasher`                             |
| `AccessTokenPort`                | `create`, `decode` (JWT de acceso)         | `JwtAccessTokenProvider`                           |
| `OpaqueTokenPort`                | `generate`, `hash` (refresh token)         | `Sha256OpaqueTokenProvider`                        |

**Reglas de dependencia**

- `services/` y `core/` no importan `sqlalchemy`, `passlib`, `jwt`, `fastapi` ni `starlette`.
- `services/` y `core/` no importan `repositories/`, `adapters/`, `api/`, `db/` ni `app.core.config`. La configuración (TTL del refresh token, secreto del JWT, datos del super_admin) entra por parámetros del constructor o del método.
- Los routers (`api/v1/*`, `api/auth_deps.py`) solo hablan con servicios. Solo `api/deps.py` conoce repositorios y adaptadores.
- Los modelos SQLAlchemy y `fastapi_pagination` (`Page`, `Params`) son la excepción práctica: se consideran parte del núcleo.

`tests/test_architecture.py` verifica estas reglas leyendo los `import` de cada archivo, así que romperlas hace fallar la suite.

**Un servicio por entidad**

| Entidad        | Servicio                | Responsabilidad                                                  |
|----------------|-------------------------|------------------------------------------------------------------|
| `User`         | `UserService`           | CRUD, unicidad de username/email, rol único de super_admin       |
| `Role`         | `RoleService`           | CRUD, roles de sistema protegidos, asignación de permisos        |
| `Permission`   | `PermissionService`     | Consulta, edición del título y siembra                           |
| `RefreshToken` | `RefreshTokenService`   | Emitir, validar, marcar como usado, revocar la familia           |
| `Category`     | `CategoryService`       | CRUD y nombre único                                              |
| `Product`      | `ProductService`        | CRUD y validación de la categoría                                |

`AuthService` no es una entidad: es un caso de uso que **orquesta** a `UserService`, `RefreshTokenService`, `PasswordHasherPort` y `AccessTokenPort` para hacer signup, login, refresh, logout y resolver el usuario de un access token.

## Principios aplicados

El proyecto mantiene una separación clara entre capas:

- Los routers solo manejan HTTP y delegan la lógica al servicio.
- Los servicios contienen la lógica de negocio y validaciones del dominio. Cada entidad tiene su propio servicio, y los casos de uso que combinan varias (como `AuthService`) orquestan a esos servicios.
- Los repositorios encapsulan SQLAlchemy y acceso a datos. Solo hacen `flush()`; el `commit` lo hace `get_db` una vez por request. Sus lecturas aceptan un parámetro `relations` para elegir qué relaciones cargar.
- Los mappers convierten entre modelos ORM y schemas Pydantic. El router mapea, el servicio devuelve modelos.
- Los errores de negocio se centralizan en `app/core/exceptions.py` y `main.py` los traduce a códigos HTTP.
- Los permisos son constantes en `app/core/permissions.py`; no se escriben strings sueltos en los routers.
- La base no se crea con `create_all()` al arrancar ni se modifica manualmente; todo se gestiona con Alembic.
- La inyección de dependencias se hace mediante `Depends`.

## Estándar de diseño

La política del proyecto está documentada en [docs/engineering-standards.md](docs/engineering-standards.md). Se aplican estas reglas:

- Los routers no hacen persistencia directa.
- Los servicios no dependen de SQLAlchemy ni de bcrypt/JWT: dependen de los puertos de `core/ports/`.
- Los repositorios no conocen HTTP ni request/response.
- Las migraciones son obligatorias para cambios de esquema.
- Los cambios funcionales deben ir acompañados de pruebas.
- La configuración vive en variables de entorno.

## Requisitos

- Python 3.11 o superior
- PostgreSQL disponible localmente o en un servidor accesible
- Docker y Docker Compose para ejecutar el entorno en contenedor
- Entorno virtual del proyecto

## Instalación local

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para desarrollo y testing:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Configuración del entorno

Crea un archivo `.env` con una configuración similar a esta:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/python
PROJECT_NAME=Products API
API_V1_PREFIX=/api/v1
ENVIRONMENT=development
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
LOG_LEVEL=INFO

# Orígenes del frontend permitidos por CORS, separados por coma
CORS_ORIGINS=http://localhost:5173,http://localhost:4200

# Autenticación JWT
JWT_SECRET=una-clave-larga-y-aleatoria
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Super admin único, sembrado automáticamente al arrancar la app
SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=CambiaEstaClave123!
SUPER_ADMIN_EMAIL=superadmin@tudominio.com
SUPER_ADMIN_NAME=Super
SUPER_ADMIN_SURNAME=Admin
```

`JWT_SECRET` y `SUPER_ADMIN_PASSWORD` tienen valores por defecto pensados solo para desarrollo. Cámbialos siempre fuera de tu máquina. `CORS_ORIGINS` también trae por defecto los puertos de desarrollo de Vite y Angular: en producción reemplázalo por la URL real de tu frontend. No guardes secrets reales en el repositorio ni en el código fuente.

## Ejecutar la aplicación

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

URLs de la API:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Health live: http://127.0.0.1:8000/health/live
- Health ready: http://127.0.0.1:8000/health/ready

## CORS

La API permite peticiones desde el navegador solo a los orígenes de `CORS_ORIGINS` (una lista separada por comas, sin barra final). `CORSMiddleware` se registra en `app/main.py` como la capa más externa, así que responde el preflight `OPTIONS` sin exigir autenticación y agrega los headers CORS también a las respuestas de error.

- Métodos permitidos: `GET`, `POST`, `PUT` y `DELETE`.
- Headers permitidos: `Authorization` y `Content-Type`.
- No se usan cookies: el token viaja en el header `Authorization`, por lo que las credenciales de CORS están desactivadas.
- Un origen que no esté en la lista no recibe headers CORS, y su preflight responde `400`. El navegador lo bloquea.

Si tu frontend corre en otro puerto o dominio, agrégalo a `CORS_ORIGINS` y reinicia la app.

## Endpoints principales

Todos los endpoints de `/categories`, `/products`, `/users`, `/roles` y `/permissions` requieren `Authorization: Bearer <token>` y el permiso correspondiente (ver [Autenticación y autorización](#autenticación-y-autorización)).

### Auth

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Categories

- `GET /api/v1/categories`
- `POST /api/v1/categories`
- `GET /api/v1/categories/{category_id}`
- `PUT /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`
- `POST /api/v1/categories/{category_id}/restore`

### Products

- `GET /api/v1/products`
- `POST /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `PUT /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`
- `POST /api/v1/products/{product_id}/restore`

### Users

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/restore`

El rol se envía como referencia, igual que `category` en los productos:

```json
{
  "username": "ana",
  "name": "Ana",
  "surname": "López",
  "email": "ana@example.com",
  "password": "password123",
  "role": { "id": 2 }
}
```

- `role` es opcional. Si el `id` no existe responde `404`; si no es un entero mayor que 0 o no viene como objeto (`"role": 2`), responde `422`.
- En `PUT /users/{id}` todos los campos son opcionales. Omitir `role` (o enviar `null`) deja el rol como está: la API no permite quitarle el rol a un usuario.
- La respuesta devuelve `role` sin sus permisos (`id`, `name`, `active` y campos de auditoría), tanto en el listado como en el detalle. Para ver los permisos de un rol usa `GET /roles/{id}`.
- Ya no se acepta `role_id`: si un cliente lo envía, se ignora y el usuario queda sin rol.

### Roles

- `GET /api/v1/roles` (lista completa, sin paginar y sin `permissions`)
- `POST /api/v1/roles`
- `GET /api/v1/roles/{role_id}` (incluye `permissions`)
- `PUT /api/v1/roles/{role_id}`
- `DELETE /api/v1/roles/{role_id}`
- `POST /api/v1/roles/{role_id}/restore`

### Permissions

Los permisos no se crean ni se eliminan por la API: los define el código y los siembra el seed. Solo se puede editar su `title`.

- `GET /api/v1/permissions`
- `GET /api/v1/permissions/{permission_id}`
- `PUT /api/v1/permissions/{permission_id}`

Los listados de categorías, productos y usuarios soportan paginación (`page`, `size`), búsqueda (`search`) y ordenamiento (`sort=campo,asc|desc`, repetible).

## Autenticación y autorización

### Flujo

- `signup`, `login` y `refresh` responden `{ "token", "refreshToken", "data" }`. `data` es un objeto con `id`, `username`, `name`, `surname`, `email`, `role` (nombre del rol o `null`) y `permissions`:

  ```json
  {
    "token": "eyJhbGciOi...",
    "refreshToken": "eYpeKRDFdCnum-...",
    "data": {
      "id": 1,
      "username": "superadmin",
      "name": "Super",
      "surname": "Admin",
      "email": "superadmin@tudominio.com",
      "role": "super_admin",
      "permissions": ["users:list", "users:read", "products:list", "..."]
    }
  }
  ```

- El **access token** es un JWT firmado con `JWT_SECRET`. Solo lleva `sub` (id del usuario), `iat`, `exp` y `type=access`. Dura `ACCESS_TOKEN_EXPIRE_MINUTES` (15 por defecto).
- El **refresh token** es un string aleatorio opaco. En base de datos solo se guarda su hash SHA-256. Dura `REFRESH_TOKEN_EXPIRE_DAYS` (7 por defecto).
- `POST /auth/refresh` **rota** el refresh token: marca el recibido como usado y emite uno nuevo dentro de la misma familia (`family_id`).
- Si se vuelve a presentar un refresh token ya usado, se revoca toda la familia y se responde `401`. Esa revocación se confirma (`commit`) antes de devolver el error, para que no se pierda con el rollback del request.
- `POST /auth/logout` revoca la familia completa del refresh token recibido.
- Un usuario bloqueado (`blocked = true`) recibe `403` en login, refresh y en cualquier request con un token válido.
- `signup` crea el usuario **sin rol**, así que no tiene permisos hasta que un administrador le asigne uno con `PUT /users/{id}` enviando `{ "role": { "id": 2 } }`.

### Autorización por permisos (RBAC)

Los permisos no viajan en el token: se resuelven en cada request a partir del rol actual del usuario. Cambiar el rol de un usuario, o desactivar el rol, tiene efecto inmediato. Un usuario sin rol, o con un rol inactivo, no tiene ningún permiso.

Cada endpoint declara qué permiso exige:

```python
from app.api.auth_deps import require_permissions
from app.core.permissions import UPDATE_PRODUCT

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_permissions(UPDATE_PRODUCT))],
)
def update_product(...):
    ...
```

`require_permissions` acepta varios permisos y exige **todos**. Si falta alguno responde `403 Not enough permissions`.

El esquema de seguridad es `HTTPBearer`. En Swagger, ejecuta `POST /auth/login`, copia el `token` de la respuesta y pégalo en el botón **Authorize**.

Los permisos siguen la forma `recurso:acción` (`products:update`), pero en el código siempre se usan mediante su constante:

| Recurso     | Constantes                                                                                         |
|-------------|----------------------------------------------------------------------------------------------------|
| Users       | `LIST_USERS`, `READ_USER`, `CREATE_USER`, `UPDATE_USER`, `DELETE_USER`                             |
| Roles       | `LIST_ROLES`, `READ_ROLE`, `CREATE_ROLE`, `UPDATE_ROLE`, `DELETE_ROLE`                             |
| Permissions | `LIST_PERMISSIONS`, `READ_PERMISSION`, `UPDATE_PERMISSION`                                         |
| Products    | `LIST_PRODUCTS`, `READ_PRODUCT`, `CREATE_PRODUCT`, `UPDATE_PRODUCT`, `DELETE_PRODUCT`              |
| Categories  | `LIST_CATEGORIES`, `READ_CATEGORY`, `CREATE_CATEGORY`, `UPDATE_CATEGORY`, `DELETE_CATEGORY`        |

Los endpoints `POST /{id}/restore` usan el permiso `DELETE_*` del recurso.

### Dónde vive cada pieza

| Pieza                                            | Archivo                                |
|--------------------------------------------------|----------------------------------------|
| Puertos de seguridad                             | `app/core/ports/security.py`           |
| Bcrypt, JWT y token opaco (adaptadores)          | `app/adapters/security.py`             |
| Constantes y títulos de permisos                 | `app/core/permissions.py`              |
| Nombres de roles de sistema                      | `app/core/constants.py`                |
| `get_current_user`, `require_permissions`        | `app/api/auth_deps.py`                 |
| Carga de rol y permisos (`USER_WITH_PERMISSIONS`) | `app/core/relations.py`               |
| Signup, login, refresh, logout, usuario desde token | `app/services/auth_service.py`      |
| Ciclo de vida del refresh token                  | `app/services/refresh_token_service.py` |
| Conexión de puertos con adaptadores              | `app/api/deps.py`                      |
| Armado de la respuesta de auth                   | `app/mappers/auth_mapper.py`           |
| Permisos efectivos de un usuario                 | `User.permission_names` / `has_permissions()` en `app/models/user.py` |
| Siembra de permisos, roles y super_admin         | `app/db/seed.py`                       |

## Carga de relaciones (estilo TypeORM)

Las relaciones **no se cargan por defecto**. Cada consulta del repositorio decide cuáles traer con el parámetro `relations`, igual que `relations: { role: { permissions: true } }` en TypeORM:

```python
user = user_repository.get_by_id(1, relations={"role": {"permissions": True}})
page = user_repository.list(params, sort, search, relations={"role": True})
```

`apply_relations` (en `app/repositories/relations.py`) traduce ese diccionario a las opciones de carga de SQLAlchemy: `joinedload` para relaciones a un solo registro (`User.role`) y `selectinload` para colecciones (`Role.permissions`). Un diccionario anidado carga niveles más profundos, y `False` u omitir la clave significa no cargarla. Si el nombre no es una relación del modelo, lanza `ValueError`.

Cada servicio elige las relaciones según el caso de uso, y el schema de respuesta decide qué se muestra:

| Endpoint                                   | `relations`                       | Respuesta                                    |
|--------------------------------------------|-----------------------------------|----------------------------------------------|
| `GET /roles`                               | ninguna                           | `RoleSummaryResponse`, sin `permissions`     |
| `GET /roles/{id}`                          | `{"permissions": True}`           | `RoleResponse`, con `permissions`            |
| `POST/PUT /roles`, `POST /roles/{id}/restore` | carga bajo demanda             | `RoleResponse`, con `permissions`            |
| `GET /users` y `GET /users/{id}`           | `{"role": True}`                  | `role` como `RoleSummaryResponse`, sin permisos |
| `GET /auth/me`                             | `USER_WITH_PERMISSIONS`           | `ProfileResponse`, con `role.permissions`    |
| `get_current_user`, login y refresh        | `USER_WITH_PERMISSIONS`           | (uso interno para calcular permisos)         |

`USER_WITH_PERMISSIONS` es `{"role": {"permissions": True}}`.

Los dos van juntos: `relations` controla qué se consulta y el schema controla qué se devuelve. Si un schema lee una relación que no se cargó, SQLAlchemy la carga en ese momento con una consulta extra por registro. En listados, pasa siempre `relations` para evitar ese problema de N+1.

## Reglas de negocio actuales

Se implementó validación en la capa de servicio:

- no se permite crear ni actualizar una categoría con un nombre duplicado
- un producto solo puede asociarse a una categoría existente (validado por `ProductCategoryService`, que invoca el middleware `product_category.py` antes de llegar al router)
- no se permite repetir `username` ni `email` de usuario
- no se permite repetir el nombre de un rol
- solo puede existir un usuario con el rol `super_admin`
- los errores de dominio se traducen a códigos HTTP consistentes: `404` no encontrado, `409` duplicado, `401` credenciales o token inválidos, `403` sin permiso o protegido

## Roles y permisos por defecto

Al arrancar la app (`app/main.py` → `run_seed`), se siembran automáticamente:

- **Todos los permisos** definidos en `app/core/permissions.py`.
- **3 roles de sistema** (protegidos: no se pueden borrar ni renombrar vía API):
  - `super_admin`: todos los permisos, y se resincroniza en cada arranque para incluir los que se agreguen después. Solo puede existir **un** usuario con este rol; la API rechaza crear o reasignar un segundo con `409 Conflict`. El rol no se puede modificar ni desactivar por la API.
  - `admin`: `list/read/create/update/delete` sobre **usuarios, productos y categorías**. Sin acceso a roles ni permisos.
  - `client`: solo lectura de productos y categorías (`products:list/read`, `categories:list/read`).
- **1 usuario `super_admin` inicial**, con los datos definidos en `SUPER_ADMIN_USERNAME` / `SUPER_ADMIN_PASSWORD` / `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_NAME` / `SUPER_ADMIN_SURNAME` del `.env`. Si ya existe un usuario con ese username o email, el seed no crea nada y solo deja un warning en el log.

Todo el proceso es idempotente: reiniciar la app no duplica roles, permisos ni usuarios.

**Importante:** el seed crea los permisos nuevos y se los da a `super_admin` automáticamente, pero **los permisos de `admin` y `client` solo se asignan cuando el rol se crea por primera vez**. Si agregas permisos nuevos a `ROLE_PERMISSIONS` en una base que ya existe, esos roles no los recibirán solos: asígnalos con `PUT /api/v1/roles/{id}` enviando `permission_ids`.

## Borrado lógico (soft delete)

`Category`, `Product`, `Role` y `User` tienen una columna `deleted_at` (nula por defecto). `Permission` no se borra por diseño y `RefreshToken` usa su propio mecanismo de revocación, así que ninguno de los dos tiene `deleted_at`.

- `DELETE` en la API no borra la fila: pone `deleted_at = now()`.
- Todas las lecturas normales (`list`, `get`, `get_by_name`, `get_by_username`, `get_by_email`) filtran `deleted_at IS NULL`, así que un registro borrado deja de aparecer en listados y búsquedas, y un `GET /{id}` sobre él responde `404` como si no existiera.
- `POST /{id}/restore` vuelve a poner `deleted_at = NULL`. Responde `404` si el registro no existe o si no estaba borrado. Exige el permiso `DELETE_*` del recurso.
- El usuario con rol `super_admin` **nunca se puede eliminar**: `UserService.delete` devuelve `403 Forbidden` si el usuario tiene ese rol.
- Los roles de sistema (`super_admin`, `admin`, `client`) tampoco se pueden eliminar.

**Limitación conocida:** el borrado lógico se aplica a las consultas que pasan por el repositorio, pero no a las relaciones de SQLAlchemy cargadas directamente (por ejemplo, `User.role` o `Product.category`). Si algún día borras lógicamente un rol o una categoría que sigue referenciada, un usuario/producto existente podría seguir "viendo" ese registro a través de la relación aunque el repositorio ya no lo liste. No es un problema hoy porque los roles de sistema no se pueden borrar, pero es algo a tener en cuenta si agregas roles o categorías personalizadas y las borras.

## Base de datos y migraciones

Se usa Alembic para schema management. La regla del proyecto es simple: **ningún cambio de esquema se hace a mano en Postgres, todo pasa por una migración**.

### Consultar estado

```powershell
alembic current
```

Muestra la revisión aplicada actualmente en la base. Si no imprime nada, la base está "en blanco" (sin migraciones aplicadas).

### Primera vez / base de datos nueva

Si acabas de crear la base de datos (o la borraste y la recreaste), aplica todo el historial existente antes de tocar nada más:

```powershell
alembic upgrade head
```

Esto ejecuta en orden todas las migraciones de `alembic/versions/` hasta dejar la base al día. Confirma con `alembic current`.

### Cuando se agrega, quita o modifica algo en una entidad existente

Este es el flujo normal del día a día: cambiaste un modelo (agregaste una columna, quitaste un campo, cambiaste un tipo de dato, agregaste una relación, etc.) y necesitas reflejar ese cambio en Postgres.

1. Edita el modelo en `app/models/` (agrega/quita/renombra la columna, cambia el tipo, etc.).
2. Verifica que el modelo esté importado en `app/models/__init__.py`. Si Alembic no lo ve, no lo detecta en el diff.
3. Confirma que tu base local esté al día antes de generar nada:

   ```powershell
   alembic current
   ```

   Debe coincidir con el `head`. Si no coincide, corre `alembic upgrade head` primero (autogenerate se niega a correr sobre una base desincronizada).

4. Genera la migración automáticamente, con un mensaje descriptivo del cambio real:

   ```powershell
   alembic revision --autogenerate -m "add sku column to products"
   ```

5. **Abre el archivo generado en `alembic/versions/` y revísalo antes de aplicarlo.** Autogenerate detecta bien tablas y columnas nuevas, pero no siempre detecta:
   - renombrados de columna (los interpreta como "borrar una columna + crear otra", perdiendo los datos existentes; si renombraste, edita el script a mano para usar `op.alter_column(..., new_column_name=...)`)
   - cambios en `server_default`
   - algunos `CHECK constraints`
6. Aplica la migración:

   ```powershell
   alembic upgrade head
   ```

7. Si algo salió mal y quieres deshacer la última migración:

   ```powershell
   alembic downgrade -1
   ```

### Ejemplo real de este proyecto

Así se agregaron las tablas de autenticación (`users`, `roles`, `permissions`, `refresh_tokens`, `role_permissions`) después de que la migración inicial solo cubría `categories` y `products`:

```powershell
alembic current
alembic upgrade head
alembic revision --autogenerate -m "add auth tables"
alembic upgrade head
```

### Errores comunes

- **`Target database is not up to date`** al hacer `--autogenerate`: la base no está en `head`. Corre `alembic upgrade head` primero.
- **`relation "X" already exists`** al hacer `upgrade head`: la tabla ya existe físicamente pero Alembic no lo sabe (la tabla `alembic_version` está vacía o no coincide). No vuelvas a correr el `CREATE TABLE`: usa `alembic stamp <revision_id>` para decirle a Alembic en qué revisión está realmente la base, sin ejecutar SQL, pero solo si verificaste que las columnas existentes coinciden exactamente con las que define esa migración.

## Cómo agregar un nuevo dominio (ejemplo: Provider)

Esta guía crea el dominio **Provider** (`/api/v1/providers`) con CRUD completo, paginación, búsqueda, ordenamiento, borrado lógico con restore y permisos. Para cualquier otro dominio (`Brand`, `Warehouse`, `Customer`...) el proceso es el mismo: cambia el nombre y los campos.

El flujo respeta el orden de capas del proyecto: **model → migración → schema → mapper → errores → port → repository → service → permisos → deps → router → registro → seed → tests**.

Provider tendrá: `name` (obligatorio, único, sin importar mayúsculas), `email` (opcional) y `phone` (opcional).

| # | Paso                     | Archivo                                      |
|---|--------------------------|----------------------------------------------|
| 1 | Modelo                   | `app/models/provider.py` + `models/__init__.py` |
| 2 | Migración                | `alembic/versions/`                          |
| 3 | Schemas                  | `app/schemas/provider.py`                    |
| 4 | Mapper                   | `app/mappers/provider_mapper.py`             |
| 5 | Errores de dominio       | `app/core/exceptions.py`                     |
| 6 | Port del repositorio     | `app/core/ports/repositories.py` + `core/ports/__init__.py` |
| 7 | Repositorio              | `app/repositories/provider_repository.py`    |
| 8 | Servicio                 | `app/services/provider_service.py`           |
| 9 | Permisos                 | `app/core/permissions.py`                    |
| 10 | Inyección de dependencias | `app/api/deps.py`                          |
| 11 | Router                  | `app/api/v1/providers.py`                    |
| 12 | Registro en la app      | `app/main.py`                                |
| 13 | Permisos por rol (seed) | `app/db/seed.py`                             |
| 14 | Exports `__init__.py`   | models, repositories, schemas, services, mappers |
| 15 | Tests                   | `tests/test_provider_service.py`             |

### 1. Modelo

`app/models/provider.py`. Heredar de `BaseEntity` te da `id`, `created_at`, `updated_at` y `deleted_at`.

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseEntity


class Provider(BaseEntity):
    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
```

Regístralo en `app/models/__init__.py`. **Sin este import Alembic no detecta la tabla.**

```python
from app.models.provider import Provider

__all__ = [..., "Provider"]
```

### 2. Migración

```powershell
alembic current
alembic upgrade head
alembic revision --autogenerate -m "add providers table"
```

Revisa el archivo generado en `alembic/versions/`. Debe crear la tabla `providers` con sus columnas y el índice único sobre `name`, y el `downgrade` debe borrarlos. Luego aplícala:

```powershell
alembic upgrade head
```

### 3. Schemas

`app/schemas/provider.py`. Las respuestas heredan `AuditFieldsMixin` para exponer `createdAt`, `updatedAt` y `deletedAt`.

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.audit import AuditFieldsMixin


class ProviderBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(ProviderBase):
    pass


class ProviderResponse(ProviderBase, AuditFieldsMixin):
    model_config = ConfigDict(from_attributes=True)

    id: int
```

### 4. Mapper

`app/mappers/provider_mapper.py`

```python
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderResponse


class ProviderMapper:
    @staticmethod
    def to_model(data: ProviderCreate) -> Provider:
        return Provider(**data.model_dump())

    @staticmethod
    def to_response(provider: Provider) -> ProviderResponse:
        return ProviderResponse.model_validate(provider)

    @staticmethod
    def to_responses(providers: list[Provider]) -> list[ProviderResponse]:
        return [ProviderMapper.to_response(provider) for provider in providers]
```

### 5. Errores de dominio

Agrega en `app/core/exceptions.py`. Heredar de `DomainError` es lo que permite a `main.py` traducirlos a HTTP.

```python
class ProviderNotFoundError(DomainError):
    def __init__(self, provider_id: int) -> None:
        self.provider_id = provider_id
        super().__init__(f"Provider {provider_id} not found")


class DuplicateProviderNameError(DomainError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Provider '{name}' already exists")
```

### 6. Port del repositorio

Agrega en `app/core/ports/repositories.py` (junto con `from app.models.provider import Provider`) y expórtalo en `app/core/ports/__init__.py`. El servicio depende de este Protocol, no de SQLAlchemy.

```python
class ProviderRepositoryPort(Protocol):
    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Provider]: ...
    def get(self, provider_id: int) -> Optional[Provider]: ...
    def get_by_name(self, name: str) -> Optional[Provider]: ...
    def add(self, provider: Provider) -> Provider: ...
    def save(self, provider: Provider) -> Provider: ...
    def delete(self, provider: Provider) -> None: ...
    def restore(self, provider_id: int) -> Optional[Provider]: ...
```

### 7. Repositorio

`app/repositories/provider_repository.py`. Todas las lecturas filtran `deleted_at IS NULL`; `restore` es la única que puede ver un registro borrado. Solo hace `flush()`, nunca `commit()`.

```python
from datetime import datetime, timezone

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.provider import Provider
from app.repositories.sorting import apply_sort


class ProviderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Provider]:
        query = select(Provider).where(Provider.deleted_at.is_(None))
        if search:
            pattern = f"%{search}%"
            query = query.where(or_(Provider.name.ilike(pattern), Provider.email.ilike(pattern)))
        if sort:
            query = apply_sort(query, Provider, sort, {"id", "name", "email", "phone"})
        else:
            query = query.order_by(Provider.id)
        return paginate(self.session, query, params)

    def get(self, provider_id: int) -> Provider | None:
        return self.session.scalar(
            select(Provider).where(Provider.id == provider_id, Provider.deleted_at.is_(None))
        )

    def get_by_name(self, name: str) -> Provider | None:
        return self.session.scalar(
            select(Provider).where(Provider.name.ilike(name), Provider.deleted_at.is_(None))
        )

    def add(self, provider: Provider) -> Provider:
        self.session.add(provider)
        self.session.flush()
        self.session.refresh(provider)
        return provider

    def save(self, provider: Provider) -> Provider:
        self.session.flush()
        self.session.refresh(provider)
        return provider

    def delete(self, provider: Provider) -> None:
        provider.deleted_at = datetime.now(timezone.utc)
        self.session.flush()

    def restore(self, provider_id: int) -> Provider | None:
        provider = self.session.scalar(select(Provider).where(Provider.id == provider_id))
        if provider is None or provider.deleted_at is None:
            return None
        provider.deleted_at = None
        self.session.flush()
        self.session.refresh(provider)
        return provider
```

`apply_sort` solo acepta los campos que le pases en el set: es la lista blanca de columnas ordenables.

### 8. Servicio

`app/services/provider_service.py`. Aquí van las reglas de negocio; no hay nada de HTTP ni de SQLAlchemy.

```python
from fastapi_pagination import Page, Params

from app.core.exceptions import DuplicateProviderNameError, ProviderNotFoundError
from app.core.ports import ProviderRepositoryPort
from app.mappers.provider_mapper import ProviderMapper
from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderUpdate


class ProviderService:
    def __init__(self, repository: ProviderRepositoryPort) -> None:
        self.repository = repository

    def list(self, params: Params, sort: list[str] | None, search: str | None) -> Page[Provider]:
        return self.repository.list(params, sort, search)

    def get(self, provider_id: int) -> Provider:
        provider = self.repository.get(provider_id)
        if provider is None:
            raise ProviderNotFoundError(provider_id)
        return provider

    def create(self, data: ProviderCreate) -> Provider:
        if self.repository.get_by_name(data.name.strip()) is not None:
            raise DuplicateProviderNameError(data.name)
        return self.repository.add(ProviderMapper.to_model(data))

    def update(self, provider_id: int, data: ProviderUpdate) -> Provider:
        provider = self.get(provider_id)

        candidate_name = data.name.strip()
        if candidate_name.lower() != provider.name.lower():
            existing = self.repository.get_by_name(candidate_name)
            if existing is not None and existing.id != provider_id:
                raise DuplicateProviderNameError(candidate_name)

        for field, value in data.model_dump().items():
            setattr(provider, field, value)
        return self.repository.save(provider)

    def delete(self, provider_id: int) -> None:
        self.repository.delete(self.get(provider_id))

    def restore(self, provider_id: int) -> Provider:
        provider = self.repository.restore(provider_id)
        if provider is None:
            raise ProviderNotFoundError(provider_id)
        return provider
```

### 9. Permisos

En `app/core/permissions.py` agrega las constantes y su título. **`PERMISSION_TITLES` es lo que el seed usa para crear los permisos en la base de datos**, así que una constante que no esté ahí nunca se sembraría.

```python
LIST_PROVIDERS = "providers:list"
READ_PROVIDER = "providers:read"
CREATE_PROVIDER = "providers:create"
UPDATE_PROVIDER = "providers:update"
DELETE_PROVIDER = "providers:delete"

PERMISSION_TITLES: dict[str, str] = {
    ...
    LIST_PROVIDERS: "Listar proveedores",
    READ_PROVIDER: "Ver detalle de un proveedor",
    CREATE_PROVIDER: "Crear proveedores",
    UPDATE_PROVIDER: "Actualizar proveedores",
    DELETE_PROVIDER: "Eliminar proveedores",
}
```

### 10. Inyección de dependencias

En `app/api/deps.py` agrega el repositorio y el servicio (más sus imports):

```python
def get_provider_repository(db: Session = Depends(get_db)) -> ProviderRepository:
    return ProviderRepository(db)


def get_provider_service(repository: ProviderRepository = Depends(get_provider_repository)) -> ProviderService:
    return ProviderService(repository)
```

### 11. Router

`app/api/v1/providers.py`. Cada endpoint declara su permiso con `require_permissions(...)`. `restore` usa el permiso de borrado.

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import StringConstraints

from app.api.auth_deps import require_permissions
from app.api.deps import get_provider_service
from app.core.permissions import (
    CREATE_PROVIDER,
    DELETE_PROVIDER,
    LIST_PROVIDERS,
    READ_PROVIDER,
    UPDATE_PROVIDER,
)
from app.mappers.provider_mapper import ProviderMapper
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.provider import ProviderCreate, ProviderResponse, ProviderUpdate
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])
SortItem = Annotated[str, StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*,(asc|desc)$")]


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(CREATE_PROVIDER))],
)
def create_provider(data: ProviderCreate, service: ProviderService = Depends(get_provider_service)):
    return ProviderMapper.to_response(service.create(data))


@router.get(
    "",
    response_model=PaginatedResponse[ProviderResponse],
    dependencies=[Depends(require_permissions(LIST_PROVIDERS))],
)
def list_providers(
    params: PaginationParams = Depends(),
    sort: list[SortItem] | None = Query(None, min_length=1, description="Usa campo,direccion. Repite sort para varios campos."),
    search: str | None = Query(None, min_length=1, description="Texto a buscar en nombre o email."),
    service: ProviderService = Depends(get_provider_service),
):
    page = service.list(params, sort, search)
    return PaginatedResponse(
        data=ProviderMapper.to_responses(page.items),
        pagination=PaginationMeta(page=page.page, pageSize=page.size, pageCount=page.pages, total=page.total),
    )


@router.get(
    "/{provider_id}",
    response_model=ProviderResponse,
    dependencies=[Depends(require_permissions(READ_PROVIDER))],
)
def get_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    return ProviderMapper.to_response(service.get(provider_id))


@router.put(
    "/{provider_id}",
    response_model=ProviderResponse,
    dependencies=[Depends(require_permissions(UPDATE_PROVIDER))],
)
def update_provider(provider_id: int, data: ProviderUpdate, service: ProviderService = Depends(get_provider_service)):
    return ProviderMapper.to_response(service.update(provider_id, data))


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(DELETE_PROVIDER))],
)
def delete_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)) -> None:
    service.delete(provider_id)


@router.post(
    "/{provider_id}/restore",
    response_model=ProviderResponse,
    dependencies=[Depends(require_permissions(DELETE_PROVIDER))],
)
def restore_provider(provider_id: int, service: ProviderService = Depends(get_provider_service)):
    return ProviderMapper.to_response(service.restore(provider_id))
```

### 12. Registro en `main.py`

Hay cuatro cambios en `app/main.py`:

```python
from app.api.v1 import auth, categories, permissions, products, providers, roles, users
from app.core.exceptions import (
    ...,
    DuplicateProviderNameError,
    ProviderNotFoundError,
    ...,
)
```

Agrega una entrada en `openapi_tags` para que aparezca agrupado en Swagger:

```python
{
    "name": "Providers",
    "description": "Create, search, sort, paginate and manage providers.",
},
```

Clasifica los errores para que respondan con el código HTTP correcto. Si olvidas este paso, responden `400` en lugar de `404` o `409`:

```python
_NOT_FOUND_ERRORS = (
    ...,
    ProviderNotFoundError,
)
_CONFLICT_ERRORS = (
    ...,
    DuplicateProviderNameError,
)
```

Y registra el router:

```python
app.include_router(providers.router, prefix=settings.api_v1_prefix)
```

### 13. Permisos por rol en el seed

En `app/db/seed.py` decide qué roles de sistema reciben los permisos nuevos. `super_admin` los recibe siempre (su valor es `None`, que significa "todos").

```python
ROLE_PERMISSIONS: dict[str, list[str] | None] = {
    SUPER_ADMIN_ROLE_NAME: None,
    ADMIN_ROLE_NAME: [
        ...,
        LIST_PROVIDERS,
        READ_PROVIDER,
        CREATE_PROVIDER,
        UPDATE_PROVIDER,
        DELETE_PROVIDER,
    ],
    CLIENT_ROLE_NAME: [
        ...,
        LIST_PROVIDERS,
        READ_PROVIDER,
    ],
}
```

Recuerda importar las constantes al inicio del archivo.

**Base de datos ya existente:** al reiniciar la app, los cinco permisos `providers:*` se crean y `super_admin` los recibe solo. Los roles `admin` y `client` **no**, porque ya existen y el seed solo les asigna permisos al crearlos. Asígnalos con `PUT /api/v1/roles/{id}` enviando los `permission_ids` completos del rol (los `id` salen de `GET /api/v1/permissions`). En una base nueva, el seed ya los deja bien.

### 14. Exports

Agrega el nuevo elemento a los `__init__.py` de `models`, `repositories`, `schemas`, `services` y `mappers`, siguiendo el estilo de los existentes. El de `models` es obligatorio (paso 1); el resto mantiene la consistencia del proyecto.

### 15. Tests

Los servicios dependen de un Protocol, así que sus reglas de negocio se prueban sin base de datos usando un repositorio falso en memoria. `tests/test_provider_service.py`:

```python
import pytest

from app.core.exceptions import DuplicateProviderNameError, ProviderNotFoundError
from app.schemas.provider import ProviderCreate
from app.services.provider_service import ProviderService


class FakeProviderRepository:
    def __init__(self) -> None:
        self.items = {}

    def get(self, provider_id):
        return self.items.get(provider_id)

    def get_by_name(self, name):
        return next((p for p in self.items.values() if p.name.lower() == name.lower()), None)

    def add(self, provider):
        provider.id = len(self.items) + 1
        self.items[provider.id] = provider
        return provider


def test_create_rejects_duplicate_name():
    service = ProviderService(FakeProviderRepository())
    service.create(ProviderCreate(name="Acme"))

    with pytest.raises(DuplicateProviderNameError):
        service.create(ProviderCreate(name="acme"))


def test_get_raises_when_provider_does_not_exist():
    service = ProviderService(FakeProviderRepository())

    with pytest.raises(ProviderNotFoundError):
        service.get(999)
```

### Verificación rápida

1. `alembic upgrade head` termina sin errores y `alembic current` muestra la nueva revisión.
2. Al arrancar la app, `GET /api/v1/permissions` lista los cinco permisos `providers:*`.
3. Con el token del `super_admin`:
   - `POST /api/v1/providers` con `{"name": "Acme", "email": "ventas@acme.com"}` responde `201`.
   - Repetir el mismo nombre (aunque cambie el uso de mayúsculas) responde `409`.
   - `GET /api/v1/providers/999` responde `404`.
   - `DELETE` responde `204`, el `GET` posterior responde `404` y `POST /{id}/restore` lo devuelve.
4. Sin token responde `401`. Con un usuario sin el permiso correspondiente responde `403`.

### Si el dominio se relaciona con otro

Por ejemplo, para que cada producto tenga un proveedor: agrega `provider_id` (con `ForeignKey("providers.id")`) y `relationship` en `Product`, y el lado inverso en `Provider`, genera una migración nueva y valida que el proveedor exista en `ProductService`, igual que hoy se valida la categoría con `ProductCategoryService`.

La convención del proyecto es que los payloads referencian la entidad relacionada como objeto, no como un `*_id` suelto: `category: { "id": 1 }` en productos y `role: { "id": 2 }` en usuarios. Para seguirla, define un schema de referencia y úsalo en el `Create`/`Update`:

```python
class ProviderReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0)
```

En el servicio, lee `data.provider.id`, verifica que exista (lanza `ProviderNotFoundError` si no) y asígnalo a `provider_id`. La respuesta sigue devolviendo el objeto completo (`ProviderResponse`).

Para cargar la relación en las consultas, usa `relations` en el repositorio: recibe `relations: Relations | None = None` y aplícalo con `apply_relations(query, Product, relations)` (de `app.repositories.relations`), como hacen `UserRepository` y `RoleRepository`. Así los listados pasan `relations={"provider": True}` y evitas consultas extra por producto.

## Testing

Ejecutar la suite:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

La suite cubre al menos:

- health checks
- reglas de negocio críticas
- validación de duplicados y categorías inexistentes
- CORS: preflight, orígenes permitidos y rechazados (`test_cors.py`)
- `AuthService` y `RefreshTokenService` (login, rotación, reuso, expiración, logout) con puertos falsos
- la regla de dependencias de la arquitectura hexagonal (`test_architecture.py`)

Al agregar un dominio nuevo, agrega sus pruebas en el mismo cambio (ver [paso 15](#15-tests)).

## Docker

Levantar el entorno con Docker Compose:

```powershell
docker compose up -d --build
```

## Archivo de estándares

- [docs/engineering-standards.md](docs/engineering-standards.md)

## Observaciones finales

La estructura actual está preparada para crecer sin mezclar responsabilidades. Si se agrega una nueva entidad al dominio, mantén exactamente el mismo flujo: model → migración → schema → mapper → repository → service → permisos → router, y regístrala en `deps.py`, `main.py` y `seed.py`. La guía de [Provider](#cómo-agregar-un-nuevo-dominio-ejemplo-provider) es la plantilla a seguir.