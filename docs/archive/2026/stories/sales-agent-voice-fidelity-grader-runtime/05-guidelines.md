<!-- voseo-allowed: cita Chris autonomy mandate verbatim ("vos decidís + sales agent también califica") en owner routing § paridad Story C precedent -->
# 05-guidelines.md — Story sales-agent-voice-fidelity-grader-runtime

> /architect orchestrator delivered (2026-05-08). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N updates)

### Backend (Python 3.12 + Pydantic v2 + SQLAlchemy 2.0)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` en `MajEvalScore`, `JudgeOpinion`, `RubricGradeRequest`. Cero `class Config` inner.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`tenant_slug`, `simulation_id`, `turn_n`, `rubric_id`, `judge_id`, `round_n`, `error_class`).
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`. `created_at` `DateTime(timezone=True)` always.
- **SQLAlchemy 2.0 only** — `select(EvalSimulatorGradeModel).where(...)`. NUNCA `session.query()` (SA 1.x).
- **Async session** — `AsyncSession` from `src.core.database`. `await session.commit()` después de `session.add(...)`. Read via `await session.execute(select(...))` + `.scalar()` / `.scalars().all()`.
- **YAML safe_load** — N/A Story E (no YAML reading; Story C/D YAML data consumed via existing loaders).
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. Subclase desde shared, NO mirror. Story E REUSES Story B/C/shared infra.
- **`from __future__ import annotations` PERMITIDO en `grader/_internal/judge_registry.py`, `grader/_internal/cache.py`, `grader/_internal/judge_prompts.py`, persistence/models/`*.py`** — NOT in LangGraph compose path. **PROHIBIDO en grader/_internal/maj_eval.py** si llega a importarse desde simulator/_internal/runner.py (currently no — but defense-in-depth Story B cement).
- **Migrations idempotent raw SQL** — `op.execute("CREATE TABLE IF NOT EXISTS ...")`. NUNCA `op.create_table()` non-idempotent. NUNCA `sa.Enum(create_type=True)` (broken SA 2.0.27).
- **Schema-mirror exception R5** — `builder-backend` MAY touch `modules/sales_agent/observability/eval_simulator/persistence/models/` para schema mirror desde Alembic 127 migration. NO toca `domain/`, `application/`, `api/` del módulo agentic.

### Pydantic v2 schema versioning forward-compat

- **`MajEvalScore.schema_version: Literal[1] = 1`** cement. Future bumps register `(MajEvalScore, 1, 2)` identity migrator en Story B `SCHEMA_MIGRATIONS` registry.
- DDL column `schema_version SMALLINT NOT NULL DEFAULT 1` — paridad pattern Story B.
- `JudgeOpinion` + `RubricGradeRequest` también frozen=True post-construction.

### MAJ-EVAL state machine specific (`grader/_internal/maj_eval.py`)

- **Round 1 parallel** — `asyncio.gather(*[...3 judges...])` con `Semaphore(JUDGE_CONCURRENCY=20)` provider DoS protection (D-AG-10 / D17).
- **Variance check `max - min`** simple range — NOT statistical variance (D3 spec cement). Threshold `0.15` constant `VARIANCE_R1_THRESHOLD`.
- **Round 2 conditional** — only if `r1_variance > 0.15`. Each judge receives ONLY OTHER 2 R1 reasoning (DQ3 anti-anchoring).
- **R2 partial fallback (DQ6)** — if a judge fails R2, use R1 score for that judge + flag `r2_partial=true`. Mixed R1/R2 scores in `MajEvalScore.judges` JSONB.
- **Unconverged fallback (D4)** — R2 variance ≥ 0.10 → `final_score = round_1_weighted_avg` + flag `unconverged=true` + `structlog.warn` (NOT block — DQ8).
- **Suspicious flag (DQ8)** — all 3 judges score 1.0 + `injection_attempt_detected=true` → flag `suspicious=true` + structlog warn. NOT auto-block. Chris reviews semestralmente.
- **`asyncio.create_task` callback async** — Story B `run_simulation` post-turn hook (D17 / DQ5 cement). Best-effort try/except + structlog warn — NEVER propagates exception to sim loop.

### Sandbox markers cement (DQ2 / D14)

3-layer defense-in-depth:

1. **Slot 1 system directive** — verbatim `CRITICAL SECURITY DIRECTIVE` block in `grader/_internal/judge_prompts.py::SLOT_1_TEMPLATE`. Cacheable TTL=1h.
2. **Slot 5 builder** — literal `<<TRANSCRIPT_BEGIN>>` and `<<TRANSCRIPT_END>>` strings wrap transcript content. Static AST gate enforces.
3. **Arch fitness gate** `test_grader_sandbox_markers_enforced.py` — AST scan asserts marker literals present in builder fn body.

NUNCA accept `<<TRANSCRIPT_BEGIN>>` parametrized via variable (e.g., `BEGIN_MARKER = '<<TRANSCRIPT_BEGIN>>'` then `f"{BEGIN_MARKER}..."`). Static AST scan checks LITERAL string in code body — accept only inline f-string with verbatim markers OR direct concatenation literal `"<<TRANSCRIPT_BEGIN>>" + ...`.

### Cache hash composition cement (D8 precision)

- **Order-stable**: 5 fields sorted alphabetically (`compute_cache_key` per §3.5 03-arch.md).
- **JSON canonical** — `json.dumps(payload, sort_keys=True, separators=(",", ":"))`. NEVER vary serializer (str() / repr()).
- **sha256 hex 64 chars** — `hashlib.sha256(...).hexdigest()`. Cache PK VARCHAR(64).
- **Invalidation precision (D16)** — bump `rubric_version` field invalidates ALL entries for that rubric. Bump `judge_set_hash` invalidates ALL entries (judge weight change). Bump `tenant_voice_hash` invalidates per-tenant.

### Anthropic prompt caching cement (DQ1 + research §10)

- **Slots 1+2+3 cacheable TTL=1h** — declared **explicitly** vía `cache_control={"type": "ephemeral", "ttl": "1h"}` in Anthropic SDK call (post 2026-03-06 default change to 5min — see [DEV Community](https://dev.to/whoffagents/anthropic-silently-dropped-prompt-cache-ttl-from-1-hour-to-5-minutes-16ao)).
- **Slot 1 system directive cacheable** — same content for ALL judges within rubric_set version. Cache invalidates only on prompt template edit (rare).
- **Slot 2 rubric MD verbatim cacheable** — invalidates per `rubric_version` bump (D16).
- **Slot 3 tenant voice cacheable** — invalidates per `tenant_voice_hash` change.
- **Slots 4+5+6 NOT cached** — per-call variable.
- **NUNCA `{tenant_name}` interpolation** mid-block cacheable slot — sales-agent-expert §3 anti-pattern.
- **LiteLLM Proxy normalizes** OpenAI / Kimi cache mechanics; Anthropic-specific 1h tier headers passed via extra_headers.

### Round 2 peer critique cement (DQ3 anti-anchoring)

- Round 2 prompt for judge X receives ONLY judges {A, B} R1 reasoning (where A, B ≠ X).
- **NEVER inject judge X's own R1 reasoning** in its R2 prompt (avoid self-anchoring per MoA-Judge research).
- Static AST gate `test_grader_round_2_no_self_reasoning.py` scans Round 2 prompt builder fn body — assert no path injects `judge.judge_id == self.judge_id` reasoning.

### Voice + Spanish neutro

- **Code (`maj_eval.py`, `cache.py`, `judge_registry.py`, `judge_prompts.py`, persistence/models/)** + **structlog events** + **comments** + **tests** — Spanish neutro tuteo per `.claude/rules/spanish-text.md` glosario.
- **Judge prompts (Slot 1+2+6) + reasoning** = English (DQ4 cement — analytical layer determinism).
- **Rubric MD `qualification-accuracy.md` v1** = Spanish neutro tuteo. Threshold/scoring methodology Spanish prose; rubric IDs literal English.
- **Calibration MD `voice_fidelity_calibration.md`** = Spanish neutro.
- **Mockup transcript §11 design** ya cita es-AR voseo legitimately (sales_agent voice exception per `.claude/rules/sales-agent-brand-voice.md`) — design markdown line 2 magic comment present.
- **`personality_profile.system_instruction` Slot 3** = verbatim from tenant SSoT (sales-agent-expert §3 protected — voseo permitted if tenant es-AR; judges READ-ONLY).
- **NUNCA crear `brand_voice_summary` table mirror** (creep guard cement sales-agent-brand-voice).
- **NUNCA fine-tune judges per tenant** — generic judges + voice via Slot 3 = single variable (D19 cement).
- **NUNCA voice-rewriter LLM pass post-generation** (creep guard).

### Tests (TDD obligatorio)

- **RED → GREEN → REFACTOR** per layer:
  1. DDL migration 127 RED → GREEN (T-1 — raw SQL idempotent verifiable via `migration_idempotency` validator)
  2. SQLAlchemy 2.0 models RED → GREEN (T-2 — `EvalSimulatorGradeModel` + `EvalSimulatorGradeCacheModel`; insert/select round-trip)
  3. Pydantic types RED → GREEN (T-2 — `MajEvalScore` + `JudgeOpinion` + `RubricGradeRequest` with frozen=True invariants)
  4. NEW rubric MD `qualification-accuracy.md` v1 RED → GREEN (T-3 — frontmatter validates v1 + 4 axes A1-A4 present + threshold default 0.75)
  5. `judge_registry.py` 3 judges RED → GREEN (T-4 — JUDGE_WEIGHTS + JUDGE_MODELS + LiteLLM Proxy dispatch)
  6. `cache.py` hash composition RED → GREEN (T-6 — compute_cache_key deterministic + invalidation triggers)
  7. `judge_prompts.py` 6-slot template RED → GREEN (T-7 — sandbox markers literal + Round 2 peer-only)
  8. `maj_eval.py` Round 1 + Round 2 state machine RED → GREEN (T-5 — variance check, debate trigger, unconverged fallback, r2_partial)
  9. `simulator/__init__.py` H9 expand 7→8 + arch fitness re-freeze RED → GREEN (T-8)
  10. `run_simulation` integration grader hook RED → GREEN (T-9 — `asyncio.create_task` callback + Scenarios 1+2+3+4)
  11. Capability YAML + module narrative + auditor-downstream-regression rule + calibration MD seed (T-10 post-merge by /pm)
- **Pytest markers** — `@pytest.mark.eval` para tests que invocan LLM real. `@pytest.mark.no_eval` para unit tests no-LLM. CI default skips `--run-evals`-gated tests; full suite runs nightly.
- **Pytest fixtures** — Story B `run_id` reused. Story E adds `grader_session_factory` fixture in `conftest.py` (AsyncSession per test) + `mock_judge_factory` (for unit tests sin LLM real).

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()` from `shared/domain/datetime_utils.py`.
- ❌ Hardcoded `'USD'` — N/A Story E (no monetary user-facing).
- ❌ Hardcoded model names — use `JUDGE_MODELS` registry as-is. Bumps require Chris ratification + re-calibration cycle (D15).
- ❌ Modificar `simulator/__init__.py` `__all__` MÁS de 1 NEW name — Story E adds EXACTLY `grade_transcript_maj_eval` (8 names total). Future expansion requires bumping H9 invariant explicit.
- ❌ Modificar `LLM_ROLE_BY_SITE` SSoT (Story B / sales-agent-expert §2.1).
- ❌ Modificar `personality_profiles.system_instruction` (sales-agent-expert §3 protected).
- ❌ Modificar §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup) — STOP escalate.
- ❌ Modificar `eval_simulator_llm_call` / `eval_simulator_trace_event` schema (Story B R5 schema-mirror cement).
- ❌ Modificar Story C YAML files `archetype-aware/*.yaml` (consume only).
- ❌ Modificar Story D goldens YAML (consume only).
- ❌ Modificar Story A `dialect_catalog.yaml` (consume only).
- ❌ Modificar Story B `_fixtures/golden_v1_simulation_result.yaml` (H10 byte-equal cement).
- ❌ Modificar Story B existing arch fitness gates pre-existing logic (extend/edit allowlists OK; edit cement logic NO).
- ❌ Mirror callbacks/observability — REUSE Story B `EvalSimulatorObservabilityContext` + `BaseAgentCallbackHandler` subclass + shared `cost_recorder` + `PricingResolver/FXResolver` + `sanitize_payload`.
- ❌ Mirror judge LLM dispatch — `LiteLLMService.acompletion(...)` ÚNICAMENTE. Direct `openai.ChatCompletion.create` / `anthropic.messages.create` PROHIBIDO en `grader/`.
- ❌ Crear nueva tabla en `modules/sales_agent/` SOLO — DDL nace en Alembic migration 127 con consumer mirror en persistence/models/ (R5 cement Story B precedent).
- ❌ TypedDict en MajEvalScore / JudgeOpinion / RubricGradeRequest — Pydantic only (Story B D4 cement).
- ❌ HTTP webhook invocation desde grader (test-infra in-process only).
- ❌ Cross-module imports excepto `copilot` — Story E imports: `tests/agentic_evals/sales_agent/{simulator,grader,goldens,fixtures}/*` + `src/core/{config,database,enums}` + `src/shared/{agent_observability,domain,infrastructure}/*` + `src/modules/sales_agent/observability/eval_simulator/persistence/*` (R5 schema-mirror).
- ❌ `from __future__ import annotations` en `simulator/_internal/runner.py` o `simulator/_internal/customer_node.py` (importados por LangGraph compose — Story B cement T-4..T-7).
- ❌ Skip `sanitize_payload(transcript)` pre-judge call (defense-in-depth even synthetic — arch fitness gate).
- ❌ Skip sandbox markers `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` literal en Slot 5 builder (DQ2 production-critical).
- ❌ Round 2 self-reflection (judge sees own R1 reasoning) — DQ3 anti-anchoring cement.
- ❌ Multi-turn ensemble debate beyond Round 2 — D18 cement (cap; unconverged flag preferred).
- ❌ Per-tenant judge fine-tuning — D19 (generic judges + voice via Slot 3 = single variable).
- ❌ Inline `{tenant_name}` interpolation en cacheable slots (Slots 1+2+3) — sales-agent-expert §3 anti-pattern.
- ❌ Voice-rewriter LLM pass post-grade output (creep guard).
- ❌ Crear `brand_voice_summary` table mirror (sales-agent-brand-voice rule SSoT cement).
- ❌ Modificar `core/config.py` defaults — N/A Story E (no flag flip; env vars `SALES_AGENT_*_THRESHOLD` opcionales runtime override). Si Story E necesita flag flip → R31 anti-default-flip-audit applies.
- ❌ `// eslint-disable` / `# noqa` sin justification comment.
- ❌ `any` TS / `Any` Python loose types — strict typing.
- ❌ `git add .` / `git add -A` — stage por nombre exacto.
- ❌ `git commit --no-verify` — pre-commit hook native enforced.
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia.
- ❌ Crear feature branches/worktrees — `development` única branch.

