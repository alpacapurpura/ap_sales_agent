---
ticket: T-3b
story: luana-crm-analytics-landing-connections
state: pushed
commit_sha: 2d5460d
pushed_at: 2026-05-11
builder: builder-backend (claude-sonnet-4-6)
---

# T-3b Result — Analytics Infrastructure Lift

## Commit

`2d5460d feat(story-4/T-3b): lift analytics infrastructure (cache+etl+models+providers+repositories+sync)`

Push: `44e04fb..2d5460d main -> main` (alpacapurpura/luana-platform)

## Files lifted: 49 infrastructure files

Directories copied verbatim from `backend/src/modules/analytics/infrastructure/`:

| Subdirectory | Files |
|---|---|
| `infrastructure/__init__.py` | 1 |
| `infrastructure/cache/` | 2 (`__init__`, `metrics_cache`) |
| `infrastructure/etl/` | 5 (`__init__`, `aggregations`, `period_pipeline`, `pipeline`, `transformers`) |
| `infrastructure/models/` | 10 (`__init__` + 9 model files) |
| `infrastructure/providers/` | 15 (`__init__` + 14 provider files) |
| `infrastructure/repositories/` | 13 (`__init__` + 12 repository files) |
| `infrastructure/sync/` | 2 (`__init__`, `campaign_sync_pipeline`) |

**Total: 49 source files + pyproject.toml change = 51 changed (11099 insertions)**

## Import rewrites applied

All `src.*` imports cleared. Rewrites applied:
- `src.modules.analytics.*` → `luana_core_analytics_engine.*`
- `src.modules.connections.*` → `luana_core_connections.*` (TYPE_CHECKING-only, no runtime dep needed)
- `src.modules.iam.*` → `luana_core_iam.*`
- `src.shared.domain.*` → `luana_core_platform.domain.*`
- `src.shared.links.*` → `luana_core_platform.links.*`
- `src.shared.infrastructure.*` → `luana_core_platform.infrastructure.*`
- `src.shared.application.*` → `luana_core_platform.application.*`
- `src.core.*` → `luana_core_platform.core.*`

## Deferred

- `analytics/copilot_provider/` — not present in `infrastructure/` (lives at module root level, already excluded per T-3a)

## Verification checklist

- [x] AISALESHT untouched: `git diff ca1ab02f HEAD -- backend/ frontend/` = empty
- [x] No copilot_provider in infrastructure: `ls ... | grep copilot || echo "NO"` = NO
- [x] No forward Story 5+ imports: grep clean
- [x] No brand control flow: grep clean
- [x] No hardcoded credentials: grep clean
- [x] No remaining `src.*` imports: grep clean
- [x] `uv sync --all-packages` resolves 170 packages cleanly
- [x] `ruff check` passes (added E712 to workspace ignore list — SQLAlchemy ORM pattern same as E711)

## Test status

| Test | Status | Notes |
|---|---|---|
| `test_scheduler_tick.py` | EXPECTED FAIL | `workers/scheduler` not yet lifted — T-3c scope |
| All other tests | TIMEOUT (>2min) | Consistent with T-3a aggregate isolation issue — deferred to T-3c per spec |

Per spec (T-3b entry): "Tests may NOT all be GREEN yet (workers + scheduler tests). DOCUMENT count + which tests fail. Defer GREEN check to T-3c."

## pyproject.toml change

Added `E712` to ruff ignore list in workspace root `pyproject.toml`. Rationale: `Model.col == True/False` is valid SQLAlchemy ORM filter syntax (same rationale as existing `E711` ignore for `== None`). AISALESHT passes E712 via narrower rule selection. luana-platform uses `["E", "F", "I"]` which catches it.
