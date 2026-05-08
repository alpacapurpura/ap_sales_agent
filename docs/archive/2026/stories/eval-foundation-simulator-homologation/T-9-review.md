<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — T-9 Public API surface + ActorProfile fixtures + frozen golden v1 + 4 arch fitness gates

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-08
> Iter: 1
> Verdict: **CHANGES_REQUESTED**
> Generated: 2026-05-08T22:00:00Z

## Inputs
- CONTEXT-BRIEF.md: used (validator APPROVED, faithfulness clean)
- gate-output.json (full suite): used; **shows FAIL on `test_no_internal_symbols_leaked` confirmed by reproducible local run**
- Skills invoked: copilot-expert=N (sales_agent-only), sales-agent-expert=Y, tessl__langgraph=N, tessl__graceful-degradation=N

## Gate status (T-9 scope)
| Gate | Status | Errors |
|---|---|---|
| ruff | PASS (1 F541 fix) | 0 |
| ruff-format | PASS (6 reformatted) | 0 |
| mypy --strict | PASS | 0 |
| pytest (T-9 ticket-tests, isolated 70/70 — 15+17+8+14+16) | PASS | 0 |
| **arch fitness gate `test_simulator_public_api_surface.py::test_no_internal_symbols_leaked` UNDER full-suite collection** | **FAIL** | 1 |
| arch fitness gate isolated (15/15) | PASS | 0 |
| simulator suite (139/139 + 5 skip) | PASS | 0 |

## 15 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | n/a |
| 2 | Tool registration | PASS | n/a |
| 3 | Prompt cache architecture | PASS | n/a |
| 4 | deepagents subagent isolation | PASS | n/a |
| 5 | Observability | PASS | n/a — T-9 is API surface + fixtures + arch gates |
| 6 | **Eval goldens** | **PASS (anchor — H10 frozen golden)** | `_fixtures/golden_v1_simulation_result.yaml:1-81` — frozen v1 fixture with header `# FROZEN GOLDEN v1 — NEVER EDIT.` Deterministic UUIDs documented in header (line 14-20). Schema_version field on every nested model. Spanish neutro tenant_coach_lat reply. |
| 7 | RAG / Qdrant hygiene | PASS | n/a |
| 8 | LLM provider routing | PASS | n/a |
| 9 | Cost optimization | PASS | golden YAML cost_summary cap (`agent_cost_usd: 0.0021 + simulator_cost_usd: 0.0008 = total 0.0029`) well under D9 individual cap $0.05. |
| 10 | Channel format & brand voice | PASS | `fixtures/actor_profiles.py:144-187` — `actor_profile_jailbreak_attempt` uses `dialect_code="es-AR"` voseo with magic comment escape in module docstring (line 29-31). `actor_profile_lead_frio_impaciente` (line 48-83) and `actor_profile_loop_forever` (line 95-132) use `es-419` neutro. Voice constraints honored. |
| 11 | DDD compliance | PASS | T-9 lives entirely under `tests/agentic_evals/sales_agent/simulator/` + `tests/architecture/`. |
| 12 | **Tests / TDD** | **FAIL** | `test_simulator_public_api_surface.py::test_no_internal_symbols_leaked` (line 96-175) FAILS under realistic full-suite test collection due to **structural design flaw**: pytest collection imports `test_*.py` modules into the simulator package namespace as submodules; the `_ALLOWED_SUBMODULES` frozenset (line 139-149) lists only production submodules (`_internal`, `actor_profile`, `fixtures`, `_fixtures`, `result`, `state`, `termination`) but not test modules (`conftest`, `test_agent_bridge_unit`, `test_concurrency_property`, `test_customer_node_unit`, `test_leak_assertions_unit`, `test_observability_resilience`, `test_pydantic_models_unit`, `test_runner_unit`, `test_schema_migration_regression`, `test_simulator_smoke`, `test_termination_registry`). **Confirmed reproducible** locally: `pytest tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_simulator_public_api_surface.py` → 1 failed (the cited test). The H9 invariant the gate POLICES is structurally sound (`__all__ == 7 names` PASS isolated); the FALSE POSITIVE comes from the gate's own `_ALLOWED_SUBMODULES` allowlist incompleteness. |
| 13 | Mirror detection | PASS | `tests/architecture/test_simulator_no_mirrors_shared.py:55-67` walks shared/agent_observability tree + simulator tree, intersects basenames. Allowlist `_ALLOWED_BASENAMES = {"__init__.py"}` (line 52). 17/17 tests PASS isolated. Subclass-exemption helper (line 70-80) wired for future churn. Excellent. |
| 14 | Default-flip side-effect coverage | NA | T-9 touches zero `core/config.py` defaults. |
| 15 | Decisions honored cite (R6) | WARN | Ticket `decisions_applicable: [D7, H1, H9, H10]` (06-tickets.yaml:556). All honored in code. Commit `fc587350` cites inline but no formal "## Decisions honored" section. |

