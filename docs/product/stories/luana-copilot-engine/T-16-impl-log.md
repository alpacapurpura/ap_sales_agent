# T-16 — Implementation Log

**Ticket:** UNLIFT Stories 2-5 copilot_provider/ subfolders (22 src + 4 tests + offer_ai.py — 27 files)
**Owner:** builder-agentic (Opus 4.7) — R23 mandatory
**Status:** done
**Estimate:** 90min · **Actual:** ~80min

## Skills Consulted

- `copilot-expert` — confirmed registry SSoT pattern + ModuleDescriptor discovery + brand-agnostic engine + no-mirror observability + cross-module ports
- `sales-agent-expert` — n/a (no sales_agent touch — verified via grep)
- `tessl__langgraph` — n/a (no LangGraph state changes — UNLIFT preserves verbatim)
- `tessl__graceful-degradation` — n/a (no new external calls)
- `tessl__pytest-api-testing` — fixture migration patterns for cross-coupling tests
- `tessl__fastapi` — n/a (offer_ai.py is verbatim FastAPI router lift, no changes)
- `.claude/rules/anti-duplication.md` — verified zero mirror created in copilot_provider/ (per D-T6 cardinal)
- `.claude/rules/auditor-downstream-regression.md` — V-F-py-2 baseline comparison (pre/post stash check)

## Step 0 GATE — Skill invocation summary

Each skill was loaded via Skill tool slash command at session start. Decisions captured:
- copilot-expert §1 + §3 + §10: NO new abstractions, EXTEND from luana_core_copilot.domain.ports
- sales-agent-expert §0: anti-duplication cardinal verified zero new mirrors
- tessl__langgraph: NO graph changes (UNLIFT is file-only relocation)

## Step 0.5 — Default flip detection

NOT APPLICABLE — T-16 does not modify any flag defaults in core/config.py. Pure file UNLIFT.

## Cross-module audit — NO-NEW-LAYER

Verified before UNLIFT:
- `luana_core_copilot.domain.ports` exposes `BaseCopilotProvider`, `DataAccessProvider`, `ModuleData`, `WorkflowProvider`, `DataQueryPlan`, `DataQueryResult` — all needed by Stories 2-5 copilot_provider/ subfolders. EXTEND not REPLACE.
- `luana_core_copilot.domain.workflow` exposes `NodeOutput` + workflow base classes — consumed by workflow_handlers.py.
- `luana_core_copilot.application.services.offer_psychology_service.CopilotOfferPsychologyService` consumed by offer-studio api/offer_ai.py.

## Implementation

### Phase 1 — UNLIFT 8 packages copilot_provider/ (22 src files)

For each Story 2-5 package, applied:
1. `mkdir -p .../copilot_provider/`
2. `cp` from AISALESHT verbatim
3. Apply unified sed mapping per 05-guidelines.md §1.3:
   - `src.modules.{brand,offer,crm,...}` → `luana_core_{brand_studio,offer_studio,crm,...}`
   - `src.modules.copilot` → `luana_core_copilot`
   - `src.modules.iam` → `luana_core_iam`
   - `src.modules.assets` → `luana_core_assets`
   - `src.shared.agent_observability.channels` → `luana_core_channels`
   - `src.shared.agent_observability` → `luana_core_observability`
   - `src.shared.domain_events` → `luana_core_events`
   - `src.shared.idempotency` → `luana_core_idempotency`
   - `src.shared.billing` → `luana_core_billing`
   - `src.shared.infrastructure.llm` → `luana_core_llm`
   - `src.shared.{domain,links,infrastructure,application,workers,api}` → `luana_core_platform.X`
   - `src.core` → `luana_core_platform.core`

