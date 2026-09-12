# Products API

API REST construida con FastAPI, SQLAlchemy, PostgreSQL, Alembic y Pydantic.

Este proyecto usa un **monolito modular**: una sola aplicación desplegable, organizada por responsabilidades. Es una base adecuada para crecer sin introducir microservicios antes de necesitarlos.

## Arquitectura

```text
app/
	api/            HTTP, routers y dependencias de FastAPI
	core/           configuración, logging y contratos
	db/             engine, sesiones y Base de SQLAlchemy
	models/         entidades ORM: Category y Product
	schemas/        DTOs y validación Pydantic
	mappers/        conversión DTO <-> ORM
	repositories/  acceso a datos y paginación SQLAlchemy
	services/       casos de uso y reglas de negocio
alembic/          migraciones versionadas de PostgreSQL
tests/            pruebas automatizadas
```

Reglas importantes:

- Los routers no contienen lógica de persistencia.
- Los servicios dependen de contratos (`Protocol`), no de SQLAlchemy concreto.
- Los repositorios no reciben ni devuelven respuestas HTTP.
- Las tablas se modifican únicamente con Alembic.
- La aplicación nunca ejecuta `create_all()` al arrancar.

## Requisitos

- Python 3.11 o superior.
- PostgreSQL ejecutándose localmente o en un servidor accesible.
- Base de datos creada, por ejemplo `python`.
- Docker Desktop, si se ejecutará en contenedor.
- Cliente PostgreSQL (`pg_dump` y `pg_restore`) para backups.

## Inicializar el backend

Ejecuta estos comandos desde la raíz del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Qué hace cada comando:

- `python -m venv venv`: crea un entorno virtual aislado en la carpeta `venv`.
- `... -m pip install --upgrade pip`: actualiza `pip` dentro de ese entorno.
- `... -m pip install -r requirements.txt`: instala exactamente las dependencias de producción fijadas en el archivo.

Usar `...\Scripts\python.exe` garantiza que los comandos utilicen el entorno del proyecto y no el Python global del equipo.

Para instalar también las herramientas de desarrollo y testing:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Este archivo incluye `requirements.txt`, `pytest` y `httpx`. Instálalo para ejecutar tests; no es necesario incluirlo en la imagen runtime de producción.

Las versiones de producción y desarrollo están fijadas para que la instalación local, CI y Docker usen el mismo conjunto de paquetes.

## Configurar PostgreSQL

