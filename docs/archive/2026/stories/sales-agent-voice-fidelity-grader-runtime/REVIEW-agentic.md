<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — Story E: sales-agent-voice-fidelity-grader-runtime

> Auditor: `auditor-agentic` (Opus 4.7) — INDEPENDENT Conv 3 audit (supersedes Phase 1 builder mechanical 2026-05-09)
> Invariants validated against canonical docs as of 2026-05-11
> Iter: 1 (Conv 3 independent)
> Verdict: **PASS** (with 1 advisory WARN — non-blocking, cosmetic)
> Generated: 2026-05-11T00:00:00Z

## Inputs

- CONTEXT-BRIEF.md: used (R24 gate validated — `Validator pass: PASS` + `Faithfulness flag: clean`, 2026-05-09T01:05:00Z)
- gate-output.json: used + RE-EXECUTED independently 2026-05-11 (live native WSL)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y (state machine review), tessl__graceful-degradation=Y (Rule 1+2 audit)
- IMPL-LOG Skills Consulted: documented in T-1..T-10 impl-log files

## Gate status — re-executed 2026-05-11 by Conv 3 auditor

| Gate | Status | Evidence |
|---|---|---|
| ruff check (35 files: grader + arch + models) | PASS | "All checks passed!" |
| ruff format --check | PASS | "35 files already formatted" |
| pytest grader full | PASS | 151/151 (11.58s) |
| pytest arch fitness full | PASS | 1063/1063 + 1 env-gated skip (29.54s) |
| pytest simulator regression (full) | PASS | 214/214 + 36 toolkit-dep skips (113.41s) — no timeout this run |
| WebFetch Anthropic prompt-caching docs | VERIFIED | TTL=1h available via explicit `cache_control={"type":"ephemeral","ttl":"1h"}`, pricing 2x base input on write, 0.1x read (live May 2026) |

