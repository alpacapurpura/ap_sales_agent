# T-5 Result — `EvalSimulator{ObservabilityContext, CallbackHandler}` subclasses

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-5
**Owner:** builder-agentic Opus 4.7
**State:** developed (validators GREEN, awaiting `/auditor` independent verdict per Conv 3)
**Date stamp:** 2026-05-07

## Summary

Shipped the eval-simulator observability subclasses honoring anti-duplication §0
verbatim — both new classes inherit from `shared/agent_observability/` base and
override only the abstract Template Method hooks they own:

- `EvalSimulatorObservabilityContext(BaseObservabilityContext)` — overrides 3
  abstract hooks (`_add_trace_event`, `_aggregate_totals`,
  `_legacy_compat_keys_or_empty`) + adds `start(...)` factory + private
  `_most_used_model(...)` helper. Inherits the entire turn lifecycle
  (`observe_turn`, `_write_turn_*`, `set_turn_*`, `langchain_config`,
  `_commit_session`) verbatim.
- `EvalSimulatorCallbackHandler(BaseAgentCallbackHandler)` — overrides 2
  abstract persisters (`_persist_llm_call_row`, `_persist_trace_event_row`).
  Inherits the 8 LangChain callbacks (`on_chat_model_start`, `on_llm_end`,
  `on_llm_error`, `on_tool_start`, `on_tool_end`, `on_tool_error`,
  `on_chain_start`, `on_chain_end`) + `_persist_llm_call` Template Method
  skeleton (sanitize → resolve pricing → calculate cost → persist) verbatim.
- Two test-infra repos (`EvalSimulatorLlmCallRepository` +
  `EvalSimulatorTraceEventRepository`) co-located in the same file, kept
  under `_internal/` so they do not pollute the H9 public surface.
- `build_eval_metadata(...)` helper SSoT for the H5 mandatory dict — 6 keys
  (`eval_run_kind="simulator"`, `archetype_slug`, `actor_profile_id`,
  `trial_n`, `simulation_id`, `run_id`).
- `_assert_eval_metadata_complete(...)` defense-in-depth validator triggered
  at 3 layers (helper output, callback `__post_init__`, repo `add` defense).
- `build_eval_simulator_observability_context(...)` factory paridad
  sales_agent — best-effort: returns `None` on construction failure rather
  than raising, with structured `structlog.warning` breadcrumb.

Zero touch on protected surfaces (sales-agent §3, R5 schema-mirror exception
NA — T-5 lives entirely under `tests/`). Zero mirror of any shared
abstraction. Step 0 anti-duplication grep evidence captured in commit body.

## Acceptance criteria

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | `EvalSimulator{ObservabilityContext, CallbackHandler}` inherit from shared base, no mirror | `python -c "from ..._internal.observability import ...; assert issubclass(...)"` + `pytest test_observability_resilience.py::TestSubclassInheritance` (4 tests) | **PASS** |
| A2 | Mandatory H5 metadata fields enforced per row written | `pytest test_observability_resilience.py::TestMandatoryEvalMetadata` (5 tests) | **PASS** |
| A3 | Best-effort writes — failure during persist NO breaks simulation | `pytest test_observability_resilience.py::TestPersistFailureResilience::test_persist_failure_logs_warning_no_raise` (+ 3 supporting tests) | **PASS** |

A1's full arch fitness gate (`test_simulator_no_mirrors_shared.py`) is a T-9
deliverable. The A1 verifier here is the inline `issubclass(...)` smoke check
spelled out in the prompt + the 4 inheritance tests in this ticket's own
test module.

## Validator gates output

| Validator | Status | Notes |
|---|---|---|
| `be_lint` | PASS | 0 errors after 1-pass autofix (8 RUF100/FURB157 cleared) |
| `be_format` | PASS | 2/2 files clean after `ruff format` |
| `be_mypy_strict` | PASS | 0 errors after 1 manual fix (`tenant_currency = str(billing_cfg.billing_currency)`) |
| Native ticket tests | PASS | 13/13 in `test_observability_resilience.py` |
| Full simulator suite | PASS | 59/59 (no regression on T-4 deliverables) |
| `tests/modules/sales_agent/observability/` | PASS | 224/224 — downstream regression check, no break |
| `tests/shared/agent_observability/` | PASS | included above |
| Architecture fitness suite | PASS | 881/881 (no new violations introduced) |

The validator gates `agentic_no_mirrors_shared`, `agentic_eval_kind_tag_enforced`,
`agentic_observability_invariants` (named in the ticket's `quality_gates`
block) are NEW arch fitness tests that will be created by T-2 + T-9 — they
are not yet present in the suite, so they neither pass nor fail in this
ticket's run. Their preconditions (the subclass code that those gates
probe) are now in place.

## Diff resumen

2 NEW files, ~890 LOC total after format:

```
backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py       (NEW, ~414 LOC)
backend/tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py (NEW, ~470 LOC)
```

Plus: `06-tickets.yaml` T-5 entry transitions appended; `checkpoint.md` state +
bitácora updated; `T-5-impl-log.md` written.

