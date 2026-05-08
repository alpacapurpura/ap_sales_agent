# 05-guidelines.md — Story sales-agent-eval-cost-budget-cap

> /architect orchestrator delivered (2026-05-08T12:00Z). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N runs)

### Backend (Python 3.12 + Pydantic v2 + SQLA 2.0 async + asyncio)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` heredado Story B/E/F. Cero `class Config` inner. Frozen=True para immutability post-snapshot.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`run_id`, `bucket`, `tier`, `current_usd`, `cap_usd`, `pct`). 3 canonical events: `eval.budget.tier_warning` (warn), `eval.budget.cap_exceeded` (error), `eval.budget.bypass_detected` (warn).
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`. `started_at` / `aborted_at_timestamp` / `final_at` / `BudgetWarning.timestamp` = `utc_now()` (timezone-aware UTC). Reference impl in §3.2 uses `datetime.now(tz=timezone.utc)` — equivalent; prefer `utc_now()` if helper available.
- **Decimal monetary** — `Decimal` for ALL cost fields (cost_usd, cap_usd, current_cost_usd, estimated_next_usd, projected_total_usd). Quantize to 6dp precision via `cost.quantize(Decimal("0.000001"))` per cost_estimator §3.3 reference. NO float / int monetary.
- **SQLA 2.0 async** — `select(EvalSimulatorLlmCallModel).where(...)` + `await session.execute(stmt)` per §3.2 reference. NUNCA `session.query()` (SA 1.x). Use `func.coalesce(func.sum(...), 0)` for nullable cost_usd handling.
- **asyncio.create_task** — canonical Python 3.12 pattern per §3.4 reference. Caller responsibility for Task lifecycle (start at run start, cancel at run end via try/finally). Never spawn Task in arch fitness or unit tests (mock with `AsyncMock` + `monkeypatch`).
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. CONSUMA Story B `eval_simulator_llm_call.cost_usd` (read-only via SQL), Story E `eval_simulator_grade.cost_usd_total` (read-only via SQL), `model_pricing_snapshot` shared (read-only via PricingSnapshotRepository accessor). NO mirror cost recording (Story B H7 owns). NO mirror production `BudgetGuard` shared/billing (paradigma distinto cement §2 audit).
- **`from __future__ import annotations` PERMITIDO en TODOS los Story H files** — guard NO es LangGraph runtime (no introspection caveat de Story B T-4 cement). Es deterministic Python guard + asyncio Task.
- **Lazy import for cross-story deps** — `EvalSimulatorGradeModel` (Story E) importado lazy en `guard.compute_remaining_budget` para evitar import error si Story E no built (synthetic fixtures used pre-Story E build for unit tests).

### Read-only guard invariant (CRITICAL — D-BE-8 cement)

- **Cero LLM imports** en `guard.py` + `_internal/cost_estimator.py` + `_internal/sweep.py` + `_schema.py`:
  - ❌ `import litellm`
  - ❌ `import anthropic`
  - ❌ `import openai`
  - ❌ `from litellm import ...`
  - ❌ `from anthropic import ...`
  - ❌ `from openai import ...`
- Arch fitness gate `test_eval_llm_calls_use_budget_guard.py` enforces via AST static scan (Layer 1 enforcement). 2 enforcement modes:
  - **Mode A — eval files import LLM**: each eval file importing forbidden module MUST also import `from tests.agentic_evals.sales_agent.budget.guard import check_budget_before_call`. Allowlist empty shrink-only.
  - **Mode B — guard module itself imports forbidden**: guard module MUST NOT import LLM modules (forbidden list scan). Empty allowlist.
- Guard solo escribe a `_artifacts/eval_runs/{run_id}/budget_summary.json` (filesystem JSON output). CERO writes a `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `copilot_llm_call`, `sales_agent_llm_call`. Verificado via integration test `test_guard_runs_produce_zero_llm_call_writes` (DB query post-aggregation: zero NEW rows con timestamp > test_start_at).

### Multi-tier cap architecture (D1-D2 cement spec)

