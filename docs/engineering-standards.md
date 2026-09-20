# Estándar de arquitectura y calidad

Este proyecto sigue un estándar de arquitectura hexagonal (puertos y adaptadores) y modular para APIs Python con FastAPI. El objetivo es mantener una base fácil de escalar, testear y mantener sin mezclas de responsabilidades.

## 1. Arquitectura obligatoria

Toda funcionalidad debe respetar esta separación de capas.

**Núcleo (el hexágono): reglas de negocio y contratos**

- `services/`: reglas de negocio y casos de uso. Un servicio por entidad; los casos de uso que combinan varias entidades orquestan a esos servicios.
- `schemas/`: DTOs, validación y contratos de request/response.
- `models/`: entidades ORM. Son las entidades del dominio de este proyecto.
- `mappers/`: conversión entre modelos ORM y schemas.
- `core/`: errores de dominio (`exceptions.py`), constantes de permisos y roles, tipos compartidos y **puertos** (`core/ports/`). `config.py` y `logging.py` son la excepción: son infraestructura compartida.

**Adaptadores de entrada: quien llama al núcleo**

- `api/`: routers HTTP, `auth_deps.py` (autenticación y RBAC) y `deps.py`, que es la **raíz de composición**.
- `middleware/`: interceptores HTTP. Componen servicios, no contienen reglas de negocio.
- `db/seed.py`: siembra inicial al arrancar.

**Adaptadores de salida: quien implementa los puertos**

- `repositories/`: acceso a la base de datos y consultas (SQLAlchemy).
- `adapters/`: servicios externos al núcleo, como bcrypt, JWT y tokens opacos.
- `db/`: sesión y conexión a la base de datos.

**Soporte**

- `alembic/`: migraciones versionadas.
- `tests/`: pruebas.

Las dependencias siempre apuntan hacia el núcleo:

```text
adaptadores de entrada  ──▶  núcleo (services + puertos)  ◀──  adaptadores de salida
   api/, middleware/           services/, core/ports/           repositories/, adapters/
```

Un servicio nunca importa un adaptador: pide un puerto en su constructor, y `api/deps.py` le entrega la implementación concreta.

## 2. Reglas de diseño (obligatorias)

### 2.1. Los routers no tienen lógica de persistencia
Los endpoints deben delegar la lógica a servicios. No se deben realizar queries directas ni manipulación de ORM en los routers. Los routers solo conocen servicios: no importan repositorios, adaptadores ni `db/`. Solo `api/deps.py` los conoce.

### 2.2. Los servicios dependen de puertos, no de infraestructura
Los servicios pueden usar las entidades de `models/`, pero no dependen de SQLAlchemy concreto (`Session`, `select`, opciones de carga), ni de bcrypt, JWT, FastAPI o `app.core.config`. Todo lo externo entra por un puerto de `core/ports/`:

| Puerto                          | Adaptador                                   |
|---------------------------------|---------------------------------------------|
| `*RepositoryPort` / `*Protocol` | `repositories/*_repository.py`              |
| `PasswordHasherPort`            | `BcryptPasswordHasher`                      |
| `AccessTokenPort`               | `JwtAccessTokenProvider`                    |
| `OpaqueTokenPort`               | `Sha256OpaqueTokenProvider`                 |

`fastapi_pagination` (`Page`, `Params`) es la única librería de framework permitida en el núcleo.

### 2.3. Los repositorios no conocen HTTP
Los repositorios solo manejan acceso a datos y no conocen request, response, status codes ni detalles de transporte. Solo hacen `flush()`: el `commit` lo hace `get_db` una vez por request. La única excepción es confirmar una revocación antes de lanzar un error, como en la detección de reuso del refresh token.

### 2.4. La base de datos no se crea con `create_all()`
La estructura de la base debe gestionarse solo a través de Alembic. El proyecto debe arrancar sin crear tablas automáticamente.

