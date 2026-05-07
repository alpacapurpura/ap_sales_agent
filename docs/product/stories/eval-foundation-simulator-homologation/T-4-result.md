# T-4 Result — Pydantic state machines + termination registry + schema migrations

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-4
**Owner:** builder-agentic Opus 4.7
**State:** developed (validators GREEN, awaiting `/auditor` independent verdict per Conv 3)
**Date stamp:** 2026-05-07T00:00:00Z

## Summary

Shipped foundational Pydantic state machines for the eval simulator dual-LLM
harness:

- `SimulationState` — LangGraph Pydantic state with `Annotated[list[ConversationTurn], operator.add]` reducer for transcript append-only, `tenant_id` mandatory tenant isolation, max-iter `iterations` H3 guard
- `ActorProfile` — AWS Strands ActorProfile pattern (D7); BCP-47 `dialect_code` field with `es-AR` voseo escape per persona
- `ConversationTurn` / `CostSummary` / `SimulationResult` — frozen Pydantic types in `result.py` with full schema_version field per H1 forward-compat
- `TerminationReason` 6-value StrEnum + `AgentErrorSubtype` 4-value StrEnum + `TERMINATION_POLICIES` Strategy registry (H8) + `register_termination_policy(name, predicate)` public API + 4 default policies registered at module import
- `SCHEMA_MIGRATIONS` registry stub + `apply_migrations` chain function + `CURRENT_SCHEMA_VERSIONS` lookup (H1 — story B v1-only, registry empty intentionally)
- 3 acceptance test modules (39 + 6 + 11 = 56 ticket tests) + STUB `simulator/__init__.py` (T-9 will rebind to exact 7-name `__all__` per H9)

Zero touch on protected surfaces (sales-agent §3, R5 schema-mirror exception NA — T-4 lives entirely under `tests/`). Zero mirror of shared abstractions per anti-duplication §0 (T-5 will subclass `BaseObservabilityContext` + `BaseAgentCallbackHandler`; T-4 only ships types).

## Acceptance criteria

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | All Pydantic classes deserializable + frozen + schema_version field | `pytest test_pydantic_models_unit.py` | **PASS** (39 tests) |
| A2 | TERMINATION_POLICIES exposes 4 default policies + register_termination_policy public | `pytest test_termination_registry.py::test_default_policies_registered` | **PASS** (6 tests) |
| A3 | SCHEMA_MIGRATIONS importable + arch fitness gate exhaustive | `pytest test_schema_migrations_registry_complete.py` | **PASS** (11 tests) |

## Validator gates output

See `gate-output.T-4.json` for canonical verdict per validator. Summary:

| Validator | Status | Notes |
|---|---|---|
| `be_lint` | PASS | All 14 ruff issues fixed (10 autofix + 4 manual ERA001 banner naming + variable docstring) |
| `be_format` | PASS | 10/10 files clean |
| `be_mypy_strict` | PASS | 10/10 source files clean (file-level form; dir-level NA pre-T-1 due to `tests/` exclude in `pyproject.toml [tool.mypy]`) |
| `hardening_h8_termination_registry` | PASS | 6/6 registry contract tests |
| `agentic_termination_policy_registry_contract` | PASS | Story B baseline. Full architecture gate `test_termination_policy_registry_contract.py` is T-9 deliverable |
| `jscpd_no_duplication` | PASS | 0.74% duplication (1 clone — semantically required import block between `__init__.py` STUB and `test_pydantic_models_unit.py`); below 5% threshold |
| `be_arch_fitness_full` | PASS | 838/838 — no regression |
| `legacy_client_simulator_intact` (D6) | PASS | `git diff HEAD client_simulator/` empty |

## Diff resumen

10 NEW files, 1512 LOC total:

```
backend/tests/agentic_evals/sales_agent/simulator/
├── __init__.py                    # T-4 STUB public surface (T-9 final)
├── actor_profile.py               # 78 LOC — AWS Strands pattern
├── result.py                      # 156 LOC — ConversationTurn + CostSummary + SimulationResult
├── state.py                       # 119 LOC — LangGraph Pydantic state
├── termination.py                 # 190 LOC — StrEnum + registry + 4 default policies
├── _internal/
│   ├── __init__.py
│   └── schema_migrations.py       # 156 LOC — H1 registry + chain function
├── test_pydantic_models_unit.py   # 458 LOC — A1 acceptance (39 tests)
└── test_termination_registry.py   # 102 LOC — A2 acceptance (6 tests)
backend/tests/architecture/
└── test_schema_migrations_registry_complete.py  # 209 LOC — A3 acceptance (11 tests)
```

Plus: 06-tickets.yaml T-4 entry transitions appended; checkpoint.md state + bitácora updated; T-4-impl-log.md written.

## Hardening invariants honored

| H | Invariant | Where enforced in T-4 |
|---|---|---|
| H1 | Schema versioning forward-compat | Every Pydantic class has `schema_version: int = 1`. `SCHEMA_MIGRATIONS` registry + `apply_migrations` + `CURRENT_SCHEMA_VERSIONS` shipped. Arch fitness gate verifies. |
| H2 | Idempotency UUID5 (deferred to T-3/T-8) | NA — type definitions only. Documented in `state.py` SimulationState.simulation_id field comment that runner derives via uuid5(). |
| H3 | Async-first concurrency-safe | NA — no async surface in T-4. Documented in SimulationState.iterations field as max-iter guard for T-8 graph. |
| H4 | Rate-limiting customer LLM | NA T-4 (T-6 builder ships concurrency.py). |
| H5 | Observability eval-vs-prod tags | NA T-4 (T-5 builder enforces metadata writes). `eval_metadata: dict[str, str | int]` field on SimulationState reserves the propagation slot. |
| H6 | Cost bucket separation | NA T-4 (T-5 builder ships subclasses; T-1 builder ships DDL). `CostSummary.llm_calls_count_split` typed `Literal["sales_agent", "eval_simulator"]` enforces bucket discriminator at typecheck time. |
| H7 | Failure-mode taxonomy | `AgentErrorSubtype` StrEnum 4 values shipped: TIMEOUT / EMPTY_RESPONSE / HTTP_ERROR / INVALID_STATE. T-7 builder maps from agent_bridge failure paths. |
| H8 | Termination policy registry (Strategy) | **PRIMARY T-4 deliverable.** `TERMINATION_POLICIES` dict + `register_termination_policy()` public API + 4 default policies registered at import + `evaluate_termination()` iteration helper. Arch test verifies. |
| H9 | Public API surface minimal | T-9 final — T-4 ships STUB `__init__.py` exporting 8 names (run_simulation NOT yet bound; T-9 binds + freezes to exact 7). Documented inside the `__init__.py` docstring for hand-off. |
| H10 | Frozen golden v1 fixture (T-9/T-10) | NA T-4 (T-9 ships YAML fixture). `apply_migrations` raises `KeyError` on missing chain step — guards future regressions. |

## Decisions (architectural fingerprints recorded)

1. `from __future__ import annotations` cement extended from `simulator/_internal/graph.py` (arch-agentic §1.1 spec) to all Pydantic state classes (`state.py`, `actor_profile.py`, `result.py`). Same root cause: LangGraph runtime introspection requires resolved annotations. `_internal/schema_migrations.py` retains the future-import — it has no Pydantic class, only Callable type aliases; safe.

2. `goal_completion_predicate` shipped as no-op stub. Story E (MAJ-EVAL grader) overrides via `register_termination_policy("goal_completion", real_predicate)` (idempotent on name). Default policy slot is preallocated to keep the default-policy-list stable across stories.

3. `apply_migrations` raises `KeyError` on missing chain step (defensive). Forces explicit migration registration at every schema bump — prevents silent regression on frozen golden v1 deserialization.

4. Module-level `_default_llm_call_count_split` factory (not lambda) for `CostSummary.llm_calls_count_split` default — required for mypy to resolve `Literal["sales_agent", "eval_simulator"]` keys precisely.

