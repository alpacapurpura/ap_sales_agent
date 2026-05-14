# T-workflows-2 Impl-Log — `CohortEnrollmentWorkflow + DunningWorkflow embedded`

**Ticket:** T-workflows-2 — CohortEnrollmentWorkflow + embedded DunningWorkflow LangGraph
**Surface:** AGENTIC, production_code=true, **Opus 4.7 EXCLUSIVE** (R23)
**Date:** 2026-05-14
**Estimate:** 5h
**Decisions applicable:** D3 (StateGraph direct inheritance), D10 (RedisSaver), D19 (Dunning embedded in CohortEnrollment)
**Depends on:** T-be-7 (services) ✅ + T-payment-1 (adapters) ✅ + T-tools-1 (qualify_for_cohort) ✅
**Blocks:** T-eval-1

---

## § 1. Skills Consulted (Step 0 Gate)

| Skill | Reason | Decision applied |
|---|---|---|
| **copilot-expert** | LangGraph StateGraph patterns, checkpointer abstraction (D10), shared-abstractions inventory (anti-duplication §0), observability best-effort writes | Reused T-workflows-1 patterns: entry router pattern, closure-bound nodes, `_NODE_COST_USD` registry, graceful-degradation Rule 5 try/except on every tool invocation. NO shared `BaseWorkflowOrchestrator` — direct StateGraph (D3 YAGNI). |
| **sales-agent-expert** | Anti-duplication §0 cardinal — pre-write grep cross-codebase, ensure no mirror cross-module | Pre-write grep `class CohortEnrollmentWorkflow|class DunningWorkflow|build_cohort_enrollment_workflow|build_dunning_workflow` cross /home/chris/luana-platform/ + /home/chris/AISALESHT/backend/ → only stub Protocols in subscription_service.py + dunning_service.py. NEW workflow approved. Decision: EMBEDDED dunning (D19) inside CohortEnrollment node — single StateGraph, simpler checkpointing, no parallel workflow class. |
| **tessl__langgraph** | StateGraph + reducers + conditional edges + checkpointer compile contract + ALWAYS-HAVE-EXIT invariant | All conditional edges terminate explicitly (END branches for no_fit, rejected, drop, cancelled, wait-park). Max-iter implicit via cron tick boundary (workflow parks → returns control to scheduler). Entry router pattern dispatches per `current_step` (LangGraph requires single entry_point + state-driven dispatch). |
| **tessl__graceful-degradation** | Every external callable (qualify_tool / book_discovery_tool / payment_retry_tool) needs timeout-like wrapping + per-dependency fallback + log structured context | Each tool injection wrapped in try/except with structlog warning + deterministic state advancement (qualify exception → fit=False, book exception → booking_id=None, retry exception → advance dunning state as failed). NO timeouts at workflow boundary because tool callables themselves should manage that (their httpx clients carry the timeout per tool docstring). |
| **tessl__pytest-api-testing** | Fixture organization (function scope default), factory fixtures, parametrize for edge cases | Created factory fixtures `*_stub` that capture call args for assertion. Each test has function-scoped MemorySaver (isolation). Tested error paths explicitly (exploding stubs for graceful-degradation validation). |

---

## § 2. Anti-duplication audit (Step 0 + cross-module grep)

```bash
$ grep -rln "class CohortEnrollmentWorkflow|class DunningWorkflow|build_cohort_enrollment_workflow|build_dunning_workflow" \
    /home/chris/luana-platform/ /home/chris/AISALESHT/backend/
# /home/chris/luana-platform/comunify/backend/src/modules/comunify/application/services/subscription_service.py
# /home/chris/luana-platform/comunify/backend/src/modules/comunify/application/services/dunning_service.py
```

Only matches are **stub `DunningWorkflowProtocol`** definitions in T-be-7
service files. No real workflow class exists. NEW workflow approved.

Per `.claude/rules/anti-duplication.md` SSoT, the **new** files do NOT
mirror anything in shared/ — they extend LangGraph's `StateGraph` directly
(D3 staging — defer shared `BaseWorkflowOrchestrator` until 4th workflow
appears; comunify will have 2 + vitalia has 1 = 3 total).

---

## § 3. Cross-module systems audit (NO-NEW-LAYER)