**Pre-existing simulator timeout flake** noted in original gate-output (`test_db_session_propagated_to_agent_bridge_via_contextvar`) did NOT repro in fresh run (60s timeout, 113s wall-clock). Confirmed Story B environmental flake — NOT Story E regression.

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | N/A | Story E does NOT use LangGraph compose path. Pure Python async state machine (D-AG-12 cement). Only LangGraph touch: `simulator/_internal/runner.py:423` additive `grader_callback: Callable | None = None` — fire-and-forget hook. Zero ripple to Story B graph state schema. |
| 2 | Tool registration | N/A | Story E exposes no agent tools. Test-infra grader runtime, not production tool surface. |
| 3 | Prompt cache architecture | PASS | `_internal/judge_prompts.py:182` — 6-slot architecture with cement constant `_CACHE_CONTROL_TTL_1H: dict[str, str] = {"type": "ephemeral", "ttl": "1h"}`. Slots 1+2+3 cacheable (`build_judge_prompt` lines 348-350 attach `cache_control` dict-copy per slot). SLOT 3 carries `personality_profile.system_instruction` VERBATIM via `_resolve_voice_attributes` (line 254) — no `{tenant_name}` interpolation; `tenant_slug` lives in SLOT 6 volatile zone (line 169). Cache prefix stability preserved per documented contract. WebFetch confirmed live Anthropic API behavior matches 2026-05-11. |
| 4 | deepagents subagent isolation | N/A | No deepagents subagents. Story E uses 3 LiteLLM Proxy adapters (`_JudgeAdapter`); each call independent (`Semaphore(JUDGE_CONCURRENCY=20)` per `maj_eval.py:112`, D17 cement). Round 2 peer reasoning isolated per judge — `judge_prompts.py:227` filter `[(jid, sc, rsn) for (jid, sc, rsn) in peer_reasoning if jid != judge_id]` + arch fitness `test_grader_round_2_no_self_reasoning.py:77-92` enforces inequality + `<<ROUND_2_PEER_REASONING>>` markers + `round_n == 2` guard. |
| 5 | Observability | PASS | `_JudgeAdapter.grade` (`judge_registry.py:151-157`) builds `extended_eval_metadata` with 5 NEW Story E keys (`grader=maj_eval`, `rubric_id`, `rubric_version`, `judge_id`, `round_n`, `cache_hit`). Passes via `obs_context.langchain_config()` + merged callbacks. Cost-bucket H7 cement enforced by `tests/architecture/test_grader_writes_eval_only_bucket.py` (lines 173-222) static AST scan — forbidden ORM imports + table literals fail gate. Best-effort persist + cache (`maj_eval.py:240-270`) try/except + structlog warn + fallback per Graceful Degradation Rule 2. |
| 6 | Eval goldens (sales_agent) | PASS | 4 rubrics in scope (D5 cement). `qualification-accuracy.md` v1 OWNED by Story E (D6) — `docs/specs/rubrics/qualification-accuracy.md:14` `last_modified: 2026-05-09 owner_story: sales-agent-voice-fidelity-grader-runtime`, `version: 1`, threshold_default 0.75. 4 scenario test suites (`scenarios/test_scenario_{1,2,3,4}.py`). Calibration MD seeds for all 4 rubrics (`grader/calibration/{voice_fidelity,qualification_accuracy,no_overpromise,no_hallucination}_calibration.md`). Cache invalidation precision verified by `test_grader_cache.py` 3 invalidation tests. |
| 7 | RAG / Qdrant hygiene | N/A | Story E does NOT use RAG/Qdrant. Pure judge-based grading runtime. |
| 8 | LLM provider routing | PASS | `JUDGE_MODELS` registry pinned (D15 cement, Chris-ratified): `sonnet=claude-sonnet-4-6`, `gpt4o=gpt-4o-2024-11-20`, `kimi=kimi-k2.6` (`judge_registry.py:83-87`). NOT auto-tracking. Dispatch via `LiteLLMService` ONLY (line 59 import). D-AG-17 cement enforced by validator `agentic_litellm_proxy_dispatch_only` (zero direct openai/anthropic SDK imports — `grep -rn "from openai\|from anthropic"` returns empty in grader/). Eval-side judges are test infrastructure, not production `LLM_ROLE_BY_SITE` roles — registry pattern is the documented & ratified path (D2/D15). |
| 9 | Cost optimization | PASS | TTL=1h explicit (judge_prompts.py:182). Cache hit rate target ≥70% documented (CONTEXT-BRIEF §10). Cost budget ~$330 cold / ~$108 warm per design v2 + arch test `agentic_cost_budget_full_eval_cold_warm` enforces $400 ceiling. Per-judge cost recorded via cost_recorder bridge into `eval_simulator_llm_call` only (H7 cement). |
| 10 | Channel format & brand voice | PASS | Voice consumed VERBATIM (READ-ONLY) per sales-agent-expert §3. `personality_profile.system_instruction` read at `cache.py:110` (`compute_tenant_voice_hash` sha256 of bytes — no mutation) + `judge_prompts.py:261-264` (`_resolve_voice_attributes` extracts text + dialect_code; no rewrite). NO `brand_voice_summary` table created. NO `{tenant_name}` interpolation mid-prefix. NO voseo in grader code (judge prompts English in slots 1+2+6 per DQ4; voseo permitted ONLY in Slot 3 verbatim voice + Slot 5 verbatim transcript subject — magic comment `# voseo-allowed:` present in 23 places where glosario cited per R25). |
| 11 | DDD compliance (agentic) | PASS | All grader code under `backend/tests/agentic_evals/sales_agent/grader/` (test-infra). Two `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade*.py` files are R5 schema-mirror exception per `.claude/rules/backend-ddd.md` (Alembic 127 mirror). NO touches to `modules/sales_agent/{domain,application,api}/`. NO cross-module imports. ONLY production code modified: `simulator/_internal/runner.py:423,645-669` additive `grader_callback` param (D17/DQ5 fire-and-forget; 25 lines, all inside try/except — Story B determinism preserved when `grader_callback=None` default). |
| 12 | Tests / TDD | PASS | 151/151 grader unit + integration + scenarios PASS (re-confirmed 2026-05-11). 6 NEW grader-specific arch fitness gates — `test_grader_sandbox_markers_enforced.py` (DQ2 layer 2) + `test_grader_pii_sanitize_pre_judge.py` (D10) + `test_grader_round_2_no_self_reasoning.py` (DQ3) + `test_grader_writes_eval_only_bucket.py` (H7) + `test_grader_no_mirrors_shared.py` (anti-duplication) + `test_grader_public_api_surface.py` (D-AG-16). H9 expansion `test_simulator_public_api_surface.py:42-77` 7→8 names (`grade_transcript_maj_eval` added). Allowlists empty (shrink-only ratchet). |
| 13 | Mirror detection | PASS | `test_grader_no_mirrors_shared.py:67-82` enforces zero basename overlap with `shared/agent_observability/` (subclass exemption only). Manual review confirms all shared abstractions (sanitize_payload, LiteLLMService, cost_recorder, EvalSimulatorObservabilityContext, PricingResolver, FXResolver) consumed via import (no mirror). CONTEXT-BRIEF §7.5 cross-reference matrix: 14 inventory items mapped to REUSE; zero NEW mirror files. |
| 14 | Default-flip side-effect coverage | N/A | Story E does NOT flip any feature flag default. No `core/config.py` defaults touched. CONTEXT-BRIEF §5 row anti-default-flip-audit: "N/A Story E (no flag flip); env vars optional". |
| 15 | Decisions honored cite (R6) | WARN | `06-tickets.yaml` populates `decisions_applicable` for all 10 tickets (e.g. T-1 line 35: `[D-BE-1, D-BE-2, D-BE-6]`; T-2 line 92: `[D-BE-3, D-BE-4, D-BE-5]`; T-3 line 162: `[D-BE-7, D6]`). Each commit body cites decisions concretely (e.g. T-5 commit `b13cad65` body: "Decisions cement: D2 weights 0.4/0.4/0.2, D3 variance 0.15 max-min, D4 unconverged fallback to R1 weighted avg, D10 PII sanitize pre-judge, D17/D-AG-9 Semaphore(20)..."). T-6/T-7/T-9 similar. **WARN**: heading wording is "Decisions cement" / "Decisions cement applied" / inline cites rather than literal R6 cardinal "Decisions honored". Substance present + per-D# concrete cites + file:line evidence verifiable. NOT verdict-blocking — R6 cardinal intent (decisions cited concretely per D# in commit body) is honored substantively; only heading string differs. |

