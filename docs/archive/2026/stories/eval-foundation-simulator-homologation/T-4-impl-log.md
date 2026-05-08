# T-4 Impl Log — eval-foundation-simulator-homologation

**Ticket:** T-4 — Pydantic state machines + termination registry + schema migrations
**Owner:** builder-agentic Opus 4.7 (R23 ratification — agentic test-infra cero deuda)
**State transitions:** draft → developing → developed
**Started:** 2026-05-07 (today via Step 0 capture)
**Date stamp:** 2026-05-07T00:00:00Z

## Step 0 GATE — Skill consultation

R30 enforcement — skills declared + invoked + cited per CLAUDE.md mandate.

### Skills Consulted

1. **`copilot-expert`** (auto-loaded via `<skill-format>true</skill-format>` block)
   - Anti-duplication §0 cardinal — invertired §3 protected surfaces, "trazas mintiendo" anti-pattern, observability invariants for future T-5 callback handler subclass.
   - Decision applied: T-4 introduces ZERO observability code; T-5 builder will subclass shared `BaseObservabilityContext` + `BaseAgentCallbackHandler` per inventory. T-4 only ships Pydantic types + termination registry + schema migrations registry — clean separation honored.

2. **`sales-agent-expert`** (auto-loaded — required for any `tests/agentic_evals/sales_agent/`)
   - §3 protected surfaces verified UNTOUCHED: closer_studio, SmartBufferService, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot schema, tool_call_dedup.py.
   - "NO `from __future__ import annotations` en `*/orchestrator/graph.py`" — extended to story B `simulator/_internal/graph.py` cement; **also** applied to `simulator/state.py`, `actor_profile.py`, `result.py`, `termination.py` per arch-agentic decision §1.1 (LangGraph runtime introspection requires resolved annotations on Pydantic state).
   - Brand voice rule honored: customer prompt cache prefix safety reserved for T-6 builder (no `{tenant_name}` interpolation). T-4 ships only types — no prompt strings touched.

3. **`tessl__langgraph`** (LangGraph state graph patterns)
   - Pattern "Basic Agent Graph" + "State with Reducers" referenced.
   - Confirmed `Annotated[list[ConversationTurn], operator.add]` is canonical reducer hint (LangGraph 0.2+ tested per arch-agentic.md §15 research notes).
   - Pydantic state OK in LangGraph — `SimulationState(BaseModel)` validated per spec D4.

4. **`tessl__pytest-api-testing`** (pytest fixture + test organization)
   - Patterns applied: factory fixture `_make_actor()` / `_make_state()` / `_make_result()` for test data variations; pytest-classes (`TestActorProfile`, etc.) for grouping; parametrize for cross-class invariants (`test_every_class_has_schema_version_field`); explicit `pytestmark = pytest.mark.no_eval` to opt-out of `--run-evals` autouse marker per `tests/agentic_evals/sales_agent/conftest.py`.

### Skills NOT invoked (justified — no scope match)

- `tessl__graceful-degradation` — T-4 has zero external calls (no LLM, no DB, no HTTP). Pure Pydantic + registry types + tests. Graceful-degradation patterns belong to T-5..T-8 builders.
- `tessl__fastapi` — no FastAPI routes/endpoints in T-4 scope. Public API surface delivered via T-9 (`__init__.py` final).
- `claude-api` — no Anthropic SDK usage in T-4. Customer LLM dispatch reserved T-6.

## Default-flip detection (Step 0.5)

T-4 touches **zero** files in `backend/src/core/config.py`. No flag flips. Step 0.5 NA.

## Cross-module audit (NO-NEW-LAYER)

Step 0 anti-duplication greps executed:

```bash
# 1. Class collision check
grep -rn "class SimulationState\b\|class ActorProfile\b\|class TerminationReason\b\|class AgentErrorSubtype\b\|class CostSummary\b\|class SimulationResult\b\|class ConversationTurn\b" \
    backend/src backend/tests --include="*.py"
# → cero matches outside of `client_simulator/` legacy (D6 preserved). NEW types justified — eval test-infra ONLY.

# 2. Registry name collision
grep -rn "TERMINATION_POLICIES\|register_termination_policy\|SCHEMA_MIGRATIONS" \
    backend/src backend/tests --include="*.py"
# → cero matches. NEW. test-infra ONLY.
```

