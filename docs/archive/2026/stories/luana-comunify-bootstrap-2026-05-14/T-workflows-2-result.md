# T-workflows-2 Result — `CohortEnrollmentWorkflow + DunningWorkflow embedded` LangGraph

**Ticket:** T-workflows-2 — CohortEnrollmentWorkflow + embedded DunningWorkflow LangGraph
**Surface:** AGENTIC, production_code=true, **Opus 4.7 EXCLUSIVE** (R23)
**Date:** 2026-05-14
**State:** `tests-passing` (awaiting orchestrator → gate-runner → auditor-agentic)
**Validators required:** V-AE-10 + V-F-10
**Decisions applicable:** D3 (StateGraph direct), D10 (RedisSaver), D19 (Dunning embedded)

---

## § 1. Outcome

**28 new unit + e2e tests** GREEN on first complete run after one
anti-loop guard fix.

```
tests/agentic_evals/workflows/test_cohort_enrollment_cron.py .......      [ 15%]
tests/agentic_evals/workflows/test_cohort_enrollment_dunning.py ......    [ 29%]
tests/agentic_evals/workflows/test_cohort_enrollment_resume.py ..         [ 34%]
tests/agentic_evals/workflows/test_cohort_enrollment_workflow_smoke.py ....... [ 50%]
tests/agentic_evals/workflows/test_community_engagement_*.py ...............    [ 86%]
tests/e2e/test_subscription_recurring_dunning_e2e.py ......                    [100%]
====================== 44 passed in 0.80s ======================
```

**Full comunify backend regression:** 628 passed, 9 skipped, 0 failed
(was 600/9 before T-workflows-2; +28 new tests, zero regression of
T-workflows-1 / T-be-7 / T-payment-1 / T-tools-* prior surface).

Ruff lint + format on scoped files: clean.

---

## § 2. Files created

| Path | Lines | Role |
|---|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/cohort_enrollment_workflow.py` | ~620 | LangGraph 2.0 StateGraph + 7 nodes + 5 routing fns + 3 callable Protocols + factory + checkpointer abstraction + embedded DunningWorkflow sub-state machine |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_workflow_smoke.py` | ~420 | 7 smoke tests — happy path qualification → enrolled, no_fit, rejected, expired retry, expired drop, cost budget, tenant isolation |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_dunning.py` | ~420 | 6 dunning embedded tests — past_due entry, retry_1 success, escalate retry_1 fail → retry_2 fail → suspended → cancelled, retry_2 success after retry_1 fail, graceful-degradation, no tool wired degraded mode |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_resume.py` | ~210 | 2 resume tests — state reconstruction across workflow instances, mid-dunning sub-state preservation |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_cohort_enrollment_cron.py` | ~260 | 7 cron handler tests — all 5 handlers registered, descriptor cron rule contract, payment_followup_24h tick, dunning_retry_1 tick invokes retry tool, graceful-degradation (factory raise + state_loader raise), suspend tick |
| `/home/chris/luana-platform/comunify/backend/tests/e2e/test_subscription_recurring_dunning_e2e.py` | ~340 | 6 V-F-10 e2e tests — subscription create wires dunning stub, payment fails → embedded dunning, retry_1 success → enrolled, retry exhausted → cancelled, tenant isolation per lead, DunningService transition_status integration |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-workflows-2-impl-log.md` | this file | Impl-log (skills consulted, anti-duplication audit, plan, quality gates, R3 scope) |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-workflows-2-result.md` | this file | Result |

## § 3. Files modified (APPEND only — parallel-safety M8 + anti-duplication §0)

| Path | Change |
|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/module_registry_entry.py` | Appended `comunify_cohort_enrollment_descriptor` instance per arch § 6.6 (5 CronRules + workflow_slug + cost_budget=0.20 USD). One docstring tense update ("will EXTEND" → "EXTENDS"). T-workflows-1 `comunify_community_engagement_descriptor` untouched. |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/cron_handler.py` | Appended `_invoke_cohort_enrollment_tick` DRY helper + 5 `@register_cron_handler` decorators (payment_followup_24h / payment_followup_48h / dunning_retry_1 / dunning_retry_2 / dunning_suspend). T-workflows-1 `handle_community_engagement_drift_check` untouched. |

No files outside ticket `files_in_scope` modified.

---

## § 4. Validator V-AE-10 status

```yaml
- id: V-AE-10
  category: agentic_eval
  type: pytest
  cmd: "cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/workflows/ -v --tb=short"
  must_pass: true
  timeout_sec: 600
  description: "CommunityEngagementWorkflow + CohortEnrollmentWorkflow state machines + transitions + resume from checkpoint"
