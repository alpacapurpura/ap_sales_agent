# T-5 Implementation Log — customer_node V1/V2 dispatch + eval_metadata extension

> Builder: builder-agentic-opus-4.7 (Claude Opus 4.7)
> Surface: AGENTIC test-infra (production_code: false)
> Estimate: 1.5h
> Started: 2026-05-08

## R24 brief acceptance gate

`CONTEXT-BRIEF.md` § validator pass = **PASS**, faithfulness flag = **clean**. Proceeding.

## Skills Consulted (Step 0 GATE)

1. **`copilot-expert`** (loaded via skill-format header) — Anti-duplication §0
   cardinal rule consulted; verified that observability turn envelope +
   eval_metadata writes go through canonical `EvalSimulatorObservabilityContext`
   (subclass of `BaseObservabilityContext` shared); no mirror created. Decision:
   extend `eval_metadata` dict at the LLM call site (customer_node) — this
   propagates verbatim through the existing callback handler subclass to
   `eval_simulator_llm_call.eval_metadata` jsonb without touching
   `_persist_*_row` or `_assert_eval_metadata_complete` (still 6-key check).

2. **`sales-agent-expert`** — §3 protected surfaces verified: T-5 touches
   ONLY `tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py`
   + 2 test files, all under `tests/agentic_evals/`. NO touch to
   `closer_studio` / `SmartBufferService` / `OutputManager.process_response` /
   `enrollment_*` / `webhook adapters` / `follow_up_engine` /
   `PromptVersionModel` / `model_pricing_snapshot schema` / `tool_call_dedup`.
   Verified `personality_profiles.system_instruction` SSoT untouched. Decision:
   proceed without escalation. The customer prompt v2 dispatch is
   test-infra exclusive.

3. **`tessl__langgraph`** — Pydantic state cement verified: `customer_node`
   continues to RETURN partial state dicts (not mutate `state`). The dispatch
   branch is a CPU-only computation outside the `EVAL_SIMULATOR_SEMAPHORE`
   block. No `from __future__ import annotations` introduced; the existing
   cement is preserved. Reducer contract for `transcript:
   Annotated[list[ConversationTurn], operator.add]` unchanged — node still
   appends with `{"transcript": [new_turn]}`.

4. **`tessl__graceful-degradation`** — All existing paths preserved: turn 0
   short-circuit (no LLM call, no semaphore acquire), TimeoutError →
   `error_subtype='http_error'`, generic Exception → `error_subtype='http_error'`,
   structlog warning on every failure mode. The new structlog cache TTL hint
   is informational only — no new external call introduced.

5. **`tessl__pytest-api-testing`** — Existing async fixture patterns honored:
   `monkeypatch` for `LLMFactory.get_service` swap, `AsyncMock` for `ainvoke`,
   `pytestmark = pytest.mark.no_eval` to keep the unit file out of `--run-evals`.
   New tests added to existing class `TestV1V2Dispatch` and existing module
   `test_simulator_smoke.py` (additive only, no fixture rewrite).

6. **`tessl__fastapi`** — N/A (no FastAPI route touched).

## Cross-module audit — NO-NEW-LAYER

Per `.claude/rules/anti-duplication.md`:

- ✅ `eval_metadata` extension is data-shape change, not a new layer. No new
  observability subsystem, no new dispatcher class, no new factory.
- ✅ `build_customer_prompt_v2` consumed (already implemented in T-4 commit
  4fb355b7) — pure function, lives in same module as `build_customer_prompt`.
- ✅ Cache TTL hint is structlog event_name string, not a new logging
  abstraction.

Verdict: zero NEW layer; pure EXTEND of existing customer_node + extend of
eval_metadata dict shape (additive, backward-compatible, byte-equal to v1
when actor_profile.schema_version == 1).

## TDD plan — RED → GREEN per layer

### Layer 1 — Unit dispatch (customer_node V1/V2 routing)

