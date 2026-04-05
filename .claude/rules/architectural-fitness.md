# Architectural Fitness Tests

## What
Automated tests in `backend/tests/architecture/` that enforce structural rules
Ruff and ESLint cannot catch: DDD boundaries, API contracts, coding conventions.

## Ratchet Pattern
- Tests have allowlists (`KNOWN_*` sets) of legacy violations
- **New violations fail the build** — you cannot ship code that adds a new cross-module import
- Allowlists only shrink (fix violations, remove from list)
- Adding to an allowlist requires explicit justification in the commit message

## When to Run
- `make arch-test` or `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` — standalone (native, never via Docker)
- Included automatically in `pytest`, `/test-backend`, `/test-all`, `/pase-produccion`

## What to Do When a Fitness Test Fails

### `test_no_new_cross_module_imports`
You imported from another module's domain/infrastructure/application. Fix:
1. Move shared types/enums to `src/shared/`
2. Use domain events for cross-module communication
3. Create a port/interface in `src/shared/links/`

### `test_domain_layer_has_no_framework_imports`
You imported SQLAlchemy/FastAPI/httpx in a `domain/` file. Fix:
1. Domain must be pure Python + Pydantic only
2. Move framework code to `infrastructure/`

### `test_all_endpoints_have_response_model`
You created an endpoint without `response_model=`. Fix:
1. Create a Pydantic response DTO
2. Add `response_model=YourDTO` to the decorator

### `test_no_hard_deletes`
You used `session.delete()`. Fix:
1. Use `obj.deleted_at = datetime.utcnow()` instead
2. Update queries to filter `WHERE deleted_at IS NULL`

### `test_no_sqlalchemy_1x_query_syntax`
You used `session.query()`. Fix:
1. Use `session.execute(select(Model).where(...))` instead
2. Use `result.scalars().all()` for the result