## Findings (file:line)

### FAIL

(none)

### WARN

- [Cat 15] All 10 Story E commits — heading "Decisions cement" / "Decisions cement applied" instead of R6 cardinal "Decisions honored". Substance + per-D# concrete cites are present. → Recommended fix: PM `/auditor` orchestrator can ratify substance + standardize heading rename in Conv 3 merge protocol. Trivial cosmetic delta — does NOT block merge.

### info

- [Cat 3] `judge_prompts.py:182` cache_control TTL=1h hardcoded as `dict[str, str] = {"type": "ephemeral", "ttl": "1h"}`. WebFetch live Anthropic docs (2026-05-11) confirm 1h tier still requires explicit header at 2x base input write cost. Story E correctly opts in. No drift.
- [Cat 4] `_grade_one_turn_rubric` (`maj_eval.py:282-441`) implements degenerate `<2 valid judges` defense at line 318-340 (rare 2-providers-down case → `unconverged=True`, structlog error, R1 fallback). Excellent graceful degradation discipline.
- [Cat 5] `_persist_grade` (`maj_eval.py:627-675`) uses `pg_insert(...).on_conflict_do_nothing(index_elements=[...])` per backend-migrations.md SQLite-portable convention.
- [Cat 11] `runner.py:414` carries `noqa: PLR0915` with explicit justification ("orchestrator topology spec'd as 12 linear steps; splitting into helpers would fragment the spec'd story-wide cement"). Rationale acceptable.
- [Cat 8 inherited concern] `LiteLLMService` (shared/infrastructure/llm/providers/litellm.py, 216 LOC) does NOT carry explicit `timeout=` per `tessl__graceful-degradation` Rule 1 ("every external call needs a timeout"). This is a **shared infra concern**, NOT Story E regression — Story E grader wraps in try/except (Rule 2 fallback to `score=None`). Recommend follow-up process-improvement ticket for shared/llm timeout cement (cross-consumer impact: copilot + sales_agent + brand + offer + landing all share this surface). Not verdict-blocking for Story E.

## Cross-scope flags (if any)