- **`_load_caps()` env var pattern** — guard.py `_load_caps()` returns dict cement byte-equal:
  ```python
  {
      "per_trial": Decimal(os.getenv("SALES_AGENT_EVAL_PER_TRIAL_CAP_USD", "0.10")),
      "per_grade": Decimal(os.getenv("SALES_AGENT_EVAL_PER_GRADE_CAP_USD", "0.20")),
      "per_run": Decimal(os.getenv("SALES_AGENT_EVAL_PER_RUN_CAP_USD", "500")),
      "per_bucket_generation": Decimal(os.getenv("SALES_AGENT_EVAL_PER_BUCKET_GENERATION_CAP_USD", "20")),
      "per_bucket_grader": Decimal(os.getenv("SALES_AGENT_EVAL_PER_BUCKET_GRADER_CAP_USD", "400")),
  }
  ```
- **4 tiers Literal cement** in TierState: `Literal["per_trial", "per_grade", "per_run", "per_bucket"]`. NO additions without spec bump.
- **2 buckets Literal baseline** in BucketState: `Literal["generation", "grader"]`. Story I extends additively (Pydantic Literal additive).
- **Warning threshold** — `SALES_AGENT_EVAL_BUDGET_WARNING_PCT=80` default (D10 cement). Per-bucket trigger (earlier signal vs per-run 80%).

### Pre-flight cost estimation (D4 cement over-estimate strict)

- **Formula cement byte-equal** in cost_estimator.py:
  ```python
  cost = (Decimal(input_tokens) * input_rate) + (Decimal(max_output_tokens) * output_rate)
  return cost.quantize(Decimal("0.000001"))
  ```
- **NO 1.10x safety multiplier** (D-BE-13 cement) — production `shared/billing/cost_estimator.py` uses 1.10x for runtime; Story H eval expects exact spec input_tokens (caller tokenizer-counted, deterministic test fixtures).
- **Pricing source** — `model_pricing_snapshot` shared table via `PricingSnapshotRepository(session)` accessor. Anti-duplication respect at data layer.
- **Conservative fallback** when pricing snapshot missing — Decimal("0.000005") input + Decimal("0.000015") output (Claude Opus tier — 1000-tenants safety). structlog `eval.budget.cost_estimate_fallback` warning.

### Periodic sweep (D5 cement 30s default)

- **Pattern canonical** per §3.4 reference:
  ```python
  asyncio.create_task(_sweep_loop(session, run_id))
  ```
- **Caller lifecycle responsibility** — orchestrator MUST cancel returned Task at run end:
  ```python
  task = start_periodic_sweep(session, run_id=run_id)
  try:
      await run_eval_suite(...)
  finally:
      task.cancel()
      try:
          await task
      except asyncio.CancelledError:
          pass
  ```
- **Soft-fail iteration** — sweep MUST NOT take down run on transient DB error. `_sweep_loop` catches `Exception` (NOT `BudgetCapExceededError` which propagates) + logs `eval.budget.sweep_iteration_failed_soft_fail` + continues next interval.
- **Interval configurable** via `SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S` env var. Default 30s. Test override to 1s for fast assertion.

### Public API surface H9 expand (D-BE-6 cement)

- **`simulator/__init__.py` __all__ 8→9 names** — single addition `check_budget_before_call`. Re-freeze 9 names post-Story H ship.
- **`test_simulator_public_api_surface.py` allowlist 8→9** — `_EXPECTED_PUBLIC_NAMES` frozenset adds `check_budget_before_call` + cardinality test asserts `len(__all__) == 9`.
- **PRE-CONDITION** — Story E build COMPLETE before Story H build start (hard blocker: 7→8 expansion ships first; Story H expands 8→9).

### Schema versioning forward-compat (D-BE-4 cement Story B H1 reuse)

- **`BudgetState.schema_version: Literal[1] = 1`** cement v1.
- **SCHEMA_MIGRATIONS registry anchor entry** — extend `simulator/_internal/schema_migrations.py` `CURRENT_SCHEMA_VERSIONS` dict adds `"BudgetState": 1`. No migrator function for v1 (sentinel). Future v2 register `(BudgetState, 1, 2)` migrator function.

### PII sanitization (D-BE-15 spec D8 reuse)

