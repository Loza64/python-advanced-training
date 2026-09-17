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

## Base de datos y migraciones

Se usa Alembic para schema management.

Generar migración:

```powershell
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe the change"
```

Aplicar migraciones:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

Consultar estado:

```powershell
.\venv\Scripts\python.exe -m alembic current
```

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