## Files in scope (builders edit ONLY these)

### Migration + persistence models (BE test-infra — R5 schema-mirror exception)

- `backend/alembic/versions/127_add_eval_simulator_grade_tables.py` (NEW — raw SQL idempotent migration)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` (NEW — SQLAlchemy 2.0 model)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade_cache.py` (NEW — SQLAlchemy 2.0 model)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py` (EDIT additive — register 2 NEW models)

### Pydantic types + grader package (AGENTIC test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/grader/__init__.py` (NEW — minimal, zero re-exports per D-AG-16)
- `backend/tests/agentic_evals/sales_agent/grader/result.py` (NEW — `MajEvalScore` + `JudgeOpinion` + `RubricGradeRequest` Pydantic v2 frozen)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/__init__.py` (NEW — minimal)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_registry.py` (NEW — 3 judges + weights + LiteLLM Proxy adapter)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/cache.py` (NEW — hash composition + lookup/persist + graceful degradation)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (NEW — 6-slot template builder + sandbox markers + Round 2 peer-only injection)
- `backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` (NEW — state machine Round 1 + variance + Round 2 + persist + unconverged/r2_partial fallbacks)

### Calibration MD (AGENTIC test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md` (NEW — Chris seed labels skeleton + auto-calibration baseline)
- `backend/tests/agentic_evals/sales_agent/grader/calibration/__init__.py` (placeholder for future calibration scripts)

