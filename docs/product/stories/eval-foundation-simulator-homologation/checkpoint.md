<!-- voseo-allowed: verbatim quote of Chris's mandate phrasing (es-AR speaker) — bitácora audit trail -->
---
story_id: eval-foundation-simulator-homologation
outcome: pi-12-sales-agent-eval-foundation
state: developing
phase: BUILD_GREEN_T-5
last_artifact: T-5-result.md
last_modified: 2026-05-07T18:30:00Z
next_action: "T-5 done (state: developed; 13 ticket-tests + 881 arch fitness GREEN). Awaiting orchestrator to spawn gate-runner + auditor-agentic for independent verdict. Other tickets T-2 / T-3 (BE) + T-6..T-10 (AGENTIC) restan."
ratified_by_chris: true                  # mandato 2026-05-07: "vos decidís cero deuda 1000+ tenants"
spawned_at: 2026-05-06T17:11:00Z
spawned_by: /pm
parallel_safe: false                     # A done, B unblocks C/D/E/F/G/H/I — focus serial
blocked_reason: null
audit_iterations: 0
audit_iterations_cap: 3                  # D11 ratified
legacy_exempt: true
po_version: 2
arch_version: 1
ticket_count: 10
total_estimate_hours: 22
critical_path: [T-1, T-5, T-7, T-8, T-9, T-10]
---

## Bitácora

- 2026-05-06 17:11Z — `/pm` creó folder + checkpoint. Story B (foundation) — homologa `client_simulator/` raíz a `backend/tests/agentic_evals/sales_agent/simulator/`. Wirea dual-LLM pattern usando ActorProfile pattern (AWS Strands Evals). Bloquea C/D/E/F/G/H/I.
- 2026-05-07 20:50Z — `/po` draft v1 escrito tras unblock por A done. 4 scenarios + 11 open questions. Decisión cardinal propuesta: in-process `agent_app.ainvoke`.
- 2026-05-07 21:15Z — Chris mandato "vos decidís cero deuda escala 1000+ tenants × N updates futuras". `/po` ratifica las 11 Qs (D1-D11) + agrega 10 hardening extras (H1-H10). `state: refining → refined`.
- 2026-05-07 22:00Z — `architect-orchestrator` (single-shot full-stack) entregó:
  - `03-arch-be.md` (617 líneas) — Migration 124 + 4 SQLAlchemy models + spec registration + bootstrap + DB-seed fixture + 5 arch fitness gates + downstream regression rule update
  - `03-arch-agentic.md` (1122 líneas) — LangGraph state machine + dual-LLM dispatch + customer prompt v1 + observability subclasses + termination registry + schema versioning + public API surface + concurrency + voice constraints
  - `03-arch.md` (258 líneas) — orchestrator-consolidated cross-cutting decisions
  - Cross-module audit `agent_kind` clarification: NO Postgres enum (registry-level discriminator), bucket separation via NEW tables (paridad campaigns/observability/ PI-1 S0 PR-1 / Alembic 083)
  - 3 open questions surfaced: OQ-A1 stub schema migration (decisión: NO YAGNI), OQ-A2 Pydantic-only fixtures B (decisión: SI), OQ-A3 EVAL_USER_SIMULATOR eval-only registry (decisión: SI architect recommendation)
