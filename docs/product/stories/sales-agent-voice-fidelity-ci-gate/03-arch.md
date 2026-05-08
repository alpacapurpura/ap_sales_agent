---
story_id: sales-agent-voice-fidelity-ci-gate
arch_role: orchestrator-consolidated-be
arch_version: 1
mode: SINGLE_SHOT_FULLSTACK   # canonical pattern post 2026-05-08 (learnings.md): /architect-orchestrator handles BE+AGENTIC+FE in one pass
                              # Story G = BE-only (CI gate orchestrator + comment generator + workflow YAML) — AGENTIC N/A, FE N/A
last_modified: 2026-05-08T13:00:00Z
links:
  spec: 01-spec.md                       # po_version=2 ratified Chris 2026-05-08T12:00Z (Q1-Q7 all option A)
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  story_b_archive: ../../../archive/2026/stories/eval-foundation-simulator-homologation/
  story_c_archive: ../../../archive/2026/stories/sales-agent-personas-instrumented-runtime/
  story_d_spec: ../sales-agent-goldens-3-tenants-dataset/01-spec.md
  story_e_arch: ../sales-agent-voice-fidelity-grader-runtime/03-arch.md
  story_f_arch: ../sales-agent-eval-pass-k-tracking/03-arch.md
  story_h_arch: ../sales-agent-eval-cost-budget-cap/03-arch.md
  consumers:
    - ../sales-agent-adversarial-jailbreak-suite/   # I — extends gate `monthly` cadence row additively
date_research: 2026-05-08
---

## §0 Resumen

Story G entrega el **CI gate aggregator + GitHub Actions workflow + PR comment generator + DDL migration `eval_gate_verdict`** bajo `backend/tests/agentic_evals/sales_agent/ci_gate/` + `backend/scripts/run_eval_gate.py` + `.github/workflows/voice-fidelity-gate.yml` + arch fitness gate `test_gate_threshold_defaults_protected.py`. Cierra el loop del Objetivo 2 del PI-12 (eval foundation): convierte el grader Story E + pass^k Story F + budget cap Story H + goldens Story D + simulator Story B + personas Story C en **garantía operacional vs PR merge**.

**Paradigma:** **dynamic threshold per cadence** (3 cadences declarative — PR / nightly / monthly) consume Stories F+H artifacts read-only → emit `GateVerdict` v1 row per `(commit_sha, cadence)` en NEW table `eval_gate_verdict` + JSON output `_artifacts/eval_runs/{run_id}/gate_verdict.json` + Markdown PR comment via `actions/github-script@v7`.

**Read-only orchestrator invariant cement:** gate aggregator NO emite LLM calls — solo **orchestrates** Story B `run_simulation` × Story E grading (write to `eval_simulator_grade`) × Story F `compute_pass_k_for_run` (write to `eval_pass_k_summary`) × Story H budget tracking. Cero NEW LLM calls beyond Story E grader (Story B H7 cost-bucket cement). Arch fitness gate `test_aggregator_no_llm_calls.py` (Story F NEW) extends to cover Story G aggregator.

**Cero deuda invariants** (heredados Stories B/C/D/E/F/H protected):

- `simulator/__init__.py` H9 surface frozen (post Story E expand 7→8, Story H expand 8→9) — Story G no toca (consumer downstream — aggregator API vive en `ci_gate/__init__.py` package-local).
- `personality_profiles.system_instruction` SSoT untouched — gate no lee voz, solo Story E `MajEvalScore` rows + Story F `pass_k_report.json` + Story H `budget_summary.json`.
- Cost-bucket separation (Story B H7 + Story F D6 cement): gate orchestrator escribe SOLO a `eval_gate_verdict` (NEW table separate). Cero touch a `eval_simulator_llm_call/grade/grade_cache`, `eval_pass_k_summary`, `copilot_llm_call`, `sales_agent_llm_call`.
- `LLM_ROLE_BY_SITE` SSoT — Story G NO agrega rol (no LLM calls — orchestrator).
- Anti-duplication §0 — gate CONSUMES Story F `pass_k_report.json` + `eval_pass_k_summary` table (no recompute pass^K), Story H `budget_summary.json` (no recompute budget), Story E `eval_simulator_grade` rows (no re-grade), Story B `run_simulation` API + `eval_simulator_trace_event` (no re-simulate), Story C `trial_policy_by_persona_kind` constants (heterogeneous K), Story D goldens YAML (golden_set_hash compute). NO mirror grading, simulation, pass^K, budget, persona loading.
- R5 schema-mirror exception — DDL migration NEW las maneja `builder-backend` Sonnet (declarative SQL); model en `modules/sales_agent/observability/eval_simulator/persistence/models/eval_gate_verdict.py` (paridad Story B/E/F pattern).
- Goldens YAML immutable post-commit (Story D D16 + Story F D15 cement) — defense-in-depth via `golden_yaml_hash` snapshot + Story F `--validate-strict` flag invoked on every gate run.
- Schema versioning forward-compat (Story B H1 reuse) — `GateVerdict.schema_version: Literal[1] = 1` cement; future bumps register migrator post-ship. Story I extends `cadence` Literal additively (NO bump v1→v2 — Literal allows superset forward).
- `inputs_hash` field tamper detection (D9 cement spec) — composite hash of (`pass_k_report` + `budget_summary` + `golden_set_hash` + `judge_set_hash` + `rubric_set_hash` + `cadence` + `commit_sha`). Mismatch → `GateValidationError`.

**Owner choice rationale (TL;DR):** Story G = service-story BE-only `production_code: false` CI infrastructure + tests + docs. R23 explicit allow Sonnet (production_code=false → Sonnet OK). All 6 tickets `builder-backend` Sonnet eligible:
- T-1 DDL migration + SQLA model (declarative SQL + R5 schema-mirror)
- T-2 Pydantic schemas (declarative)
- T-3 cadence config (declarative dict + Pydantic validation)
- T-4 orchestrator + comment generator (deterministic Python pipeline — orchestrate Stories B/E/F/H subprocess calls + JSON parsing + Markdown templating)
- T-5 GitHub Actions workflow YAML + CLI script entry (declarative YAML + argparse)
- T-6 arch fitness gate + capability YAML extension + module narrative (3 NEW arch tests + post-merge by /pm)

PM confirms final routing antes Conv 2 starts. Build order: hard blocker on Stories B+C+D+E+F+H build done — Story G es **last** en sub-épica eval-foundation.

## §1 Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| BE test-infrastructure (DDL idempotent migration `eval_gate_verdict` + SQLA 2.0 async model R5 schema-mirror + Pydantic v2 types `GateVerdict`/`FailingGoldenDetail`/`CadenceConfig` + cadence_config.py declarative + orchestrator.py + comment_generator.py + script run_eval_gate.py + arch fitness gate + capability YAML extension + module narrative + downstream regression rule entry) | NO (test-infra + R5 schema-mirror exception) | **`builder-backend` Sonnet** (declarative SQL + Pydantic types + simple deterministic orchestration pipeline + Markdown templating + YAML workflow + arch ratchet) | **`auditor-backend` Opus C1-C3 + Sonnet tests** | backend-expert, tessl__fastapi (Pydantic v2 patterns), tessl__pytest-api-testing, tessl__graceful-degradation |
| CI infrastructure (`.github/workflows/voice-fidelity-gate.yml` + branch protection setup checklist for repo admin) | NO (CI infra) | **`builder-backend` Sonnet** | **`auditor-backend` Opus C1-C3** | playwright-expert reference for CI patterns (read-only) |
| AGENTIC | N/A (read-only orchestrator — zero NEW LLM calls beyond Stories B/E orchestrated) | — | — | — |
| FE | N/A | — | — | — |

> **Owner choice rationale**: Story G service-story `production_code: false`, simple deterministic CI orchestration pipeline (zero LLM/agentic/LangGraph). Per CLAUDE.md cost-routing matrix R23: agentic tickets `production_code=false` → Sonnet OK. Story G **no es agentic** (orchestrator subprocess calls + JSON parsing + Markdown templating). **Sonnet OK todos los 6 tickets**. Per Chris autonomy mandate cero deuda 1000+ tenants: gate is leverage point cross-stories I, but logic = subprocess orchestration + JSON deserialization + dict aggregation + sha256 hash + Markdown rendering. Sonnet handles native. Si en build encuentra bloqueo en T-4 orchestrator (subprocess error handling) o T-5 GitHub Actions YAML (required check semantics) → escalate /pm para Opus override puntual. PM confirms final routing en spawn.

## §2 Existing systems audit (NO NEW LAYER rule — `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] Self-run greps Path B (CONTEXT-BRIEF.md absent — direct audit prior to design ratification)

### Audit cross-module ejecutado

```bash
# 1. Cross-codebase ci_gate + GateVerdict + run_eval_gate + eval_gate_verdict + voice-fidelity-gate — verify NEW genuinely
grep -rn "ci_gate\|GateVerdict\|run_eval_gate\|eval_gate_verdict\|voice-fidelity-gate" \
  backend/ .github/ 2>/dev/null | grep -v __pycache__
# Result: ZERO BE/test code matches. Only spec/00-story.md/checkpoint.md references in story dir.
# Conclusion: feature genuinely NEW — no parallel layer to subsume.

# 2. Existing CI gate workflows — confirm only llm-eval-gate.yml exists (different paradigm)
ls .github/workflows/
# Result: deploy-prod.yml + e2e-tests.yml + llm-eval-gate.yml + test-ssh.yml
# llm-eval-gate.yml triggers on .env.example/litellm_config.yaml/copilot/evals path — different paradigm:
#   - copilot classifier/summarizer eval gate (no sales_agent eval)
#   - threshold per-role (NOT per-cadence)
#   - no JSON output / no eval_gate_verdict table / no PR comment with root-cause attribution
# Conclusion: Story G workflow is genuinely NEW — orthogonal paradigm (sales_agent voice fidelity per-cadence).

# 3. Existing PR comment generators / orchestrators
grep -rn "actions/github-script\|gh pr comment" .github/ backend/scripts/ 2>/dev/null
# Result: llm-eval-gate.yml uses actions/github-script@v7 for failure comment (single template).
# Story G needs RICH attribution comment — multi-template (PASS/FAIL/ABORTED) + table + root cause + reproduce cmd.
# Conclusion: NEW comment_generator.py with Markdown templating — no existing module to extend.

# 4. eval_gate_verdict table — confirm NEW (no existing migration)
find backend/alembic/versions -name "*gate_verdict*" -o -name "*ci_gate*" 2>/dev/null
# Result: empty. NEW migration justified (number 129, post Story F=128, Story H=no DDL).

# 5. Story F pass_k_report.json + Story H budget_summary.json paths
grep -rn "pass_k_report.json\|budget_summary.json" backend/tests/ 2>/dev/null | head -5
# Result: not yet built (Stories F+H refined, await build). Gate references planned artifacts:
#   - _artifacts/eval_runs/{run_id}/pass_k_report.json (Story F output)
#   - _artifacts/eval_runs/{run_id}/budget_summary.json (Story H output)
# Build order: Stories F+H build precede Story G build (hard blocker).

# 6. Cadence config — confirm no existing
grep -rn "CadenceConfig\|cadence_config\b\|GATE_CADENCE" backend/ 2>/dev/null | head -5
# Result: empty. NEW genuinely.

# 7. inputs_hash composition — Story F precedent reusable
grep -n "compute_inputs_hash\|inputs_hash" docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md | head -5
# Result: Story F §3.6 inputs_hasher.py — sha256 composition pattern. Story G aggregator REUSES pattern
#   but composes different inputs (pass_k_report + budget_summary + golden_set_hash + judge_set_hash + rubric_set_hash + cadence + commit_sha)
# Conclusion: pattern reusable, NEW composition function inside ci_gate/_internal/inputs_hasher.py
#   (separate from Story F inputs_hasher because different inputs).

# 8. SCHEMA_MIGRATIONS registry — confirm Stories E/F/H entries planned
grep "register_schema_migration\|CURRENT_SCHEMA_VERSIONS" docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md | head -3
# Result: Story F §3.3 — anchor entry `EvalPassKSummary v1`. Story H §3.1 — anchor `BudgetState v1`.
# Story G adds `GateVerdict v1` anchor (sentinel for future bumps).

# 9. Capability YAML extension target
ls docs/product/capabilities/sales-agent/sales-conversational-engine.yaml
# Result: file exists, Story C extended with eval block. Story F appends pass_k_report fields.
# Story G appends `eval.ci_gate_cadences` (3 cadences config) + `eval.ci_gate_workflow_path` + `eval.ci_gate_table` + `eval.ci_gate_branch_protection_required_check`.

# 10. Branch protection setup checklist target
grep -rn "branch protection\|required check\|voice-fidelity-gate-required" docs/process/ 2>/dev/null | head -5
# Result: no existing checklist. Story G adds checklist to module narrative (post-merge by /pm)
# + optional separate `docs/process/branch-protection-checklist.md` if /pm decides standalone.

# 11. arch fitness threshold default protection — Story F precedent
grep -n "test_bloom_threshold_defaults_protected" docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md | head -2
# Result: Story F NEW gate `test_bloom_threshold_defaults_protected.py`. Story G adds analogous
#   `test_gate_threshold_defaults_protected.py` (different env vars: SALES_AGENT_VOICE_FIDELITY_THRESHOLD_<CADENCE>).
# Reuse Story F pattern, NEW gate file (different env var names).
```

