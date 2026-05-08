---
story_id: sales-agent-eval-cost-budget-cap
type: service-story
module: sales_agent
capability: sales-conversational-engine
po_version: 2
last_modified: 2026-05-08T11:00Z
ratified_by_chris: true   # spec v2 ratificada Chris 2026-05-08T11:00Z (Q1-Q6 todas opción A recomendada)
role_in_outcome: "H — cost cap per eval run (defensa preventiva runaway)"
depends_on:
  - story_b: eval-foundation-simulator-homologation (DONE 2026-05-08) — `eval_simulator_llm_call.cost_usd` + cost-bucket invariant H7
  - story_c: sales-agent-personas-instrumented-runtime (REFINED) — heterogeneous trials_per_persona_kind drive baseline cost calc
  - story_d: sales-agent-goldens-3-tenants-dataset (REFINED) — generation cost ~$5.40 baseline
  - story_e: sales-agent-voice-fidelity-grader-runtime (REFINED) — `eval_simulator_grade.cost_usd_total` (~$330 cold / ~$108 warm full eval grader cost)
  - story_f: sales-agent-eval-pass-k-tracking (REFINED) — read-only aggregator (no cost contribution)
consumed_by:
  - story_g: sales-agent-voice-fidelity-ci-gate — CI gate runs respect budget cap (abort signal cascades)
  - story_i: sales-agent-adversarial-jailbreak-suite — extends cost tracking with adversarial persona_kind cost lines
links:
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  story_e_spec: "../sales-agent-voice-fidelity-grader-runtime/01-spec.md"
  story_f_spec: "../sales-agent-eval-pass-k-tracking/01-spec.md"
---

## Resumen ejecutivo

> **Reframe vs 00-story.md original ($5/run cap, single global threshold):** baseline cost real post Story C+E expansion = **generation $5.40 (Story D) + grader $108 warm cache / $330 cold (Story E) = ~$115 warm / ~$340 cold full eval**. Cap único $5 obsoleto. Reframe a **multi-tier cap con cost-bucket separation** + **pre-flight estimation** + **graceful abort con partial report**.

Implementar el **eval-run cost guard** que consume `eval_simulator_llm_call.cost_usd` (Story B H7) + `eval_simulator_grade.cost_usd_total` (Story E) + Story D generation cost en tiempo real, aborta el run cuando se supera tier cap, persiste partial report, y expone signal pa Story G CI gate consumer.

**Multi-tier cap architecture:**
1. **Per-trial cap** ($0.10 default) — abort single simulation if runaway loop in agent
2. **Per-rubric-grade cap** ($0.20 default) — abort grader Round 2 chain if judges spike cost
3. **Per-run total cap** ($500 default cold cache, $150 warm) — global ceiling for full eval suite
4. **Per-bucket cap** (separate `eval_simulator_llm_call` vs `eval_simulator_grade.cost_usd_total`) — surface drift bucket-specific

**Pre-flight estimation:** before LLM call, `estimate_remaining_budget(run_id)` queries cost-bucket sum + projects next-call cost (input_tokens × price + max_output × price). If projected > cap remaining → **`BudgetCapExceededError`** raised + partial report persisted.

## Cambio respecto 00-story.md (original)

| Aspecto | Original ($5 single cap) | v1 reframe (multi-tier cost-bucket) |
|---|---|---|
| Cap structure | single global $5/run | 4 tiers (per-trial/per-grade/per-run/per-bucket) |
| Cap value | $5.00 hardcoded | $500 cold / $150 warm default (Story E baseline-realistic) + per-tier env vars |
| Cost source | `cost_usd` from copilot wrapper | `eval_simulator_llm_call.cost_usd` (Story B H7) + `eval_simulator_grade.cost_usd_total` (Story E) — bucket-separated |
| Pre-flight | input × price + estimated_output | input × price + max_output × price (over-estimate strict) |
| Abort behavior | raise + partial report | raise + partial report + cost-bucket attribution + structlog cite |
| Warning threshold | 80% of cap | per-tier (80% per-run, 50% per-bucket — earlier signal) |
| Story integration | Story 4 cost recorder | Story B + E cost-bucket invariant + Story F report consumes |
| Override | `_DISABLE=1` | `_DISABLE=1` + per-tier override (`SALES_AGENT_EVAL_PER_TRIAL_CAP_USD`, etc.) |

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `cost-cap-happy-path-within-budget` (`type: happy`)

**Given:**
- Story B + E delivered: cost rows persisted in `eval_simulator_llm_call` + `eval_simulator_grade.cost_usd_total`
- Env vars: `SALES_AGENT_EVAL_PER_RUN_CAP_USD=500` (cold default), `SALES_AGENT_EVAL_PER_TRIAL_CAP_USD=0.10`, `SALES_AGENT_EVAL_PER_GRADE_CAP_USD=0.20`, `SALES_AGENT_EVAL_PER_BUCKET_GENERATION_CAP_USD=20`, `SALES_AGENT_EVAL_PER_BUCKET_GRADER_CAP_USD=400`
- Function `check_budget_before_call(run_id, estimated_cost_usd, bucket) → None | raise BudgetCapExceededError` exposed via `simulator/__init__.py` H9 expand 8→9 names
- Existe service `compute_remaining_budget(run_id) → BudgetState` con buckets + tiers + warnings

**When:**
- Eval suite ejecutado: 75 sims × heterogeneous trials × 3.5 rubrics × 3 judges
- Total cost expected: $5.40 generation (Story D) + $108 grader warm cache (Story E) = ~$115 within $150 warm cap
- Pre-flight check before each LLM call passes (estimated_remaining > 0)

**Then:**
- Run completa sin abort
- `BudgetState` records final per-bucket sum: `{generation: $5.42, grader: $108.30, total: $113.72}` con `caps: {per_run: $500, per_bucket_generation: $20, per_bucket_grader: $400}`
- Warnings emitidos en consola cuando per-bucket grader 80% threshold cruzado: `"⚠ grader bucket at 80% of $400 cap (current $320)"`
- Per-tier warnings logged separadamente: `eval.budget.tier_warning` structlog event con `tier`, `current_usd`, `cap_usd`, `pct`
- `BudgetState` JSON persisted at `_artifacts/eval_runs/{run_id}/budget_summary.json`

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py::test_within_cap_no_abort" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/budget/test_budget_state.py::test_per_bucket_aggregation" }`
- `{ type: state_check, target: filesystem, query: "test -f _artifacts/eval_runs/<run_id>/budget_summary.json" }`
- `{ type: state_check, target: structlog, query: "tier_warning event when bucket >= 80%", expect: ">= 1 warning" }`

---

### Scenario 2 — `cost-cap-mid-run-abort` (`type: edge`)

**Given:**
- Run ejecutándose: 30 sims completed, 45 pending. Generation bucket actual = $4.50 (under $20 cap), grader bucket actual = $380 (95% of $400 cap)
- Next grader call estimated cost = $0.45

**When:**
- Pre-flight check: `4.50 + 380 + 0.45 = 384.95` projected vs grader cap $400 → 96% — within cap
- Sin embargo, NEXT round-2 debate triggered (variance > 0.15) → estimated cost spike to $0.90 → `380 + 0.90 = 380.90` projected
- `check_budget_before_call(run_id, estimated_cost_usd=0.90, bucket="grader")` evaluates: `380 + 0.90 = 380.90 < 400` (per_bucket OK) AND `113.72 + 0.90 = 114.62 < 500` (per_run OK) → **passes**
- Continue. Eventually call N+5 projects `cumulative grader = 405.20 > 400`

**Then:**
- `BudgetCapExceededError` raised con cita: `"Budget cap exceeded: bucket=grader, current=$400.50, estimated_next=$0.30, projected=$400.80, cap=$400.00. Aborted at run_id=<uuid>, simulation_id=<uuid>, turn=<n>, rubric=<id>."`
- Partial report persisted en `_artifacts/eval_runs/{run_id}/budget_summary.json` con `aborted: true`, `abort_reason: budget_cap_exceeded`, `abort_bucket: grader`, `aborted_at: {sim_id, turn, rubric}`, `completed_sims: 60`, `pending_sims: 15`
- Story F aggregator detects partial run → marks affected goldens as `unconverged: true` (Story F D9 cement) + `pass_k_strict=null`
- structlog ERROR: `eval.budget.cap_exceeded` con metadata
- Process exit code = 2 (distinct from generic test failure exit 1)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py::test_per_bucket_grader_cap_aborts" }`
- `{ type: pytest_raises, exception: "BudgetCapExceededError" }`
- `{ type: state_check, target: filesystem, query: "jq '.aborted' _artifacts/eval_runs/<run_id>/budget_summary.json", expect: "true" }`
- `{ type: state_check, target: stdout, query: "exit_code == 2" }`

