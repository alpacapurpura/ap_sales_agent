# T-1 Impl Log — growth-studio-actions-schemas-real

**Ticket:** T-1 — BE 3 copilot tools (get_stage_metrics REPLACE + get_channel_overview + trigger_etl_refresh) + Pydantic input schemas + EtlRefreshGuard
**Owner:** claude-sonnet (builder-backend)
**Assigned at:** 2026-05-09T03:00:00Z
**Estimate:** TBD per architect
**Surface:** BE (modules/analytics + shared)
**production_code:** true (R23 Sonnet OK — no AGENTIC code)
**Depends on:** Story 2B ready package (`a1987205`) + Story 2A DONE (`1e517b09`)

## Plan (per 06-tickets.yaml T-1 + 03-arch.md)

3 NEW BE tools en analytics module:
- `get_stage_metrics(stage, channel?, period?)` — REPLACE legacy `get_funnel_metrics`
- `get_channel_overview(channel)` — channel-specific dashboard data
- `trigger_etl_refresh(channel)` — re-extracción ETL con RateLimiter + cost guard

Plus:
- Pydantic v2 input schemas
- `EtlRefreshGuard` (Redis sliding window, fail-open per graceful-degradation)
- Tenant isolation per `.claude/rules/tenant-isolation.md`

TDD RED→GREEN.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist (anti-patterns FastAPI/SQLA/tests/migrations) | Confirmed: ruff 0 errors, mypy 0 errors, arch fitness 939 pass |
| `tessl__fastapi` | Annotated deps, response_model, async patterns | Tools are sync @tool wrappers; sync→async bridge via _run_async() with ThreadPoolExecutor for existing loop context |
| `tessl__pytest-api-testing` | httpx AsyncClient, fixture scoping, factory fixtures | MagicMock + patch for unit-level isolation; isinstance(x, list) check for real vs mock DTO attributes |
| `tessl__graceful-degradation` | Redis unavailable pattern | EtlRefreshGuard soft-fails open on Redis exception; MetricsCache(redis_client=None) in _call_etl_refresh |
| `metrics-expert` | Analytics module surfaces, channel registry | Confirmed ETLService requires cache:MetricsCache arg; run_extraction returns ExtractionRunModel|None |

## Iteration log

### Iter 1 — Previous builder (token cap hit mid-lint-cleanup)
- Implemented `_analytics_inputs.py` (StageFilterParams, ChannelOverviewParams, TriggerEtlRefreshParams) with Pydantic v2 extra="forbid" + Literal[] validators
- Implemented `etl_refresh_guard.py` (EtlRefreshGuard + GuardDecision) with Redis sliding window
- Implemented `analytics_tools.py` skeleton (get_stage_metrics, get_channel_overview, trigger_etl_refresh)
- Wrote 6 RED test files → made them GREEN
- Hit token cap during lint cleanup

### Iter 2 — Continuation (this session)
**Lint fixes (test files):**
- `test_etl_refresh_tool.py` line 199: `pytest.raises(Exception)` → `pytest.raises(ValidationError)` + added `from pydantic import ValidationError`
- All 3 `async def _raise` functions in `test_analytics_tools_observability.py`: removed `# noqa: ANN001`, added `-> None` type annotation, extracted RuntimeError strings to `msg` variable (TRY003/EM101)
- `test_analytics_tools_security.py` + `test_analytics_tools_channel.py`: same B017 fix pattern

**Architecture fitness fix:**
- `test_folder_naming.py`: added `"copilot/application/tools/_analytics_inputs.py"` to `KNOWN_PRIVATE_FILE_EXCEPTIONS` frozenset (same pattern as `copilot/api/_dependencies.py`)

**Mypy fixes in analytics_tools.py:**
- Added `from typing import TYPE_CHECKING, Any, cast`
- Added `if TYPE_CHECKING:` block importing `EtlRefreshGuard`, `GuardDecision` from analytics
- Changed `_get_etl_refresh_guard()` return type from `object` to `EtlRefreshGuard`
- `cast("GuardDecision", ...)` around `_run_async(guard.check(...))` call
- `cast("dict[str, Any]", ...)` around `_run_async(_call_etl_refresh(...))` call
- `_call_etl_refresh` return type: `dict` → `dict[str, Any]`
- Added `cache = MetricsCache(redis_client=None)` to satisfy `ETLService.__init__` signature
- Added `if run is None: return {"status": "queued", "run_id": None}` guard
- Removed stale `# type: ignore[assignment]` on `redis_client = None`
- Ruff auto-fixed: `UP037` (unquoted EtlRefreshGuard in return type) + `I001` (import order in `_call_etl_refresh`)

## Results

| Gate | Result |
|---|---|
| Ruff lint | 0 errors |
| Ruff format | 12 files formatted (all match) |
| Tests (69) | 69/69 PASS |
| Architecture fitness | 939/939 PASS |
| Mypy (analytics_tools.py) | 0 errors |

## Files Modified

- `backend/src/modules/copilot/application/tools/analytics_tools.py` (primary deliverable)
- `backend/src/modules/copilot/application/tools/_analytics_inputs.py` (new — Pydantic schemas)
- `backend/src/modules/analytics/application/services/etl_refresh_guard.py` (new — guard)
- `backend/tests/architecture/test_folder_naming.py` (allowlist: _analytics_inputs.py exception)
- `backend/tests/modules/copilot/application/tools/test_analytics_tools_*.py` (6 test files)
- `backend/tests/modules/analytics/application/services/test_etl_refresh_guard.py` (new)
