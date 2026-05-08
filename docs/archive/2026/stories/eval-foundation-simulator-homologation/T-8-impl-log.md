# T-8 Impl Log — Graph compose + run_simulation orchestrator + artifact persistence

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-8
**Owner:** builder-agentic Opus 4.7
**State:** developing
**Started:** 2026-05-08

## Step 0 GATE — Skills Consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `sales-agent-expert` | Touching `tests/agentic_evals/sales_agent/simulator/` (test-infra production_code=false). | §3 protected surfaces NOT touched (closer_studio, SmartBufferService, OutputManager, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup). NO `from __future__ import annotations` in graph.py / runner.py per cement (T-4..T-7 invariant). Cost computation queries both `eval_simulator_llm_call` (customer) + `sales_agent_llm_call` (agent) by simulation_id jsonb tag — H6 cost bucket separation honored. |
| `copilot-expert` | LangGraph orchestration patterns (StateGraph compile + conditional edges + state graph mutation contract). | StateGraph(SimulationState).compile() — no checkpointer (test infra, single-shot per simulation). Nodes return PARTIAL state dict (NEVER mutate). Conditional edges always have exit (max-iter via `should_continue` calling `evaluate_termination` from T-4 registry + defense-in-depth `iterations >= max_turns + 5` cap). |
| `tessl__langgraph` | Graph node + state machine semantics. | Pydantic state OK (LangGraph 0.6 May 2026). Reducer `Annotated[list[ConversationTurn], operator.add]` already declared on `SimulationState.transcript` (T-4). `increment_turn` returns `{"current_turn": state.current_turn + 1, "iterations": state.iterations + 1}` partial. `should_continue` reads `state.is_finished` AND `evaluate_termination(state)` AND `iterations >= max_turns + 5`. Exit conditions: `END` when terminate. |
| `tessl__graceful-degradation` | Runner orchestrates fixture (DB) + graph (LLM) + observability (cost query). | Per-dependency error isolation: cost query failure should NOT break SimulationResult build (best-effort with default zero CostSummary + structlog warning). Artifact JSON write best-effort (mkdir -p + atomic write) with structlog warning on failure. Fixture invocation (DB seed) propagates errors — early entry-point validation prevents wasted work. |
| `tessl__pytest-api-testing` | Test patterns (factories + fixtures + parametrize + monkeypatch). | Factory fixtures for ActorProfile + minimal SimulationState. Use `pytest.mark.no_eval` (sibling of T-7 patterns) so tests run on default CI. monkeypatch the lazy-imports `agent_app` + `eval_tenant_seeded` + `_compute_cost_summary` for unit-level isolation. Don't hit real DB in unit tests. |

## Step 0.5 — Default flip detection

Reviewed `core/config.py` for flag defaults: T-8 does NOT touch any feature flag. NO default flip. Skip default-flip workflow.

## Step 0 — Anti-duplication grep

```bash
grep -rn "build_simulation_graph\|run_simulation" backend/tests/ backend/src/
```

Result: only references found in T-4 docstrings (`result.py:114`), T-7 docstrings (`agent_bridge.py:126`), public surface stub (`__init__.py:7,11,27,43`), T-7 test file docstring (`test_agent_bridge_unit.py:18`), T-6 docstring (`customer_node.py:19`). Zero implementation files exist before T-8 — clean primera vez.

Legacy reference at `client_simulator/src/simulator/graph.py` (D6 byte-equal preserved) — read for topology only, NOT copied (legacy uses TypedDict state + dict turns; T-8 uses Pydantic + ConversationTurn).

## Cross-module systems audit (NO-NEW-LAYER)

T-8 deliverables (`graph.py` + `runner.py`) live entirely under `tests/agentic_evals/sales_agent/simulator/_internal/`. Zero new layer in production code paths. Reuses:

