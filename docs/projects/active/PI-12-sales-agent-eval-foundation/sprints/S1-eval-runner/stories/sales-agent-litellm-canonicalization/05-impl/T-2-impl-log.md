---
ticket: T-2
title: "make sync-pricing extends litellm_sync.py + drift detection + Makefile target"
owner: dev-team (claude-opus-4-7)
started: 2026-05-05T08:00Z
phase: impl_in_progress
---

# T-2 Implementation Log (live)

## Step 0 GATE — Skills consulted

- **backend-expert** — invoked. Loaded `references/runtime-quality-checklist.md` (read at impl start). Decision: anti-patterns avoided — no `Any` in DTOs, no untyped dicts in service interfaces, structlog only, idempotent in-memory caching of yaml file (warn on missing).
- **tessl__pytest-api-testing** — invoked. Decision: factory fixtures for SyncResult, parametrized tests for exit codes 0/1/2, monkeypatch for httpx ConnectError simulation, autouse fixture for cleanup.
- **tessl__graceful-degradation** — invoked. Decision: yaml parse wrapped in try/except → warn + continue (best-effort cross-check; sync still proceeds even if yaml unreachable). Upstream HTTP already has `httpx.Client(timeout=30.0)` in pricing_sync_task; T-2 does not regress.
- **metrics-expert** — invoked (tagged in tickets.yaml). Decision: pricing snapshot drift detection logged as structlog warn (not raise) — analytics extraction-contract pattern matches "best-effort observability for runtime, hard fail in tests".

## Step 0.5 — Default-flip detection

- N/A. T-2 does NOT modify any feature flag in `core/config.py`. No call-path side-effect change. Skipping audit per rule (only triggers on flag flip).

## Anti-duplication audit (Step 0 grep evidence)

```bash
$ grep -rn "def sync_pricing\|class.*Sync" backend/src/shared/agent_observability/
backend/src/shared/agent_observability/pricing/litellm_sync.py:66:class SyncResult:
backend/src/shared/agent_observability/pricing/litellm_sync.py:75:def sync_pricing(...
```

Decision: EXTEND existing `litellm_sync.py` per arch doc § 1 Sistema 2 + decision A5 (BINDING). No parallel sync module created. Adds:
- `_validate_yaml_against_litellm_registry(yaml_path)` helper (cross-check warn).
- `_detect_upstream_drift(snapshot, upstream_entry)` helper (drift warn).
- New `SyncResult` fields `config_yaml_warnings: int`, `drift_warnings: int`.

## Files modified / created (planned)

```
M  backend/src/shared/agent_observability/pricing/litellm_sync.py             (+~120 lines: yaml parser + drift detector + 2 SyncResult fields)
M  backend/src/shared/agent_observability/workers/pricing_sync_task.py        (+5 lines: propagate new fields to log + return dict)
M  Makefile                                                                    (+8 lines: sync-pricing target)
N  backend/tests/shared/agent_observability/pricing/__init__.py                (empty)
N  backend/tests/shared/agent_observability/pricing/test_litellm_sync_extensions.py  (4 tests per ticket A1-A4 + 2 supporting)
```

`requirements-runtime.txt` UNCHANGED — pyyaml 6.0.3 already transitively installed (langchain-core, langchain-community). No GHA workflow file added — A6 ratificada decisión: ARQ scheduler primary, no GHA cron (security perimeter).

## TDD cycle

- [x] RED tests written (6 tests; ran first → 1 FAIL on `config_yaml_path` arg missing, others FAIL on event-name expectations)
- [x] GREEN implementation (extended `litellm_sync.py` + `pricing_sync_task.py`; switched test capture to `structlog.testing.capture_logs()`)
- [x] REFACTOR (TYPE_CHECKING for `Path`, ruff format)
- [x] Lint + format clean (ruff check + format → all passed)
- [x] T-2 tests pass (6/6)
- [x] Existing pricing-sync regression preserved (3/3 in `test_litellm_sync.py`)
- [x] Wider observability suite + arch fitness (1014 + 823 passed)
- [x] Coverage maintained ≥43% — `litellm_sync.py` 88%, module aggregate 75%
- [ ] `make sync-pricing` smoke (deferred to ops — needs live DATABASE_URL)

## Cross-module reads (none)

## Final files modified

```
M  backend/src/shared/agent_observability/pricing/litellm_sync.py        (+136/-7)
M  backend/src/shared/agent_observability/workers/pricing_sync_task.py   (+44/-9)
M  Makefile                                                              (+16/-1)
N  backend/tests/shared/agent_observability/pricing/__init__.py
N  backend/tests/shared/agent_observability/pricing/test_litellm_sync_extensions.py  (+247)
N  docs/projects/.../05-impl/T-2-impl-log.md (this file)
N  docs/projects/.../05-impl/T-2-result.md
```

## Pre-existing failures NOT caused by T-2

- `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used`
- `tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns`

Verified via `git stash` of T-2 changes — both fail without T-2 too. They belong to T-1 / T-7
territory (`cost_recorder.no_call_id_on_response` warnings → `cost_usd=None` → assertion fails).
T-7 builder is responsible.
