<!-- voseo-allowed: glosario reference cites prohibited voseo verbatim to teach contributors -->
# 05-guidelines.md — Story sales-agent-voice-fidelity-ci-gate

> /architect orchestrator delivered (2026-05-08T13:00Z). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N PRs/day)

### Backend (Python 3.12 + Pydantic v2 + SQLA 2.0 async)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` heredado Story B/E/F. Cero `class Config` inner. Frozen=True para immutability post-verdict.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`run_id`, `commit_sha`, `cadence`, `verdict`, `error_class`). Excepción: CLI script `print(...)` user-facing OK (bilingual: errors Spanish, structlog English).
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`. `created_at`/`started_at`/`completed_at` en GateVerdict = `utc_now()` (timezone-aware UTC).
- **`Decimal` para monetary** — `cost_usd_total`, `budget_warm_usd`, `budget_cold_usd` = `Decimal` USD only (eval-only synthetic; no multi-currency tenant data). `Decimal(str(value))` para conversion JSON → Decimal.
- **SQLA 2.0 async** — `select(EvalGateVerdictModel).where(...)` + `await session.execute(stmt)`. NUNCA `session.query()` (SA 1.x). Insert: `pg_insert(EvalGateVerdictModel).on_conflict_do_update(...)` UPSERT pattern (PK composite invalidation). Read: `result.scalars().all()`.
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. CONSUMA Story B `run_simulation` API (subprocess), Story C `trial_policy_by_persona_kind` (import constant), Story D goldens YAML (read-only golden_set_hash compute), Story E `eval_simulator_grade` rows (read-only via SQL), Story F `pass_k_report.json` + `--validate-strict` (subprocess invoke + JSON read), Story H `budget_summary.json` (JSON read) + exit code 2 cascade. NO mirror grading / runner / persona loader / pass^K / budget guard.
- **Raw SQL idempotent migration** — `op.execute("CREATE TABLE IF NOT EXISTS ...")` + `op.execute("CREATE INDEX IF NOT EXISTS ...")`. NUNCA `op.create_table()` o `sa.Enum(create_type=True)`.
- **`from __future__ import annotations` PERMITIDO en TODOS los Story G files** — orchestrator NO es LangGraph runtime (no introspection caveat de Story B T-4 cement). Es deterministic Python pipeline.
- **subprocess invocation** — `subprocess.run([...], check=False, capture_output=True, text=True, timeout=cadence_config.wall_clock_max_seconds)` — NEVER `shell=True`, NEVER unbounded timeout. Capture stderr for diagnostic. Stories B+E+F+H entry points invoked via subprocess (pipeline orchestration).
- **`actions/github-script@v7`** — JavaScript inline script para PR comment idempotent edit (Markdown listComments + updateComment + createComment fallback). NEVER `gh pr comment` CLI (extra installation + token management overhead).

### Read-only orchestrator invariant (CRITICAL — D-BE-9 cement)

- **Cero LLM imports** en `orchestrator.py` + `_internal/cadence_config.py` + `_internal/inputs_hasher.py` + `comment_generator.py` + `scripts/run_eval_gate.py`:
  - ❌ `import litellm`
  - ❌ `import anthropic`
  - ❌ `import openai`
  - ❌ `from litellm import ...`
  - ❌ `from anthropic import ...`
  - ❌ `from openai import ...`
- Story F arch fitness gate `test_aggregator_no_llm_calls.py` extended to scan `ci_gate/` paths (allowlist empty shrink-only).
- Orchestrator solo escribe a `eval_gate_verdict` table. CERO writes a `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `eval_pass_k_summary`, `copilot_llm_call`, `sales_agent_llm_call`. Verificado via integration test `test_orchestrator_zero_llm_call_writes` (DB query post-orchestration: zero NEW rows con timestamp > test_start_at en copilot/sales_agent llm_call tables — Stories E grader writes accounted to grader bucket separate from gate orchestrator).

### Cadence config declarative (D-BE-7 + D14 cement)

- **`CADENCE_CONFIGS` dict cement byte-equal** — 3 cadences (pr/nightly/monthly):
  ```python
  CADENCE_CONFIGS: Final[dict[str, CadenceConfig]] = {
      "pr": CadenceConfig(cadence="pr", threshold_pass_k_rate=..., threshold_bloom_stage=..., goldens_scope="smoke_5", k_trials_uniform=1, budget_warm_usd=Decimal("30.00"), budget_cold_usd=Decimal("80.00"), mode="block", wall_clock_max_seconds=300),
      "nightly": CadenceConfig(cadence="nightly", threshold_pass_k_rate=..., threshold_bloom_stage=..., goldens_scope="full_20_30", k_trials_uniform=None, budget_warm_usd=Decimal("150.00"), budget_cold_usd=Decimal("500.00"), mode="block", wall_clock_max_seconds=1800),
      "monthly": CadenceConfig(cadence="monthly", threshold_pass_k_rate=..., threshold_bloom_stage=..., goldens_scope="full_plus_adversarial", k_trials_uniform=None, budget_warm_usd=Decimal("200.00"), budget_cold_usd=Decimal("700.00"), mode="warning", wall_clock_max_seconds=3600),
  }
  ```
