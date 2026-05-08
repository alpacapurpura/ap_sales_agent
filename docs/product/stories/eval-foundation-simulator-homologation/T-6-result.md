# T-6 Result — Customer node + persona prompt v1 + EVAL_LLM_ROLES + concurrency semaphore

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-6
**Owner:** builder-agentic Opus 4.7 (R23 — voice fidelity defense + cache prefix safety + dialect injection)
**State:** developed (validators GREEN, awaiting `/auditor` independent verdict per Conv 3)
**Date stamp:** 2026-05-08

## Summary

Shipped the dual-LLM simulator's customer side — the LangGraph node that
generates the next customer message based on a deterministic actor persona,
plus its eval-only registry, prompt template v1, and per-worker concurrency
semaphore:

- `EVAL_LLM_ROLES` registry (eval-only, separate from production
  `LLM_ROLE_BY_SITE` SSoT — decision §2.1 arch-agentic.md). Single role
  `EVAL_USER_SIMULATOR → ModelRole.NANO`. `EVAL_DEFAULT_MODELS` map binds the
  role to wire-name `gpt-5-nano`. Defensive `get_eval_llm_model(role)`
  accessor raises `KeyError` on unknown role.
- `CUSTOMER_PERSONA_PROMPT_V1` — H1 versioned prompt template adapted from
  `client_simulator/src/simulator/customer_node.py::PERSONA_SYSTEM_PROMPT`
  (legacy preserved byte-equal under `client_simulator/` per D6). 7 strict
  rules, [EXIT] token, hidden actor_goal not revealed, no-emojis, no-personaje-roto.
  Cache-prefix safe: NO `{tenant_name}` interpolation mid-block, NO timestamps,
  NO conversation IDs. `build_customer_prompt(actor_profile)` signature
  accepts ZERO tenant identity parameters — type-system enforces invariant.
- `EVAL_SIMULATOR_SEMAPHORE` — module-level `asyncio.Semaphore(N)` with
  `EVAL_SIMULATOR_MAX_CONCURRENCY` env override (default 10). Per-worker
  semantics matching `OutboundRateLimiter` precedent. `get_eval_simulator_semaphore()`
  accessor for test mocks.
- `customer_node` — LangGraph async node: turn 0 short-circuit (verbatim
  `actor.initial_message`, no LLM, no semaphore acquire); turn N+ wraps
  `await llm.ainvoke(...)` in `async with EVAL_SIMULATOR_SEMAPHORE`; LLM
  via `LLMFactory.get_service().get_client(role=ModelRole.NANO)`; `model_override`
  + `eval_metadata` propagated via `config={"metadata": {...}}` to the
  `EvalSimulatorCallbackHandler` (T-5). Returns partial state dict
  `{"transcript": [new_turn]}` on success or `{"is_finished": True,
  "error_subtype": "http_error"}` on graceful failure (TimeoutError +
  generic Exception isolated branches with structlog warnings).
- 17 acceptance tests covering A1 (initial-turn-zero, dialect injection
  including `test_dialect_es_ar_voseo` headline, no-tenant-leak,
  pain-points/objections rendering, template-v1 shape), A2 (semaphore
  acquired during LLM call, module singleton, default cap 10), A3
  (eval registry isolation from production SSoT), error path (graceful
  termination via H7 taxonomy), and LLM dispatch (factory invocation +
  whitespace-stripped output appended).

Zero touch on protected surfaces (sales-agent §3, R5 schema-mirror exception
NA — T-6 lives entirely under `tests/`). Zero mirror of any shared abstraction
per anti-duplication §0 — customer node consumes `LLMFactory`, `LangGraph`,
`langchain_core.messages`, `structlog`; introduces no new abstractions.

## Acceptance criteria

| ID | Description | Verifier (06-tickets.yaml literal) | Result |
|---|---|---|---|
| A1 | Customer node generates message from ActorProfile + dialect respected | `pytest test_customer_node_unit.py::test_dialect_es_ar_voseo` | **PASS** |
| A2 | Concurrency semaphore caps active LLM calls (baseline; full property test = T-10) | `pytest test_concurrency_property.py` (T-10 deliverable; T-6 baseline `TestSemaphoreWrapping` 3 tests) | **PASS (baseline)** |
| A3 | EVAL_LLM_ROLES NOT polluting LLM_ROLE_BY_SITE SSoT | `! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py` | **PASS** |

A2's full property-based concurrency test (`test_concurrency_property.py`) is
T-10 deliverable per ticket spec ("full coverage en T-10, baseline aquí"). The
T-6 baseline asserts `async with` semantics on a size-1 semaphore mock, plus
module-singleton invariant, plus default cap 10 — sufficient unit-level
evidence H4 wiring is correct.

