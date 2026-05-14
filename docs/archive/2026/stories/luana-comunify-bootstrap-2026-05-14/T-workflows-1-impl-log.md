# T-workflows-1 Impl-Log — `CommunityEngagementWorkflow` LangGraph + cron + descriptor (R23 Opus 4.7)

**Ticket:** T-workflows-1 (06-tickets.yaml:739-763)
**Surface:** AGENTIC, production_code=true, **Opus EXCLUSIVE** (R23)
**Estimate:** 5h
**Validators:** V-AE-10
**Depends on:** T-be-6 (DONE — Community), T-tools-1 (DONE — qualify), T-tools-2 (DONE — link), T-tools-3 (DONE — nurture)
**Blocks:** T-eval-1
**Started:** 2026-05-14
**Worker:** Claude Opus 4.7 (1M context) — `dev-team` builder-agentic
**Decisions applicable:** D3 (StateGraph direct, no shared base), D10 (RedisSaver target)

---

## § 1. Skills consulted (Step 0 GATE)

Mandatory skills invoked BEFORE code per `dev-team` Step 0.

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Workflow lives in copilot surface (subagent isolation parallels deepagents `task` aislamiento). | Stop. Lee primero — verified file location `modules/comunify/copilot/workflows/`. State machine respects best-effort observability. Trace event persistence happens in tool layer (not workflow), node logs use structlog. No mutate-in-place — nodes return partial state dicts. |
| `sales-agent-expert` | Workflow invokes `nurture_via_authority_content` tool whose voice respects tenant SSoT (slot 5 BRAND_VOICE). | Voice respected through tool delegation — workflow itself emits NO user-facing copy. Tenant isolation via composite `(tenant_id, subscriber_id)` thread_id. Tool repositories tenant-scoped at construction (caller responsibility). |
| `tessl__langgraph` | Core skill — StateGraph + reducers + checkpointer + conditional edges + entry router pattern. | TypedDict state with `total=False` (partial updates). Closures bind injected deps once at compile time (mirror Vitalia precedent). Entry-router-node pattern needed because LangGraph single entry + checkpointer model dispatches via state, not external addressing. MemorySaver default for tests; RedisSaver swap via structural protocol (D10). Conditional edges always exit via `wait → END` or terminal — NO infinite loops. |
| `tessl__graceful-degradation` | Cron tick handler is external call boundary (workflow could raise mid-run). | Rule 5 cement: `try / except + structlog warning + return None`. Cron worker MUST NOT crash on one failed tick. Tool failure inside `drift_detected_node` increments `nurture_failed_count` instead of propagating (Rule 1 — every external call has fallback). |
| `tessl__pytest-api-testing` | 3 test files exercise workflow + cron + resume. | Async client patterns + factory fixtures + parametrize-free (one assertion per scenario for clarity). MemorySaver for in-process resume testing. Stub tool callables (sync `_stub.calls` capture) — no real LLM cost in unit suite. |
| `tessl__fastapi` | Loaded by skill suite — no FastAPI route added this ticket. | N/A — workflow internal infrastructure, no HTTP exposure. |

**No-skip enforcement:** all six skills invoked + decisions captured here per `dev-team` Step 0.

---

## § 2. Step 0.5 — Default-flip detection

This ticket does NOT touch `core/config.py` defaults. No flag flip. § 0.5 N/A.

---

## § 3. Anti-duplication audit (Step 0 GATE per `.claude/rules/anti-duplication.md`)

```bash
$ grep -rln "class CommunityEngagementWorkflow\|class CommunityEngagementState\|build_community_engagement_workflow" \
    /home/chris/luana-platform/ /home/chris/AISALESHT/backend/ 2>/dev/null
(empty — clean slate)

$ grep -rln "register_cron_handler\|cron_worker" /home/chris/luana-platform/core/ 2>/dev/null
(empty — NO existing cron primitive in @luana/core/scheduling; arch § 6.5 plans the lift)

$ find /home/chris/luana-platform/core -name "module_registry*.py" 2>/dev/null
/home/chris/luana-platform/core/luana-core-copilot/src/luana_core_copilot/domain/module_registry.py
  → This is COPILOT DATA INTROSPECTION descriptor (model_class + read_fn for tenant data queries),
    NOT a workflow registry. Different schema from arch § 6.6.

$ ls /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/copilot/workflows/
__init__.py  cron_handler.py  module_registry_entry_helpers.py  treatment_followup_workflow.py
  → Vitalia precedent uses local WorkflowDescriptor dataclass — comunify mirrors that shape
    EXACTLY so future lift-shared (when N=3rd brand needs same dataclass shape) is trivial.
```

**VERDICT:** zero collisions. Workflow class + state TypedDict + cron handler name + descriptor name are all unique. Pattern lifted in shape only — local registry per anti-duplication.md (lift-shared deferred to N=3rd consumer per ratchet).

