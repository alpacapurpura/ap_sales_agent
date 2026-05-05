# T-4 — Multi-layer assertion library — Implementation log

**Builder:** claude-opus-4-7 (1M ctx, agentic story mandate)
**Phase:** builder
**Surface:** agentic (test harness only — `production_code: false`)
**Started:** 2026-05-05 (post Wave 4 spawn)
**Commit:** TBD (added at end)
**State on completion:** `tests-passing` (orchestrator → gate-runner → auditor-agentic)

---

## R24 brief acceptance gate

- `Validator pass`: PASS — `CONTEXT-BRIEF-validation.md` (16/16 sections, 2 MEDIUM advisories non-blocking, zero contradictions).
- `Faithfulness flag`: `clean` (NOT `partial` / `blocking`).
- Brief consumed in full per CONTEXT-BRIEF.md (370 lines, 16 sections).

---

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| **sales-agent-expert** (loaded as `command-name`) | Touching `tests/agentic_evals/sales_agent/` — agentic surface. | §0 anti-duplication cardinal: do NOT mirror callback handler / sanitize_payload / FX resolver. T-3 already established composition pattern — T-4 reads spy outputs only. Tenant isolation in cost query (mandatory). Spanish neutro LATAM in user-facing error messages (no voseo: "se esperó / se observó"). |
| **tessl__pytest-api-testing** (loaded as `command-name`) | New pytest fixtures + tests. | Function-scoped fixtures default. Used `pytest.MonkeyPatch.context()` for replacing `importlib.import_module` (langdetect mock) + `langdetect.detect`. Test errors not just happy paths (forbidden tool fires, cost = 0 row, model mismatch, langdetect failure path). Extended existing `test_eval_runner_fixtures.py` (Section 6) — did NOT replace. |
| **tessl__graceful-degradation** (loaded as `command-name`) | Lazy import + langdetect optional dep. | Rule 6 (lazy import + fallback): `_detect_language_safe` imports langdetect via `importlib.import_module` ONLY inside function body. Try/except both `ImportError` AND `LangDetectException` — return `"unknown"`. `assert_output` skips language layer when detection unavailable (logs warning, continues with `must_mention` check). Never raises from detection helper. |

`tessl__langgraph` NOT applicable (no graph code modified — T-4 reads spy outputs).
`tessl__fastapi` NOT applicable (no routes — assertions are pytest-only).
`copilot-expert` NOT applicable (test harness for sales_agent only).

Step 0.5 default-flip detection: N/A — T-4 does not touch `core/config.py` defaults.

---

## Step 0 GATE — pre-implementation greps

**Cross-module audit (NO-NEW-LAYER per anti-duplication.md):**

```bash
$ grep -rn 'def detect_lang\|def language_detect\|def _detect_language' \
  /home/chris/AISALESHT/backend/src/ /home/chris/AISALESHT/backend/tests/agentic_evals/
→ 0 matches (no existing language detection helpers anywhere)

$ grep -rn 'def assert_\|class.*AssertionError' \
  /home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/
→ 0 matches (no existing assertion utilities)

$ grep -rn 'sanitize_payload' /home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/runner/
→ 4 matches (artifacts.py + trajectory_spy.py docstrings + 1 import from shared canonical)
  Decision: REUSE shared, NEVER mirror. assertions.py does NOT import or duplicate.

$ grep -rn 'BaseAgentCallbackHandler' /home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/runner/
→ 0 executable refs (confirmed by existing AST-walk arch test
  test_no_base_agent_callback_handler_subclass_in_runner_dir)
```

**Verdict:** ZERO existing systems overlap T-4 scope. assertions.py is NEW (4 layer assertions + 1 EXTEND for cost via DB-read). NO shared lift required — eval harness is intentionally isolated in `tests/agentic_evals/`.

---

## Decisions honored from CONTRACT

