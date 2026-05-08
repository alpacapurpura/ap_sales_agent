# 05-guidelines.md — Story sales-agent-eval-pass-k-tracking

> /architect orchestrator delivered (2026-05-08). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N runs)

### Backend (Python 3.12 + Pydantic v2 + SQLA 2.0 async)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` heredado Story B/E. Cero `class Config` inner. Frozen=True para immutability post-aggregation.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`run_id`, `tenant_slug`, `persona_kind`, `golden_id`, `error_class`). Excepción: CLI script `print(...)` user-facing OK (bilingual: errors Spanish, structlog English).
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`. `created_at` en EvalPassKSummary = `utc_now()` (timezone-aware UTC).
- **YAML safe_load** — `yaml.safe_load(...)` para Story D goldens YAML. NUNCA `yaml.load()` sin Loader (security risk).
- **SQLA 2.0 async** — `select(EvalPassKSummaryModel).where(...)` + `await session.execute(stmt)`. NUNCA `session.query()` (SA 1.x). Insert: `session.add(...)` + `await session.commit()`. Read: `result.scalars().all()`.
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. CONSUMA Story E `MajEvalScore` via SQL (no recompute), Story B `eval_simulator_trace_event` (read-only), Story C `trial_policy_by_persona_kind` (import constant), Story D goldens YAML (read-only). NO mirror grading logic / runner / persona loader.
- **Raw SQL idempotent migration** — `op.execute("CREATE TABLE IF NOT EXISTS ...")` + `op.execute("CREATE INDEX IF NOT EXISTS ...")`. NUNCA `op.create_table()` o `sa.Enum(create_type=True)`.
- **`from __future__ import annotations` PERMITIDO en TODOS los Story F files** — aggregator NO es LangGraph runtime (no introspection caveat de Story B T-4 cement). Es deterministic Python pipeline.

### Read-only aggregator invariant (CRITICAL — D-BE-12 cement)

- **Cero LLM imports** en `aggregator.py` + `_internal/bloom_scorer.py` + `_internal/inputs_hasher.py` + `scripts/compute_pass_k_report.py`:
  - ❌ `import litellm`
  - ❌ `import anthropic`
  - ❌ `import openai`
  - ❌ `from litellm import ...`
  - ❌ `from anthropic import ...`
  - ❌ `from openai import ...`
- Arch fitness gate `test_aggregator_no_llm_calls.py` enforces via AST static scan (allowlist empty shrink-only).
- Aggregator solo escribe a `eval_pass_k_summary` table. CERO writes a `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `copilot_llm_call`, `sales_agent_llm_call`. Verificado via integration test `test_aggregator_zero_llm_call_writes` (DB query post-aggregation: zero NEW rows con timestamp > test_start_at).

### Bloom 4-stage scoring contract (D-BE-13 cement)

- **`_BLOOM_THRESHOLD_DEFAULTS` dict cement byte-equal**:
  ```python
  _BLOOM_THRESHOLD_DEFAULTS: Final[dict[str, float]] = {
      "understanding": 0.7,
      "ideation": 0.7,
      "rollout": 0.7,
      "judgment": 0.7,
  }
  ```
- **4 env var canonical pattern**: `SALES_AGENT_BLOOM_<STAGE>_THRESHOLD` (UPPER_SNAKE_CASE):
  - `SALES_AGENT_BLOOM_UNDERSTANDING_THRESHOLD`
  - `SALES_AGENT_BLOOM_IDEATION_THRESHOLD`
  - `SALES_AGENT_BLOOM_ROLLOUT_THRESHOLD`
  - `SALES_AGENT_BLOOM_JUDGMENT_THRESHOLD`
- **No-hallucination override** (Story E D13 reuse): `SALES_AGENT_RUBRIC_NO_HALLUCINATION_THRESHOLD=0.85` aplica en stage Rollout (per-rubric stricter override, NOT stage-global).
- Arch fitness gate `test_bloom_threshold_defaults_protected.py` enforces dict + env var names byte-equal.

