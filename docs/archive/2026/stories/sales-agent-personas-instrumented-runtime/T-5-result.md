# T-5 Result — customer_node V1/V2 dispatch + eval_metadata extension

> Builder: builder-agentic-opus-4.7 (Claude Opus 4.7)
> State: developing → developed
> Surface: AGENTIC test-infra (production_code: false)
> Estimate: 1.5h · Actual: ~1h (single iteration, no cap reached)
> Commit SHA: `ed671c99`

## Summary

T-5 wires the V1/V2 customer prompt builder dispatch into
`customer_node.py` keyed on `actor_profile.schema_version` and extends
the per-LLM-call `eval_metadata` dict with the 3 Story C keys
(`persona_kind`, `schema_version`, `archetype`) without mutating the
underlying `state.eval_metadata` field. Story B 6-key H5 invariants
preserved end-to-end.

## Deliverables

| Path | Status | Notes |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` | EDIT | +56 lines: dispatch branch, structlog cache TTL hints, extended_eval_metadata builder. |
| `backend/tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py` | EDIT | +279 lines: `_stub_llm_factory` helper + `TestV1V2Dispatch` (2 tests) + `TestExtendedEvalMetadata` (3 tests). |
| `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` | EDIT | +87 lines: `test_eval_metadata_extended_persona_kind` smoke test (eval-gated). |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-5-impl-log.md` | NEW | Iteration log + skills consulted + validators outcome. |
| `docs/product/stories/sales-agent-personas-instrumented-runtime/T-5-result.md` | NEW | This file. |

3 source files touched; 419 insertions, 3 deletions.

## Acceptance criteria

- **A1** (06-tickets T-5.A1) — `customer_node` V1/V2 dispatch correct on
  `schema_version`. ✅ Verified by
  `test_customer_node_unit.py::TestV1V2Dispatch::*` (2 tests, both
  GREEN). V2 path triggers when `actor_profile.schema_version >= 2`
  (default per Story C T-1 bump); V1 path preserved verbatim for
  legacy `schema_version=1` instances.
- **A2** (06-tickets T-5.A2) — `eval_metadata` extended with
  `persona_kind` + `schema_version` + `archetype`. ✅ Verified by
  `test_customer_node_unit.py::TestExtendedEvalMetadata::*` (3 tests
  GREEN: extension shape, archetype default fallback, state-mutation
  guard). Smoke integration
  `test_simulator_smoke.py::test_eval_metadata_extended_persona_kind`
  gracefully skips outside `--run-evals` (parent conftest design) and
  will GREEN against persisted `eval_simulator_llm_call` rows when
  Postgres + LLM keys available.

## Validators (per 06-tickets.yaml T-5 quality_gates)

| Validator | Result |
|---|---|
| `be_lint` | ✅ All checks passed (ruff) |
| `be_format` | ✅ 36 files already formatted (ruff) |
| `be_mypy_strict` | ✅ 0 new errors on T-5 surface (3 files) — pre-existing 21 errors in `fixtures/tenant_seeded.py` baseline from Story A/B (T-4-result.md confirmed same baseline as PASS) |
| `agentic_observability_extended_metadata` | ⏭ eval-gated skip (test added; requires `--run-evals` + Postgres) |
| `legacy_simulator_invariants_intact` | ✅ 112/112 PASS (Story B 6 arch fitness gates intact) |
| `jscpd_no_duplication` | ✅ 20 clones vs 19 baseline (+1, threshold 5% not exceeded; `_stub_llm_factory` helper extracted to minimize duplication) |
| `customer_prompt_v2_unit` | ✅ 26/26 PASS (T-4 surface unchanged) |
| `be_arch_fitness_full` | ✅ 980/980 PASS |

Story B regression scope (downstream-regression.md surface map for
`simulator/_internal/customer_node.py`):

| Surface | Tests | Status |
|---|---|---|
| Story B 6 arch fitness gates | 112 | ✅ All green |
| V1 callers (test_customer_node_unit.py) | 22 (5 NEW + 17 pre-existing) | ✅ All green |
| Full simulator suite (no `--run-evals`) | 184 | ✅ 184 passed, 8 skipped (eval-marked, Postgres-bound) |
| Full BE arch fitness | 980 | ✅ All green |

## Decisions / cement

1. **Dispatch branch** — `if actor.schema_version >= 2:` not
   `actor.schema_version == 2`. Forward-compat: any future v3+ persona
   with sub-slot rotation features will continue to use the V2 builder
   transparently until a V3 builder is registered. v1 personas (legacy
   fixtures, frozen golden v1) take the `else` branch — byte-equal
   back-compat preserved (H10 cement Story B).

