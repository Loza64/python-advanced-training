# Products API

API REST para gestión de productos y categorías, construida con FastAPI, SQLAlchemy, PostgreSQL, Alembic y Pydantic.

Este proyecto usa un monolito modular con separación clara de responsabilidades, reglas de negocio en la capa de servicios y dependencias inyectadas mediante FastAPI. La estructura actual está alineada con un estándar muy cercano al utilizado por equipos senior en Python.

## Arquitectura actual

```text
app/
  api/
    v1/
      categories.py         Router de categorías
      products.py           Router de productos
  core/
    config.py              Configuración y variables de entorno
    exceptions.py          Errores de dominio y negocio
    logging.py             Logging compartido
    ports.py               Protocols para repositorios
    sorting.py             Ordenamiento reutilizable
  db/
    base.py                Base declarativa de SQLAlchemy
    session.py             Engine y sesión de la base de datos
  middleware/
    product_category.py    Validación de categoría asociada al producto
    request_logging.py     Logging de requests
  models/
    category.py            Entidad Category
    product.py             Entidad Product
  mappers/
    category_mapper.py
    product_mapper.py
  repositories/
    category_repository.py
    product_repository.py
  schemas/
    category.py
    pagination.py
    product.py
  services/
    category_service.py    Lógica de negocio de categorías
    product_service.py     Lógica de negocio de productos
    product_category_service.py  Validación de relación producto-categoría
  main.py                  Aplicación FastAPI y manejo global de errores
alembic/
  versions/
  env.py
  script.py.mako

docs/
  engineering-standards.md

tests/
  test_health.py
  test_business_rules.py
```

## Principios aplicados

El proyecto mantiene una separación clara entre capas:

- Los routers solo manejan HTTP y delegan la lógica al servicio.
- Los servicios contienen la lógica de negocio y validaciones del dominio.
- Los repositorios encapsulan SQLAlchemy y acceso a datos.
- Los mappers convierten entre modelos ORM y schemas Pydantic.
- Los errores de negocio se centralizan en `app/core/exceptions.py`.
- La validación de categorías para productos se hace a través de un servicio dedicado y no dentro de middleware como lógica de negocio.
- La base no se crea con `create_all()` al arrancar ni se modifica manualmente; todo se gestiona con Alembic.
- La inyección de dependencias se hace mediante `Depends`.

## Estandar de diseño

La política del proyecto está documentada en [docs/engineering-standards.md](docs/engineering-standards.md). Se aplican estas reglas:

- Los routers no hacen persistencia directa.
- Los servicios no dependen de SQLAlchemy concreto.
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

# Super admin único, sembrado automáticamente al arrancar la app
SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=CambiaEstaClave123!
SUPER_ADMIN_EMAIL=superadmin@tudominio.com
SUPER_ADMIN_NAME=Super
SUPER_ADMIN_SURNAME=Admin
```

No guardes secrets reales en el repositorio ni en el código fuente.

## Ejecutar la aplicación

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

URLs de la API:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Health live: http://127.0.0.1:8000/health/live
- Health ready: http://127.0.0.1:8000/health/ready

## Endpoints principales

### Categories

- `GET /api/v1/categories`
- `POST /api/v1/categories`
- `GET /api/v1/categories/{category_id}`
- `PUT /api/v1/categories/{category_id}`
- `DELETE /api/v1/categories/{category_id}`

### Products

- `GET /api/v1/products`
- `POST /api/v1/products`
- `GET /api/v1/products/{product_id}`
- `PUT /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`

Los endpoints soportan paginación, búsqueda y ordenamiento por campos.

## Reglas de negocio actuales

Se implementó validación en la capa de servicio:

- no se permite crear ni actualizar una categoría con un nombre duplicado
- un producto solo puede asociarse a una categoría existente
- los errores de dominio se traducen a códigos HTTP consistentes
- la relación producto-categoría se valida de forma centralizada antes del flujo principal

## Roles y permisos por defecto

Al arrancar la app (`app/main.py` → `run_seed`), se siembran automáticamente:

- **3 roles de sistema** (protegidos: no se pueden borrar ni renombrar vía API):
  - `super_admin` — todos los permisos. Solo puede existir **un** usuario con este rol; la API rechaza crear o reasignar un segundo con `409 Conflict`. Sus permisos tampoco se pueden reducir ni desactivarse el rol.
  - `admin` — gestión de usuarios (`users:list/read/create/update/delete`), sin acceso a roles ni permisos.
  - `client` — sin permisos administrativos (rol base para usuarios regulares).
- **1 usuario `super_admin` inicial**, con los datos definidos en `SUPER_ADMIN_USERNAME` / `SUPER_ADMIN_PASSWORD` / `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_NAME` / `SUPER_ADMIN_SURNAME` del `.env`. Si ya existe un usuario con ese username o email, el seed no crea nada y solo deja un warning en el log.

Todo el proceso es idempotente: reiniciar la app no duplica roles, permisos ni usuarios.

## Borrado lógico (soft delete)

`Category`, `Product`, `Role` y `User` tienen una columna `deleted_at` (nula por defecto). `Permission` no se borra por diseño y `RefreshToken` usa su propio mecanismo de revocación, así que ninguno de los dos tiene `deleted_at`.

- `DELETE` en la API ya no borra la fila: pone `deleted_at = now()`.
- Todas las lecturas normales (`list`, `get`, `get_by_name`, `get_by_username`, `get_by_email`) filtran `deleted_at IS NULL`, así que un registro borrado deja de aparecer en listados y búsquedas, y un `GET /{id}` sobre él responde `404` como si no existiera.
- Cada repositorio tiene un método `restore(id)` que vuelve a poner `deleted_at = NULL`. Por ahora vive solo en repositorio/servicio — no hay endpoint `POST /.../{id}/restore` todavía; pídelo si lo quieres expuesto en la API.
- El usuario con rol `super_admin` **nunca se puede eliminar** (ni lógica ni físicamente): `UserService.delete` devuelve `403 Forbidden` si el usuario tiene ese rol.
- Los roles de sistema (`super_admin`, `admin`, `client`) tampoco se pueden eliminar (`is_system=true`), igual que antes.

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
2. Verifica que el modelo esté importado en `app/models/__init__.py` — si Alembic no lo ve, no lo detecta en el diff.
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
   - renombrados de columna (los interpreta como "borrar una columna + crear otra", perdiendo los datos existentes — si renombraste, edita el script a mano para usar `op.alter_column(..., new_column_name=...)`)
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
- **`relation "X" already exists`** al hacer `upgrade head`: la tabla ya existe físicamente pero Alembic no lo sabe (la tabla `alembic_version` está vacía o no coincide). No vuelvas a correr el `CREATE TABLE`: usa `alembic stamp <revision_id>` para decirle a Alembic en qué revisión está realmente la base, sin ejecutar SQL — pero solo si verificaste que las columnas existentes coinciden exactamente con las que define esa migración.

## Testing

Ejecutar la suite:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

La suite cubre al menos:

- health checks
- reglas de negocio críticas
- validación de duplicados y categorías inexistentes

## Docker

Levantar el entorno con Docker Compose:

```powershell
docker compose up -d --build
```

## Archivo de estándares

- [docs/engineering-standards.md](docs/engineering-standards.md)

## Observaciones finales

La estructura actual está preparada para crecer sin mezclar responsabilidades. Si se agrega una nueva entidad al dominio, se recomienda mantener exactamente el mismo flujo: model -> repository -> service -> router -> schema -> mapper.