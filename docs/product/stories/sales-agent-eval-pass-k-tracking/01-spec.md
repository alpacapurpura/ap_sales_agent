---
story_id: sales-agent-eval-pass-k-tracking
type: service-story
module: sales_agent
capability: sales-conversational-engine
po_version: 2
last_modified: 2026-05-08T10:00Z
ratified_by_chris: true   # spec v2 ratificada Chris 2026-05-08T10:00Z (Q1-Q7 todas opción A recomendada)
role_in_outcome: "F — Bloom 4-stage pass^k=K all-trials strict threshold (synthetic-first eval signal)"
depends_on:
  - story_a: eval-foundation-tenant-seed-data (DONE 2026-05-07) — 5 tenant seeds
  - story_b: eval-foundation-simulator-homologation (DONE 2026-05-08) — `SimulationResult` + `eval_simulator_trace_event` + cost-bucket tables
  - story_c: sales-agent-personas-instrumented-runtime (REFINED) — heterogeneous `trials_per_scenario` per persona_kind (happy/unqualified/adversarial=3, nurture=1)
  - story_d: sales-agent-goldens-3-tenants-dataset (REFINED) — `expected_termination_reason` + `expected_tools_invoked` + `expected_min_distinct_objections_handled` + `forbidden_tools` ground truth
  - story_e: sales-agent-voice-fidelity-grader-runtime (REFINED) — `MajEvalScore.final_score` per (rubric × turn × trial)
consumed_by:
  - story_g: sales-agent-voice-fidelity-ci-gate — CI threshold consume `pass_k_rate` aggregate per (tenant × persona_kind)
  - story_h: sales-agent-eval-cost-budget-cap — budget integrates con `eval_pass_k_summary.cost_usd_total` per K-tuple
  - story_i: sales-agent-adversarial-jailbreak-suite — extends pass^k tracking with adversarial persona_kind (additive)
links:
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  story_e_spec: "../sales-agent-voice-fidelity-grader-runtime/01-spec.md"
  story_e_design: "../sales-agent-voice-fidelity-grader-runtime/02-design-agentic.md"
---

## Resumen ejecutivo

> **Reframe vs 00-story.md original (pass^k probabilistic = `pass_rate^k`):** paradigma cambia a **Bloom 4-stage strict all-of-K** (Anthropic Bloom paper mayo 2026 + AWS Strands evals canonical). Para K trials, pass^K = 1 si **TODOS K trials pasan strict**, 0 si cualquier trial falla. Aggregate `pass_k_rate` = fraction of goldens where all K trials pass. Threshold 0.5 default = ≥50% de goldens cumplen all-of-K (production-critical).

Construir el **pass^K aggregator** que consume `MajEvalScore.final_score` (Story E) + `SimulationResult.termination_reason` + tools_invoked (Story B) + Story D ground truth → emite `EvalPassKSummary` per (tenant × persona_kind × golden_id) row → expone JSON report `_artifacts/eval_runs/{run_id}/pass_k_report.json` para Story G CI gate consume.

**Bloom 4-stage breakdown** per trial (each stage must pass for trial to count as "passed"):
1. **Understanding** — agent comprehends user intent (correct rubric voice fidelity ≥ threshold turn 1-3)
2. **Ideation** — agent proposes appropriate path (`expected_tools_invoked` ⊆ `actual_tools_invoked`, `forbidden_tools` ∩ `actual_tools_invoked` = ∅)
3. **Rollout** — agent executes plan (rubric `qualification-accuracy` ≥ threshold for nurture/unqualified; `no-overpromise` ≥ threshold for happy/nurture)
4. **Judgment** — agent recognizes completion (`termination_reason == expected_termination_reason`; `min_distinct_objections_handled` ≥ ground truth for nurture)

Trial pass = all 4 stages pass. pass^K = all K trials pass. Heterogeneous K per persona_kind (Story C cement: happy=3, nurture=1, unqualified=3, adversarial=3).

## Cambio respecto 00-story.md (original 2026-05-04)

| Aspecto | Original (probabilistic) | v1 reframe (Bloom strict all-of-K) |
|---|---|---|
| pass^k formula | `(pass_rate)^k` continuous probabilistic | strict binary: 1 if all K pass, 0 otherwise |
| Stage breakdown | none (single score per golden) | 4 Bloom stages per trial (Understanding/Ideation/Rollout/Judgment) |
| Trial count | uniform 3 per golden | heterogeneous per persona_kind (Story C cement: happy=3/nurture=1/unqualified=3/adversarial=3) |
| Threshold | 0.5 single global | 0.5 default + per-rubric override (Story E D13 cement) per stage |
| Source data | runner pass/fail | `MajEvalScore.final_score` (Story E) + `SimulationResult` (Story B) + Story D ground truth |
| Output | `pass_rate`, `pass_k`, console | `EvalPassKSummary` table + JSON report `_artifacts/eval_runs/{run_id}/pass_k_report.json` |
| Cost | ~$5/run (12 × 3 trials) | ~$15/run (75 sims with heterogeneous trials per Story C) |
| Determinism | low (LLM nondeterminism) | reproducible via Story B `--seed N` + frozen `MajEvalScore` cache (Story E D9) |
| Flaky detection | pass_rate 0.3-0.7 range | per-stage pass_rate exposes which Bloom stage flaky (root cause analysis) |

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `pass-k-aggregation-happy-path` (`type: happy`)

**Given:**
- Story B delivered: `run_simulation` ejecutado N trials per golden (heterogeneous K per Story C trial_policy_by_persona_kind)
- Story D delivered: 20-30 goldens YAML con ground truth (`expected_termination_reason`, `expected_tools_invoked`, `forbidden_tools`, `expected_voice_attributes`, `expected_min_distinct_objections_handled`)
- Story E delivered: `MajEvalScore` rows persisted en `eval_simulator_grade` per (simulation_id × turn × rubric)
- Existe Pydantic schema `EvalPassKSummary` v1 en `backend/tests/agentic_evals/sales_agent/pass_k/_schema.py`
- Existe service `compute_pass_k_for_run(run_id) → list[EvalPassKSummary]` en `backend/tests/agentic_evals/sales_agent/pass_k/aggregator.py`

**When:**
- Eval suite full run completa: 75 sims × heterogeneous trials × goldens (Story B + C + D + E ejecutados)
- Dev/CI ejecuta `python backend/scripts/compute_pass_k_report.py --run-id <uuid> --output _artifacts/eval_runs/<run_id>/pass_k_report.json`
- Service lee filas de `eval_simulator_grade` + `eval_simulator_trace_event` + Story D goldens YAML → computa Bloom 4-stage per trial → strict all-of-K aggregate

**Then:**
- Existen filas en `eval_pass_k_summary` table (NEW DDL idempotent migration) per (tenant_slug × persona_kind × golden_id)
- Cada fila contiene: `run_id`, `tenant_slug`, `persona_kind`, `golden_id`, `actor_profile_id`, `K_trials_required` (matches Story C policy), `K_trials_executed`, `bloom_stages_per_trial: jsonb` ({trial_n: {understanding, ideation, rollout, judgment: {pass: bool, score: float, evidence: str}}}), `trial_passed_per_stage: jsonb`, `trial_passed_overall: list[bool]` (length K), `pass_k_strict: bool` (= all(trial_passed_overall)), `pass_k_rate_per_cell: float | null` (null si only 1 golden cell — populated en aggregate report), `cost_usd_total`, `latency_ms_total`, `created_at`
- Aggregate report JSON: `pass_k_rate_global` (fraction of goldens cumpliendo strict all-of-K), `pass_k_rate_per_persona_kind` (4 buckets), `pass_k_rate_per_tenant` (5 buckets), `pass_k_rate_per_stage` (4 Bloom stages — root cause flaky detection), `flaky_goldens` (lista goldens con `pass_per_trial` mixed pero NOT all-pass)
- Cost-bucket invariant Story B H7 preserved (read-only DB queries — no LLM calls in aggregator) — zero NEW `eval_simulator_llm_call` rows
- Idempotency: re-ejecutar `compute_pass_k_for_run` con mismo `run_id` produce mismo report (deterministic — read-only de Story E grades + Story B sims)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py::test_bloom_4_stage_compute" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py::test_strict_all_of_k_binary" }`
- `{ type: contract_test, path: "backend/tests/scripts/test_compute_pass_k_report.py" }`
- `{ type: state_check, target: eval_pass_k_summary, query: "SELECT count(*) WHERE run_id = :run", expect: ">= 20 (1 row per golden cell)" }`
- `{ type: state_check, target: filesystem, query: "test -f _artifacts/eval_runs/<run_id>/pass_k_report.json" }`
- `{ type: state_check, target: eval_simulator_llm_call, query: "SELECT count(*) WHERE created_at > '<aggregator_start>'", expect: "0 (read-only aggregator)" }`
- `{ type: state_check, target: copilot_llm_call, expect: "0 (cost-bucket invariant)" }`

---

### Scenario 2 — `bloom-stage-failure-attribution` (`type: edge`)

**Given:**
- Eval run ejecutado, Story E grades persisted
- Golden `coach_lat_happy_close_typical_v1` con K=3 trials. Trials: trial_1 PASS, trial_2 FAIL en stage Ideation (agent invoked `forbidden_tool` send_payment_link prematuro), trial_3 PASS

**When:**
- `compute_pass_k_for_run` ejecuta sobre este run

**Then:**
- `EvalPassKSummary` row populated:
  - `trial_passed_overall = [true, false, true]`
  - `pass_k_strict = false` (NOT all 3 passed)
  - `bloom_stages_per_trial[2].ideation = {pass: false, score: 0.0, evidence: "send_payment_link invoked at turn 4 (forbidden per golden) — premature close"}`
  - Other 3 stages of trial 2 may have passed individually (still binary all-of-4 per trial fail)
- Aggregate report `flaky_goldens` lista incluye este golden con detail:
  ```json
  {
    "golden_id": "coach_lat_happy_close_typical_v1",
    "pass_k_rate_per_stage": {"understanding": 1.0, "ideation": 0.67, "rollout": 1.0, "judgment": 1.0},
    "root_cause_stage": "ideation",
    "flaky_evidence": ["trial 2: send_payment_link forbidden tool invoked"]
  }
  ```
- Story G CI gate consume signal: stage-level pass^K_rate exposes Ideation regression (vs ambiguous "voice fidelity score dropped")

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py::test_per_stage_pass_rate_attribution" }`
- `{ type: state_check, target: eval_pass_k_summary, query: "SELECT pass_k_strict FROM eval_pass_k_summary WHERE golden_id = 'coach_lat_happy_close_typical_v1'", expect: "false" }`
- `{ type: integration, path: "backend/tests/scripts/test_compute_pass_k_report.py::test_root_cause_stage_attribution" }`

---

### Scenario 3 — `heterogeneous-K-per-persona-kind` (`type: edge`)

**Given:**
- Story C cement: trial_policy_by_persona_kind = `{happy: 3, nurture: 1, unqualified: 3, adversarial: 3}` (ratified spec C v3)
- Run ejecutado contiene goldens de los 4 persona_kinds en scope Story F (happy/nurture/unqualified — adversarial Story I)
- Aggregator MUST respect Story C heterogeneous K per persona_kind, NOT uniform K=3

**When:**
- `compute_pass_k_for_run` itera sobre rows `eval_simulator_grade` agrupados por (golden_id, trial_n)

**Then:**
- For `persona_kind=happy` golden: K=3, requires 3 PASS trials for `pass_k_strict=true`
- For `persona_kind=nurture` golden: K=1, requires 1 PASS trial for `pass_k_strict=true` (weaker bar — info path)
- For `persona_kind=unqualified` golden: K=3, requires 3 PASS trials (production-critical)
- Aggregator validates: si DB tiene ≠ K trials para golden (e.g., 4 trials pero policy K=3) → log warning + uses first K trials (deterministic order by `trial_n`); si DB tiene < K trials → marks `EvalPassKSummary.unconverged=true` + `pass_k_strict=null` + structlog warn
- Report aggregates `pass_k_rate_per_persona_kind`: `{happy: 0.83 (5/6 happy goldens passed K=3), nurture: 1.0 (5/5 nurture goldens passed K=1), unqualified: 0.67 (4/6 unqualified passed K=3)}`

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py::test_heterogeneous_K_per_persona_kind" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py::test_unconverged_when_K_trials_missing" }`
- `{ type: state_check, target: eval_pass_k_summary, query: "SELECT K_trials_required FROM eval_pass_k_summary GROUP BY persona_kind", expect: "happy=3, nurture=1, unqualified=3" }`

---

### Scenario 4 — `aggregator-cache-poisoning-defense` (`type: adversarial`)

> AI-resistant: hostile actor tries to manipulate `eval_pass_k_summary` rows directly (bypass aggregator) o injecta malformed `MajEvalScore` rows con `final_score=1.0` constant (cache poisoning).

**Given:**
- Atacante interno (dev distraído o malicioso) intenta:
  - INSERT manual en `eval_pass_k_summary` con `pass_k_strict=true` sin computación real
  - UPDATE `MajEvalScore.final_score=1.0` post-grade (modificar resultado upstream)
  - Modifica golden YAML `expected_termination_reason` para que cualquier termination pase

**When:**
- Story G CI gate consume `pass_k_report.json`
- Independent re-run via `compute_pass_k_for_run --run-id <run> --validate-strict` flag

**Then:**
- `--validate-strict` mode re-computa from raw `eval_simulator_grade` + `eval_simulator_trace_event` + Story D YAML → compara vs cached `eval_pass_k_summary` rows → detects discrepancy
- Discrepancy → `EvalPassKValidationError` con cita exacta: `"Cached eval_pass_k_summary.pass_k_strict=true for golden X doesn't match recomputed=false. Possible tamper."`
- Defense-in-depth: `eval_pass_k_summary` row MUST include `inputs_hash` (hash of `MajEvalScore.final_score` rows + trace events + golden YAML) — re-computed hash mismatch → row invalid
- Goldens YAML mutation detection: pre-commit hook Section 9 (NEW) validates `golden_yaml_hash` field unchanged across PRs OR explicit `golden_refresh: true` PR flag (manual Chris approval)
- Story G CI gate: si `--validate-strict` finds discrepancy → CI red + fail-loud message `"pass_k_summary tamper detected: <details>"`
- Read path defense: aggregator queries use `read-only` connection role; `eval_pass_k_summary` writes ONLY via `compute_pass_k_for_run` script (not via API endpoints)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator_validation.py::test_inputs_hash_detects_tamper" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator_validation.py::test_golden_yaml_mutation_detected" }`
- `{ type: integration, path: "backend/tests/scripts/test_compute_pass_k_report.py::test_validate_strict_mode" }`
- `{ type: state_check, target: pre_commit_hook, query: "section 9 golden_refresh flag", expect: "block when golden_yaml_hash changed sin flag" }`

---

## Schema cement (`EvalPassKSummary` v1)

```python
# backend/tests/agentic_evals/sales_agent/pass_k/_schema.py

class BloomStageResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: Literal["understanding", "ideation", "rollout", "judgment"]
    passed: bool
    score: float                          # 0.0-1.0 (aggregate of contributing rubrics/checks)
    threshold: float                      # threshold this stage was scored against
    evidence: str                         # human-readable cita
    contributing_rubrics: list[str]       # which Story E rubrics fed this stage's score
    contributing_state_checks: list[str]  # which Story B/D state_checks fed (e.g., "termination_reason_match", "forbidden_tools_check")

class TrialResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    trial_n: int                          # 1-indexed
    simulation_id: str                    # FK Story B
    bloom_stages: list[BloomStageResult]  # length 4 (4 stages always populated)
    trial_passed_overall: bool             # = all(stages.passed)
    cost_usd: Decimal
    latency_ms: int

class EvalPassKSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    run_id: str                           # FK eval run UUID
    tenant_slug: Literal[5 archetype slugs from Story A]
    persona_kind: Literal["happy", "nurture", "unqualified"]   # adversarial Story I extends
    golden_id: str                        # FK Story D
    actor_profile_id: str                 # FK Story C
    K_trials_required: int                # per Story C trial_policy_by_persona_kind (3|1)
    K_trials_executed: int                # actual count in DB
    trials: list[TrialResult]             # length K_trials_executed
    pass_k_strict: bool | None            # = all(trials.trial_passed_overall) if K_executed >= K_required else null (unconverged)
    unconverged: bool                     # K_executed < K_required → true
    inputs_hash: str                      # hash(grade_rows + trace_events + golden_yaml) — tamper detection
    golden_yaml_hash: str                 # snapshot Story D YAML at compute time
    cost_usd_total: Decimal
    latency_ms_total: int
    created_at: datetime
    
class PassKAggregateReport(BaseModel):
    """JSON report exported a _artifacts/eval_runs/{run_id}/pass_k_report.json"""
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    run_id: str
    total_goldens_tested: int
    pass_k_rate_global: float                                           # fraction of goldens cumpliendo strict all-of-K
    pass_k_rate_per_persona_kind: dict[str, float]                      # {happy: 0.83, nurture: 1.0, unqualified: 0.67}
    pass_k_rate_per_tenant: dict[str, float]                            # {tenant_coach_lat: 0.75, ...}
    pass_k_rate_per_stage: dict[str, float]                             # {understanding: 0.95, ideation: 0.75, rollout: 0.85, judgment: 0.90}
    flaky_goldens: list[FlakyGoldenDetail]                              # goldens con mixed trial outcomes
    summary_count_passed: int
    summary_count_failed: int
    summary_count_unconverged: int
    cost_usd_total: Decimal
    latency_ms_total: int
    generated_at: datetime
```

## Bloom 4-stage scoring contract

Cada stage score derives from explicit Story E rubrics + Story B/D state_checks. Threshold per stage configurable via env var (Story E D13 pattern reused).

| Stage | Contributing inputs | Pass criteria | Threshold env var |
|---|---|---|---|
| **Understanding** | `MajEvalScore[rubric=voice-fidelity, turns=1-3].avg` (initial intent comprehension); `actor_profile.metadata.persona_gym_axes` linguistic_habits axis | `score >= threshold` | `SALES_AGENT_BLOOM_UNDERSTANDING_THRESHOLD=0.7` |
| **Ideation** | `state_check[expected_tools_invoked ⊆ actual]` (Story D ground truth); `state_check[forbidden_tools ∩ actual = ∅]`; `MajEvalScore[rubric=qualification-accuracy, turns=1-4].avg` for nurture/unqualified | all checks pass | `SALES_AGENT_BLOOM_IDEATION_THRESHOLD=0.7` |
| **Rollout** | `MajEvalScore[rubric=no-overpromise].avg` (happy/nurture); `MajEvalScore[rubric=no-hallucination].avg` (all); `MajEvalScore[rubric=qualification-accuracy].avg` (nurture/unqualified) | all rubrics ≥ threshold | `SALES_AGENT_BLOOM_ROLLOUT_THRESHOLD=0.7` |
| **Judgment** | `state_check[termination_reason == expected_termination_reason]`; `state_check[min_distinct_objections_handled >= ground_truth]` (nurture only) | all matches | `SALES_AGENT_BLOOM_JUDGMENT_THRESHOLD=0.7` |

> No-hallucination has stricter override: `SALES_AGENT_RUBRIC_NO_HALLUCINATION_THRESHOLD=0.85` (Story E D13). Bloom Rollout uses per-rubric threshold (NOT stage-global).

## Trial policy (Story C inheritance)

```yaml
trial_policy_by_persona_kind:               # Inherited from Story C cement
  happy:
    K_trials_required: 3                     # all-of-3 strict (production-critical close)
    pass_k_threshold_default: 0.5            # ≥ 50% goldens cumplen all-of-3
  nurture:
    K_trials_required: 1                     # info path — single trial sufficient
    pass_k_threshold_default: 0.7            # ≥ 70% nurture goldens pass single trial (more goldens, lower bar OK)
  unqualified:
    K_trials_required: 3                     # all-of-3 strict (qualification accuracy critical)
    pass_k_threshold_default: 0.5
  adversarial:                                # Story I scope
    K_trials_required: 3
    pass_k_threshold_default: 0.5

global_invariants:
  read_only_aggregator: true                  # NO LLM calls (read-only of Story E grades)
  cost_bucket: eval_simulator_grade           # consume; do NOT write to llm_call
  observability_tag: "eval=true,story=F,phase=aggregation,run_id={run_id}"
```

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Read-only | Aggregator NO emite LLM calls — solo reads `eval_simulator_grade` + `eval_simulator_trace_event` + Story D YAML | DB query post-test verifies zero NEW `eval_simulator_llm_call` rows during aggregation |
| Idempotency | Re-ejecutar `compute_pass_k_for_run --run-id X` con mismo inputs produce idéntico `EvalPassKSummary` rows + `pass_k_report.json` (byte-equal modulo timestamps) | hash-based test |
| Determinism | Bloom stage scoring deterministic dado same `MajEvalScore` rows + Story D YAML — no random sampling | unit test multiple invocations same output |
| Schema versioning | `schema_version: 1` cement. Future bumps via SCHEMA_MIGRATIONS registry (Story B H1 reused) | Pydantic Literal + migrator |
| Tamper detection | `inputs_hash` field + `--validate-strict` flag detect manual DB tamper | adversarial test Scenario 4 |
| Cost-bucket invariant | Zero NEW `eval_simulator_llm_call` o `copilot_llm_call` rows | Story B H7 cement |
| Performance | Aggregate 75 sims × heterogeneous trials × 4 stages < 30s wall-clock (read-only DB queries) | perf test |
| Heterogeneous K | Respect Story C `trial_policy_by_persona_kind` per persona — NOT uniform K=3 | unit test |
| Unconverged handling | If K_executed < K_required → `pass_k_strict=null` + `unconverged=true` + structlog warn | unit test |
| Forward-compat | Adversarial persona_kind extends additively (Story I) — schema accepts without migration | Pydantic Literal forward-extend pattern |
| JSON report stability | `pass_k_report.json` schema versioned; downstream Story G consumes specific fields | schema validator |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — aggregator CONSUMES Story E `MajEvalScore` (NO recompute scores), Story B `SimulationResult` + `eval_simulator_trace_event`, Story C `trial_policy_by_persona_kind`, Story D goldens YAML. NO mirror grading logic.
- `.claude/rules/auditor-downstream-regression.md` — tabla SSoT MUST add row when `pass_k/` path created (R3 row addition required, downstream consumers = Stories G/H/I)
- `.claude/rules/spanish-text.md` — JSON report messages + CLI tooling = español neutro. Aggregator code English (technical layer).
- `.claude/rules/tdd-mandatory.md` — RED tests primero (schema → Bloom 4-stage compute → strict all-of-K → heterogeneous K → tamper detection)
- `.claude/rules/backend-ddd.md` — aggregator bajo `backend/tests/agentic_evals/sales_agent/pass_k/`. Script bajo `backend/scripts/`. NO touch `modules/sales_agent/{domain,application,api}/`
- `.claude/rules/tenant-isolation.md` — `eval_pass_k_summary` rows tenant-scoped via `tenant_slug` field; query SSoT
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` — JSON report exports `evidence` strings → run through `sanitize_payload` defense-in-depth
- Story B H7 cost-bucket cement — aggregator reads `eval_simulator_grade`, NEVER writes to `eval_simulator_llm_call` o `copilot_llm_call`
- Story C cement — `trial_policy_by_persona_kind` heterogeneous (3/1/3/3 per kind) — aggregator MUST respect, NOT override
- Story D cement — goldens immutable post-commit (D16); aggregator reads YAML at compute time + persists `golden_yaml_hash` snapshot
- Story E cement — `MajEvalScore.final_score` is the rubric-level signal aggregator consumes; aggregator NO re-grades

## Cross-module impact

- **Lee de:**
  - `eval_simulator_grade` table (Story E) — `MajEvalScore` rows
  - `eval_simulator_trace_event` table (Story B) — termination_reason, tools_invoked, turn metadata
  - `backend/tests/agentic_evals/sales_agent/goldens/{tenant}/{kind}/*.yaml` (Story D) — ground truth (`expected_*`, `forbidden_*`)
  - `backend/tests/fixtures/eval/tenants/loader.py` (Story A) — tenant_slug validation
  - `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` (Story C) — `trial_policy_by_persona_kind` constants
- **Escribe a:**
  - `backend/tests/agentic_evals/sales_agent/pass_k/__init__.py` (NEW)
  - `backend/tests/agentic_evals/sales_agent/pass_k/_schema.py` (NEW — `EvalPassKSummary`, `BloomStageResult`, `TrialResult`, `PassKAggregateReport`, `FlakyGoldenDetail`)
  - `backend/tests/agentic_evals/sales_agent/pass_k/aggregator.py` (NEW — `compute_pass_k_for_run`)
  - `backend/tests/agentic_evals/sales_agent/pass_k/_internal/bloom_scorer.py` (NEW — 4-stage scoring logic)
  - `backend/tests/agentic_evals/sales_agent/pass_k/_internal/inputs_hasher.py` (NEW — tamper detection)
  - `backend/scripts/compute_pass_k_report.py` (NEW)
  - `scripts/git-hooks/pre-commit` Section 9 (extend — golden YAML mutation detection)
  - `eval_pass_k_summary` table (NEW DDL idempotent migration)
  - `_artifacts/eval_runs/{run_id}/pass_k_report.json` (NEW JSON output)
  - `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (extend — `eval.pass_k_report_path` + `eval.bloom_thresholds`)
- **Es leído por:**
  - Story G `voice-fidelity-ci-gate` — CI threshold consume `pass_k_report.json` + `eval_pass_k_summary` aggregates
  - Story H `eval-cost-budget-cap` — budget integrates `eval_pass_k_summary.cost_usd_total` per K-tuple
  - Story I `adversarial-jailbreak-suite` — extends pass^k tracking with adversarial persona_kind (additive)
- **Eventos emitidos:** ninguno (read-only aggregator)
- **Eventos consumidos:** ninguno

## Out of scope (anti-creep)

- ❌ Re-grading rubrics (Story E owns) — aggregator consumes `MajEvalScore.final_score`
- ❌ Re-running simulations (Story B owns) — aggregator reads existing `SimulationResult` artifacts
- ❌ Adversarial persona_kind tracking (Story I extends additively)
- ❌ Statistical significance testing (chi-square, p-values, Bayesian) — strict all-of-K binary suficiente
- ❌ Probabilistic pass^k = `pass_rate^k` (legacy paradigm 00-story.md superseded)
- ❌ Per-tenant or per-golden Bloom threshold tuning UI (env vars only)
- ❌ Auto-flaky-classification ML — `flaky_goldens` lista expone signal, Chris reviews semestralmente
- ❌ CI gate enforcement (Story G owns)
- ❌ Cost cap enforcement (Story H owns — F just exposes `cost_usd_total`)
- ❌ Backfill historical sims (no historical sims exist — synthetic-first paradigm)
- ❌ Tocar `simulator/__init__.py` H9 public API (NO expand needed — F is downstream consumer)
- ❌ Tocar `eval_simulator_grade` o `eval_simulator_llm_call` (read-only)
- ❌ Tocar Story D goldens YAML (read-only — golden_yaml_hash snapshot only)
- ❌ Modificar `core/config.py` defaults (no flag flips this story)
- ❌ Re-run aggregator en CI per-PR (cost prohibitive — manual trigger post-eval-run only)

## Decisiones cardinales (cement)

| # | Decisión | Razón |
|---|---|---|
| D1 | Reframe to **Bloom 4-stage strict all-of-K** (NOT probabilistic `pass_rate^k`) | Anthropic Bloom paper mayo 2026 + AWS Strands canonical. Strict all-of-K matches "production-confidence" semantic Story G CI gate consumes |
| D2 | 4 stages: Understanding / Ideation / Rollout / Judgment per trial | Bloom paper §2.3 canonical breakdown. Stage-level pass_rate exposes flaky root cause (better than ambiguous total score) |
| D3 | Trial pass = all 4 stages pass. pass^K = all K trials pass (binary) | Strict definition — "agent works reliably" requires zero stage failure across K trials |
| D4 | Heterogeneous K per persona_kind (Story C cement: happy=3, nurture=1, unqualified=3, adversarial=3) — aggregator respects, NOT override | Cost optimization + info path nature of nurture (single trial sufficient, multiple trials = redundant cost) |
| D5 | Bloom stage threshold default 0.7 + per-stage env var override (`SALES_AGENT_BLOOM_<stage>_THRESHOLD`) | Story E D13 pattern reused. Per-stage tuning when calibration drift detected |
| D6 | Read-only aggregator — zero LLM calls (consume Story E `MajEvalScore` rows) | Cost optimization + determinism + idempotency |
| D7 | `inputs_hash` field tamper detection + `--validate-strict` flag re-compute | Defense-in-depth vs manual DB tamper or cache poisoning Scenario 4 |
| D8 | Schema `EvalPassKSummary` v1 cement con SCHEMA_MIGRATIONS forward-compat (Story B H1 pattern reused) | Forward-compat 5+ years + adversarial persona_kind Story I additive extension |
| D9 | `unconverged` flag when K_executed < K_required (e.g., simulator failed, fewer than K trials in DB) | Defense-in-depth — partial data marked, NOT silently aggregated |
| D10 | Output JSON `pass_k_report.json` versioned schema (`schema_version: 1`) | Story G CI gate consumes specific fields — bump invalidates downstream consumers safely |
| D11 | `eval_pass_k_summary` DDL idempotent migration (CREATE TABLE IF NOT EXISTS) per `.claude/rules/backend-migrations.md` | Migration safety + parallel session DB pattern |
| D12 | Aggregator path `backend/tests/agentic_evals/sales_agent/pass_k/` (NOT `modules/sales_agent/`) | Test infrastructure ONLY — no touch production runtime |
| D13 | `flaky_goldens` lista en JSON report con `root_cause_stage` + `flaky_evidence` per golden | Surface flaky signal pa Chris + dev — root cause Bloom stage actionable |
| D14 | NO retry on transient error during simulation (Story B owns retries). Aggregator counts trials as-is | Bloom strict semantic — flaky stage is real signal, not infrastructure noise (Story B already retries provider errors) |
| D15 | Goldens YAML mutation detection: pre-commit hook Section 9 + `golden_yaml_hash` field per row | Story D D16 cement (immutable post-commit) — defense-in-depth aggregator-side |
| D16 | Cost-bucket invariant Story B H7: aggregator reads `eval_simulator_grade`, ZERO writes to `eval_simulator_llm_call` o `copilot_llm_call` | Zero contamination prod observability |

## Open questions — RESUELTAS (Chris ratificó 2026-05-08T10:00Z)

- [x] **Q1 → A**: Bloom **4 stages** Understanding/Ideation/Rollout/Judgment per trial (Anthropic Bloom paper). Stage-level pass_rate exposes flaky root cause actionable — Story G CI gate gets richer report.
- [x] **Q2 → A**: **Strict binary all-of-K** (NOT probabilistic). Production-confidence semantic — agent works reliably = zero failure across K trials.
- [x] **Q3 → A**: **Per-stage threshold env vars** = `SALES_AGENT_BLOOM_<stage>_THRESHOLD=0.7` × 4. Matches Story E D13 per-rubric pattern. Granular tuning when calibration drift detected per stage.
- [x] **Q4 → A**: **Include `inputs_hash`** field tamper detection. `--validate-strict` flag re-computes + compares. Defense-in-depth vs manual DB tamper o cache poisoning.
- [x] **Q5 → A**: Goldens YAML mutation = **strict block sin `golden_refresh: true` flag** PR explicit (pre-commit hook Section 9 NEW). Story D D16 cement (immutable post-commit). Chris approval flag pa refresh cycle.
- [x] **Q6 → A**: Unconverged handling = **`pass_k_strict=null` + `unconverged=true` + structlog warn**. Story G CI gate trata null como RED. Surface incomplete data prominentemente.
- [x] **Q7 → A**: **Rich report** scope = `pass_k_rate_global` + per_persona_kind (3 buckets) + per_tenant (5 buckets) + per_stage (4 Bloom buckets) + `flaky_goldens` lista con `root_cause_stage` + `flaky_evidence`.

## Próximo paso

Service-story → `/po` ratifica con Chris (loop iterativo) → spec ratificada → transition `state: refining → refined` → `/architect` orchestrator spawna `/architect-be` (DDL migration + Pydantic models + aggregator + script + pre-commit hook Section 9 + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → `/dev-team` build (espera Stories C+D+E build done — bloqueador hard).

> **Build order ack:** Story F build MUST come AFTER Stories C+D+E builds (consume `MajEvalScore` rows + `trial_policy_by_persona_kind` + goldens YAML + sim trace events). Refinement parallel-safe NOW; build serialization downstream.

## Changelog

- v0 2026-05-04 — `/pm` 00-story.md initial brief (paradigma probabilistic `pass_rate^k`, threshold 0.5 single global, 12 goldens × 3 trials).
- v1 2026-05-08T09:30Z — `/po` reframe Bloom 4-stage strict all-of-K (Anthropic Bloom paper mayo 2026). Consume Story B (`SimulationResult` + trace events) + Story C (heterogeneous `trial_policy_by_persona_kind`) + Story D (ground truth `expected_*`/`forbidden_*` YAML) + Story E (`MajEvalScore.final_score` per rubric). Schema `EvalPassKSummary` v1 con 4-stage breakdown + `inputs_hash` tamper detection + `golden_yaml_hash` mutation snapshot. Heterogeneous K per persona_kind (3/1/3/3). Per-stage threshold env vars (4 × `SALES_AGENT_BLOOM_<stage>_THRESHOLD`). 4 scenarios obligatorios (happy/edge stage attribution/edge heterogeneous K/adversarial tamper detection). 16 decisiones cardinales D1-D16. 7 open questions Q1-Q7 awaiting Chris ratification.
- v2 2026-05-08T10:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). Decisiones cement: D2 Bloom 4 stages; D3 strict all-of-K binary; D5 per-stage env vars; D7 inputs_hash tamper detection; D15 golden YAML mutation strict block sin `golden_refresh: true` flag; D9 unconverged null + structlog warn; rich report con per_stage + per_persona_kind + per_tenant + flaky_goldens. `ratified_by_chris: true`. Service-story → transition `state: refining → refined`. Próximo: `/architect` orchestrator → ready package.
