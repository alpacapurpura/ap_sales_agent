<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-7 Agent_bridge in-process + leak_assertions defense-in-depth

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **APPROVED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (validator APPROVED, faithfulness clean)
- gate-output.json (full suite): used; T-7-scope GREEN per impl-log (43/43 ticket tests + 122/122 simulator + 36/36 sales_agent obs)
- Skills invoked: copilot-expert=N (sales_agent-only), sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y (4 H7 failure modes)

## Gate status (T-7 scope)
| Gate | Status | Errors |
|---|---|---|
| ruff | PASS (9 fixes — RUF002 ×3, N802, SIM300, UP041, RET501, SIM105, PYI034/036, PLR0911 noqa for H7 cement) | 0 |
| ruff-format | PASS | 0 |
| mypy --strict | PASS 4/4 (3 manual fixes — None-return, dict[str, object], cast RunnableConfig) | 0 |
| pytest (T-7 ticket-tests, 43/43 across 7 acceptance classes) | PASS | 0 |
| full simulator suite (122/122 + 5 skipped DB) | PASS | 0 |
| sales_agent obs downstream regression (36/36) | PASS | 0 |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `_internal/agent_bridge.py:170-218` — async node returns partial state dict, NEVER mutates. `_build_terminal_dict` (line 153-167) centralizes terminal partials so registry's `_agent_error_predicate` (T-4) reads consistent shape. NO `from __future__ import annotations` (story-wide cement). |
| 2 | Tool registration | PASS | n/a |
| 3 | Prompt cache architecture | PASS | n/a — agent_bridge consumes production `agent_app` (slot 5 BRAND_VOICE compiled by production knowledge_builder, untouched). |
| 4 | deepagents subagent isolation | PASS | n/a |
| 5 | Observability | PASS | `_internal/agent_bridge.py:310-345` — Step 6 builds `EvalSimulatorObservabilityContext` via T-5 factory; Step 7 invokes `await agent_app.ainvoke(...)` INSIDE `async with obs.observe_turn(...)` so turn_start/turn_end rows persist around the LangGraph stream. Best-effort: factory returns None on failure, bridge falls back to invocation without observability per `.claude/rules/copilot-observability.md` cement. |
| 6 | Eval goldens | PASS | n/a |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | Bridge consumes production `agent_app` — uses canonical sales_agent LLM router (no parallel layer). |
| 9 | Cost optimization | PASS | LLM cost recorded to `sales_agent_llm_call` (production agent's own callback) for agent runtime; eval-side observability writes eval_simulator tables. H6 cost-bucket separation honored at table level. |
| 10 | **Channel format & brand voice** | **PASS** | `_internal/agent_bridge.py:281-298` — `create_initial_state(channel_type='eval_simulator', ...)` marks downstream observability path. Production `agent_app` continues to compile brand voice from `personality_profiles.system_instruction` (untouched). T-7 imports verbatim `TenantKnowledgeBuilder.{build_identity, build_brand_voice}` (line 255-257) — paridad fixture pattern. |
| 11 | DDD compliance | PASS | All files under `tests/agentic_evals/sales_agent/simulator/_internal/`. Production `agent_app` consumed read-only via lazy import (line 251-260). |
| 12 | Tests / TDD | PASS | 43 ticket-tests across 7 acceptance classes per impl-log. |
| 13 | Mirror detection | PASS | `_internal/agent_bridge.py:24-34` § "Anti-duplication §0" lists reused symbols verbatim — `agent_app`, `TenantKnowledgeBuilder`, `create_initial_state`, `build_eval_simulator_observability_context`. Cero re-implementation. Step 0 grep evidence in impl-log. |
| 14 | Default-flip side-effect coverage | NA | T-7 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [D1, H7, H10]` (06-tickets.yaml:437). All three honored in code (D1 in-process invocation line 326-352; H7 4 failure modes line 200-208 + structlog events table in docstring; H10 leak_assertions module). Commit `39c25d96` body cites inline but no formal "## Decisions honored" section. |

## H7 failure-mode taxonomy verification
4 failure modes mapped 1:1 to `AgentErrorSubtype` enum (T-4):
- `TIMEOUT` → `simulator.agent_timeout` (line 352-360)
- `EMPTY_RESPONSE` → `simulator.agent_empty_response` (line 388-396)
- `HTTP_ERROR` → `simulator.agent_http_error` (line 361-372)
- `INVALID_STATE` → `simulator.agent_invalid_state` (line 220-244, 266-276, 299-308, 373-382)

Each emits structured structlog event (no string parsing). `# noqa: PLR0911` on line 170 explicitly justified in same line — cement of the H7 cardinal. Excellent.

## H10 leak_assertions verification
`_internal/leak_assertions.py:78-87` — `FORBIDDEN_LEAK_STRINGS: frozenset[str]` with EXACTLY 6 spec values (compiler v2, system_instruction, BRAND_VOICE, slot 5, ASÍ HABLAS, ASÍ NO). Frozenset chosen explicitly (immutable cement — line 95-98 docstring). `assert_no_leak` performs case-insensitive substring scan, emits `simulator.system_prompt_leak_detected` structlog warning, raises AssertionError. Defense in depth: bridge catches AssertionError to NOT corrupt transcript (line 404 — `with contextlib.suppress(AssertionError)`); adversarial smoke tests T-10 own the raise.

## Findings (file:line)

### FAIL
None.

### WARN
- [Cat 15] `06-tickets.yaml:437` declares `decisions_applicable: [D1, H7, H10]` → commit body cites inline but not formal "## Decisions honored" R6 section.

### info
- [Cat 5] `_internal/agent_bridge.py:122-145` — `_resolve_session_for_simulation` documented as T-7 stub; T-8 runner replaces with contextvar/thread-local. Tests monkeypatch the helper. Forward-looking design + integration boundary clearly documented.
- [Cat 1] `_internal/agent_bridge.py:336-346` — `cast("RunnableConfig", obs_ctx.langchain_config())` with rationale comment (line 327-332): `BaseObservabilityContext.langchain_config()` returns `dict[str, Any]` legacy contract; `Pregel.ainvoke` expects `RunnableConfig | None` TypedDict alias. Cast at call site satisfies mypy strict; runtime unchanged. Documented divergence honored.
- [Cat 7] `_internal/leak_assertions.py:51-58` — § Anti-duplication §0 explicitly states "NOT a mirror of any shared abstraction. The defense-in-depth forbidden-string list is simulator-specific (eval test infrastructure)". Justified NEW (not LIFT).
- [Cat 10] `_internal/agent_bridge.py:8-15` § Anti-duplication §0 — REUSE inventory documented in module docstring, paridad with `fixtures/entrypoint.py`. Excellent.

## Cross-scope flags
None.

## Research notes
None novel — T-7 honors `tessl__graceful-degradation` Rule 1 (timeouts) + Rule 2 (fallback) + Rule 6 (structured logs).

## Recommendations for builder fix-loop
None.

## Drift detection
NO drift. T-7 deliverables map literal to `06-tickets.yaml:447-449`.

## Verdict
APPROVED

## Findings
- 0 FAIL / 1 WARN (Cat 15 R6 cite trivial) / 4 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py`
- `backend/tests/agentic_evals/sales_agent/simulator/test_agent_bridge_unit.py`
- `backend/tests/agentic_evals/sales_agent/simulator/test_leak_assertions_unit.py`
- `docs/product/stories/eval-foundation-simulator-homologation/T-7-impl-log.md`

<!-- @pm: T-7-review.md ready (verdict=APPROVED). H7 taxonomy + H10 leak defense exemplary. -->
