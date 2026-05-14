# T-tools-4 — Implementation Log

**Ticket:** T-tools-4 (Tool `treatment_followup_check` — workflow node + Haiku classifier)
**Owner:** Claude Opus 4.7 (1M context) — R23 mandatory production AGENTIC code
**Date:** 2026-05-14 (W9 Sesion 4)
**State:** developed (tests-passing)
**Estimate:** 4h · **Actual:** ~1.5h (single iter, GREEN first run)
**Decisions applied:** D1 (DDD Inside-Out tool→service→repo via Protocol DI) + D3 (LangGraph 2.0 workflow internal node)
**Validators:** V-AE-5 GREEN (62/62 tools tests) · V-AE-15 unit-level GREEN (cost budget asserted in `test_cost_budget`)

---

## Step 0 — Anti-duplication grep (cardinal pre-write)

```bash
$ grep -rln "treatment_followup_check|TreatmentFollowupCheck" /home/chris/luana-platform/ 2>/dev/null
/home/chris/luana-platform/vitalia/config/brand.yaml
/home/chris/luana-platform/vitalia/backend/tests/unit/test_extensions_register_all.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/copilot/workflows/treatment_followup_workflow.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/tools/__init__.py  # placeholder docstring
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/prompts/compose.py

$ grep -rln "record_d5_response|record_d14_response|record_d90_response" /home/chris/luana-platform/ 2>/dev/null
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py  # spec ref only

$ grep -rln "treatment_followup_check" /home/chris/AISALESHT/backend/src/ 2>/dev/null
(empty)
```

