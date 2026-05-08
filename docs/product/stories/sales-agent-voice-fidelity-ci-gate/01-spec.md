---
story_id: sales-agent-voice-fidelity-ci-gate
type: service-story
module: sales_agent
capability: sales-conversational-engine
po_version: 2
last_modified: 2026-05-08T12:00Z
ratified_by_chris: true   # spec v2 ratificada Chris 2026-05-08T12:00Z (Q1-Q7 todas opción A recomendada)
role_in_outcome: "G — CI gate dynamic threshold per cadence (PR/nightly/monthly) consume Story F pass^K + Story H budget + Story E MajEvalScore"
depends_on:
  - story_b: eval-foundation-simulator-homologation (DONE 2026-05-08) — `run_simulation` + cost-bucket tables
  - story_c: sales-agent-personas-instrumented-runtime (READY 2026-05-08) — `load_actor_profile_for_tenant` + 15 archetype-aware personas
  - story_d: sales-agent-goldens-3-tenants-dataset (REFINED) — 20-30 goldens YAML + coverage matrix
  - story_e: sales-agent-voice-fidelity-grader-runtime (REFINED) — `MajEvalScore.final_score` per (rubric × turn × trial)
  - story_f: sales-agent-eval-pass-k-tracking (REFINED) — `pass_k_report.json` Bloom 4-stage strict all-of-K
  - story_h: sales-agent-eval-cost-budget-cap (REFINED) — `budget_summary.json` abort signal cascade
consumed_by:
  - story_i: sales-agent-adversarial-jailbreak-suite — extends gate con `toxicity-control` rubric (additive cadence row)
links:
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  story_e_spec: "../sales-agent-voice-fidelity-grader-runtime/01-spec.md"
  story_f_spec: "../sales-agent-eval-pass-k-tracking/01-spec.md"
  story_h_spec: "../sales-agent-eval-cost-budget-cap/01-spec.md"
---

## Resumen ejecutivo

> **Reframe vs 00-story.md original (single global threshold 0.7 + warning mode 1 week rollout):** outcome v2 mandate cement → **dynamic threshold per cadence** — PR-trigger gate (lighter scope subset goldens, relaxed 0.65) → nightly full eval (strict 0.7) → monthly comprehensive + adversarial Story I (strictest 0.75 + Chris semestral review).

Implementar el **CI gate aggregator** que consume Story F `pass_k_report.json` + Story H `budget_summary.json` + Story E aggregates → emite GREEN/RED veredicto vs cadence-specific threshold → bloquea merge en GitHub Actions cuando RED → escribe PR comment estructurado con root cause attribution (Bloom stage flaky + persona_kind buckets + tenant buckets).

**Architecture key:**
1. **3 cadences declarative** (PR / nightly / monthly) con threshold + scope (goldens subset/full) + budget cap (warm/cold) + mode (warning/block) per cadence
2. **GitHub Actions workflow `voice-fidelity-gate.yml`** dispatches based on path filters + cron schedule
3. **Cache cross-PR via `commit_sha + golden_set_hash + judge_set_hash`** — re-runs same commit = cache short-circuit
4. **PR comment generator** consume `pass_k_report.json` + `budget_summary.json` → estructurado markdown con flaky evidence + reproduce instructions
5. **Cascade signals:** Story H budget abort → CI red. Story F unconverged goldens → CI red. Story E judge timeout >5% → CI yellow (warning).

## Cambio respecto 00-story.md (original 2026-05-04)

| Aspecto | Original (single threshold) | v1 reframe (dynamic threshold per cadence) |
|---|---|---|
| Threshold | 0.7 single global | 3 cadences con threshold-cadence mapping (PR=0.65 / nightly=0.70 / monthly=0.75) |
| Scope | 12 goldens × 3 trials always | PR=5 goldens (smoke) / nightly=20-30 full / monthly=full + adversarial (Story I) |
| Source signal | `voice_fidelity_score_aggregate` median | `pass_k_report.json` Bloom 4-stage + `budget_summary.json` cost cascade |
| Cache key | `(commit_sha, output_hash, voice_hash)` | `(commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence)` |
| Mode rollout | warning 1 week → block | per-cadence mode (PR=block default / nightly=block / monthly=warning + Chris review) |
| Cost integration | budget cap separate Story 3 | Story H `budget_summary.json` cascade → CI red on abort |
| Trigger | path filters basicos | path filters + cron (nightly 02:00 UTC + monthly 1st of month) |
| PR comment | aggregate score | rich attribution: Bloom stage flaky + persona_kind buckets + tenant buckets + reproduce cmd |
| Adversarial scope | not included | Story I extends additively `monthly` cadence row |
| Cost-bucket cascade | not modeled | Story H budget abort → exit code 2 → CI red distinct from test fail |

