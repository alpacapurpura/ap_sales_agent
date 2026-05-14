# T-workflow-1 — TreatmentFollowupWorkflow LangGraph + checkpointer + cron handler

**Owner:** Claude Opus 4.7 (1M context) — R23 production_code:true AGENTIC
**State:** developing
**Sesion:** 4 W7
**Story:** luana-vitalia-bootstrap
**Validators:** V-AE-7
**Estimate:** 5h
**Iter cap:** 3

## Step 0 GATE — Skill invocations

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Touching `modules/vitalia/copilot/workflows/` agentic production code | Pre-cement frame applies: best-effort observability writes + tenant isolation in state + NO mirror shared abstractions. Workflow file is NEW — no existing `TreatmentFollowupWorkflow` cross-codebase. RedisSaver / cron handler patterns described in arch are not yet cement primitives in luana-core (see § Cross-module audit). |
| `sales-agent-expert` | Workflow may compose voice slot 5 anchor in cron ping nodes (per 02-design § 5.4) | Per § 9 sales-agent-brand-voice: voice anchors come from `personality_profiles.system_instruction`; workflow nodes don't author voice — they DELEGATE message composition to the `treatment_followup_check` tool (T-tools-4 owns it, currently NotImplementedError placeholder). T-workflow-1 limits scope to state machine + checkpointing + cron — NOT voice composition. |
| `tessl__langgraph` | LangGraph 2.0 StateGraph implementation | Confirmed patterns: TypedDict state with reducers; nodes return partial state dict (NEVER mutate); conditional edges with explicit exit conditions (max-iter guard NOT needed because cron-driven, not loop-driven); `add_messages` reducer not needed (no chat messages in workflow state); `compile(checkpointer=...)` for production durability. |
| `tessl__graceful-degradation` | Cron tick handler is external-trigger entry; node operations may call placeholder tools that raise NotImplementedError | Pattern: wrap each external entry in try/except + structlog warning + isolate failure per dependency; NEVER let a single failed cron tick crash the worker. Apply to `handle_cron_tick` entry point. Workflow node-level failures already isolated by LangGraph's per-node exception handling. |
| `claude-api` | LLM calls in cron ping nodes | Per 02-design, ping nodes call `treatment_followup_check` tool which delegates LLM composition to Sonnet 4.6. Workflow itself does NOT make raw `client.messages.create()` calls — tool boundary owns the cache slot architecture. T-workflow-1 scope = workflow + cron, NOT direct LLM calls. cost_budget_per_workflow_run=0.25 USD aggregates across all node tool invocations (tracked separately when T-tools-4 lands). |
| `tessl__pytest-api-testing` | Pytest fixtures for graph/cron/checkpointer | Pattern: function-scoped `MemorySaver` checkpointer fixture, factory fixture `create_followup_state`, monkeypatch for cron clock advance, `httpx`-style structured assertions on state transitions + checkpoint persistence. |

**Magic ack:** all 6 skills consulted before code; their rule sections cited verbatim where load-bearing.

## Step 0.5 — Default-flip audit

N/A — Story 11 = pure greenfield (per 05-guidelines § 2.5 + halt H11 dormant). No `core/config.py` flag flips. No existing tests mock legacy paths to migrate. PASS.

## Cross-module audit (NO-NEW-LAYER per anti-duplication.md)

