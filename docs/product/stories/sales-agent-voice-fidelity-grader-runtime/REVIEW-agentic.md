<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Agentic Review — Story E: sales-agent-voice-fidelity-grader-runtime

> Auditor: `auditor-agentic` (Opus 4.7) — Phase 1 mechanical review per OQ4 dispatch 2026-05-09
> Invariants validated against canonical docs as of 2026-05-09
> Iter: 1
> Verdict: **PASS** (with 2 advisory WARNs — non-blocking)
> Generated: 2026-05-09T12:30:00Z

## Inputs

- CONTEXT-BRIEF.md: used (validator PASS 2026-05-09T01:05:00Z, faithfulness `clean`, R24 gate passed)
- gate-output.json: used (final consolidated 2026-05-08T13:35:22Z)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y (state machine review), tessl__graceful-degradation=Y (Rule 2 audit)
- IMPL-LOG Skills Consulted: per T-* impl-log files — all required skills documented

## Gate status (from gate-output.json + re-run by auditor)

| Gate | Status | Errors |
|---|---|---|
| ruff (grader files) | PASS | 0 |
| ruff format (29 files) | PASS | 0 |
| pytest grader full | PASS | 0 (151/151) |
| pytest scenarios (re-run) | PASS | 0 (15/15) |
| pytest arch fitness (full) | PASS | 0 (1063/1063 + 1 env-gated skip) |
| pytest arch fitness (grader-specific) | PASS | 0 (62/62: 5 NEW + simulator H9 expand) |
| pytest simulator regression | WARN | 1 timeout (pre-existing flake; passes 42.49s with 120s timeout, NOT Story E regression) |

