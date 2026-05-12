# T-4 result — Lift sales_agent domain layer

## Status: GREEN
## Commit: 09740e3 (luana-platform main) — AISALESHT untouched
## Validators satisfied: V-NF-2 (package builds + tests collect)
## Files lifted: 10 src + 2 tests = 12 (excluding __pycache__)

## Files

### Src (10)
- domain/__init__.py
- domain/base_entity.py
- domain/enrollment.py
- domain/enums.py
- domain/events.py
- domain/exceptions.py
- domain/memory/__init__.py
- domain/memory/repository.py (Protocol — tenant_id parameter present per tenant-isolation)
- domain/message.py
- domain/model_tier.py (preserves LLM_ROLE_BY_SITE + SPECIALIST_TO_ROLE SSoT — S12 cement)
- domain/semantic_routes.py
- domain/tuning.py

### Tests (2 pure-domain, GREEN)
- tests/test_enrollment_domain.py — Enrollment entity invariants (Phase 5)
- tests/test_specialist_role_mapping.py — SPECIALIST_TO_ROLE SSoT mapping (S4)

## Tests NOT lifted T-4 (cross-layer dependencies — wait for subsequent tickets)
- test_specialist_provider_routing.py — imports application.agents.sales.nodes (T-9 lifts)
- test_follow_up_engine.py — imports infrastructure.prompts.templates + infrastructure.monitoring.tracing (T-13 lifts)
- test_outbox_adapter_integration.py — imports application.* + infrastructure.* (T-8+ lifts)
- test_enrollment_repository.py — imports infrastructure.* (T-6 lifts)
- test_enrollment_service.py — imports application.services (T-12 lifts)
- test_enrollment_tools.py — imports application.tools (T-10 lifts)
- test_message_repository.py — imports infrastructure.* (T-6 lifts)
- test_auto_grant_on_paid.py — imports workers (T-13 lifts)

## Tests GREEN: 17

```
$ cd ~/luana-platform && uv run pytest core/luana-core-sales-agent/tests/ -x -q
17 passed in 0.14s
```

## SSoT preservation

- `LLM_ROLE_BY_SITE: dict[str, ModelRole]` — preserved in `domain/model_tier.py` (S12 SSoT cement)
- `SPECIALIST_TO_ROLE: dict[str, ModelRole]` — preserved (sub-view of LLM_ROLE_BY_SITE)

## Verification recipes

```bash
# Zero src.* leaks ✓
grep -rEn "from src\.(modules|shared|core)\." ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/domain/  → empty
grep -rEn "from src\." ~/luana-platform/core/luana-core-sales-agent/tests/  → empty

# Ruff clean ✓
uv run ruff check core/luana-core-sales-agent/src/luana_core_sales_agent/domain

# AISALESHT untouched ✓
git diff HEAD --name-only | grep backend/src/modules/sales_agent  → empty
```

Last line: done -> docs/product/stories/luana-sales-agent-engine/T-4-result.md
