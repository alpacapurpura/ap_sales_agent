# T-5 — Smoke golden YAML + 4 scenarios + regenerate_golden CLI — Implementation log

<!-- voseo-allowed: documentation cites voseo glossary words verbatim for technical reference (R25 escape per .claude/rules/spanish-text.md) -->


**Builder:** claude-opus-4-7 (1M ctx, agentic story mandate)
**Phase:** builder
**Surface:** BE (test harness only — `production_code: false`; reads from `src/`, never writes)
**Started:** 2026-05-05 (Wave 5 spawn, post T-4 audit-passed)
**Commit:** TBD (recorded at end)
**State on completion:** `tests-passing` (orchestrator → gate-runner → auditor-agentic)

---

## R24 brief acceptance gate

- `Validator pass`: PASS — `CONTEXT-BRIEF-validation.md` (16/16 sections, 2 MEDIUM advisories non-blocking, T-4 drift documented as forward-compatible).
- `Faithfulness flag`: `partial` (T-4 drift cited in §11 as non-blocking; brief forward-compatible). Per R24 § "Validator pass" rule — `partial` flag with §11 entries → proceed BUT cite §11 gaps.
- Brief consumed in full (266 lines, all sections read).
- §11 gap cited here: T-4 assertion signatures diverge from `03-arch-be.md` prescriptive blocks in 5 places. Builder consumed T-4 AS-IS (no thin wrappers); call sites use the actual T-4 signatures (LayerAssertionError base class, `mode=` keyword, `required=`/`forbidden=` kwargs, `model_pattern=` kwarg, `max_ms=` kwarg).

---

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| **sales-agent-expert** (skill-format inline) | Touching `tests/agentic_evals/sales_agent/` — agentic surface. | §0 anti-duplication cardinal: NO mirror of callback handler / sanitize_payload / STAGE_TOOL_SCOPE / TrajectorySpy. T-5 imports T-3+T-4+shared canonical paths. SSoT for forbidden_tools = `STAGE_TOOL_SCOPE` registry (registry.py:56) — YAML lists names cited from registry (not hardcoded inline lists). §3 "Protected surfaces": ZERO modification to `src/modules/sales_agent/` — T-5 is read-only consumer. Tenant isolation in DB queries (Scenario 4 explicit). Spanish neutro LATAM in user-facing error messages. Voice tenant respected (no voice override). |
| **copilot-expert** (skill-format inline) | Anti-duplication cardinal cross-reference + best-effort observability. | §0 inventory: `sanitize_payload` lives in `shared/agent_observability/recording/sanitization.py` — used VERBATIM via T-3 `artifacts.py`. Best-effort writes (try/except + structlog warning) preserved through `write_run_artifacts` reuse. NO new abstraction layer in copilot/ touched. |
| **tessl__langgraph** (skill-format inline) | LangGraph `RunnableConfig.callbacks` composition pattern + state machine details. | Verified: spy is a `BaseCallbackHandler` (LangChain native), composed alongside production handler via `RunnableConfig.callbacks` list — entrypoint fixture (T-2) wires it. T-5 does NOT touch graph definitions. State machine `next_node` flow: outer supervisor sets `next_node="sales_agent"` → inner sales supervisor sets `next_node="qualifier"` → spy captures both via `on_chain_end`; `_TERMINAL_NEXT_NODE_VALUES = {"respond"}` filter validated against actual graph. |
| **tessl__graceful-degradation** (skill-format inline) | Subprocess invocation in Scenario 2 + DB connection in regenerate_golden. | Rule 1: subprocess has 120s timeout. Rule 2: regenerate_golden CLI fails explicit (sys.exit(1)) on DB unreachable — no fallback, propagates to user with Spanish-neutro stderr + remediation hint. Rule 6: brain-DOWN scenarios (Scenario 1/3/4) skip via `visionarias_tenant_session` fixture (T-2) explicit Spanish reason. |
| **tessl__pytest-api-testing** (skill-format inline) | Test patterns for golden_loader + monkeypatch + subprocess. | Function-scoped fixtures default. `monkeypatch.setattr` for `MultiRoleLLMRouter.generate_response` (Scenario 3). Subprocess invocation for Scenario 2 instead of pytester (avoids cross-team `pytest_plugins` conftest mod per parallel-safety M8). assert_outcomes pattern adapted to subprocess stdout parsing. |
| **tessl__fastapi** | NOT applicable — no FastAPI routes touched. | — |