## Cadence × threshold × scope matrix (cement)

| Cadence | Trigger | Goldens scope | K trials per persona | Bloom stage threshold | pass_k_rate threshold | Cost cap (warm/cold) | Mode | Wall-clock budget |
|---|---|---|---|---|---|---|---|---|
| **PR-trigger** | path filter on PR | **5 smoke goldens** (1 per tenant × happy persona only) | uniform K=1 | 0.65 per stage | 0.50 global | $30 / $80 | **block** | < 5min |
| **Nightly** | cron 02:00 UTC | **full 20-30 goldens** (Story D dataset complete) | heterogeneous (Story C cement: happy=3/nurture=1/unqualified=3) | 0.70 per stage | 0.65 global | $150 / $500 | **block** | < 30min |
| **Monthly** | cron 1st month 02:00 UTC | **full + adversarial Story I extends** | heterogeneous + adversarial=3 | 0.75 per stage | 0.70 global | $200 / $700 | **warning** + Chris semestral review | < 60min |

> Subset 5 smoke goldens for PR cadence: `tenant_coach_lat × happy`, `tenant_medicina_estetica × happy`, `tenant_clinica_dental × happy`, `tenant_agencia_growth_video × happy`, `tenant_agencia_automatizacion_ia × happy`. Curated en Story D.

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `pr-gate-green-happy-path` (`type: happy`)

**Given:**
- Stories B+C+D+E+F+H delivered y functional
- GitHub Actions workflow `voice-fidelity-gate.yml` configured con path filters: `backend/src/modules/sales_agent/**`, `backend/src/shared/agent_observability/**`, `backend/tests/agentic_evals/sales_agent/**`, `docs/specs/personas/archetype-aware/*.yaml`, `docs/specs/rubrics/*.md`
- Dev abre PR sin tocar voice profile `personality_profile.system_instruction` (no regression risk)
- Env vars: `SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE=pr` (auto-detected from trigger), `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR=0.65`
- 5 smoke goldens disponibles + Story D golden_yaml_hash unchanged

**When:**
- PR push trigger fires workflow
- Workflow ejecuta: `python backend/scripts/run_eval_gate.py --cadence pr --output _artifacts/eval_runs/<run_id>/`
- Script orchestrates: Story B `run_simulation` × 5 smoke goldens × K=1 trial → Story E grading → Story F `compute_pass_k_for_run` → Story H budget tracking
- Resultado: `pass_k_rate_global = 0.80` (4/5 smoke goldens cumplen all-of-K=1) > threshold 0.65, `budget_summary.json.aborted = false`, all judges within variance bounds

**Then:**
- Workflow exit code 0 → CI green check
- PR comment escrito automáticamente:
  ```markdown
  ✅ Voice Fidelity Gate (PR cadence) — PASS
  
  | Metric | Value | Threshold |
  |---|---|---|
  | pass_k_rate_global | 0.80 | ≥ 0.65 ✅ |
  | bloom_stage_min | 0.85 (rollout) | ≥ 0.65 ✅ |
  | budget_total_usd | $14.20 | ≤ $80 cold cap ✅ |
  | judge_unconverged_rate | 0.0% | ≤ 5.0% ✅ |
  
  📊 [Full report](_artifacts/eval_runs/<run_id>/) · 🔄 Cadence: pr (5 smoke goldens × K=1)
  ```