### Test files (AGENTIC test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/grader/test_judge_registry.py` (NEW — 3 judges loaded + weights validates + JUDGE_MODELS pinned)
- `backend/tests/agentic_evals/sales_agent/grader/test_grader_cache.py` (NEW — hash composition deterministic + invalidation precision + lookup/persist round-trip + graceful DB unavailable)
- `backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py` (NEW — sandbox markers literal + Round 2 peer-only injection + slot composition)
- `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_unit.py` (NEW — variance calc + weighted average + rubric dispatch per persona_kind + unconverged/r2_partial fallbacks + suspicious flag)
- `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_happy.py` (NEW — Scenario 1 happy path 3 rubrics × 8 turns × 3 judges = 72 calls)
- `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_debate.py` (NEW — Scenarios 2 + edge cases R2 convergence/unconverged/r2_partial)
- `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_adversarial.py` (NEW — Scenario 4 prompt-injection + sandbox markers resist)
- `backend/tests/agentic_evals/sales_agent/grader/test_judge_no_system_leak.py` (NEW — leak assertion FORBIDDEN_LEAK_STRINGS reuse Story B pattern)
- `backend/tests/agentic_evals/sales_agent/grader/test_run_simulation_grader_hook.py` (NEW — integration with `run_simulation` async callback + extended eval_metadata 5 NEW keys)
- `backend/tests/agentic_evals/sales_agent/grader/test_unconverged_fallback.py` (NEW — fallback semantics)
- `backend/tests/agentic_evals/sales_agent/grader/conftest.py` (NEW — `grader_session_factory` + `mock_judge_factory` fixtures)