### Heterogeneous K per persona_kind (D-BE-16 cement Story C inheritance)

- **`_TRIAL_POLICY_BY_PERSONA_KIND` constant byte-equal**:
  ```python
  _TRIAL_POLICY_BY_PERSONA_KIND: Final[dict[str, int]] = {
      "happy": 3,           # production-critical close
      "nurture": 1,         # info path
      "unqualified": 3,     # qualification accuracy critical
      "adversarial": 3,     # Story I additive
  }
  ```
- **Aggregator MUST respect, NOT override** — Story C cement (delta-spec.md cement post Chris ratification 2026-05-08). Drift requires explicit cement bump in Story C + downstream regression rule R3 sync.
- Validator `agentic_heterogeneous_k_respects_story_c` enforces dict byte-equal via `python -c` assertion.

### inputs_hash determinism (D-BE-14 cement)

- **Composition order frozen** — sha256 hex of canonical JSON (`json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)`):
  ```python
  payload = {
      "grade_rows": grade_rows,            # Story E MajEvalScore rows for cell
      "trace_events": trace_events,        # Story B trace events for cell
      "golden_yaml": golden_yaml,          # Story D YAML at compute time
  }
  canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
  return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
  ```
- **64-char lowercase hex output** (Pydantic Literal validator: `Field(min_length=64, max_length=64)`).
- **Stable across runs** — Test `test_inputs_hash_deterministic_across_runs` invoca 100x same inputs, asserts all hashes identical.
- Tampering detection: re-compute hash from raw inputs + compare vs cached `EvalPassKSummary.inputs_hash`. Mismatch → `EvalPassKValidationError`.

### Goldens YAML immutability defense-in-depth (D-BE-9 + Story D D16 cement)

- **Layer 1**: pre-commit hook Section 9 NEW (block commits con golden mutation sin magic comment `# golden-refresh: <reason>` o env override `NO_VERIFY_GOLDEN_REFRESH=1`).
- **Layer 2**: `golden_yaml_hash` field per `EvalPassKSummary` row (sha256 snapshot at compute time).
- **Layer 3**: `--validate-strict` CLI flag re-computes hashes + compares vs cached row (tamper detection post-fact). `EvalPassKValidationError` raised on mismatch.
- Section 9 hook EXTEND existing `scripts/git-hooks/pre-commit` file — sections 1-8 untouched (additive, byte-equal preservation).

### Schema versioning forward-compat (D-BE-10 + D-BE-11 cement Story B H1 reuse)

- **`EvalPassKSummary.schema_version: Literal[1] = 1`** cement v1.
- **`PassKAggregateReport.schema_version: Literal[1] = 1`** cement v1 (separate from EvalPassKSummary; Story G consumer pinned v1).
- Future bumps via `SCHEMA_MIGRATIONS` registry (Story B H1 reuse). Story F adds anchor entry `EvalPassKSummary v1` (sentinel — no migrator function for v1; future v2 register `(EvalPassKSummary, 1, 2)` migrator function).

### PII sanitization (D-BE-15 cement)

- `BloomStageResult.evidence` strings (cita de violations) MUST run through `sanitize_payload` shared (`shared/agent_observability/recording/sanitization.py`) pre-persist. Defense-in-depth (even synthetic data eval) per `.tessl/.../pii-sanitisation.md`.
- Test `test_evidence_strings_sanitize_payload_applied` injects synthetic PII into trace events, asserts sanitized in persisted evidence string.

### Spanish neutro LATAM (`.claude/rules/spanish-text.md`)

- **CLI script user-facing strings** (print/error en stderr) → español neutro LATAM sin voseo:
  - `"Reporte pass^K generado: {out_path}"` ✅
  - `"ERROR computando pass^K: {exc}"` ✅
  - NO voseo: `"Te genero el reporte..."` ❌ → `"Genera el reporte..."` ✅