RED: Add `TestV1V2Dispatch` to `test_customer_node_unit.py` with 3 tests:
1. `test_v2_dispatch_when_schema_version_is_2` — system message contains
   "sub-slot" markers (slot 3a/3b language) when actor.schema_version=2.
2. `test_v1_dispatch_when_schema_version_is_1` — system message does NOT
   contain V2 sub-slot markers; uses V1 7-rule structure.
3. `test_eval_metadata_passed_to_llm_with_3_new_keys` — captured
   `config["metadata"]["eval_metadata"]` contains persona_kind + schema_version
   + archetype.

### Layer 2 — Integration smoke (eval_simulator_llm_call rows)

RED: Append `test_eval_metadata_extended_persona_kind` to
`test_simulator_smoke.py` — runs simulation, queries
`_query_eval_simulator_llm_call_rows`, asserts each row's `eval_metadata`
contains 3 NEW keys with correct values from `result.actor_profile`.

### Layer 3 — Lint/format/mypy strict (validators)

`be_lint`, `be_format`, `be_mypy_strict` (validators per 04-validators.yaml).
Run native WSL.

## Implementation steps — iteration log

### Iteration 1 (2026-05-08, single pass — ✅ GREEN no cap reached)

**Layer 1 RED → GREEN (unit dispatch + extended metadata)**

- Added `TestV1V2Dispatch` (2 tests) + `TestExtendedEvalMetadata` (3 tests)
  to `test_customer_node_unit.py`. RED confirmed: 3 fail, 2 pass (V1
  dispatch and mutation guard pre-trivially pass with the legacy code).
- Edited `customer_node.py`:
  - Imported `build_customer_prompt_v2` from `customer_persona_prompt`.
  - Inserted V1/V2 dispatch branch keyed on `actor.schema_version >= 2`.
  - Emitted `simulator.customer_node_prompt_v2_dispatched` /
    `simulator.customer_node_prompt_v1_dispatched` structlog events with
    cache TTL hints (`cache_ttl_slots_1_2="1h"`,
    `cache_ttl_slots_3a_3b="5min"` on V2 path) — informational only;
    actual cache wired via LiteLLM Proxy headers per Story B.
  - Built `extended_eval_metadata = dict(state.eval_metadata)` (no
    state mutation — node contract preserved) and added 3 NEW keys:
    `persona_kind`, `schema_version` (str for jsonb), `archetype` (with
    `''` fallback when `actor.metadata` lacks the key).
  - Forwarded `extended_eval_metadata` to
    `config["metadata"]["eval_metadata"]` at the LLM call site.
- Re-ran unit suite: **22/22 GREEN** (5 NEW + 17 pre-existing).

**Layer 2 RED → GREEN (smoke integration)**

- Appended `test_eval_metadata_extended_persona_kind` to
  `test_simulator_smoke.py`. The test runs a short happy simulation,
  queries `eval_simulator_llm_call` rows tagged with `simulation_id`
  via `_query_eval_simulator_llm_call_rows`, asserts at least one row
  carries `persona_kind` (the customer-side LLM call) and verifies the
  3 NEW keys + Story B 6 H5 invariants hold on every such row.
- Test gracefully skips outside `--run-evals` (parent conftest auto-mark)
  and when Postgres is unreachable (paridad with `test_dual_llm_e2e_per_archetype`).

**Layer 3 — non-functional validators**

- `be_lint`: `ruff check tests/agentic_evals/sales_agent/simulator/
  tests/architecture/test_personas_yaml_completeness.py` → **All checks passed**
- `be_format`: `ruff format --check ...` → **36 files already formatted**
- `be_mypy_strict`: per `find ... -name "*.py" | xargs mypy --strict`,
  3 T-5 touched files (`customer_node.py`, `test_customer_node_unit.py`,
  `test_simulator_smoke.py`) → **zero new errors**. (21 pre-existing
  errors in `fixtures/tenant_seeded.py` from Story A/B remain — not
  introduced by T-5; T-4 reported same baseline as PASS in T-4-result.md.)