## Validator gates output

| Validator | Status | Notes |
|---|---|---|
| `be_lint` | PASS | 0 errors after 1-pass autofix (3 RUF002 multiplication-sign + 1 N802 lowercase) |
| `be_format` | PASS | 5/5 files formatted clean after `ruff format` |
| `be_mypy_strict` | PASS | 0 errors on 5/5 source files (`--strict --ignore-missing-imports`) |
| `hardening_h3_concurrency_property` | DEFERRED | Full property test belongs to T-10 (06-tickets.yaml T-10 explicit). T-6 baseline 3 tests in `TestSemaphoreWrapping` PASS. |
| `jscpd_no_duplication` | PASS (inherited) | T-4 ran the project-wide jscpd at 0.74%; T-6 only adds module-internal code with no clone-magnet patterns |
| Native ticket tests | PASS | 17/17 in `test_customer_node_unit.py` |
| Full simulator suite | PASS | 79/79 (no regression on T-4 + T-5; 5 postgres-only T-3 skips unrelated) |
| `tests/architecture/test_no_new_sales_agent_module_imports.py` | PASS | Ratchet preserved |
| `tests/architecture/test_copilot_anchors.py` | PASS | Anchor cap 36/36 untouched |
| A3 shell verifier | PASS | `! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py` exits 0 |
| D6 preservation gate | PASS | `git diff HEAD -- client_simulator/` empty |
| Anti-pollution defense | PASS | `grep -rn 'EVAL_USER_SIMULATOR\|EVAL_LLM_ROLES' backend/src/` returns zero matches |

The validator gates `agentic_no_mirrors_shared`, `agentic_eval_kind_tag_enforced`,
`agentic_observability_invariants` (T-9 deliverable arch fitness suite) are NOT
yet present in the architecture suite — preconditions (the customer-side wiring
those gates probe) are now in place via T-6.

## Diff resumen

5 NEW files, 1112 LOC total after format:

```
backend/tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py                (NEW,  86 LOC)
backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py  (NEW, 125 LOC)
backend/tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py              (NEW,  86 LOC)
backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py            (NEW, 209 LOC)
backend/tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py            (NEW, 478 LOC)
                                                                                  TOTAL: 1112 LOC (+ 128 LOC docstrings vs net code ≈ 984 LOC)
```

Plus: `06-tickets.yaml` T-6 entry transitions appended; `checkpoint.md` state +
bitácora updated; `T-6-impl-log.md` written.

## Hardening invariants honored

| H | Invariant | Where enforced in T-6 |
|---|---|---|
| **H1** | **Schema versioning forward-compat** | `CUSTOMER_PERSONA_PROMPT_V1` constant name pins the version. Future bump → `CUSTOMER_PERSONA_PROMPT_V2` + migration entry in `_internal/schema_migrations.py` (T-4 registry). Frozen golden v1 fixture (T-9/T-10) materializes deterministic prompt — DO NOT edit V1 once committed without bumping. |
| H2 | Idempotency UUID5 | NA T-6 (T-8 runner derives via uuid5). Customer node reads `state.simulation_id` as opaque value. |
| H3 | Async-first concurrency-safe | Customer node is `async def`. Returns partial state dict (no in-place mutation). Reducer `Annotated[list, operator.add]` (T-4 state.py) handles transcript merge. |
| **H4** | **Rate-limiting customer LLM** | **PRIMARY T-6 deliverable.** `EVAL_SIMULATOR_SEMAPHORE = asyncio.Semaphore(int(os.getenv('EVAL_SIMULATOR_MAX_CONCURRENCY', '10')))` module-level. `async with EVAL_SIMULATOR_SEMAPHORE:` wraps ONLY `await llm.ainvoke(...)` (the rate-limited resource). Cheap CPU ops outside. Per-worker semantics. |
| H5 | Observability eval-vs-prod tags | Customer node propagates `eval_metadata` from `state.eval_metadata` → `config={"metadata": {"eval_metadata": dict(state.eval_metadata), "model_override": "gpt-5-nano"}}` → `EvalSimulatorCallbackHandler` (T-5) reads from config metadata in callbacks. The 6-key invariant H5 SSoT is enforced at the handler layer (T-5 `__post_init__` defense). |
| H6 | Cost bucket separation | Customer node does NOT directly write rows; the callback handler does (T-5). The handler subclass writes to `eval_simulator_llm_call` / `eval_simulator_trace_event` (NOT sales_agent tables) — physical separation enforced upstream. |
| **H7** | **Failure-mode taxonomy** | LLM exception → `error_subtype="http_error"` (str round-trips into `AgentErrorSubtype` StrEnum at state assignment). Empty response → same path. TimeoutError separated branch (structlog event differentiates) but maps to same subtype to keep T-6 minimal — story F upgrade may add `timeout` subtype. |
| H8 | Termination policy registry | NA T-6 (T-4 owns registry; T-8 wires `should_continue`). Customer node sets `is_finished=True` on failure → `_agent_error_predicate` (T-4 default) catches in T-8 graph eval. |
| H9 | Public API surface minimal | All 4 new files live under `_internal/` — none exported from `simulator/__init__.py`. T-9 finalizes the 7-name public `__all__` (does NOT include any T-6 symbol). |
| **H10** | **Frozen golden v1 fixture** | The persona prompt template constant `CUSTOMER_PERSONA_PROMPT_V1` is the V1 invariant: future bumps require migrator. Story B does NOT ship the YAML golden — that's T-9/T-10 deliverable. T-6 ships the bytecode-frozen template that the golden will reference. |