- **3 env var canonical pattern**: `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_<CADENCE>` (UPPER_SNAKE_CASE):
  - `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR=0.65`
  - `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_NIGHTLY=0.70`
  - `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_MONTHLY=0.75`
- **`PR_SMOKE_GOLDEN_IDS` tuple frozen** — exactly 5 entries (1 per tenant × happy persona only) — D15 cement.
- **`SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE` env var** — auto-detected from GitHub Actions trigger (pull_request → pr / cron 0 2 * * * → nightly / cron 0 2 1 * * → monthly); override for local debug.
- Arch fitness gate `test_gate_threshold_defaults_protected.py` enforces dict + env var defaults + budget caps + wall-clock max + smoke goldens count + 3-cadences-only byte-equal.

### inputs_hash determinism (D9 cement)

- **Composition order frozen** — sha256 hex of canonical JSON (`json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)`):
  ```python
  payload = {
      "pass_k_report": pass_k_report,            # Story F output JSON content
      "budget_summary": budget_summary,           # Story H output JSON content
      "golden_set_hash": golden_set_hash,         # sha256 hex of all goldens YAML in cadence scope
      "judge_set_hash": judge_set_hash,           # sha256 hex of judge models + weights + temperatures (Story E)
      "rubric_set_hash": rubric_set_hash,         # sha256 hex of rubric MDs + version + threshold
      "cadence": cadence,                          # str literal
      "commit_sha": commit_sha,                    # 40-char or 7-char short SHA
  }
  canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
  return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
  ```
- **64-char lowercase hex output** (Pydantic Literal validator: `Field(min_length=64, max_length=64)`).
- **Stable across runs** — Test `test_gate_inputs_hash_deterministic_across_runs` invoca 100x same inputs, asserts all hashes identical.
- **Tampering detection**: re-compute hash from raw inputs + compare vs cached `EvalGateVerdict.inputs_hash`. Mismatch → `GateValidationError`.
- **Pattern reuse from Story F** (NOT mirror): Story F `compute_inputs_hash` composes per-cell (grade_rows + trace_events + golden_yaml). Story G `compute_gate_inputs_hash` composes per-gate-run (cross-artifact: pass_k_report + budget_summary + 3 set hashes + cadence + commit_sha). Different inputs = separate function = separate file (anti-duplication §0 audit row 7 cement).

### Cache key composition (D6 cement)

- **Composite cache key**: `(commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence)`. SQL select on this composite + match → cache_hit=True returned without re-running pipeline.
- **Invalidation precision**: changing ANY of 5 components → new row created (UPSERT replaces by PK `(commit_sha, cadence)`). Test `test_cache_invalidation_on_input_change` mutates each component, asserts cache miss.
- **Re-run idempotency**: re-running same PR commit + same cadence → cache_hit short-circuits via cache lookup (Step 3 in orchestrator before subprocess invocation).

### GitHub Actions workflow contract (D11 + D14 cement)

- **Workflow file**: `.github/workflows/voice-fidelity-gate.yml`
- **Permissions minimal** (least-privilege): `contents: read` + `pull-requests: write` (PR comment posting only)
- **Triggers**:
  - `pull_request.paths`: 6 canonical paths (D14 cement — modifying requires R29 cascade approval)
  - `schedule.cron`: `'0 2 * * *'` (nightly) + `'0 2 1 * *'` (monthly 1st)
- **Required check name**: `voice-fidelity-gate-required` — branch protection rule configured separately (manual repo admin one-time setup post-merge per checklist in module narrative)
- **Secrets**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `KIMI_API_KEY`, `DEEPSEEK_API_KEY`, `EVAL_DATABASE_URL` — repo admin one-time setup post-merge
- **Timeout**: 75 minutes (monthly cadence wall-clock max 60min + buffer)
- **Idempotent PR comment**: marker `<!-- voice-fidelity-gate-comment -->` + `actions/github-script@v7` listComments + updateComment vs createComment (D7 cement — replace not append)

### PR comment generator templates (D7 + D17 cement)

- **4 verdict templates** Spanish neutro LATAM:
  - PASS — green checkmark + metrics table + cadence label + run_id link
  - FAIL — red X + metrics table + root cause Bloom stage + reproduce cmd + calibration ref
  - ABORTED_BUDGET — yellow warning + cost-bucket abort context + partial results + action required
  - WARNING_ONLY — yellow info + same as FAIL but mode=warning (Chris semestral review)
- **Idempotent on re-run** — workflow YAML invokes `actions/github-script@v7` to post/edit comment by marker ID match (NOT new comment per re-run).
- **Spanish neutro** — sin voseo. Glosario aplicado verbatim:
  - ✅ "Veredicto gate" / "Reporte completo" / "Reproducir local" / "Acción requerida: investiga"
  - ✅ "ABORTED (budget cap exceeded)" / "Resultados parciales capturados"
  - ❌ NO voseo: `tenés/podés/mirá/etc` → `tienes/puedes/mira/etc`

### PII sanitization (consume only — D-BE-9 cement)

- `FailingGoldenDetail.flaky_evidence` strings cited verbatim from Story F `flaky_evidence` (already sanitized by Story F D-BE-15 `sanitize_payload`). Story G consumes already-sanitized strings — NO re-sanitization needed (defense-in-depth via Story F).
- CLI script `print(...)` user-facing strings = Spanish neutro hardcoded templates (no dynamic PII insertion).

### Spanish neutro LATAM (`.claude/rules/spanish-text.md`)

- **CLI script + PR comment Markdown** → español neutro LATAM sin voseo:
  - `"Veredicto gate ({cadence}): {verdict}"` ✅
  - `"ERROR validación strict: {exc}"` ✅
  - `"Reproducir local"` ✅ (NOT `"Reproducí local"` voseo)
  - `"Acción requerida: investiga"` ✅ (NOT `"Tenés que investigar"` voseo)
- **Workflow YAML keys + structlog event names + Python identifiers** → English (technical layer).
- **Glosario voseo→neutro** aplicado en CLI strings + comment templates — ver `.claude/rules/spanish-text.md` § R2.
- **Test enforcement**: `test_pr_comment_no_voseo` greps comment templates for prohibited voseo strings — must return empty.

### Schema versioning forward-compat (D-BE-10 cement Story B H1 reuse)

- **`GateVerdict.schema_version: Literal[1] = 1`** cement v1.
- **`CadenceConfig.cadence: Literal["pr", "nightly", "monthly"]`** — Story I extends additively to `Literal["pr", "nightly", "monthly", "monthly_adversarial"]` (Literal forward-compat allows superset; NO bump v1→v2 needed).
- **`FailingGoldenDetail.persona_kind: Literal[...]`** — already 4 values (happy/nurture/unqualified/adversarial) cement Story C+I.
- Future bumps via `SCHEMA_MIGRATIONS` registry (Story B H1 reuse). Story G adds anchor entry `GateVerdict v1` (sentinel — no migrator function for v1).

### Tests (TDD obligatorio per `.claude/rules/tdd-mandatory.md`)

- **RED → GREEN → REFACTOR** per layer (orden estricto):
  1. **DDL idempotent migration + SQLA model** RED → GREEN (T-1 — Alembic 129 + EvalGateVerdictModel R5 schema-mirror; idempotency test re-run twice)
  2. **Pydantic schemas + cadence config** RED → GREEN (T-2 — GateVerdict + FailingGoldenDetail + CadenceConfig Pydantic v2 frozen + CADENCE_CONFIGS dict + PR_SMOKE_GOLDEN_IDS tuple)
  3. **inputs_hasher** RED → GREEN (T-3 — sha256 deterministic + 100x identity test + tamper test + cache key composition)
  4. **Orchestrator + comment_generator** RED → GREEN (T-4 — compute_gate_verdict + 4 verdict templates + cache lookup + UPSERT + integration with synthetic Stories B/E/F/H artifacts)
  5. **CLI script + GitHub Actions workflow** RED → GREEN (T-5 — argparse + JSON output + exit codes 0/1/2 + YAML workflow + PR comment posting via actions/github-script@v7)
  6. **Arch fitness gate + capability YAML + module narrative + downstream regression rule** (T-6 — test_gate_threshold_defaults_protected + capability YAML eval block + module narrative branch protection checklist + auditor-downstream-regression entry; post-merge by /pm)
- **Pytest markers** — `@pytest.mark.asyncio` para async tests (orchestrator integration). Cero `@pytest.mark.eval` (Story G NO LLM).
- **Pytest fixtures** — `eval_gate_test_session` (AsyncSession + tear-down rollback), `synthetic_pass_k_report` (Story F output fixture), `synthetic_budget_summary` (Story H output fixture), `synthetic_goldens_dir` (Story D fixture). Story G can build BEFORE Stories E/F/H build if synthetic fixtures used (decouple build dependency for T-1+T-2+T-3+T-6).

### Default flag flips (anti-default-flip-audit R29 cascade — N/A directo Story G)

- Story G NO modifica `core/config.py` defaults (env vars live in `cadence_config.py` declarative dict).
- BUT — arch fitness gate `test_gate_threshold_defaults_protected.py` enforces threshold defaults frozen — PR modifying defaults triggers gate FAIL → CI hard-fail (R29 cascade defense Layer 4).
- If Story G v2 ever flipea cadence_config.py default → MUST follow `.claude/rules/anti-default-flip-audit.md` 4 steps (Step 1 grep tests path viejo, Step 2 update mocks path nuevo, Step 3 run suite both flag values, Step 4 commit body docs).

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()`
- ❌ Hardcoded `'USD'` — N/A Story G (Decimal cost only, no multi-currency)
- ❌ Hardcoded model names — N/A Story G (no LLM calls)
- ❌ Modificar `simulator/__init__.py` `__all__` (frozen 9 names post Story H — Story G expand NADA)
- ❌ Modificar `LLM_ROLE_BY_SITE` SSoT (no LLM calls)
- ❌ Modificar `personality_profiles.system_instruction` (sales-agent-expert §3 protected)
- ❌ Modificar §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup) — STOP escalate
- ❌ Modificar `eval_simulator_*` DB schema o models PRE-EXISTING (R5 Story B/E/F preserved — Story G adds NEW table `eval_gate_verdict` only)
- ❌ Modificar `eval_pass_k_summary` schema (Story F territory — read-only via SQL)
- ❌ Modificar `BudgetState` Pydantic schema (Story H territory — read-only via JSON)
- ❌ Modificar Story D goldens YAML content (read-only — `golden_set_hash` snapshot only; mutation detected by Story F hook Section 9 + `--validate-strict`)
- ❌ Modificar Story C `_TRIAL_POLICY_BY_PERSONA_KIND` cement (3/1/3/3) — Story G respects, NO override
- ❌ Modificar Story E `MajEvalScore` schema (consume read-only via SQL queries)
- ❌ Modificar Story B `eval_simulator_trace_event` schema (consume read-only)
- ❌ Editar frozen golden v1 fixture `_fixtures/golden_v1_simulation_result.yaml` (H10 Story B byte-equal)
- ❌ Editar Story B/C/E/F existing arch fitness gates (extend ratchet OK, edit pre-existing logic NO)
- ❌ Mirror `EvalSimulatorObservabilityContext` desde Story B (NO USED — orchestrator zero LLM, no callback handler needed)
- ❌ Mirror grading logic desde Story E (CONSUME via SQL queries on eval_simulator_grade table)
- ❌ Mirror simulation runner desde Story B (CONSUME via subprocess invocation `run_simulation` API)
- ❌ Mirror personas loader desde Story C (CONSUME via import constant `_TRIAL_POLICY_BY_PERSONA_KIND`)
- ❌ Mirror golden authoring logic desde Story D (CONSUME via YAML safe_load read-only)
- ❌ Mirror pass^K aggregator desde Story F (CONSUME via subprocess `compute_pass_k_report.py --validate-strict` + JSON read pass_k_report.json)
- ❌ Mirror inputs_hasher composition desde Story F (REUSE PATTERN — separate function with different inputs justified per anti-duplication §0 row 7)
- ❌ Mirror budget guard desde Story H (CONSUME via JSON read budget_summary.json + exit code 2 cascade)
- ❌ Mirror cost aggregator from `CopilotCostAggregator` o `SalesAgentCostAggregator` (NO TOUCH — paradigma ortogonal: production billing vs test-infra eval)
- ❌ Mirror llm-eval-gate.yml workflow (NO TOUCH — orthogonal copilot classifier/summarizer paradigm; Story G NEW workflow voice-fidelity-gate.yml)
- ❌ `yaml.load()` sin Loader (security) — use `yaml.safe_load`
- ❌ TypedDict (no LangGraph state — Pydantic only)
- ❌ HTTP webhook invocation (no agentic — pure orchestrator)
- ❌ subprocess `shell=True` (security) — always list args + check=False + capture_output=True + timeout
- ❌ Cross-module imports excepto `copilot` (Story G imports allowed: `tests/agentic_evals/sales_agent/{simulator,goldens,grader,pass_k,budget}/`, `src/core/{config,database}`, `src/shared/{domain/datetime_utils,agent_observability/recording/sanitization}`, `src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_gate_verdict` — Story G NEW model file)
- ❌ Modificar `simulator/__init__.py` (Story G orchestrator NO se exporta via simulator surface — vive en `ci_gate/__init__.py` package separado)
- ❌ Re-running simulations (Story B owns)
- ❌ Re-grading rubrics (Story E owns)
- ❌ Re-computing pass^K (Story F owns)
- ❌ Re-computing budget tracking (Story H owns)
- ❌ LLM calls of any kind (read-only orchestrator invariant cement D-BE-9)
- ❌ Statistical tests (chi-square, p-values, Bayesian) — verdict logic threshold compare deterministic
- ❌ FE component for visualization (Story G BE-only service-story)
- ❌ Streamlit dashboard for verdict trends (separate observability story)
- ❌ Slack/email notifications (PR comment + structlog only — outcome cement)
- ❌ Custom GitHub App for branch protection bypass (per WebSearch — workarounds exist but out of scope; manual setup checklist suffices)
- ❌ LLM-summarized PR comment narrative (deterministic Markdown templates suffice; LLM summary = NEW story)
- ❌ Auto-retry on transient failures (manual re-run via GitHub Actions UI)
- ❌ Per-PR custom thresholds (frozen per cadence)
- ❌ `// eslint-disable` / `# noqa` sin justification comment (N/A FE for Story G)
- ❌ `any` TS / `Any` Python loose types — strict typing
- ❌ Default exports (N/A FE for Story G)
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git commit --no-verify` — pre-commit hook native enforced
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia

## Files in scope (builders edit ONLY these)

### NEW files (Story G creates)

#### Migration + SQLA model (BE test-infra — R5 schema-mirror exception)

- `backend/alembic/versions/129_add_eval_gate_verdict_table.py` (NEW migration — raw SQL idempotent)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_gate_verdict.py` (NEW SQLA 2.0 async model — R5 schema-mirror)

