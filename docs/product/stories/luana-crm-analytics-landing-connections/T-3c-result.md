# T-3c Result — Analytics Workers + ETL Makefile + Drift Arch Test

## Status: DONE

**Commit:** `28d5317`
**Push:** `2d5460d..28d5317 main -> main`
**Date:** 2026-05-11

## What was built

### Workers package (lift mode verbatim)

`core/luana-core-analytics-engine/src/luana_core_analytics_engine/workers/`

| File | Source | Description |
|---|---|---|
| `__init__.py` | AISALESHT `workers/__init__.py` | Package marker |
| `scheduler.py` | AISALESHT `workers/scheduler.py` | ARQ tick scheduler — 3am local enqueue + period boundary detection |
| `tasks.py` | AISALESHT `workers/tasks.py` | ARQ task functions: tenant extraction, initial load, period extraction, campaign sync, mailerlite ETL, manychat sync, inactivity detection |
| `manychat_sync.py` | AISALESHT `workers/manychat_sync.py` | ManyChat subscriber enrichment (6h rate-limited) |

**Import transformations applied:**
- `src.modules.analytics.*` → `luana_core_analytics_engine.*`
- `src.modules.iam.infrastructure.models.tenant_model` → `luana_core_iam.infrastructure.models.tenant_model`
- `src.shared.links.ports.channel_adapter` → `luana_core_platform.links.ports.channel_adapter`
- `src.shared.links.ports.crm_enrichment` → `luana_core_platform.links.ports.crm_enrichment`
- `src.shared.links.ports.calendar` → `luana_core_platform.links.ports.calendar`
- `src.shared.domain.datetime_utils` → `luana_core_platform.domain.datetime_utils`

### ETL contract generation script

`core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py`

Adapted from AISALESHT `backend/scripts/generate_extraction_contract_doc.py`. Writes to `core/luana-core-analytics-engine/docs/extraction-contract.md`.

### Makefile

`core/luana-core-analytics-engine/Makefile`

```makefile
make extraction-contract  # runs generator, writes docs/extraction-contract.md
make test                 # runs package test suite
make lint                 # ruff check + format
```

### Generated artifact

`core/luana-core-analytics-engine/docs/extraction-contract.md` — generated and committed. Idempotency verified: two consecutive runs produce identical SHA256.

### Architecture fitness test

`core/tests/architecture/test_analytics_extraction_contract_drift.py`

5 tests:
1. `test_extraction_contract_script_exists` — script at expected path
2. `test_extraction_contract_output_exists_after_generate` — output generated
3. `test_extraction_contract_idempotent` — consecutive SHA256 equality (core of T-3c)
4. `test_extraction_contract_contains_provider_summary` — section header guard
5. `test_extraction_contract_contains_worker_schedule` — section header guard

All 5 pass.

### pyproject.toml

- Added `markers = ["arch: ..."]` to suppress `PytestUnknownMarkWarning`
- Added `"**/scripts/*.py" = ["E402", "E501"]` per-file-ignore (scripts manipulate sys.path)

## Test results

```
T-3c scope tests: 14 passed, 2 skipped
  - test_scheduler_tick.py: 6 passed
  - test_campaign_sync_task.py: 3 passed, 2 skipped (luana_core_connections deferred T-5)
  - test_analytics_extraction_contract_drift.py: 5 passed

Idempotency: IDEMPOTENT GREEN (SHA256 matches on consecutive runs)
AISALESHT: UNTOUCHED (git diff ca1ab02f HEAD -- backend/ frontend/ = empty)
```

## Deferred

- `analytics/copilot_provider/` → Story 6 (excluded all analytics tickets per 05-guidelines.md)
- `luana_core_connections` tests → T-5 (2 tests skipped with `skipif(not _connections_available)`)

## Next

T-4: lift `luana-core-landing` package.