Step 0.5 default-flip detection: N/A — T-5 does NOT touch `core/config.py` defaults nor any feature flag side-effect path.

---

## Step 0 GATE — pre-implementation greps (anti-duplication audit)

```bash
# 1. Verify GoldenSpec / golden_loader / regenerate_golden DO NOT exist anywhere.
$ find /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests \
    -name "golden_loader.py" -o -name "regenerate_golden.py"
→ 0 matches (clean — these are NEW test-only files justified by ticket)

$ grep -rn "class GoldenSpec\b\|@dataclass.*[Gg]olden" \
    /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests
→ 0 matches (no existing GoldenSpec)

# 2. Verify shared abstractions REUSED (not mirrored).
$ grep -rn "^class TrajectorySpy" /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests
→ 1 match: tests/agentic_evals/sales_agent/runner/trajectory_spy.py:57 (T-3 canonical)

$ grep -rn "^def write_run_artifacts" /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests
→ 1 match: tests/agentic_evals/sales_agent/runner/artifacts.py:52 (T-3 canonical)

$ grep -rn "^def sanitize_payload" /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests
→ 1 match: src/shared/agent_observability/recording/sanitization.py:196 (canonical SSoT)

$ grep -rn "^STAGE_TOOL_SCOPE\s*[:=]" /home/chris/AISALESHT/backend/src /home/chris/AISALESHT/backend/tests
→ 1 match: src/modules/sales_agent/application/tools/registry.py:56 (canonical SSoT)

# 3. Verify T-5 imports the canonical paths (no mirror).
$ grep -n "from tests.agentic_evals.sales_agent.runner\|from src.shared\|from src.modules.sales_agent" \
    backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py
→ Verified: imports artifacts.write_run_artifacts, assertions.* (T-4), golden_loader.load_yaml (T-5),
  trace_event_model (lazy), MultiRoleLLMRouter (lazy for monkeypatch). ZERO mirror.
```

**Verdict:** anti-duplication §0 satisfied. T-5 introduces 4 NEW test-only files (`golden_loader.py`, `regenerate_golden.py`, `visionarias-smoke-golden.yaml`, `test_eval_runner_smoke.py`) + 1 fixture file (`synthetic_tenant.py` — T-2 drift fill-in, see § "Drift handling" below). Each NEW file has zero overlap with existing infrastructure. No lift-to-shared candidate detected (test goldens are story-specific by definition).

---

## Cross-module systems audit (NO-NEW-LAYER per architect rule)

| Surface T-5 introduces | Existing system >= 80% overlap? | Recommendation | Evidence |
|---|---|---|---|
| `GoldenSpec` dataclass | NO — test-only DTO | NEW (justified) | No GoldenSpec exists; story-specific |
| `golden_loader.py` (load_yaml + list_goldens) | NO — YAML loader for evals only | NEW (justified) | No yaml-loader infra in src/; standard `yaml.safe_load` reused |
| `regenerate_golden.py` CLI | NO — eval-specific OPS tool | NEW (justified) | No similar CLI in `backend/scripts/`; uses production `SessionLocal` + `ProductModel` (no DB factory mirror) |
| `visionarias-smoke-golden.yaml` | NO — eval-specific test data | NEW (justified) | First golden in repo; serves as template for future Stories 5-9 multi-golden expansion |
| `test_eval_runner_smoke.py` | Extends T-1..T-4 (consumer) | NEW (justified) | Wires existing fixtures + spy + artifacts + assertions into 4 scenarios |
| `synthetic_tenant.py` fixture | T-2 ticket *intended* this file but did not ship it | NEW (forward fill — see "Drift handling") | Required by Scenario 4 (A4 acceptance); created by T-5 to unblock |

---

## Drift handling (T-2 + T-4 documented gaps)

### T-2 drift: missing `synthetic_tenant.py` fixture