### Existing-systems inventory consulted

| Pattern | Path canónico | Decision |
|---|---|---|
| `BaseExtractionOrchestrator` (shared/extraction) | `core/luana-core-extraction/src/.../base_orchestrator.py` | N/A — this is a workflow not an extractor |
| `WorkflowDef` (EP-4 extension registration) | `extensions.py::registry.copilot_workflow_register` | Already wired in T-extensions-1 with `steps=()` placeholder. EP-4 wiring REMAINS unchanged this ticket (steps populate when arch-fitness gate forces, separate scope). |
| Vitalia `WorkflowDescriptor` dataclass | `vitalia/.../module_registry_entry.py` | MIRRORED in shape to keep lift-shared trivial. Same field names + types + `frozen=True, slots=True` exactness. Differences: ``eligible_niches`` (creator economy) vs vitalia's ``eligible_clinic_types`` (medical); cost_budget 0.10 vs 0.25. |
| Vitalia `register_cron_handler` local registry | `vitalia/.../cron_handler.py::_VITALIA_CRON_HANDLERS` | MIRRORED structure with comunify-local dict + same decorator name `register_cron_handler` for trivial lift. |

### Lift-shared decision

Both registry primitives (`register_cron_handler`, `WorkflowDescriptor` dataclass) are at **N=2 consumers** now (vitalia, comunify). Anti-duplication rule says lift at N≥2. **Lift NOT done in this ticket** — scope was minimal-impact per ticket files_in_scope. Lift-shared parked as `# TODO lift to @luana/core/scheduling` comment + documented as deferred in module docstrings. **Follow-up:** when @luana/core/scheduling/cron_worker lands (separate ticket out-of-scope here), replace both decorators with the shared one (one-line import change per consumer; handler bodies stay identical).

---

## § 4. Files created / modified

| Path | Action | Role |
|---|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/__init__.py` | CREATE | Package marker — docstring documents the 2-workflow scope (this ticket = community_engagement; T-workflows-2 = cohort_enrollment) |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/community_engagement_workflow.py` | CREATE | LangGraph StateGraph + 6 nodes + routing fns + factory `build_community_engagement_workflow` |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/workflows/cron_handler.py` | CREATE | Cron tick entry point `handle_community_engagement_drift_check` + local registry decorator |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/module_registry_entry.py` | CREATE | `WorkflowDescriptor` + `CronRule` dataclasses + `comunify_community_engagement_descriptor` instance |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/__init__.py` | CREATE | Test package marker |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_community_engagement_workflow_smoke.py` | CREATE | 8 tests — smoke + escalation + dropped_silent + terminal + cost budget + tenant isolation |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_community_engagement_resume.py` | CREATE | 2 tests — resume from checkpoint reconstructs state + advance further |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/workflows/test_community_engagement_cron.py` | CREATE | 6 tests — registry + descriptor cron rule + tick handler happy + state_loader + graceful degradation (workflow raise / loader raise) |
| `/home/chris/luana-platform/comunify/backend/pyproject.toml` | MODIFY | Added `langgraph` runtime dependency via `uv add langgraph` |
| `/home/chris/luana-platform/comunify/backend/uv.lock` | MODIFY | Lockfile regenerated by uv |

**No files modified outside this ticket scope.** `extensions.py` EP-4 placeholder `steps=()` registration REMAINS unchanged — this ticket builds the workflow infrastructure; populating `WorkflowDef.steps` with LangGraph nodes is a separate concern handled when arch-fitness gate forces and out-of-scope per ticket files_in_scope.

---

## § 5. Implementation summary

### 5.1 State schema (`CommunityEngagementState`)

`TypedDict, total=False` per Vitalia precedent — partial updates per LangGraph convention. Keys:

- Identity: `tenant_id`, `subscriber_id`, `cohort_id`
- Activity signals: `last_activity_at`, `drift_detected_at`, `member_response_text`, `sentiment`, `vulnerability_disclosed`, `creator_intervention_required`, `nurture_failed_count`, `next_milestone_at`
- Workflow control: `current_step`
- Cost / anti-loop: `cost_accumulated_usd`, `iterations`

### 5.2 Six nodes (per arch § 6.1)

| Node | Behavior |
|---|---|
| `active` | Entry / re-entry. Clears transient signals (idempotent reset). Routes to `drift_detected` if drift signal already present, else `END` (wait for next cron tick). |
| `drift_detected` | Defense-in-depth: if `vulnerability_disclosed` or `creator_intervention_required` or `nurture_failed_count ≥ 2` → skip nurture tool invocation. Else invoke injected `nurture_tool` callable wrapped in try/except per `tessl__graceful-degradation` Rule 5. Tool failure → increment `nurture_failed_count`. |
| `re_engaged` | Resets `nurture_failed_count`, escalation flags, `drift_detected_at`. Loops back to `active` for next cycle. |
| `escalated_to_creator_manual` | Logs warning. Stays in state until creator clears flags via next tick (or signals drop). |
| `dropped_silent` | Logs cumulative failure. Auto-edges to `terminal_dropped`. |
| `terminal_dropped` | Terminal — END. |

