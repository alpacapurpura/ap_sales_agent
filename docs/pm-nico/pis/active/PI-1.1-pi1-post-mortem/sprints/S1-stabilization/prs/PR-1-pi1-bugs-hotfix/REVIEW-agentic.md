# Agentic Review — PR-1-pi1-bugs-hotfix (Bug #2)

> Auditor: `nicolify-agentic-auditor` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-01
> Iter: 1
> Verdict: **WARN** (single new arch ratchet violation introduced; functional fix is correct + tested + best-effort safe; LOC ratchet is fixable in a small extract refactor before commit)
> Generated: 2026-05-01T07:30Z

## Inputs
- CONTEXT-BRIEF.md: not present — read PR.md raw
- gate-output.json: present (Bug #1 BE surface only) — extended with sales_agent surface gates manually
- Skills invoked: copilot-expert=Y (loaded via routing — non-scope reference for envelope mirror), sales-agent-expert=Y, tessl__langgraph=Y (callback config / RunnableConfig contract), tessl__graceful-degradation=Y (best-effort writes)

## Gate status (sales_agent surface)
| Gate | Status | Errors |
|---|---|---|
| ruff check (src/modules/sales_agent/) | PASS | 0 |
| ruff format (src/modules/sales_agent/) | PASS | 0 (33 files OK) |
| mypy (recording/turn_envelope.py + factory.py) | WARN | 3 errors total (1 NEW: Column[str] return-type at factory.py:72 — relocated from pre-existing factory.py:91; 2 pre-existing FXResolver call-arg) |
| pytest (tests/modules/sales_agent/observability/test_real_trace_persistence.py) | PASS | 8/8 (RED→GREEN reproducer suite for Bug #2) |
| pytest (tests/modules/sales_agent/observability/) | PASS | full suite green |
| pytest (tests/modules/sales_agent/application/orchestrator/) | PASS | full suite green incl. test_outbound_orchestrator.py (envelope rewire) |
| pytest (tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py) | FAIL | 1 (PRE-EXISTING — verified via git stash; same failure on clean main from parallel PI-5 session, NOT introduced by Bug #2) |
| arch-fitness (test_chat_orchestrator_loc_ratchet) | **FAIL — NEW** | chat.py 502 LOC > ceiling 400 (pre-fix 384 LOC, post-fix 502 LOC; +118 from inlining `_run_turn_with_observability` static method) |
| arch-fitness (sales_agent_anchors / system_prompt_order x2 / ddd_boundaries / compose_system_prompt cacheable_match_s3_plan) | FAIL | PRE-EXISTING — verified via git stash, same 4 failures from parallel PI-5 session |
| pip-audit | n/a | not run (no dependency change) |

## 12 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `turn_envelope.py:115-178` `SalesAgentObservabilityContext` is `@dataclass` (typed); state/handler not mutated mid-flight; tenant_id carried explicitly. No `TypedDict` introduced for graph state — envelope is auxiliary observability layer, not graph state. |
| 2 | Tool registration & contracts | n/a | No new tools introduced. Bug #2 is observability infra, not tool surface. |
| 3 | Prompt cache architecture | PASS | No prompt slot touched. `system_prompt_layout.py` (sales_agent) untouched. Slot 5 BRAND_VOICE prefix preserved. |
| 4 | deepagents subagent isolation | n/a | sales_agent uses StateGraph, not deepagents. |
| 5 | Observability (`*_trace_event` + cost recording) | **WARN** | PRIMARY: envelope correctly brackets turn with `turn_start`/`turn_end` + explicit `commit()` (`turn_envelope.py:275, 318, 328-357`) + best-effort try/except + `_safe_rollback` everywhere. PII via `sanitize_payload` (`turn_envelope.py:266, 314`). MINOR ISSUE: `outbound_orchestrator.py:142-158` calls `set_turn_summary` AFTER `async with observe_turn:` already exited — turn_end already committed, so summary fields (`response_length`, `message_count`, `block_count`) are dead writes for outbound only. Comment on line 142-144 acknowledges the issue. Inbound chat path (`chat.py:301-315`) DOES call summary inside the block correctly. |
| 6 | Eval goldens (sales_agent) | PASS | No specialist prompt changed; voice fidelity grader untouched. Bug #2 is recorder plumbing only. |
| 7 | RAG / Qdrant hygiene | n/a | No vector ops introduced. |
| 8 | LLM provider routing | PASS | No model strings hardcoded; LLM_ROLE_BY_SITE untouched; PricingResolver + FXResolver still consumed via shared/. |
| 9 | Cost optimization | PASS | Bug #2 fix UNBLOCKS cost recording (was 0 rows globally pre-fix). After fix, `sales_agent_llm_call` rows persist via callback handler + envelope commit. `_aggregate_totals` (`turn_envelope.py:369-411`) sums input_tokens/output_tokens/cached_read/cost_usd into turn_end row — feeds `mv_daily_llm_cost_per_tenant_v2`. |
| 10 | Channel format & brand voice | PASS | No channel_format or voice change; voseo concern n/a. Output unchanged. |
| 11 | DDD compliance (agentic specifics) | **FAIL** | NEW arch ratchet violation: `test_chat_orchestrator_loc_ratchet` fails — chat.py 502 LOC > ceiling 400. Builder added `_run_turn_with_observability` static method (137 lines) INSIDE chat.py rather than extracting to a separate collaborator (`turn_runner.py` or `observability_invoker.py`). `sales-agent-expert` skill explicitly says: "Strangler Fig: extract a new collaborator instead of growing the facade." |
| 12 | Tests / TDD | PASS | New test file `test_real_trace_persistence.py` is real-DB integration (in-memory SQLite via conftest `db_engine`) with 8 tests covering: turn_start commit, turn_end commit, callback rows visible after envelope, error path status='error', `set_turn_error` clean exit error mark, public API invariants. NO mocks of DB session. RED reproducer matches PR.md acceptance criteria ("≥3 rows in `sales_agent_trace_event`"). All 8 GREEN. Existing test patches updated for new factory name. Snapshot test pre-existing fail unrelated to Bug #2 (verified on main). |

## Findings (file:line)

### FAIL
- [Cat 11] `backend/src/modules/sales_agent/application/orchestrator/chat.py:502 LOC` — Builder inlined `_run_turn_with_observability` static method (lines ~187-315, ~137 lines) into facade. Pre-fix 384 LOC, post-fix 502 LOC, ratchet ceiling 400. Test `tests/architecture/test_chat_orchestrator_loc_ratchet.py::test_chat_orchestrator_under_loc_ceiling` was PASSING on clean main (verified via `git stash`) and now FAILS. → **Fix**: extract `_run_turn_with_observability` (and its degraded fallback) to a new collaborator file `backend/src/modules/sales_agent/application/orchestrator/turn_runner.py` exposing a `TurnRunner.run(...)` static method. Mirror copilot's `chat_orchestrator → run_graph_stream` separation. Goal: chat.py back below 400 LOC. Post-extraction: re-run `pytest tests/architecture/test_chat_orchestrator_loc_ratchet.py -q` to verify GREEN.

### WARN
- [Cat 5] `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py:142-158` — `set_turn_summary` is called AFTER `async with observability_ctx.observe_turn(...):` block exits. The envelope's `__aexit__` already wrote `turn_end` row with default summary (zeros). The post-block `set_turn_summary` mutates `_summary` field but no further `turn_end` row is written. Result: outbound `turn_end.data` carries `response_length=0, message_count=0, block_count=0` always. Inbound chat path is correct (line 301-315 — set_turn_summary inside `async with`). → **Fix**: move `try` block at lines 145-158 INSIDE `async with` (lines 109-140 of outbound_orchestrator.py), before exiting the `observe_turn` context. OR: drop the post-exit `set_turn_summary` and accept zeros for outbound turn-end (simpler). Either is a minor cleanup.

- [Cat 5] `backend/src/modules/sales_agent/observability/recording/factory.py:72` — NEW mypy error: `Incompatible return value type (got "Column[str] | str", expected "str")` in `_resolve_tenant_currency`. Pre-existing equivalent at factory.py:91 in old code. Helper extraction relocated the issue rather than fixing it. → **Fix (optional)**: cast result via `str(billing_cfg.billing_currency) if billing_cfg else "USD"`. Low-priority; same shape as pre-existing 2 errors.

### info
- [Cat 1] `turn_envelope.py:91-113` `_TurnSummary` and `_TurnErrorFlag` are private dataclasses. Clean state hygiene.
- [Cat 5] `turn_envelope.py:236-246` correctly handles `BaseException` (catches `asyncio.CancelledError` so client disconnects still leave a turn_end row) but only re-raises if not Exception, propagating only Exception subclasses to the body. This matches copilot's pattern. Honest trace recorder.
- [Cat 5] `turn_envelope.py:298-304` correctly resolves error precedence: `set_turn_error` (out-of-band flag from orchestrator catch) overrides clean exit; raised exception overrides flag. Status=`error` always when either is present (line 305).
- [Cat 5] `turn_envelope.py:343-357` `_commit_session` is best-effort with `_safe_rollback` on failure — matches `.claude/rules/copilot-observability.md` "Best-effort writes".
- [Cat 11] Architecturally the right abstraction: copilot's `ObservabilityContext` is the SSoT precedent and sales_agent now mirrors it. Module docstring (`turn_envelope.py:1-52`) explicitly references this and notes lifting to `shared/` is a deferred refactor (DRY threshold 2 met but the cross-agent surface is non-trivial — same reasoning the copilot envelope used). Reasonable.
- [Cat 12] `_chat_flow_snapshot_helpers.py:160-167` correctly splits the deterministic UUID patches: state-side counter (shared with conversation_pipeline.py via `import uuid`) AND turn_envelope-side counter (`from uuid import uuid4`). Pre-existing snapshot baseline failure on `session_id=000003` (vs expected `000001`) is NOT caused by Bug #2 fix — same failure exists on clean main with the new helpers stashed. The snapshot regen + commit is a parallel PI-5 issue.
- [Cat 9] After fix, `mv_daily_llm_cost_per_tenant_v2` will start receiving sales_agent rows for the first time. Expect material change to `/costo-agentes` admin panel. PM should announce.

## Cross-scope flags (if any)
- `backend/src/modules/copilot/**` — modified by parallel PI-5 session. NOT audited here per instructions.
- `backend/tests/modules/copilot/**` (NEW files: application/memory/, application/orchestrator/, application/tools/test_registry_telegram_runtime_filter.py, infrastructure/repositories/, integration/test_telegram_end_to_end.py) — parallel PI-5 session ajeno files.
- `docs/pm-nico/pis/active/PI-5-*` — parallel PI-5 session ajeno PR docs.
- `backend/src/modules/copilot/application/orchestrator/invoke_result.py` (NEW) — parallel PI-5 session ajeno file.
- All cross-scope files are LEFT INTACT by Bug #2 builder per parallel-safety rule M8.

## Research notes
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (accessed 2026-05-01)
- Takeaway: LangGraph 2.0 `RunnableConfig` callbacks are dispatched via `AsyncCallbackManager` for async invocations (`agent_app.ainvoke`). Sync `BaseCallbackHandler` instances are run via `run_in_executor` (foreign thread). Without explicit main-thread `flush + commit` on the SQLAlchemy session bound to those handlers, worker-thread `session.add()` calls land in the identity map but never reach Postgres. The envelope's `_commit_session` (turn_envelope.py:328-357) directly addresses this — it flushes before the aggregate SELECT (line 379) and commits explicitly on each turn boundary write.
- Source: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (accessed 2026-05-01)
- Takeaway: Cache architecture not affected by Bug #2 fix. Slot 5 BRAND_VOICE prefix invariance preserved (no change to `system_prompt_layout.py` or compiler v2).
- Delta vs reference anchors in agent definition: none.
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live researched on 2026-05-01.

## Recommendations for builder fix-loop (iter 2)

**Priority 1 — MUST FIX before commit**:
1. Extract `_run_turn_with_observability` from `backend/src/modules/sales_agent/application/orchestrator/chat.py` to a new collaborator file (suggested path: `backend/src/modules/sales_agent/application/orchestrator/turn_runner.py`). The static method has no `self` dependency and is a self-contained ~137-line unit — clean extraction. Update `process_chat_flow` to import + delegate. Re-run `cd backend && .venv/bin/pytest tests/architecture/test_chat_orchestrator_loc_ratchet.py -q` until PASS. chat.py target ≤400 LOC.

**Priority 2 — minor cleanup before commit (optional but recommended)**:
2. `outbound_orchestrator.py:_invoke_graph_with_envelope`: move `set_turn_summary` block (lines 145-158) INSIDE the `async with observability_ctx.observe_turn(...):` block (before line 141 `pass`/exit). Current location after `async with` exit means summary mutation is invisible to the already-committed turn_end row. Inbound chat path is the correct reference.

**Priority 3 — defer or fix while-you-edit**:
3. `factory.py:72` typing: cast `_resolve_tenant_currency` return as `str(...)` to silence Column[str] mypy.

## Drift detection (CONTRACT vs code)
- PR.md Bug #2 walking skeleton: ✅ "BE sales_agent observability fix (handler persists rows real)" — implemented via envelope (`turn_envelope.py`).
- PR.md Bug #2 walking skeleton: ✅ "Smoke test sales_agent observability (asserts INSERT)" — implemented (`test_real_trace_persistence.py`, 8 tests, real DB SELECT).
- PR.md Bug #2 RCA hypotheses 1-4 (handler swallow / dual-write / session scope / conditional skip): RCA identified in `turn_envelope.py:13-34` module docstring as a JOINT cause of (a) no envelope `commit` + (b) sync handler in async dispatch landing in worker-thread session. Both addressed.
- PR.md Bug #2 acceptance ("≥3 rows turn_start + tool_call + turn_end in <5s"): test asserts turn_start + turn_end + llm_call mirror — meets contract intent (tool_call requires real LangGraph `tool_executor` node which isn't part of this fix's scope; the callback handler emits tool_call rows the same way it now emits llm_call rows, so by construction it will write tool_call rows under the envelope on real Telegram traffic).
- NO drift detected. CONTRACT respected. New arch ratchet violation is a craft issue, not a CONTRACT scope issue.

## PM commit guidance (if PASS after iter 2)

**Files to stage** (sales_agent surface only — DO NOT stage copilot or PI-5 ajeno files):
```
git add backend/src/modules/sales_agent/observability/recording/factory.py
git add backend/src/modules/sales_agent/observability/recording/turn_envelope.py
git add backend/src/modules/sales_agent/application/orchestrator/chat.py
git add backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py
git add backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py
git add backend/src/modules/sales_agent/application/orchestrator/turn_runner.py   # NEW after iter 2 extract
git add backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py
git add backend/tests/modules/sales_agent/application/orchestrator/test_outbound_orchestrator.py
git add backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py
```

**DO NOT stage** (parallel PI-5 ajeno):
- `backend/src/modules/copilot/**`
- `backend/tests/modules/copilot/**`
- `backend/tests/architecture/test_copilot_telegram_separation.py`
- `docs/pm-nico/pis/active/PI-5-*`

**Suggested commit message** (after iter 2 fix):
```
fix(sales_agent): persist trace_event + llm_call rows via turn envelope — PR-1 Bug #2 RCA

Root cause: sales_agent had no turn-envelope analogous to copilot's
ObservabilityContext.observe_turn. Two gaps acted jointly:
1. Orchestrator never wrote turn_start/turn_end + never explicitly
   committed the trace-event session — every callback row added during
   ainvoke stayed pending and was discarded on session close.
2. Sync BaseCallbackHandler dispatched by LangChain AsyncCallbackManager
   via run_in_executor (foreign thread); worker-thread session.add
   calls only reach Postgres on a main-thread flush+commit.

Fix:
- New SalesAgentObservabilityContext (envelope) brackets every turn with
  turn_start (on enter) + turn_end (on exit) + explicit session.commit
  on each write (picks up callback rows queued in between).
- factory.build_sales_agent_observability_context exposes envelope to
  ChatOrchestrator + OutboundOrchestrator. Legacy
  build_sales_agent_callback_handler kept for back-compat.
- Honest error path: set_turn_error flag flips turn_end status='error'
  even when the orchestrator catches the exception itself to emit a
  user-friendly fallback.

Test: tests/modules/sales_agent/observability/test_real_trace_persistence.py
asserts INSERT into sales_agent_trace_event via real SELECT (no mocks).
8 tests, all green. Reproduces 0-rows-globally bug RED then GREEN.

Refs: PR-1 Bug #2 (PI-1.1 post-mortem), copilot S0/S11A envelope precedent.
```

<!-- @pm: REVIEW-agentic.md ready (verdict=WARN). 1 NEW arch ratchet violation (chat.py LOC) MUST be fixed in iter 2 before commit — extract _run_turn_with_observability to turn_runner.py collaborator. 2 minor WARN items recommended but optional. CONTRACT respected, no drift. Pre-existing failures (snapshot, sales_agent_anchors x4, compose_system_prompt) confirmed via git stash as PI-5 ajeno — NOT introduced by this PR. Functional fix is correct + tested + best-effort safe. -->