- Cache populated: `(commit_sha=<sha>, golden_set_hash=<h>, judge_set_hash=<h>, rubric_set_hash=<h>, cadence=pr)` → re-running same PR commit short-circuits via cache
- Cost-bucket invariant Story B H7 preserved (read-only orchestration → grader writes `eval_simulator_grade` only)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_pr_cadence.py::test_green_when_threshold_met" }`
- `{ type: integration, path: "backend/tests/scripts/test_run_eval_gate.py::test_pr_cadence_smoke_subset" }`
- `{ type: state_check, target: filesystem, query: "test -f _artifacts/eval_runs/<run_id>/gate_verdict.json" }`
- `{ type: state_check, target: github_actions, query: "exit_code == 0 AND PR comment contains '✅ PASS'" }`

---

### Scenario 2 — `pr-gate-red-bloom-stage-regression` (`type: edge`)

**Given:**
- Dev intentionalmente o accidentalmente rompe voice fidelity en PR (e.g., modifica specialist prompt eliminando voseo support)
- 5 smoke goldens corren, 2 fallan en Bloom Ideation stage (forbidden_tools `enroll_*` invocado prematuramente)
- `pass_k_rate_global = 0.40` (2/5) < threshold 0.65

**When:**
- Workflow ejecuta gate

**Then:**
- Workflow exit code 1 → CI red (NOT exit 2 — cost-abort distinct)
- PR comment estructurado:
  ```markdown
  ❌ Voice Fidelity Gate (PR cadence) — FAIL
  
  | Metric | Value | Threshold |
  |---|---|---|
  | pass_k_rate_global | 0.40 | ≥ 0.65 ❌ |
  | bloom_stage_failing | ideation (0.40) | ≥ 0.65 ❌ |
  | failing_goldens | 2/5 | — |
  
  ### Root cause
  
  Bloom Ideation stage regression detected:
  - `tenant_coach_lat × happy × close_typical_v1`: forbidden tool `enroll_high_ticket` invoked at turn 4
  - `tenant_clinica_dental × happy × invisalign_consult_v1`: forbidden tool `send_payment_link` invoked at turn 3
  
  ### Reproduce locally
  
  ```bash
  cd backend
  .venv/bin/python scripts/run_eval_gate.py --cadence pr --golden tenant_coach_lat/happy/close_typical_v1 --debug
  ```
  
  ### Calibration reference
  
  See `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md` for baseline expectations.
  ```
- PR merge blocked en GitHub branch protection rules (assumes gate is required check)
- Cache NOT populated (failure outcomes excluded — re-run after fix re-grades)
- Story F report `flaky_goldens` field populated with `root_cause_stage: ideation` + `flaky_evidence` arrays consumed verbatim

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_pr_cadence.py::test_red_on_bloom_stage_regression" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_pr_comment_generator.py::test_root_cause_attribution_in_comment" }`
- `{ type: state_check, target: github_actions, query: "exit_code == 1 AND PR comment contains '❌ FAIL'" }`
- `{ type: state_check, target: pr_comment_md, query: "comment contains 'Reproduce locally' command + golden_id evidence" }`

---

### Scenario 3 — `nightly-gate-budget-abort-cascade` (`type: edge`)

**Given:**
- Nightly cron 02:00 UTC fires gate
- Cadence=nightly: 20-30 goldens × heterogeneous K trials × 3 judges Round 1 + Round 2 (variance triggered)
- Mid-run: Story H `BudgetCapExceededError` raised (grader bucket exceeded $400 cap due to Round 2 chain spike)

**When:**
- Story H aborts simulator + grader → exit code 2 (Story H D13 cement)
- `budget_summary.json` written con `aborted: true`, `abort_reason: budget_cap_exceeded`, `abort_bucket: grader`

**Then:**
- Workflow detects Story H exit code 2 cascade → distinct CI status (`failure` con annotation `cost-abort`, NOT generic test failure)
- PR comment / nightly report:
  ```markdown
  ⚠️ Voice Fidelity Gate (nightly cadence) — ABORTED (budget cap exceeded)
  
  Cost-bucket abort triggered:
  - Bucket: grader
  - Current: $402.50
  - Cap: $400.00
  - Aborted at: simulation_id=<uuid>, turn=12, rubric=voice-fidelity
  
  Partial results captured:
  - Completed sims: 18/30
  - pass_k_rate_partial: 0.66 (partial)
  
  Action required: investigate cost runaway (likely Round 2 debate chain spike) before re-running.
  See `_artifacts/eval_runs/<run_id>/budget_summary.json` for full attribution.
  ```
- Workflow exit code = 2 (preserved from Story H)
- Nightly slack/issue notification (separate workflow consuming exit code 2)
- Re-run gate manual after cap adjusted o root cause fixed

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_nightly.py::test_budget_abort_cascade_distinct_status" }`
- `{ type: state_check, target: github_actions, query: "exit_code == 2 (NOT 1)" }`
- `{ type: state_check, target: ci_status, query: "annotation contains 'cost-abort' classification" }`
- `{ type: integration, path: "backend/tests/scripts/test_run_eval_gate.py::test_partial_results_persist_on_abort" }`

