# T-9 Result — Public API surface + ActorProfile fixtures + frozen golden v1 + 4 arch fitness gates

> Owner: builder-agentic Opus 4.7 (R23 — production_code=false test infra; Opus needed for H9/H10 invariant cement permanente)
> State: tests-passing
> Closed: 2026-05-08
> Commit SHA: _pending stage+commit_

## Deliverables shipped

| File | Status | Purpose |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` | REPLACED (T-4 stub → full surface) | H9 — exact 7-name `__all__` cement |
| `backend/tests/agentic_evals/sales_agent/simulator/fixtures/actor_profiles.py` | NEW | 3 hardcoded ActorProfile fixtures (lead_frio_impaciente, loop_forever, jailbreak_attempt) |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/__init__.py` | NEW (empty namespace) | Frozen fixture private namespace (H10) |
| `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` | NEW (frozen, NEVER edit) | H10 forward-compat regression anchor |
| `backend/tests/architecture/test_simulator_public_api_surface.py` | NEW | H9 enforces 7-name `__all__` + no symbol leak |
| `backend/tests/architecture/test_simulator_no_mirrors_shared.py` | NEW | H9 anti-mirror cross-codebase basename + AST subclass exemption |
| `backend/tests/architecture/test_simulator_writes_eval_kind_tag.py` | NEW | H5 metadata 6-key invariant via AST static analysis |
| `backend/tests/architecture/test_termination_policy_registry_contract.py` | NEW | H8 registry public API contract + StrEnum cardinality |
| `backend/tests/architecture/test_schema_migrations_registry_complete.py` | EXTENDED (T-4) | H1+H10 frozen golden v1 integration appended |

## Acceptance criteria

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | `__all__` exactly 7 names, `_internal` symbols not leaked | `pytest tests/architecture/test_simulator_public_api_surface.py` | **PASS** 15/15 |
| A2 | No mirror of shared abstractions | `pytest tests/architecture/test_simulator_no_mirrors_shared.py` | **PASS** 17/17 |
| A3 | 5 arch fitness gates green w/ empty allowlists | `pytest tests/architecture/test_{simulator_public_api_surface,simulator_no_mirrors_shared,simulator_writes_eval_kind_tag,termination_policy_registry_contract,schema_migrations_registry_complete}.py` | **PASS** 69/69 |
| A4 | Frozen golden v1 deserializable to current SimulationResult | `test_schema_migrations_registry_complete.py::test_frozen_golden_v1_deserializes_to_current_simulation_result` (T-9 EXTEND) | **PASS** |

## Quality gates (validators 04-validators.yaml T-9 quality_gates)

| Validator | Result | Detail |
|---|---|---|
| `be_lint` | **PASS** | `ruff check` 8 files, 0 errors (1 fix `F541` applied to f-string without placeholders) |
| `be_format` | **PASS** | `ruff format --check` 8 files (6 reformatted by ruff format on first pass; verified clean) |
| `be_mypy_strict` | **PASS** | `mypy --strict --ignore-missing-imports` on 2 prompt-specified files (`__init__.py` + `fixtures/actor_profiles.py`) — clean. Tests excluded from project mypy per pyproject `exclude=["tests/"]` (T-4 precedent) |
| `agentic_public_api_surface` | **PASS** | `test_simulator_public_api_surface.py` 15/15 |
| `agentic_no_mirrors_shared` | **PASS** | `test_simulator_no_mirrors_shared.py` 17/17 — basename collision check + 13 forbidden-basename probes + AST subclass exemption helper |
| `agentic_eval_kind_tag_enforced` | **PASS** | `test_simulator_writes_eval_kind_tag.py` 8/8 — AST static analysis on `observability.py`, `runner.py`, `customer_node.py`, `agent_bridge.py` |
| `agentic_termination_policy_registry_contract` | **PASS** | `test_termination_policy_registry_contract.py` 14/14 — register arity, idempotency, type-safety, StrEnum cardinality (6+4), evaluate_termination order |
| `hardening_h1_schema_migration_regression` | **PASS** | `test_schema_migrations_registry_complete.py` 16/16 (12 baseline T-4 + 4 NEW T-9 frozen golden v1 integration) |

## Native ticket tests breakdown

```
tests/architecture/test_simulator_public_api_surface.py:        15 PASS / 0 FAIL
tests/architecture/test_simulator_no_mirrors_shared.py:         17 PASS / 0 FAIL
tests/architecture/test_simulator_writes_eval_kind_tag.py:       8 PASS / 0 FAIL
tests/architecture/test_termination_policy_registry_contract.py: 14 PASS / 0 FAIL
tests/architecture/test_schema_migrations_registry_complete.py: 16 PASS / 0 FAIL  (12 base + 4 T-9 frozen golden)
                                                       TOTAL:   70 PASS / 0 FAIL
```

