---
story_id: sales-agent-eval-cost-budget-cap
arch_role: orchestrator-consolidated-fullstack
arch_version: 1
mode: SINGLE_SHOT_FULLSTACK   # Story H = BE-only (read-only multi-tier cost guard) — AGENTIC N/A, FE N/A
last_modified: 2026-05-08T12:00:00Z
links:
  spec: 01-spec.md                       # po_version=2 ratified Chris 2026-05-08T11:00Z (Q1-Q6 todas opción A)
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  story_b_archive: ../../../archive/2026/stories/eval-foundation-simulator-homologation/
  story_b_arch: ../../../archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md
  story_e_arch: ../sales-agent-voice-fidelity-grader-runtime/03-arch.md
  story_f_arch: ../sales-agent-eval-pass-k-tracking/03-arch.md
  consumers:
    - ../sales-agent-voice-fidelity-ci-gate/           # G — CI gate consume budget_summary.json + abort signal
    - ../sales-agent-adversarial-jailbreak-suite/      # I — extends bucket additively (adversarial)
date_research: 2026-05-08
---

## §0 Resumen

Story H entrega el **eval-run multi-tier cost guard read-only** bajo `backend/tests/agentic_evals/sales_agent/budget/` que consume Story B `eval_simulator_llm_call.cost_usd` (generation bucket) + Story E `eval_simulator_grade.cost_usd_total` (grader bucket) en tiempo real, evalúa pre-flight estimation + periodic sweep 30s post-facto, raises `BudgetCapExceededError` con partial report `_artifacts/eval_runs/{run_id}/budget_summary.json` cuando se supera tier cap, expone abort signal para Story G CI gate consumer + cascade Story F unconverged.

**Multi-tier cap architecture (D1-D2 cement spec):**

1. **Per-trial cap** ($0.10 default) — abort single simulation runaway
2. **Per-grade cap** ($0.20 default) — abort grader Round 2 chain spike
3. **Per-run total cap** ($500 cold cache / $150 warm) — global ceiling full eval suite
4. **Per-bucket cap** (generation $20 / grader cold $400 / warm $130) — bucket-specific runaway

**Pre-flight estimation (D4 cement over-estimate strict):** before LLM call, `estimate_cost_for_call(model, input_tokens, max_output_tokens) → Decimal` computes `input × price + max_output × price` (NOT actual_output — over-estimate intentional, better safe than sorry). Pricing from existing `model_pricing_snapshot` shared table (LiteLLM canonical sync).

**Periodic sweep (D5 cement 30s interval):** asyncio background Task `start_periodic_sweep(run_id, interval_s=30)` queries `compute_remaining_budget(run_id)` cada 30s, detecta direct LLM call bypass post-facto (Scenario 4 adversarial defense-in-depth). Layer 1 enforcement = NEW arch fitness gate `test_eval_llm_calls_use_budget_guard.py` (static analysis import scan); Layer 2 enforcement = runtime sweep.

**Public API surface H9 expand 8→9 (D11 cement):** `simulator/__init__.py` `__all__` adds `check_budget_before_call` (NEW). Re-freeze post Story H ship. Arch fitness `test_simulator_public_api_surface.py` allowlist updated 7→8 (Story E pre-shipped) → 9 post-Story H ship. Build serialization order confirms: Story B(7) → Story E builds + ships(8) → Story H builds + ships(9). PRE-CONDITION: Story E build COMPLETE before Story H build start (hard blocker).

**Cero deuda invariants** (heredados Stories A/B/C/D/E/F protected):

- `simulator/__init__.py` H9 surface — Story H expand puntual 8→9 (`check_budget_before_call`). Re-freeze post-ship.
- `personality_profiles.system_instruction` SSoT untouched — guard NO lee voz, no grader; solo cost rows.
- Cost-bucket separation (Story B H7 cement): guard READS `eval_simulator_llm_call.cost_usd` (generation) + `eval_simulator_grade.cost_usd_total` (grader) ONLY. Cero `copilot_llm_call`, `sales_agent_llm_call`, `campaign_llm_call` reads. Cero writes to ANY llm_call/grade tables (read-only invariant cement D-BE-12).
- `LLM_ROLE_BY_SITE` SSoT — Story H NO agrega rol (no LLM calls — read-only guard).
- Anti-duplication §0 — guard CONSUMES Story B cost rows + Story E grade rows. NO mirror cost recording (Story B H7 owns). NO mirror `BudgetGuard` shared/billing (different paradigm — runtime per-tenant vs eval-suite synthetic; documented §2).
- R5 schema-mirror exception — N/A Story H (NO new DDL — guard is consumer of existing tables Stories B/E).
- Schema versioning forward-compat (Story B H1 reuse) — `BudgetState.schema_version: Literal[1] = 1` cement; SCHEMA_MIGRATIONS registry extends with anchor entry post-Story F precedent.

**Owner choice rationale (TL;DR):** Story H = BE-only service-story `production_code: false` test-infra. R23 explicit allow Sonnet. Guard es deterministic Python pipeline (Pydantic + asyncio Task + SQL sum query + structlog). Cero LLM calls (read-only invariant). Cero LangGraph state machine. Cero debate Round 2. Complejidad por ticket atomic ≤ schema mirror (Story B/E/F precedent). **Sonnet OK todos 6 tickets.** Si en build encuentra bloqueo en T-4 sweep asyncio Task lifecycle o T-5 arch fitness AST scan → escalate /pm para Opus override puntual.

## §1 Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| BE test-infrastructure (Pydantic v2 types `BudgetState`/`BucketState`/`TierState`/`AbortContext`/`BudgetWarning`/`BudgetCapExceededError` + `cost_estimator.py` over-estimate strict + `guard.py` 3 public APIs + `sweep.py` periodic asyncio Task + 3 NEW arch fitness gates + capability YAML extension + module narrative + downstream-regression rule SSoT entry + JSON output `budget_summary.json` v1) | NO (test-infra) | **`builder-backend` Sonnet** (declarative Pydantic + simple guard logic + asyncio Task + AST scan arch fitness) | **`auditor-backend` Opus C1-C3 + Sonnet tests** | backend-expert, tessl__pytest-api-testing, tessl__fastapi (Pydantic v2 patterns), tessl__graceful-degradation |
| AGENTIC | N/A (read-only guard — zero LLM calls) | — | — | — |
| FE | N/A | — | — | — |

> **Owner choice rationale**: Story H service-story `production_code: false`, simple deterministic guard pipeline Python (zero LLM/agentic/LangGraph). Per CLAUDE.md cost-routing matrix R23 + `learnings.md` 2026-05-05 R23: agentic tickets `production_code=false` → Sonnet OK. Story H **no es agentic** (no LangGraph state machine, no debate, no ensemble judges, no cost recording — pure read-only consumer + asyncio sweep). **Sonnet OK todos los 6 tickets**. PM confirma final routing en spawn.

## §2 Existing systems audit (NO NEW LAYER rule — `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] Self-run greps Path B (CONTEXT-BRIEF.md absent — direct audit prior to design ratification)

### Audit cross-module ejecutado