2. **`extended_eval_metadata` is a copy, not a mutation** — built via
   `dict(state.eval_metadata)` then `.update(...)`. The
   `SimulationState` field stays the H5 6-key dict; LangGraph node
   contract preserved (nodes return partial dicts, never mutate state).
   Verified by
   `test_eval_metadata_does_not_mutate_state_field`.

3. **Cache TTL hints are structlog-only** — emitted on every dispatch
   path with `cache_ttl_slots_1_2="1h"` and `cache_ttl_slots_3a_3b="5min"`
   on the V2 path. The actual cache wiring rides through LiteLLM Proxy
   headers per Story B path; the structlog event is informational and
   gives operators a fast `WHERE event_name LIKE 'simulator.customer_node_prompt_v%_dispatched'`
   diagnostic without scanning the rendered prompt body.

4. **`schema_version` stored as `str`** (not `int`) — per arch §4.5
   ("`str` for jsonb"). Postgres jsonb columns store all primitives;
   downstream filters
   `WHERE eval_metadata->>'schema_version' = '2'` expect string values.
   Coerced at the customer_node site, not at the persistence boundary,
   because the customer_node is the only writer that adds the key.

5. **`archetype` defaults to `''`** when `actor_profile.metadata` lacks
   the key — keeps the column shape uniform across legacy fixtures
   (which have `metadata` dicts that don't declare archetype) and new
   archetype-aware YAML personas. Empty string is jsonb-safe and avoids
   `null` semantics issues at the SQL layer.

6. **Anti-duplication helper extracted** — `_stub_llm_factory(
   monkeypatch, captured_messages=, captured_kwargs=, response_content=)`
   is the canonical LLM mock setup for any future test in this module
   that needs to probe the LLM boundary. jscpd clone count post-extract
   is +1 over baseline (vs +5 pre-extract).

## Skills consulted

1. **`copilot-expert`** — Anti-duplication §0 cardinal rule consulted;
   verified `eval_metadata` extension propagates through canonical
   `EvalSimulatorObservabilityContext` subclass (no mirror, no new
   layer). The `_assert_eval_metadata_complete` helper in
   `_internal/observability.py` enforces 6-key MINIMUM (subset check),
   so adding 3 NEW keys is shape-compatible.
2. **`sales-agent-expert`** — §3 protected surfaces verified untouched
   (closer_studio, SmartBufferService, OutputManager, enrollment_*,
   webhook adapters, follow_up_engine, PromptVersionModel,
   model_pricing_snapshot schema, tool_call_dedup,
   personality_profiles.system_instruction). All edits remain under
   `tests/agentic_evals/sales_agent/simulator/`.
3. **`tessl__langgraph`** — Pydantic state cement verified: customer_node
   returns partial dict (no state mutation); reducer
   `transcript: Annotated[list[ConversationTurn], operator.add]`
   contract preserved. `from __future__ import annotations` cement
   honored (NOT introduced).
4. **`tessl__graceful-degradation`** — All existing failure paths
   preserved: turn 0 short-circuit, TimeoutError → http_error,
   generic Exception → http_error, structlog warnings on every failure.
   Cache TTL hint is informational logging only; no new external call.
5. **`tessl__pytest-api-testing`** — Async fixture patterns
   (`monkeypatch`, `AsyncMock`, `pytestmark = pytest.mark.no_eval`)
   honored; helper extraction follows DRY guidance.
6. **`tessl__fastapi`** — N/A.
7. **Anthropic prompt caching** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching,
   accessed 2026-05-08) — slot architecture aligns with 02-design-agentic.md
   §5: slot 1+2 (1h TTL invariant per persona) + slot 3a/3b (5min TTL
   pain/objections sub-slots) + variable suffix
   (`current_turn` + `next_objection_hint`, intentionally outside cache
   prefix). Builder enforces this via T-4's V2 template signature
   (no `tenant_id` parameter cement).

## Cross-module audit (NO-NEW-LAYER)

```bash
# Verify no new dispatcher / factory / registry layer introduced
$ grep -rn "extended_eval_metadata\|build_customer_prompt_v2" /home/chris/AISALESHT/backend/src/
# (empty — V2 builder + extended_eval_metadata are eval test-infra only;
#  no production code surface introduced)
```

EXTEND only: `customer_node` body extended with dispatch + metadata
build; `customer_persona_prompt.build_customer_prompt_v2` consumed
verbatim from T-4. Zero new module, zero new abstraction layer, zero
mirror.

## Next ticket

T-6 (Scenario 5 integration — agent qualifies out unqualified lead × 5
archetypes × 3 trials, ★ production-critical) — depends_on T-1, T-3,
T-4, T-5 ✅ all done. Builder-agentic Opus 4.7 spawn ready.
