# T-7 Result — Agent bridge in-process + leak_assertions defense-in-depth

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-7
**Owner:** builder-agentic Opus 4.7
**State:** tests-passing (validators GREEN, awaiting orchestrator → gate-runner → auditor-agentic for independent verdict per Conv 3)
**Date stamp:** 2026-05-08

## Summary

Shipped the in-process agent bridge LangGraph node + defense-in-depth
leak assertions for the eval-foundation simulator, honoring D1 (in-process
`agent_app.ainvoke` — NO HTTP webhook) + H7 (failure-mode taxonomy mapped to
`AgentErrorSubtype` enum) + H10 (frozen forbidden-leak-strings registry).
Both files live under `tests/agentic_evals/sales_agent/simulator/_internal/`
to honor the H9 public surface invariant (T-9 finalizes `__all__`).

- `_internal/leak_assertions.py` — frozen `FORBIDDEN_LEAK_STRINGS:
  frozenset[str]` of 6 spec values + `assert_no_leak(transcript_content:
  str) -> None` with case-insensitive substring scan, `structlog.warning`
  emission with breadcrumb (`simulator.system_prompt_leak_detected`),
  `AssertionError` raise on match. Public `__all__` exact 2 names.
- `_internal/agent_bridge.py` — async LangGraph node `agent_bridge(state:
  SimulationState) -> dict[str, Any]`. (1) Extract last customer turn or
  return `INVALID_STATE`. (2) Resolve session via internal helper
  (T-8 wires real resolver). (3) Lazy imports of production
  `agent_app` + `TenantKnowledgeBuilder` + `create_initial_state` (paridad
  with `outbound_orchestrator.py` + `fixtures/entrypoint.py`). (4) Build
  slot 4 (agent_identity) + slot 5 (brand_voice) verbatim via knowledge
  builder. (5) Compose initial state with `channel_type='eval_simulator'`.
  (6) Build `EvalSimulatorObservabilityContext` via T-5 factory. (7)
  In-process `await agent_app.ainvoke(initial_state, config=ctx.langchain_config())`
  inside `async with ctx.observe_turn(...)`. (8) Extract response text
  via `_extract_agent_text` (dual-shape — dict / AIMessage). (9) Apply
  `assert_no_leak` post-extract — defense-in-depth warning only (bridge
  swallows `AssertionError`; smoke tests T-10 own raise policy). (10)
  Append agent turn to transcript via `{"transcript": [agent_turn]}`
  reducer-friendly partial dict. (11) Failure-mode taxonomy: `TimeoutError`
  → `AgentErrorSubtype.TIMEOUT` + `simulator.agent_timeout`; empty response
  → `EMPTY_RESPONSE` + `simulator.agent_empty_response`; `httpx.HTTPStatusError`
  → `HTTP_ERROR` + `simulator.agent_http_error`; missing customer turn /
  session unavailable / generic `Exception` → `INVALID_STATE` +
  `simulator.agent_invalid_state`.
- 4 acceptance test classes + 11 ticket-level tests in `test_agent_bridge_unit.py`
  + 32 ticket-level tests in `test_leak_assertions_unit.py` = **43 total**
  ticket tests, 100% PASS.

Zero touch on protected surfaces (sales-agent §3, R5 schema-mirror exception
NA — T-7 lives entirely under `tests/`). Zero mirror of any shared
abstraction. Step 0 anti-duplication grep evidence captured in IMPL-LOG.md.

## Acceptance criteria

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | Agent bridge invokes `agent_app.ainvoke` in-process (NO HTTP) | `pytest test_agent_bridge_unit.py::TestInProcessInvocation::test_in_process_invocation` | **PASS** |
| A2 | Failure modes mapped to `AgentErrorSubtype` + structlog | `pytest test_agent_bridge_unit.py::TestFailureModesTaxonomy::test_failure_modes_taxonomy` | **PASS** (4 sub-cases inline) |
| A3 | Defense-in-depth `assert_no_leak` triggers warning on match | `pytest test_leak_assertions_unit.py` | **PASS** (32 tests) |