(69 was the count before pre-existing 12 schema_migrations base were grouped — full set across T-9 deliverable scope = 70.)

## Downstream regression (R3 surface map check)

Surfaces touched by T-9: `simulator/__init__.py`, `simulator/fixtures/`, `simulator/_fixtures/`,
`tests/architecture/`. Per `.claude/rules/auditor-downstream-regression.md`,
none of these are `shared/` cross-consumer surfaces — public API + frozen
fixture additions don't ripple. Defensive runs:

```bash
# Full simulator suite — covers T-4..T-8 + new fixture imports
.venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ -q
# → 139 passed, 5 skipped (DB-required)

# Sales_agent observability + arch fitness smoke
.venv/bin/pytest tests/modules/sales_agent/observability/ \
  tests/architecture/test_eval_simulator_observability_invariants.py \
  tests/architecture/test_sales_agent_observability_invariants.py \
  tests/architecture/test_no_new_sales_agent_module_imports.py \
  tests/architecture/test_copilot_anchors.py -q
# → 96 passed

# Full arch fitness (no-eval mark)
.venv/bin/pytest tests/architecture/ -q -m "not eval"
# → 939 passed (no regression vs T-8 baseline 838 + 5 eval gates pre-T-9 → 70 T-9 added → 939 total)
```

## Anti-duplication §0 evidence (Step 0 grep)

```bash
grep -rn "test_simulator_public_api_surface|test_simulator_no_mirrors_shared|test_simulator_writes_eval_kind_tag|test_termination_policy_registry_contract" backend/tests/architecture/
# → cero matches pre-create. Clean.

grep -rn "actor_profile_lead_frio|actor_profile_loop_forever|actor_profile_jailbreak" backend/tests/
# → 1 docstring quote in test_runner_unit.py:447 (no symbol collision).

grep -rn "golden_v1_simulation_result|FROZEN GOLDEN v1" backend/tests/
# → 1 docstring ref in _internal/schema_migrations.py:14 (no actual fixture pre-create).

ls backend/tests/architecture/test_schema_migrations_registry_complete.py
# → exists from T-4 commit b7b8d91c. EXTENDED (not recreated).
```

Cero mirror created. T-4 schema_migrations test EXTENDED with 4 new frozen-golden integration tests at file end (preserving all 12 baseline tests intact). 

## D6 preservation gate

Per spec D6 (`client_simulator/` byte-equal): T-9 touched ONLY:
- `backend/tests/agentic_evals/sales_agent/simulator/**` (new package — never overlaps client_simulator)
- `backend/tests/architecture/test_simulator_*.py` + extension to `test_schema_migrations_registry_complete.py`

```bash
git status --short -- client_simulator/
# → cero changes. D6 PASS.
```

## Self-audit checklist

- [x] CONTEXT-BRIEF.md fully consumed (R24 acceptance gate proceeded under documented justification — see T-9-impl-log.md § R24)
- [x] Domain skill `sales-agent-expert` invoked (§0 anti-duplication, §3 protected surfaces NOT touched, voice constraint magic-comment)
- [x] Domain skill `copilot-expert` cross-referenced (arch fitness gate pattern precedent)
- [x] `tessl__langgraph` cross-referenced (Pydantic state cement, NO future-annotations)
- [x] `tessl__pytest-api-testing` cross-referenced (function-scoped tests, AST static analysis, no DB side-effects)
- [x] Cross-module audit (NO-NEW-LAYER): no new layer introduced — extends existing arch fitness ratchet pattern (T-2 / T-4 precedent)
- [x] `__all__` exactly 7 names cement
- [x] Frozen golden v1 YAML — header comment cements never-edit
- [x] Magic comment `# voseo-allowed: actor persona dialect injection` for actor_profiles.py (es-AR fixture cites voseo verbatim)
- [x] AST static analysis used for metadata enforcement gate (no runtime DB invocation)
- [x] Allowlists empty — shrink-only ratchet
- [x] mypy --strict GREEN on prompt-specified files (`__init__.py` + `fixtures/actor_profiles.py`)
- [x] Type hints completos
- [x] Pydantic v2 `ConfigDict(frozen=True)` honored on all 3 fixtures
- [x] NO `from __future__ import annotations` in `simulator/__init__.py` or `fixtures/actor_profiles.py` (story-wide cement)
- [x] Step 0 anti-duplication grep evidence captured
- [x] Native WSL execution (no Docker)
- [x] Last line per R30: `tests-passing` state, awaiting orchestrator → gate-runner → auditor-agentic