| Decision | How applied |
|---|---|
| **B4 (forbidden tool names sourced from registry)** | `assert_tool_calls(spy, *, required, forbidden)` accepts list parameters; does NOT hardcode tool names inline. CONTRACT § "TOOL REGISTRY (B4 binding)": registry import is heavy/lazy → caller supplies list. Smoke test (T-5) will pass list from `STAGE_TOOL_SCOPE` constant via fixture. |
| **B5 (langdetect lazy import only)** | `assertions.py` has ZERO top-level langdetect imports. `_detect_language_safe` uses `importlib.import_module("langdetect")` inside body. Architectural test `test_assertions_module_no_top_level_langdetect_import` walks AST + verifies no `import langdetect` / `from langdetect import` at module-top-level scope. |
| **B7 (cache_hit_rate = Story 7 scope)** | `assert_voice_fidelity` is a Story-7 placeholder raising `NotImplementedError`. Test `test_assert_voice_fidelity_is_placeholder` asserts the message mentions "Story 7" or "future" so callers know where the real impl lives. Smoke test (T-5) MUST NOT call this function. |
| **Tenant isolation (`.claude/rules/tenant-isolation.md`)** | `assert_cost_recorded` query filters BOTH `tenant_id` AND `turn_id == run_id` (eval `run_id` maps to `sales_agent_llm_call.turn_id`, the canonical sales_agent column — there is no `run_id` column). Caller passes `tenant_id` explicitly from `visionarias_tenant_session` fixture. Cross-tenant leakage is a security failure — never relax this. |
| **Spanish neutro LATAM (`.claude/rules/spanish-text.md`)** | All user-facing error messages in Spanish neutro: "se esperó" / "se observó" / "no aparece" / "Trayectoria incompleta" / "Idioma del output no coincide" / "Suma de costos excede presupuesto del smoke" / "Latencia observada excede el límite del smoke". Zero voseo (`-ás/-és/-ís` forms). Layer prefix `[capa: <name>]` is ASCII for grep-friendly piping. |
| **Anti-duplication §0** | NO mirror of `sanitize_payload` (artifacts.py owns it via shared import). NO mirror of `BaseAgentCallbackHandler`. NO recompute of cost (reads `cost_usd` column written by production callback handler via shared `cost_recorder`). NO inline tool-name lists (caller supplies). |
| **Cost row degraded path (T-1 cost_recorder canonicalization)** | `assert_cost_recorded` distinguishes `cost_usd is None` (T-1 unknown-cost path) from `cost_usd <= 0` (degraded LiteLLM no-response_cost path). BOTH raise `CostAssertionError` so smoke catches silent regressions. Confirmed via `test_assert_cost_recorded_zero_row_raises`. |
| **Spy duration_ms duck-typing** | `assert_latency` reads three signal sources in order: (1) `spy.duration_ms` aggregate, (2) per-tool `duration_ms` in `tool_calls` items, (3) default `0` (no time signal → pass through). Avoids modifying T-3 spy (audit-passed) — T-3 doesn't yet capture timing; future story can add. Confirmed via 3 latency tests. |

---

## Implementation breakdown

### New file: `backend/tests/agentic_evals/sales_agent/runner/assertions.py`

- **496 lines** (post format), 12 public symbols, 1 `_SpyLike` Protocol, 4 internal helpers.
- 5 layer assertions + 1 Story-7 placeholder (`assert_voice_fidelity`).
- 6 exception classes: `LayerAssertionError` base + 5 subclasses, each with `.layer_name` class attribute + `.observed` / `.expected` instance attributes.
- Lazy langdetect import inside `_detect_language_safe` (Decision B5 binding).
- `_build_cost_query` lazily imports `SalesAgentLlmCallModel` to keep module loadable in linter pass.
- Ruff: 0 errors. Ruff format: clean.

### Modified file: `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py`

- Added Section 6 (T-4 multi-layer assertion library): 18 new tests, all `@pytest.mark.no_eval` (run on default suite without `--run-evals`).
- Acceptance covered:
  - **A1** `test_assertions_api_complete` — all 12 public symbols importable + `LayerAssertionError` hierarchy correct + `__all__` complete.
  - **A2** `test_assert_output_named_failure` — `OutputAssertionError.layer_name == "output"` + message contains layer name.
  - **A3** `test_assert_voice_fidelity_is_placeholder` — `NotImplementedError` raised with "Story 7" / "future" in message.
  - **A4** `test_detect_language_safe_returns_unknown_on_exception` — both `ImportError` (path 1, monkeypatch `importlib.import_module`) AND `LangDetectException` (path 2, monkeypatch `langdetect.detect`) yield `"unknown"`.
