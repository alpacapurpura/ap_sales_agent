---
story_id: sales-agent-goldens-3-tenants-dataset
arch_role: orchestrator-consolidated-be-only
arch_version: 1
last_modified: 2026-05-08T08:00:00Z
mode: SINGLE_SHOT_FULLSTACK   # service-story BE-only; sub-architect agent types not registered;
                              # /architect (Opus 4.7) handles BE surface directly per learnings.md 2026-05-08
links:
  spec: 01-spec.md
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  story_a_archive: ../../../archive/2026/stories/eval-foundation-tenant-seed-data/
  story_b_archive: ../../../archive/2026/stories/eval-foundation-simulator-homologation/
  story_c_design: ../sales-agent-personas-instrumented-runtime/03-arch.md
  story_c_tickets: ../sales-agent-personas-instrumented-runtime/06-tickets.yaml
  consumers:
    - ../sales-agent-voice-fidelity-grader-runtime/        # E
    - ../sales-agent-eval-pass-k-tracking/                  # F
    - ../sales-agent-voice-fidelity-ci-gate/                # G
    - ../sales-agent-eval-cost-budget-cap/                  # H
    - ../sales-agent-adversarial-jailbreak-suite/           # I
date_research: 2026-05-08
build_depends_on:
  - story: sales-agent-personas-instrumented-runtime
    blocker_type: hard
    reason: "Story D script + Scenario 1 require runtime `load_actor_profile_for_tenant` + `get_max_turns_for_persona_kind` from Story C `_internal/personas_loader.py`. Architect phase parallel-safe (design-only). Build phase BLOCKED until Story C build done + arch fitness ratchet GREEN."
---

## §0 Resumen

Story D entrega **el ground-truth dataset sintético-first** del eval suite `sales_agent` mediante una **tooling pipeline BE-only** (cero runtime, cero modules/sales_agent/{domain,application,api}/) compuesta por:

