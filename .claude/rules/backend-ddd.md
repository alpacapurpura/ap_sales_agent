---
globs: "backend/src/**/*.py"
description: DDD architecture rules for backend Python code
---

# Backend DDD Rules

## Layer Order (Inside-Out)
`domain` → `infrastructure` → `application` → `api`

- **domain/**: Models, VOs, repo interfaces, events. No framework imports.
- **infrastructure/**: SQLA repos, external clients. Implements domain interfaces.
- **application/**: Services, use cases. Calls domain+infrastructure.
- **api/**: FastAPI routes, Pydantic DTOs. Thin — delegates application.

## Constraints
- Every query MUST filter `tenant_id` (from `X-Tenant-ID`) — incluye `get_by_id()`
- Soft deletes only: `deleted_at` column, never hard delete
- SQLA 2.0 syntax: `select(Model).where(...)`, not `session.query(Model)`
- New code MUST use `AsyncSession`. Legacy sync `Session` existe — migrate incrementally
- `structlog` para logging, not `print()` / `import logging`
- Pydantic v2 DTOs — `model_config = ConfigDict(...)`, not inner `class Config`

## FastAPI App Configuration
- `FastAPI(redirect_slashes=False)` **mandatory** en `main.py`. Default (`True`) emite 307 en POST sin trailing slash; Next.js proxy strips slash, drops body silently.
- Arch test `test_fastapi_app_has_redirect_slashes_disabled` enforces.
- Never set `redirect_slashes=False` en individual `APIRouter` — app-level covers all routes.

## Cross-Module Imports
- **Default: forbidden.** Module A no importa de B's domain/infrastructure/application.
- **Allowed exceptions:** `copilot` puede importar (infra-like orchestrator). Use `shared/links/` para otras inter-module.
- Necesitas data de otro module → port/interface en `shared/` o domain event.

## Extraction Orchestrators
- Wave-based LLM extraction pipelines (brand, offer, buyer_persona, landing, …) MUST subclass `src.shared.application.extraction.base_orchestrator.BaseExtractionOrchestrator`.
- Base provides: `_run_wave`, `_pause_between_waves`, `_announce_sections`, `_get_wave_delay` hook, `log_prefix` for module-specific structlog event names.
- Subclass owns: wave composition, `_merge_and_save`, `run()` entry point.
- Arch gate: `tests/architecture/test_extraction_orchestrator_inheritance.py` blocks new `*Extraction*Orchestrator*` classes that skip the base.