Packages unlifted:
- brand-studio: 8 files (`__init__.py`, `context_inject.py`, `module_data.py`, `provider.py`, `summary.py`, `tools.py`, `workflow_handlers.py`, `workflows.py`)
- offer-studio: 5 files (`__init__.py`, `data_access.py`, `provider.py`, `workflow_handlers.py`, `workflows.py`) + 1 file `api/offer_ai.py`
- crm: 3 files (`__init__.py`, `data_access.py`, `provider.py`)
- analytics-engine: 2 files (`__init__.py`, `provider.py`)
- landing: 2 files (`__init__.py`, `provider.py`)
- connections: 2 files (`__init__.py`, `provider.py`)
- commercial-calendar: 2 files (`__init__.py`, `provider.py`)
- social-proof: 2 files (`__init__.py`, `provider.py`)

Verified zero `src.*` import leaks via `grep -rEn "from src\.|import src\."` in all 27 files post-sed.

### Phase 2 — pyproject.toml dependency additions

Added `"luana-core-copilot"` to each of 8 packages' `dependencies` array (Stories 2-5):
- luana-core-brand-studio/pyproject.toml
- luana-core-offer-studio/pyproject.toml
- luana-core-crm/pyproject.toml
- luana-core-analytics-engine/pyproject.toml
- luana-core-landing/pyproject.toml
- luana-core-connections/pyproject.toml
- luana-core-commercial-calendar/pyproject.toml
- luana-core-social-proof/pyproject.toml

Comment per row: `# Story 6 T-16 — copilot_provider/ unlift requires copilot ports`.

### Phase 3 — Lift 4 cross-coupling tests

Lifted from AISALESHT to home packages with sed applied:
- `test_brand_context_injector.py` → brand-studio/tests/
- `test_buyer_persona_fields_dropped_regression.py` → brand-studio/tests/
- `test_worker_emits_summary_and_pills.py` → brand-studio/tests/
- `test_offer_data_access_provider.py` → offer-studio/tests/

### Phase 4 — Fixes encountered during validation

**Fix A — test_offer_data_access_provider.py import:**
Sed left `from tests.modules.offer.conftest import TENANT_A, create_product_model` unchanged (no `src.` prefix). Manually adjusted to `from tests.conftest import TENANT_A, create_product_model` (canonical luana-platform layout).

**Fix B — test_buyer_persona_fields_dropped_regression.py prompt_loader:**
Sed translated `from src.shared.infrastructure.prompts.base import prompt_loader` → `from luana_core_platform.infrastructure.prompts.base import prompt_loader`. However, the platform-level `prompt_loader` has a hardcoded path (`src/modules/copilot/infrastructure/prompts/templates`) that doesn't exist in luana-platform. The luana-core-copilot package has its OWN `prompt_loader` with correct templates_dir (`<package>/infrastructure/prompts/templates`). Manually adjusted the test's import to `from luana_core_copilot.infrastructure.prompts.base import prompt_loader`. This is consistent with the Story 6 architecture — `luana_core_copilot.infrastructure.prompts.base` is the canonical prompt_loader for copilot templates.

NOTE: This is a discovery that `luana_core_platform.infrastructure.prompts.base.prompt_loader` is currently mis-configured for luana-platform layout (a Story 2 pre-existing bug — the hardcoded `templates_dir` should default to repo-relative). Future story may clean this up. Did NOT touch luana_core_platform code per "extend not replace" + scope discipline.

## Validators addressed

| Validator | Status | Evidence |
|---|---|---|
| V-F-py-2 (Stories 2-5 GREEN post-unlift) | PASS (zero regression) | All 8 packages re-tested; analytics-engine pre-existing 17 failed + 10 errors (verified via `git stash` baseline check, **NOT introduced by T-16**) |
| V-F-modules-discovery (T-20 territory) | DEFERRED | Discovery code lifted verbatim (per outcome §7.3); ModuleDescriptor wiring requires entry-points or path adapter — addressed by T-20 |

## Test results (post-T-16)

