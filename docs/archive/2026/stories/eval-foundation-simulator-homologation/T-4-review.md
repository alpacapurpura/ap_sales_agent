<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-4 Pydantic state machines + termination registry + schema migrations

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **APPROVED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (Validator pass APPROVED, faithfulness clean)
- gate-output.T-4.json: used (per-validator GREEN snapshot)
- gate-output.json (full suite): used (caveat — story-B-isolated tests GREEN; cross-suite pollution at T-9 gate addressed in T-9 review)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=N (no external calls in T-4)

## Gate status (story-B scope, T-4)
| Gate | Status | Errors |
|---|---|---|
| ruff (story-scope) | PASS | 0 |
| ruff-format (story-scope) | PASS | 0 |
| mypy --strict (file-level) | PASS | 0 |
| pytest (T-4 ticket-tests, 56 tests) | PASS | 0 |
| arch-fitness (838/838 baseline pre-T-9) | PASS | 0 |
| jscpd | PASS | 0.74% < 5% |
| D6 client_simulator/ byte-equal | PASS | empty diff |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `state.py:40-145` — `SimulationState(BaseModel)`, `tenant_id: UUID` mandatory, `transcript: Annotated[list[ConversationTurn], operator.add]` reducer, `extra="forbid"`. Nodes return partial dicts (T-6/T-7/T-8 builders honor). NO `from __future__ import annotations` (story-wide cement). |
| 2 | Tool registration | PASS | n/a — T-4 ships only types + registry, no @tool decorators. |
| 3 | Prompt cache architecture | PASS | n/a — T-4 ships zero prompts. T-6 owns customer_persona_prompt cache prefix. |
| 4 | deepagents subagent isolation | PASS | n/a — T-4 ships only Pydantic + registry. |
| 5 | Observability | PASS | `eval_metadata: dict[str, str \| int]` slot reserved on `state.py:130-142` for H5 propagation. T-5 enforces. |
| 6 | Eval goldens | PASS | T-9 owns frozen golden v1 fixture; T-4 prepares forward-compat scaffold (`_internal/schema_migrations.py`). |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | n/a — T-4 doesn't touch routers. |
| 9 | Cost optimization | PASS | `result.py:77-105` — `CostSummary` typed `Literal["sales_agent", "eval_simulator"]` enforces bucket discriminator at typecheck time (H6). |
| 10 | Channel format & brand voice | PASS | `actor_profile.py:52-54` `dialect_code: str = "es-419"` (BCP-47). voseo magic-comment escape present in module docstrings per R25. |
| 11 | DDD compliance | PASS | All files under `tests/agentic_evals/sales_agent/simulator/` — no production code touched. R5 schema-mirror exception: T-4 stays entirely under `tests/`. |
| 12 | Tests / TDD | PASS | TDD evidence in `T-4-impl-log.md` § "Iteration 1 — All tests RED, then implementation GREEN". 56 ticket tests + 1 arch fitness gate (`test_schema_migrations_registry_complete.py`). |
| 13 | Mirror detection | PASS | Step 0 grep evidence captured in impl-log. Class names (`SimulationState`, `ActorProfile`, etc.) cero collision with shared/. Legacy `client_simulator/` byte-equal. |
| 14 | Default-flip side-effect coverage | NA | T-4 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [D4, D5, H1, H2, H8]` declared in `06-tickets.yaml:234`. Commit `b7b8d91c` body lists honored decisions inline (Pydantic D4, StrEnum 6+4 D5, schema_version field H1, etc.) but no formal "## Decisions honored" section. R6 self-fix candidate (trivial — present implicitly in T-4-result.md § "Decisions"). |

## Findings (file:line)

### FAIL
None.

### WARN
- [Cat 15] `06-tickets.yaml:234` declares `decisions_applicable: [D4, D5, H1, H2, H8]` → commit `b7b8d91c` body cites them inline but not in a formal "## Decisions honored" section per R6 cement. Self-fix: trivial — already present in `T-4-result.md`.

### info
- [Cat 1] `state.py:51-56` — `extra="forbid"` documented with forward-compat note about LangGraph protocol keys via `Command(update={...})`. Defensive cement preserved.
- [Cat 9] `result.py:69-74` — `_default_llm_call_count_split` module-level factory (not lambda) chosen so mypy resolves `Literal["sales_agent", "eval_simulator"]` keys precisely. Documented rationale.
- [Cat 12] `_internal/schema_migrations.py:59` — registry intentionally empty for v1 baseline; arch fitness gate `test_schema_migrations_registry_complete.py` verifies exhaustiveness (no missing chain step for any currently-shipped class).

## Cross-scope flags
None — T-4 lives entirely under `tests/agentic_evals/sales_agent/simulator/`.

## Research notes (DATE-AWARE)
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (accessed 2026-05-08 per CONTEXT-BRIEF §15)
- Takeaway: Pydantic state machines OK in LangGraph 0.2+ provided no `from __future__ import annotations` (runtime introspection requires resolved annotations).
- Delta vs reference anchors: none. Story honors live docs.
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live researched 2026-05-07/08.

## Recommendations for builder fix-loop
None for T-4. Optional R6 self-fix in commit body retroactively NOT actionable on already-pushed commit — track in T-10 review for eventual capability YAML cite improvement.

## Drift detection (CONTRACT vs code)
NO drift detected. T-4 deliverables map literal to `06-tickets.yaml:240-249` deliverables list.

## Verdict
APPROVED

## Findings
- 0 FAIL / 1 WARN (Cat 15 R6 cite — trivial / already implicit in result.md) / 3 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/state.py`
- `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py`
- `backend/tests/agentic_evals/sales_agent/simulator/result.py`
- `backend/tests/agentic_evals/sales_agent/simulator/termination.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py`
- `backend/tests/architecture/test_schema_migrations_registry_complete.py`
- `docs/product/stories/eval-foundation-simulator-homologation/T-4-impl-log.md`
- `docs/product/stories/eval-foundation-simulator-homologation/T-4-result.md`

<!-- @pm: T-4-review.md ready (verdict=APPROVED). Ready for next ticket review. -->
