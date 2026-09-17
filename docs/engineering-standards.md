# Estándar de arquitectura y calidad

Este proyecto sigue un estándar de arquitectura modular y limpia para APIs Python con FastAPI. El objetivo es mantener una base fácil de escalar, testear y mantener sin mezclas de responsabilidades.

## 1. Arquitectura obligatoria

Toda funcionalidad debe respetar esta separación de capas:

- `api/`: entrada HTTP, routers y dependencias de FastAPI.
- `schemas/`: DTOs, validación y contratos de request/response.
- `services/`: reglas de negocio y casos de uso.
- `repositories/`: acceso a la base de datos y consultas.
- `models/`: entidades ORM.
- `mappers/`: conversión entre modelos ORM y schemas.
- `core/`: configuración, logging, contratos e infraestructura compartida.
- `db/`: sesión y conexión a la base de datos.
- `alembic/`: migraciones versionadas.

## 2. Reglas de diseño (obligatorias)

### 2.1. Los routers no tienen lógica de persistencia
Los endpoints deben delegar la lógica a servicios. No se deben realizar queries directas ni manipulación de ORM en los routers.

### 2.2. Los servicios no dependen de SQLAlchemy concreto
Los servicios deben depender de abstracciones o repositories, no de entidades ORM ni de `Session` como detalle de implementación.

### 2.3. Los repositorios no conocen HTTP
Los repositorios solo manejan acceso a datos y no conocen request, response, status codes ni detalles de transporte.

### 2.4. La base de datos no se crea con `create_all()`
La estructura de la base debe gestionarse solo a través de Alembic. El proyecto debe arrancar sin crear tablas automáticamente.

### 2.5. La configuración vive en variables de entorno
No se aceptan secretos, URLs de base de datos ni configuraciones sensibles en código fuente ni en imágenes Docker.

### 2.6. La inyección de dependencias es obligatoria
Toda dependencia de sesión, repositorio o servicio debe pasar por `Depends` en la capa HTTP.

## 3. Flujo recomendado

La forma correcta de ejecutar una funcionalidad es:

1. Request llega al router.
2. El router valida la entrada y llama a un servicio.
3. El servicio aplica la lógica de negocio.
4. El servicio usa un repositorio para acceder a la base de datos.
5. El repositorio ejecuta la operación y devuelve entidades o resultados.
6. El mapper transforma entidades a schemas si es necesario.
7. El response se devuelve al cliente.

## 4. Reglas de calidad

- cada cambio funcional debe ir acompañado de pruebas reales
- los endpoints deben devolver errores HTTP consistentes
- las migraciones deben revisarse manualmente antes de aplicarse
- los nombres de paquetes, clases y rutas deben seguir una convención consistente
- no se aceptan hacks para “ahorrar tiempo” en la capa de acceso a datos

## 5. Checklist para PRs

Antes de aceptar un pull request, revisar:

- [ ] El router no hace consulta directa a base de datos
- [ ] El servicio encapsula la lógica de negocio
- [ ] El repositorio no conoce HTTP ni request/response
- [ ] No hubo `create_all()` ni cambios de esquema manuales sin migración
- [ ] La configuración está en entorno
- [ ] Hay pruebas para la funcionalidad modificada
- [ ] La dependencia de BD está inyectada correctamente

## 6. Criterio de aprobación

Un PR se considera aceptado solo si respeta estas reglas y mantiene la separación de responsabilidades sin introducir acoplamiento innecesario.

Este estándar debe mantenerse como política del proyecto y no como recomendación informal.