#### Pydantic schemas + cadence config + helpers (BE test-infra)

- `backend/tests/agentic_evals/sales_agent/ci_gate/__init__.py` (NEW — empty or minimal `__all__` with public functions only)
- `backend/tests/agentic_evals/sales_agent/ci_gate/_schema.py` (NEW — `GateVerdict`, `FailingGoldenDetail`, `CadenceConfig` + `GateValidationError`)
- `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/__init__.py` (NEW — empty)
- `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/cadence_config.py` (NEW — `CADENCE_CONFIGS` dict + `PR_SMOKE_GOLDEN_IDS` tuple + `get_cadence_config` helper)
- `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/inputs_hasher.py` (NEW — `compute_gate_inputs_hash` + `compute_golden_set_hash` + `compute_judge_set_hash` + `compute_rubric_set_hash`)
- `backend/tests/agentic_evals/sales_agent/ci_gate/orchestrator.py` (NEW — `compute_gate_verdict` + Stories B/E/F/H subprocess orchestration + cache lookup + UPSERT)
- `backend/tests/agentic_evals/sales_agent/ci_gate/comment_generator.py` (NEW — Markdown PR comment templating Spanish neutro 4 verdict templates)

#### CLI script (BE)

- `backend/scripts/run_eval_gate.py` (NEW — CLI entry point + argparse + JSON output + exit codes 0/1/2 + structlog setup)

#### GitHub Actions workflow (CI infra)

- `.github/workflows/voice-fidelity-gate.yml` (NEW — workflow YAML + path filters + cron schedule + required check name + 5 secrets)

#### Tests (BE test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/ci_gate/test_orchestrator.py` (NEW — Scenarios 1+2+3 contract tests + cache lookup + cache invalidation + idempotency + audit trail + zero LLM writes integration)
- `backend/tests/agentic_evals/sales_agent/ci_gate/test_comment_generator.py` (NEW — 4 verdict templates: PASS/FAIL/ABORTED/WARNING + Spanish neutro grep + idempotent edit assertion)
- `backend/tests/agentic_evals/sales_agent/ci_gate/test_cadence_config.py` (NEW — CADENCE_CONFIGS byte-equal cement + 3 cadences only + threshold env var override)
- `backend/tests/agentic_evals/sales_agent/ci_gate/test_inputs_hasher.py` (NEW — sha256 deterministic 100x identity + tamper detection per component + golden_set_hash scope filter)
- `backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_bypass_defenses.py` (NEW — Scenario 4 adversarial: 5 layers defense)
- `backend/tests/scripts/test_run_eval_gate.py` (NEW — CLI integration: exit codes 0/1/2 + JSON output schema + --validate-strict mode + partial results on abort)

#### Architecture fitness gate (BE — 1 NEW)