**Verdict:** zero collisions. Tool is NEW vertical-medical specific (per 02-design § 6.2 anti-duplication note). Existing references are placeholders + workflow nodes that *will* invoke this tool from T-workflow-1 (already built). Anti-duplication SSoT consumed:
- `sanitize_payload` from `luana_core_observability.recording.sanitization` (NEVER re-implemented)
- `_detect_safety_signal` pattern mirrored from `treatment_followup_workflow._detect_safety_signal` — local copy in tool to avoid circular import (workflow imports tool's effects via WorkflowTransitioner Protocol). Lockstep evolution captured in module docstring.

---

## Skills consulted (Step 0 GATE)

| Skill | Decision |
|---|---|
| **copilot-expert** | Best-effort observability via try/except + structlog warning per `copilot-observability.md`. Tool turn NEVER breaks on observability fail. PII sanitize via canonical `sanitize_payload` (NEVER local). LangGraph workflow node returns partial state — never mutates. |
| **sales-agent-expert** | Tool ctx.tenant_id injection at boundary; repos receive tenant_id at construction. R23 Opus-only enforcement honored. SSoT shared abstractions consumed (sanitize_payload, observability protocols). |
| **tessl__langgraph** | Tool consumed by LangGraph workflow node via WorkflowTransitioner Protocol — decouples tool from graph internals. State mutations stay in workflow (T-workflow-1); tool surfaces transition trigger only. |
| **tessl__graceful-degradation** | LLM classifier wrapped in `asyncio.wait_for(timeout=5s)` per Rule 1. Per Rule 2: fallback neutral score 3 (per spec § 6.2 error mode b). Per Rule 5: per-dependency isolation (LLM, audit_log, trace_event, workflow_transitioner each in own try/except — failure of one does NOT cascade). Structured warning logs per Rule 6. |
| **tessl__pytest-api-testing** | Factory-fixture-style in-memory fakes (`_FakeFollowupRepo`, `_FakeAdherenceRepo`, etc) with capturing repos for observability assertions. `@pytest.mark.parametrize` for safety keyword variations + record action variants. asyncio_mode=auto inherited from `pyproject.toml`. |
| **tessl__fastapi** | N/A — tool is workflow-internal, not exposed as FastAPI endpoint. |
| **claude-api** | Cost budget per record_* call ≤$0.003 USD enforced at unit level via `_StubLLMClassifier(cost_per_call_usd=0.0014)` × 2 calls. Real LiteLLM dispatch lands in production wiring (via `luana_core_llm.providers.litellm.LiteLLMService`) — Protocol surface keeps tool deterministic. |

---

## Implementation summary

### Files
- `vitalia/backend/src/modules/vitalia/agentic/tools/treatment_followup_check.py` (NEW, ~620 LOC)
- `vitalia/backend/tests/agentic_evals/tools/test_treatment_followup_check.py` (NEW, 24 tests)

### Surface

**Pydantic input/output:**
- `TreatmentFollowupCheckInput`: `treatment_id` (UUID) + `action` (Literal[7 values]) + `response_text` (≤4000 chars) + `adherence_score_override` (1-5) + `sentiment_override`
- `TreatmentFollowupCheckOutput`: `current_step` + `last_response_at` + `adherence_score` + `sentiment` + `next_action_planned` + `next_scheduled_at` + `session_notes_summary` + `safety_triggered` + `safety_keywords_detected` + `cost_usd`

**Handler:** `treatment_followup_check(input, *, tenant_id, followup_repo, adherence_repo, llm_classifier, workflow_transitioner, trace_event_repo=None, audit_log_repo=None, turn_id=None, span_id=None)`

**7 actions semantic split:**
| Action | LLM cost | Persistence | Workflow transition |
|---|---|---|---|
| `initial_d{5,14,90}_ping` | $0 (future Sonnet voice composer scope T-prompts-X) | None | None |
| `record_d{5,14,90}_response` (no safety) | ≤$0.003 (2 Haiku) | adherence_record + followup advance | None (workflow advances on next cron tick) |
| `record_d{5,14,90}_response` (safety) | $0 (skip LLM) | adherence_record (safety_alert) + followup→paused_safety | `target_step="paused_safety_escalation"` |
| `snapshot_status` | $0 | None | None |

**Dependencies via Protocol (DI):**
- `_FollowupRepoLike` — `get_by_id` + `save` (matches existing `TreatmentFollowupRepository` from T-be-3)
- `_AdherenceRepoLike` — `add(...)` only (Protocol surface; concrete repo lands future ticket)
- `_LLMClassifierLike` — `classify_adherence` + `classify_sentiment` (returns `(value, cost_usd)` tuple)
- `_WorkflowTransitionerLike` — `transition_to(target_step, paused_reason)` (adapter to LangGraph `ainvoke` lives at workflow node call site)
- `_TraceEventRepoLike` + `_AuditLogRepoLike` — best-effort observability sinks

### Safety keyword scan (deterministic, pre-LLM)

Local copy of `_detect_safety_signal` mirrored from `treatment_followup_workflow.py` (T-workflow-1):
- 9 keywords: `dolor pecho`, `no puedo respirar`, `alergia`/`alérgica`/`alergica`, `reacción`/`reaccion`, `sangrado`, `fiebre alta`
- 3 phrases: `mucho dolor`, `dolor fuerte`, `no me siento bien`
- Diagnosis-request regex per § 2.2
- Negation guard: 7 prefixes (`sin `, `no `, `ni `, `ningún `, `ninguna `, `nunca `, `tampoco `)

**Lockstep with workflow:** local copy avoids circular import (workflow→tool→workflow); when patterns evolve, both must update together — captured in module docstring `_detect_safety_signal` comment.

### Graceful degradation

- LLM classifier: `asyncio.wait_for(timeout=5s)` per call → on TimeoutError/Exception fallback `(adherence=3, sentiment=None, cost=0)` + structlog warning with `dependency`, `exc_type`, `fallback`. Each classifier in own try/except (per-dep isolation Rule 5).
- audit_log + trace_event + workflow_transitioner: each wrapped in own try/except → log warning + continue. Tool turn NEVER breaks.
- Followup row IS the SSoT — workflow_transitioner failure logged but tool returns success result (workflow re-derives from row state on next cron tick).

### Anti-patterns avoided

- ❌ Did NOT mirror sanitize_payload locally (consumed canonical from `luana_core_observability`)
- ❌ Did NOT add tenant_id to input schema (security boundary — ctx-injected only)
- ❌ Did NOT call repos directly without Protocol decoupling (concrete repos receive tenant_id at construction)
- ❌ Did NOT skip best-effort observability wrappers (every persistence sink has try/except + warning)
- ❌ Did NOT bake LLM model wire-name into tool (Classifier Protocol — production wiring chooses Haiku via LiteLLM proxy)
- ❌ Did NOT couple to LangGraph internals (WorkflowTransitioner Protocol — adapter at call site)
- ❌ Did NOT log raw response_text in trace/audit (sanitized payload + SHA-256 hash for forensic correlation)

---

## TDD log

### RED (1 iter)
- 24 tests written first against unimplemented module
- Confirmed RED with `ModuleNotFoundError: No module named 'src.modules.vitalia.agentic.tools.treatment_followup_check'`

### GREEN (1 iter — first run)
```
24 passed in 0.11s
```

Test breakdown:
- 1 schema invariant — `test_tenant_id_not_in_schema` (security boundary)
- 1 schema invariant — `test_action_literal_covers_seven_actions` (7 actions per spec)
- 1 acceptance A1 — `test_safety_escalation` (record_d5 safety → paused_safety_escalation transition)
- 1 acceptance A2 — `test_cost_budget` (record_* ≤$0.003 USD)
- 3 parametrized — `test_initial_ping_actions_no_persist_on_compose` (D5/D14/D90 ping)
- 3 parametrized — `test_record_response_persists_adherence_and_advances` (D5/D14/D90 record)
- 1 — `test_snapshot_status_is_read_only_no_llm_no_persist`
- 1 — `test_cross_tenant_treatment_returns_not_found` (tenant isolation)
- 1 — `test_trace_event_failure_does_not_break_turn` (best-effort obs)
- 1 — `test_audit_log_failure_does_not_break_turn` (best-effort audit)
- 1 — `test_llm_failure_falls_back_to_neutral_score` (graceful degradation)
- 1 — `test_adherence_override_skips_llm_call`
- 5 parametrized — `test_safety_keyword_variations_trigger` (5 trigger patterns)
- 1 — `test_negation_does_not_trigger_safety` (`sin sangrado`/`no dolor`)
- 1 — `test_latency_p99_under_budget_with_stubbed_classifier` (<250ms handler overhead)
- 1 — `test_trace_event_sanitizes_response_text` (PII redaction)

### REFACTOR
- ruff format applied (extracted long lines + braces — no semantic change)
- ruff check: All checks passed

---

## Validators run

```bash
# V-AE-5 — Tools tests
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
============================== 62 passed in 0.52s ==============================

# Lint + format
$ .venv/bin/ruff check src/modules/vitalia/agentic/tools/treatment_followup_check.py tests/agentic_evals/tools/test_treatment_followup_check.py
All checks passed!
$ .venv/bin/ruff format --check src/modules/vitalia/agentic/tools/treatment_followup_check.py tests/agentic_evals/tools/test_treatment_followup_check.py
2 files already formatted
```

**V-AE-15 cost budget (unit level):** asserted in `test_cost_budget` with `_StubLLMClassifier(cost_per_call_usd=0.0014)` × 2 calls = $0.0028 < $0.003 ceiling. Production validation lands in future `tests/agentic_evals/cost_budget/test_cost_budget_followup_turn.py` (out of T-tools-4 scope per spec § 6.2).

---

## Downstream regression (R3 + R21)

Per `.claude/rules/auditor-downstream-regression.md`:

```bash
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest \
    tests/agentic_evals/tools/ \
    tests/agentic_evals/workflows/ \
    tests/unit/test_extensions_register_all.py \
    -v --tb=short
```

**Result:**
- 62 passed (all tools tests including this new one + appointment + consent + payment)
- 1 ERROR pre-existing (langgraph missing module in workflow tests — not introduced by T-tools-4; deferred install per T-workflow-1 D10 RedisSaver-swap pattern)
- 0 new test regressions introduced

T-tools-4 surface (`agentic/tools/treatment_followup_check.py`) does not modify shared/ or any other downstream-coupled surface per anti-duplication.md SSoT table. No new R3 entry required (vitalia-local tool, scoped to single test file).

---

## Out-of-scope (anti-creep)

- ❌ Concrete `AdherenceRecordRepository` implementation — Protocol surface only; concrete repo lands when needed downstream
- ❌ Concrete `WorkflowTransitioner` adapter to LangGraph `ainvoke` — adapter lives at workflow node call site (T-workflow-1 nodes wire it)
- ❌ Sonnet voice-aware ping message composer — deferred to T-prompts-X (initial_*_ping returns context only for caller dispatch)
- ❌ Real LiteLLM proxy classifier wiring — production code consumes Protocol, real impl wraps `luana_core_llm.providers.litellm.LiteLLMService`
- ❌ Idempotency window enforcement at adherence_repo level — `_IDEMPOTENCY_WINDOW_SECONDS` constant present for future use; concrete repo enforces when added

---

## Files modified

```
vitalia/backend/src/modules/vitalia/agentic/tools/treatment_followup_check.py  (NEW)
vitalia/backend/tests/agentic_evals/tools/test_treatment_followup_check.py    (NEW)
```

Final commit (post-result doc).
