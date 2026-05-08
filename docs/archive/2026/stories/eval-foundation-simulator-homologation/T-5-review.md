<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-5 EvalSimulator{ObservabilityContext, CallbackHandler} subclasses

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **APPROVED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (validator APPROVED, faithfulness clean)
- gate-output.json (full suite): used; T-5-scope GREEN per impl-log (224/224 cross-module smoke + 881/881 arch fitness)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=N (T-5 not graph compose), tessl__graceful-degradation=Y (best-effort persistence)

## Gate status (T-5 scope)
| Gate | Status | Errors |
|---|---|---|
| ruff | PASS | 0 |
| ruff-format | PASS | 0 |
| mypy --strict | PASS | 0 |
| pytest (T-5 ticket-tests, 13/13) | PASS | 0 |
| full simulator suite (59/59) | PASS | 0 |
| cross-module smoke (sales_agent obs + shared agent_obs, 224/224) | PASS | 0 |
| arch-fitness (881/881) | PASS | 0 |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | n/a — T-5 ships observability subclasses, not graph nodes. |
| 2 | Tool registration | PASS | n/a |
| 3 | Prompt cache architecture | PASS | n/a |
| 4 | deepagents subagent isolation | PASS | n/a |
| 5 | Observability | **PASS (anchor of ticket)** | `_internal/observability.py:115-137` — `build_eval_metadata(...)` SSoT helper enforces 6 mandatory H5 keys (`eval_run_kind="simulator"`, `archetype_slug`, `actor_profile_id`, `trial_n`, `simulation_id`, `run_id`). `_assert_eval_metadata_complete(...)` invoked at 3 layers (`__post_init__` of context + handler + per-row trace `add()`). Best-effort `try/except + structlog.warning` per `.claude/rules/copilot-observability.md` cement. `sanitize_payload` heredado del shared base (NOT re-implemented). |
| 6 | Eval goldens | PASS | n/a — T-9 owns frozen golden. |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | n/a |
| 9 | Cost optimization | PASS | `_aggregate_totals` reuses `eval_simulator_llm_call` schema columns (no parallel pricing layer). PricingResolver + FXResolver factories from shared/ — H6 cost-bucket separation honored at table level. |
| 10 | Channel format & brand voice | PASS | `channel_type="eval_simulator"` injected per row (line 305, 317, 437); production sales_agent rows untouched. |
| 11 | DDD compliance | PASS | T-5 lives entirely under `tests/agentic_evals/sales_agent/simulator/_internal/observability.py` + co-located test-infra repos. SQLAlchemy mirror models live under `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/` (R5 schema-mirror exception delivered by T-1). |
| 12 | Tests / TDD | PASS | 13 ticket-tests across 3 acceptance classes (TestSubclassInheritance / TestMandatoryEvalMetadata / TestPersistFailureResilience) per impl-log. |
| 13 | **Mirror detection** | **PASS (anchor of ticket — anti-mirror cardinal)** | `_internal/observability.py:78-98` — imports verbatim from `src.shared.agent_observability.{recording.turn_envelope, recording.base_callback_handler, cost.fx_resolver, pricing.resolver, persistence.pricing_snapshot_repository, persistence.tenant_billing_config_repository}`. `EvalSimulatorObservabilityContext` line 333 inherits `BaseObservabilityContext`. `EvalSimulatorCallbackHandler` line 252 inherits `BaseAgentCallbackHandler`. Cero re-implementation of any shared abstraction. Step 0 grep evidence in impl-log §3. |
| 14 | Default-flip side-effect coverage | NA | T-5 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [H5, H6]` (06-tickets.yaml:297). Commit `14c354f1` body cites H5 (eval_metadata 6-key cement) + H6 (cost-bucket separation via table) inline + in T-5-result.md, but no formal "## Decisions honored" section. Trivial. |

## Findings (file:line)

### FAIL
None.

### WARN
- [Cat 15] `06-tickets.yaml:297` declares `decisions_applicable: [H5, H6]` → commit body cites inline but not formal "## Decisions honored" R6 section.

### info
- [Cat 5] `_internal/observability.py:281-291` — `__post_init__` of `EvalSimulatorCallbackHandler` validates eval_metadata at construction time → single loud failure during turn setup vs N silent dropped rows. Excellent defense-in-depth choice.
- [Cat 5] `_internal/observability.py:440-446` — best-effort wrapping with `simulation_id` breadcrumb in structlog warning kwarg → Streamlit/operator can grep failures by simulation.
- [Cat 13] `_internal/observability.py:520-585` — `build_eval_simulator_observability_context` factory paridad with `build_sales_agent_observability_context` shape (`Context | None`) so `agent_bridge` (T-7) handles both fall-back modes identically. Good cross-agent ergonomics.
- [Cat 9] `_internal/observability.py:448-485` — `_aggregate_totals` flush+select pattern with full rollup (input/output tokens, cached_read, cost) — paridad sales_agent impl, zero divergence.

## Cross-scope flags
None.

## Research notes
None novel. T-5 honors `.claude/rules/anti-duplication.md` inventory verbatim.

## Recommendations for builder fix-loop
None.

## Drift detection
NO drift detected. T-5 deliverables map literal to `06-tickets.yaml:307-312` deliverables.

## Verdict
APPROVED

## Findings
- 0 FAIL / 1 WARN (Cat 15 R6 cite trivial) / 4 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py`
- `backend/tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py`
- `backend/src/shared/agent_observability/recording/turn_envelope.py` (read-only consumed)
- `backend/src/shared/agent_observability/recording/base_callback_handler.py` (read-only consumed)
- `docs/product/stories/eval-foundation-simulator-homologation/T-5-impl-log.md`
- `docs/product/stories/eval-foundation-simulator-homologation/T-5-result.md`

<!-- @pm: T-5-review.md ready (verdict=APPROVED). Anti-mirror discipline exemplary — best-in-class pattern. -->