- `BudgetWarning.message` strings (Spanish neutro user-facing) MUST run through `sanitize_payload` shared (`shared/agent_observability/recording/sanitization.py`) pre-persist. Defense-in-depth (even synthetic data eval) per `.tessl/.../pii-sanitisation.md`.
- Test `test_warning_message_sanitize_payload_applied` injects synthetic PII into warning context, asserts sanitized in persisted message.

### Spanish neutro LATAM (`.claude/rules/spanish-text.md`)

- **`BudgetWarning.message` user-facing strings** → español neutro LATAM sin voseo:
  - `"Bucket grader llegó al 80% del cap $400. Costo actual: $320."` ✅
  - NO voseo: `"Tu bucket llegó al 80%..."` ❌ → `"El bucket llegó al 80%..."` ✅
- **JSON output `budget_summary.json`** field names English (consumer Story G CI gate parses programmatically).
- **Guard code** (Python identifiers, docstrings, structlog event names) → English (technical layer).
- **Glosario voseo→neutro** aplicado en CLI strings — ver `.claude/rules/spanish-text.md` § R2.

### Tests (TDD obligatorio per `.claude/rules/tdd-mandatory.md`)

- **RED → GREEN → REFACTOR** per layer (orden estricto):
  1. **Pydantic schemas** RED → GREEN (T-1 — BudgetState + BucketState + TierState + AbortContext + BudgetWarning + BudgetCapExceededError + SCHEMA_MIGRATIONS anchor)
  2. **cost_estimator** RED → GREEN (T-2 — over-estimate strict + LiteLLM pricing integration + fallback rates)
  3. **guard** RED → GREEN (T-3 — `check_budget_before_call` + `compute_remaining_budget` + env var loader)
  4. **sweep** RED → GREEN (T-4 — periodic asyncio Task + post-facto detection + lifecycle)
  5. **arch fitness gates** RED → GREEN (T-5 — `test_eval_llm_calls_use_budget_guard.py` + `test_budget_state_schema_complete.py` empty allowlists)
  6. **simulator __init__ expand + integration tests + JSON output + capability YAML extend + module narrative + downstream regression rule** (T-6 — H9 expand 8→9 + scenarios 1+2+3+4 integration + JSON persist)