**Anti-duplication verdict:** zero mirror. Legacy reference (`client_simulator/src/simulator/state.py` TypedDict + `domain/models.py` Persona/Scenario Pydantic + `simulator/termination.py` logic + `domain/enums.py::FinishReason`) read for **inspiration ONLY**. Adapted to:
- TypedDict → Pydantic v2 BaseModel (D4)
- Persona/Scenario combined → ActorProfile (D7 Strands pattern)
- FinishReason 4 values → TerminationReason 6 values (preallocated for stories I/H)
- Implicit termination logic → registry pattern with `register_termination_policy()` public API (H8)

`client_simulator/` byte-equal — verified `git diff HEAD client_simulator/` empty.

## TDD execution (RED → GREEN per layer)

### Iteration 1 — All tests RED, then implementation GREEN

1. **Test files first (RED):**
   - `tests/agentic_evals/sales_agent/simulator/test_pydantic_models_unit.py` — 39 tests covering ActorProfile, ConversationTurn, CostSummary, SimulationResult, SimulationState (frozen, schema_version, validation, round-trip).
   - `tests/agentic_evals/sales_agent/simulator/test_termination_registry.py` — 6 tests: default policies registered, public API, enum value count + values, idempotency, non-callable rejection.
   - `tests/architecture/test_schema_migrations_registry_complete.py` — 11 tests: importability, types, exhaustive vs CURRENT_SCHEMA_VERSIONS, apply_migrations chain semantics.
   - Verified RED via `pytest --co` → `ModuleNotFoundError` for `simulator.actor_profile`, `simulator.termination`, `simulator._internal.schema_migrations`.

2. **Implementation files (GREEN):**
   - `simulator/actor_profile.py` — `ActorProfile(BaseModel)` per arch-agentic §1.1, frozen + extra=forbid + 11 fields including dialect_code BCP-47 default `es-419`.
   - `simulator/termination.py` — `TerminationReason` 6-value StrEnum + `AgentErrorSubtype` 4-value StrEnum + `TERMINATION_POLICIES` dict registry + `register_termination_policy(name, predicate)` public API + 4 default predicates registered at module import + `evaluate_termination(state)` iteration helper.
   - `simulator/result.py` — `ConversationTurn` (frozen, role Literal, min_length content), `CostSummary` (frozen, Decimal default zero, llm_calls_count_split Literal-keyed dict), `SimulationResult` (frozen, schema_version, all 14 spec fields).
   - `simulator/state.py` — `SimulationState(BaseModel)` per arch-agentic §1.1, extra=forbid, transcript with `Annotated[list[ConversationTurn], operator.add]` LangGraph reducer hint, all spec fields including `iterations` H3 max-iter guard, `eval_metadata` H5 propagation slot.
   - `simulator/_internal/schema_migrations.py` — `SCHEMA_MIGRATIONS` registry (empty for v1-only story B), `CURRENT_SCHEMA_VERSIONS` lookup dict for 5 Pydantic classes, `apply_migrations(model, raw, target)` chain function (raises KeyError on missing chain step), `register_schema_migration` decorator helper.
   - `simulator/__init__.py` — STUB exports per T-4 deliverable §7 (T-9 will rebind to exact 7-name `__all__`).
   - `simulator/_internal/__init__.py` — empty private namespace marker.

3. **Verified GREEN:**
   ```
   ============================== 57 passed in 11.11s ==============================
   ```

### Iteration 2 — Quality gates

- **`be_lint` (ruff check)** — Initial: 14 errors. Auto-fixed 10 (import paths, Decimal verbose). Remaining 4 ERA001 (commented-out-code false positive on section banners + example block). Resolved by:
  - Renaming section banners to non-Python-identifier-like (`# Enums per spec decision D5` instead of `# Enums (D5)`)
  - Moving migration example from inline comment to variable docstring