```bash
# 1. Cross-codebase BudgetState + check_budget_before_call + eval_budget_cap — verify NEW genuinely
grep -rn "BudgetState\|check_budget_before_call\|BudgetCapExceededError\|eval_budget_cap\|class.*BudgetState\|compute_remaining_budget" \
  backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__
# Result: ZERO BE/test code matches outside this story dir. Spec/checkpoint references only.
# Conclusion: feature genuinely NEW — no parallel layer to subsume.

# 2. Existing BudgetGuard cross-module — verify scope independence
grep -rn "class.*BudgetGuard\b\|class.*Budget\b" backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__ | head -10
# Result:
#   src/shared/billing/application/budget_guard.py::BudgetGuard       (production runtime per-tenant Others vs SA pool, MV-backed)
#   src/shared/billing/application/exceptions.py::BudgetExceeded      (production exception for HTTP 402 mapping)
#   src/shared/billing/domain/budget_decision.py::BudgetDecision      (production VO — pool / spent_usd / cap_usd / reason)
#   src/shared/billing/application/llm_guards.py::BudgetGuardingLLMService  (production LangChain wrapper)
# Conclusion: existing prod BudgetGuard es runtime per-tenant cost cap (Others vs SA pool, plan-driven, MV-backed,
#             enforced at orchestrator/middleware layer). Story H es eval-suite synthetic cost cap (per-run +
#             bucket separation generation/grader, eval-only, multi-tier). Paradigmas ortogonales:
#               - Scope: per-tenant runtime vs per-run eval-suite
#               - Trigger: pre-LLM-call orchestrator wrapper vs pre-flight + post-facto sweep guard
#               - Source data: mv_daily_llm_cost_per_tenant_v2 vs eval_simulator_llm_call + eval_simulator_grade
#               - Pool semantics: SA reserved 50% / Others vs generation / grader buckets
#             NO duplication.

# 3. Existing cost_estimator cross-module — verify scope independence
grep -rn "estimate_llm_cost\|class.*CostEstimator\b\|cost_estimator" backend/src/ backend/tests/ 2>/dev/null | grep -v __pycache__ | head -5
# Result:
#   src/shared/billing/application/cost_estimator.py::estimate_llm_cost  (production: prompt char × _TOKENS_PER_CHAR + max_output × rate × 1.10 safety multiplier)
# Conclusion: existing prod cost_estimator es general-purpose pre-LLM-call estimator with character-based heuristic
#             (4 chars/token Spanish LATAM). Story H cost_estimator usa input_tokens directamente (caller passes
#             tokenizer-counted value), no character heuristic. Story H NO multiplier 1.10x — cap caller responsibility.
#             Story H es eval-only, consume mismo `model_pricing_snapshot` shared table como pricing source
#             (anti-duplication respect — extends not mirrors). Distinct enough en uso (input_tokens param vs prompt str)
#             to justify separate file. PM consideró LIFT-TO-SHARED if Story I también necesita; mantiene en story dir
#             de momento (YAGNI — Story I extends additively post-ship).

# 4. eval_simulator_llm_call.cost_usd column — confirm consume read-only
grep -n "cost_usd" backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py
# Result: cost_usd Column(Numeric(10,6), nullable=True) — Story B H7 cement (Alembic 125)
# Conclusion: read-only sum query: SELECT SUM(cost_usd) FROM eval_simulator_llm_call WHERE run_id = :run_id

# 5. eval_simulator_grade.cost_usd_total column — confirm Story E plans + consume read-only
grep -n "cost_usd_total" docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md | head -3
# Result: §3.1 DDL "cost_usd_total NUMERIC(10,6) NOT NULL DEFAULT 0" planned Alembic 127
# Conclusion: Story E builds → eval_simulator_grade.cost_usd_total available. Story H consumes via SQL sum.

# 6. simulator/__init__.py public API — confirm 7 baseline + Story E expansion plan
cat backend/tests/agentic_evals/sales_agent/simulator/__init__.py | grep -A12 "__all__"
# Result: __all__ = 7 names (Story B cement). Story E plans expand 7→8 (grade_transcript_maj_eval).
#         Story H plans expand 8→9 (check_budget_before_call) — pre-condition Story E ships first.

# 7. asyncio Task background patterns — verify pattern existing
grep -rn "asyncio.create_task\|asyncio.Task" backend/src/shared/ backend/tests/agentic_evals/ 2>/dev/null | grep -v __pycache__ | head -5
# Result: existing patterns in shared/billing/workers/ + others. Story H uses canonical asyncio.create_task pattern.

# 8. Pydantic model_pricing_snapshot — confirm Story H reads via existing accessor
grep -n "model_pricing_snapshot" backend/src/shared/agent_observability/persistence/ -r | head -3
# Result: shared/agent_observability/persistence/pricing_snapshot_repository.py — canonical accessor
# Conclusion: Story H cost_estimator imports PricingSnapshotRepository (shared) for model price lookup.
#             Read-only consumer — anti-duplication respect.

# 9. SCHEMA_MIGRATIONS registry — confirm Story H adds anchor entry
grep "register_schema_migration\|CURRENT_SCHEMA_VERSIONS" backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py 2>/dev/null
# Result: 2 entries Story C (ActorProfile, 1, 2) + (CustomerPrompt, 1, 2). Story F plans add EvalPassKSummary v1 anchor.
#         Story H adds BudgetState v1 anchor (sentinel — no migrator function v1; future v2 register migrator).

# 10. capability YAML extension target
ls docs/product/capabilities/sales-agent/sales-conversational-engine.yaml
# Result: file exists. Story C/F extend with eval block. Story H appends `budget_caps_per_tier`,
#         `budget_summary_path`, `budget_disable_flag`, `cost_baseline_per_run_usd`.
```

### Sistemas existentes encontrados (Stories A/B/C/D/E/F SSoT — consume READ-ONLY, NOT mirror)

| Sistema | Path canónico | Estado | Decisión Story H |
|---|---|---|---|
| `eval_simulator_llm_call.cost_usd` (Story B) | `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py` (Alembic 125) | active | **READ-ONLY** — guard queries `SELECT SUM(cost_usd) WHERE run_id = :run_id` (generation bucket sum) |
| `eval_simulator_grade.cost_usd_total` (Story E) | `modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` (Alembic 127 planned) | planned (Story E refined) — built before Story H | **READ-ONLY** — guard queries `SELECT SUM(cost_usd_total) WHERE run_id = :run_id via simulation_id FK` (grader bucket sum) |
| `model_pricing_snapshot` shared table | `shared/agent_observability/persistence/models/pricing_snapshot_model.py` | active LiteLLM canonical sync daily | **READ-ONLY** — `cost_estimator.py` reads via `PricingSnapshotRepository` shared accessor for input/output rate per (provider, model) |
| `BudgetGuard` (production runtime) | `shared/billing/application/budget_guard.py` | active runtime prod | **NO TOUCH** — different paradigm (runtime per-tenant Others vs SA pool, MV-backed plan-driven). Story H eval-suite synthetic. Documented §2 audit anti-duplication respect |
| `BudgetExceeded` (production exception) | `shared/billing/application/exceptions.py` | active runtime prod | **NO TOUCH** — production HTTP 402 mapping. Story H uses NEW `BudgetCapExceededError` (eval-only, distinct semantics: pre_flight vs post_facto bypass detection field) |
| `BudgetGuardingLLMService` (production wrapper) | `shared/billing/application/llm_guards.py` | active runtime prod | **NO TOUCH** — production LangChain wrapper. Story H NO wrapper (caller invokes guard.check_budget_before_call manually pre-flight) |
| `estimate_llm_cost` (production cost_estimator) | `shared/billing/application/cost_estimator.py` | active runtime prod | **NO MIRROR** — production uses prompt char × heuristic + 1.10x multiplier; Story H caller passes tokenizer-counted input_tokens (no heuristic). Eval-only context — paradigmas distintos. Both reuse `model_pricing_snapshot` shared (anti-duplication respect at data layer) |
| `EvalSimulatorObservabilityContext` (Story B) | `simulator/_internal/observability.py` | active | **NO TOUCH** — guard emits structlog ONLY (no DB writes to llm_call/trace_event). NO callback handler needed (read-only) |
| `simulator/__init__.py` `__all__` 7 names baseline (Story B) + 8 Story E (planned) | `simulator/__init__.py` | active frozen 7 + Story E expand 7→8 planned | **EXPAND 8→9** — `check_budget_before_call` NEW. PRE-CONDITION: Story E ships first. Re-freeze 9 names post-Story H ship |
| `SCHEMA_MIGRATIONS` registry (Story B H1) | `simulator/_internal/schema_migrations.py` | active 2 entries Story C + Story F plans add 1 (EvalPassKSummary v1) | **EXTEND** — register `BudgetState` v1 anchor (sentinel for future bumps; no migrator function v1) |
| Capability YAML | `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` | active | **EXTEND** — append eval block fields per §3.9 (post-merge by /pm) |
| `BudgetGuard` test-infra cost recording | N/A | does not exist | **NEW (Story H creates)** — eval-only context, paradigm distinct from production |

### Decisión por sistema — sumario

- **READ-ONLY (consume only)**: `eval_simulator_llm_call.cost_usd` (Story B), `eval_simulator_grade.cost_usd_total` (Story E), `model_pricing_snapshot` shared table.
- **EXTEND (additive, justified)**: `SCHEMA_MIGRATIONS` registry (1 anchor entry `BudgetState` v1), `simulator/__init__.py` `__all__` (8→9 puntual expansion `check_budget_before_call`), capability YAML eval block, `auditor-downstream-regression.md` SSoT entry.
- **NEW (genuinely justified, last resort — no existing system overlaps ≥80%)**:
  - Pydantic types `_schema.py` (`BudgetState`, `BucketState`, `TierState`, `AbortContext`, `BudgetWarning`, `BudgetCapExceededError`)
  - `_internal/cost_estimator.py` (over-estimate strict — input × price + max_output × price, NO 1.10x multiplier — caller responsibility)
  - `guard.py` (3 public APIs: `check_budget_before_call`, `compute_remaining_budget`, `start_periodic_sweep`)
  - `_internal/sweep.py` (periodic asyncio Task post-facto detection)
  - 2 NEW arch fitness gates (`test_eval_llm_calls_use_budget_guard.py`, `test_budget_state_schema_complete.py`)
  - 1 UPDATE arch fitness gate (`test_simulator_public_api_surface.py` allowlist 8→9)
  - `simulator/__init__.py` H9 expand 8→9 (single `check_budget_before_call` addition)
- **NO TOUCH**: §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot **schema** read-only, tool_call_dedup), `LLM_ROLE_BY_SITE`, `personality_profiles.system_instruction`, `eval_simulator_*` DB schema (Stories B/E own — read-only), Story F aggregator (consume cascade only — `unconverged: true` flag set on partial run), modules/copilot/, modules/sales_agent/{domain,application,api,observability/recording}/, frontend/, client_simulator/, `core/config.py` defaults (env vars only — no flag flip per `.claude/rules/anti-default-flip-audit.md`), Story B `simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency,schema_migrations}.py` (Story H EDITS solo `schema_migrations.py` anchor entry append + `simulator/__init__.py` expand — el resto NO TOUCH), shared `BudgetGuard` (production paradigm — different scope).

## §3 BE arch (Pydantic v2 + cost_estimator + guard + sweep + arch fitness gates + H9 expand)

### §3.1 Pydantic v2 types (`_schema.py`)

File NEW: `backend/tests/agentic_evals/sales_agent/budget/_schema.py`. Pattern parity con Story F `_schema.py` (Pydantic v2 frozen=True + extra=forbid + Literal forward-compat).

Reference impl (matches spec § Schema cement v1):

```python
"""Pydantic v2 schemas for Story H eval cost-budget guard.

Schema cement v1 — forward-compat via SCHEMA_MIGRATIONS registry (Story B H1 reuse).

Decision D-BE-1: BudgetState frozen=True (immutable post-aggregation snapshot).
Decision D-BE-2: BucketState Literal["generation", "grader"] cement; Story I extends additively.
Decision D-BE-3: TierState Literal 4 tier_id values cement (per_trial / per_grade / per_run / per_bucket).
Decision D-BE-4: schema_version Literal[1] = 1 cement; future bumps register migrator.
Decision D-BE-5: BudgetCapExceededError include post_facto field — distinguishes pre_flight vs sweep detection.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BucketState(BaseModel):
    """One row per cost bucket — generation (Story B) or grader (Story E)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    bucket_id: Literal["generation", "grader"]
    current_cost_usd: Decimal
    cap_usd: Decimal
    pct_of_cap: float = Field(ge=0.0, le=200.0)  # may exceed 100% on post-facto detection
    threshold_warning_pct: Literal[80] = 80
    warning_emitted: bool


class TierState(BaseModel):
    """One row per tier — per_trial / per_grade / per_run / per_bucket."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    tier_id: Literal["per_trial", "per_grade", "per_run", "per_bucket"]
    cap_usd: Decimal
    cap_disabled: bool


class AbortContext(BaseModel):
    """Where + when the abort fired (Scenario 2 detail capture)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    simulation_id: str | None = None
    turn_n: int | None = None
    rubric_id: str | None = None
    estimated_next_usd: Decimal
    projected_total_usd: Decimal
    cap_usd: Decimal


class BudgetWarning(BaseModel):
    """Single warning event (≥ 80% per-bucket threshold crossed)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    timestamp: datetime
    tier: str
    bucket: str | None = None
    current_usd: Decimal
    cap_usd: Decimal
    pct: float = Field(ge=0.0, le=200.0)
    message: str  # Spanish neutro LATAM user-facing


class BudgetState(BaseModel):
    """Persisted JSON snapshot at `_artifacts/eval_runs/{run_id}/budget_summary.json`."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    run_id: str
    buckets: list[BucketState]   # 2 buckets baseline (generation + grader); Story I extends additively
    tiers: list[TierState]       # 4 tiers cement (per_trial / per_grade / per_run / per_bucket)
    total_cost_usd: Decimal
    total_cap_usd: Decimal
    aborted: bool
    abort_reason: Literal["budget_cap_exceeded", "manual"] | None = None
    abort_bucket: Literal["generation", "grader"] | None = None
    abort_tier: Literal["per_trial", "per_grade", "per_run", "per_bucket"] | None = None
    aborted_at: AbortContext | None = None
    disabled: bool             # SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1
    completed_sims: int = Field(ge=0)
    pending_sims: int = Field(ge=0)
    warnings: list[BudgetWarning]
    started_at: datetime
    aborted_at_timestamp: datetime | None = None
    final_at: datetime | None = None


class BudgetCapExceededError(Exception):
    """Raised when pre-flight projection or post-facto sweep detects cap breach.

    Distinct from production `shared/billing/exceptions.py::BudgetExceeded` —
    eval-only context, post_facto field discriminates pre-flight vs sweep detection.
    """

    def __init__(
        self,
        *,
        bucket: str,
        tier: str,
        current_usd: Decimal,
        estimated_next_usd: Decimal,
        cap_usd: Decimal,
        abort_context: AbortContext,
        post_facto: bool = False,
    ) -> None:
        self.bucket = bucket
        self.tier = tier
        self.current_usd = current_usd
        self.estimated_next_usd = estimated_next_usd
        self.cap_usd = cap_usd
        self.abort_context = abort_context
        self.post_facto = post_facto
        suffix = " (post-facto bypass detected)" if post_facto else ""
        super().__init__(
            f"Budget cap exceeded{suffix}: bucket={bucket}, tier={tier}, "
            f"current=${current_usd}, estimated_next=${estimated_next_usd}, "
            f"projected=${current_usd + estimated_next_usd}, cap=${cap_usd}.",
        )
```

### §3.2 `guard.py` — 3 public APIs

File NEW: `backend/tests/agentic_evals/sales_agent/budget/guard.py`.

Reference impl:

```python
"""Multi-tier eval cost-budget guard — pre-flight + sweep + read-only API.

Decision D-BE-6: 3 public APIs cement — check_budget_before_call (pre-flight),
                 compute_remaining_budget (read), start_periodic_sweep (post-facto detection).
Decision D-BE-7: Cap defaults via env vars Pydantic Settings or os.getenv with Decimal cast;
                 SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1 short-circuits all checks.
Decision D-BE-8: Read-only invariant — zero LLM imports (arch fitness gate enforce static scan).
                 Zero writes to *_llm_call / *_grade tables (only structlog + JSON output).
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_llm_call import (
    EvalSimulatorLlmCallModel,
)
# NOTE: EvalSimulatorGradeModel imported lazily — Story E build precedes Story H build (hard blocker).
# Synthetic fixtures used during isolated Story H tests; integration tests gated post-Story E.
from tests.agentic_evals.sales_agent.budget._internal.cost_estimator import (
    estimate_cost_for_call,
)
from tests.agentic_evals.sales_agent.budget._internal.sweep import (
    start_periodic_sweep,
)
from tests.agentic_evals.sales_agent.budget._schema import (
    AbortContext,
    BucketState,
    BudgetCapExceededError,
    BudgetState,
    BudgetWarning,
    TierState,
)

logger = structlog.get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _is_disabled() -> bool:
    return os.getenv("SALES_AGENT_EVAL_BUDGET_CAP_DISABLE", "0") == "1"


def _load_caps() -> dict[str, Decimal]:
    """Load cap defaults from env vars (D-BE-7).

    Defaults match spec § caps cement:
      per_trial=0.10, per_grade=0.20, per_run cold=500 (default), warm=150,
      per_bucket_generation=20, per_bucket_grader cold=400 / warm=130.
    """
    return {
        "per_trial": Decimal(os.getenv("SALES_AGENT_EVAL_PER_TRIAL_CAP_USD", "0.10")),
        "per_grade": Decimal(os.getenv("SALES_AGENT_EVAL_PER_GRADE_CAP_USD", "0.20")),
        "per_run": Decimal(os.getenv("SALES_AGENT_EVAL_PER_RUN_CAP_USD", "500")),
        "per_bucket_generation": Decimal(
            os.getenv("SALES_AGENT_EVAL_PER_BUCKET_GENERATION_CAP_USD", "20"),
        ),
        "per_bucket_grader": Decimal(
            os.getenv("SALES_AGENT_EVAL_PER_BUCKET_GRADER_CAP_USD", "400"),
        ),
    }


def _warning_pct() -> int:
    return int(os.getenv("SALES_AGENT_EVAL_BUDGET_WARNING_PCT", "80"))


async def compute_remaining_budget(
    session: AsyncSession,
    *,
    run_id: str,
) -> BudgetState:
    """Read-only: compute current per-bucket sums + return BudgetState snapshot.

    Queries:
      - eval_simulator_llm_call.cost_usd SUM (generation bucket — Story B H7)
      - eval_simulator_grade.cost_usd_total SUM (grader bucket — Story E)

    NEVER writes to any LLM call / grade table (read-only invariant cement D-BE-8).
    """
    # Story E grader table import lazy — synthetic fixtures used pre-Story E build.
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade import (
        EvalSimulatorGradeModel,
    )

    caps = _load_caps()
    disabled = _is_disabled()

    # Generation bucket sum
    gen_stmt = (
        select(func.coalesce(func.sum(EvalSimulatorLlmCallModel.cost_usd), 0))
        .where(EvalSimulatorLlmCallModel.eval_metadata["run_id"].astext == run_id)
    )
    gen_result = await session.execute(gen_stmt)
    generation_sum = Decimal(str(gen_result.scalar() or 0))

    # Grader bucket sum (Story E table)
    grader_stmt = (
        select(func.coalesce(func.sum(EvalSimulatorGradeModel.cost_usd_total), 0))
        # Story E: simulation_id FK to run_id resolution via subquery on eval_simulator
        # (see Story E §3.4 query pattern); pseudocode here — actual impl per Story E schema
        .where(EvalSimulatorGradeModel.run_id == run_id)  # if run_id direct column post Story E
    )
    grader_result = await session.execute(grader_stmt)
    grader_sum = Decimal(str(grader_result.scalar() or 0))

    total_cost = generation_sum + grader_sum
    total_cap = caps["per_run"]

    warning_pct = _warning_pct()

    gen_pct = float((generation_sum / caps["per_bucket_generation"]) * 100) if caps["per_bucket_generation"] > 0 else 0.0
    grader_pct = float((grader_sum / caps["per_bucket_grader"]) * 100) if caps["per_bucket_grader"] > 0 else 0.0

    buckets = [
        BucketState(
            bucket_id="generation",
            current_cost_usd=generation_sum,
            cap_usd=caps["per_bucket_generation"],
            pct_of_cap=gen_pct,
            warning_emitted=gen_pct >= warning_pct,
        ),
        BucketState(
            bucket_id="grader",
            current_cost_usd=grader_sum,
            cap_usd=caps["per_bucket_grader"],
            pct_of_cap=grader_pct,
            warning_emitted=grader_pct >= warning_pct,
        ),
    ]
    tiers = [
        TierState(tier_id="per_trial", cap_usd=caps["per_trial"], cap_disabled=disabled),
        TierState(tier_id="per_grade", cap_usd=caps["per_grade"], cap_disabled=disabled),
        TierState(tier_id="per_run", cap_usd=caps["per_run"], cap_disabled=disabled),
        TierState(tier_id="per_bucket", cap_usd=caps["per_bucket_generation"], cap_disabled=disabled),
    ]
    warnings: list[BudgetWarning] = []
    for b in buckets:
        if b.warning_emitted:
            warnings.append(
                BudgetWarning(
                    timestamp=_utc_now(),
                    tier="per_bucket",
                    bucket=b.bucket_id,
                    current_usd=b.current_cost_usd,
                    cap_usd=b.cap_usd,
                    pct=b.pct_of_cap,
                    message=(
                        f"Bucket {b.bucket_id} llegó al {b.pct_of_cap:.1f}% del cap "
                        f"${b.cap_usd}. Costo actual: ${b.current_cost_usd}."
                    ),
                ),
            )
            logger.warning(
                "eval.budget.tier_warning",
                run_id=run_id,
                bucket=b.bucket_id,
                tier="per_bucket",
                current_usd=str(b.current_cost_usd),
                cap_usd=str(b.cap_usd),
                pct=b.pct_of_cap,
            )

    return BudgetState(
        run_id=run_id,
        buckets=buckets,
        tiers=tiers,
        total_cost_usd=total_cost,
        total_cap_usd=total_cap,
        aborted=False,
        disabled=disabled,
        completed_sims=0,
        pending_sims=0,
        warnings=warnings,
        started_at=_utc_now(),
    )


async def check_budget_before_call(
    session: AsyncSession,
    *,
    run_id: str,
    estimated_cost_usd: Decimal,
    bucket: str,
    simulation_id: str | None = None,
    turn_n: int | None = None,
    rubric_id: str | None = None,
) -> None:
    """Pre-flight gate. Raises ``BudgetCapExceededError`` on projected breach.

    Must be invoked BEFORE every LLM call. Layer 1 enforcement (arch fitness gate
    test_eval_llm_calls_use_budget_guard.py static scan + import requirement).
    Layer 2 enforcement (runtime sweep — see start_periodic_sweep).
    """
    if _is_disabled():
        return  # debug mode short-circuit

    state = await compute_remaining_budget(session, run_id=run_id)

    # Per-bucket projection
    target = next((b for b in state.buckets if b.bucket_id == bucket), None)
    if target is None:
        # Unknown bucket — fail-closed defensive (better safe than sorry)
        raise BudgetCapExceededError(
            bucket=bucket,
            tier="per_bucket",
            current_usd=Decimal("0"),
            estimated_next_usd=estimated_cost_usd,
            cap_usd=Decimal("0"),
            abort_context=AbortContext(
                simulation_id=simulation_id,
                turn_n=turn_n,
                rubric_id=rubric_id,
                estimated_next_usd=estimated_cost_usd,
                projected_total_usd=estimated_cost_usd,
                cap_usd=Decimal("0"),
            ),
            post_facto=False,
        )

    projected = target.current_cost_usd + estimated_cost_usd
    if projected > target.cap_usd:
        ctx = AbortContext(
            simulation_id=simulation_id,
            turn_n=turn_n,
            rubric_id=rubric_id,
            estimated_next_usd=estimated_cost_usd,
            projected_total_usd=projected,
            cap_usd=target.cap_usd,
        )
        logger.error(
            "eval.budget.cap_exceeded",
            run_id=run_id,
            bucket=bucket,
            tier="per_bucket",
            current_usd=str(target.current_cost_usd),
            estimated_next_usd=str(estimated_cost_usd),
            projected_total_usd=str(projected),
            cap_usd=str(target.cap_usd),
        )
        raise BudgetCapExceededError(
            bucket=bucket,
            tier="per_bucket",
            current_usd=target.current_cost_usd,
            estimated_next_usd=estimated_cost_usd,
            cap_usd=target.cap_usd,
            abort_context=ctx,
            post_facto=False,
        )

    # Per-run projection (additive across all buckets)
    projected_total = state.total_cost_usd + estimated_cost_usd
    if projected_total > state.total_cap_usd:
        ctx = AbortContext(
            simulation_id=simulation_id,
            turn_n=turn_n,
            rubric_id=rubric_id,
            estimated_next_usd=estimated_cost_usd,
            projected_total_usd=projected_total,
            cap_usd=state.total_cap_usd,
        )
        logger.error(
            "eval.budget.cap_exceeded",
            run_id=run_id,
            bucket=bucket,
            tier="per_run",
            current_usd=str(state.total_cost_usd),
            estimated_next_usd=str(estimated_cost_usd),
            projected_total_usd=str(projected_total),
            cap_usd=str(state.total_cap_usd),
        )
        raise BudgetCapExceededError(
            bucket=bucket,
            tier="per_run",
            current_usd=state.total_cost_usd,
            estimated_next_usd=estimated_cost_usd,
            cap_usd=state.total_cap_usd,
            abort_context=ctx,
            post_facto=False,
        )


__all__ = [
    "check_budget_before_call",
    "compute_remaining_budget",
    "estimate_cost_for_call",
    "start_periodic_sweep",
    "BudgetCapExceededError",
    "BudgetState",
    "BucketState",
    "TierState",
    "AbortContext",
    "BudgetWarning",
]
```