## Decisions (architectural fingerprints recorded)

The 9 decision fingerprints were documented during the initial build pass in
T-6-impl-log.md § "Decision fingerprints". The resume operation honored every
single one of them verbatim. Summary:

1. `from __future__ import annotations` allowed in 3 files (registries +
   prompt + concurrency); FORBIDDEN in `customer_node.py` (LangGraph runtime
   introspection consumer).
2. Customer prompt slot order — `dialect_code` rendered early (LLM sees
   dialect immediately).
3. Module-level `EVAL_SIMULATOR_SEMAPHORE` — initialized at import (H4 spec
   "global per worker"); `get_eval_simulator_semaphore()` for test mocks.
4. `build_customer_prompt(actor_profile)` minimal signature — NO `tenant_id`
   parameter (cache prefix safety enforced via type system).
5. Initial turn 0 reads `actor.initial_message` (flat field per T-4
   canonical schema; ticket's "context.initial_message" reference was a
   draft revision leftover).
6. `async with EVAL_SIMULATOR_SEMAPHORE` wraps ONLY `await llm.ainvoke(...)`;
   prompt building + message construction outside (cheap CPU ops).
7. Failure path returns `error_subtype="http_error"` — string assigned to
   `AgentErrorSubtype | None` field; StrEnum coerces.
8. TimeoutError vs broad Exception separated branches — different structlog
   events for differentiation; both map to same `is_finished=True` +
   `error_subtype="http_error"`.
9. No `del tenant_id` antifootgun needed — signature has no `tenant_id`
   parameter at all.

Two additional resume-time refinements (R30 builder phase polish only):

10. Renamed `test_build_customer_prompt_injects_dialect_es_ar` →
    `test_dialect_es_ar_voseo` to match `06-tickets.yaml` T-6.A1
    `verifier.path` literal — verifier name strict-match invariant honored.
11. Replaced 3 multiplication-sign characters in `concurrency.py` docstring
    with literal `x` (RUF002 lint) + lowercased `NOT` in test name (N802
    PEP 8) — cosmetic only.

## Files NOT touched (verification)