Configura `.env` con la URL de conexión:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/python
PROJECT_NAME=Products API
API_V1_PREFIX=/api/v1
ENVIRONMENT=development
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
```

No subas `.env` al repositorio si contiene credenciales reales.

Para empezar desde cero, copia `.env.example`:

```powershell
Copy-Item .env.example .env
```

Este comando copia la plantilla de configuración. Después debes editar `.env` con la URL real de PostgreSQL. El archivo `.env` está ignorado por Git porque puede contener credenciales.

En producción, carga estas variables desde el gestor de secretos de tu proveedor cloud. No las guardes en el código, en la imagen Docker ni en el repositorio.

Variables disponibles:

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | URL PostgreSQL obligatoria |
| `PROJECT_NAME` | Nombre de la API |
| `API_V1_PREFIX` | Prefijo de endpoints |
| `ENVIRONMENT` | `development`, `test` o `production` |
| `DATABASE_POOL_SIZE` | Conexiones base del pool |
| `DATABASE_MAX_OVERFLOW` | Conexiones adicionales permitidas |
| `DATABASE_POOL_TIMEOUT` | Tiempo máximo esperando conexión |
| `DATABASE_POOL_RECYCLE` | Reciclaje de conexiones en segundos |
| `LOG_LEVEL` | Nivel de logging, por ejemplo `INFO` |

## Crear o actualizar las tablas

Las tablas se administran con Alembic:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

`upgrade head` ejecuta todas las migraciones pendientes hasta la última versión registrada. Crea o modifica tablas de forma versionada y no borra datos salvo que una migración lo indique explícitamente.

Para comprobar la versión actual:

```powershell
.\venv\Scripts\python.exe -m alembic current
```

`current` muestra la revisión que tiene aplicada la base de datos conectada por `DATABASE_URL`. Sirve para verificar si la base está actualizada.

Cuando cambies los modelos SQLAlchemy, genera y aplica una migración:

```powershell
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe el cambio"
.\venv\Scripts\python.exe -m alembic upgrade head
```

- `revision --autogenerate`: compara los modelos ORM con el esquema existente y genera un archivo de migración.
- `upgrade head`: aplica esa migración a la base configurada.
- `-m`: añade un nombre descriptivo para identificar el cambio.

Alembic puede generar operaciones incorrectas o incompletas; por eso el archivo creado debe revisarse manualmente antes de ejecutar `upgrade`.

Revisa siempre la migración generada antes de aplicarla.

Nunca ejecutes `alembic downgrade` en producción sin backup, revisión y un plan de recuperación. Para datos importantes, las migraciones destructivas deben hacerse en varios pasos compatibles hacia atrás.

## Configuración de producción

Producción debe usar PostgreSQL administrado, TLS y backups automáticos del proveedor. Un ejemplo de URL con TLS es:

```env
DATABASE_URL=postgresql://app_user:password@db.example.com:5432/products?sslmode=require
ENVIRONMENT=production
```

Antes de desplegar una migración en producción:

1. Confirma que el backup automático/PITR del proveedor está activo.
2. Ejecuta un backup lógico adicional.
3. Revisa la migración generada.
4. Ejecuta `alembic upgrade head` como paso controlado del despliegue.
5. Verifica la salud de la aplicación y las tablas.

El backend no ejecuta `create_all()` al arrancar. Esto evita cambios de esquema accidentales y obliga a usar migraciones versionadas.

## Backup y restauración

Necesitas tener instalado el cliente PostgreSQL (`pg_dump`, `pg_restore`) en la máquina de despliegue o de operaciones. Con `DATABASE_URL` cargada como secreto:

```powershell
.\scripts\backup.ps1 -BackupDirectory .\backups
```

El script valida que exista `DATABASE_URL`, crea la carpeta de destino si no existe y ejecuta `pg_dump` en formato custom. `-BackupDirectory` indica dónde guardar el archivo. Haz este backup antes de migraciones o despliegues que cambien la base.

El backup se genera en formato custom. Para restaurarlo en una base de datos vacía o de recuperación:

```powershell
pg_restore --clean --if-exists --no-owner --no-privileges --dbname=$env:DATABASE_URL .\backups\products-YYYYMMDD-HHMMSS.dump
```

- `--clean`: elimina objetos existentes antes de restaurarlos.
- `--if-exists`: no falla al intentar eliminar un objeto que no existe.
- `--no-owner`: evita cambiar propietarios durante la restauración.
- `--no-privileges`: no restaura permisos del servidor original.
- `--dbname`: indica la base de datos destino.

Usa este comando únicamente sobre una base de recuperación o después de confirmar el impacto. `--clean` puede eliminar tablas existentes.

Conserva los backups fuera del servidor de la aplicación y prueba periódicamente una restauración. Un backup que nunca se restaura no debe considerarse verificado.

La protección principal en la nube debe ser: backups automáticos, retención suficiente, recuperación a un punto en el tiempo (PITR), almacenamiento redundante y permisos separados para la aplicación y las operaciones de backup.

## Ejecutar la API

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- `-m uvicorn`: ejecuta Uvicorn usando el intérprete del entorno virtual.
- `app.main:app`: carga el objeto `app` del archivo `app/main.py`.
- `--reload`: reinicia el servidor cuando detecta cambios; úsalo solo en desarrollo.

La API estará disponible en:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`

`/health/live` confirma que el proceso está vivo. `/health/ready` comprueba la conexión con PostgreSQL y debe usarse para retirar el contenedor del tráfico cuando la base de datos no está disponible.

Para un proceso de producción, sin recarga automática:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

- `--host 0.0.0.0`: permite conexiones desde fuera del contenedor o máquina local.
- `--port 8000`: expone el puerto HTTP de la API.
- `--workers 2`: inicia dos procesos para atender más tráfico. Ajusta el número según CPU y memoria.
- En producción no se usa `--reload`.

## Ejecutar con Docker

El `Dockerfile` usa dos etapas: una etapa de build con las herramientas necesarias para compilar dependencias y una imagen runtime sin compiladores. La aplicación se ejecuta con un usuario sin privilegios.

La base de datos PostgreSQL debe estar conectada a la red externa `postgres_network`. Créala una sola vez si todavía no existe:

```powershell
docker network create postgres_network
```

Crea una red Docker externa compartida. La API puede comunicarse con un contenedor PostgreSQL conectado a esa misma red. Si la red ya existe, no ejecutes el comando otra vez.

Configura `.env` con la URL de PostgreSQL accesible desde Docker y construye la imagen:

```powershell
docker compose build
```

Lee `Dockerfile`, instala las dependencias y genera la imagen multi-stage. La imagen final no contiene compiladores ni el código excluido por `.dockerignore`.

Aplica las migraciones antes de arrancar la API:

```powershell
docker compose run --rm api alembic upgrade head
```

Crea un contenedor temporal basado en la imagen y ejecuta las migraciones dentro del mismo entorno que usará la API. `--rm` elimina ese contenedor al terminar; no elimina datos de PostgreSQL.

Arranca el servicio:

```powershell
docker compose up -d
```

Crea o actualiza el contenedor de la API y lo deja ejecutándose en segundo plano. `restart: unless-stopped` permite que Docker lo reinicie después de un fallo o reinicio del host.

Consulta los logs:

```powershell
docker compose logs -f api
```

Muestra los logs del servicio `api` y `-f` mantiene la salida abierta para seguir nuevos mensajes. Pulsa `Ctrl+C` para dejar de observarlos sin detener el contenedor.

Detén el servicio sin eliminar volúmenes de PostgreSQL:

```powershell
docker compose down
```

Detiene y elimina los contenedores definidos por Compose. No elimina la base PostgreSQL externa ni sus datos.

El contenedor no ejecuta migraciones automáticamente. Esto evita que un despliegue cambie el esquema sin una acción controlada y permite hacer un backup antes de cada migración.

## Flujo completo de despliegue

En un entorno de producción:

```powershell
# 1. Construir una imagen inmutable
docker compose build

# 2. Crear backup antes de cambiar el esquema
.\scripts\backup.ps1 -BackupDirectory .\backups

# 3. Aplicar migraciones explícitamente
docker compose run --rm api alembic upgrade head

# 4. Arrancar o actualizar la API
docker compose up -d

# 5. Revisar el servicio
docker compose ps
docker compose logs --tail=100 api
```

Después verifica:

```text
GET /health/live   -> proceso activo
GET /health/ready  -> PostgreSQL accesible
```

Usa un proxy o load balancer delante de Uvicorn en producción. El proveedor cloud debe gestionar TLS público, secretos, firewall y acceso privado a PostgreSQL.

## Instalar una nueva librería

Usa siempre el Python del entorno virtual:

```powershell
.\venv\Scripts\python.exe -m pip install nombre-paquete
```

Después añade la librería a `requirements.txt` con una versión fija:

```text
nombre-paquete==1.2.3
```

Fijar la versión evita que un despliegue futuro reciba cambios inesperados.

Luego verifica que el proyecto pueda instalarse desde cero:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Reinstala el conjunto declarado y permite comprobar que una máquina limpia puede preparar el proyecto.

Para congelar todas las versiones instaladas:

```powershell
.\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

Reemplaza el archivo con todas las versiones instaladas, incluidas dependencias transitivas. Úsalo solo si el equipo quiere congelar todo el árbol; para este proyecto se mantienen las dependencias directas fijadas manualmente.

Usa `pip freeze` solo si el equipo desea mantener también las dependencias transitivas congeladas.

## Endpoints

- `GET|POST|PUT|DELETE /api/v1/categories`
- `GET|POST|PUT|DELETE /api/v1/products`

Los endpoints de colección soportan paginación:

```http
GET /api/v1/products?page=1&size=10
```

La respuesta incluye `data` y `pagination`.

Ejemplo de respuesta paginada:

```json
{
	"data": [],
	"pagination": {
		"page": 1,
		"pageSize": 10,
		"pageCount": 0,
		"total": 0
	}
}
```

## Verificaciones

```powershell
.\venv\Scripts\python.exe -m compileall -q app
.\venv\Scripts\python.exe -m alembic check
.\venv\Scripts\python.exe -m pytest
```

- `compileall`: detecta errores de sintaxis sin arrancar la API.
- `alembic check`: verifica si los modelos tienen cambios pendientes de migración.
- `pytest`: ejecuta las pruebas automatizadas.

El workflow `.github/workflows/ci.yml` ejecuta automáticamente en cada push a `main` y en cada pull request:

- compilación de Python y Alembic;
- tests automatizados;
- build de la imagen Docker.

## Checklist de producción

- [ ] PostgreSQL administrado con TLS (`sslmode=require`).
- [ ] Usuario de aplicación sin permisos de propietario de la base.
- [ ] Secretos fuera de Git, Dockerfile e imagen.
- [ ] Backups automáticos y recuperación PITR habilitados.
- [ ] Backup lógico verificado antes de migraciones.
- [ ] Restauración probada periódicamente.
- [ ] Migraciones revisadas y aplicadas como paso explícito.
- [ ] Health checks conectados al balanceador/orquestador.
- [ ] Logs enviados a un sistema centralizado.
- [ ] Imagen ejecutada como usuario no root.
- [ ] CI verde antes de desplegar.