---

### Scenario 4 — `gate-bypass-via-skip-tag-defense` (`type: adversarial`)

> AI-resistant: hostile actor (or distracted dev) tries to bypass gate by:
> (a) adding `[skip ci]` commit tag, (b) modifying path filters to exclude their PR, (c) tampering goldens to lower threshold artificially, (d) bypassing required check via repo admin override.

**Given:**
- Hostile/careless PR escenarios:
  - PR commit con `[skip ci]` tag attempting full bypass
  - PR modifies `.github/workflows/voice-fidelity-gate.yml` removing path filters o lowering threshold
  - PR modifies Story D goldens YAML lowering `expected_*` ground truth (Story F `golden_yaml_hash` mismatch)
  - PR modifies env var defaults `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR` lowering threshold

**When:**
- Multiple defense layers engage:

**Then:**
- **Layer 1 — `[skip ci]` cannot bypass required check:** GitHub branch protection rules mark `voice-fidelity-gate-required` as required check (configured separately). `[skip ci]` does NOT skip required checks per GitHub Actions semantics — required check stays unfulfilled → merge blocked
- **Layer 2 — Workflow file changes detected:** PR diff includes `.github/workflows/voice-fidelity-gate.yml` o `backend/scripts/run_eval_gate.py` → arch fitness pre-commit hook flags + auditor manual review required (Chris approval gate)
- **Layer 3 — Goldens tamper detection:** Story F `--validate-strict` flag on gate run re-computes `inputs_hash` + `golden_yaml_hash` → mismatch detected if goldens YAML modified sin `golden_refresh: true` PR flag (Story F D15 cement)
- **Layer 4 — Threshold env var protection:** `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR` defaults frozen en `backend/src/core/config.py`. PR modifying defaults triggers anti-default-flip-audit rule (`.claude/rules/anti-default-flip-audit.md`) → CI hard-fail si threshold lowered sin Chris approval cement
- **Layer 5 — Audit trail:** every gate verdict persisted in `eval_gate_verdict` table (NEW DDL) con `commit_sha` + `cadence` + `verdict` + `inputs_hash` (immutable audit trail). Tamper post-merge detectable
- structlog WARNING: `eval.gate.bypass_attempted` con metadata + caller + change details

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_bypass_defenses.py::test_skip_ci_does_not_bypass_required_check" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_bypass_defenses.py::test_workflow_file_changes_require_review" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/ci_gate/test_gate_bypass_defenses.py::test_goldens_tamper_detected_via_validate_strict" }`
- `{ type: arch_fitness_test, path: "backend/tests/architecture/test_gate_threshold_defaults_protected.py" }`
- `{ type: state_check, target: eval_gate_verdict, query: "row per (commit_sha, cadence) with inputs_hash" }`

---

## Schema cement (`GateVerdict` v1)