- 2026-05-07 22:30Z — `/architect` orchestrator (este Skill invocation) escribió `04-validators.yaml` (24 validators across 3 categories: non_functional / functional / agentic_eval; scenario_coverage 4/4; hardening_coverage H1-H10).
- 2026-05-07 22:35Z — `/architect` escribió `05-guidelines.md` (patterns required + forbidden + files in scope + reference docs + native-first + TDD orden + owner routing).
- 2026-05-07 22:45Z — `/architect` escribió `06-tickets.yaml` (10 tickets DAG, owner_eligibility per R23 + Chris mandate, hardening per ticket coverage matrix). **state: refined → ready**.
- 2026-05-07 (today) — `builder-agentic` Opus 4.7 cerró T-4: Pydantic state machines (SimulationState, ActorProfile, ConversationTurn, CostSummary, SimulationResult) + termination registry (TerminationReason 6 values + AgentErrorSubtype 4 values + register_termination_policy public + 4 default policies) + SCHEMA_MIGRATIONS registry stub (v1 baseline) + 3 acceptance tests (57 tests) + 1 arch fitness gate (test_schema_migrations_registry_complete.py — 11 tests). All quality gates GREEN: ruff, format, mypy strict (file-level), jscpd 0.74% < 5%. Arch fitness 838 PASS (no regression). D6 preservation gate PASS. **T-4 state: ready → developing → developed**. Story global state remains `developing` (T-1..T-3 + T-5..T-10 pending).
- 2026-05-07 18:30Z — `builder-agentic` Opus 4.7 cerró T-5: `EvalSimulatorObservabilityContext(BaseObservabilityContext)` + `EvalSimulatorCallbackHandler(BaseAgentCallbackHandler)` subclasses with strict Template Method override scope (3 abstract hooks + 2 abstract persisters) + co-located test-infra repos (`EvalSimulatorLlmCallRepository`, `EvalSimulatorTraceEventRepository`) + `build_eval_metadata` SSoT helper for H5 6-key dict + defense-in-depth `__post_init__` validation at 3 layers + best-effort persist wrapping + factory `build_eval_simulator_observability_context` paridad sales_agent. 13 ticket-tests across 3 acceptance classes (TestSubclassInheritance / TestMandatoryEvalMetadata / TestPersistFailureResilience). Quality gates: ruff PASS, format PASS, mypy --strict PASS, native ticket tests PASS 13/13, full simulator suite PASS 59/59, cross-module smoke (sales_agent obs + shared agent_obs) PASS 224/224, architecture fitness 881/881 (no regression). Cero mirror — Step 0 grep evidence captured. **T-5 state: ready → developing → developed**. Awaiting orchestrator for gate-runner + auditor-agentic independent verdict.

## Ready package contents

```
docs/product/stories/eval-foundation-simulator-homologation/
├── 00-story.md                       # /pm brief
├── 01-spec.md                        # /po v2 ratified (D1-D11 + H1-H10)
├── 03-arch.md                        # /architect orchestrator consolidated
├── 03-arch-be.md                     # BE surface
├── 03-arch-agentic.md                # AGENTIC surface
├── 04-validators.yaml                # 24 validators (non_functional/functional/agentic_eval)
├── 05-guidelines.md                  # patterns required/forbidden + files in scope
├── 06-tickets.yaml                   # 10 tickets DAG
└── checkpoint.md                     # state=ready (this file)
```

## Tickets summary

| # | Title | Owner | Deps | Estimate |
|---|---|---|---|---|
| T-1 | Migration 124 + 4 SQLAlchemy models + spec registration + bootstrap | builder-backend Sonnet (R5) | — | 3h |
| T-2 | Migration test + arch fitness gate observability invariants | builder-backend Sonnet | T-1 | 1.5h |
| T-3 | Fixture eval_tenant_seeded + fixture test | builder-backend Sonnet | T-1 | 2.5h |
| T-4 | Pydantic state + actor_profile + result + termination + schema_migrations | builder-agentic Opus 4.7 | — | 3h |
| T-5 | EvalSimulator observability subclasses | builder-agentic Opus 4.7 | T-1, T-4 | 2.5h |
| T-6 | Customer node + prompt v1 + llm_roles registry + concurrency | builder-agentic Opus 4.7 | T-4 | 3h |
| T-7 | Agent_bridge in-process + leak_assertions | builder-agentic Opus 4.7 | T-4, T-5 | 2.5h |
| T-8 | Graph compose + run_simulation orchestrator | builder-agentic Opus 4.7 | T-6, T-7 | 3h |
| T-9 | Public API surface + ActorProfile fixtures + frozen golden v1 + 4 arch gates | builder-agentic Opus 4.7 | T-4..T-8 | 2.5h |
| T-10 | Smoke parametrized 5×archetype + property concurrency + R3 rule update | builder-agentic Opus 4.7 | T-3, T-9 | 3h |

**Total estimate:** 22h sequential. Parallelizable: T-1+T-4 (start), T-2+T-3+T-5 (T-1 dep), T-6+T-7 (T-4 dep). Realistic ~14h with parallelism.

## WIP cap impact

Pre-ready: ready=0 / cap 5. Post-ready: **ready=1 / cap 5**. Within cap. Other stories permanece refining/refined.

## Próximo paso

`/dev-team` Conv 2 autonomous build — comando: `/dev-team eval-foundation-simulator-homologation`. Toma T-1 first (state: ready → developing) + T-4 paralelo si workers disponibles.
