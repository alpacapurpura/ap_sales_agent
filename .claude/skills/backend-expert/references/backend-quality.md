# Backend Quality
Last verified: 2026-04-15

## Ruff: 0 errors, 70+ rules (Wave 5)
Config: `backend/pyproject.toml`. Line 120. Target py311.

Rules: E, W, F, I, UP, B, S, C901, PERF, DTZ, SIM, PIE, RET, RSE, C4, FURB, FLY, N, A, ISC, T20, LOG, ERA, PGH, PT, TCH, PL, RUF, ARG, FBT, EM, INP, ANN (src/), D (src/), FAST, NPY, PYI, PTH, TD, FIX, G, TRY, BLE.

Ignores: B008 (FastAPI Depends), PLR2004 (magic), PLR0913 (many args), FBT001/002 (bool args), E712/711 (SQLA `== True/None`), RUF001 (Spanish unicode), S105-S108/S110/S311/S324/S608/S701 (OAuth/Docker/GAQL).

Per-file: tests/ → S101, ARG, PT, F401 OK. alembic/ → INP001, D103 OK. admin/ → C901, PLR OK.

## Pytest: asyncio auto, fail_under=43%
- testpaths: `tests/`, `src/tests/`
- Markers: `integration` (live), `verify` (slow, excluded: `-m 'not verify'`)
- Coverage: `src/modules`, `src/shared`. Omit: `*/models/*`, `*/migrations/*`, `*/__init__.py`, `*/workers/*`

## 10 Architecture Fitness Gates (`backend/tests/architecture/`)

| Test | Enforces |
|---|---|
| `test_ddd_boundaries` | No cross-module imports (ratchet ~95) |
| `test_api_contracts` | `response_model=` en all endpoints. `redirect_slashes=False` |
| `test_conventions` | No `session.delete()`. No `session.query()` (SA 2.0 only) |
| `test_currency_consistency` | Currency from data source, valid ISO 4217 |
| `test_extraction_contract` | ETL contract synced providers+catalog+docs |
| `test_master_data` | No hardcoded "USD", no `utcnow()`, `DateTime(timezone=True)` |
| `test_meta_provider_invariants` | Meta `time_increment=1`, no period aggregates en official_metrics |
| `test_folder_naming` | All .py snake_case, DDD layers exist |
| `test_domain_purity` | Domain no SQLA Base, no Session |

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`

## Naming
- Files: `snake_case` (`*_repository.py`, `*_service.py`, `*_model.py`)
- Classes: `PascalCase`
- Tests: `test_{function}_{condition}_{expected}`
- Structure: `domain/` → `infrastructure/` → `application/` → `api/`

## Code quality tools

| Tool | Command | Checks |
|---|---|---|
| jscpd | `npx jscpd backend/src/ --threshold 5` | Dup (baseline 3.63%) |
| interrogate | `cd backend && .venv/bin/interrogate -vv src/modules/` | Docstring coverage |
| pytest-randomly | auto | Hidden test order deps |
| pytest-timeout | auto (30s) | Hanging async |

## Commands (native only — NEVER docker exec)

| Action | Command |
|---|---|
| Lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Format | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| Tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Arch | `cd backend && .venv/bin/pytest tests/architecture/ -x -q` |
| Coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q` |
| Single | `cd backend && .venv/bin/pytest tests/modules/{m}/ -v` |