```python
# backend/tests/agentic_evals/sales_agent/ci_gate/_schema.py

class GateVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    run_id: str                                       # FK eval run UUID
    commit_sha: str
    pr_number: int | None                             # null for nightly/monthly
    cadence: Literal["pr", "nightly", "monthly"]
    verdict: Literal["pass", "fail", "aborted_budget", "warning_only"]
    pass_k_rate_global: float | None                  # null if aborted
    threshold_applied: float                          # cadence-specific
    bloom_stage_min_score: float | None
    bloom_stage_failing: list[str]                    # ["understanding", "ideation", ...] or empty
    budget_aborted: bool                              # cascade Story H
    budget_abort_bucket: str | None
    judge_unconverged_rate: float | None              # cascade Story E warning
    failing_goldens: list[FailingGoldenDetail]        # for fail verdicts
    inputs_hash: str                                  # tamper detection — hash of pass_k_report + budget_summary + golden_set + judge_set
    cache_hit: bool
    pr_comment_md: str                                # generated markdown for PR comment
    started_at: datetime
    completed_at: datetime
    cost_usd_total: Decimal
    latency_ms_total: int

class FailingGoldenDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    golden_id: str
    tenant_slug: str
    persona_kind: str
    bloom_stage_failed: str                           # root cause stage
    bloom_stage_score: float
    flaky_evidence: list[str]                         # cita verbatim Story F flaky_evidence
    reproduce_cmd: str                                # command to reproduce locally
```

## GitHub Actions workflow contract (`voice-fidelity-gate.yml`)

```yaml
name: voice-fidelity-gate

on:
  pull_request:
    paths:
      - 'backend/src/modules/sales_agent/**'
      - 'backend/src/shared/agent_observability/**'
      - 'backend/tests/agentic_evals/sales_agent/**'
      - 'docs/specs/personas/archetype-aware/*.yaml'
      - 'docs/specs/rubrics/*.md'
      - 'backend/src/core/config.py'  # threshold defaults
  schedule:
    - cron: '0 2 * * *'              # nightly 02:00 UTC
    - cron: '0 2 1 * *'              # monthly 1st 02:00 UTC

jobs:
  determine-cadence:
    outputs:
      cadence: ${{ steps.cadence.outputs.value }}
    steps:
      - id: cadence
        run: |
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            echo "value=pr" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event.schedule }}" == "0 2 1 * *" ]]; then
            echo "value=monthly" >> $GITHUB_OUTPUT
          else
            echo "value=nightly" >> $GITHUB_OUTPUT
          fi

  voice-fidelity-gate-required:    # required check name (branch protection enforces)
    needs: determine-cadence
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python venv
        run: cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
      - name: Run gate
        env:
          SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE: ${{ needs.determine-cadence.outputs.cadence }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          KIMI_API_KEY: ${{ secrets.KIMI_API_KEY }}
        run: cd backend && .venv/bin/python scripts/run_eval_gate.py --cadence "$SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE" --output _artifacts/eval_runs/${{ github.run_id }}/
      - name: Post PR comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const verdict = require('./_artifacts/eval_runs/${{ github.run_id }}/gate_verdict.json');
            await github.rest.issues.createComment({...verdict.pr_comment_md...});
```

> Branch protection rule (configured separately in repo settings): `voice-fidelity-gate-required` is **required check** for `development` and `main` branches → `[skip ci]` cannot bypass.

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Cadence-specific config | 3 cadences (pr/nightly/monthly) con threshold + scope + budget cap + mode independent | unit test config table |
| Cache | `(commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence)` short-circuits re-run | hash-based cache test |
| Wall-clock budget | PR < 5min / nightly < 30min / monthly < 60min | perf test with timeout |
| Cost-bucket invariant | Gate orchestrates Story B+E+F+H — zero NEW LLM calls beyond Story E grader (Story B H7 cement) | DB query post-test |
| Path filter precision | Workflow triggers ONLY on relevant paths (no false positives on docs-only PRs) | path filter test |
| Required check enforcement | `voice-fidelity-gate-required` MUST be configured as required check en branch protection (manual repo admin) | manual setup checklist |
| PR comment idempotent | Multiple comments per PR replaced (NOT appended) on re-runs | unit test comment generator |
| Tamper detection | `inputs_hash` field + Story F `--validate-strict` flag detect goldens/threshold/workflow tamper | adversarial test Scenario 4 |
| Forward-compat | Story I extends `monthly` cadence row additively (adversarial scope) | Pydantic Literal forward-extend |
| Audit trail | `eval_gate_verdict` table immutable rows per (commit_sha, cadence) | DDL idempotent migration |
| Mode rollout policy | All cadences default `block` mode. NO 1-week warning period (per outcome v2 cement — direct enforcement) | env var test |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — gate orchestrator CONSUMES Story B `run_simulation`, Story E `MajEvalScore`, Story F `pass_k_report.json`, Story H `budget_summary.json`. NO mirror grading or aggregation.
- `.claude/rules/auditor-downstream-regression.md` — tabla SSoT MUST add row when `ci_gate/` path created (R3 row addition required, downstream consumer = Story I)
- `.claude/rules/anti-default-flip-audit.md` — `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_*` defaults protected. PR modifying defaults requires Chris approval cement (R29 enforcement).
- `.claude/rules/spanish-text.md` — PR comment markdown + CLI errors = español neutro. Workflow YAML keys English (technical layer).
- `.claude/rules/tdd-mandatory.md` — RED tests primero (cadence config → orchestrator → PR comment generator → bypass defenses → cache)
- `.claude/rules/backend-ddd.md` — gate bajo `backend/tests/agentic_evals/sales_agent/ci_gate/`. Script bajo `backend/scripts/`. NO touch `modules/sales_agent/{domain,application,api}/`
- `.claude/rules/architectural-fitness.md` — NEW arch test `test_gate_threshold_defaults_protected.py` enforces threshold env var defaults frozen
- `.claude/rules/parallel-safety.md` — `eval_gate_verdict` table writes serialized via run_id PK; gate run NEVER skips hooks (`--no-verify` prohibited)
- Story B H7 cost-bucket cement — gate reads `eval_simulator_grade` + `eval_simulator_llm_call` (read-only orchestrator)
- Story C cement — gate respects `trial_policy_by_persona_kind` heterogeneous trials per persona
- Story D D16 cement — goldens immutable post-commit; tamper detection cascade
- Story E cement — judge variance + unconverged signals consumed for warning thresholds
- Story F cement — `pass_k_report.json` schema v1 consumed verbatim
- Story H cement — exit code 2 cascade preserved + abort signal CI distinct status

## Cross-module impact

- **Lee de:**
  - `_artifacts/eval_runs/{run_id}/pass_k_report.json` (Story F output)
  - `_artifacts/eval_runs/{run_id}/budget_summary.json` (Story H output)
  - `eval_simulator_grade` table (Story E rows)
  - `eval_simulator_trace_event` table (Story B rows)
  - `eval_pass_k_summary` table (Story F rows)
  - `backend/tests/agentic_evals/sales_agent/goldens/{tenant}/{kind}/*.yaml` (Story D — golden_set_hash compute)
  - Env vars `SALES_AGENT_VOICE_FIDELITY_THRESHOLD_<cadence>` (NEW per-cadence)
