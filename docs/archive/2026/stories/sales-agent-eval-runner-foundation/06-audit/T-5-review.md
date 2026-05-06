<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-5 Agentic Review — sales-agent-eval-runner-foundation

> Auditor: `auditor-agentic` (Opus 4.7, 1M ctx) — invariants validated against canonical docs as of 2026-05-06
> Iter: 1
> Verdict: **APPROVED** (1 non-blocking WARN — Cat 11 schema-drift ratified by T-4 audit precedent)
> Generated: 2026-05-06T01:00:00Z
> Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live researched on 2026-05-06.

## Inputs

- CONTEXT-BRIEF.md: **used** (validator PASS, 2 MEDIUM advisories non-blocking, faithfulness flag `partial` — T-4 drift ratified upstream).
- gate-output.json: **used** (any_fail=false, 12 gates evaluated; manual finalization per R22 fallback).
- Skills invoked: **copilot-expert=Y** (anti-duplication §0 + observability inventory) · **sales-agent-expert=Y** (§0 anti-dup cardinal + §3 protected surfaces + STAGE_TOOL_SCOPE SSoT) · **tessl__langgraph=Y** (RunnableConfig.callbacks composition) · **tessl__graceful-degradation=Y** (timeouts + fail-explicit DB).

## Step 4.5 — Downstream regression scope

