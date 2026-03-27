---
globs: "backend/**/*.py"
description: DDD architecture rules for backend Python code
---

# Backend DDD Rules

## Layer Order (Inside-Out)
`domain` → `infrastructure` → `application` → `api`

- **domain/**: Models, value objects, repository interfaces, domain events. No framework imports.
- **infrastructure/**: SQLAlchemy repos, external API clients. Implements domain interfaces.
- **application/**: Services, use cases, orchestration. Calls domain + infrastructure.
- **api/**: FastAPI routes, DTOs (Pydantic). Thin layer — delegates to application.

## Constraints
- Every query MUST filter by `tenant_id` (from `X-Tenant-ID` header)
- Soft deletes only: use `deleted_at` column, never hard delete
- SQLAlchemy 2.0 syntax: `select(Model).where(...)`, not `session.query(Model)`
- All DB operations are async (`async_session`)
- No cross-module imports (module A cannot import from module B's domain)
- Use `structlog` for logging, not `print()` or `logging`
- Pydantic v2 for all DTOs