- **Escribe a:**
  - `backend/tests/agentic_evals/sales_agent/ci_gate/__init__.py` (NEW)
  - `backend/tests/agentic_evals/sales_agent/ci_gate/_schema.py` (NEW — `GateVerdict`, `FailingGoldenDetail`)
  - `backend/tests/agentic_evals/sales_agent/ci_gate/orchestrator.py` (NEW — cadence dispatch + Story B+E+F+H integration)
  - `backend/tests/agentic_evals/sales_agent/ci_gate/comment_generator.py` (NEW — markdown PR comment)
  - `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/cadence_config.py` (NEW — 3 cadences declarative)
  - `backend/scripts/run_eval_gate.py` (NEW)
  - `.github/workflows/voice-fidelity-gate.yml` (NEW)
  - `backend/tests/architecture/test_gate_threshold_defaults_protected.py` (NEW arch fitness gate)
  - `eval_gate_verdict` table (NEW DDL idempotent migration)
  - `_artifacts/eval_runs/{run_id}/gate_verdict.json` (NEW JSON output)
  - `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (extend — `eval.ci_gate_cadences` + `eval.ci_gate_workflow_path`)
- **Es leído por:**
  - Story I `adversarial-jailbreak-suite` — extends gate `monthly` cadence con adversarial Story I scope
- **Eventos emitidos:** structlog (`eval.gate.verdict_emitted`, `eval.gate.bypass_attempted`, `eval.gate.cache_hit`)
- **Eventos consumidos:** ninguno

## Out of scope (anti-creep)

- ❌ Per-tenant gate threshold (single global per cadence — Q5 ratified Story E pattern)
- ❌ Slack/email notifications (PR comment + structlog only — outcome cement)
- ❌ Auto-merge if score very high (gate ONLY blocks, never approves)
- ❌ Backfill scoring on historical PRs
- ❌ Gate for other modules (copilot, brand) — sales_agent only
- ❌ Cost gate enforcement (Story H owns — gate consumes signal)
- ❌ Pass^k computation (Story F owns — gate consumes report)
- ❌ Grader implementation (Story E owns — gate orchestrates)
- ❌ Adversarial scope on PR cadence (Story I extends `monthly` only — additive)
- ❌ Mode warning rollout 1-week (outcome v2 cement: direct block, no soft launch)
- ❌ Per-PR custom thresholds (frozen per cadence)
- ❌ Tocar Stories B/E/F/H schemas (read-only consumer)
- ❌ Modificar Story D goldens (read-only — golden_set_hash snapshot)
- ❌ Tocar `simulator/__init__.py` H9 public API (NO expand needed — gate is downstream consumer)

## Decisiones cardinales (cement)

| # | Decisión | Razón |
|---|---|---|
| D1 | 3 cadences declarative (pr / nightly / monthly) con threshold + scope + budget + mode independent | Outcome v2 mandate "dynamic threshold daily→weekly→monthly" |
| D2 | PR cadence: 5 smoke goldens × K=1 trial × threshold 0.65 × budget $30 warm/$80 cold × mode block × wall-clock <5min | Cost-efficient PR signal; smoke subset preserves CI velocity |
| D3 | Nightly cadence: full 20-30 goldens × heterogeneous K × threshold 0.70 × budget $150 warm/$500 cold × mode block × wall-clock <30min | Strict regression detection; matches Story F+H baselines |
| D4 | Monthly cadence: full + Story I adversarial × threshold 0.75 × budget $200 warm/$700 cold × mode warning + Chris semestral review × wall-clock <60min | Comprehensive baseline + adversarial scope; Chris review cycle |
| D5 | NO 1-week warning rollout. All cadences default `block` from day 1 | Outcome v2 cement — direct enforcement (vs original soft-launch) |
| D6 | Cache key `(commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence)` | Composite invalidation precision — re-runs same commit cached, but golden refresh invalidates |
| D7 | PR comment idempotent (replace, not append) on re-runs | Reduces PR noise during gate iterations |
| D8 | Story H exit code 2 preserved cascade — distinct CI status (`cost-abort` annotation) | Distinguishes budget regression from functional regression |
| D9 | Story F `--validate-strict` flag invoked on gate run — tamper detection mandatory | Defense-in-depth Scenario 4 — `inputs_hash` + `golden_yaml_hash` re-compute |
| D10 | NEW arch fitness `test_gate_threshold_defaults_protected.py` enforces env var defaults frozen | Pre-merge gate prevents threshold lowering bypass |
| D11 | Branch protection rule `voice-fidelity-gate-required` (manual repo admin setup) — `[skip ci]` cannot bypass | GitHub Actions semantics: required checks ≠ skippable |
| D12 | DDL idempotent migration `eval_gate_verdict` table — immutable audit trail per (commit_sha, cadence) | Tamper detectable post-merge; cross-PR query for trend analysis |
| D13 | Schema `GateVerdict` v1 cement con SCHEMA_MIGRATIONS forward-compat (Story B H1 reused) | Forward-compat 5+ years; Story I additive cadence row |
| D14 | Path filters precision: `modules/sales_agent/**` + `shared/agent_observability/**` + `agentic_evals/sales_agent/**` + `personas/archetype-aware/*.yaml` + `rubrics/*.md` + `core/config.py` (threshold defaults) | Trigger only on changes potentially affecting voice — not docs/comments |
| D15 | PR cadence smoke subset = 5 goldens (1 per tenant × happy persona only) — curated en Story D | Cost balance vs PR velocity; happy persona = production-critical baseline |

## Open questions — RESUELTAS (Chris ratificó 2026-05-08T12:00Z)

- [x] **Q1 → A**: Cadence × threshold = **escalating PR=0.65 / nightly=0.70 / monthly=0.75**. Outcome v2 mandate "dynamic threshold daily→weekly→monthly". PR cadence relajado (smoke fast feedback) escalando a strict comprehensive monthly.
- [x] **Q2 → A**: PR cadence smoke goldens = **5** (1 per tenant × happy only). Cost-balance vs PR velocity. Happy persona = production-critical baseline. ~$15 budget warm cache. <5min wall-clock.
- [x] **Q3 → A**: **Direct block day 1** (NO 1-week warning rollout). Per outcome v2 mandate. Confidence en pre-launch eval foundation. Warning mode adds drift risk.
- [x] **Q4 → A**: Monthly mode = **warning + Chris semestral review**. Story I adversarial scope incluido — calibration drift expected (false positives). Warning permite Chris review sin alarming devs en release windows.
- [x] **Q5 → A**: Branch protection = **manual repo admin setup checklist**. Documentado como prerequisito post-deploy. Lean implementation. One-time-only Chris en GitHub UI.
- [x] **Q6 → A**: Tamper detection = **Story F `--validate-strict` on every gate run**. Defense-in-depth Scenario 4. Hash overhead mínimo (~ms). Cero false-negative goldens tamper undetected.
- [x] **Q7 → A**: PR comment = **rich attribution** (table metrics + root cause Bloom stage + reproduce cmd + calibration ref). Story F `flaky_evidence` consumed verbatim. Reduce ping-pong PR comments.

## Próximo paso

Service-story → `/po` ratifica con Chris (loop iterativo) → spec ratificada → transition `state: refining → refined` → `/architect` orchestrator spawna `/architect-be` (orchestrator + comment generator + cadence config + workflow YAML + arch fitness gate + DDL migration + capability extension) → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets) → `/dev-team` build (espera Stories B+C+D+E+F+H build done — bloqueador hard).

> **Build order ack:** Story G build LAST en sub-épica eval-foundation (depends Stories B+C+D+E+F+H builds). Refinement parallel-safe NOW; build serialization downstream.

## Changelog

- v0 2026-05-04 — `/pm` 00-story.md initial brief (single threshold 0.7, warning mode 1 week rollout, 12 goldens × 3 trials).
- v1 2026-05-08T11:30Z — `/po` reframe dynamic threshold per cadence (outcome v2 mandate). 3 cadences: PR (5 smoke goldens × K=1 × 0.65 threshold × $30/$80 budget × block), nightly (full 20-30 × heterogeneous K × 0.70 × $150/$500 × block), monthly (full + Story I × 0.75 × $200/$700 × warning + Chris semestral). Consume Story F `pass_k_report.json` + Story H `budget_summary.json` cascade. GitHub Actions workflow `voice-fidelity-gate.yml` con path filters + cron + required check branch protection. PR comment generator rich attribution con root cause Bloom stage + reproduce cmd. Tamper detection 5 layers (skip ci required check + workflow file changes review + goldens hash + threshold defaults arch fitness + audit trail eval_gate_verdict). Schema `GateVerdict` v1 SCHEMA_MIGRATIONS forward-compat. DDL idempotent migration. NO 1-week warning rollout (direct block day 1 per outcome v2 cement). 4 scenarios obligatorios (PR green / PR red Bloom regression / nightly budget abort cascade / adversarial 5-layer bypass defense). 15 decisiones cardinales D1-D15. 7 open questions Q1-Q7 awaiting Chris ratification.
- v2 2026-05-08T12:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). Decisiones cement: D1 escalating thresholds 0.65/0.70/0.75; D2 5 smoke goldens; D5 direct block day 1; D4 monthly warning + Chris semestral; D11 manual branch protection setup checklist; D9 every-run --validate-strict; D7 rich PR comment. `ratified_by_chris: true`. Service-story → transition `state: refining → refined`. Próximo: `/architect`.