### Architecture fitness gates (BE non-prod-code — NEW + 1 EDIT)

- `backend/tests/architecture/test_simulator_public_api_surface.py` (EDIT — `_EXPECTED_PUBLIC_NAMES` 7→8 add `grade_transcript_maj_eval`; alphabetical sort cement; comment explicit Story E expansion)
- `backend/tests/architecture/test_grader_no_mirrors_shared.py` (NEW — empty allowlist shrink-only; walk grader/ tree + assert no basename collision with `shared/agent_observability/*`)
- `backend/tests/architecture/test_grader_writes_eval_only_bucket.py` (NEW — empty allowlist shrink-only; cost-bucket H7 enforce)
- `backend/tests/architecture/test_grader_public_api_surface.py` (NEW — empty allowlist; `grader/__init__.py` `__all__` cero re-exports)
- `backend/tests/architecture/test_grader_pii_sanitize_pre_judge.py` (NEW — empty allowlist; static AST scan `grade_transcript_maj_eval` calls `sanitize_payload`)
- `backend/tests/architecture/test_grader_sandbox_markers_enforced.py` (NEW — empty allowlist; static AST scan `<<TRANSCRIPT_BEGIN>>` + `<<TRANSCRIPT_END>>` literal in builder)
- `backend/tests/architecture/test_grader_round_2_no_self_reasoning.py` (NEW — empty allowlist; static AST scan Round 2 prompt builder peer-only)