- **Pytest markers** — `@pytest.mark.asyncio` para async tests (guard + sweep). Cero `@pytest.mark.eval` (Story H NO LLM).
- **Pytest fixtures** — `eval_budget_test_session` (AsyncSession + tear-down rollback), `synthetic_llm_call_rows` (Story B fixture data), `synthetic_grade_rows` (Story E fixture data), `synthetic_pricing_snapshot` (model_pricing_snapshot fixture). Story H can build BEFORE Story E build if synthetic fixtures used (decouple integration data dependency).

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()` (or `datetime.now(tz=timezone.utc)` if helper unavailable)
- ❌ Hardcoded `'USD'` en DTOs — N/A Story H (Decimal cost only, all USD synthetic eval scope; no multi-currency)
- ❌ Hardcoded model names (no LLM calls)
- ❌ Modificar `simulator/__init__.py` `__all__` more than puntual 8→9 expand (`check_budget_before_call`) — single addition cement
- ❌ Modificar `_internal/` simulator files except `schema_migrations.py` anchor entry append (Story B/C cement preserved)
- ❌ Modificar `LLM_ROLE_BY_SITE` SSoT (no LLM calls)
- ❌ Modificar `personality_profiles.system_instruction` (sales-agent-expert §3 protected)
- ❌ Modificar §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot **schema** read-only consume only, tool_call_dedup) — STOP escalate
- ❌ Modificar `eval_simulator_*` DB schema o models PRE-EXISTING (Stories B/E/F preserved — Story H reads only)
- ❌ Modificar Story F aggregator code (consume cascade only — `unconverged: true` flag set on partial run)
- ❌ Modificar `core/config.py` defaults (env vars only — `.claude/rules/anti-default-flip-audit.md`)
- ❌ NEW DDL / Alembic migration (Story H reads existing tables — no schema bump)
- ❌ NEW SQLA 2.0 model (Story H reads via existing `EvalSimulatorLlmCallModel` + `EvalSimulatorGradeModel` Stories B/E)
- ❌ Mirror production `BudgetGuard` shared/billing pattern code (paradigm distinto cement §2 audit — eval-only synthetic vs runtime per-tenant)
- ❌ Mirror production `BudgetExceeded` exception (production HTTP 402 mapping; Story H eval-only `BudgetCapExceededError` distinct semantics)
- ❌ Mirror production `BudgetGuardingLLMService` LangChain wrapper (no wrapper — caller invokes guard manually)
- ❌ Mirror production `estimate_llm_cost` cost_estimator (different formula: NO 1.10x multiplier + input_tokens param vs prompt str)
- ❌ Cross-module imports excepto `copilot` exception general (Story H imports allowed: `tests/agentic_evals/sales_agent/{simulator,goldens}/`, `src/core/{config,database}`, `src/shared/{domain/datetime_utils,agent_observability/recording/sanitization,agent_observability/persistence/pricing_snapshot_repository}`, `src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_grade}` — read-only models)
- ❌ Re-running simulations (Story B owns)
- ❌ Re-grading rubrics (Story E owns)
- ❌ Aggregating pass^K (Story F owns — Story H emits abort signal cascade only)
- ❌ LLM calls of any kind (read-only guard invariant cement D-BE-8)
- ❌ FE component for visualization (Story H BE-only service-story)
- ❌ Streamlit dashboard for budget tracking (separate observability story)
- ❌ Auto-scaling cap based on model price changes (manual env var update — D7 cement)
- ❌ ML cost projection (rule-based estimator suficiente — D4 over-estimate strict)
- ❌ Per-tenant cost cap eval (eval is global suite-scoped — D-BE-7 cement spec § Out of scope)
- ❌ Slack/email notifications (console + structlog only — spec § Out of scope)
- ❌ `// eslint-disable` / `# noqa` sin justification comment
- ❌ `any` TS / `Any` Python loose types — strict typing
- ❌ Default exports (N/A FE for Story H)
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git commit --no-verify` — pre-commit hook native enforced
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia
- ❌ Modificar test_simulator_public_api_surface.py more than allowlist 8→9 expand (single addition `check_budget_before_call` cement)
- ❌ Editar Story B/C/E/F existing arch fitness gates (extend ratchet OK puntual, edit pre-existing logic NO)
- ❌ Forget asyncio Task cancel at run end (memory leak risk — try/finally pattern obligatorio per §3.4 docstring)
- ❌ `_DISABLE=1` in CI environments (only local dev — CI workflows MUST `unset SALES_AGENT_EVAL_BUDGET_CAP_DISABLE` per Open risk MEDIUM)

## Files in scope (builders edit ONLY these)

### NEW files (Story H creates)

#### Pydantic schemas + guard + helpers (BE test-infra)

- `backend/tests/agentic_evals/sales_agent/budget/__init__.py` (NEW — public API exports per `__all__` from guard.py)
- `backend/tests/agentic_evals/sales_agent/budget/_schema.py` (NEW — `BudgetState`, `BucketState`, `TierState`, `AbortContext`, `BudgetWarning`, `BudgetCapExceededError`)
- `backend/tests/agentic_evals/sales_agent/budget/guard.py` (NEW — `check_budget_before_call`, `compute_remaining_budget`, `_load_caps`, env var loader, `__all__` export list)
- `backend/tests/agentic_evals/sales_agent/budget/_internal/__init__.py` (NEW — empty)
- `backend/tests/agentic_evals/sales_agent/budget/_internal/cost_estimator.py` (NEW — over-estimate strict + LiteLLM pricing fallback)
- `backend/tests/agentic_evals/sales_agent/budget/_internal/sweep.py` (NEW — periodic asyncio Task + post-facto detection)

#### Tests (BE test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/budget/conftest.py` (NEW — fixtures: `eval_budget_test_session`, `synthetic_llm_call_rows`, `synthetic_grade_rows`, `synthetic_pricing_snapshot`)
- `backend/tests/agentic_evals/sales_agent/budget/test_schema.py` (NEW — Pydantic schema unit tests: construction, frozen, extra forbid, Literal validation, Decimal precision)
- `backend/tests/agentic_evals/sales_agent/budget/test_cost_estimator.py` (NEW — over-estimate strict formula + fallback rates + parametrize over 10 (input, max_output, expected_cost) cases)
- `backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py` (NEW — Scenarios 1+2+3 contract tests: within_cap_no_abort + per_bucket_grader_cap_aborts + disable_flag_short_circuits + tier_warning_event + exit_code_2 + idempotent + cascades_unconverged_signal)
- `backend/tests/agentic_evals/sales_agent/budget/test_budget_state.py` (NEW — Pydantic state aggregation: per_bucket_aggregation + budget_summary_json_persisted + aborted_partial_report_persisted + only_eval_simulator_tables_read + warning_message_sanitize_payload_applied + partial_report_cited_abort_bucket)
- `backend/tests/agentic_evals/sales_agent/budget/test_sweep.py` (NEW — Scenario 4 adversarial: periodic_sweep_detects_bypass + bypass_detected_structlog_event + sweep_runs_at_configured_interval)
- `backend/tests/agentic_evals/sales_agent/budget/test_guard.py` (NEW — read-only invariant integration: `test_guard_runs_produce_zero_llm_call_writes` integration with synthetic fixtures)

