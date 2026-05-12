# T-13 Implementation Log — campaigns api + workers layer lift

**Story:** luana-campaigns-extension-sdk
**Batch:** D (final ticket)
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Lifted campaigns `api/` and `workers/` layers from AISALESHT
`backend/src/modules/campaigns/` → `luana-core-campaigns` with import path
rewriting. Full campaigns suite: **446 passed, 0 failed** (33 test files).
V-NF-1 confirmed (zero AISALESHT diff).

## Files lifted (src — 13 files)

**api/**
- `api/__init__.py`
- `api/_async_session.py`
- `api/_dependencies.py`
- `api/_service_factories.py`
- `api/routers/__init__.py`
- `api/routers/campaigns_router.py`
- `api/routers/segments_router.py`
- `api/routers/templates_router.py`

**workers/**
- `workers/__init__.py`
- `workers/audit_retention_task.py`
- `workers/execution_task.py`
- `workers/scheduler_tick.py`
- `workers/segment_refresh_tick.py`

## Test files lifted (20 files)

- `tests/api/__init__.py`
- `tests/api/_test_helpers.py` ← NEW (created, not in AISALESHT)
- `tests/api/conftest.py`
- `tests/api/test_campaigns_api.py`
- `tests/api/test_campaigns_launch_real.py`
- `tests/api/test_campaigns_stats_endpoint.py`
- `tests/api/test_segments_integration.py`
- `tests/integration/__init__.py`
- `tests/integration/test_e2e_telegram_campaign_smoke.py`
- `tests/workers/__init__.py`
- `tests/workers/test_audit_retention_task.py`
- `tests/workers/test_execution_task.py`
- `tests/workers/test_scheduler_tick.py`
- `tests/workers/test_segment_refresh_tick.py`

## Import rewriting applied

Per 05-guidelines.md §1.9 sed recipe (10 commands):
- `from src.modules.campaigns.` → `from luana_core_campaigns.`
- `from src.shared.agent_observability.` → `from luana_core_observability.`
- `from src.shared.` → `from luana_core_platform.` (and sub-variants)
- `from src.core.` → `from luana_core_platform.core.`
- `from src.modules.crm.` → `from luana_core_crm.`
- etc.

## Non-trivial fixes applied

### Fix 1: `from src.main import app` — no equivalent in luana-platform

**Root cause:** AISALESHT api tests use the monolith singleton
`from src.main import app` to share one FastAPI instance between `client`
fixture and each test body (so `dependency_overrides` set in either location
affect the same object).

**Fix:** Created `tests/api/_test_helpers.py` with `_make_campaigns_test_app()`
factory that builds a minimal FastAPI app with campaigns routers mounted at
`/api/v1`. Each affected test file declares a module-level singleton:
```python
_campaigns_test_app: FastAPI = _make_campaigns_test_app()
```
All references to `app` inside the file use this singleton — preserving the
shared-instance semantics of the original pattern.

Files fixed: `test_campaigns_api.py` (17 occurrences), `test_campaigns_launch_real.py`
(8 occurrences), `test_segments_integration.py` (4 occurrences).

### Fix 2: `test_campaigns_stats_endpoint.py` hardcoded router path

Two tests used `Path(__file__).parents[4] / "src" / "modules" / ...` to locate
the router source file — a path rooted at `/home/chris/luana-platform` (AISALESHT
layout). Fixed to `Path(__file__).parents[2] / "src" / "luana_core_campaigns" / ...`
(luana-platform package layout: `parents[2]` = `core/luana-core-campaigns`).

## Test results

```
446 passed, 0 failed, 7 warnings in 138.99s
```

Note: ~135s wall time due to Redis connection timeout on startup (Redis not running
locally; app retries before degrading gracefully). All tests pass; timing is infra,
not test logic.

## Invariants confirmed

- **V-NF-1:** `git diff -- backend/src/modules/campaigns/` = empty (zero AISALESHT touch)
- **V-NF-2:** version `0.0.8-alpha` unchanged in pyproject.toml
- **Zero import leaks:** grep `from src.modules|src.shared|src.core` in `luana-core-campaigns/src/` = empty
- **redirect_slashes=False:** confirmed in `_make_campaigns_test_app()` (`FastAPI(redirect_slashes=False)`)

## Downstream sanity

- `luana-core-platform/tests/ + luana-core-events/tests/`: all PASS (background run)
- `luana-core-channels/tests/ + luana-core-iam/tests/`: all PASS (background run)

## luana-platform commit

`df722df` — pushed to `origin main`

## Skills Consulted

- `backend-expert`: runtime quality checklist (SQLA 2.0, tenant isolation, soft deletes)
- `tessl__fastapi`: redirect_slashes=False, response_model, singleton app pattern
- `tessl__pytest-api-testing`: AsyncClient, dependency_overrides singleton semantics, factory fixtures
