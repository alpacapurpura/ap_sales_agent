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

## Schema-mirror exception (origen R5 process-improvement 2026-05-05)

`builder-backend` MAY touch `modules/copilot/persistence/models/` AND
`modules/sales_agent/persistence/models/` SOLO para schema mirror desde
shared/ migration. Cero juicio caso-a-caso auditor.

**Contexto:** business modules (`shared/agent_observability/persistence/`)
introducen tabla → SQLAlchemy model class debe vivir en módulo consumer
(copilot/sales_agent) para mantener domain ownership. Builder-backend
genera/modifica `modules/{copilot,sales_agent}/persistence/models/X.py`
para reflejar DDL nuevo SIN tocar `domain/`, `application/`, ni `api/`
del módulo agentic.

**Permitido bajo esta exception:**
- Add/modify SQLAlchemy `Mapped[]` columns matching shared migration DDL
- Add/modify table indexes matching shared migration
- Add/modify foreign keys hacia tablas creadas por shared migration
- Mark deprecated columns con `# DEPRECATED:` comment

**NO permitido bajo esta exception:**
- Tocar `modules/{copilot,sales_agent}/{domain,application,api,observability}/` — sigue jurisdicción `builder-agentic`
- Cambiar comportamiento runtime del módulo agentic (sólo schema)
- Crear nueva tabla SOLO en módulo agentic (debe nacer en shared/ con consumer mirror, no al revés)
- Modificar `personality_profiles.system_instruction` o cualquier otro field semantic-load del módulo

**Audit:** auditor-backend debe APPROVE estos cambios sin escalate.
Auditor-agentic NO audita schema mirror (es business migration ripple,
no agentic logic). Si schema change introduce regression cross-surface
→ R3 downstream regression scope captura.

**Caso origen:** PI-12 S1 T-1 (cost_recorder canonicalization). Builder
necesitaba mirror nuevas columnas `cost_usd`, `cache_read_tokens`,
`provider_canonical` en `modules/{copilot,sales_agent}/persistence/models/
copilot_llm_call.py`. Auditor inicialmente flagged "out-of-scope" — Chris
ratificó exception. Codificada aquí para evitar re-litigation.