- **Aggregator code** (Python identifiers, docstrings, structlog event names) → English (technical layer).
- **Excepción**: aggregator pipeline NO emite output user-facing directo (CLI script SI — bilingual: errors Spanish, structlog English).
- **Glosario voseo→neutro** aplicado en CLI strings — ver `.claude/rules/spanish-text.md` § R2.

### Tests (TDD obligatorio per `.claude/rules/tdd-mandatory.md`)

- **RED → GREEN → REFACTOR** per layer (orden estricto):
  1. **Pydantic schemas** RED → GREEN (T-2 — EvalPassKSummary + BloomStageResult + TrialResult + PassKAggregateReport + FlakyGoldenDetail Pydantic v2 frozen)
  2. **inputs_hasher** RED → GREEN (T-3 — sha256 deterministic + 100x identity test + tamper test)
  3. **bloom_scorer** RED → GREEN (T-4 — 4-stage scoring per Bloom contract + threshold env vars + per-stage evidence)
  4. **aggregator** RED → GREEN (T-5 — compute_pass_k_for_run + heterogeneous K + unconverged + integration with Stories B/C/D/E)
  5. **CLI script** RED → GREEN (T-6 — argparse + JSON output + --validate-strict)
  6. **Pre-commit hook Section 9** RED → GREEN (T-7 — bash + git diff staged + magic comment regex + 4 test cases)
  7. **Arch fitness gates** RED → GREEN (T-8 — 3 NEW gates empty allowlist + capability YAML + module narrative + downstream regression rule)
- **Pytest markers** — `@pytest.mark.asyncio` para async tests (aggregator integration). Cero `@pytest.mark.eval` (Story F NO LLM).
- **Pytest fixtures** — `eval_pass_k_test_session` (AsyncSession + tear-down rollback), `synthetic_grade_rows` (fixture data simulating Story E MajEvalScore), `synthetic_trace_events` (Story B trace events fixture), `synthetic_golden_yaml` (Story D golden fixture). Story F can build BEFORE Story E if synthetic fixtures used (decouple build dependency).

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()`
- ❌ Hardcoded `'USD'` — N/A Story F (Decimal cost only, no multi-currency)
- ❌ Hardcoded model names — N/A Story F (no LLM calls)
- ❌ Modificar `simulator/__init__.py` `__all__` (frozen 7 names Story B; Story E expand 7→8 but Story F NO touch)
- ❌ Modificar `LLM_ROLE_BY_SITE` SSoT (no LLM calls)
- ❌ Modificar `personality_profiles.system_instruction` (sales-agent-expert §3 protected)
- ❌ Modificar §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup) — STOP escalate
- ❌ Modificar `eval_simulator_*` DB schema o models PRE-EXISTING (R5 Story B/E preserved — Story F adds NEW table `eval_pass_k_summary` only)
- ❌ Modificar Story D goldens YAML content (read-only — `golden_yaml_hash` snapshot only; mutation detected by hook Section 9)
- ❌ Modificar Story C `_TRIAL_POLICY_BY_PERSONA_KIND` cement (3/1/3/3) — Story F respects, NO override
- ❌ Modificar Story E `MajEvalScore` schema (consume read-only via SQL queries)
- ❌ Modificar Story B `eval_simulator_trace_event` schema (consume read-only)
- ❌ Editar frozen golden v1 fixture `_fixtures/golden_v1_simulation_result.yaml` (H10 Story B byte-equal)
- ❌ Editar Story B/C/E existing arch fitness gates (extend ratchet OK, edit pre-existing logic NO)
- ❌ Mirror `EvalSimulatorObservabilityContext` desde Story B (NO USED — aggregator zero LLM, no callback handler needed)
- ❌ Mirror grading logic desde Story E (CONSUME via SQL queries on eval_simulator_grade table)
- ❌ Mirror simulation runner desde Story B (CONSUME via SQL queries on eval_simulator_trace_event table)
- ❌ Mirror personas loader desde Story C (CONSUME via import constant `_TRIAL_POLICY_BY_PERSONA_KIND`)
- ❌ Mirror golden authoring logic desde Story D (CONSUME via YAML safe_load read-only)
- ❌ Mirror cost aggregator from `CopilotCostAggregator` o `SalesAgentCostAggregator` (NO TOUCH — paradigma ortogonal: production billing vs test-infra eval pass^K binary)
- ❌ `yaml.load()` sin Loader (security) — use `yaml.safe_load`
- ❌ TypedDict (no LangGraph state — Pydantic only)
- ❌ HTTP webhook invocation (no agentic — pure aggregator)
- ❌ Cross-module imports excepto `copilot` (Story F imports allowed: `tests/agentic_evals/sales_agent/{simulator,goldens}/`, `src/core/{config,database}`, `src/shared/{domain/datetime_utils,agent_observability/recording/sanitization}`, `src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_pass_k_summary` — Story F NEW model file)
- ❌ Modificar `simulator/__init__.py` (Story F aggregator NO se exporta via simulator surface — vive en `pass_k/__init__.py` package separado)
- ❌ Re-running simulations (Story B owns)
- ❌ Re-grading rubrics (Story E owns)
- ❌ LLM calls of any kind (read-only aggregator invariant cement D-BE-12)
- ❌ Statistical tests (chi-square, p-values, Bayesian) — strict binary all-of-K cement D3
- ❌ Probabilistic `pass_rate^k` (legacy paradigm 00-story.md superseded D1)
- ❌ FE component for visualization (Story F BE-only service-story)
- ❌ Streamlit dashboard for flaky_goldens (separate observability story)
- ❌ Sections 1-8 of pre-commit hook modify (additive Section 9 only — sections 1-8 byte-equal preservation)
- ❌ `// eslint-disable` / `# noqa` sin justification comment (N/A FE for Story F)
- ❌ `any` TS / `Any` Python loose types — strict typing
- ❌ Default exports (N/A FE for Story F)
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git commit --no-verify` — pre-commit hook native enforced (Section 9 NEW added by T-7)
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia

## Files in scope (builders edit ONLY these)

### NEW files (Story F creates)

#### Migration + SQLA model (BE test-infra — R5 schema-mirror exception)

- `backend/alembic/versions/128_add_eval_pass_k_summary_table.py` (NEW migration — raw SQL idempotent)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_pass_k_summary.py` (NEW SQLA 2.0 async model — R5 schema-mirror)

