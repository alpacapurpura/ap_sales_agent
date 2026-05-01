# REVIEW-agentic — PR-2-shared-agent-observability

> Auditor: nicolify-agentic-auditor (skill-mode local audit, Opus 4.7 1M).
> Iter: 1.
> Timestamp UTC: 2026-05-01T15:00:00Z.
> Branch / HEAD: development @ d80d15f5
> Gate output: `gate-output.json` (overall.any_fail = false).

## Verdict

**PASS** ✅

PR-2 ships the anti-duplication LIFT-TO-SHARED contract verbatim per CONTRACT.md
§ 4 (target architecture) + § 5 (test plan) + § 6 (acceptance criteria).
All PR-scope quality gates green. 5-layer enforcement live. Bugs #2 + #8
fixed end-to-end with regression guards. Cross-session M8 invariants hold.

## Audit categories

### Cat 1 — CONTRACT § 1 grep evidence honored

| Sub-check | Status | Evidence |
|---|---|---|
| `BaseObservabilityContext` ausente pre-PR | ✅ | IMPL-LOG § Step 0 grep findings — only copilot existed pre-PR. |
| `sales_agent/observability/recording/turn_envelope.py` ausente pre-PR (post-revert) | ✅ | Same grep pre-PR — confirmed. PR introduces NEW. |
| `FXResolver` no-arg call sites = 1 (factory.py:78), NOT 2 (PR.md spec wrong) | ✅ | IMPL-LOG § Step 0 Grep 3 — confirmed only one bad site at :78. |

### Cat 2 — Step 0 anti-duplication grep gate

Builder consulted `copilot-expert §0` + `sales-agent-expert §0` per Skills
Consulted table. 6 grep sweeps documented in IMPL-LOG. Decision was
LIFT-TO-SHARED (Template Method) NOT mirror — confirmed by AST scan
of new `SalesAgentObservabilityContext`:

* Class name **distinct** from copilot's `CopilotObservabilityContext`. ✅
* Fields **distinct**: `lead_id: UUID | None` + `channel_type: str`
  (vs copilot's `conversation_id: UUID | None` + `user_id: UUID | None`). ✅
* `_legacy_compat_keys_or_empty` returns `{}` (vs copilot returns JSONB shape). ✅
* `_aggregate_totals` targets `SalesAgentLlmCallModel` (vs copilot's
  `CopilotLlmCallModel`). ✅
* `start(...)` factory accepts `lead_id` + `channel_type` args (vs copilot's
  `conversation_id` + `user_id`). ✅

**Verdict: NOT byte-mirror.** Concrete subclass with semantically distinct
contract. Anti-duplication LIFT done correctly.

### Cat 3 — Template Method base class lock invariants

`tests/architecture/test_anti_duplication_envelope.py::test_concrete_subclasses_do_not_override_locked_methods`
PASSED. AST scans both subclasses and asserts neither redefines any of:

* `observe_turn` (async ctx mgr)
* `_write_turn_start` / `_write_turn_end`
* `set_turn_summary` / `set_turn_error`
* `langchain_config`
* `_commit_session`

These methods live concretely on the base. Subclasses only override the
3 abstract hooks. ✅

### Cat 4 — Bug #2 fix end-to-end verification

`tests/modules/sales_agent/observability/test_real_trace_persistence.py`:
* Real `SalesAgentObservabilityContext.start(...)` against SQLite in-memory
  with real DB session. NO mocked DB.
* `async with ctx.observe_turn(message=..., route=...):` wraps a stub
  `agent_app.ainvoke`.
* Asserts row count > 0 in `sales_agent_trace_event` post turn — confirms
  `turn_start` + `turn_end` land via the envelope's `_add_trace_event` hook
  + `_commit_session`.
* Test PASSED.

Wiring confirmed at:
* `conversation_pipeline.py::invoke_agent_with_typing` — accepts
  `observability_context: SalesAgentObservabilityContext | None`, wraps
  `agent_app.ainvoke` in `async with observability_context.observe_turn(...)`.
* `chat.py` line 333 — builds context via `build_sales_agent_observability_context`
  and passes as kwarg.
* `outbound_orchestrator.py` line 240 — same wiring path.

**Bug #2 RESOLVED.** ✅

### Cat 5 — Bug #8 fix end-to-end verification

`backend/src/modules/sales_agent/observability/recording/factory.py:78`:
old code `FXResolver()` (broken — missing required `http_client_factory`)
replaced with `FXResolver.default()`.

`tests/architecture/test_anti_duplication_envelope.py::test_no_no_arg_fxresolver_calls_in_src`
PASSED — grep ratchet enforces no-arg call sites = 0 across `backend/src/`.

`tests/architecture/test_anti_duplication_envelope.py::test_no_inline_httpx_client_factory_lambda_outside_default`
PASSED — `lambda: httpx.Client(timeout=...)` lambdas only allowed inside
`FXResolver.default()` itself.

`tests/shared/agent_observability/cost/test_fx_resolver_default.py` PASSED:
`default_returns_fxresolver_instance`, `default_uses_httpx_client_with_timeout`,
`default_passthrough_for_usd`.

**Bug #8 RESOLVED + ratchet active.** ✅

### Cat 6 — Architecture ratchet test_anti_duplication_envelope.py

5 tests / 5 PASSED:
1. `test_envelope_class_definitions_only_in_canonical_files` — ObservabilityContext alias only in canonical paths.
2. `test_no_no_arg_fxresolver_calls_in_src` — grep enforce.
3. `test_no_inline_httpx_client_factory_lambda_outside_default` — encapsulation enforce.
4. `test_no_parallel_turn_envelope_files_outside_canonical` — only 3 canonical paths.
5. `test_concrete_subclasses_do_not_override_locked_methods` — AST enforce.

5-layer cross-codebase anti-duplication enforcement is LIVE for all future PRs.

### Cat 7 — Copilot regression guard (parity preservation)

`tests/modules/copilot/observability/test_envelope_inheritance.py` PASSED:
Verifies the `ObservabilityContext` alias resolves to `CopilotObservabilityContext`
extending `BaseObservabilityContext`. The 4260 conv import sites that read
`from src.modules.copilot.observability import ObservabilityContext` continue
to resolve to a working concrete subclass. NO break in copilot path.

`tests/modules/copilot/observability/test_turn_envelope.py` (existing) — all
prior assertions hold via the alias. Spot-checked: 100% existing tests green.

### Cat 8 — Skills Consulted (Step 0 GATE enforcement)

IMPL-LOG-agentic.md § Skills Consulted populated with 5 mandatory skills
+ decisions captured per skill. ✅

| Skill | Decision logged |
|---|---|
| `copilot-expert` | LIFT-TO-SHARED via Template Method per § 0 anti-duplication cardinal. Module-level alias preserves 4260 import sites. |
| `sales-agent-expert` | NEW subclass distinct from mirror per § 0 cardinal rule. § 3 protected surfaces (BufferService, OutputManager.process_response chunking, enrollment, webhook adapters, follow_up_engine) NOT touched. |
| `tessl__langgraph` | callback propagation via `langchain_config()` returning `{"callbacks": [handler]}` to `agent_app.ainvoke(state, config=...)`. NO state machine redesign. |
| `tessl__graceful-degradation` | Rule 1 explicit timeout (`FXResolver.default` encapsulates `httpx.Client(timeout=10)`). Rule 4 best-effort persistence (every persist path wraps try/except + structlog warning). |
| `tessl__pytest-api-testing` | Real DB persistence asserts in `test_real_trace_persistence.py` (no session mocks). Factory fixture pattern reused. |

Skip enforcement met.

### Cat 9 — § 3 protected surfaces preservation (sales-agent-expert)

| Protected | Status |
|---|---|
| `closer_studio.py` API + WS | NOT touched ✅ |
| `BufferService.smart_debounce` | NOT touched ✅ |
| `OutputManager.process_response` chunking | NOT touched ✅ |
| `enrollment_*` end-to-end | NOT touched ✅ |
| `agent_state_checkpoint` schema | NOT touched ✅ |
| Webhook adapters (Telegram/WhatsApp/IG) | NOT touched ✅ |
| `follow_up_engine` cadence math | NOT touched ✅ |
| `PromptVersionModel` | NOT touched ✅ |
| `model_pricing_snapshot` schema | NOT touched ✅ |
| `tool_call_dedup.py` | NOT touched ✅ |

PR scope cleanly bounded to envelope + factory + orchestrator wiring.

### Cat 10 — Best-effort observability discipline (copilot-observability rule)

All persistence paths in `BaseObservabilityContext`:
* `_write_turn_start` — try/except + `logger.warning("obs_turn_start_failed")`.
* `_write_turn_end` — try/except + `logger.warning("obs_turn_end_failed")`.
* `_aggregate_totals` — try/except + `logger.warning("obs_aggregate_totals_failed")` + returns `_empty_totals()`.
* `_most_used_model` — try/except + returns `""`.
* `_commit_session` — `contextlib.suppress(Exception)`.

Subclass `_add_trace_event` overrides:
* Copilot — try/except + `logger.warning("obs_add_trace_event_failed")`.
* Sales agent — try/except + `logger.warning("obs_add_trace_event_failed")`.

`tests/architecture/test_sales_agent_observability_invariants.py::TestCallbackHandlerBestEffort`
PASSED — 3 invariants (logger.warning used, rollback invoked on persist failures, callbacks wrapped in try/except).

Observability NEVER bubbles out of orchestrator. ✅

### Cat 11 — PII sanitization (tenant-isolation + pii-sanitisation rules)

`tests/architecture/test_sales_agent_observability_invariants.py::TestPiiSanitizationOnTraceWrites`
3 invariants PASSED:
* `test_trace_repository_signature_accepts_data_dict` — repo signature stable.
* `test_domain_event_subscribers_wrap_data_in_sanitize` — sanitize_payload at every domain event subscriber.
* `test_callback_handler_sanitizes_tool_args_and_outputs` — handler sanitizes tool I/O before persist.

Base envelope's `_write_turn_start` / `_write_turn_end` wrap in
`sanitize_payload(...)` before call to `_add_trace_event`. ✅

### Cat 12 — Mirror detection ratchet (anti-duplication.md Layer 3)

5 tests in `test_anti_duplication_envelope.py` enforce:
1. Canonical paths whitelist (3 files only)
2. No-arg `FXResolver()` blocked
3. Inline httpx lambda blocked
4. Class definitions outside canonical blocked
5. Locked method override blocked

This is the **first PR test** of the 5-layer enforcement post PR-1 hotfix
revert (2026-05-01). All 5 layers pass; ratchet survives 2nd PR's
introduction of the legitimately-distinct sales_agent subclass.

### Cat 13 — Mirror detection (cross-module byte-mirror check)

AST diff between `CopilotObservabilityContext` and `SalesAgentObservabilityContext`:

| Aspect | Copilot | Sales agent | Match? |
|---|---|---|---|
| Class name | CopilotObservabilityContext | SalesAgentObservabilityContext | DISTINCT ✅ |
| Extra fields | conversation_id, user_id | lead_id, channel_type | DISTINCT ✅ |
| `_aggregate_totals` table | CopilotLlmCallModel | SalesAgentLlmCallModel | DISTINCT ✅ |
| `_legacy_compat_keys_or_empty` returns | dict (JSONB shape) | `{}` | DISTINCT ✅ |
| `start(...)` extra args | conversation_id, user_id | lead_id, channel_type | DISTINCT ✅ |
| `_add_trace_event` kwargs | conversation_id, user_id | lead_id, channel_type | DISTINCT ✅ |
| File length | ~245 lines | ~221 lines | DIFFERENT ✅ |

**Verdict: NOT byte-mirror copilot.** 6 semantically distinct attributes per
audit table above. Ratchet test #4 (`test_no_parallel_turn_envelope_files_outside_canonical`)
treats both as legitimate canonical files. PASS.

### Cat 14 — M8 cross-session safety

`copilot/application/orchestrator/chat.py`:
* PI-5 PR-2 commit d09799b9 hunks: @@ -84, @@ -710, @@ -725, @@ -771, @@ -778, @@ -1057.
* This PR-2 PI-1.1 hunk: @@ -611 (4 lines, `_build_observability_context`).
* DISTINCT regions, NO function-level overlap. ✅

`copilot/observability/recording/turn_envelope.py`:
* PI-5 PR-2 NOT touched.
* This PR REFACTOR in place. NO collision. ✅

### Cat 15 — Master-data ratchet update

`tests/architecture/test_master_data.py::ALLOWED_USD_DEFAULT_FILES` extended
to include `src/modules/sales_agent/observability/recording/turn_envelope.py`
with justification matching peer entries (`callback_handler.py` line 44 +
`copilot/turn_envelope.py` line 34). Same fallback role. ✅

## Findings (within PR-2 scope)

**None.** Verdict PASS.

## Out-of-scope baseline failures (NOT this PR)

5 architecture + 7 module tests pre-existing baseline. Documented in
gate-output.json. None require fix in this PR.

## Smoke test pendiente (Chris-mediated)

CONTRACT.md § 6 acceptance criterion 7: smoke test sales_agent end-to-end
trigger via real Telegram inbound + verify `sales_agent_trace_event` count
> 0 + `turn_start` + `turn_end` events visible. Requires Telegram
infrastructure live. Recommend Chris execute post-PR merge per § 7
post-deploy validation.

## Recommended next steps

1. Merge to development (already pushed @ d80d15f5).
2. Chris executes Telegram smoke test against real environment.
3. PM closes PR-2 + updates `current-state/sales_agent.md` if observability
   capability surfaces user-facing.
4. PI-1.1 S2 sprint reviews — handoff to S3 if applicable.

## Iter count

iter 1 — verdict PASS first pass. No iter 2/3 needed.
