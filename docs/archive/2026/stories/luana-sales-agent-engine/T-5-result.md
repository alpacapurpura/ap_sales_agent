# T-5 result — Lift sales_agent infrastructure models + db

## Status: GREEN
## Commit: 20857d9 (luana-platform main) — AISALESHT untouched
## Validators satisfied: V-NF-2 (package builds + tests collect)
## Files lifted: 20 src files

## Files

### infrastructure/models/ (12 SQLA + __init__)

§3 protected (4 — sha256 POST-sed canonical baseline for V-AG-8 T-18):
- message_model.py — `612106ce401a77a8ae310ac2c1b8c7997ec840b2f28b713dcd319bb4f92608d1`
- enrollment_model.py — `a1c402460fbd7795fb9a55e417dfe5319ced24cc51de53dbc587705ed215b138`
- prompt_version_model.py — `1d38d2a223e417bad860cf5aa5c9d7a1347e8579dfbcb521aad161fff70f03fc`
- agent_state_checkpoint_model.py — `580623d9e63260cfc050e07e60412d0d7c25440de4f1dde2ba2fa5cc37d46167`

Other models (8):
- agent_trace_model
- llm_log_model
- payment_grant_audit_model
- payment_link_model
- payment_webhook_event_model
- scheduler_webhook_event_model
- sensitive_data_model
- workflow_metric_model

### infrastructure/db/ (5 files)
- base.py (BaseRepository with tenant_id auto-filter — per tenant-isolation rule)
- database.py (SessionLocal factory)
- repositories/business_repository.py
- models/__init__.py (cross-module SQLA Registry bootstrap)
- db/__init__.py

## Tests GREEN: 17 (no new infrastructure tests at this DAG stage — repository tests need fixtures from T-6 + service tests need T-12)

```
$ cd ~/luana-platform && uv run pytest core/luana-core-sales-agent/tests/ -x -q
17 passed in 0.14s
```

## SSoT preservation

- SQLA Base imported from `luana_core_platform.domain.base_entity` (no mirror)
- SessionLocal imported from `luana_core_platform.core.database` (no mirror)
- BaseRepository tenant_id auto-filter preserves multi-tenant guarantee
- §3 protected files hash captured POST-sed POST-ruff-auto-fix as canonical baseline

## Verification recipes

```bash
# Zero src.* leaks ✓
grep -rEn "from src\." ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/  → empty

# Ruff clean ✓
uv run ruff check core/luana-core-sales-agent

# AISALESHT untouched ✓
git diff HEAD --name-only | grep backend/src/modules/sales_agent  → empty
```

## Note on db/models/__init__.py

AISALESHT db/models/__init__.py contains imports from `src.shared.infrastructure.models.{agent_trace,llm_log,prompt_version}` which DO NOT EXIST in shared/ (dead code — no consumer imports `sales_agent.infrastructure.db.models`). Lifted verbatim per architect spec; sed conversion to `luana_core_platform.infrastructure.models.*` preserves the same dead-code pattern. Future cleanup deferred (not in Story 7 scope — would require removing dead AISALESHT code which is V-NF-4 prohibited).

Last line: done -> docs/product/stories/luana-sales-agent-engine/T-5-result.md
