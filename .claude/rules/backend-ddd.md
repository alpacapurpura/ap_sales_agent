---
globs: "backend/src/**/*.py"
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
- Every query MUST filter by `tenant_id` (from `X-Tenant-ID` header) — including `get_by_id()` methods
- Soft deletes only: use `deleted_at` column, never hard delete
- SQLAlchemy 2.0 syntax: `select(Model).where(...)`, not `session.query(Model)`
- New code MUST use `AsyncSession`. Legacy sync `Session` exists — migrate incrementally when touching those files
- Use `structlog` for logging, not `print()` or `import logging`
- Pydantic v2 for all DTOs — use `model_config = ConfigDict(...)`, not inner `class Config`

## Cross-Module Imports
- **Default: forbidden.** Module A cannot import from module B's domain/infrastructure/application.
- **Allowed exceptions:** `copilot` may import from other modules (it's an infra-like orchestrator). Use `shared/links/` for all other inter-module communication.
- If you need data from another module, add a port/interface in `shared/` or emit a domain event.
