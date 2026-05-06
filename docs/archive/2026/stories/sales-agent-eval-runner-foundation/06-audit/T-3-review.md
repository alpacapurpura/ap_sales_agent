<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-3 (sales-agent-eval-runner-foundation)

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-05
> Iter: 1
> Commit: 555c81c1
> Verdict: **PASS (APPROVED)**
> Generated: 2026-05-05T22:00Z

## Inputs
- CONTEXT-BRIEF.md: used (R24 acceptance gate satisfied — Validator pass: PASS, Faithfulness flag: clean)
- gate-output.json: used (any_fail=false, 4 PASS + 1 DEFERRED accepted per ticket plan)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y

## Gate status (from gate-output.json)
| Gate | Status | Errors |
|---|---|---|
| ruff_lint | PASS | 0 |
| ruff_format | PASS | 0 |
| pytest_architecture | PASS | 0 (823/823) |
| pytest_coverage | PASS | 0 (9012 PASS, 35 SKIP, 16 deselected integration) |
| pytest_eval_run_evals | DEFERRED | acceptable — eval-flag entrypoint gates at Story B T-5 smoke per ticket plan; A2 verified inline (0 mirror grep) |

Shared full-suite log with T-4 (HEAD 4a5d57a2 covers 555c81c1 + 429913a3) — single CI parity invocation per parallel-safety M3 sequencial test execution.

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `trajectory_spy.py:93-186` — spy is read-only observer, never mutates state; reads `outputs.get("next_node")` with `isinstance(outputs, dict)` guard; appends to its own in-memory lists only. No state schema change. |
| 2 | Tool registration | N/A | T-3 adds zero tools. Reads `serialized.get("name")` at `on_tool_start` for capture; no @tool decorators introduced. |
| 3 | Prompt cache architecture | N/A | T-3 surface invokes production `agent_app.ainvoke` honoring slot 5 BRAND_VOICE compiled from `PersonalityProfile.system_instruction` (entrypoint.py:160-162). Decision B6 honored — zero override. T-3 introduces no LLM call surface. |
| 4 | deepagents subagent isolation | N/A | sales_agent uses LangGraph supervisor pattern, not deepagents `task` tool. T-3 does not touch subagent topology. |
| 5 | Observability | PASS | Production `SalesAgentObservabilityContext` factory reused verbatim (entrypoint.py:130-148); spy appended to `RunnableConfig.callbacks` list (entrypoint.py:181) — production handler runs first (DB writes), spy second (in-memory). PII via `sanitize_payload` reuse from shared (artifacts.py:30, 87, 94). Best-effort try/except + `structlog.warning` on every spy callback method body (trajectory_spy.py:118-123, 147-152, 181-186). |
| 6 | Eval goldens | PASS (deferred) | T-3 is foundation only. A1 acceptance test `test_trajectory_spy_captures_first_specialist_and_tool_calls` (line 623) is `@pytest.mark.eval` — properly skipped on default CI; runs with `--run-evals` at T-5 smoke gate. Goldens authored at T-5 (Story B). |
| 7 | RAG / Qdrant hygiene | N/A | T-3 makes no Qdrant calls. |
| 8 | LLM provider routing | N/A | T-3 invokes production path; no model literal hardcoded. |
| 9 | Cost optimization | PASS | T-3 is test harness with `<5s` extra latency per CONTEXT-BRIEF §14. Cost recording (Capa 4) reused verbatim from production handler. |
| 10 | Channel format & brand voice | PASS | Decision B6 honored — `TenantKnowledgeBuilder.build_brand_voice(tenant_id)` invoked from production path (entrypoint.py:162). Channel `"eval_harness"` registered at T-2 in shared registry — no mirror. Voseo cleanup completed at fixtures/tenant.py:158 (`Configurá voz...guardá` → `Configura la voz...guarda`); 0 voseo matches in T-3 modified files (auditor verified independently). |
| 11 | DDD compliance | PASS | All T-3 surfaces live in `tests/agentic_evals/sales_agent/{runner,fixtures}/` — zero src/modules touch, zero src/shared touch. Read-only consumer of canonical exports. |
| 12 | Tests / TDD | PASS | 11 new meta-tests (test_eval_runner_fixtures.py:286-623) covering A1/A2/A3/A4 acceptance, best-effort, reset, JSON-serialisability, idempotent rerun, PII redaction. AST guard at line 313 walks `runner/` for any executable `BaseAgentCallbackHandler` reference. RED→GREEN sequence honored per builder impl-log §"Tests added". |
| 13 | Mirror detection | PASS (CRITICAL) | Anti-duplication §0 GATE: (a) `grep -rn "BaseAgentCallbackHandler" backend/tests/agentic_evals/sales_agent/runner/` → 0 matches (auditor verified independently — exit 1); (b) `grep -rn "def sanitize_payload\|class FXResolver\|class TurnEnvelope\|class PricingResolver" backend/tests/agentic_evals/` → 0 matches (auditor verified); (c) `from src.shared.agent_observability.recording.sanitization import sanitize_payload` at artifacts.py:30 — verbatim reuse, no mirror; (d) `BaseCallbackHandler` parent (LangChain native) is the test harness contract per CONTEXT-BRIEF §3. EXTEND via composition decision ratified by architect. |
| 14 | Default-flip side-effect coverage | NA | T-3 modifies zero `core/config.py` flag defaults. Commit body explicit: "No flag flips in this commit. T-3 surfaces are tests/ only — zero src/modules touched; zero src/shared touched." |
| 15 | Decisions honored cite (R6) | PASS | Commit body `555c81c1` § "Decisions honored (arch-agentic.md)" cites B1-B7 verbatim each tied to concrete implementation evidence: B1 ↔ trajectory_spy.py:48 (`from langchain_core.callbacks import BaseCallbackHandler`); B2 ↔ trajectory_spy.py:109 + 116 (filter on `_TERMINAL_NEXT_NODE_VALUES`); B3 ↔ trajectory_spy.py:118-123/147-152/181-186 (try/except + structlog.warning); B4 ↔ artifacts.py:30+87+94 (verbatim shared import); B5 ↔ entrypoint.py:179-181 (compose append); B6 ↔ entrypoint.py:160-162 (TenantKnowledgeBuilder production path, no override); B7 ↔ T-3-impl-log.md §Decisions honored row B7 (deferred to Story 7 voice grader). All 7 architect decisions accounted for; none silently ignored. |