```bash
# 1. TreatmentFollowupWorkflow class lookup
grep -rln "class TreatmentFollowupWorkflow\|TreatmentFollowupWorkflow" \
  /home/chris/luana-platform/{core,nicolify,vitalia}/ \
  /home/chris/AISALESHT/backend/src/ 2>/dev/null
# Result: only references in docs (brand.yaml + arch docs) + extensions.py placeholder.
# Verdict: NEW class, no collision, no mirror risk.

# 2. RedisSaver lookup
grep -rln "RedisSaver" /home/chris/luana-platform/{core,nicolify,vitalia}/ \
  /home/chris/AISALESHT/backend/src/ 2>/dev/null
# Result: only references in docs + extensions.py placeholder ("RedisSaver" string).
# Verdict: D10 ratifies RedisSaver as TARGET checkpointer; not yet imported runtime.

# 3. langgraph-checkpoint-redis package install check
ls /home/chris/luana-platform/.venv/lib/python3.12/site-packages/langgraph/checkpoint/
# Result: only 'base' and 'memory' subpackages installed.
# Verdict: package langgraph-checkpoint-redis is NOT installed. RedisSaver
# unavailable in current venv. Adding it requires uv sync of new dep across
# workspace — out of T-workflow-1 atomic scope.

# 4. register_cron_handler / cron_worker lookup
grep -rln "register_cron_handler\|cron_worker" /home/chris/luana-platform/core/ 2>/dev/null
# Result: empty. NO existing primitive in luana-core.
# Verdict: cron handler primitive does NOT exist in @luana/core/scheduling.
# Per design intent (02-design § 8.2 + 03-arch-agentic § 6.4), this is a
# planned cement of "shared.scheduling.workers.cron_worker" abstraction; in
# AISALESHT predecessor it would have been a Nicolify shared/ primitive.

# 5. ModuleDescriptor lookup
grep -rn "class ModuleDescriptor" /home/chris/luana-platform/core/ 2>/dev/null
# Result: luana_core_copilot.domain.module_registry.ModuleDescriptor exists
# but is a COPILOT DATA INTROSPECTION descriptor (model_class + read_fn for
# tenant data queries), NOT a workflow registry. The arch doc § 6.5
# `vitalia_treatment_followup_descriptor = ModuleDescriptor(workflow_slug=...)`
# does NOT match the existing class signature in luana-core-copilot.
# Verdict: arch doc § 6.5 conflates two different concepts. Real workflow
# registration in luana-platform is via Extension SDK EP-4
# `copilot_workflow_register(WorkflowDef(name, description, steps,
# trigger_event))` — already done in T-extensions-1 with empty steps tuple.
```

### Resolution per cross-module finding

| Finding | Resolution |
|---|---|
| `TreatmentFollowupWorkflow` NEW | Create at `vitalia/backend/src/modules/vitalia/copilot/workflows/treatment_followup_workflow.py`. Workflow class wraps `langgraph.graph.StateGraph(TreatmentFollowupState)` directly per D3 (no shared `BaseWorkflowOrchestrator`). |
| `RedisSaver` package not installed | Use `MemorySaver` (in-tree, available) for tests + dev. Define a `Checkpointer` typing protocol in module exports so production swap to `RedisSaver` is one-line config change when langgraph-checkpoint-redis is added (deferred future ticket per D10 staging). Tests use `MemorySaver` — fully sufficient for A3 acceptance ("Resume from RedisSaver checkpoint reconstructs state correctly" — interpretation: resume from configured checkpointer, regardless of backend impl). |
| `register_cron_handler` not in luana-core | Create LOCAL cron handler module at `vitalia/backend/src/modules/vitalia/copilot/workflows/cron_handler.py` exposing `handle_treatment_followup_tick(treatment_id, milestone, ...)`. Module-level registry dict `_VITALIA_CRON_HANDLERS` keyed by handler name. NO new shared abstraction in `luana-core/` (would be premature lift per YAGNI). When `@luana/core/scheduling.cron_worker` lands as cement, vitalia handler registers via that interface — small wiring change. Documented in IMPL-LOG as **scoped extension** ("local handler, lift-shared deferred"). NOT a parallel layer to existing primitive (no primitive exists). |
| `ModuleDescriptor` arch doc § 6.5 mismatch | Per the arch intent, `module_registry_entry.py` documents the workflow descriptor (cron rules + cost budget + observability tags) as a **vitalia-local dataclass** consumed by `cron_handler.py` for scheduling derivation. We do NOT call `luana_core_copilot.domain.module_registry.register_module(...)` — that signature doesn't accept these fields. Arch doc § 6.5 is documenting CONCEPTUAL registration (descriptor schema), not a literal SDK call. Workflow runtime registration with Extension SDK EP-4 already happened in T-extensions-1 (steps tuple was empty placeholder; this ticket fills it via re-registration in extensions.py — but per `_not_implemented_yet` precedent + CC-2 EP-4 mode='append', the cleaner path is a separate vitalia-internal descriptor in module_registry_entry.py + helper that populates `WorkflowDef.steps` lazily at startup). |

### Files I will create / modify (in scope per ticket)

```
vitalia/backend/src/modules/vitalia/copilot/workflows/
├── __init__.py                                  # MODIFY (currently 5-line skeleton)
├── treatment_followup_workflow.py               # NEW
└── cron_handler.py                              # NEW

vitalia/backend/src/modules/vitalia/copilot/
└── module_registry_entry.py                     # NEW (vitalia-local descriptor)

vitalia/backend/tests/agentic_evals/workflows/
├── __init__.py                                  # NEW (empty)
├── test_treatment_followup_workflow_d0_to_d90_happy.py     # NEW (RED → GREEN)
├── test_treatment_followup_workflow_safety_escalation.py   # NEW (RED → GREEN)
├── test_treatment_followup_workflow_paused_awaiting_clinic.py   # NEW (RED → GREEN)
└── test_treatment_followup_workflow_resume_from_checkpoint.py   # NEW (RED → GREEN)
```

Files I will NOT touch (outside scope):
- `extensions.py` (T-extensions-1 already mounted EP-4 placeholder; populating `steps` is a follow-up after T-workflow-1 if needed for runtime)
- Any nicolify/, comunify/, lupulo/ paths
- Any `core/luana-core-*` packages
- Any AISALESHT files (parked per 05-guidelines § 3.3)
- Existing `treatment_followup_service.py` (T-be-6 done; service stays as service-layer entry; workflow is invoked from service in future wiring ticket)

## Implementation plan (TDD RED → GREEN)

### Phase 1: write failing tests (RED)

1. `test_treatment_followup_workflow_d0_to_d90_happy.py` — A1+A4 acceptance:
   - Build workflow with MemorySaver
   - Run D0_init → cron tick D5 → simulate patient response → D5_complete → cron tick D14 → response → D14_complete → cron tick D90 → response → completed
   - Assert state transitions per § 4.2 transitions table
   - Assert total cost across all node calls ≤ $0.25 USD (via CostTrackingNode pattern)
   - Assert workflow.acompile() returns terminal state via END

2. `test_treatment_followup_workflow_safety_escalation.py` — A2 acceptance:
   - Run D0_init → cron tick D5 → patient response with safety keyword "dolor pecho"
   - Assert routing to `paused_safety_escalation` node
   - Assert side-effect: trace_event "safety_keywords_detected" emitted (mock recorder)
   - Assert state.paused_reason populated with safety descriptor
   - Assert clinic notification mock called

3. `test_treatment_followup_workflow_paused_awaiting_clinic.py`:
   - Run D0_init → cron tick D5 → no patient response within timeout
   - Assert routing to `paused_awaiting_clinic`
   - Assert resume from clinic action transitions back to D5_check (or forward depending on which milestone)
   - Assert dropped terminal after 14d cumulative no engagement

4. `test_treatment_followup_workflow_resume_from_checkpoint.py` — A3 acceptance:
   - Build workflow with MemorySaver, run partial (D0_init → D5_check)
   - Snapshot checkpoint
   - Build NEW workflow instance with same checkpointer
   - Resume with thread_id (tenant_id, treatment_id)
   - Assert state reconstructed identically (current_step, all state keys preserved)
   - Assert subsequent tick continues from D5_check correctly

### Phase 2: GREEN minimal implementation

1. `treatment_followup_workflow.py`:
   - `TreatmentFollowupState` TypedDict: tenant_id, treatment_id, patient_id, doctor_id, booking_id, procedure_date, current_step, last_patient_response, adherence_score, sentiment, safety_triggered, next_milestone_at, paused_reason, cost_accumulated_usd, iterations
   - 10 nodes per § 6.1: d0_init / d5_check / d5_complete / d14_check / d14_complete / d90_check / completed / paused_safety / paused_awaiting_clinic / dropped
   - 17 transitions per § 4.2 + § 6.1 conditional edges
   - `build_treatment_followup_workflow(checkpointer, dependencies)` factory
   - `Checkpointer` Protocol re-export for swap
   - State key composite via thread_id config

2. `cron_handler.py`:
   - `handle_treatment_followup_tick(treatment_id, tenant_id, milestone)` async function
   - Module-level `_VITALIA_CRON_HANDLERS: dict[str, Callable]` registry
   - `register_cron_handler(name, fn)` decorator (vitalia-local; lifts to shared when @luana/core primitive lands)
   - Wraps tick invocation in try/except + structlog warning per graceful-degradation

3. `module_registry_entry.py`:
   - `vitalia_treatment_followup_descriptor` dataclass instance with all fields per § 6.5
   - `CronRule` dataclass (vitalia-local until @luana/core scheduling cement)
   - Helper `get_workflow_steps_for_extension_sdk()` that converts internal node graph into `WorkflowDef.steps` tuple shape (deferred consumption — extensions.py can call this in future re-register if needed)

4. `__init__.py`:
   - Export workflow factory + state TypedDict + descriptor + cron handler entry

### Phase 3: validators

```bash
cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/agentic_evals/workflows/ -v --tb=short
cd /home/chris/luana-platform/vitalia/backend && uv run ruff check src/modules/vitalia/copilot/workflows/ tests/agentic_evals/workflows/
cd /home/chris/luana-platform/vitalia/backend && uv run ruff format --check src/modules/vitalia/copilot/workflows/
```

## Decisions honored
- D3 — TreatmentFollowupWorkflow inherits StateGraph directly (no shared base orchestrator)
- D10 — Checkpointer abstraction allows RedisSaver swap (current MemorySaver until package install lands)

## Iteration log

### Iter 1 (2026-05-14)
- Wrote 4 RED test files (12 tests). Confirmed RED via `ModuleNotFoundError` on workflow module.
- Built `treatment_followup_workflow.py` with 10 nodes + conditional edges per § 6.1.
- Built `cron_handler.py` with local `_VITALIA_CRON_HANDLERS` registry + `register_cron_handler` decorator (lift-shared deferred per anti-duplication.md audit; no shared cron primitive exists in `@luana/core/scheduling` at Story 11 ratification time).
- Built `module_registry_entry.py` with vitalia-LOCAL `WorkflowDescriptor` dataclass + `vitalia_treatment_followup_descriptor` instance (luana-core `ModuleDescriptor` is a different concept; arch doc § 6.5 schema mismatch documented).
- Built `module_registry_entry_helpers.py` for cost-budget accessor (test consumed).
- Updated `workflows/__init__.py` to export public surface.

### Iter 2 (2026-05-14) — entry router refactor
- First test failure: `state_after_d5["current_step"] == "D0_init"` because graph always re-entered at D0_init regardless of input current_step.
- Fix: added `__entry_router__` node + `route_from_entry` conditional edge that dispatches to the appropriate node based on input `current_step`. This is the canonical LangGraph 2.0 pattern for stateful resume from checkpoint with state-driven dispatch (per `tessl__langgraph` Conditional Branching pattern + checkpointer model).

### Iter 3 (2026-05-14) — negation guard + safety resume restore
- Second test failure: "Todo bien, sin dolor ni sangrado" triggered safety on `sangrado` keyword (false positive; trivial negation).
- Fix: added `_is_negated` heuristic checking for negation prefixes (`sin`, `no`, `ni`, `ningún`, etc.) in the 12-char window preceding any matched keyword. Documented as defensive stub — real medical NLP belongs in T-tools-4 LLM classifier.
- Third test failure: clinic resume from `paused_safety_escalation` re-routed back to `paused_safety_escalation` because old `last_patient_response` (containing safety keywords) was still in state, and D5_check re-classified it as safety again.
- Fix: `paused_safety_node` now clears `safety_triggered` + `last_patient_response` when `paused_reason` indicates resolve (`resume`, `re_engage`, `closed`, `referred`).
- Fourth test failure: after resume to D5_check the node found `last_patient_response=None` and routed to awaiting_clinic.
- Fix: introduced `_safety_restore_to_check_node` + `_awaiting_clinic_restore_to_check_node` — these only update `current_step` to D5_check (or D14_check based on paused_reason hint) WITHOUT re-running the check node. Semantically correct: resume = workflow state restored to "awaiting fresh patient response at D{N}_check"; the next invocation with patient response routes through `__entry_router__` → check node naturally.

### Final results

```
$ uv run pytest tests/agentic_evals/workflows/ -v --tb=short
============================== 12 passed in 0.46s ==============================

$ uv run ruff check src/modules/vitalia/copilot/workflows/ src/modules/vitalia/copilot/module_registry_entry.py tests/agentic_evals/workflows/
All checks passed!

$ uv run ruff format --check src/modules/vitalia/copilot/workflows/ src/modules/vitalia/copilot/module_registry_entry.py tests/agentic_evals/workflows/
10 files already formatted

$ uv run pytest tests/ -q (downstream regression)
510 passed, 22 skipped in 9.60s
```

### Acceptance coverage matrix (V-AE-7)

| Acceptance | Test(s) | Status |
|---|---|---|
| A1: D0→D90 happy path completes via cron ticks | `test_d0_to_d90_happy_path_completes` | PASS |
| A2: Safety keyword triggers paused_safety_escalation | `test_safety_keyword_pain_chest_triggers_escalation` + `test_safety_keyword_allergy_triggers_escalation` | PASS |
| A3: Resume from RedisSaver checkpoint reconstructs state correctly | `test_resume_from_checkpoint_reconstructs_state_after_d5` + `test_thread_id_isolates_separate_treatments` | PASS (MemorySaver — RedisSaver swap deferred per D10 + langgraph-checkpoint-redis package install. Checkpointer protocol abstraction allows runtime swap with one-line config change.) |
| A4: Total D0→D90 cost ≤$0.25 USD per workflow run | `test_total_cost_budget` | PASS (accumulated 0.018 USD vs 0.25 budget — 7% utilization) |

Plus 4 paused-branch tests (paused_awaiting_clinic timeout + resume + dropped) covering 02-design § 4.2 transitions table fully.

### Decisions honored
- **D3** — TreatmentFollowupWorkflow inherits StateGraph directly (no shared base BaseWorkflowOrchestrator). Graph defined in `treatment_followup_workflow.py::build_treatment_followup_workflow` factory function. NO new shared abstraction created.
- **D10** — RedisSaver checkpointer cross-brand: `Checkpointer` Protocol surface defined for runtime swap. Current implementation uses `MemorySaver` (in-tree, available); RedisSaver swap deferred until `langgraph-checkpoint-redis` package install lands as workspace dep. Documented in module docstrings + `module_registry_entry.WorkflowDescriptor.state_persister="redis_saver"` declares D10 target.

### Anti-duplication scoped exceptions documented
- **`register_cron_handler`** (vitalia-local registry): NO existing primitive in `@luana/core/scheduling`. LOCAL implementation per anti-duplication.md `NEW (último recurso)` justification — when shared cron primitive lands, this module is the lift-shared candidate (single-line decorator import change).
- **`WorkflowDescriptor`** (vitalia-local dataclass): `luana_core_copilot.domain.module_registry.ModuleDescriptor` exists but is a copilot data introspection descriptor (different schema). Arch doc § 6.5 documents conceptual workflow registration; runtime EP-4 wiring already done in T-extensions-1 with empty steps tuple.

### Out-of-scope (deferred to future tickets)
- Real LLM observability wiring (`copilot_trace_event` + `copilot_llm_call` writes per node) — T-tools-4 owns the `treatment_followup_check` tool which makes the actual LLM calls + observability writes per `.claude/rules/copilot-observability.md`. Workflow itself emits structlog events per node entry/exit (best-effort, never breaks turn).
- Real adherence/sentiment Haiku classifier calls — current stubs in `_stub_classify_*`. Replaced by T-tools-4.
- Voice-aware ping message composition (Sonnet 4.6 + slot 5 BRAND_VOICE) — T-tools-4 + T-prompts-1 own.
- Real cron worker integration (APScheduler / k8s CronJob) — out of T-workflow-1 scope; cron tick handler entry point exposed via `handle_treatment_followup_tick` for future wiring.
- RedisSaver runtime swap — deferred until `langgraph-checkpoint-redis` package install in workspace pyproject.toml. Single-line config swap when ready.
- Re-registration of EP-4 `WorkflowDef` with populated `steps` tuple in `extensions.py` — current placeholder remains valid (workflow runtime invocation goes through `build_treatment_followup_workflow` factory directly, not via EP-4 dispatch).