- `client_simulator/src/simulator/*.py` — D6 preservation gate PASS
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording,observability/persistence}/` — unchanged
- `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE` — unchanged (decision §2.1 arch-agentic.md)
- `backend/src/shared/{infrastructure,agent_observability}/` — read-only (consumed via `LLMFactory.get_service()`)
- `backend/src/modules/sales_agent/observability/eval_simulator/` — T-1 deliverable; left intact
- `backend/src/shared/infrastructure/agent_observability_bootstrap.py` — T-1 already wired
- `backend/src/core/config.py` — no flag flips (Step 0.5 NA)
- T-4 deliverables (`state.py`, `actor_profile.py`, `result.py`, `termination.py`,
  `_internal/schema_migrations.py`) — read-only
- T-5 deliverable (`_internal/observability.py`) — read-only
- All §3 sales-agent protected surfaces — UNTOUCHED
- All `.claude/rules/*` — unchanged

## Native commands record

```bash
# Lint clean (post-fix)
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check \
    tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py \
    tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py \
    tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py --no-cache
# → All checks passed!

# Format clean
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check \
    tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py \
    tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py \
    tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py
# → 5 files already formatted

# Mypy strict file-level
cd /home/chris/AISALESHT/backend && .venv/bin/mypy --strict \
    tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py \
    tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py \
    tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py \
    tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py \
    --ignore-missing-imports
# → Success: no issues found in 5 source files

# Native ticket tests
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py -v --tb=short \
    --override-ini="addopts="
# → 17 passed, 1 warning in 10.70s

# Full simulator suite (no regression)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/ --override-ini="addopts=" -q
# → 79 passed, 5 skipped (postgres-only T-3 tests)

# Architecture fitness smoke (no regression on ratchet/anchor caps)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/architecture/test_no_new_sales_agent_module_imports.py \
    tests/architecture/test_copilot_anchors.py \
    --override-ini="addopts=" -q
# → 5 passed, 1 warning

# A3 verifier (06-tickets.yaml shell)
! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py
# → exit 0 (A3 PASS)

# Anti-pollution defense (extra)
grep -rn 'EVAL_USER_SIMULATOR\|EVAL_LLM_ROLES' /home/chris/AISALESHT/backend/src/
# → (empty) — eval-only registry zero pollution

# D6 preservation gate
git diff HEAD --name-only -- client_simulator/
# → (empty)
```

## Commit SHA

To be filled by the orchestrator on `git push origin development` success.

## Next builders

T-7 (agent_bridge in-process + leak_assertions) consumes:
- `EvalSimulatorCallbackHandler` + `build_eval_metadata` from T-5 (already shipped)
- T-6 deliverables NOT consumed directly — T-7 owns the agent side, T-6 owns the customer side; both are graph nodes that meet at T-8.

T-8 (graph compose + run_simulation) consumes:
- `customer_node` (T-6) — wired via `g.add_node("customer", customer_node)`
- `agent_bridge` (T-7) — paired node
- `EVAL_SIMULATOR_SEMAPHORE` (T-6) — propagated via the customer node
- `evaluate_termination` + `TERMINATION_POLICIES` (T-4) — wires the conditional edge `should_continue`
- `SimulationState`, `SimulationResult`, `AgentErrorSubtype` (T-4) — state schema + return type + failure taxonomy

T-9 (public API + frozen golden + arch gates) finalizes:
- `simulator/__init__.py::__all__` to exact 7 names (H9) — none of T-6's symbols re-exported
- 5 NEW arch fitness gates that probe T-6 invariants (no-mirror, eval-kind-tag, public API, schema registry, termination registry)
- Frozen golden v1 fixture (H10) materializing `CUSTOMER_PERSONA_PROMPT_V1` rendered output
- `test_concurrency_property.py` (full A2 verifier) — property-based hypothesis test on the semaphore ceiling

T-10 (smoke parametrize + observability writes assertion + fitness gates) consumes T-6 customer-side via the integrated graph (T-8).

## Audit readiness

T-6 deliverables align literal with `06-tickets.yaml` line items:

- ✅ `_internal/llm_roles.py` — `EVAL_LLM_ROLES = {"EVAL_USER_SIMULATOR": ModelRole.NANO}` eval-only registry
- ✅ `_internal/customer_persona_prompt.py` — `CUSTOMER_PERSONA_PROMPT_V1` constant adapted from legacy. Versioned (H1). NO `{tenant_name}` mid-block. Voseo permitido si `dialect_code='es-AR'` (magic comment escape applied)
- ✅ `_internal/concurrency.py` — `EVAL_SIMULATOR_SEMAPHORE = asyncio.Semaphore(int(os.getenv('EVAL_SIMULATOR_MAX_CONCURRENCY', '10')))` module-level (H4)
- ✅ `_internal/customer_node.py` — LangGraph node async. Builds prompt from ActorProfile (dialect-aware). Calls LLM via `LLMFactory.get_service().get_client(role=ModelRole.NANO)` with `model_override` + `eval_metadata` propagated. Honors concurrency semaphore. Initial turn 0 = `actor_profile.initial_message` (no LLM, no semaphore). Subsequent turns LLM-generated. Failure modes mapped to `error_subtype` taxonomy.
- ✅ A1 `test_dialect_es_ar_voseo` (verifier path literal) PASS
- ✅ A2 baseline (3 tests in `TestSemaphoreWrapping`) PASS — full property test = T-10
- ✅ A3 negative grep + extra anti-pollution scan PASS
- ✅ Anti-duplication §0 cardinal honored — all 4 new basenames unique under `simulator/_internal/`; legacy `client_simulator/customer_node.py` byte-equal preserved
- ✅ Spanish neutro respected (logs/structlog event names neutral); voseo allowed via magic comment escape on persona prompt + tests
- ✅ Best-effort failure handling — both TimeoutError and broad Exception branches log via `structlog.warning` and return graceful termination dict (no exception bubble)

Verdict for orchestrator: T-6 ready for gate-runner pickup → auditor-agentic
independent review. Build phase state per R30 is `tests-passing` ONLY — auditor
verdict is independent and not claimed here.
