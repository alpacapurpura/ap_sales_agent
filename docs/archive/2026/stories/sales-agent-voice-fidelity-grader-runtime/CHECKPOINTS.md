<!-- voseo-allowed: audit checkpoints may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# CHECKPOINTS — Story E: sales-agent-voice-fidelity-grader-runtime

> Conv 3 deliverable per `.claude/skills/auditor/SKILL.md` C1-C5 grid.
> Auditor: `auditor-agentic` (Opus 4.7) — INDEPENDENT review (supersedes builder Phase 1)
> Generated: 2026-05-11T00:00:00Z
> Verdict: **APPROVED**

## Decision

**APPROVED** — Story E ready for `/pm` merge orchestration + capability promotion + state transition `reviewing → done`.

One advisory WARN (Cat 15 commit body heading "Decisions cement" vs cardinal "Decisions honored") — substance present, only format string differs. Cosmetic delta — does NOT block merge. PM may standardize wording at merge or defer.

## C1 — Code (impl matches design)

| Status | Evidence |
|---|---|
| **PASS** | `_internal/maj_eval.py` (735 LOC) implements per-(turn × rubric) state machine: PII sanitize → cache lookup → Round 1 parallel `asyncio.gather` + `Semaphore(20)` D17 → variance check max-min D3 (threshold 0.15) → Round 2 conditional debate peer-only DQ3 → R2 partial fallback DQ6 → unconverged fallback to R1 weighted avg D4 → suspicious flag DQ8 → persist + cache best-effort Rule 2. Cement constants `Final[float|int]`. |
| | `_internal/judge_prompts.py` (365 LOC) implements 6-slot architecture: Slots 1+2+3 cacheable TTL=1h (lines 348-350 dict-copy `_CACHE_CONTROL_TTL_1H`); Slot 5 sandbox-wrapped transcript with literal `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` markers (lines 245-247). Voice SSoT `personality_profile.system_instruction` consumed READ-ONLY (lines 261-264). |
| | `_internal/judge_registry.py` (358 LOC) — 3 judges pinned per D15 (sonnet=claude-sonnet-4-6 / gpt4o=gpt-4o-2024-11-20 / kimi=kimi-k2.6, lines 83-87) with weights 0.4/0.4/0.2 D2 (lines 75-79). Dispatch via LiteLLMService ONLY (D-AG-17, line 59). Best-effort try/except (line 224 BLE001) returns `score=None` on judge fail. |
| | `_internal/cache.py` (233 LOC) — D8 cement frozen alphabetical 5-field hash composition (lines 48-54 `_CACHE_KEY_FIELDS` Final tuple). Lookup + persist with graceful degradation Rule 2 (lines 171, 224 try/except + structlog warn + skip). |
| | `integration.py` (262 LOC) — `make_grader_callback` factory wires grade_transcript_maj_eval to runner.py grader_callback hook (D17/DQ5 fire-and-forget). |
| | `simulator/_internal/runner.py:423,645-669` additive `grader_callback` param (25 lines, all inside try/except, default None — Story B determinism preserved). |

## C2 — Spec (Gherkin scenarios pass)

| Status | Evidence |
|---|---|
| **PASS** | Scenario 1 (happy multi-judge) — `scenarios/test_scenario_1_happy_multi_judge.py` PASS via 151/151 grader suite. |
| | Scenario 2 (edge — Round 2 debate trigger on variance > 0.15) — `scenarios/test_scenario_2_edge_round_2_debate.py` PASS + DQ3 anti-anchoring verified by `test_grader_round_2_no_self_reasoning.py` (4 arch gates). |
| | Scenario 3 (cache hit deterministic re-run) — `scenarios/test_scenario_3_cache_idempotency.py` PASS + cache invalidation precision via `test_grader_cache.py` 3 invalidation tests (rubric_version, judge_weights, voice_hash). |
| | Scenario 4 (adversarial prompt-injection in transcript content) — `scenarios/test_scenario_4_adversarial_prompt_injection.py` PASS + sandbox markers literal cement via `test_grader_sandbox_markers_enforced.py` (3 arch gates) + leak assertions via `test_judge_no_system_leak.py`. |
| | All 28 validators in `04-validators.yaml` covered by gate-runner execution (re-confirmed 2026-05-11). |

## C3 — Architecture (matches 03-arch.md, no drift)

| Status | Evidence |
|---|---|
| **PASS** | 52 cement decisions verified honored: D1-D20 (spec) + DQ1-DQ8 (design) + D-AG-1..D-AG-18 (agentic arch) + D-BE-1..D-BE-8 (BE schema). |
| | D-AG-15 H9 expand 7→8: `simulator/__init__.py:80-89` `__all__` 8 names frozen alphabetical; `test_simulator_public_api_surface.py:42-77` enforces equality + cardinality. |
| | D-AG-16 grader package zero re-exports: `grader/__init__.py` `__all__: list[str] = []`; `test_grader_public_api_surface.py` enforces. |
| | D-AG-17 LiteLLM Proxy ONLY: `grep -rn "from openai\|from anthropic" tests/agentic_evals/sales_agent/grader/` returns empty. Validator `agentic_litellm_proxy_dispatch_only` enforces. |
| | D-BE-3 R5 schema-mirror exception: only `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade*.py` + `__init__.py` touched in `backend/src/`. Zero domain/application/api touches. Per `.claude/rules/backend-ddd.md`. |
| | Migration 127 idempotent raw SQL `IF NOT EXISTS` (`backend/alembic/versions/127_add_eval_simulator_grade_tables.py:34,63,67,71`). |
| | Anti-duplication §0: 14 inventory items mapped to REUSE per CONTEXT-BRIEF §7.5. Zero NEW mirror files. `test_grader_no_mirrors_shared.py` enforces basename non-overlap with shared/agent_observability. |
| | ZERO drift detected vs CONTRACT (spec v2 + design v2 + 03-arch.md). |