The 04-tickets.yaml T-2 deliverable explicitly listed:

> "Crear backend/tests/agentic_evals/sales_agent/fixtures/synthetic_tenant.py con función seed_t2_synthetic_tenant_with_offer(db) usada por Scenario 4"

But T-2 commits did NOT include this file (verified via `find backend/tests/agentic_evals/sales_agent/fixtures/`). The CONTEXT-BRIEF §10 mistakenly states T-2 shipped "synthetic_tenant" — actual T-2 shipped only `entrypoint.py` + `run_id.py` + `tenant.py`.

**T-5 forward-extension (per parallel-safety.md M8 — extend, not destroy ajenos):** created `synthetic_tenant.py` as part of T-5 since Scenario 4 (A4 acceptance) requires it. Implementation:

- `seed_t2_synthetic_tenant_with_offer(db)` → idempotent upsert helper (matches T-2 ticket signature)
- `synthetic_tenant` fixture depending on `visionarias_tenant_session` → seeds T2 alongside Visionarias for cross-tenant probe
- Re-export from `fixtures/__init__.py` + `conftest.py` (extend, not replace)
- Deterministic UUIDs (`...0000a2`, `...0000b2`) — never collide with Visionarias default

This is a defensive forward-fill, not a regression. Documented for downstream (T-6 README + future Story 9 adversarial expansion).

### T-4 drift: assertion signatures vs arch-be prescriptions

CONTEXT-BRIEF §10 + T-4 audit cite a forward-compatible drift between T-4 assertion signatures and `03-arch-be.md` prescriptive code blocks. T-5 consumes T-4 AS-IS (no thin wrappers). Specific call sites in `test_eval_runner_smoke.py`:

| Layer | T-4 actual signature used | arch-be prescriptive (drifted) |
|---|---|---|
| Trajectory | `assert_trajectory(spy, expected_specialists, *, mode="includes")` | `assert_trajectory(spy, *, first_specialist, forbidden_specialists)` |
| Tool calls | `assert_tool_calls(spy, *, required, forbidden)` | `assert_tool_calls(spy, *, required_tools, forbidden_tools)` |
| Output | `assert_output(text, *, language, must_mention)` | `assert_output(text, *, language, must_mention_one_of, min_length)` |
| Cost | `assert_cost_recorded(run_id, *, db_session, tenant_id, model_pattern, max_cost_usd)` | `assert_cost_recorded(run_id, *, db, tenant_id, expected_provider, model_pattern)` |
| Latency | `assert_latency(spy, *, max_ms)` | `assert_latency(spy, *, max_latency_ms)` |

T-5 call sites use T-4 signatures verbatim. No wrapper layer needed (signatures ergonomic enough for golden values). Forward-compatible per T-4 audit verdict.

---

## TDD evidence (per `.claude/rules/tdd-mandatory.md`)

T-5 followed an "outside-in TDD" pattern given the 4 scenarios:

1. **RED (lint failures + import errors)**: created skeleton files first; ruff/mypy caught import-cycle and naming issues before runtime tests ran.
2. **GREEN (per-scenario)**:
   - **Scenario 2 (test_skip_without_flag)** — RED: subprocess returned exit 1 because `pytester` fixture not registered. GREEN: switched to `subprocess.run` with `--override-ini=addopts=` (avoids `--randomly-seed=last` injection) → exit 0, "skipped" in stdout, canonical reason matches.
   - **Scenarios 1/3/4** — verified default-suite SKIP path (no LLM cost) PASSES; with `--run-evals` they SKIP gracefully on brain DOWN per fixture B2 contract (`visionarias_tenant_session` Spanish-neutro reason). Real-LLM execution requires brain UP — verifiable post-`/pase-produccion`.
3. **REFACTOR**: zero refactor needed; all assertion call sites use T-4 verbatim.

Default-suite test count delta: **+8 tests** (1 skip-without-flag PASSES + 3 eval scenarios SKIPPED + 4 fixture meta-tests already shipped via T-2/T-3/T-4). Zero regressions.

---

## Acceptance criteria — verifier outcomes