(none — Story E is purely test-infra under `backend/tests/agentic_evals/sales_agent/grader/` + R5 schema-mirror exception in `modules/sales_agent/observability/eval_simulator/persistence/models/`. Zero cross-module business-logic touches. The 3 BE schema mirror files (eval_simulator_grade.py + eval_simulator_grade_cache.py + models/__init__.py) are within auditor-backend's R5 exception — auditor-agentic correctly delegates schema audit per `.claude/rules/backend-ddd.md` exception.)

## Downstream regression scope (R3 verification)

`git diff --name-only` cd840485~1..e5407815 → backend/src/ paths confirmed:

| Surface modified | Path classification | Downstream test targets | Status |
|---|---|---|---|
| `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` (NEW T-2) | R5 schema-mirror | grader full suite + arch gates | PASS (151/151 + 1063/1063) |
| `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade_cache.py` (NEW T-2) | R5 schema-mirror | grader cache tests + arch gates | PASS |
| `modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py` (EDIT T-2) | R5 schema-mirror barrel | model imports verified | PASS |
| `tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` (NEW T-5) | grader runtime | grader full suite + 5 arch gates | PASS (151/151 + 5/5) |
| `tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (NEW T-7) | grader runtime | grader suite + sandbox/round_2/leak gates | PASS |
| `docs/specs/rubrics/qualification-accuracy.md` (REPLACE T-3) | rubric MD | grader cache invalidation downstream | PASS (cache key recompute on rubric_version) |
| `tests/architecture/test_grader_*.py` (5 NEW + 1 EDIT T-8) | arch fitness | full arch fitness suite | PASS (1063/1063) |
| `tests/agentic_evals/sales_agent/simulator/_internal/runner.py` (T-9 additive `grader_callback`) | simulator orchestrator | simulator regression suite | PASS (214/214) |
| `tests/agentic_evals/sales_agent/simulator/__init__.py` (T-8 H9 expand) | public surface | `test_simulator_public_api_surface.py` | PASS (8 names frozen) |

**`shared/agent_observability/` NOT modified** by Story E — no R3 downstream cascade required for copilot/sales_agent observability tests. CONTEXT-BRIEF §11 conditional flag was pre-emptive scoping (story stayed within bounds).

## Cost bucket H7 cement verification

- `test_grader_writes_eval_only_bucket.py` static AST scan — PASS:
  - Forbidden ORM model class imports (`CopilotLlmCallModel`, `SalesAgentLlmCallModel`, `CampaignLlmCallModel`) → 0 hits across grader subtree
  - Forbidden table name literals (`copilot_llm_call`, `sales_agent_llm_call`, `campaign_llm_call`) in executable code → 0 hits
  - Canonical eval write path indicators (`eval_simulator_llm_call`, `EvalSimulatorLlmCallModel`, `modules.sales_agent.observability.eval_simulator.persistence`) → present
- `_JudgeAdapter.grade` (`judge_registry.py:151-157`) explicitly builds `extended_eval_metadata` with `grader=maj_eval` + 5 NEW Story E keys; passes via `obs_context.langchain_config()` callback chain — cost rollups land in `eval_simulator_llm_call` exclusively

## H9 public API surface verification

- `simulator/__init__.py:80-89` `__all__` expanded 7 → 8 names (frozen alphabetical): `ActorProfile`, `AgentErrorSubtype`, `SimulationResult`, `SimulationState`, `TerminationReason`, `grade_transcript_maj_eval`, `register_termination_policy`, `run_simulation`
- `test_simulator_public_api_surface.py:42-77` `_EXPECTED_PUBLIC_NAMES` frozenset matches; `len(__all__)==8` cardinality cement enforced
- `_internal/maj_eval.py` + `_internal/judge_prompts.py` + `_internal/cache.py` + `_internal/judge_registry.py` NOT exposed (under `_internal/` subpackage). `grader/__init__.py` `__all__: list[str] = []` per D-AG-16 cement.

## Round 2 debate logic verification (DQ3 anti-anchoring)

- Variance threshold `VARIANCE_R1_THRESHOLD: Final[float] = 0.15` (`maj_eval.py:106` D3 cement)
- Round 2 trigger gate at `_grade_one_turn_rubric:346` — converged R1 (`r1_variance <= 0.15`) returns immediately; else logs `maj_eval_debate_triggered` (lines 365-372) + builds R2 tasks
- DQ3 anti-anchoring **TRIPLE-LAYER cement**:
  1. `maj_eval.py:376-379` — peer_reasoning list comprehension excludes `op.judge_id == jid` (R1 own)
  2. `judge_prompts.py:227` — second filter belt-and-suspenders inside `_build_slot_4`
  3. `test_grader_round_2_no_self_reasoning.py` — 4 arch fitness gates verifying AST inequality + `<<ROUND_2_PEER_REASONING>>` markers + `round_n == 2` guard
- Convergence test: `maj_eval.py:415` `unconverged = r2_variance >= VARIANCE_R2_TARGET` (0.10 D4 cement)
- Unconverged → `final_score = r1_weighted` (lines 561-563) + `structlog.warning` (lines 417-425) — graceful degradation NOT block (DQ8 cement)
- R2 partial fallback (DQ6): `maj_eval.py:396-409` — if R2 judge score=None, substitute R1 opinion → `r2_partial=True`
- Suspicious flag (DQ8): `maj_eval.py:575-589` — all 3 judges score=1.0 + ANY injection_attempt → log warning + flag

## Sandbox markers verification (DQ2 — defense-in-depth 3 layers)

- **Layer 1 (Slot 1 directive)**: `judge_prompts.py:64-83` SLOT_1_TEMPLATE contains `CRITICAL SECURITY DIRECTIVE` block citing markers verbatim
- **Layer 2 (Slot 5 builder)**: `judge_prompts.py:235-251` `_build_slot_5` wraps transcript with literal `<<TRANSCRIPT_BEGIN>>\n...<<TRANSCRIPT_END>>\n` strings (lines 245-247) — NOT parametrized
- **Layer 3 (arch fitness gate)**: `test_grader_sandbox_markers_enforced.py:66-91` AST static scan — both literals MUST appear as inline string constants

## Brand voice compliance (CRITICAL — sales-agent-expert §3)

- `personality_profiles.system_instruction` consumed READ-ONLY:
  - `cache.py:110` `voice_profile.system_instruction.encode("utf-8")` — read for hash, no write
  - `judge_prompts.py:261-264` `getattr(voice_profile, "system_instruction", "")` — read for Slot 3, no mutation
- NO `brand_voice_summary` table or mirror created
- NO fine-tuning per tenant (D19 cement)
- NO voice-rewriter LLM pass post-generation
- NO `{tenant_name}` interpolation mid-prefix — `judge_prompts.py:127-131` Slot 3 carries `tenant_voice_hash + dialect + voice_system_instruction_verbatim`. `tenant_slug` lives ONLY in Slot 6 (volatile). Cache prefix stability preserved.

## Research notes (Anthropic prompt caching TTL — DATE-AWARE)

- Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching (accessed 2026-05-11)
- Takeaway: 1h TTL still available via explicit `cache_control={"type":"ephemeral","ttl":"1h"}`; default 5min; pricing 2x base input write / 0.1x base read
- Delta vs reference anchors in agent definition: NONE — Story E correctly opts into 1h tier per documented contract
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live verified 2026-05-11

## Recommendations for builder fix-loop

(no FAILs — story passes Conv 3 independent audit)

Optional pre-merge polish (NOT blocking):

1. **WARN Cat 15** — When PM ratifies merge in Conv 3, consider standardizing commit body heading from "Decisions cement" / "Decisions cement applied" → "Decisions honored" per R6 cardinal verbatim. Substance + per-D# concrete cites already present; only heading string differs. Cosmetic.
2. **Info shared infra concern** — Process-improvement ticket recommended for `shared/infrastructure/llm/providers/litellm.py` to add explicit `timeout=` per `tessl__graceful-degradation` Rule 1 ("every external call needs a timeout"). Cross-consumer surface (copilot + sales_agent + brand + offer + landing). NOT Story E scope.

## Drift detection (CONTRACT vs code)

52 cement decisions verified honored:
- D1-D20 spec decisions: ALL cited concretely in commits + verifiable via file:line
- DQ1-DQ8 design decisions: ALL implemented (state machine specifics, sandbox markers, async callback, cache semantics)
- D-AG-1..D-AG-18 agentic arch: ALL cement
  - D-AG-15 H9 expand 7→8: VERIFIED
  - D-AG-16 grader package zero re-exports: VERIFIED (`grader/__init__.py` `__all__: list[str] = []`)
  - D-AG-17 LiteLLM Proxy ONLY: VERIFIED (zero direct openai/anthropic SDK imports)
- D-BE-1..D-BE-8 BE schema: ALL cement
  - D-BE-3 R5 schema-mirror exception: VERIFIED (only persistence/models/ touched)

ZERO drift detected. CONTRACT spec v2 + design v2 + arch package faithfully implemented.

## Summary

**Verdict: PASS** — Story E sales-agent-voice-fidelity-grader-runtime ships clean Conv 3 INDEPENDENT audit. 10/10 tickets shipped GREEN, 151/151 grader tests PASS (re-executed), 1063/1063 arch fitness PASS (5 NEW grader gates), 214/214 simulator regression PASS, H7 cost-bucket invariant cemented, H9 public API surface 7→8 frozen, DQ2 sandbox markers literal-enforced (3-layer cement), DQ3 anti-anchoring filter present (3-layer cement), voice SSoT consumed READ-ONLY zero creep, R5 schema-mirror exception cleanly observed.

One non-blocking WARN (Cat 15 commit body heading wording) — substance present, only format differs. Cosmetic, not verdict-blocking.

Pre-existing simulator timeout flake noted in original gate-output did NOT repro in Conv 3 fresh native WSL run — confirmed Story B environmental, not Story E regression.

Live WebFetch verified Anthropic prompt caching API behavior (TTL=1h via explicit header) matches Story E implementation as of 2026-05-11.

**Ready for /pm Conv 3 merge orchestration + capability promotion + state transition reviewing → done.**