### Sistemas existentes encontrados (Stories B/C/D/E/F/H SSoT — consume READ-ONLY, NOT mirror)

| Sistema | Path canónico | Estado | Decisión Story G |
|---|---|---|---|
| Story B `run_simulation` API + `eval_simulator_trace_event` | `tests/agentic_evals/sales_agent/simulator/__init__.py` (H9 frozen 7→8 post E, 8→9 post H) + table | active (Story B done, E/H refined) | **READ-ONLY** — orchestrator invokes `run_simulation()` for each (golden × persona × trial); reads trace events for Story F pass^K |
| Story C `trial_policy_by_persona_kind` (heterogeneous K) | `tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` | active (refined) | **READ-ONLY** — orchestrator imports policy constants for trial planning |
| Story D goldens YAML | `tests/agentic_evals/sales_agent/goldens/{tenant}/{kind}/*.yaml` | refined (build pending) | **READ-ONLY** — gate reads YAML at compute time, computes `golden_set_hash` snapshot |
| Story E `MajEvalScore` rows in `eval_simulator_grade` | table (via Story E migration 127) | refined (build pending) | **READ-ONLY** — gate reads rows for variance + unconverged signal cascade |
| Story F `EvalPassKSummary` rows in `eval_pass_k_summary` + `pass_k_report.json` | table (Story F migration 128) + JSON output | refined (build pending) | **READ-ONLY** — gate reads `pass_k_rate_global` + `pass_k_rate_per_stage` + `flaky_goldens` for verdict + comment attribution |
| Story F `--validate-strict` CLI flag | `backend/scripts/compute_pass_k_report.py` | refined (build pending) | **INVOKE** — orchestrator runs `compute_pass_k_report.py --validate-strict` for tamper detection (D9 cement) |
| Story H `BudgetState` JSON `budget_summary.json` + exit code 2 cascade | `backend/scripts/run_simulation_with_budget.py` (or similar) + JSON output | refined (build pending) | **READ-ONLY** — gate reads `aborted` + `abort_reason` + `abort_bucket` for cascade verdict; preserves exit code 2 distinct status |
| Story F `inputs_hasher` pattern | `tests/agentic_evals/sales_agent/pass_k/_internal/inputs_hasher.py` | refined (build pending) | **REUSE PATTERN** — Story G adds `ci_gate/_internal/inputs_hasher.py` with different composition (pass_k_report + budget_summary + golden_set_hash + judge_set_hash + rubric_set_hash + cadence + commit_sha) — NOT mirror, separate inputs |
| `SCHEMA_MIGRATIONS` registry (Story B H1) | `tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` | active 4 entries (Stories C+E+F+H planned) | **EXTEND** — register `GateVerdict v1` anchor (sentinel for future bumps; no migrator function v1) |
| `_VALID_TENANT_SLUGS` (Story C) | `tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` | active frozenset 5 valid | **READ-ONLY** — gate validates `tenant_slug` from grade rows against set |
| `EvalSimulatorObservabilityContext` (Story B) | `tests/agentic_evals/sales_agent/simulator/_internal/observability.py` | active | **NO TOUCH** — gate emits structlog events ONLY (no DB writes to llm_call/trace_event); orchestrator wraps Story B `run_simulation` which uses context internally |
| `simulator/__init__.py` `__all__` 7→8→9 names (H9) | `tests/agentic_evals/sales_agent/simulator/__init__.py` | active frozen | **NO TOUCH** — Story G aggregator NO se exporta via simulator surface (vive en `ci_gate/__init__.py` package separado) |
| Capability YAML | `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` | active (extended Stories C+F) | **EXTEND** — append `eval.ci_gate_*` block fields (additive, post-merge by /pm) |
| `auditor-downstream-regression.md` rule SSoT | `.claude/rules/auditor-downstream-regression.md` | active | **EXTEND** — append `tests/agentic_evals/sales_agent/ci_gate/` row + downstream consumer = Story I (post-merge by /pm) |
| `llm-eval-gate.yml` (existing CI workflow) | `.github/workflows/llm-eval-gate.yml` | active (copilot classifier/summarizer paradigm) | **NO TOUCH** — orthogonal paradigm; Story G adds NEW workflow `voice-fidelity-gate.yml` |
| `core/config.py` Settings class | `backend/src/core/config.py` | active | **NO TOUCH** — Story G adds NEW env vars (`SALES_AGENT_VOICE_FIDELITY_THRESHOLD_<CADENCE>` x3 + `SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE`) but defaults live in `cadence_config.py` declarative dict (NOT in core/config.py — anti-default-flip-audit per R29 keeps core/config.py threshold defaults frozen) |

### Decisión por sistema — sumario

- **READ-ONLY (consume only)**: Story B `run_simulation` API + `eval_simulator_trace_event`, Story C `trial_policy_by_persona_kind`, Story D goldens YAML, Story E `eval_simulator_grade`, Story F `eval_pass_k_summary` + `pass_k_report.json` + `--validate-strict`, Story H `BudgetState` + `budget_summary.json` + exit code 2. Gate orchestrates via subprocess + reads JSON files + reads DB rows; NEVER writes back.
- **EXTEND (additive, justified)**: `SCHEMA_MIGRATIONS` registry (1 anchor entry `GateVerdict` v1), capability YAML eval block (`eval.ci_gate_*` 4 fields), `auditor-downstream-regression.md` table SSoT (1 NEW row `ci_gate/` path).
- **REUSE PATTERN (justified, NOT mirror)**: Story F `inputs_hasher.py` sha256 composition pattern → Story G `ci_gate/_internal/inputs_hasher.py` with different inputs (pass_k_report + budget_summary + golden_set_hash + judge_set_hash + rubric_set_hash + cadence + commit_sha). Different composition function = separate file (justified by anti-duplication §0 path B audit row 7).
- **NEW (genuinely justified, last resort — no existing system overlaps ≥80%)**:
  - DDL migration `129_add_eval_gate_verdict_table.py` (raw SQL idempotent, 1 NEW table + 4 indexes)
  - SQLAlchemy 2.0 async model `eval_gate_verdict.py` (R5 schema-mirror exception)
  - Pydantic types `_schema.py` (`GateVerdict`, `FailingGoldenDetail`, `CadenceConfig`)
  - `_internal/cadence_config.py` (declarative 3 cadences PR/nightly/monthly)
  - `_internal/inputs_hasher.py` (sha256 deterministic composition for gate verdict)
  - `orchestrator.py` (`compute_gate_verdict` + Stories B/E/F/H subprocess orchestration + cache lookup)
  - `comment_generator.py` (Markdown PR comment templating — PASS/FAIL/ABORTED templates Spanish neutro user-facing)
  - `scripts/run_eval_gate.py` CLI
  - `.github/workflows/voice-fidelity-gate.yml` GitHub Actions workflow
  - 1 NEW arch fitness gate (`test_gate_threshold_defaults_protected.py`)
- **NO TOUCH**: §3 sales-agent protected surfaces, `simulator/__init__.py` public API (frozen 9 names post Story H), `personality_profiles.system_instruction`, `LLM_ROLE_BY_SITE`, `core/config.py` Settings defaults (R29 cement), `eval_simulator_*` DB schema, `eval_pass_k_summary` schema (Story F cement), `BudgetState` schema (Story H cement), Story D goldens YAML content (mutation detected by Story F hook + `--validate-strict`), `simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,...}`, `pass_k/{aggregator,bloom_scorer,inputs_hasher}` (Story F territory — read via SQL), `budget/{guard,cost_estimator,sweep}` (Story H territory — read via JSON), `modules/{copilot,sales_agent}/{domain,application,api}/`, frontend/, client_simulator/, llm-eval-gate.yml (orthogonal copilot paradigm).

## §3 BE arch (DDL idempotent + SQLA 2.0 + Pydantic v2 + cadence config + orchestrator + comment generator + script + workflow YAML + arch fitness gate)

### §3.1 NEW migration `129_add_eval_gate_verdict_table.py` (raw SQL idempotent)

Pattern parity con Alembic 125 (Story B) + 127 (Story E) + 128 (Story F).

```python
"""Eval gate verdict table (Story G sales-agent-voice-fidelity-ci-gate).

Idempotente raw SQL IF NOT EXISTS (regla backend-migrations.md).

Creates 1 new table + 4 indexes for the CI gate verdict aggregator:
  - eval_gate_verdict : GateVerdict rows per (commit_sha, cadence) — immutable audit trail

Pattern parity: eval_simulator (Alembic 125) + eval_simulator_grade (Alembic 127) + eval_pass_k_summary (Alembic 128).
Cost-bucket invariant H7 — gate aggregator NO escribe a llm_call tables; solo a este NEW table.

Decision D-BE-1: schema_version column = 1 cement; future bumps via SCHEMA_MIGRATIONS registry (H1 reuse).
Decision D-BE-2: PK composite (commit_sha, cadence) — natural-key idempotency; re-runs UPSERT.
Decision D-BE-3: failing_goldens JSONB stored verbatim (audit trail) for FailingGoldenDetail list.
Decision D-BE-4: inputs_hash + golden_set_hash + judge_set_hash + rubric_set_hash columns para D9 tamper detection.
Decision D-BE-5: pr_comment_md TEXT column persisted (multi-line Markdown) — idempotent comment replacement on re-runs.

Revision ID: 129_add_eval_gate_verdict_table
Revises: 128_add_eval_pass_k_summary_table
Create Date: 2026-05-08
"""

from alembic import op

revision = "129_add_eval_gate_verdict_table"
down_revision = "128_add_eval_pass_k_summary_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create eval_gate_verdict table."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_gate_verdict (
            schema_version SMALLINT NOT NULL DEFAULT 1,
            run_id UUID NOT NULL,
            commit_sha VARCHAR(40) NOT NULL,
            pr_number INTEGER,
            cadence VARCHAR(16) NOT NULL,
            verdict VARCHAR(32) NOT NULL,
            pass_k_rate_global NUMERIC(5,4),
            threshold_applied NUMERIC(5,4) NOT NULL,
            bloom_stage_min_score NUMERIC(5,4),
            bloom_stage_failing JSONB NOT NULL DEFAULT '[]'::jsonb,
            budget_aborted BOOLEAN NOT NULL DEFAULT FALSE,
            budget_abort_bucket VARCHAR(32),
            judge_unconverged_rate NUMERIC(5,4),
            failing_goldens JSONB NOT NULL DEFAULT '[]'::jsonb,
            inputs_hash VARCHAR(64) NOT NULL,
            golden_set_hash VARCHAR(64) NOT NULL,
            judge_set_hash VARCHAR(64) NOT NULL,
            rubric_set_hash VARCHAR(64) NOT NULL,
            cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
            pr_comment_md TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ NOT NULL,
            cost_usd_total NUMERIC(10,6) NOT NULL DEFAULT 0,
            latency_ms_total INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_eval_gate_verdict PRIMARY KEY (commit_sha, cadence)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_gate_verdict_run
        ON eval_gate_verdict (run_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_gate_verdict_pr
        ON eval_gate_verdict (pr_number) WHERE pr_number IS NOT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_gate_verdict_cadence_verdict
        ON eval_gate_verdict (cadence, verdict)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_gate_verdict_created_at
        ON eval_gate_verdict (created_at DESC)
    """)


def downgrade() -> None:
    """Drop CI gate verdict table (eval-only, no production data)."""
    op.execute("DROP TABLE IF EXISTS eval_gate_verdict CASCADE")
```

**Idempotency test command** (Native WSL):

```bash
cd backend && docker exec visionarias_brain_dev alembic upgrade head
# Re-run twice — both succeed (IF NOT EXISTS preserves):
cd backend && docker exec visionarias_brain_dev alembic upgrade head
# Validator `migration_idempotency` runs both invocations and asserts zero error.
```

### §3.2 SQLAlchemy 2.0 async model (R5 schema-mirror exception)

File NEW: `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_gate_verdict.py` (paridad Story B/E/F pattern). R5 exception applies — `builder-backend` MAY touch `persistence/models/` for schema mirror from migration. Cero domain/application/api/ touches.

```python
"""SQLAlchemy model for ``eval_gate_verdict`` (Story G CI gate verdict aggregator).

Mirror of Alembic migration 129. Pydantic ``GateVerdict`` v1 schema cement.

Pattern parity: ``eval_pass_k_summary.py`` (Story F). R5 schema-mirror exception
(.claude/rules/backend-ddd.md): builder-backend MAY touch persistence/models/ for schema
mirror from migration. Cero domain/application/api/ touches.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class EvalGateVerdictModel(Base):
    """ORM mapping for ``eval_gate_verdict``.

    PK composite ``(commit_sha, cadence)`` — one row per gate run per cadence.
    failing_goldens JSONB stores list[FailingGoldenDetail dict] verbatim (audit trail).
    bloom_stage_failing JSONB stores list[str] (e.g. ['ideation', 'rollout']).
    pr_comment_md TEXT stores multi-line Markdown for idempotent re-comment on re-runs.
    """

    __tablename__ = "eval_gate_verdict"

    schema_version = Column(SmallInteger, nullable=False, default=1)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    commit_sha = Column(String(40), nullable=False)
    pr_number = Column(Integer, nullable=True)
    cadence = Column(String(16), nullable=False)
    verdict = Column(String(32), nullable=False)
    pass_k_rate_global = Column(Numeric(5, 4), nullable=True)
    threshold_applied = Column(Numeric(5, 4), nullable=False)
    bloom_stage_min_score = Column(Numeric(5, 4), nullable=True)
    bloom_stage_failing = Column(JSONB, nullable=False, default=list)
    budget_aborted = Column(Boolean, nullable=False, default=False)
    budget_abort_bucket = Column(String(32), nullable=True)
    judge_unconverged_rate = Column(Numeric(5, 4), nullable=True)
    failing_goldens = Column(JSONB, nullable=False, default=list)
    inputs_hash = Column(String(64), nullable=False)
    golden_set_hash = Column(String(64), nullable=False)
    judge_set_hash = Column(String(64), nullable=False)
    rubric_set_hash = Column(String(64), nullable=False)
    cache_hit = Column(Boolean, nullable=False, default=False)
    pr_comment_md = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    cost_usd_total = Column(Numeric(10, 6), nullable=False, default=0)
    latency_ms_total = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "commit_sha", "cadence",
            name="pk_eval_gate_verdict",
        ),
    )
```

> **Async session pattern**: tests use `AsyncSession` from `src.core.database` via Story B `conftest.py` fixture. NEVER `session.query()` (SA 1.x). Insert via `session.add(...)` + `await session.commit()`. Read via `select(EvalGateVerdictModel).where(...)`. UPSERT pattern: PostgreSQL `INSERT ... ON CONFLICT (commit_sha, cadence) DO UPDATE` for re-run idempotency.

### §3.3 Pydantic v2 types — `backend/tests/agentic_evals/sales_agent/ci_gate/_schema.py`

Cement schema_version=1; bumps via SCHEMA_MIGRATIONS post-ship (Story B H1 reuse). Story I extends `cadence` Literal additively (NO bump v1→v2 — Literal allows superset forward).

```python
"""CI gate verdict Pydantic types (Story G v1 cement).

Schema versioning: ``GateVerdict.schema_version: Literal[1] = 1``. Future bumps via
``SCHEMA_MIGRATIONS`` registry (Story B H1 reuse) — register identity migrator
(GateVerdict, 1, 2) when bumping. Frozen=True per ConfigDict (immutable post-verdict).

Story G is read-only orchestrator — these types model the AGGREGATION OUTPUT only,
NOT the inputs (Story F pass_k_report.json + Story H budget_summary.json + Story E
eval_simulator_grade rows stay queried via SQL/JSON read).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FailingGoldenDetail(BaseModel):
    """Per-golden failure detail in GateVerdict.failing_goldens list."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    golden_id: str
    tenant_slug: Literal[
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    ]
    persona_kind: Literal["happy", "nurture", "unqualified", "adversarial"]
    bloom_stage_failed: Literal["understanding", "ideation", "rollout", "judgment"]
    bloom_stage_score: float = Field(ge=0.0, le=1.0)
    flaky_evidence: list[str]                                                       # cited verbatim from Story F flaky_evidence
    reproduce_cmd: str                                                              # CLI command Spanish neutro stderr-friendly


class CadenceConfig(BaseModel):
    """Single cadence declarative config — 3 instances cement (PR/nightly/monthly)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cadence: Literal["pr", "nightly", "monthly"]
    threshold_pass_k_rate: float = Field(ge=0.0, le=1.0)                            # PR=0.65 / nightly=0.70 / monthly=0.75
    threshold_bloom_stage: float = Field(ge=0.0, le=1.0)                            # per-stage min — PR=0.65 / nightly=0.70 / monthly=0.75
    goldens_scope: Literal["smoke_5", "full_20_30", "full_plus_adversarial"]
    k_trials_uniform: int | None = Field(default=None, ge=1, le=10)                  # PR=1 (uniform) / nightly=null (heterogeneous via Story C) / monthly=null
    budget_warm_usd: Decimal                                                         # PR=$30 / nightly=$150 / monthly=$200
    budget_cold_usd: Decimal                                                         # PR=$80 / nightly=$500 / monthly=$700
    mode: Literal["block", "warning"]                                                # PR=block / nightly=block / monthly=warning
    wall_clock_max_seconds: int = Field(ge=60, le=7200)                              # PR=300 / nightly=1800 / monthly=3600


class GateVerdict(BaseModel):
    """CI gate verdict aggregated per (commit_sha × cadence)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1                                                   # cement v1 — future bumps register migrator
    run_id: str                                                                       # FK eval run UUID (string)
    commit_sha: str = Field(min_length=7, max_length=40)                              # GitHub SHA
    pr_number: int | None = Field(default=None, ge=1)                                 # null for nightly/monthly
    cadence: Literal["pr", "nightly", "monthly"]                                      # Story I extends additively (Literal forward-compat)
    verdict: Literal["pass", "fail", "aborted_budget", "warning_only"]
    pass_k_rate_global: float | None = Field(default=None, ge=0.0, le=1.0)            # null if aborted before pass^K compute
    threshold_applied: float = Field(ge=0.0, le=1.0)                                  # cadence-specific threshold cited
    bloom_stage_min_score: float | None = Field(default=None, ge=0.0, le=1.0)         # min(pass_k_rate_per_stage)
    bloom_stage_failing: list[Literal["understanding", "ideation", "rollout", "judgment"]]  # stages below threshold
    budget_aborted: bool                                                              # cascade from Story H
    budget_abort_bucket: Literal["generation", "grader"] | None = None                # cascade bucket
    judge_unconverged_rate: float | None = Field(default=None, ge=0.0, le=1.0)        # cascade Story E warning signal
    failing_goldens: list[FailingGoldenDetail]                                        # populated for fail verdicts (verbatim Story F flaky_evidence)
    inputs_hash: str = Field(min_length=64, max_length=64)                            # sha256 hex(pass_k_report + budget_summary + golden_set_hash + judge_set_hash + rubric_set_hash + cadence + commit_sha) — D9 tamper detection
    golden_set_hash: str = Field(min_length=64, max_length=64)                        # sha256 hex(all goldens YAML for cadence scope) — D6 cache key component
    judge_set_hash: str = Field(min_length=64, max_length=64)                         # sha256 hex(judge models + weights + temperatures from Story E) — D6 cache key component
    rubric_set_hash: str = Field(min_length=64, max_length=64)                        # sha256 hex(rubric MDs + version + threshold from docs/specs/rubrics/) — D6 cache key component
    cache_hit: bool                                                                   # true if (commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence) cache row found
    pr_comment_md: str                                                                # Spanish neutro user-facing Markdown for PR comment (idempotent replace on re-run)
    started_at: datetime
    completed_at: datetime
    cost_usd_total: Decimal = Decimal("0")                                            # sum of orchestrated Stories E grading cost (Story F+H aggregate)
    latency_ms_total: int = Field(ge=0)
```

### §3.4 Cadence config declarative — `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/cadence_config.py`

D1+D2+D3+D4+D5+D14 cement. 3 cadences declarative; arch fitness gate `test_gate_threshold_defaults_protected.py` enforces dict byte-equal.

```python
"""CI gate cadence config (Story G D1-D4 cement — 3 cadences declarative).

Single source of truth for cadence × threshold × scope × budget × mode × wall-clock matrix.
Arch fitness gate `test_gate_threshold_defaults_protected.py` enforces dict byte-equal.

Story I extends additively — adds 4th cadence row (NOT replace existing 3).

Threshold defaults frozen — anti-default-flip-audit rule R29 enforces. PR modifying
defaults requires Chris approval cement (CI hard-fail).

Env var override pattern:
- SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR (default 0.65)
- SALES_AGENT_VOICE_FIDELITY_THRESHOLD_NIGHTLY (default 0.70)
- SALES_AGENT_VOICE_FIDELITY_THRESHOLD_MONTHLY (default 0.75)
- SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE (auto-detected from GitHub Actions trigger; override for local debug)
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Final

from tests.agentic_evals.sales_agent.ci_gate._schema import CadenceConfig

# D1-D4 cement — 3 cadences declarative (immutable cross-runs)
CADENCE_CONFIGS: Final[dict[str, CadenceConfig]] = {
    "pr": CadenceConfig(
        cadence="pr",
        threshold_pass_k_rate=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR", "0.65")),
        threshold_bloom_stage=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR", "0.65")),
        goldens_scope="smoke_5",
        k_trials_uniform=1,
        budget_warm_usd=Decimal("30.00"),
        budget_cold_usd=Decimal("80.00"),
        mode="block",
        wall_clock_max_seconds=300,
    ),
    "nightly": CadenceConfig(
        cadence="nightly",
        threshold_pass_k_rate=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_NIGHTLY", "0.70")),
        threshold_bloom_stage=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_NIGHTLY", "0.70")),
        goldens_scope="full_20_30",
        k_trials_uniform=None,                              # heterogeneous via Story C trial_policy_by_persona_kind
        budget_warm_usd=Decimal("150.00"),
        budget_cold_usd=Decimal("500.00"),
        mode="block",
        wall_clock_max_seconds=1800,
    ),
    "monthly": CadenceConfig(
        cadence="monthly",
        threshold_pass_k_rate=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_MONTHLY", "0.75")),
        threshold_bloom_stage=float(os.getenv("SALES_AGENT_VOICE_FIDELITY_THRESHOLD_MONTHLY", "0.75")),
        goldens_scope="full_plus_adversarial",
        k_trials_uniform=None,
        budget_warm_usd=Decimal("200.00"),
        budget_cold_usd=Decimal("700.00"),
        mode="warning",                                      # D4 cement: monthly = Chris semestral review
        wall_clock_max_seconds=3600,
    ),
}

# D15 cement — 5 smoke goldens (1 per tenant × happy persona only)
PR_SMOKE_GOLDEN_IDS: Final[tuple[str, ...]] = (
    "tenant_coach_lat/happy/close_typical_v1",
    "tenant_medicina_estetica/happy/consult_typical_v1",
    "tenant_clinica_dental/happy/invisalign_consult_v1",
    "tenant_agencia_growth_video/happy/intake_typical_v1",
    "tenant_agencia_automatizacion_ia/happy/audit_typical_v1",
)


def get_cadence_config(cadence: str) -> CadenceConfig:
    """Resolve cadence config by name. Raises KeyError if unknown."""
    if cadence not in CADENCE_CONFIGS:
        raise KeyError(f"Unknown cadence {cadence!r}. Valid: {sorted(CADENCE_CONFIGS.keys())}")
    return CADENCE_CONFIGS[cadence]
```

### §3.5 inputs hasher — `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/inputs_hasher.py`

D9 cement — sha256 deterministic; pattern reused from Story F but different inputs (composite of cross-story artifacts).

```python
"""CI gate inputs hasher (Story G D9 cement — tamper detection).

Composition order — ANY change breaks idempotency cement.
sha256 of canonicalized JSON (sort_keys=True, ensure_ascii=False, default=str).

Different inputs from Story F inputs_hasher (which composes per-cell grade_rows + trace_events + golden_yaml).
This composes per-gate-run cross-artifact hashes:
- pass_k_report.json (Story F output — full report content)
- budget_summary.json (Story H output — full state content)
- golden_set_hash (sha256 of all goldens YAML in cadence scope, sorted)
- judge_set_hash (sha256 of judge models + weights + temperatures from Story E config)
- rubric_set_hash (sha256 of rubric MDs + version + threshold from docs/specs/rubrics/)
- cadence (str literal)
- commit_sha (40-char GitHub SHA)

Cache key: composite of (commit_sha, golden_set_hash, judge_set_hash, rubric_set_hash, cadence) — D6 cement.
Tamper detection: re-compute inputs_hash + compare vs cached `eval_gate_verdict.inputs_hash` row.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def compute_gate_inputs_hash(
    *,
    pass_k_report: dict[str, Any],
    budget_summary: dict[str, Any],
    golden_set_hash: str,
    judge_set_hash: str,
    rubric_set_hash: str,
    cadence: str,
    commit_sha: str,
) -> str:
    """Compute sha256 hex hash of (pass_k_report + budget_summary + 3 set hashes + cadence + commit_sha).

    Stable across runs given identical inputs. Re-computing on cached row + comparing
    detects manual DB tamper (Scenario 4 cache-poisoning defense).

    Returns: 64-char lowercase hex.
    """
    payload = {
        "pass_k_report": pass_k_report,
        "budget_summary": budget_summary,
        "golden_set_hash": golden_set_hash,
        "judge_set_hash": judge_set_hash,
        "rubric_set_hash": rubric_set_hash,
        "cadence": cadence,
        "commit_sha": commit_sha,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_golden_set_hash(goldens_dir: Path, scope_filter: tuple[str, ...] | None = None) -> str:
    """Compute sha256 hex hash of all goldens YAML in cadence scope.

    Args:
        goldens_dir: backend/tests/agentic_evals/sales_agent/goldens/
        scope_filter: tuple of golden_ids if PR cadence smoke subset (5 goldens);
                      None = full scope (all YAMLs walked).

    Returns: 64-char lowercase hex.
    """
    payload: dict[str, str] = {}
    for yaml_path in sorted(goldens_dir.rglob("*.yaml")):
        relative = yaml_path.relative_to(goldens_dir).as_posix().removesuffix(".yaml")
        if scope_filter is not None and relative not in scope_filter:
            continue
        payload[relative] = yaml_path.read_text(encoding="utf-8")
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_judge_set_hash(judge_config: dict[str, Any]) -> str:
    """Compute sha256 hex hash of judge models + weights + temperatures (Story E config snapshot).

    Args:
        judge_config: dict of judge_id → {model, weight, temperature, ...} from Story E judge_registry.

    Returns: 64-char lowercase hex.
    """
    canonical = json.dumps(judge_config, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_rubric_set_hash(rubrics_dir: Path) -> str:
    """Compute sha256 hex hash of all rubric MDs + version + threshold (docs/specs/rubrics/*.md).

    Args:
        rubrics_dir: docs/specs/rubrics/

    Returns: 64-char lowercase hex.
    """
    payload: dict[str, str] = {}
    for md_path in sorted(rubrics_dir.glob("*.md")):
        payload[md_path.name] = md_path.read_text(encoding="utf-8")
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### §3.6 Gate orchestrator — `backend/tests/agentic_evals/sales_agent/ci_gate/orchestrator.py`

```python
"""CI gate orchestrator (Story G D6+D7+D8+D9 cement — read-only orchestration).

Orchestrates Stories B (run_simulation) + E (grading) + F (compute_pass_k_for_run +
--validate-strict) + H (budget tracking) → emits GateVerdict per (commit_sha × cadence).

Read-only invariant cement (Story B H7 + Story F D6 cement): zero NEW LLM calls beyond
Stories B/E orchestrated via subprocess. Cero writes to llm_call tables. Arch fitness gate
`test_aggregator_no_llm_calls.py` (Story F NEW) extends to scan ci_gate/ paths.

Cache cement D6: re-runs same (commit_sha + golden_set_hash + judge_set_hash + rubric_set_hash + cadence)
short-circuit via cache lookup → cache_hit=True returned without re-running.

Idempotency cement: re-run with same inputs → same EvalGateVerdict row + same JSON output
+ same Markdown comment. UPSERT on PK (commit_sha, cadence) — comment replacement on re-run (D7 cement).
"""

from __future__ import annotations

import json
import os
import subprocess
import structlog
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_gate_verdict import (
    EvalGateVerdictModel,
)
from src.shared.domain.datetime_utils import utc_now
from tests.agentic_evals.sales_agent.ci_gate._internal.cadence_config import (
    CADENCE_CONFIGS,
    PR_SMOKE_GOLDEN_IDS,
    get_cadence_config,
)
from tests.agentic_evals.sales_agent.ci_gate._internal.inputs_hasher import (
    compute_gate_inputs_hash,
    compute_golden_set_hash,
    compute_judge_set_hash,
    compute_rubric_set_hash,
)
from tests.agentic_evals.sales_agent.ci_gate._schema import (
    FailingGoldenDetail,
    GateVerdict,
)
from tests.agentic_evals.sales_agent.ci_gate.comment_generator import (
    generate_pr_comment,
)

logger = structlog.get_logger()


class GateValidationError(Exception):
    """Raised when --validate-strict re-compute detects tamper (D9 cement)."""


async def compute_gate_verdict(
    session: AsyncSession,
    *,
    cadence: str,
    commit_sha: str,
    pr_number: int | None = None,
    output_dir: Path,
    artifacts_root: Path = Path("_artifacts/eval_runs"),
) -> GateVerdict:
    """Compute CI gate verdict for a given cadence + commit_sha.

    Orchestrates:
    1. Resolve cadence config (threshold + scope + budget + mode + wall-clock)
    2. Compute golden_set_hash + judge_set_hash + rubric_set_hash
    3. Cache lookup (commit_sha + 3 set hashes + cadence) — short-circuit if hit
    4. Generate run_id (UUID) + create artifact dir
    5. Invoke Story B+E+F+H orchestrated subprocess (run_simulation × goldens × K trials → grade → pass_k → budget)
    6. Read pass_k_report.json (Story F output) + budget_summary.json (Story H output)
    7. Compute inputs_hash from full payload
    8. Determine verdict (pass / fail / aborted_budget / warning_only)
    9. Generate failing_goldens FailingGoldenDetail list (cited from Story F flaky_evidence)
    10. Generate Markdown PR comment via comment_generator
    11. UPSERT eval_gate_verdict row (PK commit_sha + cadence)
    12. Write gate_verdict.json artifact
    13. Return GateVerdict

    Args:
        session: AsyncSession from src.core.database.
        cadence: 'pr' | 'nightly' | 'monthly' (resolves to CADENCE_CONFIGS).
        commit_sha: GitHub SHA (40-char or 7-char short).
        pr_number: GitHub PR number (null for nightly/monthly).
        output_dir: artifact output directory (typically _artifacts/eval_runs/{run_id}/).
        artifacts_root: root for cross-run artifact discovery.

    Returns:
        GateVerdict — populated with verdict + metadata + Markdown comment.

    Raises:
        GateValidationError: When Story F --validate-strict re-compute detects tamper (D9 defense).
        KeyError: When cadence not in CADENCE_CONFIGS.
    """
    config = get_cadence_config(cadence)
    started_at = utc_now()

    # Step 2: Compute set hashes (cache key components)
    goldens_dir = Path("backend/tests/agentic_evals/sales_agent/goldens")
    rubrics_dir = Path("docs/specs/rubrics")
    scope_filter = PR_SMOKE_GOLDEN_IDS if cadence == "pr" else None
    golden_set_hash = compute_golden_set_hash(goldens_dir, scope_filter=scope_filter)
    judge_config = _load_judge_config()                                              # from Story E judge_registry — read-only
    judge_set_hash = compute_judge_set_hash(judge_config)
    rubric_set_hash = compute_rubric_set_hash(rubrics_dir)

    # Step 3: Cache lookup (D6 cement — composite key)
    cached = await _cache_lookup(
        session=session,
        commit_sha=commit_sha,
        cadence=cadence,
        golden_set_hash=golden_set_hash,
        judge_set_hash=judge_set_hash,
        rubric_set_hash=rubric_set_hash,
    )
    if cached is not None:
        logger.info(
            "ci_gate.cache_hit",
            commit_sha=commit_sha, cadence=cadence,
            golden_set_hash=golden_set_hash[:16] + "...",
        )
        return cached

    # Step 4: Generate run_id + ensure dir
    run_id = str(uuid4())
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 5: Invoke Story B+E+F+H orchestrated subprocess
    # NOTE: cmd composition delegates to run_eval_gate.py CLI — orchestrator is library-level
    # but production invocation is via CLI; this function exposes library API for tests.
    pass_k_report = await _invoke_pass_k_pipeline(
        cadence=cadence,
        run_id=run_id,
        config=config,
        output_dir=output_dir,
    )
    budget_summary = await _read_budget_summary(output_dir / "budget_summary.json")

    # Step 6: Determine verdict (D8 cement — exit code semantics)
    if budget_summary.get("aborted", False):
        verdict_str: str = "aborted_budget"
        pass_k_rate_global: float | None = None
        bloom_stage_min_score: float | None = None
        bloom_stage_failing: list[str] = []
        budget_aborted = True
        budget_abort_bucket = budget_summary.get("abort_bucket")
    else:
        pass_k_rate_global = pass_k_report["pass_k_rate_global"]
        per_stage = pass_k_report["pass_k_rate_per_stage"]
        bloom_stage_min_score = min(per_stage.values()) if per_stage else None
        bloom_stage_failing = [
            stage for stage, rate in per_stage.items()
            if rate < config.threshold_bloom_stage
        ]
        budget_aborted = False
        budget_abort_bucket = None
        if pass_k_rate_global >= config.threshold_pass_k_rate and not bloom_stage_failing:
            verdict_str = "pass"
        elif config.mode == "warning":
            verdict_str = "warning_only"
        else:
            verdict_str = "fail"

    # Step 7: Compute inputs_hash (D9 tamper detection)
    inputs_hash = compute_gate_inputs_hash(
        pass_k_report=pass_k_report,
        budget_summary=budget_summary,
        golden_set_hash=golden_set_hash,
        judge_set_hash=judge_set_hash,
        rubric_set_hash=rubric_set_hash,
        cadence=cadence,
        commit_sha=commit_sha,
    )

    # Step 8: Build failing_goldens list (cite Story F flaky_evidence verbatim)
    failing_goldens = _build_failing_goldens(pass_k_report, cadence)

    # Step 9: Read judge_unconverged_rate from grader cascade (Story E warning signal)
    judge_unconverged_rate = pass_k_report.get("judge_unconverged_rate")

    # Step 10: Generate PR comment Markdown (Spanish neutro user-facing)
    pr_comment_md = generate_pr_comment(
        verdict=verdict_str,
        cadence=cadence,
        pass_k_rate_global=pass_k_rate_global,
        threshold_applied=config.threshold_pass_k_rate,
        bloom_stage_min_score=bloom_stage_min_score,
        bloom_stage_failing=bloom_stage_failing,
        budget_aborted=budget_aborted,
        budget_abort_bucket=budget_abort_bucket,
        judge_unconverged_rate=judge_unconverged_rate,
        failing_goldens=failing_goldens,
        budget_summary=budget_summary,
        run_id=run_id,
    )

    completed_at = utc_now()

    verdict = GateVerdict(
        run_id=run_id,
        commit_sha=commit_sha,
        pr_number=pr_number,
        cadence=cadence,
        verdict=verdict_str,
        pass_k_rate_global=pass_k_rate_global,
        threshold_applied=config.threshold_pass_k_rate,
        bloom_stage_min_score=bloom_stage_min_score,
        bloom_stage_failing=bloom_stage_failing,
        budget_aborted=budget_aborted,
        budget_abort_bucket=budget_abort_bucket,
        judge_unconverged_rate=judge_unconverged_rate,
        failing_goldens=failing_goldens,
        inputs_hash=inputs_hash,
        golden_set_hash=golden_set_hash,
        judge_set_hash=judge_set_hash,
        rubric_set_hash=rubric_set_hash,
        cache_hit=False,
        pr_comment_md=pr_comment_md,
        started_at=started_at,
        completed_at=completed_at,
        cost_usd_total=Decimal(str(pass_k_report.get("cost_usd_total", "0"))),
        latency_ms_total=int((completed_at - started_at).total_seconds() * 1000),
    )

    # Step 11: UPSERT row + write artifact + emit structlog
    await _upsert_verdict(session, verdict)
    _write_artifact(verdict, output_dir / "gate_verdict.json")
    logger.info(
        "ci_gate.verdict_emitted",
        run_id=run_id, commit_sha=commit_sha, cadence=cadence,
        verdict=verdict_str, pass_k_rate_global=pass_k_rate_global,
        cache_hit=False,
    )
    return verdict
```

> Helpers `_load_judge_config`, `_cache_lookup`, `_invoke_pass_k_pipeline`, `_read_budget_summary`, `_build_failing_goldens`, `_upsert_verdict`, `_write_artifact` — implementation detail per builder. Static analysis arch fitness gate (Story F NEW `test_aggregator_no_llm_calls.py` extended to cover ci_gate/) ensures no `litellm`/`anthropic`/`openai` imports.

### §3.7 Comment generator — `backend/tests/agentic_evals/sales_agent/ci_gate/comment_generator.py`

D7+D17 cement — Markdown PR comment Spanish neutro user-facing. Idempotent replace on re-run (NOT append).

```python
"""CI gate PR comment generator (Story G D7 + D17 cement — Markdown rich attribution).

Templates:
- PASS: green checkmark + metrics table + cadence label + run_id link
- FAIL: red X + metrics table + root cause Bloom stage + reproduce cmd + calibration ref
- ABORTED_BUDGET: yellow warning + cost-bucket abort context + partial results + action required
- WARNING_ONLY: yellow info + same as FAIL but mode=warning (Chris semestral review)

Spanish neutro LATAM (sin voseo) — `.claude/rules/spanish-text.md`. Workflow YAML keys English (technical layer).

Idempotent on re-run: PR comment replacement uses GitHub API edit (NOT new comment) via
actions/github-script@v7 in workflow YAML. comment_generator.py emits Markdown verbatim;
workflow handles editing existing comment by ID match.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tests.agentic_evals.sales_agent.ci_gate._schema import FailingGoldenDetail


_TEMPLATE_PASS = """\
✅ Voice Fidelity Gate ({cadence_label} cadence) — PASS

| Métrica | Valor | Umbral |
|---|---|---|
| pass_k_rate_global | {pass_k_rate_global:.2f} | ≥ {threshold_applied:.2f} ✅ |
| bloom_stage_min | {bloom_stage_min_score:.2f} ({stage_name}) | ≥ {threshold_applied:.2f} ✅ |
| budget_total_usd | ${cost_usd_total:.2f} | ≤ ${budget_cap:.2f} cold cap ✅ |
| judge_unconverged_rate | {judge_unconverged_pct:.1f}% | ≤ 5.0% ✅ |

📊 [Reporte completo](_artifacts/eval_runs/{run_id}/) · 🔄 Cadencia: {cadence} ({scope_label})
"""

_TEMPLATE_FAIL = """\
❌ Voice Fidelity Gate ({cadence_label} cadence) — FAIL

| Métrica | Valor | Umbral |
|---|---|---|
| pass_k_rate_global | {pass_k_rate_global:.2f} | ≥ {threshold_applied:.2f} ❌ |
| bloom_stage_failing | {failing_stages_str} | ≥ {threshold_applied:.2f} ❌ |
| failing_goldens | {n_failing}/{n_total} | — |

### Root cause

{failing_goldens_section}

### Reproducir local

```bash
cd backend
.venv/bin/python scripts/run_eval_gate.py --cadence {cadence} --golden {first_golden_id} --debug
```

### Referencia de calibración

Ver `backend/tests/agentic_evals/sales_agent/grader/calibration/voice_fidelity_calibration.md` (Story E) para baseline esperado.
"""

_TEMPLATE_ABORTED = """\
⚠️ Voice Fidelity Gate ({cadence_label} cadence) — ABORTED (budget cap exceeded)

Cost-bucket abort triggered:
- Bucket: {abort_bucket}
- Estado: ${current_usd:.2f} / ${cap_usd:.2f} (excedido)
- Aborted at: simulation_id={abort_sim_id}, turn={abort_turn}, rubric={abort_rubric}

Resultados parciales capturados:
- Sims completadas: {completed_sims}/{total_sims}
- pass_k_rate_partial: {pass_k_rate_partial:.2f} (parcial)

Acción requerida: investiga la disparada de costo (probablemente Round 2 debate chain spike) antes de re-correr.
Ver `_artifacts/eval_runs/{run_id}/budget_summary.json` para atribución completa.
"""

_TEMPLATE_WARNING = """\
⚠️ Voice Fidelity Gate ({cadence_label} cadence) — WARNING (modo informativo)

(Cadencia mensual — modo warning + revisión semestral por Chris. NO bloquea merge.)

| Métrica | Valor | Umbral |
|---|---|---|
| pass_k_rate_global | {pass_k_rate_global:.2f} | ≥ {threshold_applied:.2f} ⚠️ |
| bloom_stage_failing | {failing_stages_str} | ≥ {threshold_applied:.2f} ⚠️ |

{failing_goldens_section}

Esto NO bloquea el merge. Chris revisará trends mensuales en review semestral.
"""

_CADENCE_LABELS: dict[str, str] = {
    "pr": "PR-trigger",
    "nightly": "Nightly",
    "monthly": "Monthly",
}

_SCOPE_LABELS: dict[str, str] = {
    "pr": "5 smoke goldens × K=1",
    "nightly": "20-30 goldens × heterogeneous K",
    "monthly": "full + adversarial × heterogeneous K",
}


def generate_pr_comment(
    *,
    verdict: str,
    cadence: str,
    pass_k_rate_global: float | None,
    threshold_applied: float,
    bloom_stage_min_score: float | None,
    bloom_stage_failing: list[str],
    budget_aborted: bool,
    budget_abort_bucket: str | None,
    judge_unconverged_rate: float | None,
    failing_goldens: list[FailingGoldenDetail],
    budget_summary: dict[str, Any],
    run_id: str,
) -> str:
    """Generate Markdown PR comment per verdict template.

    Returns Spanish neutro user-facing Markdown. Workflow YAML invokes
    actions/github-script@v7 to post/edit comment idempotently.
    """
    cadence_label = _CADENCE_LABELS[cadence]
    scope_label = _SCOPE_LABELS[cadence]

    if verdict == "aborted_budget":
        return _render_aborted(
            cadence_label=cadence_label,
            budget_summary=budget_summary,
            run_id=run_id,
        )

    if verdict == "pass":
        return _render_pass(
            cadence_label=cadence_label,
            cadence=cadence,
            scope_label=scope_label,
            pass_k_rate_global=pass_k_rate_global or 0.0,
            threshold_applied=threshold_applied,
            bloom_stage_min_score=bloom_stage_min_score or 0.0,
            stage_name=_min_stage_name(bloom_stage_failing, bloom_stage_min_score),
            cost_usd_total=Decimal(str(budget_summary.get("total_cost_usd", "0"))),
            budget_cap=Decimal(str(budget_summary.get("total_cap_usd", "0"))),
            judge_unconverged_pct=(judge_unconverged_rate or 0.0) * 100,
            run_id=run_id,
        )

    # fail or warning_only — both render same metrics + root cause
    template = _TEMPLATE_WARNING if verdict == "warning_only" else _TEMPLATE_FAIL
    return _render_fail_or_warning(
        template=template,
        cadence_label=cadence_label,
        cadence=cadence,
        pass_k_rate_global=pass_k_rate_global or 0.0,
        threshold_applied=threshold_applied,
        bloom_stage_failing=bloom_stage_failing,
        failing_goldens=failing_goldens,
    )
```

> Helpers `_render_pass`, `_render_fail_or_warning`, `_render_aborted`, `_min_stage_name`, `_format_failing_goldens_section` — implementation per builder.

### §3.8 CLI script — `backend/scripts/run_eval_gate.py`

Production entry point invoked from `.github/workflows/voice-fidelity-gate.yml`. Wraps orchestrator + handles exit codes + structlog setup.

```python
"""CI gate CLI (Story G D8 cement — exit code semantics + cadence dispatch).

Exit codes (cement D8):
- 0: verdict=pass OR verdict=warning_only (mode=warning never blocks)
- 1: verdict=fail (functional regression — Bloom stage failure / pass_k_rate below threshold)
- 2: verdict=aborted_budget (cost-bucket cascade — distinct CI status from generic fail)

Spanish neutro LATAM stderr messages + English structlog events.

Native invocation:
    cd backend && .venv/bin/python scripts/run_eval_gate.py \\
        --cadence pr --output _artifacts/eval_runs/{run_id}/ \\
        [--commit-sha <sha>] [--pr-number <n>] [--validate-strict]

GitHub Actions invocation: see .github/workflows/voice-fidelity-gate.yml
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import structlog
import sys
from pathlib import Path

from src.core.database import get_async_session
from tests.agentic_evals.sales_agent.ci_gate.orchestrator import (
    GateValidationError,
    compute_gate_verdict,
)


async def _async_main(args: argparse.Namespace) -> int:
    """Async entry — returns exit code per D8 cement."""
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    async with get_async_session() as session:
        try:
            verdict = await compute_gate_verdict(
                session=session,
                cadence=args.cadence,
                commit_sha=args.commit_sha,
                pr_number=args.pr_number,
                output_dir=output_dir,
            )
        except GateValidationError as exc:
            print(f"ERROR validación strict: {exc}", file=sys.stderr)
            return 1
        except KeyError as exc:
            print(f"ERROR cadencia desconocida: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:                                                     # pragma: no cover
            print(f"ERROR inesperado en gate: {exc}", file=sys.stderr)
            return 1

    print(f"Veredicto gate ({verdict.cadence}): {verdict.verdict}")
    print(f"Reporte completo: {output_dir / 'gate_verdict.json'}")

    # D8 cement — exit code semantics
    if verdict.verdict == "aborted_budget":
        return 2
    if verdict.verdict == "fail":
        return 1
    return 0                                                                          # pass + warning_only both green CI


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CI voice fidelity gate (Story G)")
    parser.add_argument("--cadence", required=True, choices=("pr", "nightly", "monthly"))
    parser.add_argument("--output", required=True, type=str, help="Output dir for gate_verdict.json")
    parser.add_argument("--commit-sha", default=os.getenv("GITHUB_SHA", "unknown"))
    parser.add_argument("--pr-number", type=int, default=None)
    parser.add_argument("--validate-strict", action="store_true",
                        help="Re-compute Story F inputs_hash + verify (D9 tamper detection)")
    return parser.parse_args()


def main() -> int:
    structlog.configure(processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ])
    args = _parse_args()
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    sys.exit(main())
```

### §3.9 GitHub Actions workflow — `.github/workflows/voice-fidelity-gate.yml`

D11 cement — required check via branch protection (configured separately by repo admin per checklist post-merge). `[skip ci]` cannot bypass required check per GitHub Actions semantics.

```yaml
name: voice-fidelity-gate

# Story G CI gate — voice fidelity per cadence (PR / nightly / monthly)
# Required check via branch protection (manual repo admin setup post-merge — see checklist in module narrative)

on:
  pull_request:
    paths:
      - 'backend/src/modules/sales_agent/**'
      - 'backend/src/shared/agent_observability/**'
      - 'backend/tests/agentic_evals/sales_agent/**'
      - 'docs/specs/personas/archetype-aware/*.yaml'
      - 'docs/specs/rubrics/*.md'
      - 'backend/src/core/config.py'                          # threshold defaults — anti-default-flip-audit cascade
  schedule:
    - cron: '0 2 * * *'                                        # nightly 02:00 UTC
    - cron: '0 2 1 * *'                                        # monthly 1st of month 02:00 UTC

permissions:
  contents: read
  pull-requests: write                                          # for actions/github-script comment posting

jobs:
  determine-cadence:
    runs-on: ubuntu-latest
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

  voice-fidelity-gate-required:                                 # required check name (branch protection enforces)
    needs: determine-cadence
    runs-on: ubuntu-latest
    timeout-minutes: 75                                          # monthly cadence wall-clock max 60min + buffer
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install backend deps
        working-directory: backend
        run: |
          python -m venv .venv
          .venv/bin/pip install -e ".[dev]"

      - name: Run gate
        env:
          SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE: ${{ needs.determine-cadence.outputs.cadence }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          KIMI_API_KEY: ${{ secrets.KIMI_API_KEY }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          DATABASE_URL: ${{ secrets.EVAL_DATABASE_URL }}
        working-directory: backend
        run: |
          .venv/bin/python scripts/run_eval_gate.py \
            --cadence "$SALES_AGENT_VOICE_FIDELITY_GATE_CADENCE" \
            --output _artifacts/eval_runs/${{ github.run_id }}/ \
            --commit-sha "${{ github.sha }}" \
            $([ "${{ github.event_name }}" = "pull_request" ] && echo "--pr-number ${{ github.event.pull_request.number }}") \
            --validate-strict

      - name: Upload gate verdict artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: gate-verdict-${{ github.run_id }}
          path: backend/_artifacts/eval_runs/${{ github.run_id }}/

      - name: Post or update PR comment
        if: github.event_name == 'pull_request' && always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const verdictPath = `backend/_artifacts/eval_runs/${{ github.run_id }}/gate_verdict.json`;
            if (!fs.existsSync(verdictPath)) {
              core.setFailed('Gate verdict JSON not produced');
              return;
            }
            const verdict = JSON.parse(fs.readFileSync(verdictPath, 'utf-8'));
            const body = verdict.pr_comment_md;
            const marker = '<!-- voice-fidelity-gate-comment -->';
            const fullBody = `${marker}\n${body}`;

            // Idempotent replace: find existing comment by marker, update if exists, create otherwise (D7 cement)
            const comments = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            const existing = comments.data.find(c => c.body && c.body.startsWith(marker));
            if (existing) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existing.id,
                body: fullBody,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: fullBody,
              });
            }