- **`be_format` (ruff format --check)** — 3 files reformatted (length 120 line wrapping). All clean.
- **`be_mypy_strict`** — Initial: 5 errors (Generic dict types, default_factory Literal inference, type annotation strictness). Resolved by:
  - `dict[str, object]` explicit args on `Callable[[dict], dict]` typing
  - `_default_llm_call_count_split` module-level factory function (mypy can't infer Literal keys from inline lambda dict literal)
  - `int(current_version_obj) if isinstance(current_version_obj, (int, str)) else 1` for `dict.get("schema_version", 1)` with `dict[str, object]`
  - `cls: type[BaseModel]` parametrize annotation
  - Replaced runtime-only `# type: ignore[call-arg]` blocks with `model_validate(dict)` for negative tests (mypy unhappy with kwarg pass when args don't match Pydantic generated `__init__` Literal).
- **`jscpd_no_duplication`** — 0.74% duplication (1 clone — import block between `__init__.py` STUB and `test_pydantic_models_unit.py`, semantically necessary). < 5% threshold PASS.

### Iteration 3 — Validators per acceptance

| Acceptance | Validator | Result |
|---|---|---|
| A1: All Pydantic classes deserializable + frozen + schema_version | `pytest test_pydantic_models_unit.py` (39 tests) | PASS |
| A2: TERMINATION_POLICIES exposes 4 default policies + register_termination_policy public | `pytest test_termination_registry.py::test_default_policies_registered` (+5 contract tests) | PASS |
| A3: SCHEMA_MIGRATIONS importable + arch fitness gate exhaustive | `pytest test_schema_migrations_registry_complete.py` (11 tests) | PASS |

### Cross-cutting verification

- **`be_arch_fitness_full`** — `tests/architecture/` 838 tests PASS (no regression introduced).
- **`legacy_client_simulator_intact` (D6 preservation gate)** — `git diff HEAD -- client_simulator/src/simulator/` empty. PASS.
- **Voseo glosary compliance** — pre-commit voseo hook honored: every test module + each module that mentions "voseo" carries `# voseo-allowed: …` magic comment escape per R25 (rule `.claude/rules/spanish-text.md`).

## Decisions taken (cementadas)

1. **`from __future__ import annotations` discipline** — extended cement scope per arch-agentic §1.1 from `simulator/_internal/graph.py` to ALL Pydantic state classes (`state.py`, `actor_profile.py`, `result.py`). LangGraph runtime introspection requires resolved annotations on the BaseModel class — same root cause as copilot redesign 2026-04 + sales-agent S6. `_internal/schema_migrations.py` retains `from __future__ import annotations` because it has no Pydantic class — only Callable type aliases; safe.

2. **Goal completion predicate stub** — T-4 registers `goal_completion` slot with always-None predicate. Story E (MAJ-EVAL grader) will override via `register_termination_policy("goal_completion", real_predicate)` (idempotent on name). This keeps the default-policy-list stable + lets stories I/H/E mutate via public API only.

3. **`apply_migrations` raises KeyError on missing chain step** — defensive design. If a future schema bump misses a migrator, deserialization of historic golden v1 fixtures will fail loud, not silent. Preserves frozen golden v1 contract H10.

4. **`current_version` type guard** — `dict[str, object]` strict typing required `isinstance(...)` check before `int(...)` coercion. Adds 1 line vs `# type: ignore` — preferred per arch-fitness rule + mypy strict invariant.

5. **`_default_llm_call_count_split` factory** — module-level not lambda, so mypy resolves `Literal["sales_agent", "eval_simulator"]` keys precisely. Documented inline why (avoids future mypy regression on lambda pattern).

## Files created

| Path | LOC | Purpose |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` | 35 | T-4 STUB public API surface (T-9 final) |
| `backend/tests/agentic_evals/sales_agent/simulator/state.py` | 119 | `SimulationState(BaseModel)` LangGraph state |
| `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` | 78 | `ActorProfile(BaseModel)` Strands pattern |
| `backend/tests/agentic_evals/sales_agent/simulator/result.py` | 156 | `ConversationTurn` + `CostSummary` + `SimulationResult` |
| `backend/tests/agentic_evals/sales_agent/simulator/termination.py` | 190 | StrEnum + registry + 4 default policies + evaluator |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/__init__.py` | 9 | private namespace marker |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` | 156 | H1 forward-compat registry + apply_migrations |
| `backend/tests/agentic_evals/sales_agent/simulator/test_pydantic_models_unit.py` | 458 | A1 acceptance — 39 tests |
| `backend/tests/agentic_evals/sales_agent/simulator/test_termination_registry.py` | 102 | A2 acceptance — 6 tests |
| `backend/tests/architecture/test_schema_migrations_registry_complete.py` | 209 | A3 acceptance — 11 tests |

Total: 1512 LOC (1041 production-types + 471 tests).

## Iteration log

| Iter | Action | Outcome |
|---|---|---|
| 1 | Read CONTEXT-BRIEF + 03-arch-agentic + 06-tickets T-4 entry | Mental model GREEN |
| 1 | Step 0 grep cross-codebase anti-duplication | Zero collisions — proceed |
| 1 | Read legacy `client_simulator/` reference files | Inspiration captured, NO copy |
| 1 | Write 3 RED tests (Pydantic models + termination + schema_migrations) | RED confirmed via collection failure |
| 1 | Implement 7 production files (state, actor_profile, result, termination, schema_migrations, 2x __init__) | RED → GREEN 57/57 |
| 2 | `ruff check` 14 errors → autofix 10 + manual 4 ERA001 | All pass |
| 2 | `ruff format` 3 files reformatted | All pass |
| 2 | `mypy --strict` 5 errors → fix Generic types + Literal-keyed factory | Mypy clean on file-level (note: dir-level fails because `tests/` is mypy-excluded — validator command will pick up files when src/eval_simulator/ exists post-T-1) |
| 2 | `jscpd` duplication scan | 0.74% < 5% threshold PASS |
| 3 | Re-run all tests after refactors | 57/57 GREEN |
| 3 | Full arch fitness suite | 838/838 GREEN — zero regression |
| 3 | D6 preservation gate | `git diff HEAD client_simulator/` empty PASS |

**State transition:** developing → developed (validators GREEN, ready for `/auditor` review per Conv 3 paradigm).

## Native-first commands record

```bash
# Lint
cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_schema_migrations_registry_complete.py --no-cache
# → All checks passed!

# Format
cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/simulator/ tests/architecture/test_schema_migrations_registry_complete.py
# → 10/10 formatted clean

# Mypy strict (file-level — dir-level needs T-1 src/ files)
cd backend && .venv/bin/mypy --strict --explicit-package-bases \
    tests/agentic_evals/sales_agent/simulator/state.py \
    tests/agentic_evals/sales_agent/simulator/actor_profile.py \
    tests/agentic_evals/sales_agent/simulator/result.py \
    tests/agentic_evals/sales_agent/simulator/termination.py \
    tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py \
    tests/agentic_evals/sales_agent/simulator/__init__.py \
    tests/agentic_evals/sales_agent/simulator/_internal/__init__.py \
    tests/agentic_evals/sales_agent/simulator/test_pydantic_models_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_termination_registry.py \
    tests/architecture/test_schema_migrations_registry_complete.py \
    --ignore-missing-imports
# → Success: no issues found in 10 source files

# Tests
cd backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/test_pydantic_models_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_termination_registry.py \
    tests/architecture/test_schema_migrations_registry_complete.py \
    --override-ini="addopts=" -v
# → 57 passed in 11.11s

# Arch fitness regression check
cd backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="
# → 838 passed in 29.74s

# jscpd
cd backend && npx --yes jscpd@4 tests/agentic_evals/sales_agent/simulator/ --min-tokens 50 --threshold 5 --reporters consoleFull
# → Found 1 clones with 10(0.74%) duplicated lines — under 5% threshold

# D6 preservation gate
cd /home/chris/AISALESHT && git diff HEAD --name-only -- client_simulator/src/simulator/
# → empty (PASS)
```
