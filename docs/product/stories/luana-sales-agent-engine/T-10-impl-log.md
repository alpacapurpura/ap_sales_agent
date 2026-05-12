---
story_id: luana-sales-agent-engine
ticket_id: T-10
owner: builder-agentic (Opus 4.7 — R23)
state: done
last_modified: 2026-05-11
commit_sha: c2fbae1
---

# T-10 — Lift application/tools/ (registry + payment + scheduling provider strategy + §3 webhook adapters)

## Scope

Lift `backend/src/modules/sales_agent/application/tools/` from AISALESHT (10 src files + 10 test files). Includes 2 §3 PROTECTED webhook adapter files (hash-stable).

## Steps executed

1. `cp -r` tools/ from AISALESHT (3 subfolders + registry.py).
2. Cleared __pycache__.
3. Verified pre-sed: scheduling/providers.py has 6 deferred imports inside method bodies (lines 217/234/306/319/330/346) — confirmed per 03-arch.md §9.2.
4. Applied sed pipeline per 05-guidelines.md §1.4 (22 substitutions).
5. Verified zero `from src.*` leaks at top-level via grep.
6. Verified deferred imports correctly rewritten + remain inside method bodies:
   ```
   217:        from luana_core_platform.links.ports.scheduling import (
   234:        from luana_core_platform.links.ports.domain_lookup import create_domain_lookup
   306:        from luana_core_platform.links.ports.scheduling import list_event_type_slots
   319:        from luana_core_iam.infrastructure.models.tenant_model import TenantModel
   330:        from luana_core_platform.links.ports.scheduling import lookup_booking_link_by_token
   346:        from luana_core_platform.links.ports.scheduling import (
   ```
7. V-AG-2 AST check: zero top-level `from luana_core_scheduling.*` imports in src/.
8. Ran `ruff format` (6 files reformatted).
9. Ran `ruff check --fix` — encountered E402 in payment/providers.py forward-reference re-export of `PaymentWebhookEvent`. Added per-file-ignore per §1.7 verbatim-lift principle.
10. Final ruff check: All checks passed!
11. Captured §3 sha256 baselines POST-sed POST-ruff for T-18 V-AG-8.
12. Copied tests (5 payment + 4 scheduling + 1 test_tools = 10 test files).
13. Applied sed pipeline to tests (imports + monkeypatch strings). Also rewrote test deferred imports `src.modules.scheduling.*` → `luana_core_scheduling.*` to anticipate Story 8 lift (remain INSIDE method bodies — V-AG-2 invariant preserved).
14. Ran `ruff format` + `ruff check --fix` on tests — 14 errors autofix, 5 files reformatted.
15. AST parse OK all 10 src files.

## §3 hash-stable baselines (CANONICAL for T-18 V-AG-8)

POST-sed POST-ruff format:

```
payment/webhook_providers.py:    9cf3cfd927cec33eabdbe690e5bcab4f1f2a9664a10a75e7feb1777af8261b44
scheduling/webhook_providers.py: 6a4899d95483089e99843529b51ac5b2cf7bed13ccc4366d82cb371ad3bf8a18
```

## Tests deferred

Tools tests (10 files) require `application.services.{payment_state_service,meeting_state_service}` which T-13 lifts. Expected per DAG.

`test_payment_provider_strategy.py` partially ran: **9 passed, 1 failed** (the 1 failure imports `application.services.payment_state_service` — expected dependency on T-13).

Tests will run GREEN post T-13 (application/services lift).

## Invariants verified

| Invariant | Status | Evidence |
|---|---|---|
| AISALESHT UNTOUCHED (V-NF-4) | ✅ | git status of AISALESHT clean |
| Zero top-level `from src.*` leaks (V-AG-1) | ✅ | grep returns empty |
| Deferred scheduling imports preserved inside method bodies | ✅ | 6 imports lines 217-346 in scheduling/providers.py remain `^\s+from luana_core_*` |
| V-AG-2: zero top-level `luana_core_scheduling.*` imports | ✅ | grep `^from luana_core_scheduling` returns empty in src/ |
| §3 sha256 captured for T-18 | ✅ | webhook_providers.py hashes documented |
| AST parse OK | ✅ | python ast.parse() success on 10 files |
| ruff check + format clean | ✅ | "All checks passed!" |
| Test scheduling imports rewritten + remain method-body | ✅ | `luana_core_scheduling.*` only indented |

## Files created (luana-platform)

### src — 10 files
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/registry.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/tools.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/providers.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/payment/webhook_providers.py (§3)
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/scheduling/__init__.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/scheduling/tools.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/scheduling/providers.py
- core/luana-core-sales-agent/src/luana_core_sales_agent/application/tools/scheduling/webhook_providers.py (§3)

### tests — 13 files (incl 3 __init__.py)
- core/luana-core-sales-agent/tests/application/tools/__init__.py
- core/luana-core-sales-agent/tests/application/tools/test_tools.py
- core/luana-core-sales-agent/tests/application/tools/payment/__init__.py
- core/luana-core-sales-agent/tests/application/tools/payment/test_create_payment_link.py
- core/luana-core-sales-agent/tests/application/tools/payment/test_grant_access_idempotent.py
- core/luana-core-sales-agent/tests/application/tools/payment/test_payment_provider_strategy.py
- core/luana-core-sales-agent/tests/application/tools/payment/test_payment_state_service.py
- core/luana-core-sales-agent/tests/application/tools/payment/test_verify_payment_status.py
- core/luana-core-sales-agent/tests/application/tools/scheduling/__init__.py
- core/luana-core-sales-agent/tests/application/tools/scheduling/test_internal_scheduler_provider.py
- core/luana-core-sales-agent/tests/application/tools/scheduling/test_meeting_state_service.py
- core/luana-core-sales-agent/tests/application/tools/scheduling/test_scheduler_webhook_dedup.py
- core/luana-core-sales-agent/tests/application/tools/scheduling/test_scheduling_tools.py

### Modified
- core/luana-core-sales-agent/pyproject.toml (added per-file-ignores for payment/providers.py forward-refs)

## Validators addressed

- V-NF-2: zero `from src.*` cross-module leaks at top-level ✅
- V-F-tools-registry: registry.py + payment/scheduling provider strategy preserved verbatim ✅
- V-AG-2 prep: NO top-level scheduling imports in src ✅
- V-AG-8 prep: 2 §3 sha256 baselines captured ✅

## Commit

```
c2fbae1 feat(luana-core-sales-agent): lift application tools (registry + payment + scheduling provider strategy + §3 2 webhook adapters hash-stable + deferred scheduling imports per §9.2)
```