## Hardening invariants honored

| H | Invariant | Where enforced in T-5 |
|---|---|---|
| H1 | Schema versioning forward-compat | NA T-5 (T-4 + T-9 own this). T-5 does not introduce new schema-bumped types. |
| H2 | Idempotency UUID5 | NA T-5 (runner T-8 owns derivation). T-5 only consumes the IDs through `eval_metadata` propagation. |
| H3 | Async-first concurrency-safe | NA T-5 — observability subclass is sync (matches `Session` orchestrator pattern). The async story belongs to T-8 graph compose. |
| H4 | Rate-limiting customer LLM | NA T-5 (T-6 ships concurrency.py). |
| **H5** | **Observability eval-vs-prod tags** | **PRIMARY T-5 deliverable.** `_MANDATORY_EVAL_METADATA_KEYS` frozenset + `build_eval_metadata(...)` SSoT helper + `_assert_eval_metadata_complete(...)` defense-in-depth at 3 layers (helper/`__post_init__`/repo). 6 mandatory keys verified per row written. |
| **H6** | **Cost bucket separation** | **PRIMARY T-5 deliverable.** Subclass overrides inject `channel_type='eval_simulator'` + `lead_id=None` + `eval_metadata` jsonb on every persisted row. `_aggregate_totals(...)` queries `EvalSimulatorLlmCallModel` (NOT `SalesAgentLlmCallModel`) — physical-table separation H6 enforced at runtime. |
| H7 | Failure-mode taxonomy | T-5 honors via best-effort wrapping (try/except + structlog.warning) — `agent_bridge` (T-7) maps to `AgentErrorSubtype` enum. |
| H8 | Termination policy registry | NA T-5 (T-4 owns the registry; T-8 wires `should_continue`). |
| H9 | Public API surface minimal | T-5 keeps `EvalSimulatorLlmCallRepository` + `EvalSimulatorTraceEventRepository` + `EvalSimulatorObservabilityContext` + `EvalSimulatorCallbackHandler` + `build_*` helpers under `_internal/observability.py` — none re-exported from `simulator/__init__.py`. T-9 will finalize the 7-name public `__all__`. |
| H10 | Frozen golden v1 fixture | NA T-5 (T-9 ships YAML fixture + regression test). |

## Decisions (architectural fingerprints recorded)

1. **Repos co-located in `_internal/observability.py`** — rather than a separate
   `eval_simulator/persistence/llm_call_repository.py` BE-side mirror of the
   sales_agent layout. Two reasons: (a) T-5 prompt strict file scope
   (`<files_in_scope_strict>`) lists only `_internal/observability.py` +
   `test_observability_resilience.py`; (b) repos here are test-infra glue
   binding T-1's mirror models to the H5 invariant — they have no other
   consumer outside the simulator harness. If a future story (e.g. Story H
   billing cap) introduces production code that needs to read
   `eval_simulator_llm_call`, the repos LIFT-TO-SHARED move would be a
   one-commit refactor — anti-duplication §0 cardinal honored.

2. **`__post_init__` H5 validation** at construction time — rather than only
   per-row at persist time. Catches missing keys with a single loud failure
   during turn setup vs N silent dropped rows during the LangGraph stream.
   Per-row defense-in-depth still applies in `EvalSimulatorTraceEventRepository.add`
   (callback row payloads land here through the inherited Template Method
   skeleton).

3. **`monkeypatch.setattr(obs_mod.logger, "warning", ...)`** in the headline
   A3 test — instead of `caplog`. Discovery: structlog's default
   `ConsoleRenderer` pipeline emits to stdout via a path that bypasses the
   stdlib `logging` root that `caplog` hooks. First test run had visible
   stdout warning but empty `caplog.records`. Pattern matches existing
   `backend/tests/modules/sales_agent/observability/test_callback_handler.py`
   approach.

4. **`tenant_currency = str(billing_cfg.billing_currency) if billing_cfg else "USD"`**
   in factory — paridad sales_agent factory has same line typed loose
   (`Column[str] | str` returned). With `mypy --strict` enabled at the file
   level here, the explicit `str(...)` wrapper is required. No semantic
   change — `billing_currency` is always a `str` at runtime.

5. **NO `from __future__ import annotations`** in `observability.py` — keeps
   parity with the rest of the simulator tree (`state.py`, `actor_profile.py`,
   `result.py`, `termination.py`) per the story-wide cement T-4 imposed.
   The dataclass field `pricing_resolver: PricingResolver` works at runtime
   without forward-stringification because the class is imported at module
   top.

## Files NOT touched (verification)