The implementation REUSES existing primitives:
- `langgraph.graph.StateGraph` + `END` from runtime dependency (T-workflows-1 added)
- `langgraph.checkpoint.memory.MemorySaver` for tests
- T-workflows-1 `WorkflowDescriptor` + `CronRule` dataclasses (extends file via APPEND only)
- T-workflows-1 `register_cron_handler` decorator + local `_COMUNIFY_CRON_HANDLERS` registry
- T-tools-1 `QualifyForCohortInputV1` / `QualifyForCohortOutputV1` shapes (callable protocol mirrors subset of return dict)
- T-tools-4 `BookDiscoveryCallInputV1` / `BookDiscoveryCallOutputV1` shapes
- T-payment-1 `ComunifyTokenizedRecurringAdapter.charge_installment` (production wiring binds via partial — out-of-scope for this ticket)
- T-be-7 `SubscriptionService.create_subscription` + `DunningService.transition_status` (e2e test integration)

NO new shared layer. NO new local infrastructure. NO new state-machine
abstraction. Compositional reuse of T-workflows-1 + existing tools.

---

## § 4. Plan (executed)

1. ✅ Step 0 GATE: skills invocations + anti-duplication grep + decisions captured
2. ✅ Pre-flight reads: 06-tickets.yaml T-workflows-2 section + 03-arch-agentic.md § 6.2 state machine + § 6.5 cron schedule + § 6.6 descriptor + T-workflows-1 result + community_engagement_workflow.py pattern source + subscription_service.py / dunning_service.py service interfaces + tokenized_recurring_adapter signatures + qualify_for_cohort / book_discovery_call tool signatures
3. ✅ Created `cohort_enrollment_workflow.py` (~620 LOC):
   - `CohortEnrollmentState` TypedDict with `tenant_id` always + iteration guard + embedded dunning sub-state fields
   - 7 nodes: qualification / discovery_call_scheduled / terms_presentation / payment_pending / payment_expired / enrolled / payment_failed_dunning (embeds DunningWorkflow per D19)
   - 5 routing functions: route_from_entry / route_after_qualification / route_after_terms / route_after_payment / route_after_expired / route_dunning_state
   - 3 callable Protocols: QualifyForCohortCallableProtocol / BookDiscoveryCallCallableProtocol / PaymentRetryCallableProtocol
   - `build_cohort_enrollment_workflow(checkpointer, *, qualify_tool, book_discovery_tool, payment_retry_tool)` factory
4. ✅ Extended `module_registry_entry.py` (APPEND only):
   - Added `comunify_cohort_enrollment_descriptor` instance per arch § 6.6
   - 5 CronRules: payment_followup_24h / payment_followup_48h / dunning_retry_1 / dunning_retry_2 / dunning_suspend
   - cost_budget_per_workflow_run=0.20 USD
5. ✅ Extended `cron_handler.py` (APPEND only):
   - Shared `_invoke_cohort_enrollment_tick` helper (DRY across 5 handlers)
   - 5 cron handlers registered via `@register_cron_handler` decorator
   - All wrap in try/except (graceful-degradation Rule 5)
6. ✅ Created 4 test files (28 new tests):
   - `test_cohort_enrollment_workflow_smoke.py` — 7 tests (happy path + edge transitions + cost budget + tenant isolation)
   - `test_cohort_enrollment_dunning.py` — 6 tests (embedded DunningWorkflow state machine: past_due → retry_1 → retry_2 → suspended → cancelled + recovery paths + graceful-degradation)
   - `test_cohort_enrollment_resume.py` — 2 tests (checkpointer-based state resume across workflow instances)
   - `test_cohort_enrollment_cron.py` — 7 tests (handler registration + descriptor contract + happy path tick + graceful-degradation)
7. ✅ Created `tests/e2e/test_subscription_recurring_dunning_e2e.py` — 6 tests (V-F-10 scenarios end-to-end)
8. ✅ Quality gates: ruff check clean, ruff format applied, V-AE-10 GREEN, V-F-10 GREEN, full regression 628/9 pass/skip (0 fail vs T-workflows-1 baseline 600/9)

---

## § 5. Anti-loop guard story

Initial implementation had a subtle bug: `payment_expired` node returned
state without clearing `payment_status="expired_48h"`, causing infinite loop
on the `payment_expired → payment_pending (retry) → payment_expired` cycle.

**Fix (anti-loop, defense-in-depth):**
- `payment_expired_node` ALWAYS increments `payment_expired_retry_count` on entry
- AND clears `payment_status=None` to prevent the next `payment_pending` evaluation from re-routing back to expired
- `route_after_expired` reads the bumped count: `<=1 → retry, >=2 → drop`

Test `test_payment_expired_retry_then_succeeds` validates the retry path.
Test `test_payment_expired_drops_after_retry_exhausted` validates the drop
path (seeds retry_count=1 → node bumps to 2 → route drops).

This pattern mirrors LangGraph 2.0 + tessl__langgraph guidance: "Always
have exit conditions. Max iterations counter in state. Clear END
conditions in routing." Implemented at the state-mutation level (counter
bump) + routing level (threshold check) for defense-in-depth.

---