### Rubric MD (BE test-infra — REPLACE Story C placeholder)

- `docs/specs/rubrics/qualification-accuracy.md` (REPLACE — Story C 25-line placeholder → Story E v1 full per §3.4 03-arch.md; threshold default 0.75; 4 assertions A1-A4 + scoring methodology)

### Public API surface H9 expand (AGENTIC test-infra — EDIT)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (EDIT — single addition: `from tests.agentic_evals.sales_agent.grader._internal.maj_eval import grade_transcript_maj_eval` + add to `__all__` alphabetical sort 7→8 names)

### Integration (AGENTIC test-infra — EDIT existing Story B + Story E test)

- `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` (EDIT minimal additive — `run_simulation` accepts OPTIONAL `grader_callback: Callable | None = None` parameter; per-turn `if grader_callback: asyncio.create_task(grader_callback(...))`. Story B existing tests pass `None` → zero ripple)

### SSoT updates (rules + capability + module narrative — post-merge by /pm)

- `.claude/rules/auditor-downstream-regression.md` (EDIT additive — append 3 entries tabla SSoT per §11 03-arch.md)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (EDIT additive — append `grader` block per §11 03-arch.md)
- `docs/product/modules/sales-agent.md` (EDIT additive — narrative addition 1-2 sentences per §11 03-arch.md)

## Files NEVER touched (escalate to Chris if needed)