### §3.3 `_internal/cost_estimator.py` — over-estimate strict (D4 cement)

File NEW: `backend/tests/agentic_evals/sales_agent/budget/_internal/cost_estimator.py`.

Reference impl:

```python
"""Pre-flight cost estimator for Story H eval budget guard.

Over-estimate strict (D4 cement spec): input_tokens × input_price + max_output_tokens × output_price.
NO 1.10x safety multiplier (cap caller responsibility — production cost_estimator uses multiplier
for runtime; eval-only context expects exact spec input_tokens passed by caller tokenizer).

Decision D-BE-9: Pricing source = `model_pricing_snapshot` shared table (LiteLLM canonical sync daily).
                 Read-only consumer — anti-duplication respect. NO mirror prod estimate_llm_cost helper.
"""

from __future__ import annotations

from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.agent_observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)

logger = structlog.get_logger(__name__)


async def estimate_cost_for_call(
    session: AsyncSession,
    *,
    model: str,
    input_tokens: int,
    max_output_tokens: int,
) -> Decimal:
    """Over-estimate USD cost BEFORE LLM call (D4 cement strict).

    Formula: input_tokens × input_rate + max_output_tokens × output_rate.
    NO multiplier (eval expects caller-passed input_tokens tokenizer-counted; cap pre-emptive).

    Returns Decimal with 6dp precision.
    """
    repo = PricingSnapshotRepository(session)
    pricing = await repo.get_latest_for_model(model)

    if pricing is None:
        # Conservative fallback (Claude Opus tier — 1000-tenants safety)
        input_rate = Decimal("0.000005")
        output_rate = Decimal("0.000015")
        logger.warning(
            "eval.budget.cost_estimate_fallback",
            model=model,
        )
    else:
        input_rate = Decimal(str(pricing.input_cost_per_token))
        output_rate = Decimal(str(pricing.output_cost_per_token))

    cost = (Decimal(input_tokens) * input_rate) + (Decimal(max_output_tokens) * output_rate)
    return cost.quantize(Decimal("0.000001"))
```

### §3.4 `_internal/sweep.py` — periodic asyncio Task (D5 cement 30s interval)

File NEW: `backend/tests/agentic_evals/sales_agent/budget/_internal/sweep.py`.