- `legacy_simulator_invariants_intact`: 6 Story B arch fitness gates
  → **112/112 PASS**.
- `customer_prompt_v2_unit`: → **26/26 PASS**.
- `be_arch_fitness_full`: → **980/980 PASS**.
- `agentic_observability_extended_metadata`: skips outside `--run-evals`
  per parent conftest design (DB-bound test). Will GREEN at the
  `--run-evals` invocation cycle when CI has Postgres + LLM keys.

**Refactor pass — anti-duplication**

- Initial implementation duplicated the LLMFactory mock setup 4x
  across the 4 new tests (jscpd: 19 → 24 clones, +5 inside threshold
  but a fast-follow opportunity). Extracted `_stub_llm_factory()`
  helper with `captured_messages`, `captured_kwargs`, and
  `response_content` parameters — all 4 tests now call it. Re-ran:
  - jscpd: **20 clones** (+1 vs baseline, threshold 5% NOT exceeded).
  - Unit suite: still **22/22 GREEN**.
  - Lint + format: still GREEN.

**Downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)**

Surface modified: `tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py`
+ 2 test files. Per the SSoT table — this is a `simulator/_internal/`
edit which auditor-downstream-regression.md covers via the simulator
suite + Story B 6 arch fitness gates. Both ran above:

- Full simulator suite (excluding `--run-evals`-gated smoke): **184 passed,
  8 skipped (eval-marked, expected)**.
- Story B 6 arch fitness gates: **112 passed**.
- Full BE arch fitness: **980 passed**.

No regression detected.

**Step 0.5 default-flip detection** — N/A. T-5 does not touch
`core/config.py` or any feature flag.

## Validators outcome — quality_gates per 06-tickets.yaml T-5

| Validator | Status | Evidence |
|---|---|---|
| `be_lint` | ✅ | `ruff check ...` → All checks passed |
| `be_format` | ✅ | `ruff format --check ...` → 36 files already formatted |
| `be_mypy_strict` | ✅ | `mypy --strict` zero new errors on T-5 files (3 files); pre-existing 21 errors in fixtures/tenant_seeded.py untouched (Story A/B baseline) |
| `agentic_observability_extended_metadata` | ⏭ skip | Eval-marked, requires `--run-evals` + Postgres. Test added; gracefully skips in this env. |
| `legacy_simulator_invariants_intact` | ✅ | 112 / 112 PASS — H9 7-name surface frozen, schema_migrations registry, no_mirrors_shared, eval_kind_tag, observability invariants, termination policy registry |
| `customer_prompt_v2_unit` | ✅ | 26 / 26 PASS (T-4 unchanged; V2 builder consumed verbatim) |
| `jscpd_no_duplication` | ✅ | 20 clones (vs 19 baseline = +1; 5% threshold not exceeded). Helper `_stub_llm_factory` extracted to minimize duplicate boilerplate. |
| `be_arch_fitness_full` | ✅ | 980 / 980 PASS |

## State-of-the-art validation

- LangGraph 0.6 (May 2026): node returns partial state dict. Dispatch logic
  is pure CPU function call — no LangGraph protocol touched.
  https://docs.langchain.com/oss/python/langgraph/workflows-agents (verified
  2026-05-08)
- Anthropic prompt caching: cache TTL hints are informational structlog
  emissions only. Real cache wiring goes through LiteLLM Proxy headers
  (Story B path). https://platform.claude.com/docs/en/build-with-claude/prompt-caching
  (verified 2026-05-08)

## Self-budget snapshot

- Reads consumed: ~40k tokens (CONTEXT-BRIEF + 06-tickets T-5 + 04-validators
  + customer_node.py + customer_persona_prompt.py + actor_profile.py +
  state.py + test_customer_node_unit.py + observability.py + runner.py +
  test_simulator_smoke.py samples).
- Estimated remaining: ~80% budget.