#### Pydantic schemas + aggregator + helpers (AGENTIC test-infra — but NOT agentic logic)

- `backend/tests/agentic_evals/sales_agent/pass_k/__init__.py` (NEW — empty or minimal `__all__` with public functions only)
- `backend/tests/agentic_evals/sales_agent/pass_k/_schema.py` (NEW — `EvalPassKSummary`, `BloomStageResult`, `TrialResult`, `PassKAggregateReport`, `FlakyGoldenDetail`)
- `backend/tests/agentic_evals/sales_agent/pass_k/aggregator.py` (NEW — `compute_pass_k_for_run` + `EvalPassKValidationError`)
- `backend/tests/agentic_evals/sales_agent/pass_k/_internal/__init__.py` (NEW — empty)
- `backend/tests/agentic_evals/sales_agent/pass_k/_internal/bloom_scorer.py` (NEW — 4-stage scoring per Bloom contract)
- `backend/tests/agentic_evals/sales_agent/pass_k/_internal/inputs_hasher.py` (NEW — sha256 deterministic + tamper detection)

#### CLI script (BE)

- `backend/scripts/compute_pass_k_report.py` (NEW — CLI entry point + argparse + JSON output + --validate-strict flag)

#### Tests (BE test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py` (NEW — Scenarios 1+2+3 contract tests + Bloom 4-stage compute + heterogeneous K + unconverged + idempotency + integration with synthetic fixtures)
- `backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator_validation.py` (NEW — Scenario 4 adversarial: inputs_hash tamper + golden_yaml_hash mutation + EvalPassKValidationError)
- `backend/tests/scripts/test_compute_pass_k_report.py` (NEW — CLI integration: JSON report exists + valid Pydantic + --validate-strict mode + root_cause_stage attribution)