- `backend/tests/agentic_evals/sales_agent/simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency,schema_migrations,personas_loader,customer_persona_prompt,customer_node}.py` ← Story B + Story C cement; Story E only edits `runner.py` MINIMAL ADDITIVE (`grader_callback` parameter)
- `backend/tests/agentic_evals/sales_agent/simulator/{actor_profile,state,result,termination}.py` ← Story B/C cement; Story E does NOT modify
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/{actor_profiles,tenant_seeded}.py` ← Story B/C cement; Story E reuses fixtures
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` ← H10 byte-equal Story B
- `backend/tests/agentic_evals/sales_agent/goldens/**` ← Story D YAML data (when build done); Story E READ-ONLY consume
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_trace_event,eval_synthetic_tenants}.py` ← Story B R5 schema-mirror cement; Story E adds 2 NEW models alongside (no edit existing)
- `backend/src/shared/agent_observability/**` ← shared abstractions; Story E consumes via inheritance Story B subclasses
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording}/` ← runtime sales_agent (sales-agent-expert §3 protected)
- `backend/src/modules/copilot/**` ← agentic builder territory ONLY
- `backend/src/core/config.py` ← R31 anti-default-flip-audit (Story E declares env var docs only — no `core/config.py` edit needed)
- `backend/alembic/versions/{001..125,2b27...,9c6f...,194925...}.py` ← Story E adds 127 ONLY
- `backend/tests/fixtures/eval/tenants/{dialect_catalog.yaml,loader.py}` ← Story A cement; Story E READ-ONLY consume
- `docs/specs/personas/**` ← Story C cement; Story E READ-ONLY consume
- `docs/specs/rubrics/{voice-fidelity,no-overpromise,no-hallucination,empathy-tone,tool-trajectory,completeness,code-quality}.md` ← existing rubrics; Story E READ-ONLY consume
- `frontend/**` ← N/A esta story FE no toca
- `client_simulator/src/simulator/*.py` ← D6 preservation gate Story B (sha256 unchanged)
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression.md entry add post-merge by /pm) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)

1. `01-spec.md` (re-read 4 scenarios + 20 decisiones D1-D20 + 9 ratified questions Q1-Q9 mid-build)
2. `02-design-agentic.md` (state machine §1 + slot architecture §2 + voice constraints §4 + error recovery §5 + observability §8 + 8 ratified DQ1-DQ8)
3. `03-arch.md` (this story consolidated arch — 11 sections; especialmente §2 audit + §3 BE + §4 AGENTIC + §5 cross-cutting + §6 D-AG-/D-BE-)
4. `04-validators.yaml` (test commands ejecutables — 4 scenarios cement)
5. Spec Schema cement §"Schema cement (`MajEvalScore` v1 + supporting types)" (Pydantic types verbatim)

### Story B / C / A references (Story E extends, do NOT mirror)

- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md` (Story B BE+AGENTIC arch — `EvalSimulatorObservabilityContext` + `eval_simulator_llm_call` schema + H1-H10 cement)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/05-guidelines.md` (Story B patterns required/forbidden — Story E respects)
- `docs/archive/2026/stories/eval-foundation-tenant-seed-data/03-arch.md` (Story A `dialect_catalog` + tenant fixtures + 5 personality profiles)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/03-arch.md` (Story C — `personas_loader` + `actor_profile.metadata['persona_gym_axes']` + customer prompt v2)

### Skills (per surface)

- `sales-agent-expert` — §3 protected surfaces, anti-patterns, voice fidelity SSoT, brand voice cement, tier pricing
- `copilot-expert` — observability writes best-effort try/except + structlog warning (callbacks)
- `tessl__langgraph` — Pydantic state, async patterns, runtime introspection caveats
- `claude-api` — Anthropic SDK + prompt caching slot architecture (1h TTL explicit per 2026-03-06 default change)
- `tessl__graceful-degradation` — Rule 1+2: timeouts on every external call, fallbacks per dependency
- `tessl__pytest-api-testing` — pytest-asyncio, fixtures, parametrize
- `backend-expert` — DDD patterns, arch fitness ratchet, schema-mirror exception R5 (cement Story B precedent)
- `tessl__fastapi` — Pydantic v2 patterns (ConfigDict, Annotated, no Ellipsis)

### Rules (cement before each Edit)

- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file; grader uses Story B EvalSimulatorObservabilityContext + shared cost_recorder/PricingResolver/FXResolver/sanitize_payload — REUSE not mirror)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entry post-merge with grader paths + downstream tests Stories F/G/I
- `.claude/rules/architectural-fitness.md` — 4 NEW grader gates (test_grader_*.py) empty allowlists shrink-only + 1 EDIT (test_simulator_public_api_surface.py 7→8)
- `.claude/rules/backend-ddd.md` — schema-mirror exception R5 (Story E uses for 2 NEW models eval_simulator_grade + eval_simulator_grade_cache mirror Alembic 127 — paridad Story B precedent)
- `.claude/rules/backend-migrations.md` — raw SQL IF NOT EXISTS idempotent + prod-clone test command
- `.claude/rules/copilot-observability.md` — best-effort writes try/except + structlog warning (loader scan errors, judge timeout, parse-fail, cache DB unavailable)
- `.claude/rules/copilot-resilience.md` — observability invariants Story B preserved
- `.claude/rules/parallel-safety.md` — `git add` por nombre exacto, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — voice creep guard cement (NO crear brand_voice_summary table mirror, NO LLM-distilled voice cache, NO fine-tuning per tenant, NO voice-rewriter post-pass, NO `{tenant_name}` mid-block cache prefix)
- `.claude/rules/spanish-text.md` — voseo glosario + magic comment escape (Story E code Spanish neutro tuteo; mockup transcript design es-AR voseo legitimately)
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer (DDL → models → types → judge_registry → cache → judge_prompts → maj_eval → integration)
- `.claude/rules/tenant-isolation.md` — synthetic tenants only (Story B `tenant_id = uuid5(NS_DNS, f"eval-{slug}")`); MajEvalScore.tenant_slug literal; production sales_agent NEVER invokes grader
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches
- `.claude/rules/anti-default-flip-audit.md` — N/A Story E (no flag flip in `core/config.py`; env vars `SALES_AGENT_*_THRESHOLD` are runtime override only, no default change)

### Templates (consult during ticket execution)

- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO.
- Docker only para `alembic upgrade` migration test (`migration_idempotency` validator).

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:

1. **DDL migration 127 + idempotency test** RED → GREEN (T-1 — Alembic 127 raw SQL idempotent + `migration_idempotency` validator passes both runs)
2. **SQLAlchemy 2.0 models + Pydantic types** RED → GREEN (T-2 — `EvalSimulatorGradeModel`, `EvalSimulatorGradeCacheModel`, `MajEvalScore`, `JudgeOpinion`, `RubricGradeRequest`)
3. **Rubric MD `qualification-accuracy.md` v1 (replace Story C placeholder)** RED → GREEN (T-3 — `qualification_accuracy_rubric_v1_replaced` validator)
4. **`judge_registry.py` 3 judges** RED → GREEN (T-4 — `judge_registry_3_judges_loaded` + LiteLLM Proxy dispatch)
5. **`maj_eval.py` Round 1 + Round 2 state machine** RED → GREEN (T-5 — variance calc + debate trigger + unconverged/r2_partial fallbacks + tests unit per fn)
6. **`cache.py` hash composition + lookup/persist** RED → GREEN (T-6 — `compute_cache_key` deterministic + invalidation triggers + DB graceful unavailable)
7. **`judge_prompts.py` 6-slot template + sandbox markers + Round 2 peer-only** RED → GREEN (T-7 — sandbox AST + Round 2 self-check AST)
8. **`simulator/__init__.py` H9 expand 7→8 + arch fitness re-freeze** RED → GREEN (T-8 — `_EXPECTED_PUBLIC_NAMES` 7→8 + 4 NEW grader arch fitness gates)
9. **Integration `run_simulation` grader_callback hook + 4 scenario tests** RED → GREEN (T-9 — async callback fire-and-forget + Scenarios 1-4 contract tests)
10. **Capability YAML + module narrative + auditor-downstream-regression rule + calibration MD seed** (T-10 post-merge by /pm only — no builder action)

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py`).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:

- `done -> docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-5-result.md`
- `blocked -> docs/product/stories/sales-agent-voice-fidelity-grader-runtime/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_debate.py:42 [round 2 unconverged not flagged]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE test-infra (DDL migration 127) | false | builder-backend Sonnet | YAML+SQL declarative — pure test-infra, idempotent raw SQL pattern |
| T-2 | BE test-infra (SQLA models + Pydantic types) | false | builder-backend Sonnet | Schema-mirror R5 + Pydantic v2 frozen=True — declarative paridad Story B |
| T-3 | BE test-infra (rubric MD `qualification-accuracy.md` v1) | false | builder-backend Sonnet | Markdown content + frontmatter — declarative |
| T-4 | AGENTIC test-infra (`judge_registry.py` 3 judges) | false | builder-agentic Opus 4.7 | LiteLLM Proxy adapter + cost recording bridge — agentic plumbing critical path |
| T-5 | AGENTIC test-infra (`maj_eval.py` state machine Round 1 + Round 2) | false | builder-agentic Opus 4.7 | ★ Critical complexity — variance calc + debate trigger + unconverged/r2_partial fallbacks + suspicious flag + asyncio.gather Semaphore. R23 permite Sonnet pero Chris cero deuda mandate + production-critical defense-in-depth → Opus mandatory |
| T-6 | AGENTIC test-infra (`cache.py` hash composition + lookup/persist) | false | builder-agentic Opus 4.7 | Cache key composition precision (D8/D16) + idempotency cement — agentic critical path |
| T-7 | AGENTIC test-infra (`judge_prompts.py` 6-slot template + sandbox markers + Round 2 peer-only) | false | builder-agentic Opus 4.7 | ★ Sandbox markers DQ2 cement (production-critical anti-injection) + Round 2 anti-anchoring DQ3 — agentic security-critical |
| T-8 | AGENTIC test-infra (`simulator/__init__.py` H9 expand 7→8 + arch fitness 4 NEW gates + 1 EDIT) | false | builder-agentic Opus 4.7 | Public API surface cement + arch fitness static AST gates — agentic invariant management |
| T-9 | AGENTIC test-infra (integration `run_simulation` grader hook + 4 scenario tests) | false | builder-agentic Opus 4.7 | ★ Integration complexity + 4 production-critical scenarios (happy/edge/cache/adversarial) + asyncio.create_task fire-and-forget callback |
| T-10 | docs (capability YAML + module narrative + auditor-downstream-regression rule + calibration MD seed) | false | /pm post-merge (NO builder) | Documentation reconciliation — `/pm` skill ownership |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris autonomy mandate cero deuda 1000+ tenants. Aunque R23 permite Sonnet en agentic test-infra, Chris autonomy mandate "vos decidís + sales agent también califica" + 4 production-critical scenarios (Scenario 4 prompt-injection / sandbox markers DQ2 / Round 2 anti-anchoring DQ3 / cache invalidation precision D8/D16) + state machine MAJ-EVAL complexity + cost-bucket invariant H7 cross-judge → **Opus 4.7 mandatory para T-4..T-9 (6 agentic tickets)**. T-1, T-2, T-3 BE (DDL + models + rubric MD) → Sonnet OK. PM confirma final routing antes Conv 2 arranca.

## Build order (depends_on critical path — bloqueador hard)

```
Story C build done (refined+ready: post 2026-05-08 build wave) ───┐
Story D build done (refined+ready: post 2026-05-08 build wave) ───┴──→  Story E build STARTS
                                                                              │
                                                                              ├─→ T-1 (DDL) + T-2 (models) + T-3 (rubric MD)  [parallel]
                                                                              │      │
                                                                              │      ▼
                                                                              ├─→ T-4 (judge_registry) [needs T-2]
                                                                              ├─→ T-6 (cache) [needs T-2]
                                                                              ├─→ T-7 (judge_prompts) [needs T-2]
                                                                              │      │
                                                                              │      ▼
                                                                              ├─→ T-5 (maj_eval) [needs T-2, T-4, T-6, T-7]
                                                                              │      │
                                                                              │      ▼
                                                                              ├─→ T-8 (H9 expand + arch fitness) [needs T-5]
                                                                              │      │
                                                                              │      ▼
                                                                              ├─→ T-9 (integration + 4 scenarios) [needs T-5, T-8]
                                                                              │      │
                                                                              │      ▼
                                                                              └─→ T-10 (docs reconciliation /pm post-merge)
```

Critical path: T-1+T-2+T-3 (parallel) → T-4+T-6+T-7 (parallel) → T-5 → T-8 → T-9 → T-10.

## sales_agent toolkit dependency (escalation path — paridad Story C)

Scenarios 1+2+3+4 use `run_simulation` from Story B (post Story C wired). If `qualify_lead` o `tag_lead_status` tools absent en sales_agent runtime al build time:

- T-9 Scenarios assume sales_agent runtime supports the tools needed. Story C T-6/T-7 ya escaló esto en spec § "sales_agent toolkit dependency".
- If still absent at Story E build time → SKIP Scenarios 5/6 dependent verification (paridad Story C decision); Story E core (judge runtime + cache + 4 grader scenarios using synthetic transcripts from Story D goldens) NOT dependent on `qualify_lead` (works against Story D YAML transcript[] verbatim).

This is OUT OF SCOPE Story E scope per spec anti-creep guards.