## Findings (file:line)

### FAIL
- (none)

### WARN
- (none)

### info
- [Cat 12] `test_eval_runner_fixtures.py:619-623` — eval-marker test docstring documents A1 acceptance contract; smoke gate at T-5 will exercise it with `--run-evals`. No action; observation only.
- [Cat 5] `entrypoint.py:184-195` — best-effort fallback when obs_ctx is None still attaches spy via minimal config. Acceptable resilience pattern (graceful-degradation Rule 6). No action.
- [Cat 9] `trajectory_spy.py:94` — `del parent_run_id, kwargs` idiom prevents linter unused warnings + signals intentional drop. Stylistic; documented.

## Cross-scope flags
None. T-3 lives entirely in `backend/tests/agentic_evals/sales_agent/`. Zero touches outside agentic test harness scope.

## Downstream regression scope (Step 4.5 mandatory)

Per `.claude/rules/auditor-downstream-regression.md` lookup:

| Surface modified (path) | Tabla SSoT entry | Required downstream tests | gate-runner status |
|---|---|---|---|
| `backend/tests/agentic_evals/sales_agent/runner/*.py` (NEW test harness) | NOT LISTED — test-only, no shared/ or modules/ src touched | none required | n/a |
| `backend/tests/agentic_evals/sales_agent/fixtures/{entrypoint,tenant}.py` | NOT LISTED — test fixtures only | none required | n/a |
| `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` | NOT LISTED — meta-tests only | none required | n/a |

Builder report (impl-log §"Quality gates"): `tests/modules/{copilot,sales_agent}/observability/` 200 PASS — confirmed regardless. R3 satisfied: no shared/ ripple.

## Research notes
T-3 invokes well-precedented patterns:
- LangChain `BaseCallbackHandler` composition — verified via `backend/.venv/lib/python3.12/site-packages/langchain_core/callbacks/base.py:493` per builder state-of-the-art validation.
- LangGraph supervisor pattern + `state["next_node"]` SSoT — anchored in 03-arch-agentic.md § "Topology classification" (knowledge cutoff Jan 2026 + tessl__langgraph skill loaded; no novel pattern introduced; no live WebFetch required).
- Anthropic prompt caching invariants — N/A this ticket; honored at production runtime path via Decision B6 (no test-only override).

Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026. T-3 delivers established LangChain primitives (`BaseCallbackHandler`, `RunnableConfig.callbacks`); no canonical doc divergence detected.

## Recommendations for builder fix-loop
None — APPROVED on iter 1. Builder may publish `tests-passing` → `audit-passed` state per `docs/process/ticket-states.md`.

## Drift detection (CONTRACT vs code)
NO drift. Architecture decisions B1-B7 in 03-arch-agentic.md ↔ commit body `555c81c1` ↔ implementation files: 1:1 traceable per Cat 15 evidence row above.

---

**Verdict: APPROVED.** Composition over subclass exemplar. Anti-duplication §0 satisfied at 4 levels (lexical grep, AST walk, type-system `not issubclass`, builder commit body declaration). PII safety preserved via verbatim shared `sanitize_payload` reuse. Production observability path untouched — zero risk to live sales_agent traffic.