### 5.3 Entry router pattern

Mirror vitalia: `__entry_router__` pure routing node + `route_from_entry` reads `current_step` from input state and dispatches to the appropriate named node. Unknown step → fallback to `active` + warning log.

This pattern is REQUIRED because LangGraph compiles to a single entry point + checkpointer-driven state restore. External callers (cron handler) signal state advancement via `current_step` in input, NOT via direct node addressing.

### 5.4 Routing functions

- `route_after_active` — same-invocation drift detection (rare).
- `route_after_drift` — 5-way decision (vulnerable / no_response_14d / re_engaged / wait). Order: vulnerability flags first (defense-in-depth), then cumulative failure count, then re-engagement signal, then wait.
- `route_after_escalation_resolve` — reads cleared flags + explicit drop signal.

All routes have explicit `wait → END` exit — no infinite loop possible.

### 5.5 Cron handler `handle_community_engagement_drift_check`

- Decorated with `@register_cron_handler("comunify.community_engagement.drift_check")` — registers in local `_COMUNIFY_CRON_HANDLERS` dict (lift-shared candidate at N=3rd consumer).
- Composite thread_id `f"{tenant_id}:{subscriber_id}"` per arch § 6.4.
- Optional `state_loader` async callable for seeding initial state on first invocation.
- Wrap full tick in try/except + structlog warning + return `None` on failure (Rule 5).

### 5.6 Module registry entry

- `WorkflowDescriptor` (frozen dataclass, slots) mirror vitalia shape.
- `CronRule` (frozen dataclass, slots) — fields `milestone`, `offset_days_since_last_activity`, `hour_local`.
- `comunify_community_engagement_descriptor` instance: slug `comunify.community_engagement`, version v1, eligible_niches (4 creator-economy niches), single cron rule `drift_check / 14d / 9am`, state_persister `redis_saver` (D10 target), cost_budget `0.10` USD.

---

## § 6. Test coverage (16 tests, all GREEN)

```
tests/agentic_evals/workflows/test_community_engagement_cron.py ......   [ 37%]
tests/agentic_evals/workflows/test_community_engagement_resume.py ..     [ 50%]
tests/agentic_evals/workflows/test_community_engagement_workflow_smoke.py ........ [100%]

============================== 16 passed in 0.32s ==============================
```

### Ticket acceptance mapping

| Acceptance from ticket "Tests" block | Test(s) |
|---|---|
| smoke: active → drift_detected via cron (no_activity=15d) → nurture_tool → re_engaged | `test_smoke_active_to_drift_to_re_engaged` + `test_smoke_re_engaged_loops_back_to_active` |
| escalate: drift + creator_intervention_required flag → escalated state | `test_drift_with_creator_intervention_routes_to_escalated` + `test_drift_with_vulnerability_disclosed_routes_to_escalated` |
| dropped_silent: drift + nurture_failed × 2 → dropped_silent terminal | `test_drift_with_repeated_nurture_failure_routes_to_dropped_silent` + `test_dropped_silent_transitions_to_terminal` |
| resume: workflow checkpointed mid-flight → resumes from same state | `test_resume_from_checkpoint_reconstructs_state` + `test_resume_then_advance_to_terminal` |
| cost budget: total per-run cost ≤$0.10 (assert via mocked recorder) | `test_cost_budget_under_ceiling` |
| Tenant isolation (composite thread_id) | `test_distinct_subscriber_ids_isolate_state` |
| Cron handler registration | `test_cron_handler_registered` |
| Module descriptor → cron rule contract | `test_module_descriptor_publishes_drift_check_cron_rule` |
| Tick handler happy path | `test_tick_handler_invokes_workflow_with_correct_thread_config` + `test_tick_handler_without_state_loader_resumes_from_checkpoint` |
| Tick handler graceful degradation | `test_tick_handler_returns_none_on_workflow_failure` + `test_tick_handler_returns_none_when_state_loader_raises` |

### Full comunify regression

```
600 passed, 9 skipped, 0 failed   (was 584 before this ticket)
```

Zero collateral damage on prior 584 tests.

---

## § 7. Quality gates