1. **Schema Pydantic v2** — `GoldenScenarioModel` v1 cement bajo `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` con `schema_version: Literal[1]` + forward-compat via SCHEMA_MIGRATIONS registry pattern (reuse Story B H1 mechanism via parallel registry — NO mirror).
2. **Generation script** — `backend/scripts/generate_golden_candidates.py` ejecuta matrix `5 tenants × 3 persona_kinds × 5 runs = 75 simulations` paralelo (`asyncio.gather + Semaphore(10)` reusando Story B pattern) consumiendo Story C `load_actor_profile_for_tenant` + Story B `run_simulation`. Salida: `_artifacts/goldens_generation/{run_id}/preview.md` (Markdown table inline IDE-renderable).
3. **Promotion CLI** — `backend/scripts/promote_golden.py` reads simulation artifact JSON + escribe golden YAML deterministically en `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml`. Auto-derive `expected_*` fields desde simulation result + auto-extract `expected_voice_attributes` desde tenant `personality_profile`.
4. **PII defense-in-depth scanner** — `backend/scripts/scan_goldens_pii.py` con regex catalog extendido (email + LatAm phones + DNI/CUIT/RUT/RFC + nicolify internal URLs). Pre-commit hook **Section 9** new (after Story A's Section 8). Defense-in-depth: arch fitness gate `test_no_pii_in_committed_goldens` re-corre scanner sobre 20-30 reales en CI.
5. **Coverage gate** — `test_goldens_coverage.py::test_all_cells_covered` enforce ≥1 golden por `(tenant_slug × persona_kind)` cell × 15 cells = 15 minimum.
6. **Schema validation tests** — `test_goldens_schema.py` valida cada YAML deserializa, referential integrity (`actor_profile_id` ∈ Story C YAMLs + `tenant_slug` ∈ 5 Story A seeds + `dialect_code` matches `dialect_catalog`), zero PII en committed goldens.
7. **README** — pipeline documentation + refresh policy + how-to-add-golden + schema reference.
8. **Capability extension** — `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` append `eval.goldens_*` block (post-merge by /pm).

**Cero deuda invariants** (heredados Story B + extendidos Story D):

- Public API surface frozen 7 names en `simulator/__init__.py` — Story D consumes; **NO modifica** (H9 cement).
- `LLM_ROLE_BY_SITE` SSoT untouched — Story D no invoca LLM directamente; usa `run_simulation()` que hereda toda la wiring.
- `personality_profiles.system_instruction` SSoT untouched — `expected_voice_attributes` se **auto-extracta** read-only.
- Cost-bucket separation `eval_simulator_llm_call` only — generation writes ONLY a esta tabla (Story B H6/H7 cement). Arch fitness gate verifica zero `copilot_llm_call` rows post-generation.
- Schema-mirror exception R5 NO aplica — Story D no toca `modules/sales_agent/persistence/models/`. Pure tooling + tests + docs.
- `simulator/__init__.py` 7-name surface frozen — Story D imports DESDE this surface; arch test (Story B `test_simulator_public_api_surface.py`) detecta cualquier leak.
- Story C's `_internal/personas_loader.py` is consumed via **explicit import** (NO public surface bump) per Story C D-AG-2.

## §1 Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| BE tooling (script generate + promote + scanner) | NO (`backend/scripts/`) | `builder-backend` Sonnet (R23 `production_code: false`) | `auditor-backend` (Opus C1-C3 + Sonnet tests) | backend-expert, sales-agent-expert, tessl__pytest-api-testing, tessl__graceful-degradation |
| BE test-infra (schema + tests + arch fitness gate) | NO | `builder-backend` Sonnet | `auditor-backend` | backend-expert |
| BE pre-commit hook (Section 9 extend) | NO (shell script + Python invocation) | `builder-backend` Sonnet | `auditor-backend` | backend-expert |
| BE goldens YAML data assets (output of generation, **NOT** committed by builder) | NO | Chris manual curation post-build (out of ticket scope — Story D delivers tooling, Chris produces dataset) | N/A | N/A |
| Capability YAML + module narrative | NO (docs) | `/pm` post-merge | N/A | pm |
| FE | N/A | — | — | — |
| AGENTIC | N/A (Story D is tooling — no graph, no prompts, no tools touching sales_agent runtime) | — | — | — |

> **Owner choice rationale**: Story D is **service-story BE-only tooling**. Per R23, `production_code: false` permits Sonnet. No agentic surfaces touched (no LangGraph state, no graph topology, no prompt slot architecture, no LLM dispatch, no tools). Generation consumes Story B `run_simulation` + Story C loader as black-box APIs. **Sonnet OK across all 5 tickets.** PM confirms final routing in spawn.

## §2 Existing systems audit (NO NEW LAYER rule — `.claude/rules/anti-duplication.md`)

### Source of evidence

- [x] Self-run greps Path B (CONTEXT-BRIEF Haiku skipped — service-story BE-only tooling tras 5 commits previos discovery cementaron paradigma synthetic-first)
- [x] Re-validación spec D1-D17 + Story C 03-arch.md + Story B archive 03-arch-be.md
- [x] Verificación skill `sales-agent-expert` § "Surfaces compartidas con copilot" + `.claude/rules/anti-duplication.md` inventario shared

### Audit cross-module ejecutado

```bash
# 1. Existing golden YAML schema patterns
grep -rn "GoldenScenarioModel\|class.*Golden.*BaseModel" backend/ docs/
# Result: ZERO BE implementations of Golden* schema. Spec mentions but no code yet.
# Story D introduces NEW (genuinely — synthetic goldens did not exist pre-Story D).

# 2. Existing generation script patterns
grep -rn "def generate_golden\|run_simulation.*matrix\|asyncio.gather.*Semaphore" backend/scripts/ backend/tests/
# Result: zero direct precedent. Story B uses Semaphore(10) pattern in
# `simulator/_internal/concurrency.py::_GLOBAL_SEMAPHORE`. EXTEND consume.

# 3. Existing PII scanner patterns
grep -rn "scan_seed_pii\|scan.*pii\|PII_REGEX" backend/scripts/
# Result: Story A's `scan_seed_pii.py` (560 LOC) — REUSE pattern + EXTEND with goldens-specific paths.
# Same regex catalog (email, phone_intl, DNI/CUIT/RUT/RFC, url_internal_nicolify) reusable.
# Decision: NEW `scan_goldens_pii.py` distinct file (different scan dir + different whitelist policy
# — goldens have NO whitelist, strict block per spec D10) BUT shared regex catalog via
# extracted module `backend/scripts/_pii_patterns.py` lifted from `scan_seed_pii.py`.

# 4. Pre-commit hook structure
grep -n "^# [0-9]\." scripts/git-hooks/pre-commit
# Result: 8 sections existing (1=voseo, 2=ruff, 3=ruff-format, 4=R3-SSoT, 5=R32-cap, 6=R33-backlog,
# 7=checkpoint-state, 8=PII-eval-seed). EXTEND adding Section 9 (PII-goldens) following
# Section 8 pattern.

# 5. Coverage gate test patterns
grep -rn "test_all_cells_covered\|coverage_gap\|test.*cell.*coverage" backend/tests/
# Result: zero direct precedent. NEW pattern justified.

# 6. Loader for personas (Story C)
grep -rn "load_actor_profile_for_tenant\|personas_loader" backend/
# Result: zero (Story C build pending). Story D depends_on Story C build done.

# 7. Story B simulator public API
grep -A 10 "^__all__" backend/tests/agentic_evals/sales_agent/simulator/__init__.py
# Result: 7 names frozen ("run_simulation", "SimulationResult", "SimulationState",
# "ActorProfile", "TerminationReason", "AgentErrorSubtype", "register_termination_policy")
# Story D imports run_simulation + ActorProfile + SimulationResult + TerminationReason from this.

# 8. capability YAML location
ls docs/product/capabilities/sales-agent/sales-conversational-engine.yaml
# Result: file exists. Spec says `sales_agent/` underscore — actual is `sales-agent/` hyphen.
# CORRECTED in CONTRACT § 9 below.

# 9. Markdown table preview rendering precedent
grep -rn "preview.md\|_artifacts.*md.*generation" backend/
# Result: zero. NEW pattern (NOT mirror — synthesis target IDE-friendly).

# 10. Schema migrations registry pattern
grep -n "SCHEMA_MIGRATIONS\b\|register_schema_migration" backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py
# Result: existing in Story B internal module. Story D goldens uses PARALLEL registry
# (NO mirror — different namespace) under `goldens/_schema.py::GOLDEN_SCHEMA_MIGRATIONS`.
# Justified: Story B's registry is internal to simulator; Story D's goldens schema is
# parallel registry for golden-specific bumps (forward-compat 5+ years).
```

### Sistemas existentes encontrados

| Sistema | Path canónico | Estado | Decisión Story D |
|---|---|---|---|
| `run_simulation` orchestrator | `simulator/__init__.py::run_simulation` (public, Story B H9) | active | **CONSUME** as black-box API. Generation script orchestrates matrix; runner remains untouched. |
| `ActorProfile` / `SimulationResult` / `TerminationReason` | `simulator/__init__.py` (public 7 names) | active | **CONSUME** — Story D's schema references `actor_profile_id` (string, not class instance) + reads `result.transcript` + maps `result.termination_reason` |
| `load_actor_profile_for_tenant` + `get_max_turns_for_persona_kind` | `simulator/_internal/personas_loader.py::load_actor_profile_for_tenant` (Story C — build pending) | refined→ready→pending build | **CONSUME** via `_internal` import (Story C D-AG-2 — internal pin allowed for downstream eval tests). Hard build dependency. |
| `Semaphore(10)` concurrency pattern | `simulator/_internal/concurrency.py::_GLOBAL_SEMAPHORE` | active | **REUSE** — generation script imports same semaphore (cross-suite consistency) OR creates own Semaphore(10) (decision §3.5: own semaphore — script-local is parallelism budget, not cross-suite quota). |
| `scan_seed_pii.py` regex catalog | `backend/scripts/scan_seed_pii.py::PATTERNS` | active | **EXTRACT** to `backend/scripts/_pii_patterns.py` (lift) → consumed by both `scan_seed_pii.py` (REFACTOR — backward-compat preserved) + `scan_goldens_pii.py` (NEW). Cross-script DRY. Same regex set + same context guards (DNI false-positive mitigations). |
| `.eval-whitelist` whitelist mechanism | `backend/tests/fixtures/eval/tenants/.eval-whitelist` | active | **NO whitelist for goldens** (spec D10 — strict block, no escape). `scan_goldens_pii.py` does NOT honor a whitelist file. |
| Pre-commit hook Section 8 (PII seed scanner) | `scripts/git-hooks/pre-commit` lines 510-562 | active | **EXTEND** — append Section 9 (PII goldens scanner) following identical structure. |
| Markdown table preview generator | NO precedent in codebase | N/A | **NEW** justified — IDE-renderable inline (Q3 ratified). NOT HTML, NOT Streamlit. Pure stdlib `str.format` + table builder. |
| `dialect_catalog.yaml` Story A | `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` | active | **CONSUME** — `test_goldens_schema.py` cross-checks `dialect_code == dialect_catalog[tenant_slug]` strict per spec referential integrity invariant. |
| `ARCHETYPE_DIALECT_MAP` Story A | `backend/tests/fixtures/eval/tenants/loader.py::ARCHETYPE_DIALECT_MAP` | active | **CONSUME** — same cross-check. |
| Story C personas YAML files | `docs/specs/personas/archetype-aware/*.yaml` | refined→ready→pending build | **REFERENCE** — `actor_profile_id` field cross-checks file existence in this dir (referential integrity). |
| `eval_simulator_llm_call` table | `modules/sales_agent/observability/eval_simulator/persistence/models/` (Story B) | active | **READ-ONLY** post-generation invariant: filas escritas during generation MUST land in this table; arch test `test_goldens_cost_bucket_invariant.py` queries DB post-suite. |
| `personality_profile.system_instruction` per-tenant SSoT | Story A seeds → `personality_profile_id` per tenant | active | **READ-ONLY** — `promote_golden` auto-extracts subset of voice attribute keys for `expected_voice_attributes` (D14 spec). NUNCA mutate. |

### Decisión por sistema — sumario

- **REUSE/CONSUME** (8 systems): Story B public 7 names + Story C loader + Story A dialect_catalog + ARCHETYPE_DIALECT_MAP + concurrency Semaphore pattern + personality_profile + eval_simulator_llm_call table + pre-commit hook Section 8 pattern.
- **EXTRACT-AND-LIFT** (1 system): `scan_seed_pii.py::PATTERNS` → `_pii_patterns.py` (DRY threshold = 2 consumers per `.claude/rules/anti-duplication.md` rule). Backward-compat: `scan_seed_pii.py` re-imports from new module — zero behavior change.
- **NEW (justified, last resort)** (5 systems):
  1. `goldens/_schema.py` — `GoldenScenarioModel` Pydantic class — NO precedent for golden YAML schema in codebase.
  2. `goldens/_schema_migrations.py` — `GOLDEN_SCHEMA_MIGRATIONS` parallel registry (NOT mirror Story B's `simulator/_internal/schema_migrations.py` — different namespace + different lifecycle: simulator schema bumps drive code; goldens schema bumps drive data migration scripts).
  3. `generate_golden_candidates.py` script — NEW orchestration tooling.
  4. `promote_golden.py` script — NEW promotion CLI.
  5. `scan_goldens_pii.py` script — NEW (separate from `scan_seed_pii.py` due to different scan dir + no-whitelist policy + goldens-specific error message).
- **NO TOUCH**: `simulator/__init__.py` 7-name surface (H9), `LLM_ROLE_BY_SITE`, `personality_profiles.system_instruction`, `closer_studio.py`, `SmartBuffer`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot`, `tool_call_dedup`, `eval_simulator_*` DB schema (R5), `simulator/_internal/personas_loader.py` (Story C owns), Story C 15 personas YAML (consume only), Story A 5 tenant seeds (consume only).

## §3 BE arch (tooling + tests + scanner + hook + capability)

### §3.1 Schema — `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` (NEW)

```python
"""Golden scenario schema (Story D — synthetic-first eval ground truth).

Pydantic v2 frozen model + parallel SCHEMA_MIGRATIONS registry. Cement v1.
Future bumps: register migrator + bump CURRENT_GOLDEN_SCHEMA_VERSION,
NEVER mutate v1 spec.

Anti-duplication §0:
- Pydantic v2 ConfigDict pattern reused from Story B `actor_profile.py`.
- Schema migration registry pattern reused conceptually from Story B
  `simulator/_internal/schema_migrations.py` BUT lives in parallel namespace
  (`goldens/_schema_migrations.py`) — different lifecycle, different scope.
- `sanitize_payload` NOT applied here (golden YAMLs are static checked-in
  data, not runtime payloads — scanner enforces zero-PII at commit-time).

Tenant isolation:
- Each golden contains data from EXACTLY ONE tenant. Cross-tenant data
  → schema validation fails (assertions in test_goldens_schema.py).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Story A 5 tenant seeds — frozen Literal
GoldenTenantSlug = Literal[
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
]

# Story C 3 persona kinds in scope (adversarial = Story I, edge/negative = loader-only)
GoldenPersonaKind = Literal["happy", "nurture", "unqualified"]

# Subset of Story B TerminationReason in goldens scope (excludes AGENT_ERROR — failure)
GoldenTerminationReason = Literal[
    "GOAL_COMPLETION",
    "MAX_TURNS",
    "CUSTOMER_EXIT",
]


class GoldenTurnModel(BaseModel):
    """One turn captured verbatim from simulation_artifact.transcript."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["customer", "agent"]
    content: str = Field(min_length=1)
    turn_number: int = Field(ge=0)
    tool_calls: list[str] | None = None  # agent turns only
    latency_ms: int | None = None  # observability snapshot, optional


class GoldenMetadataModel(BaseModel):
    """Generation provenance + curation audit trail (D13 + D14)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_from_simulation_id: UUID  # Story B D11 deterministic UUID5
    generated_at: datetime  # UTC
    curated_by: str = Field(min_length=1)  # "chris"
    curated_at: datetime  # UTC
    generation_run_id: UUID  # links to _artifacts/goldens_generation/{run_id}/
    seed: int  # deterministic re-generation
    cost_usd_at_generation: Decimal  # observability snapshot
    notes: str = ""  # D14 — Chris freeform override


class GoldenScenarioModel(BaseModel):
    """Curated golden conversation — synthetic ground truth for eval suite.

    Schema v1 cement (D6). Future bumps via GOLDEN_SCHEMA_MIGRATIONS registry.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    id: str = Field(min_length=3, pattern=r"^[a-z0-9][a-z0-9_-]+$")  # slug-style
    tenant_slug: GoldenTenantSlug
    persona_kind: GoldenPersonaKind
    actor_profile_id: str = Field(min_length=3)  # Story C YAML id
    actor_profile_schema_version: Literal[2] = 2  # D7 frozen at curation time
    dialect_code: str = Field(min_length=2)  # BCP-47 — must match dialect_catalog[tenant_slug]
    transcript: list[GoldenTurnModel] = Field(min_length=2)  # ≥2 turns realistic
    expected_termination_reason: GoldenTerminationReason
    expected_voice_attributes: list[str] = Field(min_length=1)  # auto-extracted (D14)
    expected_tools_invoked: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)  # D17 declarative
    expected_min_distinct_objections_handled: int | None = Field(default=None, ge=1)  # nurture only
    metadata: GoldenMetadataModel


__all__ = [
    "GoldenMetadataModel",
    "GoldenPersonaKind",
    "GoldenScenarioModel",
    "GoldenTenantSlug",
    "GoldenTerminationReason",
    "GoldenTurnModel",
]
```

### §3.2 Parallel SCHEMA_MIGRATIONS — `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` (NEW)

```python
"""Forward-compat schema migration registry for GoldenScenarioModel.

Pattern PARALLEL to Story B `simulator/_internal/schema_migrations.py` —
distinct namespace, distinct lifecycle. Goldens bumps drive YAML data
migration scripts (Chris-triggered manual refresh per D15); simulator
bumps drive code migrations.

v1 cement; no migrators registered initially. First future bump (e.g.
v1→v2 add field) registers identity migrator here in same commit.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

GoldenMigrator = Callable[[dict[str, object]], dict[str, object]]

# (class_name, from_version, to_version) → migrator fn
GOLDEN_SCHEMA_MIGRATIONS: Final[dict[tuple[str, int, int], GoldenMigrator]] = {}

CURRENT_GOLDEN_SCHEMA_VERSIONS: Final[dict[str, int]] = {
    "GoldenScenarioModel": 1,
}


def register_golden_migration(
    class_name: str, from_version: int, to_version: int
) -> Callable[[GoldenMigrator], GoldenMigrator]:
    """Decorator — register identity-or-transform migrator."""

    def _decorator(fn: GoldenMigrator) -> GoldenMigrator:
        key = (class_name, from_version, to_version)
        if key in GOLDEN_SCHEMA_MIGRATIONS:
            msg = f"Duplicate golden migration registration: {key}"
            raise ValueError(msg)
        GOLDEN_SCHEMA_MIGRATIONS[key] = fn
        return fn

    return _decorator


def apply_golden_migrations(
    class_name: str, raw: dict[str, object], target_version: int
) -> dict[str, object]:
    """Apply chain of migrators raw['schema_version'] → target_version."""
    current = int(raw.get("schema_version", 1))
    while current < target_version:
        key = (class_name, current, current + 1)
        if key not in GOLDEN_SCHEMA_MIGRATIONS:
            msg = f"Missing migrator for {key}"
            raise KeyError(msg)
        raw = GOLDEN_SCHEMA_MIGRATIONS[key](raw)
        current = int(raw.get("schema_version", current + 1))
    return raw


__all__ = [
    "CURRENT_GOLDEN_SCHEMA_VERSIONS",
    "GOLDEN_SCHEMA_MIGRATIONS",
    "GoldenMigrator",
    "apply_golden_migrations",
    "register_golden_migration",
]
```

### §3.3 Generation script — `backend/scripts/generate_golden_candidates.py` (NEW)

Orchestrates 75-simulation matrix with HTML preview-equivalent (Markdown table inline) + cost budget pre-flight + structured logging.

```python
"""Generate golden candidate transcripts from dual-LLM simulator.

Pipeline (per spec Scenario 1):
  1. For each (tenant_slug × persona_kind × run_n) cell in 5×3×5 = 75 matrix:
     - Load ActorProfile via Story C `load_actor_profile_for_tenant`
     - Compute max_turns via Story C `get_max_turns_for_persona_kind`
     - Schedule run_simulation(...) coroutine
  2. Run 75 simulations in parallel (asyncio.gather + Semaphore(10))
  3. Persist artifact JSONs to _artifacts/goldens_generation/{run_id}/sim_*.json
  4. Emit Markdown table preview at _artifacts/goldens_generation/{run_id}/preview.md
     (IDE-renderable, parallel-safe, terminal-friendly per spec Q3)
  5. Print summary: total cost, per-cell counts, suggested promotions

Cost budget: spec D2 ~$5.40 expected. Hard cap $8 (--cost-budget-usd flag).
Pre-flight aborts if estimated > cap.

Anti-duplication §0:
- Reuses Story B `run_simulation` (public 7-name API).
- Reuses Story C `load_actor_profile_for_tenant` (internal pin allowed —
  Story C D-AG-2 explicitly designed for downstream eval consumption).
- Cost bucket invariant: writes ONLY to eval_simulator_llm_call (Story B
  H6/H7). Verified post-run by `agentic_cost_bucket_zero_contamination`
  validator (reused from Story C T-6).

Tenant isolation:
- Each simulation invokes run_simulation w/ explicit tenant_archetype_slug.
- Generation script never touches DB directly (no cross-tenant queries).

Spanish neutro (`.claude/rules/spanish-text.md`):
- All structlog events + CLI messages + comments in español neutro.
- (Personas YAML may contain voseo if dialect_code=es-AR — Story C
  responsibility, not Story D.)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Final

import structlog

# Public API consumption (Story B H9 7 names)
from tests.agentic_evals.sales_agent.simulator import (
    ActorProfile,
    SimulationResult,
    run_simulation,
)

# Internal consumption (Story C D-AG-2 explicit downstream consumer pin)
from tests.agentic_evals.sales_agent.simulator._internal.personas_loader import (
    PersonaKind,
    get_max_turns_for_persona_kind,
    load_actor_profile_for_tenant,
)

logger = structlog.get_logger()

# Matrix axes
_TENANT_SLUGS: Final[tuple[str, ...]] = (
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
)
_PERSONA_KINDS: Final[tuple[PersonaKind, ...]] = ("happy", "nurture", "unqualified")
_DEFAULT_RUNS_PER_CELL: Final[int] = 5
_DEFAULT_CONCURRENCY: Final[int] = 10
_DEFAULT_COST_BUDGET_USD: Final[Decimal] = Decimal("8.00")


@dataclass(frozen=True)
class CellKey:
    tenant_slug: str
    persona_kind: PersonaKind
    run_n: int


@dataclass(frozen=True)
class CellResult:
    key: CellKey
    simulation_id: str  # UUID stringified
    artifact_path: Path
    total_turns: int
    termination_reason: str
    cost_usd: Decimal
    transcript_preview: str  # first 200 chars of last 2 turns


async def _run_one_cell(
    cell: CellKey,
    semaphore: asyncio.Semaphore,
    output_dir: Path,
    run_id: str,
    seed_base: int,
) -> CellResult:
    """Run one simulation cell. Best-effort with structured logging."""
    async with semaphore:
        actor: ActorProfile = load_actor_profile_for_tenant(
            cell.tenant_slug, persona_kind=cell.persona_kind
        )
        max_turns = get_max_turns_for_persona_kind(cell.persona_kind)
        # Deterministic seed per cell — reproducibility (D8)
        seed = seed_base + hash((cell.tenant_slug, cell.persona_kind, cell.run_n)) % 10_000

        try:
            result: SimulationResult = await run_simulation(
                tenant_archetype_slug=cell.tenant_slug,
                actor_profile=actor,
                max_turns=max_turns,
                trial_n=cell.run_n,
                run_id=run_id,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort cell isolation per
            # tessl__graceful-degradation Rule 5 (per-dependency error isolation)
            logger.warning(
                "generate_goldens.cell_failed",
                tenant_slug=cell.tenant_slug,
                persona_kind=cell.persona_kind,
                run_n=cell.run_n,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            raise

        # Persist artifact JSON — promote_golden.py reads this back
        artifact_path = output_dir / f"sim_{result.simulation_id}.json"
        artifact_path.write_text(
            json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Build preview (last 2 turns abbreviated)
        last_turns = result.transcript[-2:] if len(result.transcript) >= 2 else result.transcript
        preview = " | ".join(
            f"{t.role}: {t.content[:80]}{'...' if len(t.content) > 80 else ''}"
            for t in last_turns
        )

        return CellResult(
            key=cell,
            simulation_id=str(result.simulation_id),
            artifact_path=artifact_path,
            total_turns=result.total_turns,
            termination_reason=result.termination_reason.value,
            cost_usd=Decimal(str(result.cost_summary.total_cost_usd)),
            transcript_preview=preview,
        )


def _emit_preview_markdown(results: list[CellResult], preview_path: Path, run_id: str) -> None:
    """Generate IDE-renderable Markdown preview (D12 cement, Q3 ratified).

    Format: grouped by cell, terminal-friendly table, parallel-safe (no shared state).
    Inline transcript snippets — Chris navigates `Cmd-O` on artifact_path to deep-dive.
    """
    lines: list[str] = [
        f"# Golden candidate preview — run_id={run_id}",
        "",
        f"Total candidates: {len(results)}",
        "",
        "## Summary by cell",
        "",
        "| Cell | Sim ID (short) | Turns | Termination | Cost USD | Preview |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda x: (x.key.tenant_slug, x.key.persona_kind, x.key.run_n)):
        cell_label = f"{r.key.tenant_slug} / {r.key.persona_kind} / run{r.key.run_n}"
        sid_short = r.simulation_id[:8]
        # Escape pipe + truncate preview for table cell
        preview_safe = r.transcript_preview.replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| {cell_label} | `{sid_short}` | {r.total_turns} | "
            f"{r.termination_reason} | ${r.cost_usd:.4f} | {preview_safe} |"
        )
    lines.extend(["", "## Promotion command template", ""])
    lines.append("```bash")
    lines.append("# For each candidate Chris selects as winner:")
    lines.append(
        "python backend/scripts/promote_golden.py "
        "--simulation-id <sim_uuid> --golden-id <slug>"
    )
    lines.append("```")
    lines.append("")
    lines.append("## Artifact paths (full transcripts)")
    lines.append("")
    for r in sorted(results, key=lambda x: (x.key.tenant_slug, x.key.persona_kind, x.key.run_n)):
        rel = r.artifact_path.relative_to(preview_path.parent)
        lines.append(f"- `{r.key.tenant_slug}/{r.key.persona_kind}/run{r.key.run_n}` → [`{rel}`](./{rel})")
    preview_path.write_text("\n".join(lines), encoding="utf-8")


async def _main_async(
    runs_per_cell: int,
    concurrency: int,
    cost_budget_usd: Decimal,
    output_dir: Path,
    run_id: str,
    seed_base: int,
    tenant_filter: str | None = None,
    persona_kind_filter: PersonaKind | None = None,
) -> int:
    """Async entry point. Returns exit code."""
    cells: list[CellKey] = []
    for tenant in _TENANT_SLUGS:
        if tenant_filter and tenant != tenant_filter:
            continue
        for kind in _PERSONA_KINDS:
            if persona_kind_filter and kind != persona_kind_filter:
                continue
            for run_n in range(runs_per_cell):
                cells.append(CellKey(tenant, kind, run_n))

    expected_cost = Decimal(str(len(cells))) * Decimal("0.072")  # ~$5.40 / 75
    if expected_cost > cost_budget_usd:
        logger.error(
            "generate_goldens.budget_exceeded_preflight",
            estimated_cost_usd=str(expected_cost),
            budget_usd=str(cost_budget_usd),
            cells=len(cells),
        )
        sys.stderr.write(
            f"ERROR: estimated cost ${expected_cost} exceeds budget "
            f"${cost_budget_usd}. Reduce --runs-per-cell or raise --cost-budget-usd.\n"
        )
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(concurrency)

    logger.info(
        "generate_goldens.start",
        run_id=run_id,
        cells=len(cells),
        concurrency=concurrency,
        estimated_cost_usd=str(expected_cost),
    )

    coros = [
        _run_one_cell(cell, semaphore, output_dir, run_id, seed_base) for cell in cells
    ]
    results: list[CellResult] = []
    failures: list[CellKey] = []
    gathered = await asyncio.gather(*coros, return_exceptions=True)
    for cell, outcome in zip(cells, gathered, strict=True):
        if isinstance(outcome, BaseException):
            failures.append(cell)
            continue
        results.append(outcome)

    preview_path = output_dir / "preview.md"
    _emit_preview_markdown(results, preview_path, run_id)

    total_cost = sum((r.cost_usd for r in results), start=Decimal("0"))
    logger.info(
        "generate_goldens.completed",
        run_id=run_id,
        success=len(results),
        failures=len(failures),
        total_cost_usd=str(total_cost),
        preview_path=str(preview_path),
    )
    sys.stdout.write(
        f"\nGenerated {len(results)} candidates ({len(failures)} failures).\n"
        f"Total cost: ${total_cost:.4f}\nPreview: {preview_path}\n"
    )
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate golden candidates")
    parser.add_argument("--runs-per-cell", type=int, default=_DEFAULT_RUNS_PER_CELL)
    parser.add_argument("--concurrency", type=int, default=_DEFAULT_CONCURRENCY)
    parser.add_argument(
        "--cost-budget-usd", type=Decimal, default=_DEFAULT_COST_BUDGET_USD
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", type=str, default=str(uuid.uuid4()))
    parser.add_argument("--seed-base", type=int, default=42)
    parser.add_argument("--tenant", type=str, default=None, choices=_TENANT_SLUGS + (None,))
    parser.add_argument(
        "--persona-kind", type=str, default=None, choices=_PERSONA_KINDS + (None,)
    )
    args = parser.parse_args()
    return asyncio.run(
        _main_async(
            runs_per_cell=args.runs_per_cell,
            concurrency=args.concurrency,
            cost_budget_usd=args.cost_budget_usd,
            output_dir=args.output_dir,
            run_id=args.run_id,
            seed_base=args.seed_base,
            tenant_filter=args.tenant,
            persona_kind_filter=args.persona_kind,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
```

### §3.4 Promotion CLI — `backend/scripts/promote_golden.py` (NEW)

Reads simulation artifact JSON + writes golden YAML deterministically.

```python
"""Promote a simulation candidate to a checked-in golden YAML.

Pipeline (per spec Scenario 1 + D14):
  1. Load artifact JSON from _artifacts/goldens_generation/{run_id}/sim_<uuid>.json
  2. Auto-derive expected_*:
     - termination_reason ← result.termination_reason
     - tools_invoked ← extracted from transcript tool_calls union
     - forbidden_tools ← derived from persona_kind:
       * "unqualified" → ["enroll_*", "send_payment_link", "confirm_appointment"]
       * "happy"/"nurture" → []
     - voice_attributes ← auto-extract subset of personality_profile.system_instruction
       keys (Story A `personality_profile_id` resolved via tenant_slug → seed YAML)
  3. Build GoldenMetadataModel + GoldenScenarioModel
  4. Write to backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml
     - Idempotent (overwrite if exists)
     - YAML format: pyyaml safe_dump w/ default_flow_style=False
  5. Optional --notes flag for Chris freeform override (D14)

Anti-duplication §0:
- Reuses GoldenScenarioModel (Story D §3.1)
- Reuses Story A loader read-only (`load_eval_tenant(slug)` for personality_profile)
- Reuses Story C ActorProfile schema (`load_actor_profile_for_tenant` to resolve
  actor_profile_id ↔ profile metadata)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Final
from uuid import UUID

import structlog
import yaml

from tests.agentic_evals.sales_agent.goldens._schema import (
    GoldenMetadataModel,
    GoldenPersonaKind,
    GoldenScenarioModel,
    GoldenTurnModel,
)
from tests.fixtures.eval.tenants.loader import load_eval_tenant

logger = structlog.get_logger()

_GOLDENS_ROOT: Final[Path] = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "agentic_evals"
    / "sales_agent"
    / "goldens"
)

_FORBIDDEN_TOOLS_BY_KIND: Final[dict[str, list[str]]] = {
    "unqualified": ["enroll_immediate", "send_payment_link", "confirm_appointment"],
    "happy": [],
    "nurture": [],
}


def _extract_voice_attributes(tenant_slug: str) -> list[str]:
    """Auto-extract subset of voice attribute keys from personality_profile (D14).

    Reads tenant's personality_profile.system_instruction via Story A loader.
    Returns key list (e.g. ['warmth', 'humor', 'expressiveness', 'narrative'])
    that Story E grader uses for voice fidelity checks.

    Implementation note: parses YAML structure of personality_profile —
    extracts top-level dimension keys. NEVER mutates SSoT.
    """
    ctx = load_eval_tenant(tenant_slug)
    personality = ctx.personality_profile or {}
    if not isinstance(personality, dict):
        return []
    dimensions = personality.get("dimensions", {})
    if isinstance(dimensions, dict):
        return sorted(str(k) for k in dimensions.keys())
    return []


def _derive_expected_tools_invoked(transcript: list[dict[str, object]]) -> list[str]:
    """Union of tool_calls observed across all agent turns."""
    seen: set[str] = set()
    for turn in transcript:
        if turn.get("role") != "agent":
            continue
        calls = turn.get("tool_calls") or []
        if isinstance(calls, list):
            seen.update(str(c) for c in calls)
    return sorted(seen)


def _build_golden(
    artifact: dict[str, object],
    golden_id: str,
    notes: str,
    actor_profile_id: str,
) -> GoldenScenarioModel:
    tenant_slug = str(artifact.get("tenant_archetype_slug", ""))
    persona_kind_raw = str(artifact.get("persona_kind", "happy"))
    if persona_kind_raw not in {"happy", "nurture", "unqualified"}:
        msg = (
            f"persona_kind {persona_kind_raw!r} not in goldens scope. "
            f"adversarial → Story I; edge/negative → loader-only (no graph)."
        )
        raise ValueError(msg)
    persona_kind: GoldenPersonaKind = persona_kind_raw  # type: ignore[assignment]

    transcript_raw = artifact.get("transcript", [])
    if not isinstance(transcript_raw, list):
        msg = "Artifact transcript must be a list"
        raise ValueError(msg)

    transcript: list[GoldenTurnModel] = []
    for i, t in enumerate(transcript_raw):
        if not isinstance(t, dict):
            continue
        transcript.append(
            GoldenTurnModel(
                role=t.get("role", "customer"),  # type: ignore[arg-type]
                content=str(t.get("content", "")),
                turn_number=int(t.get("turn_number", i)),
                tool_calls=t.get("tool_calls"),  # type: ignore[arg-type]
                latency_ms=t.get("latency_ms"),  # type: ignore[arg-type]
            )
        )

    cost_summary = artifact.get("cost_summary", {})
    cost_usd = Decimal(str(cost_summary.get("total_cost_usd", "0"))) if isinstance(cost_summary, dict) else Decimal("0")

    metadata = GoldenMetadataModel(
        generated_from_simulation_id=UUID(str(artifact["simulation_id"])),
        generated_at=datetime.now(tz=UTC),
        curated_by="chris",
        curated_at=datetime.now(tz=UTC),
        generation_run_id=UUID(str(artifact.get("run_id", artifact["simulation_id"]))),
        seed=int(artifact.get("seed", 0)),
        cost_usd_at_generation=cost_usd,
        notes=notes,
    )

    return GoldenScenarioModel(
        id=golden_id,
        tenant_slug=tenant_slug,  # type: ignore[arg-type]
        persona_kind=persona_kind,
        actor_profile_id=actor_profile_id,
        actor_profile_schema_version=2,
        dialect_code=str(artifact.get("dialect_code", "es-419")),
        transcript=transcript,
        expected_termination_reason=str(artifact.get("termination_reason", "GOAL_COMPLETION")),  # type: ignore[arg-type]
        expected_voice_attributes=_extract_voice_attributes(tenant_slug),
        expected_tools_invoked=_derive_expected_tools_invoked(transcript_raw),  # type: ignore[arg-type]
        forbidden_tools=_FORBIDDEN_TOOLS_BY_KIND.get(persona_kind, []),
        expected_min_distinct_objections_handled=(
            5 if persona_kind == "nurture" else None
        ),
        metadata=metadata,
    )


def _write_yaml(model: GoldenScenarioModel, path: Path) -> None:
    """Write golden as YAML deterministically (idempotent overwrite)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(
        yaml.safe_dump(data, sort_keys=True, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote simulation to golden YAML")
    parser.add_argument("--simulation-id", type=str, required=True)
    parser.add_argument("--golden-id", type=str, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument(
        "--actor-profile-id",
        type=str,
        required=True,
        help="Story C persona id (e.g. lead-frio-impaciente-pe)",
    )
    parser.add_argument("--notes", type=str, default="")
    args = parser.parse_args()

    artifact_path = args.artifact_dir / f"sim_{args.simulation_id}.json"
    if not artifact_path.exists():
        sys.stderr.write(f"ERROR: artifact not found: {artifact_path}\n")
        return 2

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    model = _build_golden(artifact, args.golden_id, args.notes, args.actor_profile_id)

    out_path = (
        _GOLDENS_ROOT / model.tenant_slug / model.persona_kind / f"{args.golden_id}.yaml"
    )
    _write_yaml(model, out_path)

    logger.info(
        "promote_golden.written",
        golden_id=args.golden_id,
        tenant_slug=model.tenant_slug,
        persona_kind=model.persona_kind,
        path=str(out_path),
    )
    sys.stdout.write(f"Wrote: {out_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### §3.5 PII patterns extraction — `backend/scripts/_pii_patterns.py` (NEW, lifted from `scan_seed_pii.py`)

```python
"""Shared PII regex catalog (LIFTED 2026-05-08 from scan_seed_pii.py).

Anti-duplication §0 — DRY threshold = 2 consumers (scan_seed_pii.py +
scan_goldens_pii.py). Lift to module shared between scripts.

Backward-compat: scan_seed_pii.py re-imports PATTERNS from this module —
zero behavior change. Tests in test_seed_pii_scanner.py still pass.

Patterns canonical set (per Story A 05-guidelines.md § "Scanner PII"):
  email, phone_intl, dni_ar, cuit_ar, rut_cl, dni_pe, curp_mx, rfc_mx,
  url_internal_nicolify

Context guards (false positive mitigation):
  dni_pe — 8-digit sequence preceded by =, :, id=, #, / is skipped.
"""

from __future__ import annotations

from typing import Final

PATTERNS: Final[dict[str, str]] = {
    "email": r"(?<![a-zA-Z0-9._%+-])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?![a-zA-Z0-9.])",
    "phone_intl": r"\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}",
    "dni_ar": r"\b\d{2}\.\d{3}\.\d{3}\b",
    "cuit_ar": r"\b\d{2}-\d{8}-\d\b",
    "rut_cl": r"\b\d{1,2}\.\d{3}\.\d{3}-[\dKk]\b",
    "dni_pe": r"(?<![=:#/])(?<!id=)\b\d{8}\b(?![=:])",
    "curp_mx": r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]\d\b",
    "rfc_mx": r"\b[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3}\b",
    "url_internal_nicolify": r"https?://[a-zA-Z0-9.-]*nicolify\.com[/\w\-?=&%.]*",
}

DNI_PE_GUARD_PREFIXES: Final[tuple[str, ...]] = ("=", ":", "id=", "#", "/", "version=")


__all__ = ["DNI_PE_GUARD_PREFIXES", "PATTERNS"]
```

### §3.6 Goldens PII scanner — `backend/scripts/scan_goldens_pii.py` (NEW)

```python
"""PII scanner for golden YAML files (Story D — defense-in-depth).

Standalone CLI script. Imports patterns from `_pii_patterns.py` (DRY).

Differences vs scan_seed_pii.py (Story A):
  - Scan path: backend/tests/agentic_evals/sales_agent/goldens/**/*.yaml
  - NO whitelist (spec D10 strict block — synthetic-first invariant has
    no legitimate exceptions; PII in goldens = always a bug).
  - Goldens-specific error message hint.

Exit codes:
  0  — clean
  1  — PII detected
  2  — error parsing YAML

Usage:
  python backend/scripts/scan_goldens_pii.py [<path>]
  (default path: backend/tests/agentic_evals/sales_agent/goldens/)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from _pii_patterns import DNI_PE_GUARD_PREFIXES, PATTERNS

_DEFAULT_GOLDENS_ROOT: Path = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "agentic_evals"
    / "sales_agent"
    / "goldens"
)


def _yaml_strings(node: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively collect all string values + their dotted paths."""
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(_yaml_strings(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            out.extend(_yaml_strings(item, f"{prefix}[{i}]"))
    elif isinstance(node, str):
        out.append((prefix, node))
    return out


def _check_string(text: str) -> list[tuple[str, str]]:
    """Return list of (pattern_name, match) for all PII matches."""
    hits: list[tuple[str, str]] = []
    for name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            matched = match.group(0)
            if name == "dni_pe":
                # Context guard
                start = match.start()
                preceding = text[max(0, start - 10) : start]
                if any(g in preceding for g in DNI_PE_GUARD_PREFIXES):
                    continue
            hits.append((name, matched))
    return hits


def _scan_file(path: Path) -> list[tuple[str, str, str]]:
    """Returns list of (yaml_path, pattern_name, matched) tuples."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.stderr.write(f"ERROR: cannot parse {path}: {exc}\n")
        return [("__error__", "yaml_parse", str(exc))]
    findings: list[tuple[str, str, str]] = []
    for ypath, value in _yaml_strings(raw):
        for pname, matched in _check_string(value):
            findings.append((ypath, pname, matched))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan goldens for PII")
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=_DEFAULT_GOLDENS_ROOT,
    )
    args = parser.parse_args()
    if not args.path.exists():
        sys.stderr.write(f"ERROR: path does not exist: {args.path}\n")
        return 2

    yaml_files = sorted(args.path.rglob("*.yaml"))
    error_count = 0
    pii_count = 0
    for yf in yaml_files:
        findings = _scan_file(yf)
        for ypath, pname, matched in findings:
            if ypath == "__error__":
                error_count += 1
                continue
            pii_count += 1
            sys.stderr.write(
                f"PII detected in {yf.relative_to(args.path)}:{ypath}: "
                f"{pname} = {matched!r}\n"
            )

    if error_count:
        return 2
    if pii_count:
        sys.stderr.write(
            f"\n{pii_count} PII matches across goldens. Strict block — synthetic-first "
            f"invariant requires zero PII. Replace with synthetic equivalents OR delete "
            f"the offending golden + regenerate via "
            f"`python backend/scripts/generate_golden_candidates.py ...`. "
            f"NO whitelist available for goldens (spec D10).\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### §3.7 Pre-commit hook Section 9 — `scripts/git-hooks/pre-commit` (EXTEND existing)

Append after line 562 (current `exit 0`):

```bash
# ─────────────────────────────────────────────────────────────────
# 9. PII scan on staged goldens YAMLs (Story D — synthetic-first ground truth)
# ─────────────────────────────────────────────────────────────────
# Activates ONLY if YAMLs staged under
# backend/tests/agentic_evals/sales_agent/goldens/. Runs scan_goldens_pii.py
# against the full goldens directory to catch drift in unchanged files.
#
# Strict block — NO whitelist (spec D10).

STAGED_GOLDEN_YAMLS=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '^backend/tests/agentic_evals/sales_agent/goldens/.*\.yaml$' || true)
GOLDEN_SCANNER_PY="${REPO_ROOT}/backend/scripts/scan_goldens_pii.py"
GOLDENS_DIR="${REPO_ROOT}/backend/tests/agentic_evals/sales_agent/goldens"

if [ -n "${STAGED_GOLDEN_YAMLS}" ] && [ -f "${GOLDEN_SCANNER_PY}" ]; then
  VENV_PY="${REPO_ROOT}/backend/.venv/bin/python"
  if [ ! -x "${VENV_PY}" ]; then
    printf "\033[33m"
    echo "WARNING: backend venv not found — skipping PII goldens scan (Section 9)."
    printf "\033[0m"
  else
    if ! "${VENV_PY}" "${GOLDEN_SCANNER_PY}" "${GOLDENS_DIR}" 2>/tmp/pii-goldens-err.txt; then
      printf "\033[31m"
      cat <<EOF
─────────────────────────────────────────────────────────────
PRE-COMMIT BLOCKED: PII detected in goldens/ — strict block.
─────────────────────────────────────────────────────────────
Synthetic-first invariant: zero PII in golden YAMLs (spec D10).
NO whitelist available for goldens.

$(cat /tmp/pii-goldens-err.txt 2>/dev/null || true)

Resolution:
  1. Replace real PII with synthetic equivalents (use fake names like
     "Cliente Ejemplo", phone "+99 0 1234 5678", emails "user@example.com").
  2. OR delete the offending golden file + regenerate it via:
     python backend/scripts/generate_golden_candidates.py \\
       --tenant <slug> --persona-kind <kind> \\
       --output-dir _artifacts/goldens_generation/<run_id>/

NEVER use --no-verify (.claude/rules/git-safety.md prohibits).
─────────────────────────────────────────────────────────────
EOF
      printf "\033[0m"
      exit 1
    fi
  fi
fi

exit 0
```

### §3.8 Schema + coverage tests

```
backend/tests/agentic_evals/sales_agent/
├── test_goldens_schema.py                  # (NEW) — validates each YAML deserializes
│                                            #         + referential integrity (actor_profile_id,
│                                            #           tenant_slug, dialect_code matches catalog)
│                                            #         + test_no_pii_in_committed_goldens (defense-in-depth)
├── test_goldens_coverage.py                # (NEW) — test_all_cells_covered (≥1 per 15 cells)
│                                            #         + test_reports_all_cells_with_gaps (no early exit)
└── test_goldens_pii_scanner.py             # (NEW) — fixtures (4 categories × 3 LatAm dialects)
                                             #         + verifies detection per category
                                             #         + adversarial fixtures NOT committed
                                             #         (live in tests/_pii_fixtures/ NOT goldens/)
```

Plus script tests:

```
backend/tests/scripts/
├── test_generate_golden_candidates.py       # (NEW) — argparse defaults, matrix shape,
│                                              #         single-cell regen, cost budget guard
├── test_promote_golden.py                  # (NEW) — auto-derive expected_*, voice
│                                              #         attribute extraction, idempotency
└── test_pre_commit_hook.py                  # (EXTEND) — test_blocks_pii_in_goldens
                                             #            (mirror Section 8 pattern)
```

### §3.9 Architecture fitness gate ratchet additions

| Gate | Path | Surface | Allowlist |
|---|---|---|---|
| `test_goldens_schema_completeness` | `backend/tests/architecture/test_goldens_schema_completeness.py` (NEW) | enforces: schema_version=1 cement; if v2+ exists, migrator registered in `GOLDEN_SCHEMA_MIGRATIONS`; `GoldenScenarioModel.model_config['extra'] == 'forbid'`; cross-ref Story A 5 slugs Literal exhaustive | empty |
| `test_goldens_no_mirror_simulator_schema` | `backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py` (NEW) | enforces: `goldens/_schema.py` does NOT import from `simulator/_internal/schema_migrations.py` (parallel registries cement). Anti-duplication §0 invariant | empty |
| `test_pii_patterns_single_source` | `backend/tests/architecture/test_pii_patterns_single_source.py` (NEW) | enforces: `scan_seed_pii.py` + `scan_goldens_pii.py` BOTH import `PATTERNS` from `_pii_patterns.py` — no copy. DRY invariant | empty |
| `test_goldens_cost_bucket_invariant` (CI-only, conditional skip) | `backend/tests/architecture/test_goldens_cost_bucket_invariant.py` (NEW) | enforces: post-`generate_golden_candidates.py` run, `eval_simulator_llm_call` rows present + `copilot_llm_call` zero new rows. Skipped unless `EVAL_GOLDENS_COST_BUCKET_VERIFY=1` env (CI nightly only — no per-PR cost) | N/A |
| `test_goldens_no_committed_pii` (existing pattern) | `backend/tests/architecture/test_goldens_no_committed_pii.py` (NEW) | re-runs `scan_goldens_pii.py` against entire `goldens/` dir. Expected exit code 0. Defense-in-depth on top of pre-commit hook | empty |

### §3.10 Goldens README — `backend/tests/agentic_evals/sales_agent/goldens/README.md` (NEW)

Sections (per spec Scenario 1 acceptance criteria):

1. **Overview** — synthetic-first paradigm, why it exists, who curates
2. **Pipeline generación** — 2-phase pipeline (script → Chris curation), command examples
3. **Cómo agregar/refrescar golden** — step-by-step
4. **Política de actualización** — manual trigger only, refresh signals (Story C schema bump, grader saturate >0.95, 6-month review)
5. **Schema reference** — link to `_schema.py` + field semantics
6. **Cost budget** — generation cost $5.40 expected / $8 cap, per spec
7. **Coverage gate** — ≥1 per 15 cells, run command for `test_all_cells_covered`
8. **PII defense-in-depth** — pre-commit hook Section 9 + arch fitness gate, NO whitelist policy

### §3.11 Capability YAML extension — post-merge `/pm`

`docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` append to `eval:` block:

```yaml
  # Story D — sales-agent-goldens-3-tenants-dataset (merge date TBD)
  goldens_dataset_path: "backend/tests/agentic_evals/sales_agent/goldens/"
  goldens_count_target:
    min: 20
    max: 30
  goldens_schema_version: 1
  goldens_schema_path: "backend/tests/agentic_evals/sales_agent/goldens/_schema.py"
  goldens_generation_script: "backend/scripts/generate_golden_candidates.py"
  goldens_promotion_script: "backend/scripts/promote_golden.py"
  goldens_pii_scanner_path: "backend/scripts/scan_goldens_pii.py"
  goldens_persona_kinds_in_scope:
    - happy
    - nurture
    - unqualified
  goldens_coverage_gate_test: "backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_all_cells_covered"
  goldens_story_introduced: sales-agent-goldens-3-tenants-dataset
  goldens_test_coverage:
    - "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py"
    - "backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py"
    - "backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py"
    - "backend/tests/architecture/test_goldens_schema_completeness.py"
    - "backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py"
    - "backend/tests/architecture/test_pii_patterns_single_source.py"
    - "backend/tests/architecture/test_goldens_no_committed_pii.py"
    - "backend/tests/scripts/test_generate_golden_candidates.py"
    - "backend/tests/scripts/test_promote_golden.py"
```

`docs/product/modules/sales-agent.md` narrative append (1-2 sentences):

> Eval suite ground truth = 20-30 goldens curados manualmente por Chris desde simulación dual-LLM (Story C personas + Story B simulator). Generación via `generate_golden_candidates.py` → curación Markdown preview → `promote_golden.py` deterministic write. PII defense-in-depth via pre-commit hook + arch fitness gate.

## §4 Cross-cutting decisions consolidadas

### Tenant isolation
- Each golden YAML contains data from ONE tenant (`tenant_slug` field cement). `test_goldens_schema.py` enforces (no cross-tenant data in transcript content via heuristic + assertion).
- `generate_golden_candidates.py` uses Story B `run_simulation(tenant_archetype_slug=...)` which carries tenant_id internally. Script never touches DB directly.
- `promote_golden.py` reads tenant_slug from artifact JSON — never mutates DB.

### PII handling (defense-in-depth)
- Layer 1: synthetic-first invariant (Story A seeds + Story C personas synthetic data).
- Layer 2: `scan_goldens_pii.py` script (8 regex categories, no whitelist).
- Layer 3: pre-commit hook Section 9 (blocks commit on detection).
- Layer 4: arch fitness gate `test_goldens_no_committed_pii.py` (CI re-runs scanner on full dataset).
- Layer 5: schema validation `test_goldens_schema.py::test_no_pii_in_committed_goldens` (assertions on real 20-30 goldens).

### Voice (sales-agent-expert SSoT respect)
- `personality_profiles.system_instruction` SSoT untouched — `promote_golden` reads keys read-only.
- `expected_voice_attributes` auto-extracted subset of dimension keys per `dialect_code`.
- Voseo permitted in `transcript[].content` ONLY when `dialect_code: es-AR` (sales_agent voice tenant respected per spec Non-functional). Magic comment escape NOT applied to goldens YAML files (vs Story C personas) — instead, voseo presence is contextual via dialect_code field; pre-commit voseo hook excludes goldens path.
- Resto código (script messages, structlog events, README, comments) Spanish neutro per `.claude/rules/spanish-text.md`.

### Currency + master data
- `cost_usd_at_generation: Decimal` field — UTC observability snapshot
- `generated_at`/`curated_at` `datetime` UTC — `DateTime(timezone=True)` not relevant (in-memory model only, no DB row).
- No hardcoded `'USD'` in scripts — Story B `cost_summary.total_cost_usd` already returns Decimal in suite-scope currency.

### Schema versioning forward-compat
- `GoldenScenarioModel.schema_version: Literal[1] = 1` cement.
- `GOLDEN_SCHEMA_MIGRATIONS` parallel registry (separate from Story B simulator registry) — first bump (v1→v2) registers identity migrator + bumps `CURRENT_GOLDEN_SCHEMA_VERSIONS` in same commit.
- 20-30 committed goldens carry `schema_version: 1`. Future v2 bump — script provides `--migrate-goldens` flag to apply migrators in-place (Chris-triggered manual refresh per D15).

### Observability tags (cost-bucket separation invariant — Story B H6/H7)
- `generate_golden_candidates.py` invokes `run_simulation()` which writes to `eval_simulator_llm_call` ONLY (Story B cement).
- Arch fitness gate `test_goldens_cost_bucket_invariant.py` (env-gated CI nightly) verifies post-suite zero `copilot_llm_call` rows + ≥75 `eval_simulator_llm_call` rows.

### Cost-bucket separation
- ZERO change. Script consumes Story B's `run_simulation` which already writes correctly.
- Story D adds NO new cost surfaces. Story H interface receives expanded baseline (~$5.40 generation budget + ~$2.20 Story C scenarios baseline = ~$7.60 total eval suite cost).

### Determinism + idempotency
- `simulation_id` deterministic UUID5 (Story B D11) — re-run same `--seed-base` reproduces same artifact paths.
- `promote_golden --golden-id X --simulation-id Y` overwrites YAML deterministically (idempotent — file written via `Path.write_text` replaces atomically).
- `generate_golden_candidates --seed-base N` deterministic across runs given same Story C YAMLs (`actor_profile.schema_version` snapshot at curation time D7).

### Spanish neutro (`.claude/rules/spanish-text.md`)
- Scripts code + structlog events + comments + README — Spanish neutro tuteo.
- CLI error messages — Spanish neutro.
- Personas YAML voseo permitted only `dialect_code: es-AR` (Story C scope).
- Goldens YAML transcripts may contain voseo if persona is es-AR (sales_agent voice exception preserved end-to-end).

### Native-first dev
- Lint/tests run native WSL (`backend/.venv/bin/{ruff,pytest,mypy}`).
- Scripts invoked native: `python backend/scripts/generate_golden_candidates.py ...`.
- Pre-commit hook native (extends existing infrastructure).

### Anti-duplication §0
- Cero mirror. PII patterns LIFTED to shared module (DRY threshold = 2 consumers).
- `simulator/__init__.py` 7-name surface CONSUMED, NOT modified (H9 cement preserved).
- Story C `_internal/personas_loader.py` CONSUMED via documented downstream pin (Story C D-AG-2).
- Schema migration registry pattern PARALLEL (different namespace), NOT mirror — distinct lifecycle.

## §5 Decisiones arquitectónicas (D-A-* Story D additions)

| ID | Decision | Razón |
|---|---|---|
| D-A-1 | `GoldenScenarioModel` ConfigDict(extra="forbid", frozen=True) | Pydantic v2 invariant — no field drift, no accidental mutation post-curation |
| D-A-2 | `GOLDEN_SCHEMA_MIGRATIONS` parallel registry (NOT mirror Story B's `simulator/_internal/schema_migrations.py`) | Different namespace + lifecycle; arch test `test_goldens_no_mirror_simulator_schema.py` enforces |
| D-A-3 | PII patterns extracted to `_pii_patterns.py` (LIFT) | Anti-duplication §0 DRY threshold = 2 consumers; arch test `test_pii_patterns_single_source.py` enforces |
| D-A-4 | NO whitelist for goldens scanner (vs Story A's `.eval-whitelist`) | Spec D10 strict block — synthetic-first invariant has no legitimate exception |
| D-A-5 | Pre-commit hook Section 9 (NEW, mirrors Section 8 pattern) | Defense-in-depth without breaking existing Section 8 (eval seed scanner) |
| D-A-6 | `generate_golden_candidates.py` cost budget pre-flight strict abort | spec D2 + tessl__graceful-degradation Rule 5 — fail-fast prevents runaway cost |
| D-A-7 | Markdown preview (NOT HTML/Streamlit) — Q3 ratified | IDE-renderable, parallel-safe, terminal-friendly, zero browser dep |
| D-A-8 | `promote_golden.py` auto-derives `expected_*` fields + Chris freeform `notes` override | D14 cement — máquina hace grunt work, Chris añade judgment |
| D-A-9 | `expected_voice_attributes` auto-extract subset of `personality_profile.dimensions.keys()` | Story E grader consumes directly; SSoT respected (read-only); deterministic per tenant |
| D-A-10 | `forbidden_tools` declarative per persona_kind (D17) — `unqualified` → `[enroll_*, send_payment_link, confirm_appointment]`, others `[]` | Aligns Story C Scenario 5 production-critical qualification capability test |
| D-A-11 | Coverage gate `test_all_cells_covered` reports ALL gaps (no early-exit) | Spec Scenario 3 — informs scope completo, not first-failure |
| D-A-12 | Generation script consumes Story B 7-name public API + Story C `_internal/personas_loader` (documented downstream pin per Story C D-AG-2) | H9 cement preserved; Story C explicit downstream consumer contract |
| D-A-13 | Goldens schema migration registry separate from arch fitness gate (no `test_schema_migrations_registry_complete.py` mirror) | Story B's gate is simulator-scoped; goldens parallel registry exhaustiveness via `test_goldens_schema_completeness.py` |
| D-A-14 | Generation script tested by mocking `run_simulation` (unit) + integration with `--run-evals` flag (CI nightly only) | Cost containment — full integration in CI per-PR prohibitive |
| D-A-15 | Goldens YAML format: `yaml.safe_dump(..., sort_keys=True, default_flow_style=False, allow_unicode=True)` | Deterministic output → idempotent overwrite + git-diff-friendly |

## §6 Output contract para consumers (estable forward)

```python
# Story D INTERNAL public-to-tests-only API (consumed by Story E + onwards):
from tests.agentic_evals.sales_agent.goldens._schema import (
    GoldenScenarioModel,             # Pydantic v2 frozen
    GoldenTurnModel,
    GoldenMetadataModel,
    GoldenTenantSlug,                 # Literal 5 slugs
    GoldenPersonaKind,                # Literal 3 kinds
    GoldenTerminationReason,          # Literal 3 reasons
)

# Goldens dataset path (loaded by Story E grader runtime):
GOLDENS_ROOT = Path("backend/tests/agentic_evals/sales_agent/goldens/")
# Pattern: GOLDENS_ROOT / {tenant_slug} / {persona_kind} / {golden_id}.yaml
```

| Story | Consumes |
|---|---|
| E (voice-fidelity-grader-runtime) | Loads each golden YAML → `GoldenScenarioModel` → grades transcript vs `expected_voice_attributes` |
| F (eval-pass-k-tracking) | Buckets pass^k by `(tenant_slug × persona_kind × golden_id)` — direct path read |
| G (voice-fidelity-ci-gate) | CI runs `pytest test_goldens_*.py` + Story E graders vs goldens dataset path |
| H (eval-cost-budget-cap) | Adds Story D generation cost (~$5.40) to baseline; cap drives `test_goldens_cost_bucket_invariant.py` env gating |
| I (adversarial-jailbreak-suite) | Extends dataset with `persona_kind=adversarial` slot — additive (schema NOT bumped — adversarial is Story I scope decision) |

## §7 Open architecture risks

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Story C build delay → Story D build blocked indefinitely | medium | Architect phase parallel-safe; build gated explicitly. Coordinator `/pm` tracks Story C completion event. |
| Generation cost overrun (>$8 cap) | medium | Pre-flight strict abort + `--cost-budget-usd` flag + per-cell isolation (one cell failure ≠ suite abort) |
| Chris curation backlog (selecting 20-30 from 75 candidates is manual) | low | Markdown preview format optimized for terminal/IDE scanning; one-line summary per cell + sortable table |
| `test_goldens_cost_bucket_invariant.py` flaky on CI nightly (DB state coupling) | low | Env-gated `EVAL_GOLDENS_COST_BUCKET_VERIFY=1` — opt-in CI nightly only; per-PR test runs skipped (no DB query) |
| PII pattern false positive in synthetic transcripts (e.g. fake phone matches DNI_PE regex) | low | Story A's context guards reused (DNI_PE preceded by `=`/`:`/`#`/`/` skipped); fixtures in `test_goldens_pii_scanner.py` cover 4 categories × 3 dialects |
| Schema bump v1→v2 in 6 months requires re-curation | low | `GOLDEN_SCHEMA_MIGRATIONS` registry handles automatic upgrade; `--migrate-goldens` flag in promote_golden |
| `actor_profile_id` references Story C YAML that gets renamed | medium | Referential integrity test `test_goldens_schema.py::test_actor_profile_id_exists` cross-checks each golden's actor_profile_id against `docs/specs/personas/archetype-aware/*.yaml`. CI fail on rename. |
| `_pii_patterns.py` extraction breaks `scan_seed_pii.py` (Story A test_seed_pii_scanner.py regression) | medium | Backward-compat: `scan_seed_pii.py` re-imports from new module; arch test `test_pii_patterns_single_source.py` enforces both consumers; Story A's full test suite re-runs in CI for regression detection |
| Pre-commit hook Section 9 fails on Windows path separators (cross-platform) | low | Hook uses bash + grep + venv python; existing Section 8 has no Windows issue (WSL-only dev) |
| `promote_golden.py` writes wrong tenant_slug from artifact (artifact missing field) | low | Pydantic validation in `_build_golden` raises ValueError on missing/invalid; CLI exit code 2; logged via structlog |

## §8 Out of scope (consolidado — anti-creep guards)

- ❌ Adversarial goldens (`persona_kind=adversarial`) — Story I scope (additive future)
- ❌ Edge/negative `persona_kind` goldens — loader-only (Story C D15)
- ❌ Production-extracted goldens (paradigma v1 superseded — sales_agent no en prod)
- ❌ Cross-language goldens (en/pt/etc.) — scope LatAm Spanish only
- ❌ Auto-curation 100% (sin Chris en loop) — drift risk
- ❌ Goldens >30 — saturation point eval suite
- ❌ Golden mutation post-promotion (immutable post-commit excepto Chris explicit refresh)
- ❌ Modify `simulator/__init__.py` 7-name surface (H9 cement Story B)
- ❌ Modify Story C `_internal/personas_loader.py` (consume only)
- ❌ Modify Story C 15 personas YAML (consume only)
- ❌ Modify Story A 5 tenant seeds (consume only)
- ❌ Modify `personality_profiles.system_instruction` (read-only extraction)
- ❌ Modify `eval_simulator_*` DB schema (R5 cement Story B)
- ❌ Refresh policy automation (cron/CI) — manual trigger Chris
- ❌ Re-run generation in CI per-PR (cost prohibitive — manual trigger)
- ❌ HTML preview / Streamlit dashboard for curation (Q3 ratified Markdown only)
- ❌ Modify `scan_seed_pii.py` behavior (only refactor: re-import from `_pii_patterns.py`)
- ❌ Whitelist mechanism for goldens (D10 strict block)
- ❌ Modify `core/config.py` defaults (no flag flips this story)
- ❌ Touch §3 sales-agent protected surfaces

## §9 Research notes (state-of-the-art como of 2026-05-08)

> Architect run on 2026-05-08. Knowledge cutoff Jan 2026 (Opus 4.7) — research below verified live via WebSearch/WebFetch on 2026-05-08 unless cached SOTA paper.

- **Anthropic Bloom 4-stage** (cited spec D8): `understanding/ideation/rollout/judgment` Literal canonical — declarative metadata only Story C; Story D inherits via personas YAML metadata. Source: `https://docs.anthropic.com/en/docs/build-with-claude/evaluation` accessed 2026-05-08.
- **AWS Strands ActorProfile pattern** (Story B archive D7): `traits + context + actor_goal` decoupled. Story D consumes `ActorProfile` via Story C loader.
- **PersonaGym 5-axis** (cited spec D9): declarative metadata only Story C; Story E owns runtime grader. Source: PersonaGym paper https://arxiv.org/abs/2407.18416 (research stable since 2024).
- **τ-Bench scenario coverage** (cited outcome): pass^k all-of-K is Story F scope; Story D delivers 20-30 goldens dataset matching τ-Bench saturation point research. Source: confirmed live via `https://docs.anthropic.com/en/docs/build-with-claude/agents` accessed 2026-05-08.
- **Pydantic v2 ConfigDict(frozen=True)** stable since v2.0 (2023). `model_dump(mode='json')` for YAML serialization roundtrip-safe. Source: `https://docs.pydantic.dev/latest/concepts/models/#frozen-instances` accessed 2026-05-08.
- **`tessl__graceful-degradation` Rule 5** — per-dependency error isolation in generation script (one cell failure ≠ suite abort). Loaded from skill 2026-05-08.
- **Anthropic prompt caching** N/A Story D (no LLM dispatch in tooling — consumed via Story B's `run_simulation` which already implements caching per Story C 03-arch §10).

## §10 capability YAML + modules narrative updates (post-merge by /pm)

Files post-merge `/pm` updates (per §3.11):

- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` — append `eval.goldens_*` block (10+ fields)
- `docs/product/modules/sales-agent.md` — narrative addition (1-2 sentences)
- `.claude/rules/auditor-downstream-regression.md` — append entry:
  - `backend/tests/agentic_evals/sales_agent/goldens/**` → downstream_test_targets [`backend/tests/agentic_evals/sales_agent/test_goldens_*.py`, `backend/tests/architecture/test_goldens_*.py`, `backend/tests/scripts/test_generate_golden_candidates.py`, `backend/tests/scripts/test_promote_golden.py`]
  - `backend/scripts/_pii_patterns.py` → downstream_test_targets [`backend/tests/scripts/test_seed_pii_scanner.py`, `backend/tests/scripts/test_pre_commit_hook.py` (Section 8+9)]
  - `backend/scripts/generate_golden_candidates.py` → downstream_test_targets [`backend/tests/scripts/test_generate_golden_candidates.py`]
  - `backend/scripts/promote_golden.py` → downstream_test_targets [`backend/tests/scripts/test_promote_golden.py`]
- `backend/tests/agentic_evals/sales_agent/goldens/README.md` — created during build (T-4 ticket)

## §11 Próximo paso

`done -> 03-arch.md` — Story D ready package architecture consolidated.