- `SimulationState` from T-4 (`simulator/state.py`)
- `ActorProfile` from T-4 (`simulator/actor_profile.py`)
- `SimulationResult`, `ConversationTurn`, `CostSummary` from T-4 (`simulator/result.py`)
- `TerminationReason`, `AgentErrorSubtype`, `evaluate_termination`, `TERMINATION_POLICIES` from T-4 (`simulator/termination.py`)
- `customer_node` from T-6 (`_internal/customer_node.py`)
- `agent_bridge` from T-7 (`_internal/agent_bridge.py`)
- `seed_eval_tenant` from T-3 (`fixtures/tenant_seeded.py`) — SYNC API; runner wraps in `asyncio.to_thread` if needed
- `ARCHETYPE_SLUGS` from Story-A loader (`tests/fixtures/eval/tenants/loader.py`)
- `EvalSimulatorLlmCallModel` from T-1 (cost query)
- `SalesAgentLlmCallModel` from production (cost query agent side)
- LangGraph `StateGraph`, `END`

Cero layer nuevo. Cero mirror.

## Iteration log

### Iteration 1 — RED tests authored (target)

Plan:
1. Write `_internal/graph.py` (build_simulation_graph + increment_turn + should_continue route)
2. Write `_internal/runner.py` (run_simulation with 12 steps per ticket spec)
3. Write `test_runner_unit.py` with 5 tests:
   - `test_simulation_id_deterministic` (A2 — H2 idempotency)
   - `test_invalid_archetype_raises` (A3)
   - `test_artifact_persistence` (A4)
   - `test_max_turns_cap` (D5/H8)
   - `test_tenant_id_deterministic` (D2)
4. Anti-future-imports negative grep
5. Quality gates — ruff + format + mypy strict + pytest

### Iteration 2 — GREEN

All gates GREEN.

| Gate | Result | Detail |
|---|---|---|
| ruff check | PASS | All checks passed (after 3 fixes: 2 unused noqa PLC0415 → reword as comments; 1 RUF002 multiplication-sign in docstring → ASCII `x`) |
| ruff format --check | PASS | 3 files formatted automatically (docstring + line wraps) |
| mypy --strict (3 files) | PASS | 0 errors after 2 fixes: (a) `CompiledStateGraph` generic type-arg → typed return as `Any` with docstring justification; (b) `dict[str, Any]` annotation on heterogeneous defaults dict in `_state` factory; (c) extract AsyncMock to a typed local before assigning to MagicMock attr to satisfy no-any-return |
| pytest test_runner_unit.py | PASS | 17/17 native ticket tests |
| pytest full simulator suite | PASS | 139 passed + 5 skipped (DB-required tests skip cleanly without Postgres) |
| pytest tests/modules/sales_agent/observability/ | PASS | 36/36 — downstream regression check (no break in T-5 obs subclass) |
| pytest architecture smoke | PASS | 16/16 — `test_no_new_sales_agent_module_imports.py` + `test_copilot_anchors.py` + `test_schema_migrations_registry_complete.py` |
| Negative grep `from __future__ import annotations` | PASS | Both `graph.py` and `runner.py` clean — docstring/comment patterns reworded to "future-annotations import" / "``__future__`` / ``annotations``" so the verbatim 3-token sequence is absent |
| D6 preservation (`git diff --name-only -- client_simulator/`) | PASS | empty |

### Iteration 3 — Quality fixes summary

Reworded 2 docstring/comment blocks to break the literal `from __future__ import annotations` 3-token sequence:

- `_internal/graph.py`: docstring "LangGraph cement" section + module-top comment
- `_internal/runner.py`: module-top comment

Both files keep the cement message clearly readable; the verifier `! grep -q 'from __future__ import annotations'` now passes.

## Skills Consulted (final summary — captured upstream Step 0)

See "Step 0 GATE — Skills Consulted" table at top of this log. Five skills invoked + cited per ticket scope (sales-agent-expert, copilot-expert, tessl__langgraph, tessl__graceful-degradation, tessl__pytest-api-testing).

## Acceptance criteria mapping

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | Graph compiled w/o `from __future__ import annotations` | `! grep -q 'from __future__ import annotations' graph.py` + `test_no_future_annotations_import_in_graph_module` | **PASS** |
| A2 | run_simulation deterministic simulation_id | `pytest test_runner_unit.py::test_simulation_id_deterministic` | **PASS** |
| A3 | Invalid archetype_slug → ValueError w/ valid list | `pytest test_runner_unit.py::test_invalid_archetype_raises` | **PASS** |
| A4 | Artifact transcript.json written + populated correctly | `pytest test_runner_unit.py::test_artifact_persistence` | **PASS** |

Plus 13 ancillary tests:

- `test_max_turns_cap` (D5/H8 — registry MAX_TURNS termination)
- `test_tenant_id_deterministic` (D2 — UUID5 paridad with fixture)
- `test_initial_state_eval_metadata_complete` (H5 — 6 mandatory keys)
- `test_zero_cost_summary_when_no_db_session` (best-effort fallback)
- `test_eval_tenant_id_paridad_with_fixture` (cross-fixture cement)
- `test_simulation_id_uses_uuid5_with_full_tuple` (H2 idempotency)
- `TestGraphCompose` × 3 (compile + future-annotations cement on both files)
- `TestIncrementTurn` × 1 (partial dict shape)
- `TestShouldContinue` × 4 (4 exit conditions including hardcap)

## Files touched (T-8 scope only)

| File | Status | LOC after format |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/graph.py` | NEW | 174 |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` | NEW | 412 |
| `backend/tests/agentic_evals/sales_agent/simulator/test_runner_unit.py` | NEW | 530 |
| `docs/product/stories/eval-foundation-simulator-homologation/T-8-impl-log.md` | NEW | this file |
| `docs/product/stories/eval-foundation-simulator-homologation/T-8-result.md` | NEW (next) | TBD |
| `docs/product/stories/eval-foundation-simulator-homologation/06-tickets.yaml` | MODIFIED | T-8 transitions appended |

Cero `backend/src/` modificado, cero `client_simulator/` modificado, cero `frontend/` modificado, cero `.claude/rules/` modificado, cero T-1..T-7 deliverable modificado. T-8 stands alone in tests/agentic_evals/sales_agent/simulator/_internal/.

## Decisions (architectural fingerprints recorded)

1. **`build_simulation_graph() -> Any`** — LangGraph 0.6 `CompiledStateGraph` is a complex parametrized generic that mypy --strict refuses bare. Returning `Any` with a docstring documenting the runtime contract (`.ainvoke`, `.astream`) is the cleanest compromise. The legacy `client_simulator/graph.py` returns `StateGraph` directly which is bare-generic; we don't replicate that bug.

2. **`run_simulation` accepts `db_session` + `seed_fn` overrides** — the production call path (T-10 smoke) wires real DB session + the T-3 fixture. Unit tests bypass with `seed_fn=None` and `db_session=None`, falling back to zero-cost summary + best-effort artifact write to a tmp dir. Rationale: tests at the unit layer should not mock 5 layers of LangGraph + 2 LLM providers + DB session lifecycle. T-10 owns the integration tests.

3. **`_compute_cost_summary` queries by simulation_id (eval) AND time-window (sales_agent)** — H6 cost-bucket separation: customer LLM rows live in `eval_simulator_llm_call` with `eval_metadata->>'simulation_id'` jsonb tag (precise filter); production agent rows live in `sales_agent_llm_call` without that tag (filter by tenant_id + started_at >= simulation_started_at — looser but adequate for synthetic eval tenants where there's no production traffic). T-10 will refine if needed.

4. **`_resolve_termination` 3-tier resolution** — (1) honor explicit reason from prior nodes (T-7 agent_bridge sets AGENT_ERROR + error_subtype), (2) re-evaluate registry on final state (covers post-`increment_turn` MAX_TURNS), (3) fallback MAX_TURNS when neither triggers (graph exit due to current_turn cap reached). The fallback handles the case where the graph compiles cleanly but neither node nor predicate ran the registry's max_turns predicate (defense-in-depth).

5. **`SimulationState.model_validate` round-trip after `ainvoke`** — LangGraph 0.6 returns a dict-like or the BaseModel depending on internal config. We coerce uniformly via `model_validate` so downstream code can reach Pydantic field accessors. Performance impact negligible (<1ms per simulation; once per run).

6. **Artifact path computed via `__file__` parents** — `_BACKEND_ROOT = Path(__file__).resolve().parents[5]` anchors against the source layout, not CWD. Tests can monkey-patch `_ARTIFACTS_BASE` to redirect to `tmp_path`. Production callers get the canonical `_artifacts/` dir without configuration.

7. **`_validate_archetype_slug` raised BEFORE any work** — A3 cement: cero DB inserts, cero graph compile, cero state construction. Spy in test_invalid_archetype_raises asserts `build_simulation_graph` `call_count == 0`.