### 2.5. La configuración vive en variables de entorno
No se aceptan secretos, URLs de base de datos ni configuraciones sensibles en código fuente ni en imágenes Docker. `JWT_SECRET` y `SUPER_ADMIN_PASSWORD` tienen valores por defecto solo para desarrollo y deben cambiarse en cualquier otro entorno. La configuración llega al núcleo por parámetros del constructor o del método, nunca porque un servicio importe `settings`. Los orígenes que CORS permite se definen en `CORS_ORIGINS`, nunca con `*` ni escritos en el código.

### 2.6. La inyección de dependencias es obligatoria
Toda dependencia de sesión, repositorio, adaptador o servicio debe pasar por `Depends` en la capa HTTP. Toda la conexión de piezas se hace en `api/deps.py`. Fuera del ciclo HTTP (por ejemplo `db/seed.py`) se conectan explícitamente, con los mismos adaptadores.

### 2.7. Cada entidad tiene su propio servicio
`UserService`, `RoleService`, `PermissionService`, `RefreshTokenService`, `CategoryService` y `ProductService` manejan cada uno su entidad. Un caso de uso que combina varias (como `AuthService`) no accede a repositorios: orquesta a los servicios y usa puertos.

### 2.8. Los permisos son constantes y todo endpoint protegido declara el suyo
- Los permisos se definen como constantes en `core/permissions.py` con la forma `recurso:acción`. No se escriben strings sueltos en los routers.
- Cada constante lleva su título en `PERMISSION_TITLES`, que el seed usa para crear los permisos en la base.
- Cada endpoint protegido declara `dependencies=[Depends(require_permissions(CONSTANTE))]`. Los `restore` usan el permiso `DELETE_*` del recurso.
- Un permiso nuevo requiere: la constante, su título y, si aplica, su asignación en `ROLE_PERMISSIONS` del seed. `super_admin` recibe todos automáticamente. En una base ya existente, `admin` y `client` no los reciben solos: se asignan con `PUT /roles/{id}`.

### 2.9. Las relaciones se piden explícitamente
Las relaciones no se cargan por defecto. Las lecturas del repositorio aceptan `relations`, por ejemplo `relations={"role": {"permissions": True}}`, y el servicio decide qué pedir según el caso de uso. Un listado no carga relaciones que su schema de respuesta no muestra, y si carga alguna, la pide con `relations` para evitar el problema de N+1.

### 2.10. El borrado es lógico
`DELETE` pone `deleted_at`, no borra la fila. Toda lectura normal del repositorio filtra `deleted_at IS NULL`. Cada entidad con borrado lógico expone `restore`, protegido por el permiso `DELETE_*`. Ninguna consulta debe devolver registros borrados por accidente.

### 2.11. Autenticación
- El access token es un JWT de corta vida que solo lleva `sub`, `iat`, `exp` y `type`. Los permisos **no** viajan en el token: se resuelven en cada request desde el rol actual del usuario.
- El refresh token es un valor opaco aleatorio. En base de datos solo se guarda su hash. Se rota en cada uso dentro de una familia; reusar uno ya usado revoca la familia completa, y esa revocación se confirma antes de responder el error.
- Las contraseñas se procesan solo a través de `PasswordHasherPort`.
- Un usuario bloqueado responde `403`. `signup` crea el usuario sin rol, y no tiene permisos hasta que un administrador se lo asigne.

### 2.12. Contratos de API consistentes
- Las relaciones en los payloads de entrada se envían como referencia, no como un `*_id` suelto: `category: { "id": 1 }`, `role: { "id": 2 }`. Cada una tiene su schema `*Reference` con `id` mayor que 0.
- Las respuestas de listado usan un schema resumido (por ejemplo `RoleSummaryResponse`, sin permisos) y las de detalle usan el completo.
- Las respuestas usan `camelCase`. Los campos de auditoría vienen de `AuditFieldsMixin`.