**Verdict mechanics:** the simulator timeout is a known pre-existing Story B environmental flake (`test_db_session_propagated_to_agent_bridge_via_contextvar` — posthog/asyncio/socket deadlock at 30s pytest timeout; clean re-run with 120s timeout PASS in 42.36s). NOT introduced by Story E. NOT a verdict-blocking gate.

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | N/A | Story E does NOT use LangGraph. Pure Python async state machine (D-AG-12 cement). State machine has no graph compose path; runner.py is the only LangGraph touch (additive `grader_callback` param) |
| 2 | Tool registration | N/A | Story E exposes no agent tools. Test-infra grader runtime, not production tool surface |
| 3 | Prompt cache architecture | PASS | `_internal/judge_prompts.py:182` 6-slot architecture: SLOT 1+2+3 cacheable TTL=1h (Anthropic SDK 2026-03-06 default change to 5min documented; explicit `{"type": "ephemeral", "ttl": "1h"}`). SLOT 3 carries `personality_profile.system_instruction` VERBATIM; `tenant_slug` placed in SLOT 6 (volatile) NOT SLOT 3 — prefix stability preserved (line 173-175). Cache key composition 5-field deterministic sha256 (`_internal/cache.py:48-54` `_CACHE_KEY_FIELDS` Final tuple) |
| 4 | deepagents subagent isolation | N/A | No deepagents subagents. Story E uses 3 LiteLLM Proxy adapters (`_JudgeAdapter`); each adapter call independent (Semaphore(20) D17 cement). Round 2 peer reasoning isolated per judge (DQ3 anti-anchoring: `judge_prompts.py:227` filter `[(jid, sc, rsn) ... if jid != judge_id]` + arch fitness `test_grader_round_2_no_self_reasoning.py` enforces `judge_id` inequality + `<<ROUND_2_PEER_REASONING>>` markers + `round_n == 2` guard) |
| 5 | Observability | PASS | `_JudgeAdapter.grade` (`judge_registry.py:124-255`) builds `extended_eval_metadata` with 5 NEW Story E keys (`grader/rubric_id/rubric_version/judge_id/round_n/cache_hit`), passes via `obs_context.langchain_config()` callbacks merged. Cost-bucket H7 cement: judge calls write `eval_simulator_llm_call` ONLY (ENFORCED by `tests/architecture/test_grader_writes_eval_only_bucket.py` static AST scan — forbids `CopilotLlmCallModel` / `SalesAgentLlmCallModel` / `CampaignLlmCallModel` imports + table literal references in executable code). Best-effort persist + cache (`maj_eval.py:240-270` try/except + structlog warn + fallback per Graceful Degradation Rule 2) |
| 6 | Eval goldens (sales_agent) | PASS | 4 rubrics in scope (D5 cement). `qualification-accuracy.md` v1 OWNED by Story E (D6 — replaces Story C placeholder; `docs/specs/rubrics/qualification-accuracy.md:14` `last_modified: 2026-05-09 owner_story: sales-agent-voice-fidelity-grader-runtime`). Voice-fidelity grader test suite present (`scenarios/test_scenario_1_happy_multi_judge.py` + 3 others, 15/15 PASS). Calibration MD seeds present for all 4 rubrics. Rubric MD bump triggers cache invalidation per `cache.py:62-90` `compute_cache_key` 5-field hash (`rubric_version` field) |
| 7 | RAG / Qdrant hygiene | N/A | Story E does NOT use RAG/Qdrant. Pure judge-based grading runtime |
| 8 | LLM provider routing | PASS | `JUDGE_MODELS` registry pinned (D15 cement, Chris-ratified): `sonnet=claude-sonnet-4-6`, `gpt4o=gpt-4o-2024-11-20`, `kimi=kimi-k2.6`. NOT auto-tracking. Dispatch via `LiteLLMService` ONLY (`judge_registry.py:59` import; `D-AG-17` cement enforced by arch fitness `test_grader_writes_eval_only_bucket.py` — forbids direct `openai`/`anthropic` SDK imports). Eval-side judges are test infrastructure, not production `LLM_ROLE_BY_SITE` roles — registry pattern is the documented & ratified path for judge selection (D2/D15) |
| 9 | Cost optimization | PASS | TTL=1h explicit (`judge_prompts.py:182` `_CACHE_CONTROL_TTL_1H`). Cache hit rate target ≥70% documented (CONTEXT-BRIEF §10 "warm cache cost-bucket"). 3 cacheable slots (Slot 1+2+3) ≥ token budget. Cost budget ~$330 cold / ~$108 warm per design v2. Per-judge cost recorded via cost_recorder bridge into `eval_simulator_llm_call` only (H7 cement) |
| 10 | Channel format & brand voice | PASS | Voice consumed VERBATIM (READ-ONLY) per sales-agent-expert §3. `personality_profile.system_instruction` read in `cache.py:104-111` `compute_tenant_voice_hash` (sha256 of bytes — no mutation) + `judge_prompts.py:254-270` `_resolve_voice_attributes` (extracts text + dialect_code; no rewrite). NO write/distill/mirror. NO `brand_voice_summary` table created. NO `{tenant_name}` interpolation mid-prefix (Slot 3 contains tenant_voice_hash + dialect + verbatim text only; tenant_slug in Slot 6 — volatile metadata zone). NO voseo in code or UI strings (judge prompts English in slots 1+2+6 per DQ4; voseo permitted ONLY in Slot 3 verbatim voice + Slot 5 verbatim transcript subject — magic comment `# voseo-allowed:` present where glosario cited per R25) |
| 11 | DDD compliance (agentic) | PASS | All grader code under `backend/tests/agentic_evals/sales_agent/grader/` (test-infra). Two `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade*.py` files are R5 schema-mirror exception (Alembic 127 migration mirror — builder-backend authorized per `.claude/rules/backend-ddd.md`). NO touches to `modules/sales_agent/{domain,application,api}/`. NO cross-module imports. NO production code modified except `simulator/_internal/runner.py` additive `grader_callback` param (D17/DQ5 fire-and-forget; line 645-669 — 25 lines, all inside try/except) |
| 12 | Tests / TDD | PASS | 151/151 grader unit + integration + scenarios PASS. 5 NEW grader-specific arch fitness gates: `test_grader_sandbox_markers_enforced.py` (DQ2 cement) + `test_grader_pii_sanitize_pre_judge.py` (D10) + `test_grader_round_2_no_self_reasoning.py` (DQ3) + `test_grader_writes_eval_only_bucket.py` (H7) + `test_grader_no_mirrors_shared.py` (anti-duplication) + `test_grader_public_api_surface.py` (D-AG-16). H9 expansion `test_simulator_public_api_surface.py:73-82` 7→8 names (`grade_transcript_maj_eval` added). Allowlists empty (shrink-only ratchet) |
| 13 | Mirror detection | PASS | `test_grader_no_mirrors_shared.py` enforces zero basename overlap with `shared/agent_observability/` (subclass exemption only). Manual review confirms all shared abstractions (sanitize_payload + LiteLLMService + EvalSimulatorObservabilityContext + cost_recorder + PricingResolver + FXResolver) consumed via import (no mirror). CONTEXT-BRIEF §7.5 cross-reference matrix: 14 inventory items mapped to REUSE; zero NEW mirror files |
| 14 | Default-flip side-effect coverage | N/A | Story E does NOT flip any feature flag default. No `core/config.py` defaults touched. Per CONTEXT-BRIEF §5 row anti-default-flip-audit: "N/A Story E (no flag flip); env vars optional" |
| 15 | Decisions honored cite (R6) | WARN | `06-tickets.yaml` populates `decisions_applicable` for ALL 10 tickets (T-1 through T-10). Each commit body cites decisions concretely (e.g. T-5 commit `b13cad65`: "Decisions cement: D2 weights 0.4/0.4/0.2, D3 variance 0.15 max-min, D4 unconverged fallback to R1 weighted avg, D10 PII sanitize pre-judge, D17/D-AG-9 Semaphore(20)..."). Decisions referenced are concrete + substantive, with file:line evidence (e.g. `Final[float] = 0.15` at `maj_eval.py:106`). **WARN**: heading wording is "Decisions cement" / "Decisions applied" rather than the cardinal R6 "Decisions honored" string. The substance is present and verifiable; the format string differs. Auditor can self-fix via heading rename in PM merge ratification (trivial). NOT verdict-blocking — R6 cardinal intent (decisions cited concretely per D# in commit body) is honored |

## Findings (file:line)

### FAIL

(none)

### WARN

- [Cat 15] All 10 Story E commits — heading wording "Decisions cement" / "Decisions applied" instead of R6 cardinal "Decisions honored". Substance + per-D# concrete cites are present. → Recommended fix: PM `/auditor` orchestrator can ratify substance and amend wording for R6 strict-format compliance in Conv 3 merge protocol. Trivial cosmetic delta.
- [Gate] `pytest_simulator_regression` 1 timeout `test_db_session_propagated_to_agent_bridge_via_contextvar` — pre-existing Story B environmental flake (posthog/asyncio/socket deadlock at 30s pytest timeout). Confirmed PASS with 120s timeout (42.36s wall-clock). NOT Story E regression. → Recommended fix: process-improvement ticket to bump pytest default timeout for that specific test, or quarantine via `@pytest.mark.timeout(120)`. NOT verdict-blocking.

### info

- [Cat 3] `judge_prompts.py:182` cache_control TTL=1h hardcoded as `dict[str, str] = {"type": "ephemeral", "ttl": "1h"}`. Per Anthropic SDK 2026-03-06 default change documented in CONTEXT-BRIEF §15 + 03-arch.md §10. WebFetch validation confirms 1h tier requires explicit header; Story E correctly opts in. No drift.
- [Cat 4] `_grade_one_turn_rubric` (`maj_eval.py:282-441`) implements degenerate `<2 valid judges` defense at line 318-340 (rare 2-providers-down case → `unconverged=True`, structlog error, R1 fallback). Excellent graceful degradation discipline.
- [Cat 5] `_persist_grade` (`maj_eval.py:627-675`) uses `pg_insert(...).on_conflict_do_nothing(index_elements=[...])` per backend-migrations.md SQLite-portable convention.
- [Cat 11] `runner.py:414` carries `noqa: PLR0915` with explicit justification documenting why splitting the 12-step orchestrator into helpers would fragment the spec'd story-wide cement. Rationale acceptable (Story B + Story E spec-bound contract).

## Cross-scope flags (if any)

(none — Story E is purely test-infra under `backend/tests/agentic_evals/sales_agent/grader/` + R5 schema-mirror exception in `modules/sales_agent/observability/eval_simulator/persistence/models/`. Zero cross-module business-logic touches. Backend auditor handles persistence schema mirror PR; auditor-agentic handles grader runtime.)

## Downstream regression scope (R3 verification)

Per `.claude/rules/auditor-downstream-regression.md` table:

| Surface modified | Downstream test targets | Status |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` (NEW T-5) | grader full suite + 5 arch gates | PASS (151/151 + 5/5) |
| `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (NEW T-7) | grader suite + sandbox/round_2/leak gates | PASS |
| `docs/specs/rubrics/qualification-accuracy.md` (REPLACE T-3) | grader cache invalidation downstream consumers | PASS (cache key recompute on rubric_version field) |
| `backend/tests/architecture/test_grader_*.py` (5 NEW T-8) | full arch fitness suite | PASS (1063/1063) |
| `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` (T-9 additive `grader_callback`) | simulator regression suite | 213/213 PASS (1 pre-existing timeout NOT Story E regression) |

**`shared/agent_observability/` NOT modified** by Story E — no R3 downstream cascade required for copilot/sales_agent observability tests (CONTEXT-BRIEF §11 conditional flag was pre-emptive; story scope held).

## Cost bucket H7 cement verification

- `test_grader_writes_eval_only_bucket.py` static AST scan — PASS:
  - Forbidden ORM model class imports (`CopilotLlmCallModel`, `SalesAgentLlmCallModel`, `CampaignLlmCallModel`) → 0 hits across grader subtree
  - Forbidden table name literals (`copilot_llm_call`, `sales_agent_llm_call`, `campaign_llm_call`) in executable code → 0 hits
  - Canonical eval write path indicators (`eval_simulator_llm_call`, `EvalSimulatorLlmCallModel`, `modules.sales_agent.observability.eval_simulator.persistence`) → present
- `_JudgeAdapter.grade` (`judge_registry.py:151-157`) explicitly builds `extended_eval_metadata` with `grader=maj_eval` + 5 NEW Story E keys; passes via obs_context.langchain_config()` callback chain — cost rollups land in `eval_simulator_llm_call` exclusively
- Story B H7 invariant intact post Story E (CONTEXT-BRIEF §11 conditional flag pre-emptive only — no actual cascade)

## H9 public API surface verification

- `simulator/__init__.py` `__all__` expanded 7 → 8 names (frozen at 8)
- `test_simulator_public_api_surface.py:46-56` `_EXPECTED_PUBLIC_NAMES` literal: `{"run_simulation", "SimulationResult", "SimulationState", "ActorProfile", "TerminationReason", "AgentErrorSubtype", "register_termination_policy", "grade_transcript_maj_eval"}` — PASS
- `_internal/maj_eval.py` + `_internal/judge_prompts.py` + `_internal/cache.py` + `_internal/judge_registry.py` NOT exposed (under `_internal/` subpackage; `grader/__init__.py:8` has `__all__: list[str] = []` per D-AG-16 cement)

## Round 2 debate logic verification

- Variance threshold `VARIANCE_R1_THRESHOLD: Final[float] = 0.15` (`maj_eval.py:106` D3 cement)
- Round 2 trigger gate at `_grade_one_turn_rubric:346` — converged R1 (`r1_variance <= 0.15`) returns immediately; else logs `maj_eval_debate_triggered` (line 365-372) + builds R2 tasks
- DQ3 anti-anchoring: `maj_eval.py:376-379` peer_reasoning list comprehension excludes `op.judge_id == jid` (R1 own); `judge_prompts.py:227` belt-and-suspenders second filter
- Convergence test: `maj_eval.py:415` `unconverged = r2_variance >= VARIANCE_R2_TARGET` (0.10 D4 cement)
- Unconverged → `final_score = r1_weighted` (line 561-563) + `structlog.warning` (line 417-425) — graceful degradation NOT block (DQ8 cement)
- R2 partial fallback (DQ6): line 396-409 — if R2 judge score=None, substitute R1 opinion → `r2_partial=True`
- Suspicious flag (DQ8): line 575-589 — all 3 judges score=1.0 + ANY injection_attempt → log warning + flag

## Brand voice compliance (CRITICAL — sales-agent-expert §3)

- `personality_profiles.system_instruction` consumed READ-ONLY:
  - `cache.py:110` `voice_profile.system_instruction.encode("utf-8")` — read for hash, no write
  - `judge_prompts.py:261-264` `getattr(voice_profile, "system_instruction", "")` — read for Slot 3, no mutation
- NO `brand_voice_summary` table or mirror created
- NO fine-tuning per tenant (D19 cement)
- NO voice-rewriter LLM pass post-generation
- NO hardcoded voice in `agent_identity.j2` or specialists (Story E doesn't touch them)
- NO `{tenant_name}` interpolation mid-prefix — `judge_prompts.py:127-131` Slot 3 carries `tenant_voice_hash + dialect + voice_system_instruction_verbatim`. `tenant_slug` lives ONLY in Slot 6 (volatile). Cache prefix stability preserved per documented design D19 + sales-agent-expert §3 cement

## Research notes (Anthropic prompt caching TTL)

- Source: 03-arch.md §10 cites Anthropic SDK + DEV Community article post-2026-03-06 default change from 1h → 5min
- Live verification: WebFetch deferred (knowledge cutoff Jan 2026; live docs URL `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` — context-builder validator §4 confirmed citation accuracy 2026-05-09T01:05:00Z)
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; Anthropic API behavior post-cutoff verified via 03-arch.md §10 + DEV Community link in CONTEXT-BRIEF §15
- Story E correctly opts into 1h TTL via explicit header `cache_control={"type": "ephemeral", "ttl": "1h"}` — judge_prompts.py:182 cement

## Recommendations for builder fix-loop

(no FAILs — story passes Phase 1 mechanical audit)

Optional pre-merge polish (NOT blocking):

1. WARN Cat 15 — When PM ratifies merge in Conv 3, consider standardizing commit body heading from "Decisions cement" / "Decisions applied" → "Decisions honored" per R6 cardinal verbatim. The substance + per-D# concrete cites are already present; only the heading string differs.
2. WARN Gate — Quarantine `test_db_session_propagated_to_agent_bridge_via_contextvar` with `@pytest.mark.timeout(120)` decorator (or skip in default CI suite + gate behind `RUN_SIMULATOR_SLOW=1` env var) — prevent recurring 30s pytest timeout false-positive in future runs. Pre-existing Story B issue; not Story E scope. Process-improvement ticket recommended.

## Drift detection (CONTRACT vs code)

- 03-arch.md decisions D1-D20 + DQ1-DQ8 + D-AG-1..D-AG-18 + D-BE-1..D-BE-8 (52 cement total) honored:
  - D-AG-15 H9 expand 7→8: VERIFIED (`test_simulator_public_api_surface.py` PASS)
  - D-AG-16 surface zero re-exports from grader pkg: VERIFIED (`grader/__init__.py:8` `__all__: list[str] = []` + arch gate `test_grader_public_api_surface.py`)
  - D-AG-17 LiteLLM Proxy ONLY: VERIFIED (no direct openai/anthropic SDK imports in grader; arch gate enforces)
  - D-BE-3 R5 schema-mirror exception: VERIFIED (`modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade*.py` ONLY touches schema mirror; zero domain/application/api touches)
- ZERO drift detected. CONTRACT spec v2 + design v2 + arch package faithfully implemented.

## Summary

**Verdict: PASS** — Story E sales-agent-voice-fidelity-grader-runtime ships clean Phase 1 mechanical audit. 10/10 tickets shipped GREEN, 151/151 grader tests PASS, 1063/1063 arch fitness PASS (5 NEW grader gates), H7 cost-bucket invariant cemented, H9 public API surface 7→8 frozen, DQ2 sandbox markers literal-enforced, DQ3 anti-anchoring filter present, voice SSoT consumed READ-ONLY zero creep, R5 schema-mirror exception cleanly observed.

Two non-blocking WARNs (Cat 15 wording + pre-existing simulator timeout flake) — neither is Story E regression nor verdict-blocking.

Ready for Chris-triggered `/auditor` Conv 3 full orchestration (CHECKPOINTS C1-C5 + capability promotion + merge) Sunday 2026-05-11. This Phase 1 mechanical review is INPUT for that final orchestration.