A1 verifier asserts both:
- `agent_app.ainvoke` was awaited exactly once per turn (mock spy on the
  patched module symbol).
- `httpx.AsyncClient.__init__` was NEVER called during the bridge invocation
  (defense against regression to the legacy webhook path —
  `client_simulator/agent_bridge.py` did use httpx; D1 spec replaces).

A2 verifier exercises 4 failure modes inline within a single test method
(per the spec's literal verifier path `test_failure_modes_taxonomy`):
TIMEOUT / EMPTY_RESPONSE / HTTP_ERROR / INVALID_STATE. Each sub-case
asserts on the returned partial dict shape (`is_finished=True`,
`termination_reason=TerminationReason.AGENT_ERROR`, `error_subtype` ==
expected enum value) AND on the captured structlog warning event name
(`simulator.agent_*`). Plus a separate test
`test_no_last_customer_turn_raises_invalid_state` confirms the bridge
short-circuits BEFORE invoking `agent_app.ainvoke` when the state's
transcript has no customer turn (the await_count == 0 assertion is
defensive — INVALID_STATE is the cleanest fail-fast path).

A3 verifier covers the entire `test_leak_assertions_unit.py` file (32
tests across 5 acceptance classes + 6 module-level tests):
`TestForbiddenStringsRegistry` (frozenset cement + 6-value count),
`TestAssertNoLeakPass` (clean transcripts), `TestAssertNoLeakFail` (each
forbidden token parametrized + multi-token), `TestAssertNoLeakCaseInsensitive`
(9 casing variants), `TestAssertNoLeakStructlogWarning` (event name
emission + breadcrumb content), `TestAssertNoLeakEdgeCases` (Unicode
NFC, special chars, return type contract), public-surface freeze
(`__all__` exact 2 names), signature spec match.

## Validator gates output

| Validator | Status | Notes |
|---|---|---|
| `be_lint` | PASS | 0 errors after fixes (RUF002 ×3, N802, SIM300, UP041, RET501, SIM105, PYI034/036, PLR0911 with H7-cement noqa) |
| `be_format` | PASS | 4/4 files clean after `ruff format` |
| `be_mypy_strict` | PASS | 0 errors after 3 manual fixes (untyped result-of-None usage, dict[str, object] type args, `cast(RunnableConfig, ...)` for langchain_config bridge) |
| Native ticket tests | PASS | 43/43 in `test_agent_bridge_unit.py` + `test_leak_assertions_unit.py` |
| Full simulator suite | PASS | 122/122 (5 skipped — DB-required tests; no regression on T-4/T-5/T-6 deliverables) |
| Sales agent observability suite | PASS | 36/36 — downstream regression check, no break |
| Architecture fitness smoke | PASS | 16/16 — no_new_sales_agent_module_imports + copilot_anchors + schema_migrations_registry_complete |

The validator gates `scenario_adversarial_no_prompt_leak` +
`scenario_adversarial_agent_error_graceful` reference smoke tests in
`test_simulator_smoke.py` (T-10 deliverable) — those validators cannot
fire until T-10 ships the smoke fixture. Their preconditions (the
`assert_no_leak` helper + `agent_bridge` H7 taxonomy + structlog event
names) are now in place.

## Diff resumen

4 NEW files, ~1140 LOC total after format:

```
backend/tests/agentic_evals/sales_agent/simulator/
├── _internal/
│   ├── leak_assertions.py                  (NEW, ~190 LOC)
│   └── agent_bridge.py                     (NEW, ~430 LOC)
├── test_leak_assertions_unit.py            (NEW, ~310 LOC)
└── test_agent_bridge_unit.py               (NEW, ~660 LOC)
```

Plus: `06-tickets.yaml` T-7 entry transitions appended (`state:
tests-passing`, `assigned_to: claude-opus`); `T-7-impl-log.md` written;
this `T-7-result.md`.

## Hardening invariants honored

| H | Invariant | Where enforced in T-7 |
|---|---|---|
| H1 | Schema versioning forward-compat | NA T-7 (T-4 owns; T-9 frozen golden). |
| H2 | Idempotency UUID5 | NA T-7 (T-8 runner derives). |
| H3 | Async-first concurrency-safe | `agent_bridge` is `async def`, returns partial state dict (NEVER mutates). State propagation via LangGraph reducer (`Annotated[list[ConversationTurn], operator.add]`). |
| H4 | Rate-limiting customer LLM | NA T-7 (T-6 owns customer-side semaphore; agent_bridge has dependency isolation per `tessl__graceful-degradation` Rule 5 — agent failure does not block customer or vice versa). |
| H5 | Observability eval-vs-prod tags | The T-5 factory `build_eval_simulator_observability_context` is invoked with the 6 mandatory keys propagated from `state` (tenant_id, simulation_id, run_id, archetype_slug, actor_profile_id, trial_n). Test `test_eval_metadata_injected_into_observability_factory` enforces this. |
| H6 | Cost bucket separation | The T-5 factory wires `EvalSimulatorCallbackHandler` (subclass override injects `channel_type='eval_simulator'`) — agent's LLM rows persist to `eval_simulator_llm_call`, NOT `sales_agent_llm_call`. Defense via subclass override at the T-5 layer; T-7 just consumes the factory. |
| **H7** | **Failure-mode taxonomy** | **PRIMARY T-7 deliverable.** 4 failure modes mapped 1:1 to `AgentErrorSubtype` enum from T-4 (TIMEOUT / EMPTY_RESPONSE / HTTP_ERROR / INVALID_STATE). Each except branch emits a canonical `structlog.warning` event (`simulator.agent_timeout` / `simulator.agent_empty_response` / `simulator.agent_http_error` / `simulator.agent_invalid_state`). `_build_terminal_dict(error_subtype)` centralizes the partial dict shape. |
| H8 | Termination policy registry | The 4 failure modes return `termination_reason=TerminationReason.AGENT_ERROR`, picked up by `_agent_error_predicate` in T-4's `TERMINATION_POLICIES` registry. |
| H9 | Public API surface minimal | Both files live under `_internal/`, NOT re-exported from `simulator/__init__.py`. `leak_assertions.__all__` is exact 2 names; `agent_bridge.__all__` is exact 1 name. T-9 finalizes the 7-name top-level `__all__`. |
| **H10** | **Defense-in-depth FORBIDDEN_LEAK_STRINGS** | **PRIMARY T-7 deliverable.** Frozen `frozenset[str]` of 6 verbatim spec values (`compiler v2`, `system_instruction`, `BRAND_VOICE`, `slot 5`, `ASÍ HABLAS`, `ASÍ NO`). Case-insensitive substring scan. Match → `structlog.warning("simulator.system_prompt_leak_detected")` with `matched_tokens` + `token_count` + `transcript_length` breadcrumbs, then `AssertionError`. The bridge applies the helper post-extract with `contextlib.suppress(AssertionError)` — warning is the actionable signal; smoke tests T-10 own raise policy. |

## Decisions (architectural fingerprints recorded)

1. **`assert_no_leak` raises by default** — even though the bridge swallows
   the AssertionError, the helper itself raises so smoke tests (T-10) get
   the loud-fail behavior. Bridge-level swallow is `contextlib.suppress`
   (ruff SIM105 compliant) — communicates intent (we know about the
   exception, we choose to ignore it for transcript continuity).

2. **`PLR0911 noqa` on `agent_bridge`** — the function has 9 explicit
   returns (4 H7 failure modes × 2 except + 2 INVALID_STATE early-return
   + 1 success). Refactoring to a single return would conflate the
   per-failure structlog event names; the H7 cement requires a unique
   structlog event AND a unique `error_subtype` enum value per failure
   mode. The noqa carries justification verbatim in the source.

3. **`_resolve_session_for_simulation` stub for T-7** — returns `None` by
   default (triggers INVALID_STATE termination). T-8 runner replaces with
   contextvar/thread-local read at simulation entry. Unit tests
   monkeypatch the helper directly. Documented in the helper docstring.

4. **`_extract_agent_text` dual-shape** — paridad with `outbound_orchestrator.py`
   + `chat.py` heuristics: agent_app may return `{"messages": [{"role":
   ..., "content": ...}]}` (dict-shape) OR `{"messages": [AIMessage(...)]}`
   (langchain object). The helper accepts both. Empty/missing message →
   empty string → caller maps to EMPTY_RESPONSE termination.

5. **`cast(RunnableConfig, obs_ctx.langchain_config())`** — the shared
   `BaseObservabilityContext.langchain_config()` returns `dict[str, Any]`
   (untyped legacy contract). LangGraph 0.2+'s `Pregel.ainvoke` expects
   `RunnableConfig | None` (TypedDict alias). `typing.cast` satisfies mypy
   strict without runtime overhead. The production
   `outbound_orchestrator.py` has the same line untyped; mypy strict is
   only enabled at the file level here.

6. **`config=None` in fallback path (instead of `config={}`)** — when the
   obs factory returns None, the bridge passes `config=None` to ainvoke.
   Empty dict was rejected by mypy strict (no overload variant matched).
   None is the canonical "no config" sentinel per the LangGraph protocol.

7. **`from typing import Self` for fake context manager type hint** — the
   test file's fake `FakeObserveTurnCM.__aenter__` annotates return as
   `Self` (PEP 673) per ruff PYI034. Python 3.11+ requirement met (per
   `pyproject.toml [tool.ruff.target-version]`).

8. **AST-based `from __future__` cement check** — the test
   `test_no_future_annotations_import` was originally a string-search
   that tripped on the docstring quoting the canonical pattern. Refactored
   to an AST walk so docstrings/comments mentioning the pattern do not
   trip the gate; only a real `ImportFrom('__future__', ['annotations'])`
   does.

## Files NOT touched (verification)

- `client_simulator/src/simulator/*.py` — D6 preservation gate PASS (`git diff HEAD` empty)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording,observability/persistence}/` — unchanged
- `backend/src/modules/sales_agent/observability/eval_simulator/` — T-1 owns; left intact
- `backend/src/shared/agent_observability/{recording,cost,channels,persistence,pricing}/` — read-only (consumed via factory + REUSE)
- `backend/src/core/config.py` — no flag flips (Step 0.5 NA)
- All `.claude/rules/*` — unchanged
- T-4 deliverables (`state.py`, `actor_profile.py`, `result.py`, `termination.py`, `_internal/schema_migrations.py`) — read-only
- T-5 deliverables (`_internal/observability.py`) — read-only
- T-6 deliverables (`_internal/{customer_node,customer_persona_prompt,llm_roles,concurrency}.py`) — read-only
- All §3 sales-agent protected surfaces — UNTOUCHED

## Native commands record

```bash
# Lint + format clean
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check \
    tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py \
    tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py \
    tests/agentic_evals/sales_agent/simulator/test_leak_assertions_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_agent_bridge_unit.py --no-cache
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check \
    tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py \
    tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py \
    tests/agentic_evals/sales_agent/simulator/test_leak_assertions_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_agent_bridge_unit.py

# Mypy strict file-level
cd /home/chris/AISALESHT/backend && .venv/bin/mypy --strict --explicit-package-bases \
    tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py \
    tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py \
    tests/agentic_evals/sales_agent/simulator/test_leak_assertions_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_agent_bridge_unit.py \
    --ignore-missing-imports

# Native ticket tests
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/test_leak_assertions_unit.py \
    tests/agentic_evals/sales_agent/simulator/test_agent_bridge_unit.py -v --tb=short

# Full simulator suite (no regression)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/ -v --tb=short

# Cross-module smoke (downstream regression — sales_agent observability)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/modules/sales_agent/observability/ -q

# Architecture fitness smoke
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/architecture/test_no_new_sales_agent_module_imports.py \
    tests/architecture/test_copilot_anchors.py \
    tests/architecture/test_schema_migrations_registry_complete.py \
    -v --tb=short --override-ini="addopts="

# Anti-mirror grep (Step 0 evidence)
grep -rn "agent_bridge\|FORBIDDEN_LEAK_STRINGS\|assert_no_leak" \
    /home/chris/AISALESHT/backend/ 2>/dev/null | grep -v __pycache__
# → Only references found in T-4/T-5/T-6 docstrings + termination.py + observability.py
#   factory comment. Zero implementation files exist before T-7 — clean primera vez.

# D6 preservation gate
git diff HEAD --name-only -- client_simulator/src/simulator/  # → empty
```

## Commit SHA

To be filled by the next commit step.

## Next builders

T-8 (graph compose + run_simulation orchestrator) consumes:
- `agent_bridge` from `_internal/agent_bridge.py` — wired into the
  LangGraph topology between `customer_node` (T-6) and `increment_turn`
  (T-8) per 03-arch-agentic § 2 topology summary.
- `_resolve_session_for_simulation` — T-8 runner replaces the stub with
  a contextvar/thread-local read at simulation entry.
- `assert_no_leak` from `_internal/leak_assertions.py` — directly
  consumable by T-10 adversarial smoke tests with raise enabled.

T-9 (public API + frozen golden + arch gates) — confirms `leak_assertions`
+ `agent_bridge` stay UNDER `_internal/` (NOT in the 7-name public
`__all__`). Arch fitness gate `test_simulator_public_api_surface.py`
will probe this.

T-10 (smoke parametrized 5×archetype + adversarial + R3 rule update) —
the `scenario_adversarial_no_prompt_leak` + `scenario_adversarial_agent_error_graceful`
validators reference `test_simulator_smoke.py` which calls `assert_no_leak`
directly with raise enabled, and validates the H7 taxonomy structlog
events end-to-end against a real (or simulated) jailbreak transcript.

## Audit readiness

T-7 deliverables align literal with `06-tickets.yaml` line items:

- `_internal/leak_assertions.py` ships `FORBIDDEN_LEAK_STRINGS:
  frozenset[str]` with 6 verbatim spec values
- Same file ships `assert_no_leak(transcript_content: str) -> None`
  function — case-insensitive substring scan, raises AssertionError on
  match, structlog warning `simulator.system_prompt_leak_detected`
  emitted on match (always, with breadcrumbs)
- `_internal/agent_bridge.py` ships async LangGraph node `agent_bridge`
- (1) Extracts last customer turn from `state.transcript`
- (2) Builds initial_state via `ConversationPipeline` helpers (`build_identity`
  + `build_brand_voice` via `TenantKnowledgeBuilder`; `create_initial_state`
  via the production state factory) — REUSED verbatim, paridad with
  `fixtures/entrypoint.py`
- (3) Wires `EvalSimulatorObservabilityContext` (T-5) via factory
- (4) Calls `await agent_app.ainvoke(initial_state, config=...)` in-process
- (5) Extracts response text via `_extract_agent_text` dual-shape helper
- (6) Applies `assert_no_leak` defense-in-depth (warning only, no raise)
- (7) Appends agent turn to state.transcript via partial state dict
- (8) Failure modes mapped 1:1 to `AgentErrorSubtype`:
  - `TimeoutError` → `TIMEOUT` + `simulator.agent_timeout`
  - empty response → `EMPTY_RESPONSE` + `simulator.agent_empty_response`
  - `httpx.HTTPStatusError` → `HTTP_ERROR` + `simulator.agent_http_error`
  - missing customer turn / session unavailable / generic Exception →
    `INVALID_STATE` + `simulator.agent_invalid_state`
- 4 acceptance test classes + 11 ticket-level tests in
  `test_agent_bridge_unit.py` + 32 ticket-level tests in
  `test_leak_assertions_unit.py` = **43 total ticket tests, 43/43 PASS**

Verdict for orchestrator: T-7 ready for gate-runner pickup →
auditor-agentic independent review.