## C4 — Cross-cutting (tenant + PII + voice + currency + observability)

| Status | Evidence |
|---|---|
| **PASS — Tenant isolation** | `tenant_slug` carried through `RubricGradeRequest` → persisted on `eval_simulator_grade` (`maj_eval.py:601`) + included in `tenant_voice_hash` invalidation. Cache lookup keyed by 5-field hash including tenant voice. Pure-function hash composition prevents cross-tenant cache leak. |
| **PASS — PII sanitisation** | D10 cement enforced via `test_grader_pii_sanitize_pre_judge.py` AST gate + runtime call at `maj_eval.py:174-186` (each transcript turn wrapped in `sanitize_payload(...)` before any judge invocation). REUSE shared `src.shared.agent_observability.recording.sanitization.sanitize_payload` (anti-duplication §0). Defense-in-depth even on synthetic data. |
| **PASS — Voice SSoT (sales-agent-expert §3)** | `personality_profile.system_instruction` consumed READ-ONLY (no write/distill/mirror/fine-tune). NO `brand_voice_summary` table created. NO `{tenant_name}` interpolation mid-prefix (Slot 3 contains `tenant_voice_hash + dialect + verbatim text` only; tenant_slug volatile zone Slot 6). NO voseo in grader code (23 magic comments where glosario cited per R25). |
| **N/A — Currency** | Story E does NOT handle monetary fields. Cost recording uses Decimal but no display formatting. |
| **PASS — Observability** | `_JudgeAdapter.grade` (judge_registry.py:151-157) builds `extended_eval_metadata` with 5 NEW Story E keys (grader/rubric_id/rubric_version/judge_id/round_n/cache_hit) merged into `obs_context.langchain_config()` callbacks. Cost-bucket H7 cement enforced by `test_grader_writes_eval_only_bucket.py` static AST scan (forbidden ORM imports + table literals fail gate). All judge LLM calls write `eval_simulator_llm_call` ONLY — zero contamination of copilot/sales_agent/campaign cost buckets. |

## C5 — Trace (observability writes correct, eval_simulator_grade table populated correctly)

| Status | Evidence |
|---|---|
| **PASS** | `_persist_grade` (`maj_eval.py:627-675`) emits one row per (simulation × turn × rubric) tuple with PK composite `(simulation_id, turn_n, rubric_id)`. Idempotent first-writer-wins via `INSERT ... ON CONFLICT DO NOTHING` (line 667 `index_elements=[...]` SQLite-portable). |
| | Schema mirror SQLA model (`eval_simulator_grade.py:30-76`) matches Alembic 127 DDL: `schema_version`, `simulation_id`, `turn_n`, `rubric_id`, `rubric_version`, `tenant_slug`, `persona_kind`, `actor_profile_id`, `judges JSONB` (full audit trail of 3-or-6 JudgeOpinion dicts), `round_1_score`, `round_2_score`, `final_score`, variances, debate_triggered, unconverged, r2_partial, suspicious, injection_attempt_detected, cost_usd_total, latency_ms_total, cache_hit_count, metadata_, created_at. |
| | Cache table separate (D9/D-BE-2): `eval_simulator_grade_cache` (cache_key VARCHAR(64) sha256 hex, payload JSONB MajEvalScore serialized, last_hit_at audit). Cache lifecycle independent from grade rows. |
| | Best-effort persist (`maj_eval.py:240-270`) try/except + structlog warn + fallback per Graceful Degradation Rule 2. NEVER raises out — caller falls back to fresh grade. |
| | 6 indexes per migration 127 for query performance: tenant_persona, rubric, unconverged, simulation, schema_version, created_at. |
| | Suspicious flag wired through to row (DQ8 cement `maj_eval.py:575-589`) — production audit trail for adversarial scenarios. |

## Gate execution summary (re-executed 2026-05-11 native WSL)

| Gate | Status | Time |
|---|---|---|
| ruff check (35 files) | PASS | <1s |
| ruff format --check | PASS | <1s |
| pytest grader full | PASS 151/151 | 11.58s |
| pytest arch fitness full | PASS 1063/1063 + 1 env-skip | 29.54s |
| pytest simulator regression | PASS 214/214 + 36 toolkit-skip | 113.41s |
| WebFetch Anthropic prompt-caching | VERIFIED | live 2026-05-11 |

Pre-existing simulator timeout flake (`test_db_session_propagated_to_agent_bridge_via_contextvar`) noted in original gate-output did NOT repro in Conv 3 fresh native WSL run — confirmed Story B environmental flake (posthog/asyncio/socket deadlock at 30s default pytest timeout), NOT Story E regression.

## Recommended PM merge actions

1. Transition `state: reviewing → done`
2. Promote capability scenarios to `docs/product/capabilities/sales_agent/` (or appropriate module YAML)
3. Update `docs/product/modules/sales_agent.md` narrative if applicable
4. Archive Story E `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/` to `docs/archive/2026/stories/sales-agent-voice-fidelity-grader-runtime/` (if /pm policy applies)
5. (Optional) Standardize commit body heading "Decisions cement" → "Decisions honored" per R6 cardinal — cosmetic, can defer to next PI lessons-learned
6. (Optional follow-up) Process-improvement ticket for `shared/infrastructure/llm/providers/litellm.py` to add explicit `timeout=` per `tessl__graceful-degradation` Rule 1 (cross-consumer impact: copilot + sales_agent + brand + offer + landing). NOT Story E scope.
7. Story E DONE unblocks luana-platform Story 7 (sales-agent-engine) — per checkpoint.md transition note 2026-05-10