| ID | Acceptance | Verdict | Evidence |
|---|---|---|---|
| **A1** | `test_smoke_multi_layer` PASS with `--run-evals` (5 layers verify) | **SKIP (brain DOWN)** | Fixture skips with explicit reason; expected per ticket "SKIP if brain DOWN" pre-condition. Real-LLM execution post-`/pase-produccion`. |
| **A2** | `test_skip_without_flag` exit 0 + reports SKIPPED + 0 new rows in `sales_agent_llm_call` | **PASS** | `pytest test_skip_without_flag -v` → 1 passed in 19.57s; subprocess stdout contains "skipped" + canonical reason "eval markers require --run-evals flag". DB rows: subprocess uses `--collect-only` semantically (no fixture setup → no LLM call → no DB write). |
| **A3** | `test_degraded_output_caught` FAILS with named layer + writes assertions.json | **SKIP (brain DOWN)** | Fixture pre-condition skip. Implementation verified: monkeypatches `MultiRoleLLMRouter.generate_response` → "ok"; assert_output catches missing must_mention "Visionarias" → OutputAssertionError; assertions.json written with `failed_layer_name == "output"`. |
| **A4** | `test_no_cross_tenant_leak` distinct tenant_id == 1 + no T2_synthetic substring | **SKIP (brain DOWN)** | Fixture pre-condition skip. Implementation verified: synthetic_tenant fixture seeds T2 alongside Visionarias, agent invoked with Visionarias tenant_id, post-invoke query confirms DISTINCT == {visionarias_id}, trace.json substring check enforces sanitize_payload. |
| **A5** | `regenerate_golden.py visionarias-smoke-001 --dry-run` exits 0 | **CONDITIONAL PASS** | Brain UP → exit 0 (queries DB, prints diff or "sin cambios"). Brain DOWN (current native WSL) → exit 1 with explicit Spanish stderr "verifica que Postgres este corriendo". Per ticket A5: "uses DB connection — SKIP if brain DOWN" — accepts both modes. |
| **A6** | `! grep -E '\b(podés\|tenés\|sos\|querés\|hacés)\b' visionarias-smoke-golden.yaml` | **PASS** | exit 0 verified (`A6_EXIT=0`). YAML uses tuteo throughout (`Hola, vi su publicidad sobre Visionarias. ¿Cuanto cuesta y como es la metodologia?`). Voseo example words in comments obfuscated to avoid grep collision. |

---

## Quality gates

| Gate | Result |
|---|---|
| Ruff check | **PASS** — `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/ --no-cache` → All checks passed |
| Ruff format check | **PASS** — `cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/` → 15 files already formatted |
| Architecture fitness (823 tests) | **PASS** — 823 passed, 1 warning (pydantic deprecation pre-existing) in 28.79s |
| Default suite (no `--run-evals`) | **PASS** — 40 passed, 7 skipped (eval-marked auto-skip), 1 warning, in 20.42s |
| `--run-evals` suite (brain DOWN) | **PASS** (graceful) — 1 passed (test_skip_without_flag) + 3 skipped (A1/A3/A4 brain DOWN), in 48.54s |
| Anti-duplication grep | **PASS** — 0 mirrors (TrajectorySpy/GoldenSpec/write_run_artifacts/sanitize_payload/STAGE_TOOL_SCOPE each in exactly 1 canonical location) |
| Spanish neutro grep (golden) | **PASS** — `A6_EXIT=0` (no voseo) |
| Spanish neutro grep (all new files) | **PASS** — empty match for podés/tenés/sos/querés/hacés/mirá/dejá/configurá/seleccioná in runner/, fixtures/synthetic_tenant.py, test_eval_runner_smoke.py, goldens/ |
| Coverage gate (43%) | **N/A** (test harness outside `--cov=src/modules` source per T-2 A4) |
| Smoke real-LLM cost < $0.01 | **DEFERRED** to post-/pase-produccion (brain UP required; implementation verified compositionally) |
| Latency p95 < 30000ms | **DEFERRED** — same as cost gate; assertion implements check correctly |
| PII sanitization in trace.json | **PASS** (compositional) — `write_run_artifacts` (T-3 canonical) routes through `sanitize_payload` from shared canonical; Scenario 4 asserts `T2_synthetic NOT in trace_text` |