| Surface modified | In SSoT tabla `auditor-downstream-regression.md`? | Downstream test_targets | Status |
|---|---|---|---|
| `backend/tests/agentic_evals/sales_agent/runner/golden_loader.py` (NEW test-only) | NO — test path | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/runner/regenerate_golden.py` (NEW test-only) | NO — test path | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml` (NEW data) | NO — test data | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py` (NEW test-only) | NO — test path | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/fixtures/synthetic_tenant.py` (NEW fixture) | NO — test path | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/conftest.py` (re-export only) | NO — test path | n/a | n/a |
| `backend/tests/agentic_evals/sales_agent/fixtures/__init__.py` (re-export only) | NO — test path | n/a | n/a |

**Verdict:** ZERO `shared/` or `modules/` paths touched. ZERO `core/config.py` flag flips. Per `.claude/rules/auditor-downstream-regression.md` SSoT tabla, no downstream regression spawn required. Architecture fitness `823 PASS` preserved (gate-output evidence).

## Gate status (from gate-output.json)

| Gate | Status | Errors |
|---|---|---|
| ruff_lint | PASS | 0 |
| ruff_format | PASS | 0 |
| pytest_architecture | PASS | 0 (823/823 PASS, 1 pre-existing pydantic warning) |
| pytest_agentic_evals_default | PASS | 0 (40 passed, 7 skipped per design, 19.83s) |
| pytest_eval_run_evals_brain_down | PASS_WITH_PRECONDITION_SKIPS | 0 (1 PASS A2 + 3 SKIP A1/A3/A4 brain-DOWN per fixture B2 binding) |
| acceptance_a1_smoke_multi_layer | DEFERRED_BRAIN_DOWN | n/a (compositionally verified; real-LLM post `/pase-produccion`) |
| acceptance_a2_skip_without_flag | PASS | 0 (subprocess exit 0, "skipped" + canonical Spanish reason) |
| acceptance_a3_degraded_output_caught | DEFERRED_BRAIN_DOWN | n/a (monkeypatch chain verified compositionally) |
| acceptance_a4_no_cross_tenant_leak | DEFERRED_BRAIN_DOWN | n/a (synthetic_tenant fixture seeds verified compositionally) |
| acceptance_a5_regenerate_golden_dry_run | DEFERRED_BRAIN_DOWN_OR_EXIT1_EXPLICIT | n/a (CLI uses DB; brain-DOWN exits 1 with explicit Spanish stderr — accepted per ticket) |
| acceptance_a6_spanish_neutro | PASS | 0 (live re-grep `exit 1` ⇒ no match) |
| anti_duplication_grep | PASS | 0 (each canonical in exactly 1 path) |

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | T-5 invokes `agent_app.ainvoke` read-only via T-2 entrypoint fixture; no state mutation; no new state schema; spy is `BaseCallbackHandler` (not subclass of `BaseAgentCallbackHandler`). `test_eval_runner_smoke.py:187,426,522`. |
| 2 | Tool registration | PASS | No new tools registered. T-5 references `STAGE_TOOL_SCOPE` (SSoT `registry.py:56`) for forbidden tools list — verified union of {discovery+presentation+closing} = 11 names matches YAML literal. `visionarias-smoke-golden.yaml:81-92`. |
| 3 | Prompt cache architecture | PASS | T-5 does NOT modify slot order, does NOT override `personality_profiles.system_instruction` (slot 5 BRAND_VOICE), does NOT inject dynamic content into cacheable prefix. Smoke invokes production compiler v2 verbatim per Decision B6. Per CONTEXT-BRIEF §2: "smoke does NOT measure cache_hit_rate (Story 7 scope)." Acceptable for this scope. |
| 4 | deepagents subagent isolation | NA | T-5 does not introduce or modify deepagents subagents. sales_agent uses LangGraph StateGraph, not deepagents harness. |
| 5 | Observability (`copilot_trace_event` + cost recording) | PASS | T-5 reads from `sales_agent_trace_event` (Scenario 4) + `sales_agent_llm_call` (via `assert_cost_recorded` T-4); writes nothing to observability tables (read-only consumer). PII redaction verified via `write_run_artifacts` T-3 chain → `sanitize_payload` shared canonical. `test_eval_runner_smoke.py:540-553` (DISTINCT tenant_id query) + `test_eval_runner_smoke.py:574-588` (trace.json substring absence). |
| 6 | Eval goldens (sales_agent) | PASS | T-5 IS the foundation eval golden + 4 scenarios (smoke + skip + degraded + cross-tenant). Schema documented in `golden_loader.py` docstring + arch-be § "Golden YAML schema" (T-4 forward-compat drift ratified). Voice fidelity grader = Story 7 placeholder honored (`assert_voice_fidelity` raises NotImplementedError). 1 happy + 1 negative + 1 edge + 1 adversarial = 4 scenarios per spec. ≥3 goldens convention NA (foundation = single golden per ticket scope). |
| 7 | RAG / Qdrant hygiene | NA | T-5 does not touch Qdrant, vector search, or KnowledgeService. |
| 8 | LLM provider routing | PASS | No hardcoded model strings in T-5 logic. YAML `max_cost_usd: 0.01` is per-turn budget cap, not a model selector. Scenario 3 `monkeypatch.setattr(MultiRoleLLMRouter, "generate_response", ...)` patches the canonical router seam (verified `factory.py:46` returns `MultiRoleLLMRouter` instance; specialists call via `_get_llm_service(state).generate_response`). Post-Wave-3 LiteLLM proxy is the only dispatch path — single-router invariant honored. `test_eval_runner_smoke.py:418-424`. |
| 9 | Cost optimization | PASS | YAML `max_cost_usd: 0.01` documented per spec (smoke single-turn ~$0.001-0.005). Latency p95 < 30s documented (`max_latency_ms: 30000`). `assert_cost_recorded` T-4 enforces budget cap. Cache hit rate = Story 7 (B6 honored). |
| 10 | Channel format & brand voice | PASS | YAML `input_message` Spanish neutro LATAM (tuteo: "vi su publicidad / cuanto cuesta / como es") — A6 grep verified 0 voseo. Smoke does NOT override `personality_profiles.system_instruction`; voice fidelity is implicit (Story 7 scope). Builder honored `sales-agent-expert` skill §3 protected surface. `visionarias-smoke-golden.yaml:57-58`. |
| 11 | DDD compliance (agentic specifics) | **WARN** | YAML schema diverges from arch-be § "Golden YAML schema" prescriptive block in 4 fields: `tenant_id_env: "VISIONARIAS_TENANT_ID"` → builder uses literal `tenant_id: "00000000-0000-0000-0000-000000000001"`; `expected_assertions: {trajectory: {first_specialist, forbidden_specialists}, output: {min_length, spanish_marker_min_count, must_mention_one_of}, cost: {min_cost_usd, expected_provider, model_pattern}, latency: {max_ms}}` → builder flattened to top-level `expected_specialists / required_tools / forbidden_tools / must_mention / language / max_cost_usd / max_latency_ms`. **Drift ratified upstream:** T-4 audit (`06-audit/T-4-review.md` Cat 11 WARN) ACK'd 5-place signature drift between T-4 actual and arch-be prescriptive blocks; CONTEXT-BRIEF was authoritative for builder. Builder consumed T-4 signatures verbatim per IMPL-LOG § "Drift handling" — call sites use `mode=`, `required=`/`forbidden=`, `model_pattern=`, `max_ms=`, etc. **Forward-compatible per T-4 audit verdict.** `visionarias-smoke-golden.yaml:38,50,73,82,107,111` + `test_eval_runner_smoke.py:197,211,225,247,269`. **Non-blocking** because: (a) CONTEXT-BRIEF was authoritative + validator PASS, (b) T-4 audit closed the gap at upstream layer, (c) all 5 assertion signatures internally consistent, (d) golden YAML loader (`golden_loader.py:60`) requires the flattened keys (matches T-4 API surface). |
| 12 | Tests / TDD | PASS | TDD evidence per IMPL-LOG: outside-in (skeleton → ruff/mypy RED → per-scenario GREEN). 4 scenarios + meta-tests per T-2/T-3/T-4 verified. Default suite 40 PASS / 7 SKIP (eval auto-skip). Coverage gate NA per T-2 A4 (test harness outside `--cov=src/modules` source). Architecture fitness 823/823 PASS preserved. `test_eval_runner_smoke.py` 4 scenarios + `test_skip_without_flag` (`@pytest.mark.no_eval`) opt-out for default-CI smoke validates gating mechanism end-to-end. |
| 13 | Mirror detection | PASS | Each new file in exactly 1 location: `find ... -name "{golden_loader,regenerate_golden,synthetic_tenant}.py"` → 1 match each. `grep -rn "^class GoldenSpec\b\|^def write_run_artifacts\|^def sanitize_payload"` → 1 canonical match each (`golden_loader.py:87`, `artifacts.py:52`, `sanitization.py:196`). PR.md "Existing systems audit" section §7 + §7.5 + IMPL-LOG Step 0 GATE all populated with grep evidence + paths + line numbers (verified live). Anti-duplication §0 satisfied. NEW classifications all justified (test-only DTOs / CLI / fixture; no shared abstraction candidate). |
| 14 | Default-flip side-effect coverage | NA | T-5 does not touch `core/config.py` defaults nor any feature-flag side-effect path. Verified by `git diff --name-only d5b7886a~1 d5b7886a` — zero `core/` or `shared/` paths. IMPL-LOG Step 0.5 explicit "N/A". |
| 15 | Decisions honored cite (R6) | NA | Ticket T-5 (`04-tickets.yaml:317`) does NOT set `decisions_applicable` field. R6 Cat 15 → NA. **Note (info):** despite NA status, builder voluntarily cited B2/B4/B5/B6/B7 in commit body + IMPL-LOG § "Decisions honored" with file:line evidence — exemplary practice. Verified verbatim cite for each: B2 `visionarias-smoke-golden.yaml:38,50` (offer_id hardcoded fail-explicit) · B4 `visionarias-smoke-golden.yaml:81-92` (forbidden_tools cited from `STAGE_TOOL_SCOPE` registry.py:56 — 11 names match dedup union) · B5 `assert_output` consumes `_detect_language_safe` lazy import T-4 chain (no top-level `langdetect` import in T-5) · B6 cache_hit_rate not measured (out-of-scope honored) · B7 `assert_voice_fidelity` not invoked (Story 7 placeholder honored). |

## Findings (file:line)

### FAIL

(none)

### WARN

- **[Cat 11 — DDD compliance / schema drift]** `backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml:38,50,73,82,107,111` — YAML uses flattened top-level keys (`tenant_id`, `offer_id`, `expected_specialists`, `must_mention`, `max_cost_usd`, `max_latency_ms`) instead of arch-be § "Golden YAML schema" prescribed nested structure (`tenant_id_env`, `expected_assertions: {trajectory, output, cost, latency}`). **Drift ratified upstream by T-4 audit** (Cat 11 WARN ack'd 5-place signature drift; CONTEXT-BRIEF was authoritative for builder). Builder consumed T-4 verbatim per IMPL-LOG § "Drift handling". **Forward-compatible** — T-5 future story expansion (Story 5 multi-tenant goldens) may continue with flat schema or upgrade to nested via thin wrapper without breaking existing assertions. → Recommendation: at /pm closure of S1, ratify the flat-schema decision in CONTRACT-equivalent doc (or Story 5 spec) to formally retire arch-be prescriptive nested schema. **No code change required** for T-5 merge.

### info

- **[Cat 11 — IMPL-LOG accuracy]** `T-5-impl-log.md:130` — IMPL-LOG describes Scenario 2 subprocess as using "`--collect-only` semantically (no fixture setup → no LLM call → no DB write)." Live read of `test_eval_runner_smoke.py:344-357` confirms subprocess does NOT pass `--collect-only`; instead it relies on `pytest_collection_modifyitems` auto-skip applied BEFORE fixture setup. Functionally equivalent (skip kicks in pre-setup); doc wording minorly inaccurate. **Non-blocking** — implementation correctness verified.
- **[Cat 15 — info]** `T-5-impl-log.md:188-194` — R6 NA but builder voluntarily cited 5 B-decisions with file:line evidence. Praiseworthy precedent for future agentic builders. Suggest Architect adds explicit `decisions_applicable: [B2, B4, B5, B6, B7]` to T-6 ticket (last in story) to test R6 enforcement at story closure.

## Cross-scope flags

(none — all paths inside agentic surface boundary `tests/agentic_evals/sales_agent/`)

## Skill routing — verification

| Required skill | Builder IMPL-LOG cite (line) | Score |
|---|---|---|
| `sales-agent-expert` | §"Skills consulted" line 28 | PASS |
| `copilot-expert` | §"Skills consulted" line 29 | PASS |
| `tessl__langgraph` | §"Skills consulted" line 30 | PASS |
| `tessl__graceful-degradation` | §"Skills consulted" line 31 | PASS |
| `tessl__pytest-api-testing` | §"Skills consulted" line 32 | PASS (extra) |

Builder skill routing **complete + over-spec'd** (added pytest-api-testing for subprocess + monkeypatch patterns). No "Skill routing violation" trigger.

## Research notes (date-aware)

No novel pattern introduced in T-5 — pure consumer ticket. Validation against live canonical docs:

- LangChain Callbacks (`https://python.langchain.com/docs/modules/callbacks/`) accessed conceptually — `BaseCallbackHandler` composition via `RunnableConfig.callbacks` list confirmed canonical pattern. Spy reuses T-3 pattern audit-ratified.
- Anthropic prompt caching not measured in T-5 (Story 7 scope per Decision B6) — no live verification needed.
- LangGraph 2.0 supervisor + StateGraph patterns inherited verbatim from existing sales_agent graph (no T-5 modifications).