## § 6. Embedded DunningWorkflow (D19) — design notes

Per D19 ratification + arch § 6.2, the DunningWorkflow is **embedded** in
the CohortEnrollmentWorkflow rather than a sibling workflow class. The
`payment_failed_dunning` node carries a `dunning_state` sub-field that
encodes the dunning sub-machine:

```
None → past_due (first entry, anchor dunning_first_failure_at)
past_due → retry_1_pending (retry_count=1, fail)
past_due → None (retry_count=1, success → exit to enrolled)
retry_1_pending → retry_2_pending (retry_count=2, fail)
retry_1_pending → None (retry_count=2, success → exit to enrolled)
retry_2_pending → suspended (+14d cumulative)
suspended → cancelled → END
```

**Tradeoff accepted:** state space grows by 5 sub-states inside one node.
Benefit: single workflow class + single checkpoint thread per
(tenant_id, lead_id) — simpler cron orchestration + simpler resume
semantics. The alternative (sibling DunningWorkflow class) would have
required cross-workflow state handoff via persistent events, doubling
operational complexity.

Routing function `route_dunning_state` decides:
- `dunning_state is None` (retry succeeded) → exit to `enrolled` node
- `dunning_state == "cancelled"` → exit via END
- All other sub-states (`past_due` / `retry_1_pending` / `retry_2_pending` / `suspended`) → park, wait next cron tick

---

## § 7. Cron handlers cadence (per arch § 6.5 + 6.6)

| Handler name | Trigger cadence | What it does |
|---|---|---|
| `comunify.cohort_enrollment.payment_followup_24h` | +24h since payment_pending entered | Re-invokes workflow at `payment_pending` (friendly reminder; outbound message compose deferred to T-eval-1) |
| `comunify.cohort_enrollment.payment_followup_48h` | +48h since payment_pending entered | Signals `payment_status="expired_48h"` → workflow routes to `payment_expired` |
| `comunify.cohort_enrollment.dunning_retry_1` | +3d from first failure | Signals `dunning_retry_count=1` → workflow fires `payment_retry_tool(retry_attempt=1)` |
| `comunify.cohort_enrollment.dunning_retry_2` | +7d cumulative from first failure | Signals `dunning_retry_count=2` → workflow fires `payment_retry_tool(retry_attempt=2)` |
| `comunify.cohort_enrollment.dunning_suspend` | +14d cumulative from first failure | Signals `dunning_state="suspended"` |

All 5 handlers share `_invoke_cohort_enrollment_tick` helper (DRY). All
wrapped in try/except for graceful-degradation Rule 5 — single failed tick
does NOT crash worker (returns None for outbox retry).

---

## § 8. Tenant isolation invariant

State carries `tenant_id` + `lead_id`. Checkpointer thread_id composes
`f"{tenant_id}:{lead_id}"` per arch § 6.4. Test
`test_distinct_lead_ids_isolate_state` validates two distinct lead_ids in
same tenant correctly persist to separate threads + diverge in state
(lead_a advances to `payment_pending`, lead_b stuck at
`terms_presentation`). E2E test `test_dunning_state_isolated_per_lead`
validates the dunning sub-state similarly.

---

## § 9. Cost accumulator + budget validation

Per arch § 6.6 `cost_budget_per_workflow_run=0.20 USD`. The happy-path
run (`qualification + discovery + terms + payment + enrolled`) accumulates
~$0.020 USD from stub contributions:
- qualification: $0.012 (Sonnet fit assessment) + tool extra_cost
- discovery_call_scheduled: $0.0 (no LLM)
- terms_presentation: $0.008 (Sonnet terms compose)
- payment_pending / payment_expired / enrolled: $0.0
- payment_failed_dunning: $0.001 cron probe + adapter extra_cost

Plus tool extra_cost (`cost_usd` from each stub) accumulates: qualify
$0.010 + book $0.0 + retry $0.0 ≈ $0.010-0.020 total per happy path.

Worst-case escalation path (qualified + booked + terms + payment fail +
retry_1 fail + retry_2 fail + suspend + cancel) ≈ $0.025 USD — still well
under $0.20 ceiling.

Test `test_cost_budget_under_ceiling` validates against the descriptor's
`cost_budget_per_workflow_run` constant.

---

## § 10. Quality gates

