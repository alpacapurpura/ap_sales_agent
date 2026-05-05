<!-- voseo-allowed: documents Spanish-neutro CLEANUP of voseo terms (citation only — not user-facing) -->
# T-3 Impl Log — sales-agent-eval-runner-foundation

> **State:** tests-passing (awaiting auditor-agentic verdict)
> **Builder:** Claude Opus 4.7 (1M context) — agentic surface, mandatory per CLAUDE.md
> **Date:** 2026-05-05
> **Surface:** AGENTIC (composition-only consumer of `modules/sales_agent/`)

## Summary

T-3 delivers the LangChain `BaseCallbackHandler`-based `TrajectorySpy`,
the artifacts writer, and the conftest fixture composition that wires
the spy alongside the production callback handler in
`RunnableConfig.callbacks`. Anti-duplication §0 absolute rule is
honored — composition over subclass; `sanitize_payload` reused from
shared canonical; zero new mirror.

WARN cleanup folded into Step 0 per Chris choice (a) — only line 158
of `fixtures/tenant.py` (`Configurá voz...guardá`) was still voseo;
prior cleanup of lines 70/101/127/133 already lives in the repo
state.

## Step 0 — Skills Consulted (mandatory)

Per CLAUDE.md hard rule (agentic ticket → Opus + skill preload). Skills
loaded via the command-message preamble of this builder spawn.

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Trajectory spy adds best-effort observability; reuse pattern | **Best-effort wrapping** in every callback method body (try/except + structlog warning). PII via `sanitize_payload` from shared canonical (not mirror). Anti-duplication §0 cardinal: ZERO mirror in `runner/` of `BaseAgentCallbackHandler` — composition via `RunnableConfig.callbacks` list. |
| `sales-agent-expert` | Eval harness consumer of `modules/sales_agent/` (read-only) | **§3 NO se toca:** zero changes to `closer_studio.py`, `BufferService`, `OutputManager` chunking, `enrollment_*`, webhook adapters, `follow_up_engine`, `tool_call_dedup`, `PromptVersionModel`, `model_pricing_snapshot`. Verified by diff. **§0 anti-duplication:** spy is composition-only. Confirmed shared inventory: `BaseAgentCallbackHandler`, `sanitize_payload`, `SalesAgentObservabilityContext` REUSED verbatim. |
| `tessl__langgraph` | LangGraph state machine + supervisor pattern + callback semantics | **Supervisor pattern** classification per arch-agentic § "Topology classification". Spy reads `state["next_node"]` at `on_chain_end` (canonical SSoT for routing post-redesign 2026-04). Cohabits with native callback handler — LangChain executes callbacks in list order. |
| `tessl__graceful-degradation` | Spy callbacks must never break `agent_app.ainvoke` | **Rule 6** — every callback method body wraps logic in `try/except` + `structlog.warning`. Defensive non-dict payloads (e.g., `outputs="not-a-dict"`) handled without raising. Verified via `test_trajectory_spy_callbacks_are_best_effort` meta-test. |
| `tessl__pytest-api-testing` | New no_eval meta-tests + monkeypatch redirect of `_ARTIFACTS_ROOT` | **Function-scoped fixtures** + **monkeypatch** for redirecting `_ARTIFACTS_ROOT` so meta-tests don't pollute the real `_artifacts/` dir. Factory-style ownership: writer accepts spy + response_text + assertions_results; tests drive injection. |
| `tessl__fastapi` | N/A — T-3 surfaces no FastAPI route | Not invoked: zero API change. |

## Cross-module audit (NO-NEW-LAYER rule)

Per `.claude/rules/anti-duplication.md` § Inventario shared abstractions:

| Surface T-3 touches | Existing path | Action | Verified |
|---|---|---|---|
| Callback handler base class | `langchain_core.callbacks.BaseCallbackHandler` (LangChain native) | **EXTEND via composition** (subclass for spy contract; spy lives in `tests/`, not `src/`) | ✅ |
| Production sales_agent handler | `modules/sales_agent/observability/recording/callback_handler.py::SalesAgentCallbackHandler` | **REUSE verbatim** via `build_sales_agent_observability_context` factory | ✅ |
| Observability context factory | `modules/sales_agent/observability/recording/factory.py::build_sales_agent_observability_context` | **REUSE verbatim** in fixture (no rebuild) | ✅ |
| PII sanitization | `shared/agent_observability/recording/sanitization.py::sanitize_payload` | **REUSE verbatim** in `runner/artifacts.py` (single import + call) | ✅ |
| Turn envelope (observability ctx) | `shared/agent_observability/recording/turn_envelope.py::SalesAgentObservabilityContext` | **REUSE verbatim** via factory | ✅ |
| FX resolver | `shared/agent_observability/cost/fx_resolver.py::FXResolver` | Not touched (production handler owns it) | ✅ |
| Pricing resolver | `shared/agent_observability/cost/calculator.py` | Not touched | ✅ |
| Channel format registry | `shared/agent_observability/channels/format_for_channel.py` | Not touched (T-2 already registered `eval_harness` channel) | ✅ |

**Decision: ZERO NEW LAYER introduced.** Spy + writer live in
`tests/agentic_evals/`, not in `src/`. Both extend canonical shared
abstractions (LangChain native parent class for spy; shared
`sanitize_payload` for writer).

## Decisions honored (from arch-agentic.md)

