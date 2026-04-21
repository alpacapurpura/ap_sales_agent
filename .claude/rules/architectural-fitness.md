# Architectural Fitness Tests

## What
Automated tests en `backend/tests/architecture/` enforzando reglas estructurales que Ruff/ESLint no catch: DDD boundaries, API contracts, conventions.

## Ratchet Pattern
- Tests tienen allowlists (`KNOWN_*`) legacy violations
- **New violations fail build** — no ship con new cross-module import
- Allowlists shrink only (fix + remove)
- Agregar a allowlist requiere justificación en commit message

## When to Run
- `make arch-test` o `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` — standalone (native, nunca Docker)
- Auto en `pytest`, `/test-backend`, `/test-all`, `/pase-produccion`

## Fixes

### `test_no_new_cross_module_imports`
Importaste de otro module domain/infra/application:
1. Move shared types/enums → `src/shared/`
2. Domain events para cross-module
3. Port/interface en `src/shared/links/`

### `test_domain_layer_has_no_framework_imports`
SQLA/FastAPI/httpx en `domain/`:
1. Domain = pure Python + Pydantic only
2. Framework code → `infrastructure/`

### `test_all_endpoints_have_response_model`
Endpoint sin `response_model=`:
1. Create Pydantic response DTO
2. Add `response_model=YourDTO`

### `test_no_hard_deletes`
Usaste `session.delete()`:
1. `obj.deleted_at = datetime.utcnow()`
2. Queries filter `WHERE deleted_at IS NULL`

### `test_no_sqlalchemy_1x_query_syntax`
Usaste `session.query()`:
1. `session.execute(select(Model).where(...))`
2. `result.scalars().all()` para resultado