- `client_simulator/src/simulator/*.py` — D6 preservation gate PASS (no edits)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording,observability/persistence}/` — unchanged
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/*.py` — T-1 owns these; left intact
- `backend/src/modules/sales_agent/observability/eval_simulator/spec.py` — T-1 owns; left intact
- `backend/src/shared/infrastructure/agent_observability_bootstrap.py` — T-1 already wired
- `backend/src/shared/agent_observability/{recording,cost,channels,persistence,pricing}/` — read-only (consumed via subclass + REUSE)
- `backend/src/core/config.py` — no flag flips (Step 0.5 NA)
- All `.claude/rules/*` — unchanged
- T-4 deliverables (`state.py`, `actor_profile.py`, `result.py`, `termination.py`, `_internal/schema_migrations.py`) — read-only
- All §3 sales-agent protected surfaces — UNTOUCHED

## Native commands record

```bash
# Lint clean
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check \
    tests/agentic_evals/sales_agent/simulator/_internal/observability.py \
    tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py --no-cache

# Format clean
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check \
    tests/agentic_evals/sales_agent/simulator/_internal/observability.py \
    tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py

# Mypy strict file-level
cd /home/chris/AISALESHT/backend && .venv/bin/mypy --strict \
    tests/agentic_evals/sales_agent/simulator/_internal/observability.py \
    tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py

# A1 inline verifier (per prompt acceptance spec)
cd /home/chris/AISALESHT/backend && .venv/bin/python -c "
from tests.agentic_evals.sales_agent.simulator._internal.observability import (
    EvalSimulatorObservabilityContext,
    EvalSimulatorCallbackHandler,
)
from src.shared.agent_observability.recording.turn_envelope import BaseObservabilityContext
from src.shared.agent_observability.recording.base_callback_handler import BaseAgentCallbackHandler
assert issubclass(EvalSimulatorObservabilityContext, BaseObservabilityContext)
assert issubclass(EvalSimulatorCallbackHandler, BaseAgentCallbackHandler)
print('A1 verifier: PASS')
"

# Native ticket tests
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/agentic_evals/sales_agent/simulator/test_observability_resilience.py -v --tb=short

# Full simulator suite (no regression)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ -v --tb=short

# Cross-module smoke (downstream regression — sales_agent observability + shared)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
    tests/modules/sales_agent/observability/ tests/shared/agent_observability/ -q

# Architecture fitness suite (no regression)
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/ -q --timeout=120

# Anti-mirror grep (Step 0 evidence)
grep -rn "class EvalSimulator" /home/chris/AISALESHT/backend/ --include="*.py" | grep -v __pycache__

# D6 preservation gate
git diff HEAD --name-only -- client_simulator/src/simulator/  # → empty
```

## Commit SHA

`14c354f1` — pushed to `origin/development` 2026-05-07. Files staged by
exact name per parallel-safety M5/M7. Pre-commit hook native enforced (no
`--no-verify`).

## Next builders

T-6 (customer node + prompt v1 + llm_roles + concurrency) consumes:
`EvalSimulatorCallbackHandler` + `build_eval_metadata` from T-5. Customer
LLM dispatch wires the callback via `LLMFactory.get_service(...).get_client(...,
config={"callbacks": [eval_handler]})`. The eval_metadata dict is propagated
in `state.eval_metadata` (T-4) and read at handler construction time.

T-7 (agent_bridge in-process + leak_assertions) consumes:
`build_eval_simulator_observability_context(...)` factory + the inherited
`async with ctx.observe_turn(...)` lifecycle. Failure-mode mapping wires the
inherited `set_turn_error(...)` to `AgentErrorSubtype` enum (T-4).

T-8 (graph compose + run_simulation) — does not consume T-5 directly; the
LangGraph compiled graph receives the callback handler via the
`agent_bridge` node which was built atop T-5 + T-7.

T-9 (public API + frozen golden + arch gates) — finalizes
`simulator/__init__.py::__all__` to exact 7 names + ships
`test_simulator_no_mirrors_shared.py` arch fitness gate that AST-scans
`simulator/**.py` basenames vs `shared/agent_observability/**.py` basenames
to enforce the cero-mirror invariant T-5 honors.

## Audit readiness

T-5 deliverables align literal with `06-tickets.yaml` line items:

- ✅ `_internal/observability.py` ships `EvalSimulatorObservabilityContext(BaseObservabilityContext)` subclass
- ✅ Same file ships `EvalSimulatorCallbackHandler(BaseAgentCallbackHandler)` subclass
- ✅ Override scope: only `_persist_llm_call_row` + `_persist_trace_event_row` (Template Method) on the callback handler
- ✅ Override scope: only `_add_trace_event` + `_aggregate_totals` + `_legacy_compat_keys_or_empty` (3 abstract hooks) on the context, plus required `start(...)` factory + private `_most_used_model(...)` helper
- ✅ Mandatory H5 metadata jsonb fields enforced en EACH write — defense at 3 levels
- ✅ `sanitize_payload(...)` reused (heredado del shared base via `_write_turn_*` outer wrappers + `_persist_llm_call` skeleton — NOT re-implemented locally)
- ✅ Best-effort writes — try/except + structlog.warning on every persist path
- ✅ Cero mirror — Step 0 grep evidence in commit body + IMPL-LOG cross-module audit section

Verdict for orchestrator: T-5 ready for gate-runner pickup → auditor-agentic
independent review.