## Files NOT touched (verification)

- `client_simulator/src/simulator/*.py` — D6 preservation gate PASS (`git diff HEAD` empty)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording,observability/persistence}/` — unchanged
- `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE` — unchanged (decisión §2.1 arch-agentic)
- `backend/src/shared/agent_observability/{recording,cost,channels}/` — read-only (no edits)
- `backend/src/core/config.py` — no flag flips (Step 0.5 NA)
- `.claude/rules/*` — unchanged (auditor-downstream-regression entry update is T-10 deliverable)

## Native commands record

```bash
# Lint clean
cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_schema_migrations_registry_complete.py --no-cache
# Format clean
cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_schema_migrations_registry_complete.py
# Mypy strict file-level (10/10 clean)
cd backend && .venv/bin/mypy --strict --explicit-package-bases <file list> --ignore-missing-imports
# Tests
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/test_pydantic_models_unit.py tests/agentic_evals/sales_agent/simulator/test_termination_registry.py tests/architecture/test_schema_migrations_registry_complete.py --override-ini="addopts=" -v
# Full arch fitness regression
cd backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="
# jscpd
cd backend && npx --yes jscpd@4 tests/agentic_evals/sales_agent/simulator/ --min-tokens 50 --threshold 5
# D6 preservation gate
git diff HEAD --name-only -- client_simulator/src/simulator/
```

## Commit SHA

Pending — to be appended after `git commit` lands. Stage by exact name per parallel-safety M5/M7.

## Next builders

T-5 (observability subclasses) consumes: `EvalSimulatorObservabilityContext(BaseObservabilityContext)` + `EvalSimulatorCallbackHandler(BaseAgentCallbackHandler)` — types from T-4 referenced via `state.SimulationState.eval_metadata` propagation slot.

T-6 (customer node + prompt + concurrency) consumes: `ActorProfile`, `SimulationState`, `ConversationTurn`.

T-7 (agent_bridge + leak_assertions) consumes: `SimulationState`, `ConversationTurn`, `AgentErrorSubtype` (taxonomy mapping at failure paths).

T-8 (graph compose + run_simulation) consumes: `SimulationState`, `SimulationResult`, `TERMINATION_POLICIES`, `evaluate_termination`.

T-9 will rebind `simulator/__init__.py::__all__` to exact 7 names (H9) once `run_simulation` is delivered by T-8.

## Audit readiness

T-4 deliverables align literal with 06-tickets.yaml:

- ✅ `state.py` ships `SimulationState(BaseModel)` with all spec scenario 1 fields + transcript reducer + tenant_id required
- ✅ `actor_profile.py` ships `ActorProfile(BaseModel, schema_version=1)` with id, name, dialect_code (BCP-47), traits, context (pain_points, budget_hint, urgency, communication_style, persona_kind, metadata, objections), actor_goal
- ✅ `result.py` ships `SimulationResult` + `ConversationTurn` + `CostSummary` with cost_summary fields agent/simulator/total/llm_calls_count_split
- ✅ `termination.py` ships `TerminationReason` 6 values + `AgentErrorSubtype` 4 values + `TERMINATION_POLICIES` registry + `register_termination_policy` public + 4 default policies registered (goal_completion, max_turns, customer_exit, agent_error)
- ✅ `_internal/__init__.py` NEW
- ✅ `_internal/schema_migrations.py` ships SCHEMA_MIGRATIONS empty stub + apply_migrations chain function + CURRENT_SCHEMA_VERSIONS dict (5 classes)
- ✅ `__init__.py` cascading STUB
- ✅ Test acceptance unit `test_pydantic_models_unit.py` + `test_termination_registry.py::test_default_policies_registered`
- ✅ Arch fitness gate `test_schema_migrations_registry_complete.py` — registry contract + exhaustive vs CURRENT_SCHEMA_VERSIONS

Verdict for orchestrator: T-4 ready for gate-runner pickup → auditor-agentic independent review.