#### Architecture fitness gates (BE — 3 NEW)

- `backend/tests/architecture/test_pass_k_summary_schema_complete.py` (NEW — Pydantic ⊆ DDL columns + Literal values match)
- `backend/tests/architecture/test_aggregator_no_llm_calls.py` (NEW — AST static scan for forbidden imports)
- `backend/tests/architecture/test_bloom_threshold_defaults_protected.py` (NEW — `_BLOOM_THRESHOLD_DEFAULTS` byte-equal + env var names canonical)

### EDIT files (Story F extends additively)

- `scripts/git-hooks/pre-commit` (EDIT — append Section 9 NEW; sections 1-8 byte-equal preservation)
- `backend/tests/scripts/test_pre_commit_hook.py` (EDIT — append Section 9 tests: 4 cases — block/magic comment/env override/no-op)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (EDIT — append `EvalPassKSummary v1` anchor entry to SCHEMA_MIGRATIONS registry; bump `CURRENT_SCHEMA_VERSIONS` dict adds `"EvalPassKSummary": 1`)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (EDIT — append eval block fields per §3.9; post-merge by /pm only — NO builder action; T-8 ticket flagged)
- `docs/product/modules/sales-agent.md` (EDIT — narrative addition 1-2 sentences; post-merge by /pm only — T-8 ticket flagged)
- `.claude/rules/auditor-downstream-regression.md` (EDIT — append entry per §11; post-merge by /pm only — T-8 ticket flagged)