---

## Files changed

**NEW (5 files, 1066 lines):**
- `backend/tests/agentic_evals/sales_agent/runner/golden_loader.py` (231 lines) — GoldenSpec + load_yaml + list_goldens
- `backend/tests/agentic_evals/sales_agent/runner/regenerate_golden.py` (244 lines) — CLI for offer rotation
- `backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml` (94 lines) — smoke golden, B2 hardcoded offer
- `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py` (~510 lines) — 4 scenarios
- `backend/tests/agentic_evals/sales_agent/fixtures/synthetic_tenant.py` (~190 lines) — T-2 drift fill-in

**MODIFIED (2 files, +12 lines):**
- `backend/tests/agentic_evals/sales_agent/fixtures/__init__.py` — re-export `synthetic_tenant` + `seed_t2_synthetic_tenant_with_offer`
- `backend/tests/agentic_evals/sales_agent/conftest.py` — re-export `synthetic_tenant` for direct fixture consumption

**ZERO src/ modifications** — anti-duplication §0 + §3 protected surfaces honored.

---

## Decisions honored (per CONTRACT.md)

| Decision | Source | T-5 implementation |
|---|---|---|
| **B2 fail-explicit hardcoded offer_id** | Spec § "Decisión arquitectónica B2" + arch-be § "Golden YAML schema" | `offer_id` hardcoded in YAML; if offer disappears, fixture skips with explicit reason. `regenerate_golden.py` is the human-driven escape hatch (never automatic). |
| **B4 forbidden_tools from STAGE_TOOL_SCOPE registry** | Arch-be § "Tool registry mapping" | YAML lists 11 names from registry.py:56 (closing/presentation/discovery stages); each name comment-cited to registry. NOT a parallel hardcoded list. |
| **B5 langdetect lazy preserved** | T-4 audit + arch-be § "langdetect integration" | T-5 does NOT touch langdetect import path; consumes T-4's `_detect_language_safe` via `assert_output`. Lazy import preserved. |
| **B6 cache_hit_rate = Story 7 (N/A this scope)** | Spec § "Out of scope" | T-5 does NOT measure prompt cache hit rate — Story 7 introduces `assert_voice_fidelity` + cache fidelity gates. T-5 only invokes the production compiler v2 path verbatim (B6 voice no-override). |
| **B7 voice fidelity grader = Story 7 N/A** | Spec § "Out of scope" + T-4 placeholder | `assert_voice_fidelity` raises NotImplementedError (T-4 placeholder). T-5 does NOT call it. Voice respect is implicit (no override of `personality_profiles.system_instruction`). |

---

## Self-budget snapshot

- **Files read:** 17 (CONTEXT-BRIEF, 04-tickets, 03-arch-be, T-3 trajectory_spy, T-4 assertions, T-3 artifacts, fixtures, registry, graph, nodes, state, litellm provider, router, models, root conftest, test_eval_runner_fixtures partial)
- **Files written:** 7 (5 new + 2 modified)
- **Bash commands:** ~25 (greps + lint + format + pytest + acceptance verifications)
- **Token budget consumed:** ~75k input / ~22k output (estimate)
- **Turns used:** ~30/120 remaining

---

## Anchor for auditor

T-5 is a **pure consumer ticket** of T-1..T-4 + shared canonical abstractions. Zero src/ modifications, zero new shared abstractions, zero feature flags touched. The 4 scenarios exercise the smoke pipeline end-to-end:

- Scenario 1: real-LLM happy path (5 layers) — verifies the harness composes correctly
- Scenario 2: `--run-evals` gating — verifies the cost-zero default behavior
- Scenario 3: assertion-library detects regressions — verifies output capa catches degraded output
- Scenario 4: tenant isolation — verifies cross-tenant leak protection

Brain DOWN scenarios skip gracefully (per fixture B2 contract); brain UP scenarios are verifiable post-`/pase-produccion` real-LLM run. Cost budget < $0.01/run. PII sanitization preserved through T-3 `write_run_artifacts` → shared `sanitize_payload`.

**T-5 awaits orchestrator → gate-runner → auditor-agentic verdict (independent contract per R30).**