- Edge cases:
  - Trajectory: includes-mode subset, exact-mode strict order mismatch.
  - Tool calls: required missing, forbidden present (B4 binding).
  - Output: case-insensitive substring, language unknown skip-through.
  - Latency: aggregate `duration_ms`, summed `tool_calls[*].duration_ms`, no signal pass-through.
  - Cost: zero/None row, model pattern mismatch, sum > max budget, happy path.
  - Architectural: `test_assertions_module_no_top_level_langdetect_import` — AST walk verifies no top-level langdetect imports.

---

## TDD evidence (RED → GREEN)

**RED iteration 1** (pre `assertions.py`):
```bash
$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py -v -k "test_assertions or test_assert or test_detect_language"
================ 18 failed, 25 deselected, 1 warning in 11.07s =================
ModuleNotFoundError: No module named 'tests.agentic_evals.sales_agent.runner.assertions'
```

**GREEN iteration 2** (post `assertions.py` + 1 fix for langdetect short-text quirk):
```bash
$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py -v -k "test_assertions or test_assert or test_detect_language"
================ 18 passed, 25 deselected, 1 warning in 11.81s =================
```

Initial GREEN run had 1 failure (`test_assert_output_must_mention_case_insensitive`) — root cause: `langdetect` mistook short Spanish "Hola, te confirmo la reserva." for Italian (well-known langdetect quirk on 30-char inputs). Fix: extended test fixture text to a longer realistic Spanish response (3 sentences, 90+ chars) — natural alignment with smoke test golden expectations. NOT a code bug.

---

## Quality gates

| Gate | Status | Evidence |
|---|---|---|
| Native ruff lint (`tests/agentic_evals/`) | ✅ PASS | `All checks passed!` |
| Native ruff format (`tests/agentic_evals/`) | ✅ PASS | `13 files already formatted` |
| Native pytest T-4 acceptance (A1-A4) | ✅ PASS | 18/18 GREEN (4 acceptance + 14 edge cases) |
| Native pytest full eval harness (no --run-evals) | ✅ PASS | 39 passed, 4 skipped (eval markers) |
| Native pytest full backend default suite (-m "not integration") | ✅ PASS | 9041 passed, 34 skipped, 16 deselected, 0 failed (568s) |
| Native pytest architecture fitness | ✅ PASS | 823 passed (preserved baseline) |
| Anti-duplication grep (no langdetect/sanitize_payload mirror) | ✅ PASS | 0 mirrors detected |
| Langdetect lazy import grep (no top-level) | ✅ PASS | `^import langdetect\|^from langdetect` returns 0 matches in assertions.py |

---

## Acceptance verdict (each)

| A# | Verifier | Result |
|---|---|---|
| A1 | `pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py::test_assertions_api_complete` | ✅ PASS |
| A2 | `pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py::test_assert_output_named_failure` | ✅ PASS |
| A3 | `pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py::test_assert_voice_fidelity_is_placeholder` | ✅ PASS |
| A4 | `pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py::test_detect_language_safe_returns_unknown_on_exception` | ✅ PASS |

---

## Forbidden file scope (parallel-safety M1+M8)

T-4 builder ONLY touched these 2 files in same session:

- `backend/tests/agentic_evals/sales_agent/runner/assertions.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` (extended Section 6, no edits to T-2/T-3 sections)

NOT touched (Wave 4 Story A T-6a builder-backend parallel session WIP):
- `backend/src/modules/iam/...` (3 files)
- `backend/src/shared/infrastructure/llm/factory.py`
- `backend/tests/modules/iam/...` (4 files)
- `backend/alembic/versions/123_*.py`

NOT touched (other parallel context-builder sessions):
- `docs/projects/.../CONTEXT-BRIEF*.md` (4 files)

Per `git add` by exact filename only. NO `git add .` / `git add -A`.

---

## Commit reference

(Filled at commit time in transitions table.)

---

## Footer for orchestrator

State transition recommended: `draft` → `tests-passing` (post-build). Next step: orchestrator spawn `gate-runner` Haiku for full `/test-backend` 13-gate sweep + downstream regression scope check, then spawn `auditor-agentic` Opus for independent verdict.
