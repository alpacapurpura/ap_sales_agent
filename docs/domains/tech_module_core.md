---
module: Technical Module Core
status: active
---

# Core (`backend/src/core/`)

Infraestructura tecnica base, 100% agnostica al negocio.

## Componentes

- **config.py** — Carga de variables de entorno via Pydantic Settings.
- **database.py** — Engine SQLAlchemy, `SessionLocal`, `get_db()` dependency.
- **context.py** — `ContextVar` para `tenant_id` y `user_id` (request-scoped, thread-safe).
- **base_repository.py** — `BaseRepository` con `_apply_tenant_filter()` y `_set_tenant()` automaticos desde ContextVars.
- **exceptions.py** — Jerarquia de excepciones de aplicacion.
- **sentry.py** — `init_sentry(service_name)` con redaccion de PII, traces sampler dinamico, integraciones por servicio (FastAPI/ARQ/SQLAlchemy/httpx).
- **security.py** — Middlewares de autenticacion y CORS.
- **logger.py** — Configuracion de structlog.
- **enums.py** — Enums globales (`AIProvider`, etc.).

## CRITICO — No Violar

- `core` NO importa de `shared` ni de `modules`. Si necesitas logica de negocio, va en `shared` o en el modulo correspondiente.