| Architect decision | Implementation evidence |
|---|---|
| **B1** — Composition over subclass | `TrajectorySpy(BaseCallbackHandler)` from `langchain_core.callbacks`; tests `test_trajectory_spy_subclasses_langchain_native_only` + `test_no_base_agent_callback_handler_subclass_in_runner_dir` enforce. |
| **B2** — `state["next_node"]` SSoT trajectory | `on_chain_end` reads `outputs.get("next_node")`; terminal sentinel `"respond"` filtered to noise-suppress. |
| **B3** — Best-effort spy callbacks | Every method body wraps in try/except + structlog warning; meta-test `test_trajectory_spy_callbacks_are_best_effort` passes 3 malformed payloads without raising. |
| **B4** — Reuse `sanitize_payload` from shared | `runner/artifacts.py` imports from `src.shared.agent_observability.recording.sanitization`; `test_artifacts_pii_sanitized` confirms email + phone fixtures get redacted. |
| **B5** — Append spy to existing callbacks list | Fixture `sales_agent_entrypoint` builds `invoke_config["callbacks"] = [*existing, spy]` — preserves production handler at index 0. |
| **B6** — No voice override / no slot manipulation | Fixture honors production `TenantKnowledgeBuilder` path; no test override of `system_instruction`. |
| **B7** — Smoke does not measure cache_hit_rate | Multi-turn metric deferred to Story 7. |

## Files changed

| File | Status | Lines | Purpose |
|---|---|---|---|
| `backend/tests/agentic_evals/sales_agent/runner/trajectory_spy.py` | NEW | 213 | Read-only LangChain callback observer (composition pattern) |
| `backend/tests/agentic_evals/sales_agent/runner/artifacts.py` | NEW | 109 | `write_run_artifacts(run_id, *, spy, response_text, assertions_results)` |
| `backend/tests/agentic_evals/sales_agent/fixtures/entrypoint.py` | EDIT | +18, -8 | Compose spy onto `RunnableConfig.callbacks` list at invoke time; expose `out["spy"]` |
| `backend/tests/agentic_evals/sales_agent/fixtures/tenant.py` | EDIT | +1, -1 | Voseo cleanup line 158 (`Configurá...guardá` → `Configura...guarda`) |
| `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` | EDIT | +245, -0 | 11 new meta-tests covering spy + artifacts + acceptance gates |

Zero `src/modules/sales_agent/` or `src/modules/copilot/` writes.

## Tests added

11 new tests; 8 default-CI (`@pytest.mark.no_eval`) + 1 eval-marked (A1
acceptance) + 2 helper integration tests:

* `test_trajectory_spy_subclasses_langchain_native_only` — A2 architectural
  guard (composition over subclass).
* `test_no_base_agent_callback_handler_subclass_in_runner_dir` — A2 lexical
  + AST guard combined.
* `test_trajectory_spy_captures_specialist_history_from_chain_end` — capture
  semantics + terminal sentinel filter.
* `test_trajectory_spy_tool_capture_drains_inflight_cache` — cache hygiene +
  orphan `on_tool_end` edge case.
* `test_trajectory_spy_callbacks_are_best_effort` — graceful-degradation
  Rule 6 verification.
* `test_trajectory_spy_reset_clears_all_state` — fixture teardown contract.
* `test_trajectory_spy_to_artifact_dict_returns_serialisable_payload` —
  JSON round-trip safety.
* `test_artifacts_writer_creates_run_id_subdir_with_3_files` — A3 acceptance.
* `test_artifacts_writer_is_idempotent` — rerun semantics.
* `test_artifacts_pii_sanitized` — A4 acceptance.
* `test_trajectory_spy_captures_first_specialist_and_tool_calls` — A1
  acceptance (eval-marked, requires `--run-evals`).

## Quality gates

| Gate | Result |
|---|---|
| Native ruff lint (eval-runner files) | ✅ `All checks passed!` |
| Native ruff format (eval-runner files) | ✅ `12 files already formatted` post-format |
| Native pytest default suite (no `--run-evals`) | ✅ `21 passed, 4 skipped, 1 warning in 10.75s` |
| Architecture fitness 823 tests | ✅ `823 passed, 1 warning in 25.51s` |
| Sales_agent observability downstream regression | ✅ `200 passed, 1 warning in 13.00s` |
| Anti-duplication grep `BaseAgentCallbackHandler` in `runner/` | ✅ `0 matches` |
| Anti-duplication grep mirrors of `sanitize_payload`, `FXResolver`, `PricingResolver`, `TurnEnvelope` in eval harness | ✅ `0 mirrors` |
| Spanish neutro voseo grep in eval-runner files | ✅ `0 matches` |
| Native-first compliance (no `docker exec ...` for lint/tests) | ✅ |

## Acceptance evidence

* **A1** — `test_trajectory_spy_captures_first_specialist_and_tool_calls` defined and properly skipped on default CI; runs with `--run-evals`.
* **A2** — `! grep -rn 'BaseAgentCallbackHandler' backend/tests/agentic_evals/sales_agent/runner/` returns exit code 1 (no matches).
* **A3** — `test_artifacts_writer_creates_run_id_subdir_with_3_files` PASS — three files (`assertions.json`, `response.txt`, `trace.json`) under `_artifacts/{run_id}/`.
* **A4** — `test_artifacts_pii_sanitized` PASS — email + phone redaction verified.

## State of the art validation

LangChain `BaseCallbackHandler` import path verified via grep against
`backend/.venv/lib/python3.12/site-packages/langchain_core/callbacks/base.py:493` —
the canonical class lives in `langchain_core.callbacks`. Method
signatures (`on_chain_end`, `on_tool_start`, `on_tool_end`) verified
against the same file's signatures. No web fetch needed (LangChain
docs URL had redirect chain noted in CONTEXT-BRIEF § 15; library
source is the more authoritative source anyway).

## Next steps

* Awaiting `gate-runner` Haiku (orchestrator-spawned) to run
  `/test-backend` 13 gates.
* Awaiting `auditor-agentic` Opus (orchestrator-spawned) for
  independent verdict.
* Builder phase complete — state `tests-passing` per
  `docs/process/ticket-states.md`.