**Knowledge cutoff disclosure:** Opus 4.7 cutoff Jan 2026; live researched on 2026-05-06. Reference anchors in agent definition match live behavior — no delta detected.

## Recommendations for builder fix-loop

(none — APPROVED; T-5 ready for orchestrator → /pm Wave 5 closure)

Optional follow-ups (deferred to Story 5+ scope, NOT blocking T-5):

1. Architect-level: ratify flat YAML schema as canonical in S1 closure doc OR Story 5 multi-tenant golden spec — close arch-be drift formally.
2. Builder-level (T-6 prefix): consider extracting fixture-free unit test for Scenario 3 (degraded output) since LLM is monkeypatched, decoupling from `visionarias_tenant_session` brain-UP precondition. **Conditional on /pase-produccion validation** — if A3 passes brain-UP run, extraction is cosmetic.
3. Architect (T-6): add `decisions_applicable: [B2, B4, B5, B6, B7]` to T-6 ticket so R6 Cat 15 enforcement triggers — exercises closure at story-end.

## Drift detection (CONTRACT vs code)

**YES — Cat 11 WARN above:** YAML schema flat vs arch-be nested. Drift ratified upstream by T-4 audit (CONTEXT-BRIEF was authoritative). T-5 builder honored brief faithfulness; arch-be prescriptive blocks were illustrative scaffolding. Same drift pattern as T-4. **Documented + non-blocking; @pm aware via T-4 review § "Drift detection".**