| Package | Pre-T-16 baseline | Post-T-16 | Δ |
|---|---|---|---|
| brand-studio | 456 passed (Story 5 close) | 459 passed | +3 (cross-coupling tests added) |
| offer-studio | 632 passed, 12 skipped | 633 passed, 12 skipped | +1 (cross-coupling test) |
| crm | 305 passed, 3 skipped | 305 passed, 3 skipped | 0 |
| analytics-engine | 1364 passed, 17 failed, 10 errors, 2 skipped (PRE-EXISTING per git stash) | 1364 passed, 17 failed, 10 errors, 2 skipped | 0 |
| landing | 107 passed, 4 skipped | 107 passed, 4 skipped | 0 |
| connections | 643 passed | 643 passed | 0 |
| commercial-calendar | 36 passed | 36 passed | 0 |
| social-proof | 35 passed | 35 passed | 0 |

**Total post-T-16:** 3582 passed (+4 from cross-coupling tests), 17 failed (PRE-EXISTING), 10 errors (PRE-EXISTING), 21 skipped.

## Files changed

### Modified
- core/luana-core-brand-studio/pyproject.toml (+1 dep)
- core/luana-core-offer-studio/pyproject.toml (+1 dep)
- core/luana-core-crm/pyproject.toml (+1 dep)
- core/luana-core-analytics-engine/pyproject.toml (+1 dep)
- core/luana-core-landing/pyproject.toml (+1 dep)
- core/luana-core-connections/pyproject.toml (+1 dep)
- core/luana-core-commercial-calendar/pyproject.toml (+1 dep)
- core/luana-core-social-proof/pyproject.toml (+1 dep)
- uv.lock (workspace resolve)

### Created
- core/luana-core-brand-studio/src/luana_core_brand_studio/copilot_provider/ (8 files)
- core/luana-core-brand-studio/tests/test_brand_context_injector.py
- core/luana-core-brand-studio/tests/test_buyer_persona_fields_dropped_regression.py
- core/luana-core-brand-studio/tests/test_worker_emits_summary_and_pills.py
- core/luana-core-offer-studio/src/luana_core_offer_studio/copilot_provider/ (5 files)
- core/luana-core-offer-studio/src/luana_core_offer_studio/api/offer_ai.py
- core/luana-core-offer-studio/tests/test_offer_data_access_provider.py
- core/luana-core-crm/src/luana_core_crm/copilot_provider/ (3 files)
- core/luana-core-analytics-engine/src/luana_core_analytics_engine/copilot_provider/ (2 files)
- core/luana-core-landing/src/luana_core_landing/copilot_provider/ (2 files)
- core/luana-core-connections/src/luana_core_connections/copilot_provider/ (2 files)
- core/luana-core-commercial-calendar/src/luana_core_commercial_calendar/copilot_provider/ (2 files)
- core/luana-core-social-proof/src/luana_core_social_proof/copilot_provider/ (2 files)

**Total: 30 files created (22 src + 4 tests + offer_ai.py + 3 crm files).** Counts match architect spec (22 src per ticket — note: crm has 3 files not 2 per actual AISALESHT count; ticket says "2 files" but data_access.py is real third).

## D-T6 cement preserved

Zero new mirrors created — verified post-T-16:
```bash
grep -rE "class (FXResolver|CostCalculator|PricingResolver|BaseObservabilityContext|BaseAgentCallbackHandler)\b" core/luana-core-{brand-studio,offer-studio,crm,analytics-engine,landing,connections,commercial-calendar,social-proof}/src/
# Output: empty (OK)
```

## Followups (NOT for T-16)

- T-17: D-T2 MessageModel stub cleanup (next)
- T-18: integration smoke + aggregate pytest (next)
- T-20: V-F-modules-discovery wiring (entry-points or filesystem adapter) — assessed by `test_module_descriptor_complete_for_lifted_packages.py`
- Future story: `luana_core_platform.infrastructure.prompts.base.prompt_loader` hardcoded `templates_dir` may want repo-relative refactor (out of scope T-16)

## Halt criteria evaluation

None triggered:
- No new circular imports (verified import resolution via uv sync)
- No aggregate pytest non-DAG failures (analytics issues are pre-existing per baseline check)
- Sed left no dangling imports (zero `src.*` leaks)
- Pre-commit hook clean
- Cumulative tool uses within bounds

## Commit

- Repo: `~/luana-platform`
- Branch: main
- See result file for SHA