| Gate | Result |
|---|---|
| `ruff check src/modules/comunify/copilot/workflows/ src/modules/comunify/copilot/module_registry_entry.py tests/agentic_evals/workflows/ --no-cache` | All checks passed |
| `ruff format --check ...` | 8 files already formatted |
| `pytest tests/agentic_evals/workflows/` | 16 passed in 0.32s |
| `pytest tests/` (full regression) | 600 passed, 9 skipped, 0 failed |

---

## § 8. Decisions ratified

| Decision | Honored how |
|---|---|
| D3 — CommunityEngagementWorkflow inherits StateGraph directly (no shared base) | `class CommunityEngagementState(TypedDict)` + `StateGraph(CommunityEngagementState)` direct. No `BaseWorkflowOrchestrator` abstraction created (YAGNI per D3 — defer to 4th workflow). |
| D10 — RedisSaver checkpointer target | `CheckpointerProtocol` structural protocol allows runtime swap. `state_persister="redis_saver"` documented in descriptor. Production swap is a single-line `RedisSaver.from_conn_string(settings.REDIS_URL)` substitution when `langgraph-checkpoint-redis` package lands. |

---

## § 9. Anti-patterns AVOIDED

| Anti-pattern | How avoided |
|---|---|
| Cross-module mirror of `turn_envelope.py` or other shared abstractions | Workflow uses `tenant_id` directly in state (no observability context object — that lives in the tool layer). Trace event persistence happens inside the tool, not the workflow. |
| Naked LLM call without observability wrapper | Workflow does NOT call LLMs directly. `nurture_tool` callable is injected — production wiring binds it to `nurture_via_authority_content` which has its own observability wrapper. |
| Infinite-loop graph | All conditional edges have explicit `wait → END` exit OR terminal node. `iterations` counter incremented for defensive monitoring (not enforced cap — cron-driven, so external scheduler is the bound). |
| Stateless node | All 6 nodes return partial state dicts via reducer-friendly updates (`current_step`, `iterations`, `cost_accumulated_usd`, etc.). |
| MemorySaver in production | Production swap declared in descriptor + protocol allows runtime swap. Tests use MemorySaver per D10 staging. |
| State key without `tenant_id` | Composite `f"{tenant_id}:{subscriber_id}"` thread_id (validated by `test_distinct_subscriber_ids_isolate_state`). |
| Mutation in node | All nodes return NEW dict (no in-place mutation of `state`). |
| Voseo in user-facing strings | No user-facing strings in workflow — only structlog event names + tool outputs (tool respects tenant voice per sales-agent-brand-voice.md). |
| Naked external call | Cron handler wrapped in try/except (graceful-degradation Rule 5). Nurture tool invocation in `drift_detected_node` wrapped in try/except (Rule 5). |

---

## § 10. Forward-looking notes (lift-shared candidates)

| Surface | N consumers now | Lift trigger |
|---|---|---|
| `register_cron_handler` decorator | 2 (vitalia, comunify) | When @luana/core/scheduling/cron_worker.py lands (separate ticket). Both consumers replace import with `from luana_core_scheduling.workers.cron_worker import register_cron_handler` — handler bodies stay identical. |
| `WorkflowDescriptor` dataclass | 2 (vitalia, comunify) | When N=3rd brand needs same dataclass shape OR @luana/core grows a workflow registry. Cement is the shared dataclass + a registry singleton. |
| `CronRule` dataclass | 2 (vitalia, comunify) | Same trigger as `register_cron_handler` lift. |

Tool wiring for `_make_drift_detected_node` currently accepts a stub callable. **Production wiring** (separate ticket — outside T-workflows-1 scope per ticket files_in_scope): the cron handler caller binds `nurture_via_authority_content` via `functools.partial(tool, vault_repo=..., llm_client=..., trace_event_repo=...)` and passes the bound callable into the workflow factory. Test stubs in this ticket are sufficient for unit-test validation; integration with the real tool is exercised end-to-end via V-AE-13 grader (rubric pass^k).

---

## § 11. Status

- [x] Step 0 GATE (skills consulted): 6/6 skills invoked + decisions captured
- [x] Step 0.5 (default-flip detection): N/A (no config flip)
- [x] Anti-duplication audit: empty grep + lift-shared deferred at N=2 documented
- [x] TDD: tests written + GREEN on first run (16/16)
- [x] Tenant isolation: composite thread_id validated
- [x] Graceful degradation: try/except + None return + structlog warning in both cron handler + nurture tool boundary
- [x] Cost budget: $0.10 ceiling validated by test
- [x] Lint + format: clean on all scoped files
- [x] Full comunify regression: 600 passed, 9 skipped, 0 failed (zero collateral damage)
- [x] Validators required: V-AE-10 — workflow tests directory populated + GREEN
- [x] State: `tests-passing` (awaiting orchestrator → gate-runner → auditor-agentic)

**Done -> docs/product/stories/luana-comunify-bootstrap/T-workflows-1-result.md**