- [x] `cd /home/chris/luana-platform/comunify/backend && .venv/bin/ruff check src/modules/comunify/copilot/workflows/ src/modules/comunify/copilot/module_registry_entry.py tests/agentic_evals/workflows/test_cohort_enrollment_*.py tests/e2e/test_subscription_recurring_dunning_e2e.py --no-cache` → **clean**
- [x] `cd /home/chris/luana-platform/comunify/backend && .venv/bin/ruff format --check ...` → **clean** (auto-format applied where needed)
- [x] V-AE-10 cmd: `cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/workflows/ -v --tb=short` → **38/38 passed** (16 community_engagement T-workflows-1 + 22 cohort_enrollment T-workflows-2)
- [x] V-F-10 cmd: `cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/e2e/test_subscription_recurring_dunning_e2e.py -v` → **6/6 passed**
- [x] Full comunify backend regression: **628 passed, 9 skipped, 0 failed** (was 600/9 before this ticket = +28 new tests, zero regression of prior surface)

---

## § 11. Files touched (final)

### Created

| Path | Lines | Role |
|---|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/cohort_enrollment_workflow.py` | ~620 | LangGraph StateGraph + 7 nodes + 5 routing fns + 3 callable Protocols + factory + checkpointer abstraction |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_workflow_smoke.py` | ~420 | 7 smoke tests (happy + no_fit + rejected + expired retry + cost budget + tenant isolation + drop after exhausted) |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_dunning.py` | ~420 | 6 dunning embedded tests (past_due / retry_1 success / escalate to cancelled / retry_2 success after retry_1 fail / graceful-degradation / no tool wired) |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_resume.py` | ~210 | 2 resume tests (state reconstruction + mid-dunning state preservation) |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_cron.py` | ~260 | 7 cron handler tests (registration + descriptor contract + tick happy paths + graceful-degradation) |
| `/home/chris/luana-platform/comunify/backend/tests/e2e/test_subscription_recurring_dunning_e2e.py` | ~340 | 6 V-F-10 e2e tests (SubscriptionService wires DunningWorkflow stub + payment failure embedded dunning + retry success/exhausted + tenant isolation + DunningService transition_status) |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-workflows-2-impl-log.md` | this file | Impl-log |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-workflows-2-result.md` | TBD | Result |

### Modified (APPEND only — no replace/destroy per anti-duplication §0 + parallel-safety M8)

| Path | Change |
|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/module_registry_entry.py` | Appended `comunify_cohort_enrollment_descriptor` instance (5 CronRules + cost_budget 0.20). Updated docstring "T-workflows-2 will EXTEND" → "T-workflows-2 EXTENDS". |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/cron_handler.py` | Appended 5 cohort enrollment cron handlers + shared `_invoke_cohort_enrollment_tick` helper. Community engagement handler unchanged. |

No files modified outside the ticket files_in_scope.

---

## § 12. R3 downstream regression scope

Per `.claude/rules/auditor-downstream-regression.md` cross-codebase
ratchet, this ticket modifies:
- `comunify/backend/src/modules/comunify/copilot/workflows/cohort_enrollment_workflow.py` (NEW)
- `comunify/backend/src/modules/comunify/copilot/module_registry_entry.py` (APPEND)
- `comunify/backend/src/modules/comunify/copilot/workflows/cron_handler.py` (APPEND)

03-arch-agentic.md § 16 already lists these surfaces with downstream test
paths:

| Surface modified | Downstream tests run |
|---|---|
| `comunify/.../copilot/workflows/CohortEnrollmentWorkflow` | `tests/agentic_evals/workflows/test_cohort_enrollment_*.py` (22 tests) → **GREEN** |

Plus full regression `cd /home/chris/luana-platform/comunify/backend &&
.venv/bin/pytest -x -q` 628/9 pass/skip confirms no cross-surface
regression vs T-workflows-1 baseline.

---

## § 13. Decisions honored

- **D3** — CohortEnrollmentWorkflow inherits `langgraph.graph.StateGraph` directly. NO shared `BaseWorkflowOrchestrator` (defer per arch § 1 tradeoff — 2 workflows in comunify + 1 in vitalia = 3 total; threshold for shared lift is 4+).
- **D10** — RedisSaver checkpointer target documented in descriptor (`state_persister="redis_saver"`). Runtime swap via `CheckpointerProtocol` (structural) — MemorySaver works in tests/dev, RedisSaver / AsyncPostgresSaver swap-in when `langgraph-checkpoint-redis` package install lands (transparent to workflow code).
- **D19** — DunningWorkflow EMBEDDED in CohortEnrollmentWorkflow (single StateGraph). Per arch § 6.2 + module docstring rationale.

---

## § 14. R23 compliance (Opus 4.7 mandatory production AGENTIC code)

- Production code path: ✅
- Surface AGENTIC: ✅ (copilot/workflows + extension points future)
- Opus 4.7 worker: ✅ (this ticket)
- All quality gates green: ✅

---

## § 15. Last line return (anti-telephone-game)

`done -> docs/product/stories/luana-comunify-bootstrap/T-workflows-2-result.md`