#### Architecture fitness gates (BE — 2 NEW + 1 UPDATE)

- `backend/tests/architecture/test_eval_llm_calls_use_budget_guard.py` (NEW — AST static scan Layer 1 enforcement; empty allowlist shrink-only)
- `backend/tests/architecture/test_budget_state_schema_complete.py` (NEW — Pydantic ⊆ JSON schema fields match cement; empty allowlist)

### EDIT files (Story H extends additively)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (EDIT — H9 expand 8→9 names: add `check_budget_before_call` import + add to `__all__` list — single addition; sorted alphabetically maintained)
- `backend/tests/architecture/test_simulator_public_api_surface.py` (EDIT — `_EXPECTED_PUBLIC_NAMES` frozenset 8→9: add `check_budget_before_call` + update cardinality test from `len == 8` to `len == 9`)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (EDIT — append `BudgetState v1` anchor entry to SCHEMA_MIGRATIONS registry; bump `CURRENT_SCHEMA_VERSIONS` dict adds `"BudgetState": 1`)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (EDIT — append eval block fields per §3.9; post-merge by /pm only — NO builder action; T-6 ticket flagged)
- `docs/product/modules/sales-agent.md` (EDIT — narrative addition 1-2 sentences; post-merge by /pm only — T-6 ticket flagged)
- `.claude/rules/auditor-downstream-regression.md` (EDIT — append entry per §11; post-merge by /pm only — T-6 ticket flagged)

## Files NEVER touched (escalate to Chris if needed)

- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` ← H10 byte-equal Story B
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency,customer_node,customer_persona_prompt,personas_loader}.py` ← Story B/C cement (Story H EDITS solo `schema_migrations.py` anchor entry append + `simulator/__init__.py` H9 expand — el resto NO TOUCH)
- `backend/tests/agentic_evals/sales_agent/simulator/{state.py,result.py,actor_profile.py,termination.py}` ← Story B cement
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/{actor_profiles,tenant_seeded}.py` ← Story B cement
- `backend/tests/agentic_evals/sales_agent/grader/**` ← Story E territory (planned/refined; Story H consumes via SQL queries on `eval_simulator_grade` table, NOT via Python imports of grader module)
- `backend/tests/agentic_evals/sales_agent/pass_k/**` ← Story F territory (Story H emits abort signal cascade only; NO direct imports — orchestrator handles)
- `backend/tests/agentic_evals/sales_agent/goldens/**/*.yaml` ← Story D territory (immutable post-commit per Story F D16 + pre-commit hook Section 9)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_trace_event,eval_simulator_grade,eval_simulator_grade_cache,eval_synthetic_tenants,eval_pass_k_summary}.py` ← Stories B/E/F cement; Story H reads via existing models (no NEW model)
- `backend/src/shared/agent_observability/**` ← shared abstractions; Story H consumes via inheritance/imports (sanitize_payload + PricingSnapshotRepository only)
- `backend/src/shared/billing/**` ← production runtime per-tenant BudgetGuard / cost_estimator paradigm — DIFFERENT scope cement §2 audit. Story H eval-only synthetic NO mirror
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording}/` ← runtime sales_agent (NO touch)
- `backend/src/modules/copilot/**` ← agentic builder territory only (NO touch — Story H BE-only)
- `backend/src/core/config.py` ← R31 anti-default-flip-audit (Story H NO flag in core/config.py — env vars only)
- `backend/alembic/versions/**` ← Story H NO new migration (reads existing tables Stories B/E)
- `backend/tests/fixtures/eval/tenants/{dialect_catalog.yaml,loader.py}` ← Story A cement
- `frontend/**` ← N/A esta story FE no toca (BE-only service-story)
- `client_simulator/src/simulator/*.py` ← D6 preservation gate Story B (sha256 unchanged)
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression entry add via T-6) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)

1. `01-spec.md` (re-read 4 scenarios + decisions D1-D13 mid-build; ratified Chris 2026-05-08T11:00Z)
2. `03-arch.md` (this story consolidated arch — Pydantic + cost_estimator + guard + sweep + arch fitness gates + H9 expand)
3. `04-validators.yaml` (test commands ejecutables — 25 validators across 3 categories)

### Story B/C/E/F references (Story H consumes, do NOT mirror)

- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md` (Story B AGENTIC arch — H1-H10 invariants + observability; cost-bucket H7 cement)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-be.md` (Story B BE arch — DDL pattern Alembic 125 — `eval_simulator_llm_call.cost_usd` column)
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md` (Story E arch — `eval_simulator_grade` table + `cost_usd_total` column)
- `docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md` (Story F arch — read-only aggregator precedent + unconverged cascade pattern D9)
- `docs/product/stories/sales-agent-eval-pass-k-tracking/05-guidelines.md` (Story F patterns precedent — service-story BE-only test-infra)

### Skills (per surface)

- `backend-expert` — DDD patterns, arch fitness ratchet, idempotent migrations (N/A here — no DDL), Pydantic v2 patterns
- `tessl__pytest-api-testing` — pytest-asyncio, fixtures, parametrize, AsyncSession test patterns
- `tessl__fastapi` — Pydantic v2 patterns (ConfigDict frozen=True, Literal forward-compat, BaseModel inheritance)
- `tessl__graceful-degradation` — Rule 1 timeouts (sweep DB query) + Rule 2 fallback (pricing snapshot missing) + Rule 6 log failures with context

### Rules (cement before each Edit)

- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file; production BudgetGuard / cost_estimator different paradigm cement §2 audit)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entry post-merge (T-6) with budget/guard path + downstream tests
- `.claude/rules/architectural-fitness.md` — 2 NEW gates empty allowlist shrink-only + 1 UPDATE allowlist 8→9
- `.claude/rules/backend-ddd.md` — Story H NO touches `domain/application/api` of sales_agent (BE test-infra path only)
- `.claude/rules/backend-migrations.md` — N/A Story H (no DDL)
- `.claude/rules/copilot-observability.md` — best-effort writes try/except + structlog warning (guard NO writes to LLM tables — invariant)
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — sales_agent voice cement preserved (Story H NO touch personality_profiles)
- `.claude/rules/spanish-text.md` — `BudgetWarning.message` español neutro LATAM
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer
- `.claude/rules/tenant-isolation.md` — N/A Story H (eval-only suite-scoped, NOT per-tenant)
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches
- `.claude/rules/anti-default-flip-audit.md` — Story H NO flag flip in core/config.py — env vars only

### Templates (consult during ticket execution)

- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Story H NO migration (no `docker exec ... alembic` needed)
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:

1. **Pydantic schemas** RED → GREEN (T-1 — 6 types frozen=True + Literal forward-compat + SCHEMA_MIGRATIONS anchor entry; tests cover construction + extra forbid + frozen mutation + Literal validation + Decimal precision)
2. **cost_estimator** RED → GREEN (T-2 — over-estimate strict formula + LiteLLM pricing snapshot integration + fallback rates; tests parametrize 10 cases + fallback path)
3. **guard** RED → GREEN (T-3 — `check_budget_before_call` + `compute_remaining_budget` + env var loader; tests cover Scenarios 1+2+3 + idempotent + cascade signal)
4. **sweep** RED → GREEN (T-4 — periodic asyncio Task + post-facto detection + lifecycle; tests cover Scenario 4 adversarial + interval override + clean cancel)
5. **arch fitness gates** RED → GREEN (T-5 — `test_eval_llm_calls_use_budget_guard.py` + `test_budget_state_schema_complete.py` empty allowlists; tests AST scan + Pydantic ⊆ JSON schema)
6. **simulator __init__ expand + integration tests + JSON output + capability YAML extend + module narrative + downstream regression rule** (T-6 — H9 expand 8→9 + scenarios full integration + JSON persist on abort + post-merge docs reconciliation by /pm)

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py` — env vars only).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:

- `done -> docs/product/stories/sales-agent-eval-cost-budget-cap/T-3-result.md`
- `blocked -> docs/product/stories/sales-agent-eval-cost-budget-cap/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py:42 [BudgetCapExceededError raised but post_facto field=False expected True]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE test-infra (Pydantic schemas + SCHEMA_MIGRATIONS anchor) | false | builder-backend Sonnet | Pydantic v2 declarative + Literal forward-compat — declarative |
| T-2 | BE test-infra (cost_estimator over-estimate strict) | false | builder-backend Sonnet | Decimal arithmetic + sqlalchemy accessor — straightforward |
| T-3 | BE test-infra (guard 2 public APIs + env var loader) | false | builder-backend Sonnet | SQL sum queries + dict aggregation + Pydantic instantiation — read-only deterministic |
| T-4 | BE test-infra (periodic sweep asyncio Task) | false | builder-backend Sonnet | asyncio.create_task pattern canonical Python 3.12. **Sonnet OK; if iteration cap reached on Task lifecycle (cancellation leak / shutdown race) → escalate /pm para Opus override.** |
| T-5 | BE test-infra (2 NEW arch fitness gates) | false | builder-backend Sonnet | AST static scan + Pydantic introspection — declarative pattern Story F precedent. **Sonnet OK; if AST walk regex precision blocks → escalate /pm para Opus override.** |
| T-6 | BE test-infra (simulator __init__ H9 expand + integration tests + capability YAML + module narrative + downstream regression rule update) | false | builder-backend Sonnet (arch tests) + /pm post-merge (capability YAML + module narrative + rule update) | Documentation reconciliation + arch fitness ratchet + scenario integration tests — declarative |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris autonomy mandate. Story H = service-story BE-only `production_code: false`, simple deterministic guard pipeline Python (zero LLM/agentic/LangGraph). **Sonnet OK todos 6 tickets.** Si en build encuentra bloqueo en T-4 sweep asyncio Task lifecycle o T-5 arch fitness AST scan → escalate /pm para Opus override puntual. PM confirma final routing antes Conv 2 arranca.

## Build dependency on Story E (HARD blocker)

Story H build BLOCKED on Story E build done:

- **Story E** `sales-agent-voice-fidelity-grader-runtime` — builds + provides `eval_simulator_grade` table + `cost_usd_total` column. Story H reads via SQL sum query.

**Decoupled build option**: T-1 through T-5 + arch fitness gates can build BEFORE Story E if synthetic test fixtures used (decouple data dependency). T-6 (integration scenarios + simulator __init__ expand) requires Story E build COMPLETE → H9 surface 7→8 must ship before Story H expands 8→9 (sequential — single-name expansion cement). PM/dev-team decides parallelization at build trigger.

## Sales_agent toolkit dependency (escalation path — N/A Story H)

Story H is read-only guard — does NOT depend on sales_agent runtime tools. If Stories C/D builds skip-with-escalation per Story C T-6/T-7 pattern, Story H still builds with synthetic fixtures + skip integration tests con `pytest.skip("Story E real grade rows needed for full integration")` until upstream lands.