---

### Scenario 3 — `cap-disabled-debug-mode` (`type: edge`)

**Given:**
- Local dev debug session: `SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1`
- Run starts con misma generation+grader workload Scenario 1

**When:**
- `check_budget_before_call` invoked

**Then:**
- All cap checks short-circuit return None (no abort)
- `BudgetState.disabled = true` field populated en JSON report
- Warnings still logged (informativos, no abort)
- Use case: dev iterating prompts, expects to exceed caps temporarily — no friction
- Production CI: env var NEVER set (`_DISABLE` ausente → cap active)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py::test_disable_flag_short_circuits" }`
- `{ type: state_check, target: filesystem, query: "jq '.disabled' _artifacts/eval_runs/<run_id>/budget_summary.json", expect: "true" }`
- `{ type: state_check, target: stdout, query: "warnings printed but no abort" }`

---

### Scenario 4 — `cap-bypass-via-direct-llm-call` (`type: adversarial`)

> AI-resistant: hostile actor (or distracted dev) bypasses `check_budget_before_call` by invoking LLM directly without budget guard. Defense-in-depth.

**Given:**
- Existe direct LLM call sin pasar por budget guard wrapper (e.g., dev escribe nuevo test que llama `litellm.acompletion` directo)
- Cost-bucket invariant Story B H7 dictates: ALL eval LLM calls write to `eval_simulator_llm_call`

**When:**
- Direct call ejecutado sin `check_budget_before_call` pre-flight
- Cost row INSERTED en `eval_simulator_llm_call` (callback handler enforces persistence regardless of budget guard)

**Then:**
- Periodic sweep `compute_remaining_budget(run_id)` (called every 30s by simulator orchestrator) detects bucket sum exceeded cap
- Raises `BudgetCapExceededError(post_facto=true)` con cita: `"Budget cap exceeded post-facto (call bypassed pre-flight): bucket=grader, current=$420 > cap $400. Likely cause: LLM call bypassed check_budget_before_call wrapper."`
- Architectural fitness gate `test_eval_llm_calls_use_budget_guard.py` (NEW arch test) detects direct litellm imports en `backend/tests/agentic_evals/` que NO pasan por `check_budget_before_call` wrapper → arch test FAIL bloquea PR
- Test fixture `MockBypasser` simula direct call to verify post-facto detection works
- structlog WARNING: `eval.budget.bypass_detected` + `caller_module` + `cost_usd` evidence

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py::test_post_facto_detection" }`
- `{ type: arch_fitness_test, path: "backend/tests/architecture/test_eval_llm_calls_use_budget_guard.py" }`
- `{ type: state_check, target: structlog, query: "bypass_detected event", expect: "1 event when direct call simulated" }`

---

## Schema cement (`BudgetState` v1)

```python
# backend/tests/agentic_evals/sales_agent/budget/_schema.py

class BucketState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bucket_id: Literal["generation", "grader"]
    current_cost_usd: Decimal
    cap_usd: Decimal
    pct_of_cap: float
    threshold_warning_pct: Literal[80] = 80
    warning_emitted: bool

class TierState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tier_id: Literal["per_trial", "per_grade", "per_run", "per_bucket"]
    cap_usd: Decimal
    cap_disabled: bool

class BudgetState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    run_id: str
    buckets: list[BucketState]              # 2 buckets: generation + grader
    tiers: list[TierState]                  # 4 tiers: per_trial + per_grade + per_run + per_bucket
    total_cost_usd: Decimal
    total_cap_usd: Decimal
    aborted: bool
    abort_reason: Literal["budget_cap_exceeded", "manual"] | None
    abort_bucket: Literal["generation", "grader"] | None
    abort_tier: Literal["per_trial", "per_grade", "per_run", "per_bucket"] | None
    aborted_at: AbortContext | None
    disabled: bool                          # SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1
    completed_sims: int
    pending_sims: int
    warnings: list[BudgetWarning]
    started_at: datetime
    aborted_at_timestamp: datetime | None
    final_at: datetime | None

class AbortContext(BaseModel):
    simulation_id: str | None
    turn_n: int | None
    rubric_id: str | None
    estimated_next_usd: Decimal
    projected_total_usd: Decimal
    cap_usd: Decimal

class BudgetWarning(BaseModel):
    timestamp: datetime
    tier: str
    bucket: str | None
    current_usd: Decimal
    cap_usd: Decimal
    pct: float
    message: str

class BudgetCapExceededError(Exception):
    def __init__(self, bucket, tier, current_usd, estimated_next_usd, cap_usd, abort_context, post_facto=False):
        self.bucket = bucket
        self.tier = tier
        self.current_usd = current_usd
        self.estimated_next_usd = estimated_next_usd
        self.cap_usd = cap_usd
        self.abort_context = abort_context
        self.post_facto = post_facto
```

## Cap defaults (post Story E baseline-realistic)

```yaml
caps:
  per_trial_usd: 0.10                              # single sim runaway protection
  per_grade_usd: 0.20                              # grader Round 2 chain spike protection
  per_run_total_usd_cold: 500                      # full eval cold cache ceiling (~$340 baseline + 50% margin)
  per_run_total_usd_warm: 150                      # warm cache ceiling (~$115 baseline + 30% margin)
  per_bucket_generation_usd: 20                    # Story D generation ($5.40 baseline + 4x margin runaway)
  per_bucket_grader_cold_usd: 400                  # Story E grader cold ($330 baseline + 20% margin)
  per_bucket_grader_warm_usd: 130                  # Story E grader warm ($108 baseline + 20% margin)

env_vars:
  SALES_AGENT_EVAL_PER_TRIAL_CAP_USD: 0.10
  SALES_AGENT_EVAL_PER_GRADE_CAP_USD: 0.20
  SALES_AGENT_EVAL_PER_RUN_CAP_USD: 500            # cold default; CI sets 150 if cache warm expected
  SALES_AGENT_EVAL_PER_BUCKET_GENERATION_CAP_USD: 20
  SALES_AGENT_EVAL_PER_BUCKET_GRADER_CAP_USD: 400  # cold default
  SALES_AGENT_EVAL_BUDGET_CAP_DISABLE: 0           # 1 = disable for debug
  SALES_AGENT_EVAL_BUDGET_WARNING_PCT: 80          # threshold pct for warnings
  SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S: 30     # post-facto detection sweep
```

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Cost-bucket invariant | Budget guard reads `eval_simulator_llm_call.cost_usd` + `eval_simulator_grade.cost_usd_total` ONLY (Story B H7 cement) — zero `copilot_*` reads | DB query post-test |
| Pre-flight precision | `check_budget_before_call(estimated)` uses `input_tokens × price + max_output_tokens × price` (over-estimate strict) | unit test edge cases |
| Abort gracefully | `BudgetCapExceededError` raised + partial report persisted + structlog ERROR | scenario 2 grader |
| Post-facto detection | Periodic sweep every 30s detects direct LLM call bypass | scenario 4 grader |
| Per-tier override | All caps env-var overridable independently | scenario 3 disable + per-tier override tests |
| Schema versioning | `BudgetState.schema_version: Literal[1]` cement. Future bumps via SCHEMA_MIGRATIONS (Story B H1 reused) | Pydantic + migrator |
| Idempotency | Re-query `compute_remaining_budget(run_id)` con mismo state DB → same `BudgetState` row (deterministic) | unit test |
| Latency budget | Pre-flight check < 50ms p95 (DB sum query) | perf test |
| Forward-compat | Adversarial bucket (Story I) extends additively | Pydantic Literal forward-extend |
| Public API surface | `simulator/__init__.py` H9 expand 8→9 names (`check_budget_before_call`). Frozen post Story H ship | arch fitness gate |
| JSON report stability | `budget_summary.json` schema versioned consume Story G CI gate | schema validator |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — budget guard CONSUMES Story B `eval_simulator_llm_call` table + Story E `eval_simulator_grade` table. NO mirror cost recording (Story B H7 owns).
- `.claude/rules/auditor-downstream-regression.md` — tabla SSoT MUST add row when `budget/` path created (R3 row addition required, downstream consumers = Stories G/I)
- `.claude/rules/spanish-text.md` — JSON report messages + CLI errors = español neutro. Code English.
- `.claude/rules/tdd-mandatory.md` — RED tests primero (schema → pre-flight → abort → post-facto → arch fitness)
- `.claude/rules/backend-ddd.md` — guard bajo `backend/tests/agentic_evals/sales_agent/budget/`. Script bajo `backend/scripts/`. NO touch `modules/sales_agent/{domain,application,api}/`
- `.claude/rules/architectural-fitness.md` — NEW arch test `test_eval_llm_calls_use_budget_guard.py` enforces direct litellm import + budget guard wrapping
- Story B H7 cost-bucket invariant — guard reads only `eval_simulator_llm_call`/`eval_simulator_grade`, NEVER `copilot_*` tables
- Story B H9 public API — expand 8→9 names (`check_budget_before_call` NEW)
- Story E D9 cost bucket — separates grader cost from generation cost (per-bucket cap aligned)
- Story F D9 unconverged handling — partial run aborted by budget guard marks goldens as `unconverged: true`

## Cross-module impact

- **Lee de:**
  - `eval_simulator_llm_call.cost_usd` (Story B) — generation bucket sum
  - `eval_simulator_grade.cost_usd_total` (Story E) — grader bucket sum
  - Env vars `SALES_AGENT_EVAL_*_CAP_USD` (configurable defaults)
- **Escribe a:**
  - `backend/tests/agentic_evals/sales_agent/budget/__init__.py` (NEW)
  - `backend/tests/agentic_evals/sales_agent/budget/_schema.py` (NEW — `BudgetState`, `BucketState`, `TierState`, `AbortContext`, `BudgetWarning`)
  - `backend/tests/agentic_evals/sales_agent/budget/guard.py` (NEW — `check_budget_before_call`, `compute_remaining_budget`, `start_periodic_sweep`)
  - `backend/tests/agentic_evals/sales_agent/budget/_internal/cost_estimator.py` (NEW — input_tokens × price + max_output × price)
  - `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (MODIFY — H9 expand 8→9 names)
  - `backend/tests/architecture/test_eval_llm_calls_use_budget_guard.py` (NEW arch fitness gate)
  - `_artifacts/eval_runs/{run_id}/budget_summary.json` (NEW JSON output)
  - `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (extend — `eval.budget_caps` + `eval.budget_summary_path`)
- **Es leído por:**
  - Story G `voice-fidelity-ci-gate` — CI gate consume `budget_summary.json` + abort signal cascades to red CI
  - Story I `adversarial-jailbreak-suite` — extends cost tracking adversarial bucket (additive)
  - Story F `eval-pass-k-tracking` — partial run abort cascades `unconverged: true` para goldens afectados
- **Eventos emitidos:** structlog (`eval.budget.tier_warning`, `eval.budget.cap_exceeded`, `eval.budget.bypass_detected`)
- **Eventos consumidos:** ninguno

## Out of scope (anti-creep)

- ❌ Per-tenant runtime cost cap (production scope, not eval)
- ❌ Per-tenant eval cost (eval is global suite, not per-tenant scope)
- ❌ Slack/email notifications (console + structlog only)
- ❌ Auto-scaling cap based on model price changes (manual env var update)
- ❌ Cost projection ML (rule-based estimator suficiente)
- ❌ Refund/chargeback handling
- ❌ Cost optimization recommendations
- ❌ Per-rubric cap differentiation (per-grade tier cubre)
- ❌ Tocar Story B `eval_simulator_llm_call` schema (read-only)
- ❌ Tocar Story E `eval_simulator_grade` schema (read-only)
- ❌ Tocar Story F aggregator (consume cascade only)
- ❌ Modificar `core/config.py` defaults (env vars only)

## Decisiones cardinales (cement)

| # | Decisión | Razón |
|---|---|---|
| D1 | Multi-tier cap (4 tiers: per_trial / per_grade / per_run / per_bucket) | Single global cap mask sources de drift. Tier-specific surfaces qué bucket runaway |
| D2 | Cost-bucket separation: `generation` (Story D) vs `grader` (Story E) caps independent | Story B H7 cement — bucket separation ya cement, budget guard mirrors |
| D3 | Default per-run cap = $500 cold / $150 warm (post Story E baseline-realistic ~$340/~$115 + 50%/30% margin) | Original $5/run obsoleto post Story C+E expansion. New defaults realistic |
| D4 | Pre-flight cost estimation: `input_tokens × price + max_output_tokens × price` (over-estimate strict) | Better safe than sorry — under-estimate causes mid-run abort surprise |
| D5 | Periodic sweep every 30s detects direct LLM call bypass (post-facto detection) | Defense-in-depth Scenario 4 — arch fitness pre-commit gate + runtime sweep redundant |
| D6 | Arch fitness test `test_eval_llm_calls_use_budget_guard.py` enforces guard wrap | Pre-merge gate prevents bypass introduction |
| D7 | `BudgetCapExceededError` includes `post_facto: bool` field — distinguishes pre-flight vs sweep detection | Audit trail — post_facto means bypass occurred (security-relevant) |
| D8 | Partial report `budget_summary.json` persisted on abort + cascades to Story F `unconverged: true` for affected goldens | Graceful degradation — Story G CI gate gets clear signal, not silent corruption |
| D9 | Per-tier env vars + global `_DISABLE=1` flag for debug | Local dev iterates without friction; CI strict |
| D10 | Warning threshold 80% per-bucket (earlier signal than per-run 80%) | Bucket runaway visible before run hits ceiling |
| D11 | `simulator/__init__.py` H9 expand 8→9 names (`check_budget_before_call`). Re-freeze post Story H ship | Public API extension justified — guard is foundational primitive |
| D12 | Schema `BudgetState` v1 cement con SCHEMA_MIGRATIONS forward-compat (Story B H1 reused) | Forward-compat 5+ years + adversarial bucket Story I additive |
| D13 | Process exit code 2 on budget abort (distinct from generic test fail exit 1) | CI distinguishes budget vs functional regression |

## Open questions — RESUELTAS (Chris ratificó 2026-05-08T11:00Z)

- [x] **Q1 → A**: Cap defaults = **$500 cold / $150 warm per-run** + $20 generation bucket + $400 grader cold / $130 grader warm. Suficiente margin para Story E variance + Round 2 spikes + adversarial Story I expansion.
- [x] **Q2 → A**: Pre-flight estimation = **over-estimate strict** (`input_tokens × price + max_output × price`). Better safe than sorry — abort surprise mid-run partial report messy.
- [x] **Q3 → A**: Post-facto detection sweep = **30s interval**. Sweet spot detection delay vs DB query overhead.
- [x] **Q4 → A**: Arch fitness test = **NEW `test_eval_llm_calls_use_budget_guard.py`** detect direct litellm imports sin guard. Pre-merge gate prevents bypass introduction.
- [x] **Q5 → A**: Process exit code = **`2` distinct from test fail `1`**. CI distingue budget-abort vs functional-regression. Story G routes diferenciado.
- [x] **Q6 → A**: Warning threshold per-bucket = **80%**. Earlier signal vs per-run 80% — bucket-level visibility actionable. Sweet spot variance noise vs real signal.

## Próximo paso

Service-story → `/po` ratifica con Chris (loop iterativo) → spec ratificada → transition `state: refining → refined` → `/architect` orchestrator spawna `/architect-be` (BudgetState Pydantic + guard impl + cost_estimator + periodic sweep + arch fitness gate + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → `/dev-team` build (espera Stories B+E build done — bloqueador hard).

> **Build order ack:** Story H build MUST come AFTER Stories B+E builds (consume `eval_simulator_llm_call.cost_usd` + `eval_simulator_grade.cost_usd_total`). Refinement parallel-safe NOW; build serialization downstream.

## Changelog

- v0 2026-05-04 — `/pm` 00-story.md initial brief (single global $5/run cap, simple Story 4 cost wrapper consumer).
- v1 2026-05-08T10:30Z — `/po` reframe multi-tier cost-bucket cap (post Story C+E expansion: $5.40 generation + $108 warm grader = ~$115 baseline). Multi-tier (per_trial/per_grade/per_run/per_bucket) + bucket-separation (generation vs grader Story B H7 cement). Pre-flight estimation over-estimate strict + periodic sweep 30s post-facto detection vs direct LLM call bypass. Arch fitness gate `test_eval_llm_calls_use_budget_guard.py` NEW. `simulator/__init__.py` H9 expand 8→9 names (`check_budget_before_call`). Schema `BudgetState` v1 con SCHEMA_MIGRATIONS forward-compat. 4 scenarios obligatorios (happy within / edge mid-run abort / edge disable debug / adversarial bypass). 13 decisiones cardinales D1-D13. 6 open questions Q1-Q6 awaiting Chris ratification.
- v2 2026-05-08T11:00Z — Chris ratificó Q1-Q6 (todas opción A recomendada). Decisiones cement: D3 caps $500/$150 cold/warm + $20 generation + $400/$130 grader; D4 pre-flight over-estimate; D5 sweep 30s; D6 arch fitness test NEW; D13 exit code 2; D10 warning 80% per-bucket. `ratified_by_chris: true`. Service-story → transition `state: refining → refined`. Próximo: `/architect`.