```

**Status:** **GREEN — 38/38 passed**.
- T-workflows-1 contributed 16 tests (community_engagement) — preserved
- T-workflows-2 contributes 22 tests (cohort_enrollment + embedded dunning + cron handlers + resume)
- 0 failures, 0 skips

## § 5. Validator V-F-10 status

```yaml
- id: V-F-10
  category: functional
  type: pytest
  cmd: "cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/e2e/test_subscription_recurring_dunning_e2e.py -v"
  must_pass: true
  timeout_sec: 180
  scenario_id: "spec § 3.4 subscription recurring + dunning"
```

**Status:** **GREEN — 6/6 passed**. All scenarios:
- F1: subscription create wires DunningWorkflow stub
- F2: cohort payment failure → embedded dunning past_due
- F3: retry_1 success → enrolled e2e
- F4: retry exhausted → suspended → cancelled e2e
- F5: tenant isolation per lead (dunning state isolated)
- F6: DunningService.transition_status integration sanity

---

## § 6. Key invariants validated

| Invariant | Validating test(s) |
|---|---|
| State machine: qualification → discovery_call → terms → payment → enrolled (happy path) | `test_smoke_happy_path_qualification_to_enrolled` |
| Qualification no_fit → END (no discovery booking) | `test_qualification_no_fit_terminates` |
| Terms rejected → END (no payment) | `test_terms_rejected_terminates` |
| Payment expired with retry available → returns to payment_pending | `test_payment_expired_retry_then_succeeds` |
| Payment expired retry exhausted → drop → END | `test_payment_expired_drops_after_retry_exhausted` |
| Cost budget per workflow run ≤ $0.20 USD | `test_cost_budget_under_ceiling` |
| Tenant isolation (composite thread_id tenant_id:lead_id) | `test_distinct_lead_ids_isolate_state` + `test_dunning_state_isolated_per_lead` |
| Embedded DunningWorkflow past_due entry sets anchor | `test_payment_failed_enters_dunning_past_due` |
| Dunning retry_1 success → exit to enrolled | `test_dunning_retry_1_success_recovers_to_enrolled` |
| Dunning retry_1 fail → retry_2 fail → suspend → cancel | `test_dunning_escalates_to_suspended_then_cancelled` |
| Dunning retry_2 success after retry_1 fail → enrolled | `test_dunning_retry_2_succeeds_after_retry_1_failed` |
| Graceful-degradation: retry tool exception → state advances | `test_dunning_handles_retry_tool_exception_gracefully` |
| Degraded mode: no retry tool wired → deterministic state advancement | `test_dunning_without_retry_tool_degrades_deterministically` |
| Resume from checkpoint reconstructs state | `test_resume_from_checkpoint_reconstructs_state` |
| Resume preserves embedded dunning sub-state | `test_resume_mid_dunning_preserves_substate` |
| All 5 cron handlers registered | `test_all_cron_handlers_registered_for_cohort_enrollment` |
| Descriptor publishes 5 cron rules + cost budget 0.20 + 4 eligible niches | `test_module_descriptor_publishes_cohort_enrollment_cron_rules` |
| payment_followup_24h cron tick advances workflow | `test_payment_followup_24h_tick_advances_workflow` |
| dunning_retry_1 cron tick fires retry_tool | `test_dunning_retry_1_tick_invokes_retry_tool` |
| Cron handler returns None on workflow factory failure (graceful-degradation Rule 5) | `test_payment_followup_24h_returns_none_on_workflow_failure` |
| Cron handler returns None on state_loader failure | `test_dunning_retry_2_returns_none_when_state_loader_raises` |
| dunning_suspend cron tick sets suspended state | `test_dunning_suspend_tick_sets_suspended_state` |
| Subscription create wires DunningWorkflowProtocol stub (e2e D14) | `test_subscription_create_wires_dunning_workflow_stub` |
| DunningService.transition_status integrates via protocol (e2e) | `test_dunning_service_transition_status_e2e` |

---

## § 7. Anti-loop guard

`payment_expired` node ALWAYS increments `payment_expired_retry_count` on
entry AND clears `payment_status=None` (defense-in-depth). `route_after_expired`
reads bumped count: `<=1 → retry, >=2 → drop`. This pattern follows
tessl__langgraph guidance "always have exit conditions + max iter counter".

The fix was caught by `test_payment_expired_retry_then_succeeds` failing
with an infinite loop on the initial implementation (payment_pending
re-routed back to payment_expired on every iteration). Single targeted fix
in node + routing got the suite GREEN.

---

## § 8. Quality gates (all green)

| Gate | Cmd | Result |
|---|---|---|
| Ruff lint scoped | `.venv/bin/ruff check src/...workflows/ src/...module_registry_entry.py tests/agentic_evals/workflows/test_cohort_enrollment_*.py tests/e2e/test_subscription_recurring_dunning_e2e.py --no-cache` | **clean** |
| Ruff format scoped | `.venv/bin/ruff format --check ...` | **clean** (auto-format applied) |
| V-AE-10 | `.venv/bin/pytest tests/agentic_evals/workflows/ -v --tb=short` | **38 passed** |
| V-F-10 | `.venv/bin/pytest tests/e2e/test_subscription_recurring_dunning_e2e.py -v` | **6 passed** |
| Full backend regression | `.venv/bin/pytest -x -q --tb=short` | **628 passed, 9 skipped, 0 failed** |

---

## § 9. Decisions honored

- **D3** — CohortEnrollmentWorkflow inherits `langgraph.graph.StateGraph` directly. NO shared `BaseWorkflowOrchestrator` (per arch § 1 tradeoff: 3 workflows total < 4+ threshold for shared lift).
- **D10** — RedisSaver checkpointer target documented in descriptor `state_persister="redis_saver"`. Runtime swap transparent via `CheckpointerProtocol` (structural). MemorySaver in tests/dev.
- **D19** — DunningWorkflow EMBEDDED in CohortEnrollmentWorkflow (single StateGraph). dunning sub-state machine inside `payment_failed_dunning` node — `dunning_state` field encodes: None → past_due → retry_N_pending → suspended → cancelled. Simpler operational complexity vs sibling DunningWorkflow class.

---

## § 10. R23 compliance (Opus 4.7 mandatory production AGENTIC code)

| Criterion | Status |
|---|---|
| Production code path | ✅ comunify/copilot/workflows/ runtime + comunify/copilot/module_registry_entry.py descriptor + comunify/copilot/workflows/cron_handler.py decorators |
| Surface AGENTIC | ✅ |
| Opus 4.7 worker | ✅ this ticket |
| All quality gates green | ✅ |

---

## § 11. Next steps (T-eval-1 dependency)

T-workflows-2 unblocks T-eval-1 per 06-tickets.yaml dependency graph.
T-eval-1 will:
- Wire production tool callables (qualify_for_cohort + book_discovery_call + payment_retry adapter) into the workflow factory via partial application at the cron handler / orchestrator call site
- Add grader rubric runs against the workflow on personas (vertical-creator-economy-fidelity rubric v1)
- Validate end-to-end pass^k against personas (cohort_enrollment happy + dunning recovery + dunning escalate to suspended)

---

## § 12. Last line return (anti-telephone-game)

<!-- @pm: build phase done (state: tests-passing). Files: 6 created + 2 modified APPEND. Native ticket tests: 44/44 PASS (V-AE-10: 38/38, V-F-10: 6/6). Full regression 628/9 pass/skip 0 fail. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->

done -> docs/product/stories/luana-comunify-bootstrap/T-workflows-2-result.md