- `backend/tests/architecture/test_gate_threshold_defaults_protected.py` (NEW — 5 invariant tests: threshold env var defaults + budget caps + wall-clock max + smoke goldens count + 3-cadences-only)

### EDIT files (Story G extends additively)

- `backend/tests/architecture/test_aggregator_no_llm_calls.py` (EDIT — extend Story F gate scan to include `ci_gate/` paths; allowlist empty shrink-only)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (EDIT — append `GateVerdict v1` anchor entry to SCHEMA_MIGRATIONS registry; bump `CURRENT_SCHEMA_VERSIONS` dict adds `"GateVerdict": 1`)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (EDIT — append eval block fields per §11; post-merge by /pm only — NO builder action; T-6 ticket flagged)
- `docs/product/modules/sales-agent.md` (EDIT — narrative addition 1-2 sentences + branch protection setup checklist; post-merge by /pm only — T-6 ticket flagged)
- `.claude/rules/auditor-downstream-regression.md` (EDIT — append 3 entries per §11; post-merge by /pm only — T-6 ticket flagged)

## Files NEVER touched (escalate to Chris if needed)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` ← H9 surface frozen 9 names Stories B/E/H
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` ← H10 byte-equal Story B
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency,customer_node,customer_persona_prompt,personas_loader}.py` ← Story B/C cement; Story G EDITS solo `schema_migrations.py` (anchor entry append) — el resto NO TOUCH
- `backend/tests/agentic_evals/sales_agent/simulator/{state.py,result.py,actor_profile.py,termination.py}` ← Story B/C cement; Story G NO modify
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/{actor_profiles,tenant_seeded}.py` ← Story B cement
- `backend/tests/agentic_evals/sales_agent/grader/**` ← Story E territory (refined; Story G consumes via SQL queries on `eval_simulator_grade` table, NOT via Python imports of grader module)
- `backend/tests/agentic_evals/sales_agent/pass_k/**` ← Story F territory (refined; Story G consumes via subprocess `compute_pass_k_report.py` + JSON read `pass_k_report.json`)
- `backend/tests/agentic_evals/sales_agent/budget/**` ← Story H territory (refined; Story G consumes via JSON read `budget_summary.json` + exit code 2 cascade)
- `backend/tests/agentic_evals/sales_agent/goldens/**/*.yaml` ← Story D territory (immutable post-commit per D16 + Story F D15 cement; Story G computes golden_set_hash read-only)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/{eval_simulator_llm_call,eval_simulator_trace_event,eval_simulator_grade,eval_simulator_grade_cache,eval_synthetic_tenants,eval_pass_k_summary}.py` ← Stories B/E/F cement; Story G adds NEW model `eval_gate_verdict.py` only
- `backend/src/shared/agent_observability/**` ← shared abstractions; Story G consumes via inheritance/imports (sanitize_payload only via Story F output passthrough)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording}/` ← runtime sales_agent (NO touch)
- `backend/src/modules/copilot/**` ← agentic builder territory only (NO touch — Story G BE-only)
- `backend/src/core/config.py` ← R29 anti-default-flip-audit (Story G NO flag in core/config.py — defaults live in `cadence_config.py` declarative dict)
- `backend/alembic/versions/{0..128}*.py` ← pre-existing migrations (Story G adds NEW 129 only)
- `backend/tests/fixtures/eval/tenants/{dialect_catalog.yaml,loader.py}` ← Story A cement
- `frontend/**` ← N/A esta story FE no toca (BE-only service-story)
- `client_simulator/src/simulator/*.py` ← D6 preservation gate Story B (sha256 unchanged)
- `.github/workflows/llm-eval-gate.yml` ← orthogonal paradigm (copilot classifier/summarizer)
- `.github/workflows/{deploy-prod,e2e-tests,test-ssh}.yml` ← orthogonal workflows
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression entry add via T-6) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)

1. `01-spec.md` (re-read 4 scenarios + decisions D1-D15 mid-build; ratified Chris 2026-05-08T12:00Z)
2. `03-arch.md` (this story consolidated arch — DDL + SQLA + Pydantic + cadence config + orchestrator + comment generator + script + workflow YAML + arch fitness gate)
3. `04-validators.yaml` (test commands ejecutables — 32 validators across 3 categories)

### Story B/C/D/E/F/H references (Story G consumes, do NOT mirror)

- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md` (Story B AGENTIC arch — H1-H10 invariants + observability)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch-be.md` (Story B BE arch — DDL pattern Alembic 125)
- `docs/archive/2026/stories/sales-agent-personas-instrumented-runtime/03-arch.md` (Story C personas + heterogeneous K cement)
- `docs/archive/2026/stories/sales-agent-personas-instrumented-runtime/05-guidelines.md` (Story C patterns precedent)
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md` (Story E arch — `MajEvalScore` schema + `eval_simulator_grade` table + judge_registry config)
- `docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md` (Story F arch — `EvalPassKSummary` + `pass_k_report.json` + `--validate-strict` + inputs_hasher precedent pattern)
- `docs/product/stories/sales-agent-eval-cost-budget-cap/03-arch.md` (Story H arch — `BudgetState` + `budget_summary.json` + exit code 2 cascade)

### Skills (per surface)

- `backend-expert` — DDD patterns, R5 schema-mirror exception, arch fitness ratchet, idempotent migrations
- `tessl__pytest-api-testing` — pytest-asyncio, fixtures, parametrize, AsyncSession test patterns, subprocess testing
- `tessl__fastapi` — Pydantic v2 patterns (ConfigDict frozen=True, Literal forward-compat, BaseModel inheritance)
- `tessl__graceful-degradation` — Rule 2 fallback (subprocess timeouts, JSON parse errors, GitHub API rate limit)
- `playwright-expert` (read-only) — CI patterns reference (E2E workflows + secrets management)

### Rules (cement before each Edit)

- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file; orchestrator genuinamente NEW per audit §2; pattern reuse Story F inputs_hasher justified)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE 3 entries post-merge (T-6) with ci_gate/orchestrator + cadence_config + workflow YAML paths + downstream consumer Story I
- `.claude/rules/architectural-fitness.md` — 1 NEW gate empty allowlist shrink-only + Story F gate extension to scan ci_gate/
- `.claude/rules/backend-ddd.md` — schema-mirror exception R5 applies (model `eval_gate_verdict.py`)
- `.claude/rules/backend-migrations.md` — idempotent raw SQL `IF NOT EXISTS` cement
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — sales_agent voice cement preserved (Story G NO touch personality_profiles)
- `.claude/rules/spanish-text.md` — CLI strings + PR comment Markdown español neutro LATAM sin voseo
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer
- `.claude/rules/tenant-isolation.md` — `eval_gate_verdict` rows tenant-scoped via `failing_goldens[*].tenant_slug` field validated against Story C `_VALID_TENANT_SLUGS`
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches
- `.claude/rules/anti-default-flip-audit.md` — N/A directo Story G (no flag flip in core/config.py); BUT arch fitness gate enforces threshold defaults frozen (R29 cascade defense Layer 4)

### Templates (consult during ticket execution)

- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Migration: `docker exec visionarias_brain_dev alembic upgrade head` (only DB ops via Docker)
- CLI script: `cd backend && .venv/bin/python scripts/run_eval_gate.py --cadence pr --output _artifacts/eval_runs/<run_id>/`
- Workflow YAML lint: `cd backend && python -c 'import yaml; yaml.safe_load(open("../.github/workflows/voice-fidelity-gate.yml"))'`
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:

1. **DDL idempotent migration + SQLA model** RED → GREEN (T-1 — Alembic 129 + EvalGateVerdictModel R5 schema-mirror; idempotency test re-run twice)
2. **Pydantic schemas + cadence config** RED → GREEN (T-2 — GateVerdict + FailingGoldenDetail + CadenceConfig Pydantic v2 frozen + CADENCE_CONFIGS dict + PR_SMOKE_GOLDEN_IDS tuple + SCHEMA_MIGRATIONS anchor)
3. **inputs_hasher** RED → GREEN (T-3 — sha256 deterministic + 100x identity test + tamper test per component + cache key composition + scope filter)
4. **Orchestrator + comment_generator** RED → GREEN (T-4 — compute_gate_verdict + 4 verdict templates Spanish neutro + cache lookup + UPSERT + integration with synthetic Stories B/E/F/H artifacts)
5. **CLI script + GitHub Actions workflow** RED → GREEN (T-5 — argparse + JSON output + exit codes 0/1/2 + YAML workflow + PR comment posting via actions/github-script@v7 + workflow YAML lint + path filters byte-equal + cron schedule byte-equal)
6. **Arch fitness gate + capability YAML + module narrative + downstream regression rule + Story F gate extension** (T-6 — test_gate_threshold_defaults_protected NEW + extend test_aggregator_no_llm_calls.py + capability eval block + module narrative branch protection checklist + auditor-downstream-regression entries; post-merge by /pm + arch fitness gates 1 NEW)

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A directo esta story (no flag en `core/config.py`). BUT arch fitness gate enforces threshold defaults frozen (R29 cascade defense).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:

- `done -> docs/product/stories/sales-agent-voice-fidelity-ci-gate/T-3-result.md`
- `blocked -> docs/product/stories/sales-agent-voice-fidelity-ci-gate/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/ci_gate/test_orchestrator.py:42 [verdict assertion mismatch]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE test-infra (DDL migration + SQLA model R5) | false | builder-backend Sonnet | DDL declarative SQL + SQLA model schema-mirror — pure BE test-infra pattern Story F precedent |
| T-2 | BE test-infra (Pydantic schemas + cadence config + SCHEMA_MIGRATIONS anchor) | false | builder-backend Sonnet | Pydantic v2 declarative + Literal forward-compat + dict declarative — straightforward |
| T-3 | BE test-infra (inputs_hasher) | false | builder-backend Sonnet | sha256 + json.dumps deterministic — simple deterministic Python (Story F precedent reusable as pattern reference) |
| T-4 | BE test-infra (orchestrator + comment_generator + integration) | false | builder-backend Sonnet | subprocess orchestration + JSON parsing + Markdown templating + AsyncSession UPSERT — deterministic Python pipeline. **Sonnet OK; if iteration cap reached on subprocess error handling complexity → escalate /pm para Opus override.** |
| T-5 | CI infra (GitHub Actions workflow YAML + CLI script entry) | false | builder-backend Sonnet | declarative YAML + argparse + exit codes — declarative. **Sonnet OK; if required check semantics or actions/github-script PR comment idempotent edit fails iteration cap → escalate /pm para Opus override.** |
| T-6 | DOCS + arch fitness gates (1 NEW gate + extend Story F gate + capability YAML + module narrative + downstream regression rule) | false | builder-backend Sonnet (arch tests + arch fitness extend) + /pm post-merge (capability YAML + module narrative branch protection checklist + rule update) | Documentation reconciliation + arch fitness ratchet — declarative |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris autonomy mandate. Story G = service-story BE-only `production_code: false`, simple deterministic CI orchestration Python (zero LLM/agentic/LangGraph). **Sonnet OK todos 6 tickets.** Si en build encuentra bloqueo en T-4 orchestrator (subprocess error handling complexity) o T-5 GitHub Actions YAML (required check semantics + PR comment idempotent edit) → escalate /pm para Opus override puntual. PM confirms final routing antes Conv 2 arranca.

## Build dependency on Stories B+C+D+E+F+H (HARD blocker)

Story G build BLOCKED on Stories B+C+D+E+F+H build done — Story G es **last** en sub-épica eval-foundation:

- **Story B** `eval-foundation-simulator-homologation` — DONE 2026-05-08. Provides `run_simulation` API + `eval_simulator_trace_event` table + cost-bucket invariants + H1 SCHEMA_MIGRATIONS.
- **Story C** `sales-agent-personas-instrumented-runtime` — REFINED. Provides `_TRIAL_POLICY_BY_PERSONA_KIND` constant + 15 archetype-aware personas + Customer Prompt V2.
- **Story D** `sales-agent-goldens-3-tenants-dataset` — REFINED. Provides 20-30 goldens YAML files con ground truth (`expected_termination_reason`, `expected_tools_invoked`, `forbidden_tools`, `expected_voice_attributes`, `expected_min_distinct_objections_handled`).
- **Story E** `sales-agent-voice-fidelity-grader-runtime` — REFINED. Provides `eval_simulator_grade` table + `MajEvalScore` rows + judge_registry config + grader script entry.
- **Story F** `sales-agent-eval-pass-k-tracking` — REFINED. Provides `eval_pass_k_summary` table + `pass_k_report.json` + `compute_pass_k_report.py --validate-strict` CLI.
- **Story H** `sales-agent-eval-cost-budget-cap` — REFINED. Provides `BudgetState` schema + `budget_summary.json` output + exit code 2 cascade + budget_caps per cadence.

**Decoupled build option**: T-1 + T-2 + T-3 + T-6 (DDL + Pydantic + cadence config + arch fitness gate + capability YAML + module narrative) can build BEFORE Stories C/D/E/F/H if synthetic test fixtures used (decouple data dependency). T-4 (orchestrator integration) + T-5 (GitHub Actions workflow YAML + CLI script integration) require real Stories B+E+F+H artifacts → BLOCKED on upstream builds. PM/dev-team decides parallelization at build trigger.

## Sales_agent toolkit dependency (escalation path — N/A Story G)

Story G is read-only orchestrator — does NOT depend on sales_agent runtime tools. If Stories C/D builds skip-with-escalation per Story C T-6/T-7 pattern (qualify_lead missing in TOOL_REGISTRY), Story G still builds with synthetic fixtures + skip integration tests con `pytest.skip("Stories E+F+H real artifacts needed for full integration")` until upstream lands.