Reference impl (canonical asyncio.create_task pattern per [Super Fast Python asyncio periodic task](https://superfastpython.com/asyncio-periodic-task/) accessed 2026-05-08):

```python
"""Periodic sweep — post-facto direct LLM call bypass detection.

Decision D-BE-10: 30s interval default cement (D5 spec). Configurable via env var
                  SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S.
Decision D-BE-11: asyncio.create_task pattern — orchestrator owns Task lifecycle
                  (start at run start, cancel at run end). Caller responsibility.

Pattern: Python 3.12 canonical periodic Task — async def loop forever; sleep + await.
Reference: https://superfastpython.com/asyncio-periodic-task/ accessed 2026-05-08.
"""

from __future__ import annotations

import asyncio
import os

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from tests.agentic_evals.sales_agent.budget._schema import (
    AbortContext,
    BudgetCapExceededError,
)

logger = structlog.get_logger(__name__)


def _interval_seconds() -> int:
    return int(os.getenv("SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S", "30"))


async def _sweep_once(session: AsyncSession, *, run_id: str) -> None:
    """One sweep iteration — query current state, detect post-facto cap breach."""
    # Lazy import — avoid circular dep with guard.py
    from tests.agentic_evals.sales_agent.budget.guard import compute_remaining_budget

    state = await compute_remaining_budget(session, run_id=run_id)

    if state.disabled:
        return  # debug mode short-circuit

    # Per-bucket post-facto check
    for b in state.buckets:
        if b.current_cost_usd > b.cap_usd:
            logger.warning(
                "eval.budget.bypass_detected",
                run_id=run_id,
                bucket=b.bucket_id,
                current_usd=str(b.current_cost_usd),
                cap_usd=str(b.cap_usd),
                pct=b.pct_of_cap,
                hint="LLM call likely bypassed check_budget_before_call wrapper",
            )
            ctx = AbortContext(
                estimated_next_usd=b.current_cost_usd - b.cap_usd,
                projected_total_usd=b.current_cost_usd,
                cap_usd=b.cap_usd,
            )
            raise BudgetCapExceededError(
                bucket=b.bucket_id,
                tier="per_bucket",
                current_usd=b.current_cost_usd,
                estimated_next_usd=Decimal("0"),  # sweep detects post-facto, no projection
                cap_usd=b.cap_usd,
                abort_context=ctx,
                post_facto=True,
            )


async def _sweep_loop(session: AsyncSession, run_id: str) -> None:
    """Sweep loop forever — exit on Task cancellation or BudgetCapExceededError."""
    interval = _interval_seconds()
    while True:
        try:
            await _sweep_once(session, run_id=run_id)
        except BudgetCapExceededError:
            raise  # Propagate to caller (orchestrator handles abort + partial report)
        except asyncio.CancelledError:
            return  # Clean shutdown
        except Exception:
            # Soft-fail: log + continue (sweep itself MUST NOT take down run on transient DB error)
            logger.exception(
                "eval.budget.sweep_iteration_failed_soft_fail",
                run_id=run_id,
            )
        await asyncio.sleep(interval)


def start_periodic_sweep(
    session: AsyncSession,
    *,
    run_id: str,
    interval_s: int | None = None,
) -> asyncio.Task[None]:
    """Schedule periodic sweep as background Task.

    Caller MUST cancel returned Task at run end:
        task = start_periodic_sweep(session, run_id=run_id)
        try:
            await run_eval_suite(...)
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    Returns: asyncio.Task[None] for caller lifecycle management.
    """
    return asyncio.create_task(_sweep_loop(session, run_id))
```

### §3.5 Env var loader pattern (D7 cement)

Caps loaded via `os.getenv(...)` with Decimal cast in `guard._load_caps()`. Disable flag short-circuits all checks via `SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1` (debug only — CI strict). Warning threshold configurable via `SALES_AGENT_EVAL_BUDGET_WARNING_PCT` (default 80% per D10 cement spec). Sweep interval via `SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S` (default 30s D5 cement).

Env vars cement (mirror spec § env_vars):

```
SALES_AGENT_EVAL_PER_TRIAL_CAP_USD=0.10
SALES_AGENT_EVAL_PER_GRADE_CAP_USD=0.20
SALES_AGENT_EVAL_PER_RUN_CAP_USD=500          # cold default; CI sets 150 if cache warm expected
SALES_AGENT_EVAL_PER_BUCKET_GENERATION_CAP_USD=20
SALES_AGENT_EVAL_PER_BUCKET_GRADER_CAP_USD=400  # cold default
SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=0           # 1 = disable for debug
SALES_AGENT_EVAL_BUDGET_WARNING_PCT=80
SALES_AGENT_EVAL_BUDGET_SWEEP_INTERVAL_S=30
```

NO flag flip in `core/config.py` — env vars only (per `.claude/rules/anti-default-flip-audit.md`).

### §3.6 NEW arch fitness gate `test_eval_llm_calls_use_budget_guard.py` (Layer 1 enforcement)

File NEW: `backend/tests/architecture/test_eval_llm_calls_use_budget_guard.py`. Empty allowlist shrink-only.

Reference impl (AST static analysis pattern per Story F arch fitness precedent):

```python
"""Architecture fitness gate — eval LLM calls MUST be wrapped by budget guard (Story H Layer 1).

Walks `backend/tests/agentic_evals/sales_agent/` for direct litellm/anthropic/openai imports.
Each file importing LLM module MUST also import `from tests.agentic_evals.sales_agent.budget.guard
import check_budget_before_call`.

Allowlist EMPTY — shrink-only ratchet.

Decision D-BE-12: Convention enforcement (import-pair check) over AST call-site analysis —
                  simpler implementation, sufficient signal: "if file imports LLM, MUST import guard".
                  False-positive risk minimal (eval-only paths; helper modules without LLM calls
                  don't import LLM module so don't trigger).

Pattern: ast.NodeVisitor walk over .py files; assert (LLM_import OR guard_import OR no_LLM_import).

Origin: Story H sales-agent-eval-cost-budget-cap T-5 (NEW arch fitness gate).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval

_EVAL_ROOT = Path(__file__).parent.parent / "agentic_evals" / "sales_agent"
_FORBIDDEN_LLM_MODULES = frozenset({"litellm", "anthropic", "openai"})
_GUARD_MODULE = "tests.agentic_evals.sales_agent.budget.guard"
_GUARD_FUNCTION = "check_budget_before_call"

# Allowlist EMPTY — shrink-only ratchet. Files exempt from guard pairing must be added with
# explicit justification + comment + auditor review.
_ALLOWLIST: frozenset[str] = frozenset()


def _file_imports(path: Path) -> tuple[set[str], set[str]]:
    """Return (top-level modules imported, names imported from)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return (set(), set())
    modules: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
            full_module = node.module
            for alias in node.names:
                names.add(f"{full_module}::{alias.name}")
    return (modules, names)


def _scan_eval_files() -> list[Path]:
    if not _EVAL_ROOT.exists():
        return []
    return [
        p for p in _EVAL_ROOT.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "conftest.py"
    ]


def test_eval_llm_imports_pair_with_budget_guard() -> None:
    """Every eval file importing litellm/anthropic/openai MUST also import guard.

    Allowlist empty (shrink-only). Build adds → forces ratchet violation discussion.
    """
    violations: list[str] = []
    for path in _scan_eval_files():
        rel = str(path.relative_to(_EVAL_ROOT))
        if rel in _ALLOWLIST:
            continue
        modules, names = _file_imports(path)
        imports_llm = bool(modules & _FORBIDDEN_LLM_MODULES)
        imports_guard = any(
            name.startswith(_GUARD_MODULE + "::") and name.endswith(_GUARD_FUNCTION)
            for name in names
        ) or any(
            module == "tests" and "budget.guard" in str(path.read_text(encoding="utf-8"))
            for module in modules
        )
        if imports_llm and not imports_guard:
            violations.append(rel)

    assert not violations, (
        f"Files import LLM module but missing budget guard pairing: {violations}. "
        f"Each file importing {sorted(_FORBIDDEN_LLM_MODULES)} MUST also import "
        f"`from {_GUARD_MODULE} import {_GUARD_FUNCTION}`. "
        f"Allowlist empty — shrink-only ratchet (NO additions without auditor justification)."
    )


def test_budget_guard_module_no_llm_imports() -> None:
    """Guard MUST NOT import LLM modules (read-only invariant cement D-BE-8).

    Static scan pass_k pattern reused — guard.py + cost_estimator.py + sweep.py + _schema.py
    forbidden imports.
    """
    guard_root = _EVAL_ROOT / "budget"
    if not guard_root.exists():
        pytest.skip("Story H not built yet")
    violations: list[str] = []
    for path in guard_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        modules, _ = _file_imports(path)
        forbidden_used = modules & _FORBIDDEN_LLM_MODULES
        if forbidden_used:
            violations.append(f"{path.relative_to(guard_root)}: {sorted(forbidden_used)}")
    assert not violations, (
        f"Guard module imports forbidden LLM modules (violates read-only invariant D-BE-8): "
        f"{violations}. Guard MUST be read-only consumer (sums cost rows + Pydantic + asyncio sweep)."
    )
```

### §3.7 `simulator/__init__.py` H9 expand 8→9 + arch fitness allowlist update

EDIT: `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (single addition `check_budget_before_call`).

```python
# Story H expand: __all__ 8→9 names. Pre-condition: Story E ships first (8 names).
# Re-freeze 9 names post Story H ship.

from tests.agentic_evals.sales_agent.budget.guard import check_budget_before_call

__all__ = [
    "ActorProfile",
    "AgentErrorSubtype",
    "SimulationResult",
    "SimulationState",
    "TerminationReason",
    "check_budget_before_call",         # NEW Story H (8→9)
    "grade_transcript_maj_eval",        # Story E (7→8)
    "register_termination_policy",
    "run_simulation",
]
```

EDIT: `backend/tests/architecture/test_simulator_public_api_surface.py`:

```python
# Story H expand allowlist 8→9 names cement.
_EXPECTED_PUBLIC_NAMES: frozenset[str] = frozenset(
    {
        "run_simulation",
        "SimulationResult",
        "SimulationState",
        "ActorProfile",
        "TerminationReason",
        "AgentErrorSubtype",
        "register_termination_policy",
        "grade_transcript_maj_eval",        # Story E
        "check_budget_before_call",         # Story H
    },
)
# Cardinality test: assert len == 9
```

### §3.8 JSON output `_artifacts/eval_runs/{run_id}/budget_summary.json` (v1 schema cement)

Persisted by orchestrator at run end (or on abort). Schema = `BudgetState.model_dump_json(indent=2)`. Story G CI gate consume verbatim (pinned v1 via `schema_version: Literal[1]`).

Forward-compat: Story I extends additively (e.g., adversarial bucket Literal expansion). SCHEMA_MIGRATIONS registry entry `(BudgetState, 1, ...)` placeholder (no migrator function v1; future v2 register migrator post-ship).

### §3.9 Capability YAML extension

EDIT (post-merge by /pm only): `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` — append eval block fields:

```yaml
eval:
  # ... existing fields from Stories C/E/F ...
  story_h_introduced: sales-agent-eval-cost-budget-cap
  story_h_merged_at: null  # set post /auditor APPROVED + /pm merge
  budget_caps_per_tier:
    per_trial_usd: "0.10"
    per_grade_usd: "0.20"
    per_run_cold_usd: "500"
    per_run_warm_usd: "150"
    per_bucket_generation_usd: "20"
    per_bucket_grader_cold_usd: "400"
    per_bucket_grader_warm_usd: "130"
  budget_summary_path: "_artifacts/eval_runs/{run_id}/budget_summary.json"
  budget_disable_flag: "SALES_AGENT_EVAL_BUDGET_CAP_DISABLE"
  cost_baseline_per_run_usd:
    cold_cache: "340"   # Story E baseline ~$340 + 50% margin → $500 cap
    warm_cache: "115"   # Story E baseline ~$115 + 30% margin → $150 cap
  story_h_test_coverage:
    - backend/tests/agentic_evals/sales_agent/budget/test_budget_guard.py
    - backend/tests/agentic_evals/sales_agent/budget/test_budget_state.py
    - backend/tests/agentic_evals/sales_agent/budget/test_sweep.py
    - backend/tests/architecture/test_eval_llm_calls_use_budget_guard.py
    - backend/tests/architecture/test_budget_state_schema_complete.py
```

### §3.10 Arch fitness gates — additions

Story H additions to `backend/tests/architecture/`:

| Gate | Purpose | Allowlist | Status |
|---|---|---|---|
| `test_eval_llm_calls_use_budget_guard.py` | NEW (Layer 1 enforcement direct LLM imports paired with guard) | empty shrink-only | NEW T-5 |
| `test_budget_state_schema_complete.py` | NEW Pydantic ⊆ JSON schema fields match cement | empty | NEW T-5 |
| `test_simulator_public_api_surface.py` | UPDATE allowlist 8→9 names (`check_budget_before_call` add) | hardcoded frozenset | EDIT T-6 |

SCHEMA_MIGRATIONS registry extend: anchor entry `BudgetState v1` (sentinel for future bumps; no migrator function v1).

## §4 AGENTIC arch — N/A

Story H = read-only guard. Zero LLM calls. Zero LangGraph state machine. Zero subagents. Zero prompt slots. Zero observability writes (only structlog + JSON output). AGENTIC arch surface NOT applicable.

## §5 Cross-cutting

- **Tenant isolation** — N/A: eval-only synthetic, run_id derives tenant via Story B `run_simulation` invoker (tests run synthetic 5-tenant slugs from Story A; per-tenant cost cap NOT eval scope per spec § Out of scope).
- **PII handling** — `BudgetWarning.message` strings (Spanish neutro user-facing) MAY contain run_id / bucket / cost values; pass through `sanitize_payload` shared (`shared/agent_observability/recording/sanitization.py`) defense-in-depth, even synthetic data eval. NO secrets / API keys / PII in messages by construction (cost values + bucket IDs only).
- **Voice cement N/A** — guard NO lee voz, no `personality_profiles.system_instruction`. NO sales-agent-expert §3 protected surface touch.
- **Currency** — Decimal monetary fields exclusively. Pydantic types use `Decimal`. NO hardcoded `'USD'` in DTO defaults (per `.claude/rules/master-data.md` + `currency-handling.md`). Spec uses USD for all caps; eval-only synthetic context — NO multi-currency support needed (Story I extends additively if required).
- **Schema versioning** — `BudgetState.schema_version: Literal[1] = 1` cement. SCHEMA_MIGRATIONS registry forward-compat (Story B H1 reuse). Future bumps via registered migrator functions.
- **Observability tags** — guard emits structlog ONLY (`eval.budget.tier_warning`, `eval.budget.cap_exceeded`, `eval.budget.bypass_detected`). NO LLM calls invariant cement D-BE-8. NO writes to `eval_simulator_llm_call`, `eval_simulator_grade`, `copilot_llm_call`, `sales_agent_llm_call`.
- **Cost buckets** — guard READS `eval_simulator_llm_call.cost_usd` (Story B H7) + `eval_simulator_grade.cost_usd_total` (Story E) ONLY. Zero `copilot_*` reads. Read-only cement D-BE-8.
- **Determinism + idempotency** — `compute_remaining_budget(session, run_id)` re-query same DB state → same `BudgetState` row deterministic (modulo timestamps). Idempotency property-based test enforce.
- **Spanish neutro LATAM** (`.claude/rules/spanish-text.md`) — `BudgetWarning.message` user-facing Spanish neutro sin voseo. structlog event names + Pydantic field names + Python identifiers English (technical layer). JSON output schema field names English (consumer Story G CI gate parses).
- **Native-first** (mandatory) — `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/budget/ -v`. NUNCA Docker exec para lint/tests/type-check.
- **Anti-duplication §0** — guard CONSUMES Story B cost rows + Story E grade rows + shared `model_pricing_snapshot`. NO mirror cost recording (Story B H7 owns). NO mirror production `BudgetGuard` shared/billing (different paradigm — runtime per-tenant vs eval-suite synthetic; documented §2). YAGNI on LIFT-TO-SHARED — Story I extends additively post-ship if cross-eval-story pattern emerges.

## §6 Decisiones D-BE-* (cementadas, justification 1 line each)

| # | Decisión | Justificación |
|---|---|---|
| D-BE-1 | BudgetState frozen=True (Pydantic ConfigDict) | Immutable post-aggregation snapshot — UPSERT semantics on JSON output preserves audit trail |
| D-BE-2 | BucketState Literal["generation", "grader"] cement; Story I extends additively | Story B H7 cost-bucket separation cement — bucket separation already cement, guard mirrors |
| D-BE-3 | TierState Literal 4 tier_id values cement (per_trial / per_grade / per_run / per_bucket) | Multi-tier architecture spec D1 cement |
| D-BE-4 | schema_version Literal[1] = 1 cement; future bumps register migrator | Forward-compat 5+ years (Story B H1 reuse) — adversarial bucket Story I additive |
| D-BE-5 | BudgetCapExceededError include post_facto: bool field | Audit trail — post_facto means bypass occurred (security-relevant — sweep detection) |
| D-BE-6 | 3 public APIs cement (check_budget_before_call / compute_remaining_budget / start_periodic_sweep) | Minimal surface — caller composes orchestration |
| D-BE-7 | Cap defaults via os.getenv with Decimal cast; SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1 short-circuit | Local dev iterates without friction; CI strict (env var NEVER set) |
| D-BE-8 | Read-only invariant — zero LLM imports + zero writes to *_llm_call/*_grade tables | Defense-in-depth (arch fitness gate static scan + integration test DB query post-aggregation) |
| D-BE-9 | Pricing source = `model_pricing_snapshot` shared (LiteLLM canonical sync daily) | Anti-duplication respect at data layer — production cost_estimator + Story H read same source |
| D-BE-10 | Periodic sweep 30s interval default cement; configurable via env var | D5 spec cement — sweet spot detection delay vs DB query overhead |
| D-BE-11 | asyncio.create_task pattern — orchestrator owns Task lifecycle | Caller responsibility (start at run start, cancel at run end) — clean lifecycle |
| D-BE-12 | Convention enforcement (import-pair check) over AST call-site analysis | Simpler arch fitness implementation, sufficient signal — false-positive risk minimal |
| D-BE-13 | NO 1.10x safety multiplier (cap caller responsibility) | Eval expects exact spec input_tokens (caller tokenizer-counted); cap pre-emptive — production has multiplier for runtime |

## §7 Output contract for consumers Stories F/G/I

**Story F** (`sales-agent-eval-pass-k-tracking`) consumes:
- `BudgetCapExceededError` raised → orchestrator marks aborted goldens as `unconverged: true` (Story F D9 cement)
- `_artifacts/eval_runs/{run_id}/budget_summary.json` `aborted=true` flag → cascade to Story F aggregator partial run handling

**Story G** (`sales-agent-voice-fidelity-ci-gate`) consumes:
- `_artifacts/eval_runs/{run_id}/budget_summary.json` v1 schema (pinned `schema_version: Literal[1]`)
- Process exit code 2 (D13 cement) — distinct from generic test fail exit 1 → CI distinguishes budget-abort vs functional-regression
- structlog `eval.budget.cap_exceeded` event → CI red signal

**Story I** (`sales-agent-adversarial-jailbreak-suite`) extends additively:
- `BucketState.bucket_id` Literal extends with adversarial bucket (forward-compat Pydantic Literal additive)
- New env var `SALES_AGENT_EVAL_PER_BUCKET_ADVERSARIAL_CAP_USD` (env-driven, no schema bump needed for Pydantic Literal additive in Story I)
- SCHEMA_MIGRATIONS registry MAY register `(BudgetState, 1, 2)` migrator if breaking Pydantic Literal change required

## §8 Open architecture risks (severity + mitigation)

| Risk | Severity | Mitigation |
|---|---|---|
| Periodic sweep latency window — 30s vs spike (cost runs $400 in 30s window theoretically possible if tenant rebursts grader Round 2) | LOW | D5 cement balanced delay vs overhead. Pre-flight is primary defense; sweep is post-facto safety net. Reduce env var override available if needed |
| Pricing snapshot drift — model price changes mid-run | LOW | LiteLLM canonical sync daily. Cost_estimator queries latest snapshot. Drift bounded ≤24h. Production cost_estimator same risk profile |
| Env var collision — caller sets `SALES_AGENT_EVAL_BUDGET_CAP_DISABLE=1` in CI accidental | MEDIUM | CI strict — env var NEVER set in CI workflow (.github/workflows/eval-*.yml). Local dev only. Guideline 05 forbids set in CI |
| `_DISABLE` flag accidental in shared CI environment | MEDIUM | CI workflows explicit `unset SALES_AGENT_EVAL_BUDGET_CAP_DISABLE` step. Auditor Cat 13/14 verify env hygiene |
| asyncio Task lifecycle — leak if orchestrator forgets cancel | MEDIUM | Pattern documented (try/finally pattern in §3.4 docstring + 05-guidelines.md). Test verifies orchestrator cleanup. structlog event on cancel |
| Process exit code 2 distinct semantics — CI tooling MAY swallow non-zero | LOW | Story G CI gate explicit `if [ $exit_code -eq 2 ]; then ... fi` branch. Guideline lock |
| Story E cost_usd_total column drift if Story E reframes schema | LOW | Story E schema cement v1 ratified Chris 2026-05-08. Story H built post-Story E build (hard blocker). Schema mismatch detected at integration test failure |
| Cross-eval-story BudgetGuard pattern emerges — LIFT-TO-SHARED candidate | LOW (YAGNI) | Story I extends additively post-ship. If cross-story pattern emerges, refactor to shared post-Story I (YAGNI now) |
| Production BudgetGuard scope creep — eval guard accidentally consumed by production code | MEDIUM | Path scope: `backend/tests/agentic_evals/sales_agent/budget/` (test-infra namespace). Arch fitness gate `test_no_test_infra_imports_from_production.py` (existing) catches |
| MV stale (mv_daily_llm_cost_per_tenant_v2 not used Story H) — production guard pattern; eval guard direct table query | NONE | Story H queries `eval_simulator_llm_call` directly (not MV). No staleness window. Cost rows synced post-call by Story B observability context |

## §9 Out of scope (anti-creep guards consolidados)

- ❌ Per-tenant runtime cost cap (production BudgetGuard owns — `shared/billing/`)
- ❌ Per-tenant eval cost (eval is global suite-scoped, NOT per-tenant)
- ❌ Slack/email notifications (console + structlog only)
- ❌ Auto-scaling cap based on model price changes (manual env var update)
- ❌ Cost projection ML (rule-based estimator suficiente — over-estimate strict)
- ❌ Refund/chargeback handling (NOT eval scope)
- ❌ Cost optimization recommendations (NOT eval scope)
- ❌ Per-rubric cap differentiation (per-grade tier cubre — Story E rubrics aggregate to grader bucket)
- ❌ Tocar Story B `eval_simulator_llm_call` schema (read-only — Stories B own)
- ❌ Tocar Story E `eval_simulator_grade` schema (read-only — Stories E own)
- ❌ Tocar Story F aggregator code (consume cascade only — `unconverged: true` flag set on partial run)
- ❌ Modificar `core/config.py` defaults (env vars only — `.claude/rules/anti-default-flip-audit.md`)
- ❌ FE component for visualization (Story H BE-only service-story)
- ❌ Streamlit dashboard (separate observability story)
- ❌ Modificar production `BudgetGuard` shared/billing (different paradigm cement)
- ❌ Modificar `simulator/__init__.py` beyond H9 expand 8→9 (single `check_budget_before_call` addition)
- ❌ Tocar `_internal/` simulator files (Story B/C cement — Story H EDITS solo `schema_migrations.py` anchor entry append + `simulator/__init__.py` H9 expand)
- ❌ LLM calls of any kind (read-only invariant cement D-BE-8)
- ❌ MV-backed cost queries (production paradigm — eval-only Story H direct table queries)

## §10 Research notes (state-of-the-art mayo 2026 — DATE-AWARE)

- **Source URL**: [Super Fast Python — Asyncio Periodic Task](https://superfastpython.com/asyncio-periodic-task/) accessed 2026-05-08
  - **Library version**: Python 3.12 stdlib (asyncio canonical)
  - **Key takeaway**: `asyncio.create_task()` + async loop forever pattern is canonical mayo 2026. `aiojobs` library considered for production scheduler but **YAGNI** for Story H (single Task per run, simple lifecycle).
  - **Why this pattern over alternatives**: stdlib only (zero dependencies), simple cancel semantics, well-understood by builders, Python 3.12 improvements (TaskGroup, asyncio.timeout) not required for periodic sweep simple pattern.

- **Source URL**: [LiteLLM Pricing Calculator](https://docs.litellm.ai/docs/proxy/pricing_calculator) + [LiteLLM Cost Per Token](https://docs.litellm.ai/docs/completion/token_usage) accessed 2026-05-08
  - **Library version**: LiteLLM ≥ v1.50 (canonical sync via Story B `model_pricing_snapshot`)
  - **Key takeaway**: `cost_per_token` + `token_counter` + `completion_cost` are canonical pre-call estimators. Story H uses **input_tokens passed by caller** (caller tokenizer-counted) instead of LiteLLM `token_counter` — eval-only context expects exact spec input_tokens (avoid double-tokenization risk; tokenizer mismatch caller vs LiteLLM bridge would over-/under-estimate inconsistently).
  - **Why this pattern over alternatives**: same `model_pricing_snapshot` shared table accessed (anti-duplication respect at data layer); caller responsibility for input_tokens fits eval test-infra context (test fixtures can mock caller tokens deterministically).

- **Knowledge cutoff disclosure**: Topic researched live on 2026-05-08 via WebSearch — Opus 4.7 cutoff is Jan 2026. No state-of-the-art shifts mid-2026 detected for either pattern. Both canonical references stable.

## §11 Capability YAML + module narrative + downstream regression rule updates required (post-merge by /pm)

**Files to update post-merge (NOT builder action — flagged in T-6 ticket):**

1. `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` — append eval block fields per §3.9 (budget_caps_per_tier + budget_summary_path + budget_disable_flag + cost_baseline_per_run_usd + story_h_introduced + story_h_merged_at + story_h_test_coverage list)

2. `docs/product/modules/sales-agent.md` — narrative addition 1-2 sentences (post-merge by /pm):
   > "Eval suite cost-budget cap (Story H, sales-agent-eval-cost-budget-cap, ratified 2026-05-08) — multi-tier guard (per_trial / per_grade / per_run / per_bucket) consume Story B `eval_simulator_llm_call.cost_usd` + Story E `eval_simulator_grade.cost_usd_total` real-time. Pre-flight estimation over-estimate strict + 30s periodic sweep post-facto detection. Defense-in-depth vs runaway cost / direct LLM call bypass. CI exit code 2 distinct from functional regression."

3. `.claude/rules/auditor-downstream-regression.md` — append SSoT entries:
   - `backend/tests/agentic_evals/sales_agent/budget/guard.py` → downstream_test_targets `[test_budget_guard.py, test_budget_state.py, test_sweep.py, test_eval_llm_calls_use_budget_guard.py, test_budget_state_schema_complete.py]`
   - `backend/tests/agentic_evals/sales_agent/budget/_internal/cost_estimator.py` → idem
   - `backend/tests/agentic_evals/sales_agent/budget/_internal/sweep.py` → idem
   - `backend/tests/agentic_evals/sales_agent/budget/_schema.py` → idem + `test_budget_state_schema_complete.py`

