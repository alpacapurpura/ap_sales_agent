# Backend Quality
Last verified: 2026-04-15

## Ruff: 0 errors, 70+ rules (Wave 5)
Config: `backend/pyproject.toml`. Line length: 120. Target: py311.

Rules: E, W, F, I, UP, B, S, C901, PERF, DTZ, SIM, PIE, RET, RSE, C4, FURB, FLY, N, A, ISC, T20, LOG, ERA, PGH, PT, TCH, PL, RUF, ARG, FBT, EM, INP, ANN (src/ only), D (src/ only), FAST, NPY, PYI, PTH, TD, FIX, G, TRY, BLE.

Strategic ignores: B008 (FastAPI Depends), PLR2004 (magic numbers), PLR0913 (many args), FBT001/002 (bool args), E712/711 (SQLAlchemy `== True/None`), RUF001 (Spanish unicode), S105-S108/S110/S311/S324/S608/S701 (OAuth/Docker/GAQL contexts).

Per-file: tests/ → S101 (assert), ARG, PT, F401 allowed. alembic/ → INP001, D103 allowed. admin/ → C901, PLR complexity allowed.

## Pytest: asyncio auto, fail_under=43%
- testpaths: `tests/`, `src/tests/`
- Markers: `integration` (live APIs), `verify` (slow, excluded by default: `-m 'not verify'`)
- Coverage source: `src/modules`, `src/shared`. Omit: `*/models/*`, `*/migrations/*`, `*/__init__.py`, `*/workers/*`

## 7 Architecture Fitness Gates

| Test file | Enforces |
|-----------|----------|
| `test_ddd_boundaries` | No cross-module imports (ratchet allowlist, ~95 known) |
| `test_api_contracts` | All endpoints have `response_model=`. `redirect_slashes=False` in app |
| `test_conventions` | No `session.delete()` (soft deletes). No `session.query()` (SA 2.0 only) |
| `test_currency_consistency` | Currency from data source, valid ISO 4217, exchange rates exist |
| `test_extraction_contract` | ETL contract synced with providers + catalog + generated docs |
| `test_master_data` | No hardcoded "USD", no `utcnow()`, `DateTime(timezone=True)` |
| `test_meta_provider_invariants` | Meta `time_increment=1`, no period aggregates in official_metrics |

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`

## Naming
- Files: `snake_case` (`*_repository.py`, `*_service.py`, `*_model.py`)
- Classes: `PascalCase` (`BrandService`, `LeadRepository`)
- Tests: `test_{function}_{condition}_{expected}`
- Module structure: `domain/` → `infrastructure/` → `application/` → `api/`

## Commands (native only — NEVER docker exec)

| Action | Command |
|--------|---------|
| Lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Format | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| Tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Arch tests | `cd backend && .venv/bin/pytest tests/architecture/ -x -q` |
| Coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q` |
| Single module | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |
