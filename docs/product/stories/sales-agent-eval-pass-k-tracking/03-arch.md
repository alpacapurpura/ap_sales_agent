---
story_id: sales-agent-eval-pass-k-tracking
arch_role: orchestrator-consolidated-fullstack
arch_version: 1
mode: SINGLE_SHOT_FULLSTACK   # canonical pattern post 2026-05-08 (learnings.md): /architect-orchestrator handles BE+AGENTIC+FE in one pass
                              # Story F = BE-only (read-only aggregator) — AGENTIC N/A, FE N/A
last_modified: 2026-05-08T11:00:00Z
links:
  spec: 01-spec.md                       # po_version=2 ratified Chris 2026-05-08T10:00Z
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  story_a_archive: ../../../archive/2026/stories/eval-foundation-tenant-seed-data/
  story_b_archive: ../../../archive/2026/stories/eval-foundation-simulator-homologation/
  story_b_arch: ../../../archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md
  story_c_archive: ../../../archive/2026/stories/sales-agent-personas-instrumented-runtime/
  story_c_arch: ../../../archive/2026/stories/sales-agent-personas-instrumented-runtime/03-arch.md
  story_d_spec: ../sales-agent-goldens-3-tenants-dataset/01-spec.md
  story_e_arch: ../sales-agent-voice-fidelity-grader-runtime/03-arch.md
  consumers:
    - ../sales-agent-voice-fidelity-ci-gate/           # G — CI gate consume pass_k_report.json
    - ../sales-agent-eval-cost-budget-cap/             # H — budget integrates cost_usd_total
    - ../sales-agent-adversarial-jailbreak-suite/      # I — extends pass^k tracking with adversarial persona_kind (additive)
date_research: 2026-05-08
---

## §0 Resumen

Story F entrega el **pass^K aggregator read-only** bajo `backend/tests/agentic_evals/sales_agent/pass_k/` que consume Story E `MajEvalScore.final_score` rows (`eval_simulator_grade` table) + Story B `eval_simulator_trace_event` (termination_reason, tools_invoked) + Story C `trial_policy_by_persona_kind` constants + Story D goldens YAML (ground truth) → emite `EvalPassKSummary` v1 row per `(run_id × tenant_slug × persona_kind × golden_id)` en NEW table `eval_pass_k_summary` + JSON report `_artifacts/eval_runs/{run_id}/pass_k_report.json` consumido por Story G CI gate.

**Paradigma:** Bloom 4-stage strict all-of-K (Anthropic Bloom paper [research.anthropic.com/bloom](https://www.anthropic.com/research/bloom) accessed 2026-05-08, `Understanding/Ideation/Rollout/Judgment`). Trial pass = todos los 4 stages pass. pass^K = todos los K trials pass (binary). Heterogeneous K per persona_kind cement Story C: `happy=3 / nurture=1 / unqualified=3 / adversarial=3` (additive Story I).

**Read-only invariant cement:** aggregator NO emite LLM calls — solo lee `eval_simulator_grade` + `eval_simulator_trace_event` + Story D YAML. Cero rows NUEVAS en `eval_simulator_llm_call` o `copilot_llm_call` durante aggregation. Arch fitness gate `test_aggregator_no_llm_calls.py` enforce static import scan.

**Cero deuda invariants** (heredados Stories A/B/C/D/E protected):

- `simulator/__init__.py` H9 surface frozen — Story F no toca (consumer downstream — nada que exportar; aggregator API vive en `pass_k/__init__.py` package-local).
- `personality_profiles.system_instruction` SSoT untouched — aggregator no lee voz, solo grader output.
- Cost-bucket separation (Story B H7 cement): aggregator escribe SOLO a `eval_pass_k_summary` (NEW table separate). Cero touch a `eval_simulator_llm_call/grade`, `copilot_llm_call`, `sales_agent_llm_call`.
- `LLM_ROLE_BY_SITE` SSoT — Story F NO agrega rol (no LLM calls).
- Anti-duplication §0 — aggregator CONSUMES Story E `MajEvalScore.final_score` (no recompute), Story B `eval_simulator_trace_event` schema, Story C `trial_policy_by_persona_kind` constants, Story D goldens YAML. NO mirror grading logic, NO mirror simulation runner, NO mirror persona loader.
- R5 schema-mirror exception — DDL migration NEW las maneja `builder-backend` Sonnet (declarative SQL); model en `modules/sales_agent/observability/eval_simulator/persistence/models/eval_pass_k_summary.py` (paridad Story B/E pattern).
- Goldens YAML immutable post-commit (Story D D16 cement) — defense-in-depth via `golden_yaml_hash` snapshot per row + pre-commit hook Section 9 NEW que detecta mutación sin magic comment `# golden-refresh: <reason>`.
- Schema versioning forward-compat (Story B H1 reuse) — `EvalPassKSummary.schema_version: Literal[1] = 1` cement; future bumps register migrator post-ship.
- `inputs_hash` field tamper detection (D7 cement spec) — `--validate-strict` flag re-computes hash, mismatch → `EvalPassKValidationError`.

**Owner choice rationale (TL;DR):** Story F = BE-only service-story `production_code: false` test-infra. R23 explicit allow Sonnet. Aggregator es deterministic read-only Python pipeline (zero LLM, zero LangGraph, zero state machine debate Round 2). Complejidad per ticket atomic ≤ schema mirror (Story B/E precedent). Sonnet OK todos tickets. PM confirma final routing en spawn (ratifica si Chris autonomy mandate cero deuda overrides para tickets críticos como T-7 pre-commit hook Section 9 → Sonnet bastará — pre-commit hook bash + simple sha256 check).

## §1 Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| BE test-infrastructure (DDL idempotent migration `eval_pass_k_summary` + SQLA 2.0 async model R5 schema-mirror + Pydantic v2 types `EvalPassKSummary`/`BloomStageResult`/`TrialResult`/`PassKAggregateReport`/`FlakyGoldenDetail` + aggregator + bloom_scorer + inputs_hasher + CLI script + pre-commit hook Section 9 + arch fitness 3 gates + capability YAML extension + module narrative) | NO (test-infra + R5 schema-mirror exception) | **`builder-backend` Sonnet** (declarative SQL + Pydantic types + simple aggregation pipeline + hash determinism) | **`auditor-backend` Opus C1-C3 + Sonnet tests** | backend-expert, tessl__pytest-api-testing, tessl__fastapi (Pydantic v2 patterns), tessl__graceful-degradation |
| AGENTIC | N/A (read-only aggregator — zero LLM calls) | — | — | — |
| FE | N/A | — | — | — |

> **Owner choice rationale**: Story F service-story `production_code: false`, simple deterministic aggregation pipeline Python (zero LLM/agentic/LangGraph). Per CLAUDE.md cost-routing matrix R23 + `learnings.md` 2026-05-05 R23: agentic tickets `production_code=false` → Sonnet OK. Story F **no es agentic** (no LangGraph state machine, no debate Round 2, no ensemble judges). **Sonnet OK todos los 8 tickets**. Per Chris autonomy mandate cero deuda 1000+ tenants: aggregator es leverage point cross-stories G/H/I, pero lógica = simple SQL queries + dict aggregation + sha256 hash + JSON serialization. Sonnet handles native. Si en build encuentra bloqueo en T-4 bloom_scorer (4-stage logic) o T-7 pre-commit hook Section 9 → escalate /pm para Opus override. PM confirma final routing en spawn.

## §2 Existing systems audit (NO NEW LAYER rule — `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] Self-run greps Path B (CONTEXT-BRIEF.md absent — direct audit prior to design ratification)

### Audit cross-module ejecutado

```bash
# 1. Cross-codebase pass_k + EvalPassK + eval_pass_k + inputs_hash + bloom_scorer — verify NEW genuinely
grep -rn "compute_pass_k\|EvalPassKSummary\|eval_pass_k\|inputs_hash\|bloom_scorer\|class.*PassK\|class.*BloomScorer" \
  backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__
# Result: ZERO BE/test code matches. Spec/00-story.md/checkpoint.md only references in story dir.
# Conclusion: feature genuinely NEW — no parallel layer to subsume.

# 2. Existing aggregator/scorer patterns cross-codebase
grep -rn "class.*Aggregator\b" backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__ | head -10
# Result:
#   src/modules/analytics/application/services/cost_aggregator.py::CostAggregator (analytics ETL aggregate)
#   src/modules/copilot/observability/reporting/aggregator.py::CopilotCostAggregator (copilot billing)
#   src/modules/sales_agent/observability/reporting/aggregator.py::SalesAgentCostAggregator (sales billing)
# Conclusion: existing aggregators son production observability rollups (cost_usd per tenant per day).
#             Story F aggregator es test-infra eval reporting (pass^K binary aggregation per goldens).
#             Paradigmas ortogonales — domain N/A (analytics) vs test-infra eval (Story F). NO duplication.

# 3. Existing hash patterns
grep -rn "hashlib.sha256\|sha256_hex" backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__ | head -5
# Result: shared/utils + Story E grader/_internal/cache.py compute_cache_key — patterns reusable
# Conclusion: Story F inputs_hasher.py reusa `hashlib.sha256(json.dumps(..., sort_keys=True).encode()).hexdigest()`
#             pattern (deterministic). Story E cache.py code referenciable as precedent.

# 4. eval_pass_k_summary table — confirm NEW (no existing migration)
find backend/alembic/versions -name "*pass_k*" -o -name "*eval_pass*" 2>/dev/null
# Result: empty. NEW migration justified.

# 5. Story E grader path — confirm consume read-only
ls backend/tests/agentic_evals/sales_agent/grader/ 2>/dev/null
# Result: not yet built (Story E refined, awaits build). Aggregator references Story E artifacts:
#         - eval_simulator_grade table (Story E §3.1 DDL)
#         - eval_simulator_grade_cache table (Story E §3.1 DDL)
#         - MajEvalScore Pydantic v1 (Story E §3.3 schema cement)
#         - EvalSimulatorGradeModel SQLA model (Story E §3.2 R5 schema-mirror)
# Build order: Story E build precedes Story F build (hard blocker). Aggregator queries via SQL on table.

# 6. Story B sim trace events — confirm consume read-only
grep -n "class EvalSimulatorTraceEventModel" backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/ -r
# Result: at modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py
# Story F aggregator queries termination_reason + tools_invoked from this table (read-only).

# 7. Story D goldens YAML — confirm consume read-only
ls backend/tests/agentic_evals/sales_agent/goldens/ 2>/dev/null
# Result: dir exists pre-Story F (created by Story D when builds). Aggregator reads YAML at compute time
#         + persists golden_yaml_hash snapshot per row.

# 8. SCHEMA_MIGRATIONS registry — confirm Story E entries NOT yet added
grep "register_schema_migration" backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py 2>/dev/null
# Result: 2 entries Story C (ActorProfile, 1, 2) + (CustomerPrompt, 1, 2). Story E adds 0 (MajEvalScore v1 cement).
#         Story F adds placeholder for forward-compat: SCHEMA_MIGRATIONS extends with EvalPassKSummary v1 anchor
#         (no migrator function needed yet — registration sentinel for future bumps).

# 9. Pre-commit hook Section 9 — confirm sections 1-8 exist + 9 is NEW
grep -nE "^# [0-9]+\." scripts/git-hooks/pre-commit | head -10
# Result: Sections 1-8 declared. Section 9 NEW for Story F (golden YAML mutation detection).

# 10. capability YAML extension target
ls docs/product/capabilities/sales-agent/sales-conversational-engine.yaml
# Result: file exists, Story C extended with eval block. Story F appends `pass_k_report_path`,
#         `bloom_thresholds`, `K_trials_per_persona_kind`, `cost_baseline_per_run_usd` fields.
```

### Sistemas existentes encontrados (Stories A/B/C/D/E SSoT — consume READ-ONLY, NOT mirror)

| Sistema | Path canónico | Estado | Decisión Story F |
|---|---|---|---|
| `EvalSimulatorGradeModel` (Story E) | `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` | **planned** (Story E refined) — built before Story F | **READ-ONLY** — aggregator queries `final_score` per `(simulation_id, turn_n, rubric_id)` |
| `MajEvalScore` Pydantic v1 (Story E) | `backend/tests/agentic_evals/sales_agent/grader/result.py` | planned | **READ-ONLY** — schema reference only (no import dependency — aggregator uses SQL not Pydantic deserialization) |
| `eval_simulator_trace_event` (Story B) | `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py` | active | **READ-ONLY** — aggregator queries `termination_reason` + `tools_invoked` per `simulation_id` |
| Story D goldens YAML | `backend/tests/agentic_evals/sales_agent/goldens/{tenant}/{kind}/*.yaml` | planned (Story D refined) — built before Story F | **READ-ONLY** — aggregator reads YAML at compute time, persists `golden_yaml_hash` snapshot per row |
| `trial_policy_by_persona_kind` (Story C) | `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` | active | **READ-ONLY** via `get_max_turns_for_persona_kind` helper + Story C cement (happy=3, nurture=1, unqualified=3, adversarial=3) — aggregator imports policy constants directly |
| `EvalSimulatorObservabilityContext` (Story B) | `backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py` | active | **NO TOUCH** — aggregator emits structlog events ONLY (no DB writes to llm_call/trace_event) |
| `SCHEMA_MIGRATIONS` registry (Story B H1) | `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` | active 2 entries Story C | **EXTEND** — register `EvalPassKSummary` v1 anchor (sentinel for future bumps; no migrator function needed for v1) |
| `_VALID_TENANT_SLUGS` (Story C) | `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` | active frozenset 5 valid | **READ-ONLY** — aggregator validates `tenant_slug` from grade rows against set |
| `CopilotCostAggregator` / `SalesAgentCostAggregator` | `modules/{copilot,sales_agent}/observability/reporting/aggregator.py` | active runtime prod | **NO TOUCH** — different paradigm (production billing rollup vs test-infra pass^K binary aggregation) |
| `simulator/__init__.py` `__all__` 7 names (H9) + Story E expand 7→8 | `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` | active frozen | **NO TOUCH** — Story F aggregator NO se exporta via simulator surface (vive en `pass_k/__init__.py` package separado) |
| Pre-commit hook Section 1-8 | `scripts/git-hooks/pre-commit` | active | **EXTEND** — Section 9 NEW (golden YAML mutation detection) — additive, sections 1-8 untouched |
| Capability YAML | `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` | active | **EXTEND** — append eval block fields (additive, post-merge by /pm) |

### Decisión por sistema — sumario

- **READ-ONLY (consume only)**: `eval_simulator_grade`, `eval_simulator_trace_event`, Story D goldens YAML, `trial_policy_by_persona_kind`, `_VALID_TENANT_SLUGS`. Aggregator queries via async SQLA + YAML loader; NEVER writes back.
- **EXTEND (additive, justified)**: `SCHEMA_MIGRATIONS` registry (1 anchor entry `EvalPassKSummary` v1), pre-commit hook Section 9 (golden YAML mutation), capability YAML eval block.
- **NEW (genuinely justified, last resort — no existing system overlaps ≥80%)**:
  - DDL migration `128_add_eval_pass_k_summary_table.py` (raw SQL idempotent, 1 NEW table + 4 indexes)
  - SQLAlchemy 2.0 async model `eval_pass_k_summary.py` (R5 schema-mirror exception)
  - Pydantic types `_schema.py` (`EvalPassKSummary`, `BloomStageResult`, `TrialResult`, `PassKAggregateReport`, `FlakyGoldenDetail`)
  - `aggregator.py` (`compute_pass_k_for_run` + `--validate-strict` mode)
  - `_internal/bloom_scorer.py` (4-stage scoring per Bloom contract table)
  - `_internal/inputs_hasher.py` (sha256 deterministic + tamper detection)
  - `scripts/compute_pass_k_report.py` CLI
  - 3 NEW arch fitness gates (`test_pass_k_summary_schema_complete.py`, `test_aggregator_no_llm_calls.py`, `test_bloom_threshold_defaults_protected.py`)
  - Pre-commit hook Section 9 (extend hook file with new check + magic comment escape)
- **NO TOUCH**: §3 sales-agent protected surfaces, `simulator/__init__.py` public API, `personality_profiles.system_instruction`, `LLM_ROLE_BY_SITE`, `core/config.py` defaults, `eval_simulator_*` DB schema, Story D goldens YAML content (mutation detected by hook), `simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,...}`, `modules/{copilot,sales_agent}/{domain,application,api}/`, frontend/, client_simulator/.

## §3 BE arch (DDL idempotent + SQLA 2.0 + Pydantic v2 + aggregator pipeline + script + pre-commit hook)

### §3.1 NEW migration `128_add_eval_pass_k_summary_table.py` (raw SQL idempotent)

Pattern parity con Alembic 125 (Story B) + 127 (Story E):

```python
"""Eval pass^K summary table (Story F sales-agent-eval-pass-k-tracking).

Idempotente raw SQL IF NOT EXISTS (regla backend-migrations.md).

Creates 1 new table + 4 indexes for the pass^K read-only aggregator:
  - eval_pass_k_summary : EvalPassKSummary rows per (run_id, tenant_slug, persona_kind, golden_id)

Pattern parity: eval_simulator (Alembic 125) + eval_simulator_grade (Alembic 127). Cost-bucket
invariant H7 — aggregator NO escribe a llm_call tables; solo a este NEW table.

Decision D-BE-1: schema_version column = 1 cement; future bumps via SCHEMA_MIGRATIONS registry (H1 reuse).
Decision D-BE-2: PK composite (run_id, tenant_slug, persona_kind, golden_id) — natural-key idempotency.
Decision D-BE-3: bloom_stages_per_trial JSONB stored verbatim (audit trail) + trial_passed_overall list[bool].
Decision D-BE-4: inputs_hash + golden_yaml_hash columns para D7+D15 tamper detection.

Revision ID: 128_add_eval_pass_k_summary_table
Revises: 127_add_eval_simulator_grade_tables
Create Date: 2026-05-08
"""

from alembic import op

revision = "128_add_eval_pass_k_summary_table"
down_revision = "127_add_eval_simulator_grade_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create eval_pass_k_summary table."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_pass_k_summary (
            schema_version SMALLINT NOT NULL DEFAULT 1,
            run_id UUID NOT NULL,
            tenant_slug VARCHAR(64) NOT NULL,
            persona_kind VARCHAR(32) NOT NULL,
            golden_id VARCHAR(128) NOT NULL,
            actor_profile_id VARCHAR(128) NOT NULL,
            k_trials_required INTEGER NOT NULL,
            k_trials_executed INTEGER NOT NULL,
            bloom_stages_per_trial JSONB NOT NULL,
            trial_passed_overall JSONB NOT NULL,
            pass_k_strict BOOLEAN,
            unconverged BOOLEAN NOT NULL DEFAULT FALSE,
            inputs_hash VARCHAR(64) NOT NULL,
            golden_yaml_hash VARCHAR(64) NOT NULL,
            cost_usd_total NUMERIC(10,6) NOT NULL DEFAULT 0,
            latency_ms_total INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_eval_pass_k_summary PRIMARY KEY (run_id, tenant_slug, persona_kind, golden_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_pass_k_summary_run
        ON eval_pass_k_summary (run_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_pass_k_summary_tenant_persona
        ON eval_pass_k_summary (tenant_slug, persona_kind)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_pass_k_summary_golden
        ON eval_pass_k_summary (golden_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_pass_k_summary_pass_k_strict
        ON eval_pass_k_summary (pass_k_strict) WHERE pass_k_strict IS NOT NULL
    """)


def downgrade() -> None:
    """Drop pass^K aggregator table (eval-only, no production data)."""
    op.execute("DROP TABLE IF EXISTS eval_pass_k_summary CASCADE")
```

**Idempotency test command** (Native WSL):

```bash
cd backend && docker exec visionarias_brain_dev alembic upgrade head
# Re-run twice — both succeed (IF NOT EXISTS preserves):
cd backend && docker exec visionarias_brain_dev alembic upgrade head
# Validator `migration_idempotency` runs both invocations and asserts zero error.
```

### §3.2 SQLAlchemy 2.0 async model (R5 schema-mirror exception)

File NEW: `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_pass_k_summary.py` (paridad Story B/E pattern). R5 exception applies — `builder-backend` MAY touch persistence/models/ for schema mirror from migration. Cero domain/application/api/ touches.

```python
"""SQLAlchemy model for ``eval_pass_k_summary`` (Story F pass^K aggregator).

Mirror of Alembic migration 128. Pydantic ``EvalPassKSummary`` v1 schema cement.

Pattern parity: ``eval_simulator_grade.py`` (Story E). R5 schema-mirror exception
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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class EvalPassKSummaryModel(Base):
    """ORM mapping for ``eval_pass_k_summary``.

    PK composite ``(run_id, tenant_slug, persona_kind, golden_id)`` — one row per goldens cell.
    bloom_stages_per_trial JSONB stores list[dict] verbatim (4 stages × K trials).
    trial_passed_overall JSONB stores list[bool] (length k_trials_executed).
    """

    __tablename__ = "eval_pass_k_summary"

    schema_version = Column(SmallInteger, nullable=False, default=1)
    run_id = Column(UUID(as_uuid=True), nullable=False)
    tenant_slug = Column(String(64), nullable=False)
    persona_kind = Column(String(32), nullable=False)
    golden_id = Column(String(128), nullable=False)
    actor_profile_id = Column(String(128), nullable=False)
    k_trials_required = Column(Integer, nullable=False)
    k_trials_executed = Column(Integer, nullable=False)
    bloom_stages_per_trial = Column(JSONB, nullable=False)
    trial_passed_overall = Column(JSONB, nullable=False)
    pass_k_strict = Column(Boolean, nullable=True)
    unconverged = Column(Boolean, nullable=False, default=False)
    inputs_hash = Column(String(64), nullable=False)
    golden_yaml_hash = Column(String(64), nullable=False)
    cost_usd_total = Column(Numeric(10, 6), nullable=False, default=0)
    latency_ms_total = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "run_id", "tenant_slug", "persona_kind", "golden_id",
            name="pk_eval_pass_k_summary",
        ),
    )
```

> **Async session pattern**: tests use `AsyncSession` from `src.core.database` via Story B `conftest.py` fixture. NEVER `session.query()` (SA 1.x). Insert via `session.add(...)` + `await session.commit()`. Read via `select(EvalPassKSummaryModel).where(...)`.

### §3.3 Pydantic v2 types — `backend/tests/agentic_evals/sales_agent/pass_k/_schema.py`

Cement schema_version=1; bumps via SCHEMA_MIGRATIONS post-ship (Story B H1 reuse).

```python
"""pass^K aggregator Pydantic types (Story F v1 cement).

Schema versioning: ``EvalPassKSummary.schema_version: Literal[1] = 1``. Future bumps via
``SCHEMA_MIGRATIONS`` registry (Story B H1 reuse) — register identity migrator
(EvalPassKSummary, 1, 2) when bumping. Frozen=True per ConfigDict (immutable post-aggregation).

Story F is read-only aggregator — these types model the AGGREGATION OUTPUT only,
NOT the inputs (Story E MajEvalScore + Story B trace events stay queried via SQL).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BloomStageResult(BaseModel):
    """Single Bloom stage result per (trial × stage). 4 stages per trial always populated."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal["understanding", "ideation", "rollout", "judgment"]
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)        # threshold this stage scored against
    evidence: str                                     # human-readable cita (sanitize_payload applied pre-persist)
    contributing_rubrics: list[str]                   # which Story E rubrics fed this stage's score
    contributing_state_checks: list[str]              # which Story B/D state_checks fed (e.g. termination_reason_match, forbidden_tools_check)


class TrialResult(BaseModel):
    """Single trial result per (golden × trial_n). Length = K_trials_executed in summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    trial_n: int = Field(ge=1)                        # 1-indexed
    simulation_id: str                                 # FK Story B (UUID string)
    bloom_stages: list[BloomStageResult]              # length 4 (4 stages always populated per Bloom paper)
    trial_passed_overall: bool                         # = all(stages.passed)
    cost_usd: Decimal
    latency_ms: int = Field(ge=0)


class EvalPassKSummary(BaseModel):
    """pass^K aggregated summary per (run × tenant × persona_kind × golden)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1                    # cement v1 — future bumps register migrator
    run_id: str                                        # FK eval run UUID (string)
    tenant_slug: Literal[
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    ]
    persona_kind: Literal["happy", "nurture", "unqualified", "adversarial"]
    golden_id: str                                     # FK Story D YAML id
    actor_profile_id: str                              # FK Story C YAML id
    k_trials_required: int = Field(ge=1, le=10)        # per Story C trial_policy_by_persona_kind (3|1)
    k_trials_executed: int = Field(ge=0, le=10)        # actual count in DB
    trials: list[TrialResult]                          # length k_trials_executed
    pass_k_strict: bool | None                         # = all(trials.trial_passed_overall) if k_executed >= k_required else null
    unconverged: bool                                  # k_executed < k_required → true
    inputs_hash: str = Field(min_length=64, max_length=64)         # sha256 hex(grade_rows + trace_events + golden_yaml) — D7 tamper detection
    golden_yaml_hash: str = Field(min_length=64, max_length=64)    # sha256 hex(golden YAML at compute time) — D15 mutation snapshot
    cost_usd_total: Decimal = Decimal("0")
    latency_ms_total: int = Field(ge=0)
    created_at: datetime


class FlakyGoldenDetail(BaseModel):
    """Per-golden flaky detail in PassKAggregateReport.flaky_goldens list."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    golden_id: str
    tenant_slug: str
    persona_kind: Literal["happy", "nurture", "unqualified", "adversarial"]
    pass_k_rate_per_stage: dict[Literal["understanding", "ideation", "rollout", "judgment"], float]  # 4-stage pass_rate
    root_cause_stage: Literal["understanding", "ideation", "rollout", "judgment"]                    # min(pass_rate_per_stage)
    flaky_evidence: list[str]                                                                         # cited from BloomStageResult.evidence


class PassKAggregateReport(BaseModel):
    """JSON report exported a `_artifacts/eval_runs/{run_id}/pass_k_report.json`.

    Story G CI gate consumes this. Schema versioned — bumps invalidate downstream consumers safely.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    run_id: str
    total_goldens_tested: int = Field(ge=0)
    pass_k_rate_global: float = Field(ge=0.0, le=1.0)                                                # fraction of goldens cumpliendo strict all-of-K
    pass_k_rate_per_persona_kind: dict[str, float]                                                    # {happy: 0.83, nurture: 1.0, unqualified: 0.67}
    pass_k_rate_per_tenant: dict[str, float]                                                          # {tenant_coach_lat: 0.75, ...}
    pass_k_rate_per_stage: dict[str, float]                                                           # {understanding: 0.95, ideation: 0.75, rollout: 0.85, judgment: 0.90}
    flaky_goldens: list[FlakyGoldenDetail]                                                            # goldens con mixed trial outcomes
    summary_count_passed: int = Field(ge=0)
    summary_count_failed: int = Field(ge=0)
    summary_count_unconverged: int = Field(ge=0)
    cost_usd_total: Decimal = Decimal("0")
    latency_ms_total: int = Field(ge=0)
    generated_at: datetime
```

### §3.4 Aggregator pipeline — `backend/tests/agentic_evals/sales_agent/pass_k/aggregator.py`

```python
"""pass^K aggregator (Story F D6 cement — read-only).

Consumes Story E `MajEvalScore.final_score` rows + Story B `eval_simulator_trace_event`
(termination_reason, tools_invoked) + Story C `trial_policy_by_persona_kind` constants +
Story D goldens YAML → emits `EvalPassKSummary` per (run × tenant × persona_kind × golden).

Read-only invariant cement (D6 + D16 spec): zero LLM calls, zero writes to llm_call tables.
Arch fitness gate `test_aggregator_no_llm_calls.py` enforces via static import scan.

Determinism cement: same inputs → same EvalPassKSummary rows byte-equal modulo timestamps.
Idempotency cement: re-run with same run_id produces same DB rows + same JSON report.
"""

from __future__ import annotations

import structlog
from datetime import datetime
from decimal import Decimal
from typing import Final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_pass_k_summary import (
    EvalPassKSummaryModel,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload
from src.shared.domain.datetime_utils import utc_now
from tests.agentic_evals.sales_agent.pass_k._internal.bloom_scorer import score_4_stages_per_trial
from tests.agentic_evals.sales_agent.pass_k._internal.inputs_hasher import (
    compute_golden_yaml_hash,
    compute_inputs_hash,
)
from tests.agentic_evals.sales_agent.pass_k._schema import (
    EvalPassKSummary,
    TrialResult,
)

logger = structlog.get_logger()

# Story C cement — heterogeneous K per persona_kind (D4)
_TRIAL_POLICY_BY_PERSONA_KIND: Final[dict[str, int]] = {
    "happy": 3,           # production-critical close — strict all-of-3
    "nurture": 1,         # info path — single trial sufficient
    "unqualified": 3,     # qualification accuracy critical — strict all-of-3
    "adversarial": 3,     # Story I extends additively — strict all-of-3
}


async def compute_pass_k_for_run(
    session: AsyncSession,
    run_id: str,
    *,
    validate_strict: bool = False,
) -> list[EvalPassKSummary]:
    """Compute pass^K summary rows for a given eval run.

    Args:
        session: AsyncSession from src.core.database.
        run_id: UUID of the eval run.
        validate_strict: If True, recompute inputs_hash + compare against cached
                         eval_pass_k_summary rows. Mismatch → EvalPassKValidationError.
                         Used by --validate-strict flag (Scenario 4 cache-poisoning defense).

    Returns:
        list[EvalPassKSummary] — one row per (tenant_slug, persona_kind, golden_id) cell.

    Raises:
        EvalPassKValidationError: When validate_strict=True + tamper detected.
    """
    # Step 1: Query Story E grade rows for this run_id (read-only)
    grade_rows = await _query_grade_rows(session, run_id)

    # Step 2: Query Story B trace events for this run_id (read-only)
    trace_events = await _query_trace_events(session, run_id)

    # Step 3: Load Story D goldens YAML (read-only)
    goldens_by_id = _load_goldens_yaml()

    # Step 4: Group grade rows by (tenant_slug, persona_kind, golden_id)
    cells = _group_by_cell(grade_rows, trace_events, goldens_by_id)

    summaries: list[EvalPassKSummary] = []
    for cell_key, cell_data in cells.items():
        tenant_slug, persona_kind, golden_id = cell_key
        k_required = _TRIAL_POLICY_BY_PERSONA_KIND[persona_kind]
        k_executed = len(cell_data["trials"])

        # Step 5: Compute Bloom 4-stage per trial (D2 cement)
        trials: list[TrialResult] = []
        for trial_data in cell_data["trials"]:
            stages = score_4_stages_per_trial(
                trial_grade_rows=trial_data["grade_rows"],
                trial_trace_events=trial_data["trace_events"],
                golden=cell_data["golden"],
            )
            trial_result = TrialResult(
                trial_n=trial_data["trial_n"],
                simulation_id=trial_data["simulation_id"],
                bloom_stages=stages,
                trial_passed_overall=all(s.passed for s in stages),
                cost_usd=trial_data["cost_usd"],
                latency_ms=trial_data["latency_ms"],
            )
            trials.append(trial_result)

        # Step 6: Compute strict all-of-K (D3 cement)
        unconverged = k_executed < k_required
        if unconverged:
            pass_k_strict = None
            logger.warning(
                "pass_k.unconverged",
                run_id=run_id, tenant_slug=tenant_slug, persona_kind=persona_kind,
                golden_id=golden_id, k_required=k_required, k_executed=k_executed,
            )
        else:
            # Use first K trials (deterministic order by trial_n)
            relevant_trials = sorted(trials, key=lambda t: t.trial_n)[:k_required]
            pass_k_strict = all(t.trial_passed_overall for t in relevant_trials)

        # Step 7: Compute hashes (D7 + D15 tamper detection)
        inputs_hash = compute_inputs_hash(
            grade_rows=cell_data["grade_rows_raw"],
            trace_events=cell_data["trace_events_raw"],
            golden_yaml=cell_data["golden_yaml_raw"],
        )
        golden_yaml_hash = compute_golden_yaml_hash(cell_data["golden_yaml_raw"])

        summary = EvalPassKSummary(
            run_id=run_id,
            tenant_slug=tenant_slug,
            persona_kind=persona_kind,
            golden_id=golden_id,
            actor_profile_id=cell_data["actor_profile_id"],
            k_trials_required=k_required,
            k_trials_executed=k_executed,
            trials=trials,
            pass_k_strict=pass_k_strict,
            unconverged=unconverged,
            inputs_hash=inputs_hash,
            golden_yaml_hash=golden_yaml_hash,
            cost_usd_total=sum((t.cost_usd for t in trials), Decimal("0")),
            latency_ms_total=sum(t.latency_ms for t in trials),
            created_at=utc_now(),
        )

        # Step 8 (validate-strict mode): compare against cached row
        if validate_strict:
            await _validate_strict_against_cached(session, summary)

        summaries.append(summary)

    # Step 9: Persist (idempotent — UPSERT on PK)
    if not validate_strict:
        await _persist_summaries(session, summaries)

    return summaries
```

> Helper functions `_query_grade_rows`, `_query_trace_events`, `_load_goldens_yaml`, `_group_by_cell`, `_validate_strict_against_cached`, `_persist_summaries`, plus `EvalPassKValidationError` exception class — implementation detail per builder.

### §3.5 Bloom 4-stage scorer — `backend/tests/agentic_evals/sales_agent/pass_k/_internal/bloom_scorer.py`

Per spec § Bloom contract table. 4 stages: Understanding / Ideation / Rollout / Judgment.

```python
"""Bloom 4-stage scorer (Story F D2 cement — Anthropic Bloom paper mayo 2026).

Per spec § Bloom contract table:
- Understanding: voice-fidelity initial intent comprehension turns 1-3
- Ideation: expected_tools_invoked ⊆ actual + forbidden_tools ∩ actual = ∅ + qualification-accuracy
- Rollout: no-overpromise + no-hallucination + qualification-accuracy execution
- Judgment: termination_reason match + min_distinct_objections_handled (nurture)

Threshold per stage configurable via env var (Story E D13 pattern reused):
- SALES_AGENT_BLOOM_UNDERSTANDING_THRESHOLD (default 0.7)
- SALES_AGENT_BLOOM_IDEATION_THRESHOLD (default 0.7)
- SALES_AGENT_BLOOM_ROLLOUT_THRESHOLD (default 0.7)
- SALES_AGENT_BLOOM_JUDGMENT_THRESHOLD (default 0.7)

No-hallucination override (Story E D13): SALES_AGENT_RUBRIC_NO_HALLUCINATION_THRESHOLD=0.85.
Bloom Rollout uses per-rubric threshold (NOT stage-global) for no-hallucination contributing.
"""

from __future__ import annotations

import os
from typing import Any, Final

from tests.agentic_evals.sales_agent.pass_k._schema import BloomStageResult

# D5 cement — per-stage threshold defaults
_BLOOM_THRESHOLD_DEFAULTS: Final[dict[str, float]] = {
    "understanding": 0.7,
    "ideation": 0.7,
    "rollout": 0.7,
    "judgment": 0.7,
}

# Story E D13 reuse — per-rubric override (no-hallucination stricter)
_NO_HALLUCINATION_THRESHOLD: Final[float] = float(
    os.getenv("SALES_AGENT_RUBRIC_NO_HALLUCINATION_THRESHOLD", "0.85"),
)


def _get_threshold(stage: str) -> float:
    """Resolve stage threshold from env var or default."""
    env_key = f"SALES_AGENT_BLOOM_{stage.upper()}_THRESHOLD"
    return float(os.getenv(env_key, str(_BLOOM_THRESHOLD_DEFAULTS[stage])))


def score_4_stages_per_trial(
    *,
    trial_grade_rows: list[dict[str, Any]],     # Story E grade rows for this trial
    trial_trace_events: list[dict[str, Any]],   # Story B trace events for this trial
    golden: dict[str, Any],                       # Story D YAML ground truth for this golden
) -> list[BloomStageResult]:
    """Score 4 Bloom stages for a single trial. Returns list of 4 BloomStageResult always."""

    persona_kind = golden["persona_kind"]
    expected_termination = golden["expected_termination_reason"]
    expected_tools = set(golden.get("expected_tools_invoked", []))
    forbidden_tools = set(golden.get("forbidden_tools", []))
    expected_min_objections = golden.get("expected_min_distinct_objections_handled", 0)

    # Extract from trace events
    actual_tools = _extract_tools_invoked(trial_trace_events)
    actual_termination = _extract_termination_reason(trial_trace_events)
    actual_objections_handled = _extract_distinct_objections(trial_trace_events)

    # Extract from grade rows (Story E MajEvalScore.final_score)
    voice_fidelity_avg = _avg_rubric_score(trial_grade_rows, rubric_id="voice-fidelity", turns_filter=(1, 3))
    qualification_avg = _avg_rubric_score(trial_grade_rows, rubric_id="qualification-accuracy")
    no_overpromise_avg = _avg_rubric_score(trial_grade_rows, rubric_id="no-overpromise")
    no_hallucination_avg = _avg_rubric_score(trial_grade_rows, rubric_id="no-hallucination")

    stages: list[BloomStageResult] = []

    # Stage 1 — Understanding (turns 1-3 voice fidelity intent comprehension)
    u_threshold = _get_threshold("understanding")
    stages.append(BloomStageResult(
        stage="understanding",
        passed=voice_fidelity_avg >= u_threshold,
        score=voice_fidelity_avg,
        threshold=u_threshold,
        evidence=f"voice-fidelity turns 1-3 avg={voice_fidelity_avg:.3f} (threshold {u_threshold})",
        contributing_rubrics=["voice-fidelity"],
        contributing_state_checks=[],
    ))

    # Stage 2 — Ideation (tools coverage + qualification-accuracy for nurture/unqualified)
    i_threshold = _get_threshold("ideation")
    expected_tools_present = expected_tools.issubset(actual_tools) if expected_tools else True
    forbidden_tools_absent = not (forbidden_tools & actual_tools)
    qual_pass = qualification_avg >= i_threshold if persona_kind in ("nurture", "unqualified") else True
    ideation_passed = expected_tools_present and forbidden_tools_absent and qual_pass
    ideation_evidence_parts = []
    if not expected_tools_present:
        ideation_evidence_parts.append(f"missing expected_tools: {sorted(expected_tools - actual_tools)}")
    if not forbidden_tools_absent:
        ideation_evidence_parts.append(f"forbidden_tools invoked: {sorted(forbidden_tools & actual_tools)}")
    if not qual_pass:
        ideation_evidence_parts.append(f"qualification-accuracy={qualification_avg:.3f} < {i_threshold}")
    if not ideation_evidence_parts:
        ideation_evidence_parts.append("expected_tools subset OK + forbidden_tools absent + qual ≥ threshold")
    stages.append(BloomStageResult(
        stage="ideation",
        passed=ideation_passed,
        score=1.0 if ideation_passed else 0.0,  # binary axis (tools/forbidden) primary
        threshold=i_threshold,
        evidence="; ".join(ideation_evidence_parts),
        contributing_rubrics=["qualification-accuracy"] if persona_kind in ("nurture", "unqualified") else [],
        contributing_state_checks=["expected_tools_invoked_subset", "forbidden_tools_disjoint"],
    ))

    # Stage 3 — Rollout (no-overpromise + no-hallucination + qualification execution)
    r_threshold = _get_threshold("rollout")
    no_overpromise_pass = (no_overpromise_avg >= r_threshold) if persona_kind in ("happy", "nurture") else True
    no_hallucination_pass = no_hallucination_avg >= _NO_HALLUCINATION_THRESHOLD  # stricter override per Story E D13
    qual_exec_pass = qualification_avg >= r_threshold if persona_kind in ("nurture", "unqualified") else True
    rollout_passed = no_overpromise_pass and no_hallucination_pass and qual_exec_pass
    rollout_evidence_parts = []
    if not no_overpromise_pass:
        rollout_evidence_parts.append(f"no-overpromise={no_overpromise_avg:.3f} < {r_threshold}")
    if not no_hallucination_pass:
        rollout_evidence_parts.append(f"no-hallucination={no_hallucination_avg:.3f} < {_NO_HALLUCINATION_THRESHOLD} (stricter override)")
    if not qual_exec_pass:
        rollout_evidence_parts.append(f"qualification-accuracy execution={qualification_avg:.3f} < {r_threshold}")
    if not rollout_evidence_parts:
        rollout_evidence_parts.append("no-overpromise + no-hallucination + qual exec all ≥ threshold")
    stages.append(BloomStageResult(
        stage="rollout",
        passed=rollout_passed,
        score=min(no_overpromise_avg, no_hallucination_avg, qualification_avg) if persona_kind in ("nurture", "unqualified") else min(no_overpromise_avg, no_hallucination_avg),
        threshold=r_threshold,
        evidence="; ".join(rollout_evidence_parts),
        contributing_rubrics=["no-overpromise", "no-hallucination"] + (["qualification-accuracy"] if persona_kind in ("nurture", "unqualified") else []),
        contributing_state_checks=[],
    ))

    # Stage 4 — Judgment (termination match + min objections handled for nurture)
    j_threshold = _get_threshold("judgment")
    termination_match = actual_termination == expected_termination
    objections_pass = (actual_objections_handled >= expected_min_objections) if persona_kind == "nurture" else True
    judgment_passed = termination_match and objections_pass
    judgment_evidence_parts = []
    if not termination_match:
        judgment_evidence_parts.append(f"termination_reason={actual_termination!r} != expected={expected_termination!r}")
    if not objections_pass:
        judgment_evidence_parts.append(f"objections_handled={actual_objections_handled} < expected_min={expected_min_objections}")
    if not judgment_evidence_parts:
        judgment_evidence_parts.append(f"termination match + objections {actual_objections_handled} ≥ {expected_min_objections}")
    stages.append(BloomStageResult(
        stage="judgment",
        passed=judgment_passed,
        score=1.0 if judgment_passed else 0.0,
        threshold=j_threshold,
        evidence="; ".join(judgment_evidence_parts),
        contributing_rubrics=[],
        contributing_state_checks=["termination_reason_match"] + (["min_distinct_objections_handled"] if persona_kind == "nurture" else []),
    ))

    return stages
```

> Helpers `_extract_tools_invoked`, `_extract_termination_reason`, `_extract_distinct_objections`, `_avg_rubric_score` — implementation per builder. Static analysis arch fitness gate `test_aggregator_no_llm_calls.py` ensures no `litellm` / `anthropic` / `openai` imports.

### §3.6 inputs hasher — `backend/tests/agentic_evals/sales_agent/pass_k/_internal/inputs_hasher.py`

D7 cement — sha256 deterministic, stable across runs. Defense vs cache poisoning Scenario 4.

```python
"""Inputs hasher (Story F D7 cement — tamper detection).

Composition order — ANY change breaks idempotency cement.
sha256 of canonicalized JSON (sort_keys=True, ensure_ascii=False, default=str).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_inputs_hash(
    *,
    grade_rows: list[dict[str, Any]],
    trace_events: list[dict[str, Any]],
    golden_yaml: dict[str, Any],
) -> str:
    """Compute sha256 hex hash of (grade_rows + trace_events + golden_yaml).

    Stable across runs given identical inputs. Re-computing on cached row + comparing
    detects manual DB tamper (Scenario 4 cache-poisoning defense).

    Returns: 64-char lowercase hex.
    """
    payload = {
        "grade_rows": grade_rows,
        "trace_events": trace_events,
        "golden_yaml": golden_yaml,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_golden_yaml_hash(golden_yaml: dict[str, Any]) -> str:
    """Compute sha256 hex hash of golden YAML (snapshot for D15 mutation detection).

    Stored in eval_pass_k_summary.golden_yaml_hash. Re-running aggregator with mutated
    YAML produces different hash → detect mutation post-fact.
    """
    canonical = json.dumps(golden_yaml, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### §3.7 CLI script — `backend/scripts/compute_pass_k_report.py`

```python
"""Story F CLI — compute pass^K report from a given run_id.

Usage:
    python backend/scripts/compute_pass_k_report.py \\
        --run-id <uuid> \\
        --output _artifacts/eval_runs/<run_id>/pass_k_report.json \\
        [--validate-strict]

--validate-strict mode: re-computes inputs_hash from raw grade rows + trace events +
goldens YAML, compares against cached eval_pass_k_summary rows, raises on mismatch.

Spanish neutro LATAM CLI strings — error messages user-facing.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from decimal import Decimal
from pathlib import Path

import structlog

from src.core.database import get_async_session_factory
from src.shared.domain.datetime_utils import utc_now
from tests.agentic_evals.sales_agent.pass_k._schema import (
    FlakyGoldenDetail,
    PassKAggregateReport,
)
from tests.agentic_evals.sales_agent.pass_k.aggregator import compute_pass_k_for_run

logger = structlog.get_logger()


def _decimal_serializer(obj: object) -> str:
    """JSON serializer for Decimal + datetime."""
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Compute pass^K report (Story F).")
    parser.add_argument("--run-id", required=True, help="Eval run UUID")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--validate-strict", action="store_true",
                        help="Re-compute hashes + validate against cached rows (tamper detection)")
    args = parser.parse_args()

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            summaries = await compute_pass_k_for_run(
                session=session, run_id=args.run_id, validate_strict=args.validate_strict,
            )
        except Exception as exc:
            logger.error("pass_k.compute_failed", run_id=args.run_id, error=str(exc), exc_info=True)
            print(f"ERROR computando pass^K: {exc}", file=sys.stderr)
            return 1

    # Build aggregate report
    report = _build_aggregate_report(summaries, run_id=args.run_id)

    # Write JSON output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report.model_dump(mode="json"), default=_decimal_serializer, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Reporte pass^K generado: {out_path}")
    print(f"  pass_k_rate_global: {report.pass_k_rate_global:.3f}")
    print(f"  total_goldens: {report.total_goldens_tested}")
    print(f"  passed: {report.summary_count_passed} | failed: {report.summary_count_failed} | unconverged: {report.summary_count_unconverged}")
    print(f"  flaky_goldens: {len(report.flaky_goldens)}")
    return 0


def _build_aggregate_report(summaries: list, run_id: str) -> PassKAggregateReport:
    """Aggregate per-cell summaries into report (D13 cement — flaky_goldens detection)."""
    # ... aggregate by persona_kind / tenant / stage; detect flaky goldens (mixed pass_per_trial NOT all-pass)
    # implementation per builder
    ...


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

### §3.8 Pre-commit hook Section 9 NEW — golden YAML mutation detection

EXTEND existing `scripts/git-hooks/pre-commit` (sections 1-8 active). Section 9 NEW:

```bash
# 9. Golden YAML mutation detection (origen Story F D15 cement)
# ============================================================
# Origen: Story D D16 cement (goldens YAML immutable post-commit). Defense-in-depth
# vs accidental mutation that would break Story F pass^K aggregator's golden_yaml_hash
# tamper detection (D15). Hook computes hash of staged goldens vs HEAD; mismatch
# requires explicit `# golden-refresh: <reason>` magic comment in commit message OR
# `--no-verify-golden-refresh` env override (Chris explicit approval).

GOLDENS_DIR="backend/tests/agentic_evals/sales_agent/goldens"
HOOK_SECTION_9_FAIL=0

if [ -d "${GOLDENS_DIR}" ]; then
    # Find staged goldens YAML files
    staged_goldens=$(git diff --cached --name-only --diff-filter=ACM | grep -E "^${GOLDENS_DIR}/.*\.yaml$" || true)

    if [ -n "${staged_goldens}" ] && [ -z "${NO_VERIFY_GOLDEN_REFRESH:-}" ]; then
        commit_msg_file="${GIT_DIR:-.git}/COMMIT_EDITMSG"
        commit_msg=""
        if [ -f "${commit_msg_file}" ]; then
            commit_msg=$(cat "${commit_msg_file}")
        fi

        # Check if commit message contains magic comment
        if ! echo "${commit_msg}" | grep -qE "^# golden-refresh:" 2>/dev/null; then
            echo ""
            echo "==> Section 9: Golden YAML mutation detected"
            echo ""
            echo "Staged goldens YAML changes:"
            echo "${staged_goldens}" | sed 's/^/  /'
            echo ""
            echo "Per Story D D16 + Story F D15 cement: goldens YAML are IMMUTABLE post-commit."
            echo "Mutation breaks Story F pass^K aggregator's golden_yaml_hash tamper detection."
            echo ""
            echo "If this is intentional (golden refresh cycle), add to commit message:"
            echo "  # golden-refresh: <reason>"
            echo ""
            echo "Or override (Chris explicit approval) with env var:"
            echo "  NO_VERIFY_GOLDEN_REFRESH=1 git commit ..."
            echo ""
            HOOK_SECTION_9_FAIL=1
        else
            echo "==> Section 9: Golden YAML mutation accepted via 'golden-refresh' magic comment"
        fi
    fi
fi

if [ "${HOOK_SECTION_9_FAIL}" -eq 1 ]; then
    exit 1
fi
```

> Tests for Section 9 cover: (1) staged golden + no magic comment → blocked; (2) staged golden + magic comment present → pass; (3) staged golden + `NO_VERIFY_GOLDEN_REFRESH=1` → pass; (4) no staged goldens → no-op. See `backend/tests/scripts/test_pre_commit_hook.py` extension.

### §3.9 Capability YAML extension (post-merge by /pm)

Append to `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` eval block:

```yaml
  story_f_introduced: sales-agent-eval-pass-k-tracking
  story_f_merged_at: null                              # pending /auditor APPROVED + /pm merge
  pass_k_paradigm: bloom_4_stage_strict_all_of_k       # Anthropic Bloom paper mayo 2026
  pass_k_report_path: "_artifacts/eval_runs/{run_id}/pass_k_report.json"
  bloom_thresholds:
    understanding: 0.7                                  # SALES_AGENT_BLOOM_UNDERSTANDING_THRESHOLD
    ideation: 0.7                                       # SALES_AGENT_BLOOM_IDEATION_THRESHOLD
    rollout: 0.7                                        # SALES_AGENT_BLOOM_ROLLOUT_THRESHOLD
    judgment: 0.7                                       # SALES_AGENT_BLOOM_JUDGMENT_THRESHOLD
  k_trials_per_persona_kind:                            # heterogeneous K cement Story C
    happy: 3
    nurture: 1
    unqualified: 3
    adversarial: 3
  cost_baseline_per_run_usd: 0                          # aggregator read-only — zero LLM cost (Story B+E own)
  story_f_test_coverage:
    - "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py"
    - "backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator_validation.py"
    - "backend/tests/scripts/test_compute_pass_k_report.py"
    - "backend/tests/architecture/test_pass_k_summary_schema_complete.py"
    - "backend/tests/architecture/test_aggregator_no_llm_calls.py"
    - "backend/tests/architecture/test_bloom_threshold_defaults_protected.py"
```

### §3.10 Arch fitness gates additions (3 NEW + 1 ratchet extend)

| Test | Surface | Allowlist | Path |
|---|---|---|---|
| `test_pass_k_summary_schema_complete.py` (NEW) | BE non-prod-code | empty (shrink-only) | `backend/tests/architecture/test_pass_k_summary_schema_complete.py` |
| `test_aggregator_no_llm_calls.py` (NEW) | BE non-prod-code | empty (shrink-only) | `backend/tests/architecture/test_aggregator_no_llm_calls.py` |
| `test_bloom_threshold_defaults_protected.py` (NEW) | BE non-prod-code | empty (shrink-only) | `backend/tests/architecture/test_bloom_threshold_defaults_protected.py` |
| `test_schema_migrations_registry_complete.py` (existing Story B) | extend ratchet | empty preserved | adds `EvalPassKSummary` v1 anchor entry verification |

**`test_pass_k_summary_schema_complete.py`** enforces:
- `EvalPassKSummary` Pydantic fields ⊆ DDL columns (column-by-column verification)
- `BloomStageResult.stage` Literal matches DDL JSONB stage values (4 canonical)
- `EvalPassKSummary.persona_kind` Literal matches Story C 4 valid + Story I forward-compat (additive)
- `EvalPassKSummary.tenant_slug` Literal matches Story A 5 valid (frozen + Story I additive)

**`test_aggregator_no_llm_calls.py`** enforces (static import scan):
- `aggregator.py` + `_internal/bloom_scorer.py` + `_internal/inputs_hasher.py` + `scripts/compute_pass_k_report.py` MUST NOT contain `import litellm`, `import anthropic`, `import openai`, `from litellm`, `from anthropic`, `from openai`
- AST parser walks files; `ImportFrom` + `Import` node names checked against forbidden set
- Allowlist empty (shrink-only)

**`test_bloom_threshold_defaults_protected.py`** enforces:
- `_BLOOM_THRESHOLD_DEFAULTS` dict in `bloom_scorer.py` matches cement `{understanding: 0.7, ideation: 0.7, rollout: 0.7, judgment: 0.7}` byte-equal
- 4 env var names match canonical `SALES_AGENT_BLOOM_<STAGE>_THRESHOLD` pattern
- Drift requires explicit edit + commit (intentional cement bump)

## §4 AGENTIC arch — N/A (read-only BE aggregator)

Story F NO toca surfaces agentic. Aggregator es deterministic Python pipeline:
- Cero LangGraph state machine
- Cero LLM calls (judges, simulator, classifier — todos viven en Stories B/C/E)
- Cero subagents deepagents
- Cero prompt cache slots
- Cero stream modes
- Cero MAJ-EVAL debate
- Cero voice fidelity grading

Aggregator consume Stories E/B/C/D rows/YAML via SQL queries + YAML loader. Output = SQL persist + JSON file write. State-of-the-art reference: AWS Strands Evals reliability framework ([aws.amazon.com/strands-evals](https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-for-production-a-practical-guide-to-strands-evals/) accessed 2026-05-08) recomienda repeated trials con variance analysis. Story F adopt strict all-of-K binary como paradigma más conservador (production-confidence semantic — cero failure across K trials per spec D3).

## §5 Cross-cutting concerns

### Tenant isolation
- `eval_pass_k_summary` rows filtered by `tenant_slug` (matches Story A 5 valid Literal). Aggregator queries scoped per `tenant_slug` via WHERE clause. Story G CI gate consume per-tenant aggregate.

### PII handling
- `evidence` strings en `BloomStageResult` (texto cita de violations) — pre-persist run through `sanitize_payload` shared (defense-in-depth, even synthetic data eval). Path: `shared/agent_observability/recording/sanitization.py`.

### Voice cement N/A
- Story F NO toca `personality_profiles.system_instruction`. Aggregator NO lee voz, solo grader output (rubric scores).

### Currency N/A
- `cost_usd_total` Decimal (USD only — Story B/E own LLM cost recording). Aggregator suma costos ya registrados en `eval_simulator_llm_call` (read-only via grade rows aggregation). NO multi-currency.

### Schema versioning forward-compat
- `EvalPassKSummary.schema_version: Literal[1] = 1` cement. Future bumps via SCHEMA_MIGRATIONS registry (Story B H1 reuse). Story F adds anchor entry `EvalPassKSummary v1` (sentinel — no migrator function for v1; future v2 register `(EvalPassKSummary, 1, 2)` migrator function). PassKAggregateReport `schema_version: Literal[1] = 1` cement separate (Story G consumer pinned).

### Observability tags
- Aggregator emits structlog events ONLY:
  - `pass_k.compute_started` (run_id, tenant_count, golden_count)
  - `pass_k.unconverged` (run_id, tenant_slug, persona_kind, golden_id, k_required, k_executed)
  - `pass_k.tamper_detected` (run_id, golden_id, expected_hash, computed_hash) [validate-strict mode]
  - `pass_k.compute_completed` (run_id, summary_count, duration_ms, flaky_count)
- Cero writes a `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `copilot_llm_call`, `sales_agent_llm_call`. Cost-bucket invariant Story B H7 preserved.

### Cost buckets — read-only invariant
- Verified by arch fitness gate `test_aggregator_no_llm_calls.py` (static import scan).
- Verified by integration test `test_aggregator_zero_llm_call_writes` (DB query post-aggregation: zero NEW rows in `eval_simulator_llm_call` con timestamp > aggregator_start).
- Aggregator ÚNICAMENTE escribe a `eval_pass_k_summary`.

### Determinism + idempotency
- Same inputs (grade rows, trace events, golden YAML) → same `EvalPassKSummary` rows byte-equal modulo timestamps (`created_at`).
- Re-run `compute_pass_k_for_run(run_id)` con mismo `run_id` produce mismo report (deterministic — read-only de Story E grades + Story B sims).
- UPSERT on PK `(run_id, tenant_slug, persona_kind, golden_id)` — re-run sin duplicate rows.
- `inputs_hash` deterministic (sha256 sort_keys=True canonical JSON) — re-compute idempotent.

### Spanish neutro LATAM
- JSON report `evidence` strings + CLI tooling messages (print/error) en español neutro LATAM (sin voseo, sin léxico regional). `.claude/rules/spanish-text.md` glosario aplicado.
- Aggregator code (Python identifiers, docstrings, structlog event names) English (technical layer — convención backend).
- Excepción: aggregator pipeline NO emite output user-facing (CLI script SI — bilingual: error messages Spanish, structlog English).

### Native-first
- Toda lint/test/type-check NATIVE WSL — NUNCA Docker:
  - `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/pass_k/ scripts/compute_pass_k_report.py`
  - `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/pass_k/`
  - `cd backend && .venv/bin/mypy --strict tests/agentic_evals/sales_agent/pass_k/`
- CLI script ejecutable native:
  - `cd backend && .venv/bin/python scripts/compute_pass_k_report.py --run-id <uuid> --output <path> [--validate-strict]`

### Anti-duplication §0
- Aggregator CONSUMES Story E `MajEvalScore.final_score` (NO recompute scores). NO mirror grading logic.
- Aggregator CONSUMES Story B `eval_simulator_trace_event` schema (read-only). NO mirror trace event recording.
- Aggregator CONSUMES Story C `trial_policy_by_persona_kind` constants (import). NO mirror policy.
- Aggregator CONSUMES Story D goldens YAML (read-only). NO mirror golden authoring.
- Story B `EvalSimulatorObservabilityContext` NO USED por aggregator (no LLM calls = no callback handler needed).
- Existing aggregators (`CopilotCostAggregator`, `SalesAgentCostAggregator`, `analytics.CostAggregator`) → NO TOUCH (paradigma ortogonal — production billing rollup vs test-infra eval pass^K).

### Goldens YAML immutability defense-in-depth
- Layer 1: pre-commit hook Section 9 NEW (block commits con golden mutation sin magic comment)
- Layer 2: `golden_yaml_hash` field per `EvalPassKSummary` row (snapshot at compute time)
- Layer 3: `--validate-strict` flag re-computes hash + compares vs cached row (tamper detection post-fact)
- Story D D16 cement (immutable post-commit) preserved + amplified.

## §6 Decisiones D-BE-* (1-line each)

| # | Decisión | Razón |
|---|---|---|
| D-BE-1 | DDL idempotent migration `eval_pass_k_summary` raw SQL `IF NOT EXISTS` (paridad Alembic 125+127) | `.claude/rules/backend-migrations.md` cement; parallel session safety |
| D-BE-2 | PK composite `(run_id, tenant_slug, persona_kind, golden_id)` | Natural-key idempotency — UPSERT semantics; downstream Story G filter eficiente |
| D-BE-3 | `bloom_stages_per_trial` JSONB stored verbatim (audit trail) + `trial_passed_overall` JSONB list[bool] | Stage-level signal preserved (D13 flaky root cause); list[bool] permite re-aggregation downstream |
| D-BE-4 | `inputs_hash` + `golden_yaml_hash` columns 64-char sha256 hex | D7 + D15 tamper detection cement |
| D-BE-5 | `pass_k_strict: bool \| None` (NULL when unconverged) | D9 cement spec — null surface + structlog warn; Story G CI gate trata null como RED |
| D-BE-6 | SQLA model bajo `modules/sales_agent/observability/eval_simulator/persistence/models/` (R5 schema-mirror) | Paridad Story B/E; cero touch domain/application/api/ |
| D-BE-7 | Aggregator path `backend/tests/agentic_evals/sales_agent/pass_k/` (NOT `modules/sales_agent/`) | Test infrastructure ONLY — no touch production runtime |
| D-BE-8 | CLI script `backend/scripts/compute_pass_k_report.py` (NOT under `backend/tests/`) | Tooling user-facing — convention `scripts/` for runnable CLI; tests cover CLI via subprocess invocation |
| D-BE-9 | Pre-commit hook Section 9 EXTEND existing file (sections 1-8 untouched) | Additive, byte-equal preservation of 1-8; Story F adds Section 9 only |
| D-BE-10 | `EvalPassKSummary` schema_version Literal[1]=1 cement; SCHEMA_MIGRATIONS registry sentinel entry | Story B H1 reuse; future bumps register migrator |
| D-BE-11 | `PassKAggregateReport` schema_version Literal[1]=1 cement (separate from EvalPassKSummary) | Story G consumer pinned to v1; bump invalidates Story G CI gate consumers safely |
| D-BE-12 | Read-only aggregator — arch fitness gate `test_aggregator_no_llm_calls.py` static import scan | Defense-in-depth — invariant verified pre-merge, not just at runtime |
| D-BE-13 | Per-stage threshold env vars 4× `SALES_AGENT_BLOOM_<stage>_THRESHOLD` default 0.7 + `_BLOOM_THRESHOLD_DEFAULTS` dict cement | Story E D13 pattern reused; arch fitness gate `test_bloom_threshold_defaults_protected.py` enforces |
| D-BE-14 | `compute_inputs_hash` sha256 deterministic (sort_keys=True canonical JSON) | Story F D7 cement; deterministic stable across runs (Python `dict` insertion order ≠ canonical) |
| D-BE-15 | `evidence` strings en BloomStageResult run through `sanitize_payload` pre-persist | Defense-in-depth PII (even synthetic data eval) per `.tessl/.../pii-sanitisation.md` |
| D-BE-16 | Heterogeneous K per persona_kind (Story C cement) — aggregator imports policy constants directly | NO mirror; respect Story C cement (happy=3, nurture=1, unqualified=3, adversarial=3) |
| D-BE-17 | `unconverged: bool` flag when k_executed < k_required + structlog warn | D9 spec cement; partial data marked, NOT silently aggregated |
| D-BE-18 | `flaky_goldens` lista en JSON report con `root_cause_stage` + `flaky_evidence` per golden | D13 spec cement — surface flaky signal pa Chris + dev — root cause Bloom stage actionable |

## §7 Output contract for consumers Stories G/H/I (estable forward)

JSON schema `pass_k_report.json` versioned. Story G consumes specific fields:

```json
{
  "schema_version": 1,
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_goldens_tested": 25,
  "pass_k_rate_global": 0.84,
  "pass_k_rate_per_persona_kind": {"happy": 0.83, "nurture": 1.0, "unqualified": 0.67},
  "pass_k_rate_per_tenant": {"tenant_coach_lat": 0.75, "tenant_medicina_estetica": 0.85, ...},
  "pass_k_rate_per_stage": {"understanding": 0.95, "ideation": 0.75, "rollout": 0.85, "judgment": 0.90},
  "flaky_goldens": [
    {
      "golden_id": "coach_lat_happy_close_typical_v1",
      "tenant_slug": "tenant_coach_lat",
      "persona_kind": "happy",
      "pass_k_rate_per_stage": {"understanding": 1.0, "ideation": 0.67, "rollout": 1.0, "judgment": 1.0},
      "root_cause_stage": "ideation",
      "flaky_evidence": ["trial 2: send_payment_link forbidden tool invoked"]
    }
  ],
  "summary_count_passed": 21,
  "summary_count_failed": 3,
  "summary_count_unconverged": 1,
  "cost_usd_total": "0.000000",
  "latency_ms_total": 1245,
  "generated_at": "2026-05-15T10:30:00+00:00"
}
```

Story G CI gate query examples:
- Global threshold check: `report.pass_k_rate_global >= 0.5` (per spec § Trial policy global default)
- Per-persona threshold: `report.pass_k_rate_per_persona_kind["nurture"] >= 0.7`
- Stage regression detection: `report.pass_k_rate_per_stage["ideation"] < 0.7` → CI red
- Unconverged guard: `report.summary_count_unconverged == 0` (or Chris-approved exception)

Story H cost integration: `report.cost_usd_total` (zero — read-only aggregator) + `EvalPassKSummary.cost_usd_total` per row (sum of trial cost from Story E grade rows = grade.cost_usd_total).

Story I additive extension: `persona_kind="adversarial"` Literal forward-compat (already in Pydantic Literal `["happy", "nurture", "unqualified", "adversarial"]`). Story I builds adversarial goldens + extends pass^K aggregation without schema migration.

## §8 Open architecture risks (severity + mitigation)

| Risk | Severity | Mitigation |
|---|---|---|
| **R1**: `flaky_goldens` detection accuracy edge case — golden con todos K trials FAIL (no mixed) marcado como `flaky` (false positive) | LOW | `flaky_goldens` definition explicit: `0 < trials_passed_count < K` (mixed only). All-fail goldens lista en `summary_count_failed` separate. Spec D13 + builder unit test covers |
| **R2**: `inputs_hash` collision (sha256 hash collision astronomically unlikely but theoretically possible) | NEGLIGIBLE | sha256 collision probability ~10^-77 per pair. Alternative: SHA-512 if Chris paranoid (config option future). |
| **R3**: Pre-commit hook Section 9 false positive — legitimate golden refresh blocked | LOW | Magic comment `# golden-refresh: <reason>` escape + env var `NO_VERIFY_GOLDEN_REFRESH=1` override (Chris explicit approval). Tests cover both escapes. |
| **R4**: SQLA JSONB performance with 75 sims × 4 stages × 3 trials = 900 stage rows → query latency >30s | LOW | `bloom_stages_per_trial` JSONB stored as nested dict (single row per cell, not exploded). Indexes on PK + tenant+persona + golden_id + pass_k_strict partial. 75 sims pequeño escala. Performance test in validators (timeout 30s). |
| **R5**: Story E `MajEvalScore` schema bump (v1→v2) breaks aggregator `_avg_rubric_score` extractor | MEDIUM | Story E SCHEMA_MIGRATIONS registry forward-compat (H1 reuse). Aggregator queries via stable column names (`final_score`, `rubric_id`, `rubric_version`); v2 migration auto-applies. If column renamed → Story E review covers downstream regression rule R3 (auditor-downstream-regression.md tabla SSoT) |
| **R6**: Story D goldens YAML schema drift mid-build (D adds field, F doesn't extract) | LOW | Story D D16 cement (immutable post-commit); Story F reads YAML at compute time + persists `golden_yaml_hash`. Future Story D refresh requires `golden-refresh` magic comment. |
| **R7**: Aggregator stale (Story E build delayed → Story F no inputs to aggregate) | LOW | Build order serialization explicit (Story F build BLOCKED on Stories C+D+E build done — checkpoint cement). Empty `eval_simulator_grade` table → aggregator returns `[]` (warning logged), NO crash. Integration test covers empty-input case. |
| **R8**: `--validate-strict` hash mismatch on legitimate Story E grade re-grading (rubric_version bump) | MEDIUM | Story E rubric_version field included in hash composition. Re-grading bumps rubric_version → new inputs_hash → mismatch flagged + structlog warn. Chris reviews + decides re-aggregation. Builder includes integration test for rubric_version bump scenario. |

## §9 Out of scope (anti-creep guards consolidados)

- ❌ Re-grading rubrics (Story E owns) — aggregator consumes `MajEvalScore.final_score` only
- ❌ Re-running simulations (Story B owns) — aggregator reads existing `SimulationResult` via trace events
- ❌ Adversarial persona_kind tracking implementation (Story I extends additively)
- ❌ Statistical significance testing (chi-square, p-values, Bayesian) — strict all-of-K binary suficiente
- ❌ Probabilistic pass^k = `pass_rate^k` (legacy paradigm 00-story.md superseded D1)
- ❌ Per-tenant or per-golden Bloom threshold tuning UI (env vars only)
- ❌ Auto-flaky-classification ML — `flaky_goldens` lista expone signal, Chris reviews semestralmente
- ❌ CI gate enforcement (Story G owns)
- ❌ Cost cap enforcement (Story H owns — F just exposes `cost_usd_total`)
- ❌ Backfill historical sims (no historical sims exist — synthetic-first paradigm)
- ❌ Tocar `simulator/__init__.py` H9 public API (NO expand — F is downstream consumer, no surface)
- ❌ Tocar `eval_simulator_grade` o `eval_simulator_llm_call` (read-only)
- ❌ Tocar Story D goldens YAML content (read-only — `golden_yaml_hash` snapshot only)
- ❌ Modificar `core/config.py` defaults (no flag flips this story)
- ❌ Re-run aggregator en CI per-PR (cost prohibitive — manual trigger post-eval-run only via CLI)
- ❌ FE component for pass^K visualization — Story F is BE-only service-story
- ❌ Streamlit dashboard for flaky_goldens — separate observability story
- ❌ `simulator/__init__.py` `__all__` expand — aggregator NO se exporta via simulator surface

## §10 Research notes (state-of-the-art mayo 2026)

**Knowledge cutoff disclosure**: Opus 4.7 cutoff Jan 2026. Topics post-Jan 2026 (Bloom 4-stage, AWS Strands evals) researched live via WebSearch on **2026-05-08**.

| Topic | Source URL | Accessed | Library version | Key takeaway | Why this pattern over alternatives |
|---|---|---|---|---|---|
| Anthropic Bloom 4-stage evaluation framework | https://www.anthropic.com/research/bloom + https://alignment.anthropic.com/2025/bloom-auto-evals/ | 2026-05-08 | Open-source Bloom released 2025-12 | 4 stages canonical: Understanding/Ideation/Rollout/Judgment. Each stage scored independently → flaky root cause attribution per stage. Claude Opus 4.1 Spearman 0.86 vs human; Sonnet 4.5 Spearman 0.75 | Story F adopts 4-stage breakdown (D2 cement) for stage-level pass_rate flaky detection (vs single ambiguous score per golden) |
| AWS Strands Evals reliability framework | https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-for-production-a-practical-guide-to-strands-evals/ | 2026-05-08 | strands-agents-evals 0.1+ (open-source GitHub) | Recomienda ≥10 trials per question + variance analysis para reveal reliability gaps. Baseline pass^k canonical pattern in production-confidence semantic | Story F adopts strict all-of-K binary (D3 cement) como variant más conservador — production-critical reliability = zero failure across K. Heterogeneous K (3/1/3/3) cement Story C respects info-path nature of nurture |
| sha256 stability + hashlib deterministic JSON | https://docs.python.org/3.12/library/hashlib.html + https://docs.python.org/3.12/library/json.html#json.dumps | 2026-05-08 | Python 3.12 stdlib | `hashlib.sha256(canonical.encode("utf-8")).hexdigest()` + `json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)` patrón canonical | Patrón reusable Story E grader cache; Story F inputs_hasher.py mirror precedent. SHA-256 collision probability ~10^-77 negligible |
| Pydantic v2 ConfigDict frozen + Literal forward-compat | https://docs.pydantic.dev/latest/concepts/models/ + https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.frozen | 2026-05-08 | Pydantic 2.10+ | `model_config = ConfigDict(extra="forbid", frozen=True)` + `Literal["a", "b"]` forward-compat additive (add Literal value = additive, no migration needed) | Cement Story B/C/E pattern reused — schema_version Literal[1]=1 + future bumps via SCHEMA_MIGRATIONS registry (H1) |
| SQLAlchemy 2.0 async + JSONB + composite PK | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html + https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#sqlalchemy.dialects.postgresql.JSONB | 2026-05-08 | SQLA 2.0.27+ | `select(Model).where(...)` + `session.add(...)` + `await session.commit()`. JSONB stored as Python dict; composite PK via `PrimaryKeyConstraint(*cols, name="pk_...")` | Cement Story B/E pattern reused — R5 schema-mirror exception applies |
| pre-commit hook bash + git diff staged | https://git-scm.com/docs/githooks#_pre_commit + `scripts/git-hooks/pre-commit` precedent | 2026-05-08 | git 2.40+ | Sections 1-8 already implemented; Section 9 additive — `git diff --cached --name-only --diff-filter=ACM | grep -E "^${GOLDENS_DIR}"` + magic comment regex check | Cement R3 + R32 + R33 hook patterns reused (voseo + ruff + R3 SSoT freshness + capability/backlog freshness + checkpoint state validator + PII scan) |

> **Note on Bloom paper claim verification**: Bloom canonical 4-stage framework verified via 2 sources (Anthropic.com/research/bloom + alignment.anthropic.com bloom-auto-evals 2025-12). Spec D1 reframe paradigm cita "Anthropic Bloom paper mayo 2026" — date approximate, framework released **December 2025** per primary sources. Story F arch references actual release date (2025-12). Refinement loop opcional pre-build si Chris quiere precisión.

## §11 Capability YAML + module narrative updates required (post-merge by /pm)

Append to `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` § eval block (per §3.9 above).

Update `docs/product/modules/sales-agent.md` narrative addition (1-2 sentences):

> Post Story F (`sales-agent-eval-pass-k-tracking` merged 2026-05-XX): pass^K aggregator read-only consume Story B/E rows + Story C/D YAML → genera `EvalPassKSummary` per golden cell + JSON report consumido por Story G CI gate. Bloom 4-stage strict all-of-K paradigm (Anthropic Bloom 2025-12 + AWS Strands evals reliability). Heterogeneous K per persona_kind (happy=3 / nurture=1 / unqualified=3 / adversarial=3 cement Story C).

Update `.claude/rules/auditor-downstream-regression.md` § tabla SSoT — append entry:

```markdown
| `backend/tests/agentic_evals/sales_agent/pass_k/aggregator.py` | `backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator.py`<br>`backend/tests/agentic_evals/sales_agent/pass_k/test_aggregator_validation.py`<br>`backend/tests/scripts/test_compute_pass_k_report.py` | Story F pass^K aggregator surface — consumed by Stories G/H/I downstream. Read-only invariant + tamper detection + Bloom 4-stage scoring + heterogeneous K respect. |
| `backend/tests/agentic_evals/sales_agent/pass_k/_internal/bloom_scorer.py` | idem | 4-stage scoring logic — threshold env vars + per-stage evidence |
| `backend/tests/agentic_evals/sales_agent/pass_k/_internal/inputs_hasher.py` | idem + `backend/tests/architecture/test_pass_k_summary_schema_complete.py` | sha256 deterministic — D7 + D15 tamper detection cement |
```

## Changelog

- v1 2026-05-08T11:00Z — `/architect` orchestrator delivered ready package. SINGLE_SHOT_FULLSTACK mode (BE-only — AGENTIC N/A, FE N/A). 18 cardinal decisions D-BE-1..D-BE-18. 8 architecture risks R1-R8 with mitigations. Reference impl ~600 LOC across 8 NEW files + 3 EXTEND files. Build order: Stories C+D+E build done → Story F build → Stories G+H+I parallel.
