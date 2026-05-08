<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-8 LangGraph graph compose + run_simulation orchestrator + artifact persistence

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **APPROVED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (validator APPROVED, faithfulness clean)
- gate-output.json (full suite): used; T-8-scope GREEN per impl-log (17/17 ticket tests + 139/139 + 5 skip simulator + 36/36 sales_agent obs downstream)
- Skills invoked: copilot-expert=N (sales_agent-only), sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y (best-effort cost summary + artifact write)

## Gate status (T-8 scope)
| Gate | Status | Errors |
|---|---|---|
| ruff | PASS (3 fixes — RUF002 + 2 RUF100) | 0 |
| ruff-format | PASS | 0 |
| mypy --strict | PASS 3/3 (3 manual fixes — CompiledStateGraph generic Any, dict[str, Any] heterogeneous, named AsyncMock local) | 0 |
| pytest (T-8 ticket-tests, 17/17) | PASS | 0 |
| full simulator suite (139/139 + 5 skip DB) | PASS | 0 |
| sales_agent obs downstream regression (36/36) | PASS | 0 |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | **LangGraph state hygiene** | **PASS (anchor of ticket)** | `_internal/graph.py:66-89` — `increment_turn` returns partial dict (`{"current_turn": ...+1, "iterations": ...+1}`), NEVER mutates. `should_continue` (line 97-141) THREE-tier exit: hard max-iter guard (`iterations >= max_turns + 5`) → `is_finished` → registry. NO `from __future__ import annotations` in graph.py NOR runner.py (line 51-55 — defensive cement). `StateGraph(SimulationState)` with reducers from T-4. Conditional edges always have exit branch. |
| 2 | Tool registration | PASS | n/a |
| 3 | Prompt cache architecture | PASS | n/a |
| 4 | deepagents subagent isolation | PASS | n/a |
| 5 | Observability | PASS | `_internal/runner.py:516-525` simulation_started + line 591-600 simulation_completed structlog events with all H5 keys + cost split. |
| 6 | Eval goldens | PASS | n/a — T-9 owns frozen golden v1. |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | n/a — graph delegates to T-6 customer_node + T-7 agent_bridge. |
| 9 | Cost optimization | **PASS (anchor — H6 cost-bucket separation)** | `_internal/runner.py:190-280` — `_compute_cost_summary` splits cost across 2 physical tables: `eval_simulator_llm_call` (filter `eval_metadata->>'simulation_id'`) and `sales_agent_llm_call` (filter `tenant_id` + `started_at >= simulation_started_at`). Best-effort wrap (line 271-279) — failure → `_zero_cost_summary`. Bucket separation honored at table level + jsonb tag. |
| 10 | Channel format & brand voice | PASS | n/a — runner doesn't touch prompts. |
| 11 | DDD compliance | PASS | All under `tests/agentic_evals/sales_agent/simulator/_internal/`. Lazy imports of production `agent_app` etc. (line 222-233) — no module-load-time DB or LLM dep. |
| 12 | Tests / TDD | PASS | 17 ticket tests in `test_runner_unit.py` covering A1 (compile + future-annotations cement on both files via AST + verbatim shell grep), A2 (deterministic sim_id), A3 (invalid archetype ValueError + cero DB inserts), A4 (artifact persistence + Pydantic roundtrip), plus 13 ancillary. |
| 13 | Mirror detection | PASS | `_internal/runner.py:25-36` § "Anti-duplication §0" reuses verbatim: `ARCHETYPE_SLUGS` (story A loader), `build_simulation_graph` (T-8), `SimulationState`/`SimulationResult`/`CostSummary` (T-4), `evaluate_termination` (T-4). Cero re-implementation. Step 0 grep clean per impl-log. |
| 14 | Default-flip side-effect coverage | NA | T-8 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [D2, D5, D10, H2, H3, H8]` (06-tickets.yaml:495). D2 (UUID5 tenant_id line 108-121), D5 (TerminationReason 6-value usage line 372-379), D10 (artifact JSON path line 287-299), H2 (deterministic UUID5 simulation_id line 124-147), H3 (max-iter guard line 121-130 in graph.py), H8 (registry consumption line 374-379) all honored in code. Commit `566d1d28` body cites inline but no formal "## Decisions honored" section. |

## H2 + D2 deterministic UUID5 verification
- Tenant_id: `_internal/runner.py:108-121` — `uuid.uuid5(NAMESPACE_DNS, f"eval-{archetype_slug}")`. Paridad with `fixtures/tenant_seeded.py` (impl-log mentions byte-equal helper).
- Simulation_id: line 124-147 — `uuid.uuid5(NAMESPACE_DNS, f"{run_id}_{slug}_{actor_profile_id}_{trial_n}")`. H2 idempotency.

## D1 in-process invocation verification
`_internal/runner.py:531` — `final_state_raw: Any = await graph.ainvoke(initial_state)` (in-process). NO httpx/HTTP webhook anywhere in runner.py. `_internal/agent_bridge.py:343` — `await agent_app.ainvoke(initial_state, config=lc_config)` (in-process via T-7). D1 cardinal honored.

## Findings (file:line)

### FAIL
None.

### WARN
- [Cat 15] `06-tickets.yaml:495` declares `decisions_applicable: [D2, D5, D10, H2, H3, H8]` → commit body cites inline but not formal "## Decisions honored" R6 section.

### info
- [Cat 1] `_internal/graph.py:121-130` — defense-in-depth max-iter guard `state.iterations >= state.max_turns + 5` IS independent of `should_continue` H8 registry to ensure graph terminates even if registry mishandles state mutation. Excellent design.
- [Cat 9] `_internal/runner.py:565-568` — artifact path re-anchored against backend root for stable repo-relative path; `ValueError` fallback to absolute path when called from external CWD. Robust path handling.
- [Cat 1] `_internal/runner.py:534-539` — handles both LangGraph 0.6 return shapes (BaseModel or dict-like) via `model_validate` round-trip. Forward-compat aware.
- [Cat 12] `test_runner_unit.py` (per impl-log) explicitly tests A1 via AST AND verbatim shell grep — defense-in-depth to prevent silent re-introduction of `from __future__ import annotations`. Excellent paranoia.

## Cross-scope flags
None.

## Research notes
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (accessed 2026-05-08)
- Takeaway: graph compose with conditional edges always with exit branch — runner.py implements 3-tier termination resolution (final_state.termination_reason → evaluate_termination → MAX_TURNS fallback) honoring spec.

## Recommendations for builder fix-loop
None.

## Drift detection
NO drift. T-8 deliverables map literal to `06-tickets.yaml:503-505`.

## Verdict
APPROVED

## Findings
- 0 FAIL / 1 WARN (Cat 15 R6 cite trivial) / 4 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/graph.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py`
- `backend/tests/agentic_evals/sales_agent/simulator/test_runner_unit.py`
- `docs/product/stories/eval-foundation-simulator-homologation/T-8-impl-log.md`

<!-- @pm: T-8-review.md ready (verdict=APPROVED). LangGraph cement + cost-bucket separation + UUID5 idempotency exemplary. -->