## Files NEVER touched (escalate to Chris if needed)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` ← H9 surface frozen 7-or-8 names Stories B/E
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` ← H10 byte-equal Story B
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency,customer_node,customer_persona_prompt,personas_loader,schema_migrations}.py` ← Story B/C cement; Story F EDITS solo `schema_migrations.py` (anchor entry append) — el resto NO TOUCH
- `backend/tests/agentic_evals/sales_agent/simulator/{state.py,result.py,actor_profile.py,termination.py}` ← Story B/C cement; Story F NO modify
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/{actor_profiles,tenant_seeded}.py` ← Story B cement
- `backend/tests/agentic_evals/sales_agent/grader/**` ← Story E territory (planned/refined; Story F consumes via SQL queries on `eval_simulator_grade` table, NOT via Python imports of grader module)
- `backend/tests/agentic_evals/sales_agent/goldens/**/*.yaml` ← Story D territory (immutable post-commit per D16 + Story F D15 cement)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_trace_event,eval_simulator_grade,eval_simulator_grade_cache,eval_synthetic_tenants}.py` ← Stories B/E cement; Story F adds NEW model `eval_pass_k_summary.py` only
- `backend/src/shared/agent_observability/**` ← shared abstractions; Story F consumes via inheritance/imports (sanitize_payload only)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording}/` ← runtime sales_agent (NO touch)
- `backend/src/modules/copilot/**` ← agentic builder territory only (NO touch — Story F BE-only)
- `backend/src/core/config.py` ← R31 anti-default-flip-audit (Story F NO flag in core/config.py)
- `backend/alembic/versions/{0..127}*.py` ← pre-existing migrations (Story F adds NEW 128 only)
- `backend/tests/fixtures/eval/tenants/{dialect_catalog.yaml,loader.py}` ← Story A cement
- `frontend/**` ← N/A esta story FE no toca (BE-only service-story)
- `client_simulator/src/simulator/*.py` ← D6 preservation gate Story B (sha256 unchanged)
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression entry add via T-8) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)

1. `01-spec.md` (re-read 4 scenarios + decisions D1-D16 mid-build; ratified Chris 2026-05-08T10:00Z)
2. `03-arch.md` (this story consolidated arch — DDL + SQLA + Pydantic + aggregator + script + hook)
3. `04-validators.yaml` (test commands ejecutables — 25 validators across 3 categories)

### Story B/C/E references (Story F consumes, do NOT mirror)

- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md` (Story B AGENTIC arch — H1-H10 invariants + observability)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-be.md` (Story B BE arch — DDL pattern Alembic 125)
- `docs/archive/2026/stories/sales-agent-personas-instrumented-runtime/03-arch.md` (Story C personas + heterogeneous K cement)
- `docs/archive/2026/stories/sales-agent-personas-instrumented-runtime/05-guidelines.md` (Story C patterns precedent)
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md` (Story E arch — `MajEvalScore` schema + `eval_simulator_grade` table + cache hash composition precedent)

### Skills (per surface)

- `backend-expert` — DDD patterns, R5 schema-mirror exception, arch fitness ratchet, idempotent migrations
- `tessl__pytest-api-testing` — pytest-asyncio, fixtures, parametrize, AsyncSession test patterns
- `tessl__fastapi` — Pydantic v2 patterns (ConfigDict frozen=True, Literal forward-compat, BaseModel inheritance)
- `tessl__graceful-degradation` — Rule 2 fallback (yaml parse errors in goldens loader)

### Rules (cement before each Edit)

- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file; aggregator genuinamente NEW per audit §2)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entry post-merge (T-8) with pass_k/aggregator path + downstream tests
- `.claude/rules/architectural-fitness.md` — 3 NEW gates empty allowlist shrink-only
- `.claude/rules/backend-ddd.md` — schema-mirror exception R5 applies (model `eval_pass_k_summary.py`)
- `.claude/rules/backend-migrations.md` — idempotent raw SQL `IF NOT EXISTS` cement
- `.claude/rules/copilot-observability.md` — best-effort writes try/except + structlog warning (aggregator NO writes to LLM tables — invariant)
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — sales_agent voice cement preserved (Story F NO touch personality_profiles)
- `.claude/rules/spanish-text.md` — CLI strings español neutro LATAM
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer
- `.claude/rules/tenant-isolation.md` — `eval_pass_k_summary` rows tenant-scoped via `tenant_slug` field
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches
- `.claude/rules/anti-default-flip-audit.md` — N/A Story F (no flag flip in core/config.py)

### Templates (consult during ticket execution)

- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Migration: `docker exec visionarias_brain_dev alembic upgrade head` (only DB ops via Docker)
- CLI script: `cd backend && .venv/bin/python scripts/compute_pass_k_report.py --run-id <uuid> --output <path>`
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:

1. **DDL idempotent migration + SQLA model** RED → GREEN (T-1 — Alembic 128 + EvalPassKSummaryModel R5 schema-mirror; idempotency test re-run twice)
2. **Pydantic schemas** RED → GREEN (T-2 — 5 types frozen=True + Literal forward-compat + SCHEMA_MIGRATIONS anchor entry)
3. **inputs_hasher** RED → GREEN (T-3 — sha256 deterministic + 100x identity test + tamper test)
4. **bloom_scorer** RED → GREEN (T-4 — 4-stage scoring per Bloom contract + threshold env vars + per-stage evidence + arch fitness gate)
5. **aggregator** RED → GREEN (T-5 — compute_pass_k_for_run + heterogeneous K + unconverged + integration with synthetic fixtures + read-only DB invariant)
6. **CLI script** RED → GREEN (T-6 — argparse + JSON output + --validate-strict flag + root_cause_stage attribution)
7. **Pre-commit hook Section 9** RED → GREEN (T-7 — bash + git diff staged + magic comment regex + 4 test cases + arch fitness gate test_aggregator_no_llm_calls.py)
8. **Capability YAML + module narrative + downstream regression rule + remaining arch fitness gates** (T-8 — post-merge by /pm + arch fitness gates 3 NEW + capability eval block + module narrative)

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py`).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:

- `done -> docs/product/stories/sales-agent-eval-pass-k-tracking/T-3-result.md`
- `blocked -> docs/product/stories/sales-agent-eval-pass-k-tracking/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py:42 [pass_k_strict assertion mismatch]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE test-infra (DDL migration + SQLA model R5) | false | builder-backend Sonnet | DDL declarative SQL + SQLA model schema-mirror — pure BE test-infra |
| T-2 | BE test-infra (Pydantic schemas + SCHEMA_MIGRATIONS anchor) | false | builder-backend Sonnet | Pydantic v2 declarative + Literal forward-compat — declarative |
| T-3 | BE test-infra (inputs_hasher) | false | builder-backend Sonnet | sha256 + json.dumps deterministic — simple deterministic Python |
| T-4 | BE test-infra (bloom_scorer 4-stage) | false | builder-backend Sonnet | 4-stage scoring per Bloom contract table — threshold env vars + dict aggregation. **Sonnet OK; if iteration cap reached on 4-stage logic complexity → escalate /pm para Opus override.** |
| T-5 | BE test-infra (aggregator + integration) | false | builder-backend Sonnet | SQL queries + dict aggregation + Pydantic instantiation — read-only deterministic pipeline |
| T-6 | BE test-infra (CLI script) | false | builder-backend Sonnet | argparse + JSON serialization + --validate-strict mode — declarative |
| T-7 | BE test-infra (pre-commit hook Section 9) | false | builder-backend Sonnet | bash + git diff + regex — extend existing hook pattern. **Sonnet OK; if hook integration with sections 1-8 byte-equal preservation breaks → escalate /pm para Opus override.** |
| T-8 | DOCS + arch fitness gates (capability YAML + module narrative + downstream regression rule + 3 NEW arch tests) | false | builder-backend Sonnet (arch tests) + /pm post-merge (capability YAML + module narrative + rule update) | Documentation reconciliation + arch fitness ratchet — declarative |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris autonomy mandate. Story F = service-story BE-only `production_code: false`, simple deterministic aggregation Python (zero LLM/agentic/LangGraph). **Sonnet OK todos 8 tickets.** Si en build encuentra bloqueo en T-4 bloom_scorer (4-stage logic) o T-7 pre-commit hook Section 9 → escalate /pm para Opus override puntual. PM confirma final routing antes Conv 2 arranca.

## Build dependency on Stories C+D+E (HARD blocker)

Story F build BLOCKED on Stories C+D+E build done:

- **Story C** `sales-agent-personas-instrumented-runtime` — builds + provides `_TRIAL_POLICY_BY_PERSONA_KIND` constant (currently in `personas_loader.py` `_MAX_TURNS_BY_PERSONA_KIND` matrix; Story F may import or duplicate cement constant — D-BE-16 prefers import).
- **Story D** `sales-agent-goldens-3-tenants-dataset` — builds + provides 20-30 goldens YAML files con ground truth (`expected_termination_reason`, `expected_tools_invoked`, `forbidden_tools`, `expected_voice_attributes`, `expected_min_distinct_objections_handled`).
- **Story E** `sales-agent-voice-fidelity-grader-runtime` — builds + provides `eval_simulator_grade` table + `MajEvalScore` rows persisted per (simulation_id × turn_n × rubric_id).

**Decoupled build option**: T-1 through T-4 + T-7 + T-8 can build BEFORE Stories C/D/E if synthetic test fixtures used (decouple data dependency). T-5 (aggregator integration) + T-6 (CLI) require Stories E+B data flowing → BLOCKED on Stories C+D+E build done. PM/dev-team decides parallelization at build trigger.

## Sales_agent toolkit dependency (escalation path — N/A Story F)

Story F is read-only aggregator — does NOT depend on sales_agent runtime tools. If Stories C/D builds skip-with-escalation per Story C T-6/T-7 pattern (qualify_lead missing in TOOL_REGISTRY), Story F still builds with synthetic fixtures + skip integration tests con `pytest.skip("Stories E+B real data needed for full integration")` until upstream lands.
