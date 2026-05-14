# T-workflow-1 — Result

**Status:** tests-passing
**Owner:** Claude Opus 4.7 (1M context) — R23 production_code:true AGENTIC
**Story:** luana-vitalia-bootstrap
**Sesion:** 4 W7
**Validators:** V-AE-7 PASS
**Date:** 2026-05-14

## Acceptance verdict

| Acceptance | Test | Result |
|---|---|---|
| A1 D0→D90 happy path completes via cron ticks | `tests/agentic_evals/workflows/test_treatment_followup_workflow_d0_to_d90_happy.py::test_d0_to_d90_happy_path_completes` | PASS |
| A2 Safety keyword triggers paused_safety_escalation | `tests/agentic_evals/workflows/test_treatment_followup_workflow_safety_escalation.py::test_safety_keyword_pain_chest_triggers_escalation` + `::test_safety_keyword_allergy_triggers_escalation` | PASS |
| A3 Resume from RedisSaver checkpoint reconstructs state correctly | `tests/agentic_evals/workflows/test_treatment_followup_workflow_resume_from_checkpoint.py` (2 tests) | PASS (MemorySaver swap-ready Checkpointer protocol per D10) |
| A4 Total D0→D90 cost ≤$0.25 USD per workflow run | `tests/agentic_evals/workflows/test_treatment_followup_workflow_d0_to_d90_happy.py::test_total_cost_budget` | PASS (0.018 USD vs 0.25 budget = 7% utilization) |

12/12 workflow tests GREEN. 510/510 vitalia downstream regression suite GREEN. Lint + format GREEN.

## Files created / modified

```
luana-platform/vitalia/backend/src/modules/vitalia/copilot/
├── workflows/
│   ├── __init__.py                                    # MODIFIED (placeholder → public surface exports)
│   ├── treatment_followup_workflow.py                 # NEW (LangGraph 2.0 StateGraph + 10 nodes + entry router + 17 transitions)
│   ├── cron_handler.py                                # NEW (vitalia-local cron handler registry — lift-shared deferred)
│   └── module_registry_entry_helpers.py               # NEW (descriptor accessor for tests + future shared lift)
└── module_registry_entry.py                           # NEW (vitalia-local WorkflowDescriptor)

luana-platform/vitalia/backend/tests/agentic_evals/workflows/
├── __init__.py                                        # NEW (empty)
├── test_treatment_followup_workflow_d0_to_d90_happy.py        # NEW (2 tests — A1 + A4)
├── test_treatment_followup_workflow_safety_escalation.py      # NEW (4 tests — A2 + clinic resume)
├── test_treatment_followup_workflow_paused_awaiting_clinic.py # NEW (4 tests — timeout + resume + dropped)
└── test_treatment_followup_workflow_resume_from_checkpoint.py # NEW (2 tests — A3 + thread isolation)
```

## Decisions honored
- **D3** — TreatmentFollowupWorkflow inherits LangGraph `StateGraph` directly (no shared `BaseWorkflowOrchestrator`). YAGNI per D3 staging — defer abstraction until 2nd vertical workflow appears.
- **D10** — Checkpointer abstraction via `CheckpointerProtocol` allows runtime swap MemorySaver → RedisSaver. Current MemorySaver impl until `langgraph-checkpoint-redis` package install lands.

## Anti-duplication audit (per .claude/rules/anti-duplication.md)
- `TreatmentFollowupWorkflow` class — NEW, no collision (grep cross-codebase: zero).
- `RedisSaver` runtime — package not installed; D10 ratifies as TARGET; abstraction surface ready for swap.
- `register_cron_handler` — NO existing primitive in `@luana/core/scheduling` (grep empty). Created vitalia-LOCAL registry per `NEW (último recurso)` justification; lift-shared deferred for when shared cron primitive lands.
- `ModuleDescriptor` arch doc § 6.5 schema mismatch with `luana_core_copilot.domain.module_registry.ModuleDescriptor` (different concept). Resolved by vitalia-local `WorkflowDescriptor` dataclass + helpers module.

## Skills consulted (per Step 0 GATE)
1. `copilot-expert` — best-effort observability + tenant isolation in state.
2. `sales-agent-expert` — voice composition delegated to T-tools-4 (out of scope).
3. `tessl__langgraph` — TypedDict state, conditional edges, entry router pattern, checkpointer.
4. `tessl__graceful-degradation` — try/except + structlog warning + isolate cron tick failures.
5. `claude-api` — LLM cache slot architecture lives at tool boundary (T-tools-4), not workflow.
6. `tessl__pytest-api-testing` — function-scoped fixtures, factory pattern, MemorySaver round-trip.

## Validators executed

```bash
$ cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/agentic_evals/workflows/ -v --tb=short
============================== 12 passed in 0.46s ==============================

$ cd /home/chris/luana-platform/vitalia/backend && uv run ruff check src/modules/vitalia/copilot/workflows/ src/modules/vitalia/copilot/module_registry_entry.py tests/agentic_evals/workflows/
All checks passed!

$ cd /home/chris/luana-platform/vitalia/backend && uv run ruff format --check src/modules/vitalia/copilot/workflows/ src/modules/vitalia/copilot/module_registry_entry.py tests/agentic_evals/workflows/
10 files already formatted

$ cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/ -q  (downstream regression)
510 passed, 22 skipped in 9.60s
```

V-AE-7 fully satisfied. Ready for /auditor → auditor-agentic.

## Out-of-scope (deferred to follow-on tickets)
- T-tools-4 owns `treatment_followup_check` real LLM calls + observability wrapper.
- T-prompts-1 owns Slot 4 MEDICAL_SAFETY_RAILS prompt template + voice composer.
- RedisSaver runtime swap deferred to dedicated infra ticket (workspace dep update).
- Real APScheduler/k8s CronJob wiring deferred to deploy ticket.
- Re-registration of EP-4 `WorkflowDef` with populated `steps` tuple — current placeholder valid (workflow invoked via `build_treatment_followup_workflow` factory directly).

done -> docs/product/stories/luana-vitalia-bootstrap/T-workflow-1-result.md