### 2.13. Los errores de negocio son errores de dominio
Los servicios lanzan excepciones de `core/exceptions.py`, nunca `HTTPException`. `main.py` las traduce a HTTP en un solo lugar (404, 409, 422, 401 o 403 según su tipo). Un error de dominio nuevo debe clasificarse ahí; si no, responde `400` por defecto. La única `HTTPException` permitida es el `401` de `api/auth_deps.py`, porque necesita el header `WWW-Authenticate`.

## 3. Flujo recomendado

La forma correcta de ejecutar una funcionalidad es:

1. Request llega al router.
2. `Depends` resuelve las dependencias: sesión, repositorios, adaptadores, servicios y, si el endpoint es protegido, el usuario actual (`get_current_user`) y sus permisos (`require_permissions`).
3. El router valida la entrada con el schema y llama a un servicio.
4. El servicio aplica la lógica de negocio y usa puertos para todo lo externo.
5. El repositorio ejecuta la operación con las relaciones solicitadas y devuelve entidades o resultados.
6. El router usa el mapper para transformar las entidades en schemas de respuesta.
7. Si algo falla, el servicio lanza un error de dominio y `main.py` lo convierte en la respuesta HTTP.
8. `get_db` confirma la transacción si todo salió bien, o hace rollback si hubo un error.
9. El response se devuelve al cliente.

## 4. Reglas de calidad

- cada cambio funcional debe ir acompañado de pruebas reales
- los servicios se prueban con puertos falsos en memoria, sin base de datos
- los endpoints deben devolver errores HTTP consistentes
- las migraciones deben revisarse manualmente antes de aplicarse
- los nombres de paquetes, clases y rutas deben seguir una convención consistente
- no se aceptan hacks para “ahorrar tiempo” en la capa de acceso a datos

### Verificación automática

`tests/test_architecture.py` lee los `import` de cada archivo y hace fallar la suite si se rompe alguna de estas reglas:

| Regla                                                                                     | Verifica |
|-------------------------------------------------------------------------------------------|----------|
| `services/` no importa `sqlalchemy`, `passlib`, `jwt`, `fastapi`, `starlette`             | 2.2      |
| `services/` no importa `repositories/`, `adapters/`, `api/`, `db/`, `middleware/` ni `app.core.config` | 2.2, 2.5 |
| `core/` (salvo `config.py` y `logging.py`) cumple las mismas restricciones                | 1, 2.2   |
| `api/` (salvo `deps.py`) no importa repositorios, adaptadores ni `db/`                    | 2.1, 2.6 |

El resto de las reglas se revisa en el pull request con la checklist.

## 5. Checklist para PRs

Antes de aceptar un pull request, revisar:

- [ ] El router no hace consulta directa a base de datos ni importa repositorios o adaptadores
- [ ] El servicio encapsula la lógica de negocio y depende solo de puertos
- [ ] Cada entidad nueva tiene su propio servicio
- [ ] El repositorio no conoce HTTP ni request/response
- [ ] Las relaciones se piden con `relations` y los listados no provocan N+1
- [ ] No hubo `create_all()` ni cambios de esquema manuales sin migración
- [ ] La configuración está en entorno y no se importa `settings` dentro de un servicio
- [ ] Los endpoints nuevos declaran su permiso con una constante de `core/permissions.py`
- [ ] Los permisos nuevos tienen título y están asignados en el seed, o se documentó cómo asignarlos
- [ ] Los errores nuevos son errores de dominio y están clasificados en `main.py`
- [ ] Los payloads referencian entidades como `{ "id": n }` y los listados no exponen datos de detalle
- [ ] Hay pruebas para la funcionalidad modificada y `tests/test_architecture.py` pasa
- [ ] La dependencia de BD, los repositorios y los adaptadores están inyectados con `Depends` en `api/deps.py`

Si el cambio agrega un dominio completo, seguir la guía del README ("Cómo agregar un nuevo dominio").

## 6. Criterio de aprobación

Un PR se considera aceptado solo si respeta estas reglas y mantiene la separación de responsabilidades sin introducir acoplamiento innecesario.

Este estándar debe mantenerse como política del proyecto y no como recomendación informal.