```

> **Branch protection rule** (configured separately in repo settings post-merge by Chris/repo admin): `voice-fidelity-gate-required` is **required check** for `development` and `main` branches → `[skip ci]` cannot bypass. Setup checklist documented in `docs/product/modules/sales-agent.md` post-merge addition (T-6).

### §3.10 NEW arch fitness gate — `backend/tests/architecture/test_gate_threshold_defaults_protected.py`

D10 cement — defense vs threshold-lowering bypass. Pattern reused from Story F `test_bloom_threshold_defaults_protected.py`. Ratchet pattern — allowlist empty, shrink-only.

```python
"""Architecture fitness gate — protect SALES_AGENT_VOICE_FIDELITY_THRESHOLD_<CADENCE> defaults.

D10 cement (Story G spec § Defense Layer 4): PR modifying threshold env var defaults
in cadence_config.py triggers this gate fail. Threshold lowering bypass requires Chris
approval cement via anti-default-flip-audit rule R29 enforcement.

Pattern parity: Story F test_bloom_threshold_defaults_protected.py (env var defaults frozen).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_CADENCE_CONFIG_PATH = Path(
    "backend/tests/agentic_evals/sales_agent/ci_gate/_internal/cadence_config.py"
)

# Cement defaults — modifying requires Chris approval cement (R29)
_EXPECTED_THRESHOLD_DEFAULTS: dict[str, str] = {
    "SALES_AGENT_VOICE_FIDELITY_THRESHOLD_PR": "0.65",
    "SALES_AGENT_VOICE_FIDELITY_THRESHOLD_NIGHTLY": "0.70",
    "SALES_AGENT_VOICE_FIDELITY_THRESHOLD_MONTHLY": "0.75",
}

_EXPECTED_BUDGET_CAPS: dict[str, dict[str, str]] = {
    "pr": {"warm": "30.00", "cold": "80.00"},
    "nightly": {"warm": "150.00", "cold": "500.00"},
    "monthly": {"warm": "200.00", "cold": "700.00"},
}

_EXPECTED_WALL_CLOCK_MAX: dict[str, str] = {
    "pr": "300",
    "nightly": "1800",
    "monthly": "3600",
}


def test_threshold_env_var_defaults_byte_equal() -> None:
    """Cadence config file MUST contain canonical threshold defaults verbatim."""
    src = _CADENCE_CONFIG_PATH.read_text(encoding="utf-8")
    for env_var, default in _EXPECTED_THRESHOLD_DEFAULTS.items():
        # Match: os.getenv("<env_var>", "<default>")
        pattern = rf'os\.getenv\(\s*"{re.escape(env_var)}"\s*,\s*"{re.escape(default)}"\s*\)'
        assert re.search(pattern, src), (
            f"{env_var} default must be {default!r} in cadence_config.py "
            f"(modifying requires Chris approval cement per R29 anti-default-flip-audit). "
            f"Found path: {_CADENCE_CONFIG_PATH}"
        )


def test_budget_caps_per_cadence_byte_equal() -> None:
    """Cadence config file MUST contain canonical budget caps verbatim."""
    src = _CADENCE_CONFIG_PATH.read_text(encoding="utf-8")
    for cadence, caps in _EXPECTED_BUDGET_CAPS.items():
        warm_pattern = rf'budget_warm_usd\s*=\s*Decimal\("{re.escape(caps["warm"])}"\)'
        cold_pattern = rf'budget_cold_usd\s*=\s*Decimal\("{re.escape(caps["cold"])}"\)'
        assert re.search(warm_pattern, src), (
            f"Cadence {cadence} budget_warm_usd MUST be Decimal({caps['warm']!r}) verbatim"
        )
        assert re.search(cold_pattern, src), (
            f"Cadence {cadence} budget_cold_usd MUST be Decimal({caps['cold']!r}) verbatim"
        )


def test_wall_clock_max_per_cadence_byte_equal() -> None:
    """Wall-clock max MUST be canonical per cadence."""
    src = _CADENCE_CONFIG_PATH.read_text(encoding="utf-8")
    for cadence, max_sec in _EXPECTED_WALL_CLOCK_MAX.items():
        pattern = rf'wall_clock_max_seconds\s*=\s*{re.escape(max_sec)}'
        assert re.search(pattern, src), (
            f"Cadence {cadence} wall_clock_max_seconds MUST be {max_sec} verbatim"
        )


def test_pr_smoke_golden_ids_5_count_cement() -> None:
    """PR cadence smoke goldens MUST be exactly 5 (1 per tenant × happy)."""
    src = _CADENCE_CONFIG_PATH.read_text(encoding="utf-8")
    # Count tuple entries — each ends with /happy/<id>_v1
    happy_ids = re.findall(r'"tenant_\w+/happy/\w+_v1"', src)
    assert len(happy_ids) == 5, (
        f"PR_SMOKE_GOLDEN_IDS MUST have exactly 5 entries (D15 cement). Found: {len(happy_ids)}"
    )


def test_three_cadences_only_no_drift() -> None:
    """CADENCE_CONFIGS dict MUST have exactly 3 keys (pr, nightly, monthly).

    Story I extends additively (NOT replace) — when Story I lands, this test
    will be updated to expect 4 keys and add adversarial cadence config.
    """
    src = _CADENCE_CONFIG_PATH.read_text(encoding="utf-8")
    # Match: "pr": CadenceConfig(...) — count cadence keys
    keys = re.findall(r'"(pr|nightly|monthly)":\s*CadenceConfig\(', src)
    assert len(keys) == 3, (
        f"CADENCE_CONFIGS MUST have exactly 3 cadence keys. Found: {sorted(keys)} ({len(keys)})"
    )
```

> **Allowlist empty shrink-only.** Any future cadence add (Story I) extends test expectations + cement bumps in this file (review-required). NO allowlist entries permitted.

## §4 AGENTIC arch (N/A — Story G is read-only orchestrator)

Story G has zero AGENTIC surfaces:
- No LangGraph state machine
- No prompt cache slot architecture
- No deepagents subagents
- No new LLM calls (orchestrates Stories B/E subprocess; Story B owns simulator agent calls; Story E owns judge calls)
- No voice / persona logic

The orchestrator pipeline is **deterministic Python**:
1. Resolve cadence config (declarative dict lookup)
2. Compute hash composites (sha256 deterministic)
3. Cache lookup (SQL select on PK)
4. Subprocess invocation (Stories B+E+F+H pipeline) — owned by upstream stories
5. JSON deserialization (pass_k_report.json + budget_summary.json)
6. Verdict logic (threshold compare + cadence mode application)
7. Markdown templating (Spanish neutro f-string)
8. UPSERT row + write artifact + emit structlog

If Story G ever needs AGENTIC surface (e.g., LLM-summarized PR comment narrative), that becomes a NEW story extending this one. Out of scope for v1.

## §5 Cross-cutting concerns

### Tenant isolation

`eval_gate_verdict` rows tenant-scoped via `failing_goldens[*].tenant_slug` field validated against Story C `_VALID_TENANT_SLUGS` frozenset (5 valid). No PII in verdict payload — synthetic test data only.

### PII sanitization (`@.tessl/RULES.md` pii-sanitisation)

`FailingGoldenDetail.flaky_evidence` strings are cited verbatim from Story F `flaky_evidence` (already sanitized by Story F D-BE-15). Story G consumes already-sanitized strings — no re-sanitization needed. CLI script `print(...)` user-facing strings = Spanish neutro hardcoded templates (no dynamic PII insertion).

### Voice + Spanish neutro LATAM (`.claude/rules/spanish-text.md`)

CLI script user-facing strings + PR comment Markdown = español neutro LATAM **sin voseo** (Glosario voseo→neutro applied verbatim):
- ✅ "Veredicto gate" / "Reporte completo" / "Reproducir local"
- ✅ "Acción requerida: investiga" / "Ver" / "ABORTED (budget cap exceeded)"
- ❌ NO voseo: "Tenés que revisar" → "Tienes que revisar" ✅ / "Mirá esto" → "Mira esto" ✅

Workflow YAML keys + structlog event names + Python identifiers = English (technical layer). Judge prompts (Story E owned) respect tenant voz cement (NO Story G touches).

### Currency + master-data

Cost fields (`cost_usd_total`, `budget_warm_usd`, `budget_cold_usd`) = `Decimal` USD only (eval-only synthetic — no multi-currency tenant data). `created_at` / `started_at` / `completed_at` = `DateTime(timezone=True)` UTC via `utc_now()`. NEVER `datetime.utcnow()`.

### Schema versioning forward-compat (Story B H1 reuse)

`GateVerdict.schema_version: Literal[1] = 1` cement v1. Future bumps register migrator in SCHEMA_MIGRATIONS post-ship. Story I extends `cadence` Literal additively → Literal["pr", "nightly", "monthly", "monthly_adversarial"] (Story I owns) — does NOT bump v1→v2 since Literal forward-compat allows superset.

### Observability writes (mandatory)

- `eval_gate_verdict` row UPSERT per (commit_sha, cadence) — immutable audit trail (D12 cement)
- structlog events: `ci_gate.verdict_emitted`, `ci_gate.cache_hit`, `ci_gate.bypass_attempted` (warning if path filter / threshold tamper detected via R29 cascade)
- GitHub Actions artifact upload: `_artifacts/eval_runs/{run_id}/` directory persisted via `actions/upload-artifact@v4`
- PR comment: posted/updated via `actions/github-script@v7` idempotent (marker comment ID match — D7 cement)

### Determinism

- Same inputs (commit_sha + golden_set_hash + judge_set_hash + rubric_set_hash + cadence + Stories B/E/F/H artifacts) → same `GateVerdict` row + same JSON output + same Markdown comment **byte-equal modulo timestamps** (`run_id`, `created_at`, `started_at`, `completed_at`, `latency_ms_total`)
- Cache key composite invalidation: change to ANY of (commit_sha + 3 set hashes + cadence) → new row created (UPSERT replaces by PK).

### Anti-duplication §0

Pre-merge audit cement: gate consumes Stories B/C/D/E/F/H artifacts — NO mirror grading/runner/persona-loader/budget-guard. Pattern reuse (Story F inputs_hasher → Story G inputs_hasher with different composition) is justified (different inputs = separate function = separate file).

### Native-first dev (`AGENTS.md`)

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy}` (venv 3.12)
- Migration: `docker exec visionarias_brain_dev alembic upgrade head`
- CLI script: `cd backend && .venv/bin/python scripts/run_eval_gate.py --cadence pr --output _artifacts/eval_runs/{run_id}/`
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO

### Parallel safety (`.claude/rules/parallel-safety.md`)

`eval_gate_verdict` table writes serialized via PK (commit_sha, cadence) UPSERT — no race condition between cadences. Multiple GitHub Actions runs same commit_sha + same cadence = idempotent (cache_hit short-circuit). `git add` por nombre exacto (no `git add .`).

## §6 Decisiones cardinales (cement)

> Anchor: spec D1-D15 + arch D-BE-1..D-BE-12 = 27 decisions total mapped to tickets.

### Spec decisions D1-D15 (cement Chris ratificó 2026-05-08T12:00Z)

(Spec § Decisiones cardinales D1-D15 — see 01-spec.md)

### Arch decisions D-BE-1..D-BE-12

| # | Decisión | Razón | Anchor |
|---|---|---|---|
| D-BE-1 | DDL migration `129_add_eval_gate_verdict_table.py` raw SQL idempotent (IF NOT EXISTS pattern) — paridad Alembic 125+127+128 | Backend-migrations rule cement — never `op.create_table()` non-idempotent | `backend-migrations.md` |
| D-BE-2 | PK composite (commit_sha, cadence) — natural-key idempotency; re-runs UPSERT | Cache cement D6 — same commit + same cadence = same row | spec D6 |
| D-BE-3 | failing_goldens JSONB stored verbatim (audit trail) for FailingGoldenDetail list | Audit trail per spec § Defense Layer 5 | spec D12 |
| D-BE-4 | inputs_hash + golden_set_hash + judge_set_hash + rubric_set_hash columns para D9 tamper detection | D9 cement — composite invalidation precision | spec D9 |
| D-BE-5 | pr_comment_md TEXT column persisted (multi-line Markdown) — idempotent comment replacement on re-runs | D7 cement — replace not append | spec D7 |
| D-BE-6 | Pydantic v2 `ConfigDict(extra="forbid", frozen=True)` cement — `class Config` inner FORBIDDEN | Backend-ddd cement — Pydantic v2 modern syntax | `backend-ddd.md` |
| D-BE-7 | `cadence_config.py` declarative 3 cadences — single source of truth + arch fitness gate enforces | D10 cement — defense vs threshold lowering bypass | spec D10 |
| D-BE-8 | `inputs_hasher.py` separate from Story F (different composition: cross-artifact vs per-cell) — pattern reuse, NOT mirror | Anti-duplication §0 row 7 audit — different inputs = separate function | `anti-duplication.md` |
| D-BE-9 | Orchestrator subprocess invocation Stories B+E+F+H — read-only via JSON read + DB select; NEVER mirror logic | Read-only invariant cement Story F D6 | spec D-BE-12 |
| D-BE-10 | `GateVerdict.schema_version: Literal[1] = 1` cement v1 + SCHEMA_MIGRATIONS anchor entry for forward-compat | H1 reuse Story B — bumps register migrator post-ship | Story B H1 |
| D-BE-11 | GitHub Actions workflow `voice-fidelity-gate.yml` permissions minimal (`contents: read`, `pull-requests: write`) — least-privilege cement | Security best practice 2026 (per WebSearch dorny/paths-filter docs) | spec D11 |
| D-BE-12 | PR comment idempotent via marker `<!-- voice-fidelity-gate-comment -->` + `actions/github-script@v7` listComments + updateComment vs createComment | D7 cement — replace not append (reduces PR noise) | spec D7 |

## §7 Output contract for Story I (downstream consumer)

Story I `sales-agent-adversarial-jailbreak-suite` extends Story G `monthly` cadence row additively:
- Adds 4th cadence row `monthly_adversarial` to `CADENCE_CONFIGS` dict (NOT replace existing 3)
- Adds adversarial persona_kind to Story C `trial_policy_by_persona_kind` (already cement: adversarial=3)
- Adds adversarial-only goldens to Story D dataset (`tenant_*/adversarial/*.yaml`)
- Adds `toxicity-control` rubric (NEW MD in `docs/specs/rubrics/`)
- Story I owns: arch test update (`test_three_cadences_only_no_drift` becomes `test_four_cadences_after_story_i`)

Story G v1 contract for Story I:
- `CadenceConfig` Pydantic schema = forward-compat Literal extends (no v2 bump)
- `cadence_config.py` exports `CADENCE_CONFIGS` dict — Story I edits via PR (1 row added)
- `eval_gate_verdict.cadence` column VARCHAR(16) — accommodates new cadence string without DDL change
- `comment_generator.py` _CADENCE_LABELS + _SCOPE_LABELS dicts — Story I edits via PR (additive)

## §8 Architecture risks + mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Stories B+C+D+E+F+H build delays past Story G build trigger (hard blocker) | High (Stories E+F+H refined, all build-pending) | Build cap reached on Story G | T-1 through T-3 + T-6 (DDL + Pydantic + cadence config + arch fitness + capability YAML) can build BEFORE Stories E/F/H build via synthetic fixtures (decouple data dependency). T-4+T-5 (orchestrator + workflow YAML) require real artifacts → BLOCKED on upstream builds. PM/dev-team decides parallelization at build trigger |
| R2 | GitHub Actions secrets misconfigured (ANTHROPIC_API_KEY/OPENAI_API_KEY/KIMI_API_KEY/EVAL_DATABASE_URL) → workflow fails generic | Medium | CI runs broken until secrets land | T-5 deliverable includes secrets setup checklist in module narrative (post-merge by /pm); manual repo admin task before first PR triggers gate |
| R3 | Branch protection rule `voice-fidelity-gate-required` not configured → required check missing → `[skip ci]` could bypass merge | High initially (manual setup checklist) | Bypass possible during rollout window | T-6 deliverable includes setup checklist in module narrative; documented as prerequisite post-deploy. One-time-only Chris setup en GitHub UI per spec D11/Q5 |
| R4 | Wall-clock budget exceeded on monthly cadence (>60min) → CI timeout 75min buffer hits → workflow fails generic | Low (timeout buffer) | Gate run incomplete | Monthly mode=warning (NOT block) — alarm trigger Chris semestral review even on timeout. Nightly cadence runs 30min < 75min timeout safe. PR cadence 5min << 75min |
| R5 | Cache invalidation false negatives (judge_set_hash drift between Story E judge_registry change + cadence_config) | Low | Stale cache hit returns wrong verdict | judge_set_hash composes ALL judge config (model + weight + temperature) — Story E judge_registry change → hash mismatch → cache invalidated automatic. Defense: arch fitness gate `test_judge_set_hash_invalidation` (Story E F-T-9 owned) |
| R6 | Story F `--validate-strict` flag fails on every gate run (false positive) → all PRs blocked | Low (Story F D7 cement deterministic) | All PRs blocked false alarm | Story F `inputs_hasher.py` deterministic test cement (test_inputs_hash_deterministic_across_runs 100x identity). Defense: T-4 integration test invokes Story F validate-strict on synthetic fixtures, asserts pass |
| R7 | PR comment quota exceeded on flapping PRs (re-runs) → GitHub API rate limit | Low (idempotent edit not create) | PR comment update fails | D-BE-12 cement: marker comment ID match + updateComment vs createComment. GitHub API quota per-token = 1000 reqs/hr ample |
| R8 | Story I build adds 4th cadence + breaks `test_three_cadences_only_no_drift` arch test | Expected (Story I owned) | Story G arch test fails post Story I land | Story I owns the test update — arch ratchet pattern = "extend not break". Story I build includes test rename `test_three_cadences_only_no_drift` → `test_four_cadences_after_story_i_extension` |

## §9 Out of scope (anti-creep)

- ❌ Per-tenant gate threshold (single global per cadence — Q5 ratified)
- ❌ Slack/email notifications (PR comment + structlog only — outcome cement)
- ❌ Auto-merge si score muy alto (gate ONLY blocks, never approves)
- ❌ Backfill scoring on historical PRs
- ❌ Gate for other modules (copilot, brand) — sales_agent only
- ❌ Cost gate enforcement (Story H owns — gate consumes signal)
- ❌ Pass^k computation (Story F owns — gate consumes report)
- ❌ Grader implementation (Story E owns — gate orchestrates)
- ❌ Adversarial scope on PR cadence (Story I extends `monthly` only — additive)
- ❌ Mode warning rollout 1-week (outcome v2 cement: direct block, no soft launch)
- ❌ Per-PR custom thresholds (frozen per cadence)
- ❌ Tocar Stories B/C/D/E/F/H schemas (read-only consumer)
- ❌ Modificar Story D goldens (read-only — golden_set_hash snapshot)
- ❌ Tocar `simulator/__init__.py` H9 public API (NO expand needed — gate is downstream consumer)
- ❌ FE component for verdict visualization (Story G BE-only service-story)
- ❌ Streamlit dashboard for verdict trends (separate observability story)
- ❌ Gate auto-retry on transient failures (manual re-run via GitHub Actions UI)
- ❌ Custom GitHub App for branch protection bypass (per WebSearch — workarounds exist but out of scope)
- ❌ LLM-summarized PR comment narrative (deterministic Markdown templates suffice; LLM summary = NEW story)

## §10 Research notes (DATE-AWARE — accessed 2026-05-08)

### GitHub Actions required check + skip-ci semantics
- Source: GitHub Community Discussions + GitHub Docs (accessed 2026-05-08)
- URLs:
  - https://github.com/orgs/community/discussions/13836 (accessed 2026-05-08)
  - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule (accessed 2026-05-08)
  - https://blog.pantsbuild.org/skipping-github-actions-jobs-without-breaking-branch-protection/ (accessed 2026-05-08)
- Key takeaway: `[skip ci]` does NOT bypass required checks per GitHub Actions semantics. Required check stays unfulfilled → merge blocked. Path filters can prevent workflow from triggering, but if configured as required check, the absence of a successful run also blocks merge. **D11 cement validated** by canonical sources.
- Why this pattern: native GitHub semantics, no custom App needed (Chris autonomy mandate avoids extra complexity for 1000+ tenants scale).

### GitHub Actions workflow path filters + cron schedule production patterns
- Source: GitHub Docs + Tech Insider 2026 GitHub Actions tutorial (accessed 2026-05-08)
- URLs:
  - https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions (accessed 2026-05-08)
  - https://tech-insider.org/github-actions-tutorial-cicd-12-steps-2026/ (accessed 2026-05-08)
- Key takeaway: combining `paths` + `branches` filters narrows scope (both must satisfy). Cron syntax POSIX standard with optional IANA timezone string (UTC default). Shortest interval = 5 minutes. **D14 cement validated** + monthly cron `'0 2 1 * *'` = 1st of month 02:00 UTC valid syntax.
- Why this pattern: standard GitHub Actions semantics, no third-party action needed. `actions/github-script@v7` for PR comment editing avoids `gh pr comment` CLI installation overhead.

### Knowledge cutoff disclosure
- Topic researched live on 2026-05-08 via WebSearch — Opus 4.7 cutoff is Jan 2026 (5 months prior). GitHub Actions v7 syntax + branch protection semantics stable since 2024; no breaking changes Jan-May 2026 per searches.

### sha256 + json.dumps deterministic — Python 3.12 stdlib
- Source: Python docs + Story F precedent (already cement Story F §3.6)
- Key takeaway: `hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()` deterministic; collision probability ~10^-77 negligible.
- Why this pattern: Story F precedent proven in PR pipeline; reuse pattern minimizes cognitive load (different composition = same primitive).

### Pydantic v2 ConfigDict frozen + Literal forward-compat
- Source: docs.pydantic.dev/latest (accessed 2026-05-08 via Story F research)
- Key takeaway: `Literal["a", "b"]` allows extension to `Literal["a", "b", "c"]` (superset = forward-compat). schema_version Literal[1] cement v1 + bump v2 register migrator.

## §11 capability YAML + module narrative + downstream regression rule updates required (post-merge by /pm)

Post-merge by /pm (NOT builder) — T-6 ticket flagged.

### Capability YAML extension (`docs/product/capabilities/sales-agent/sales-conversational-engine.yaml`)

Append to existing `eval:` block:

```yaml
eval:
  # ... existing fields preserved ...

  # Story G (sales-agent-voice-fidelity-ci-gate, 2026-05-08) — CI gate per cadence
  ci_gate_workflow_path: ".github/workflows/voice-fidelity-gate.yml"
  ci_gate_table: "eval_gate_verdict"
  ci_gate_cadences:
    - cadence: pr
      threshold: 0.65
      goldens_scope: smoke_5
      mode: block
      wall_clock_max_seconds: 300
    - cadence: nightly
      threshold: 0.70
      goldens_scope: full_20_30
      mode: block
      wall_clock_max_seconds: 1800
    - cadence: monthly
      threshold: 0.75
      goldens_scope: full_plus_adversarial
      mode: warning                            # Chris semestral review
      wall_clock_max_seconds: 3600
  ci_gate_branch_protection_required_check: "voice-fidelity-gate-required"
  ci_gate_required_check_setup_required: true   # manual repo admin one-time setup post-merge
  ci_gate_audit_table_immutable: true            # eval_gate_verdict rows per (commit_sha, cadence)
  ci_gate_story_g_introduced: sales-agent-voice-fidelity-ci-gate
  ci_gate_story_g_merged_at: null                # pending /auditor APPROVED + /pm merge
  ci_gate_test_coverage:
    - "backend/tests/agentic_evals/sales_agent/ci_gate/test_orchestrator.py"
    - "backend/tests/agentic_evals/sales_agent/ci_gate/test_comment_generator.py"
    - "backend/tests/agentic_evals/sales_agent/ci_gate/test_cadence_config.py"
    - "backend/tests/agentic_evals/sales_agent/ci_gate/test_inputs_hasher.py"
    - "backend/tests/scripts/test_run_eval_gate.py"
    - "backend/tests/architecture/test_gate_threshold_defaults_protected.py"
```

### Module narrative addition (`docs/product/modules/sales-agent.md`)

Add 1-2 sentences in eval narrative section + branch protection setup checklist:

```markdown
**CI Gate (Story G — 2026-05-08)**: GitHub Actions workflow `voice-fidelity-gate.yml`
ejecuta gate por cadencia (PR=block 0.65 / nightly=block 0.70 / monthly=warning 0.75).
Required check `voice-fidelity-gate-required` configurado en branch protection rules
(setup manual one-time post-deploy — checklist abajo). PR comments rich attribution
con root cause Bloom stage + reproduce cmd. Audit trail `eval_gate_verdict` table
inmutable per `(commit_sha, cadence)`.

### Branch protection setup checklist (post-deploy one-time by repo admin)

1. GitHub repo Settings → Branches → Add branch protection rule for `development` + `main`
2. Enable "Require status checks to pass before merging"
3. Add `voice-fidelity-gate-required` to required checks list
4. Enable "Require branches to be up to date before merging"
5. (Optional) "Require conversation resolution before merging" — recommended

Without this setup, `[skip ci]` commits could merge without gate check (per spec
Defense Layer 1). One-time only — required check enforced thereafter.
```

### Downstream regression rule entry (`.claude/rules/auditor-downstream-regression.md`)

Append row to tabla SSoT:

```markdown
| `backend/tests/agentic_evals/sales_agent/ci_gate/orchestrator.py` | `backend/tests/agentic_evals/sales_agent/ci_gate/test_orchestrator.py`<br>`backend/tests/agentic_evals/sales_agent/ci_gate/test_comment_generator.py`<br>`backend/tests/scripts/test_run_eval_gate.py`<br>`backend/tests/architecture/test_gate_threshold_defaults_protected.py` | Story G CI gate orchestrator surface — consumed by GitHub Actions workflow `.github/workflows/voice-fidelity-gate.yml` + Story I extends `monthly` cadence row additively |
| `backend/tests/agentic_evals/sales_agent/ci_gate/_internal/cadence_config.py` | `backend/tests/architecture/test_gate_threshold_defaults_protected.py` (5 invariant tests) | Story G cadence config — threshold defaults arch ratchet protect (R29 anti-default-flip-audit cascade) |
| `.github/workflows/voice-fidelity-gate.yml` | `backend/tests/scripts/test_run_eval_gate.py` integration tests + manual smoke verification post-deploy | Story G CI workflow — branch protection required check; modifying requires Chris approval cement |
```

