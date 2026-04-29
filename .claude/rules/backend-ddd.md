---
globs: "backend/src/**/*.py"
description: Backend DDD
---

# Backend DDD

## Layers (Inside-Out)
`domain` → `infrastructure` → `application` → `api`. Domain pure (no framework). Infrastructure implementa interfaces domain. Application = services/use cases. API = FastAPI routes + Pydantic DTOs (thin).

## Constraints
- Every query filter `tenant_id` (incluye `get_by_id`).
- Soft deletes only (`deleted_at`).
- SQLA 2.0 `select(Model).where(...)` (no `session.query()`).
- New code `AsyncSession`. Legacy `Session` migrate incrementally.
- `structlog`, no `print`/`logging`.
- Pydantic v2 `model_config = ConfigDict(...)` (no inner `class Config`).

## FastAPI app
`FastAPI(redirect_slashes=False)` mandatory en `main.py` (default `True` → 307 POST → Next.js drops body). Arch test enforces. NUNCA en `APIRouter` individual.

## Cross-module imports
Default forbidden. Excepción: `copilot` (infra-like). Otros: port/interface en `shared/links/` o domain event.

## Extraction orchestrators
Wave-based LLM extraction (brand/offer/buyer_persona/landing) MUST subclass `src.shared.application.extraction.base_orchestrator.BaseExtractionOrchestrator`. Subclass: wave composition + `_merge_and_save` + `run()`. Arch gate `test_extraction_orchestrator_inheritance.py`.