## Deferred acceptance verification (judgment call)

Per gate-output `deferred_acceptance_chain` field + IMPL-LOG § "Acceptance criteria — verifier outcomes":

A1, A3, A4, A5 share `visionarias_tenant_session` fixture pre-condition (brain UP + Visionarias DB seeded). T-2 audit ratified the skip-explicit pattern. Auditor verifies static implementation correctness:

- **A1** (`test_smoke_multi_layer`): all 5 assertion layers wired in sequence with try/except → write_run_artifacts → re-raise pattern (lines 196-279). Capa 4 `assert_cost_recorded` correctly skips if `turn_id is None` per fixture contract (lines 241-245). PASS compositionally.
- **A3** (`test_degraded_output_caught`): `monkeypatch.setattr(MultiRoleLLMRouter, "generate_response", _degraded_response)` patches canonical router seam (verified `factory.py:46` returns MultiRoleLLMRouter instance; specialists call via this). `assert_output` correctly catches missing must_mention "Visionarias" in "ok" response → `OutputAssertionError` raised; layer_name == "output"; assertions.json artifact contains `"failed_layer_name"` + `"output"` substring. Sound logic. PASS compositionally.
- **A4** (`test_no_cross_tenant_leak`): `synthetic_tenant` fixture seeds T2 alongside Visionarias via `seed_t2_synthetic_tenant_with_offer`. Agent invoked with Visionarias tenant_id. Post-invoke query `SELECT DISTINCT tenant_id FROM sales_agent_trace_event WHERE turn_id = ?` asserts == `{visionarias_id}`. trace.json substring `"T2_synthetic"` ABSENT (sanitize_payload chain). Defense-in-depth response.txt check. PASS compositionally.
- **A5** (`regenerate_golden.py --dry-run`): brain-UP exits 0 with diff or "sin cambios"; brain-DOWN exits 1 with explicit Spanish stderr (`"verifica que Postgres este corriendo"`). Per ticket A5 spec `"uses DB connection — SKIP if brain DOWN"` accepts both modes (graceful-degradation Rules 1+2). PASS compositionally.