## H9 verification (public API surface)
`__init__.py:60-68` — `__all__` has EXACTLY 7 names (alphabetically sorted): `ActorProfile`, `AgentErrorSubtype`, `SimulationResult`, `SimulationState`, `TerminationReason`, `register_termination_policy`, `run_simulation`. Resolved via:
- `ActorProfile` ← `actor_profile.py`
- `SimulationResult` ← `result.py`
- `SimulationState` ← `state.py`
- `AgentErrorSubtype`, `TerminationReason`, `register_termination_policy` ← `termination.py`
- `run_simulation` ← `_internal/runner.py`

Cardinality cement honored. `test_simulator_dunder_all_exact_seven_names` + `test_simulator_dunder_all_length_is_seven` PASS isolated.

## H10 verification (frozen golden v1)
`_fixtures/golden_v1_simulation_result.yaml` — header line 1 `# FROZEN GOLDEN v1 — NEVER EDIT.` Deterministic UUIDs (line 28-30) match runner D2/H2 derivations. `test_schema_migration_regression.py` (per T-10) loads YAML + asserts deserializable to current SimulationResult.

## Findings (file:line)

### FAIL
- **[Cat 12] `tests/architecture/test_simulator_public_api_surface.py:139-149`** — `_ALLOWED_SUBMODULES` frozenset omits 11 test module basenames (`conftest`, `test_agent_bridge_unit`, `test_concurrency_property`, `test_customer_node_unit`, `test_leak_assertions_unit`, `test_observability_resilience`, `test_pydantic_models_unit`, `test_runner_unit`, `test_schema_migration_regression`, `test_simulator_smoke`, `test_termination_registry`). Under full pytest collection, these are imported and bound as attributes of the `simulator` parent package (Python's import machinery), causing `test_no_internal_symbols_leaked` to assert leakage. Reproducible: `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_simulator_public_api_surface.py -v --override-ini='addopts='` → 1 failed. **Required fix**: add the test module basenames to `_ALLOWED_SUBMODULES` OR scope the discovery walk to `simulator/_internal/*.py` + `simulator/{state,actor_profile,result,termination}.py` only (semantic intent — only public production module surfaces). Recommend the latter for cleaner intent (test files are not "internal symbols" in the H9 sense).

### WARN
- [Cat 15] `06-tickets.yaml:556` declares `decisions_applicable: [D7, H1, H9, H10]` → commit body cites inline but not formal "## Decisions honored" R6 section.

### info
- [Cat 6] `_fixtures/golden_v1_simulation_result.yaml:14-20` — header documents UUID5 derivation formulae explicitly so future schema bump audits can reproduce. Excellent forensic clarity.
- [Cat 10] `fixtures/actor_profiles.py:148-156` — `actor_profile_jailbreak_attempt.actor_goal` lists 7 explicit jailbreak variants ("modo debug", "eres un sistema de prueba", "override compliance", etc.) — defense-in-depth corpus for H10 leak gate.
- [Cat 13] `tests/architecture/test_simulator_no_mirrors_shared.py:7-12` — module docstring cites the historical PR-1 PI-1.1 hotfix 2026-05-01 origin. Documentation traceability.

## Cross-scope flags
None.

## Research notes
- Source: Pytest collection model (`https://docs.pytest.org/en/stable/explanation/goodpractices.html`).
- Takeaway: When test files live alongside the package they test, pytest collection imports them, binding as submodules to the parent package. Arch fitness gates that walk `dir(package)` MUST account for test module submodules (or scope to non-test paths only).

## Recommendations for builder fix-loop
1. **PRIORITY FAIL fix**: amend `tests/architecture/test_simulator_public_api_surface.py` `_ALLOWED_SUBMODULES` frozenset to either:
   - (a) include `conftest`, `test_agent_bridge_unit`, `test_concurrency_property`, `test_customer_node_unit`, `test_leak_assertions_unit`, `test_observability_resilience`, `test_pydantic_models_unit`, `test_runner_unit`, `test_schema_migration_regression`, `test_simulator_smoke`, `test_termination_registry` — full enumeration; OR
   - (b) preferred: filter `dir(simulator)` to skip `attr.startswith("test_")` and `attr == "conftest"` BEFORE the ModuleType check, since test modules are not "private symbol" leakage in the H9 sense.

   Then verify: `pytest tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_simulator_public_api_surface.py` PASS.

## Drift detection
NO drift in spec/intent — gate FAIL is implementation-detail bug (false positive). `06-tickets.yaml:563` "exact 7 names" cement is honored via `__all__`; the failing test merely has incomplete allowlist. CHANGES_REQUESTED, NOT escalation.

## Verdict
CHANGES_REQUESTED

## Findings
- 1 FAIL (Cat 12 — arch fitness gate `_ALLOWED_SUBMODULES` allowlist incomplete) / 1 WARN (Cat 15 R6 cite trivial) / 3 info

## Cited paths
- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py`
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/actor_profiles.py`
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml`
- `backend/tests/architecture/test_simulator_public_api_surface.py` (FAIL — Cat 12)
- `backend/tests/architecture/test_simulator_no_mirrors_shared.py`
- `backend/tests/architecture/test_simulator_writes_eval_kind_tag.py`
- `backend/tests/architecture/test_termination_policy_registry_contract.py`
- `backend/tests/architecture/test_schema_migrations_registry_complete.py`
- `docs/product/stories/eval-foundation-simulator-homologation/T-9-result.md`

<!-- @pm: T-9-review.md ready (verdict=CHANGES_REQUESTED). 1 FAIL — arch fitness gate `_ALLOWED_SUBMODULES` incomplete (recommend test_*.py + conftest exclusion via attr.startswith filter). Re-spawn builder for ≤5min fix; or accept story-B-internal escalation given gate is fitness-tier (not blocking semantic correctness). -->

---

## Self-fix log (auditor Cap 1/2)

**Date:** 2026-05-08T21:30:00Z
**Iter:** 1 of 2 max
**Type:** trivial test allowlist fix
**Commit:** 61b013a3

**Diagnosis:** `_ALLOWED_SUBMODULES` frozenset (line 139-149) omitted pytest collection-bound modules. Pytest binds sibling `test_*.py` + `conftest.py` as attributes of parent simulator package (structural, not semantic). Under full-suite collection, these surface as "unknown submodule" false-positive leaks.

**Fix applied:** Skip `attr.startswith("test_")` and `attr == "conftest"` BEFORE ModuleType walk. H9 invariant (`__all__` exact 7 names) untouched — only filters pytest collection-bound modules from leak walk.

**Verification:**
- `cd backend && .venv/bin/pytest tests/architecture/test_simulator_public_api_surface.py tests/agentic_evals/sales_agent/simulator/ -q` → **175 passed, 12 skipped, 0 fails**
- `ruff check + ruff format --check` → PASS

**Verdict updated:** CHANGES_REQUESTED → **APPROVED** (post-self-fix verified GREEN)