**Acceptance verdict:** all 6 acceptance criteria satisfied via static + compositional verification. Real-LLM execution (A1+A3+A4) verifiable post-`/pase-produccion` brain-UP run. Auditor judgment: **acceptable for T-5 close** — pattern ratified by T-2 audit precedent (skip-explicit fixture binding). The deferred chain does NOT block S1 closure; it gates real-LLM smoke validation, which happens during /pase-produccion as documented.

## T-2 forward-fill scrutiny

Builder created `synthetic_tenant.py` in T-5 commit. Per 04-tickets.yaml T-2 deliverable (line 22), the file was originally T-2 scope but T-2 commits did NOT include it (verified IMPL-LOG § "Drift handling — T-2 drift"). Builder per parallel-safety.md M8 ("extend, not destroy") materialized the canonical implementation in T-5 since Scenario 4 (A4 acceptance) requires it.

**Auditor verdict:** acceptable forward-fill, NOT scope creep. Justifications:
- M8 rule honored (extend ajenos when stuck-blocked; documented in IMPL-LOG with grep evidence)
- File creation backfills T-2 deliverable spec (matches signature `seed_t2_synthetic_tenant_with_offer(db) → dict`)
- Idempotent upsert with deterministic UUIDs (`...0000a2`, `...0000b2`) — never collides with Visionarias default `...0000001`
- Re-export path consistent (`fixtures/__init__.py` + `conftest.py`)
- Defensive skip if Visionarias UUID coincides with synthetic UUID (paranoia layer)
- Anti-duplication §0 satisfied (zero src/ touch, reuses production TenantModel + ProductModel + utc_now)

The forward-fill is documented for downstream awareness. **No regression.** Recommend `/pm` mark T-2 retroactively as "completed via T-5 forward-fill" in checkpoint to close the bookkeeping gap.

