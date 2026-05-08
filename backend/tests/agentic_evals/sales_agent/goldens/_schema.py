"""Golden scenario schema — Story D (synthetic-first eval ground truth).

Pydantic v2 frozen models + parallel SCHEMA_MIGRATIONS registry.

Design decisions (03-arch.md §3.1):
    D6  — schema_version: Literal[1] cement. Future bumps via GOLDEN_SCHEMA_MIGRATIONS
          registry. NEVER mutate v1 spec in place.
    D7  — actor_profile_schema_version: Literal[2] snapshot at curation time.
          Immune to Story C v3+ bumps — frozen artifact contract.
    D17 — forbidden_tools declarative per persona_kind.

Anti-duplication (`.claude/rules/anti-duplication.md`):
    - Pydantic v2 ConfigDict(extra='forbid', frozen=True) pattern reused from
      Story B `simulator/actor_profile.py`.
    - Schema migration registry pattern PARALLEL to Story B
      `simulator/_internal/schema_migrations.py` — distinct namespace +
      distinct lifecycle. This module does NOT import from that module.
    - `sanitize_payload` NOT applied here (golden YAMLs are static checked-in
      data; scanner enforces zero-PII at commit-time via pre-commit Section 9).

Tenant isolation (`.claude/rules/tenant-isolation.md`):
    Each golden contains data from EXACTLY ONE tenant. Cross-tenant data
    fails schema validation (referential integrity tests in T-4).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Story A 5 tenant seeds — frozen Literal (D6) ─────────────────────────────
GoldenTenantSlug = Literal[
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
]
"""Exactly 5 Story A tenant seeds. Add new tenant → bump schema_version + register migrator."""

# ── Story D 3 persona kinds in scope (D3) ────────────────────────────────────
# adversarial = Story I scope
# edge/negative = loader-only, not promoted to goldens dataset
GoldenPersonaKind = Literal["happy", "nurture", "unqualified"]
"""3 persona kinds for Story D goldens. adversarial is Story I (out of scope D3)."""

# ── Termination reasons valid for golden promotion (D6) ──────────────────────
# AGENT_ERROR = failure mode — never a golden (would contaminate ground truth)
GoldenTerminationReason = Literal[
    "GOAL_COMPLETION",
    "MAX_TURNS",
    "CUSTOMER_EXIT",
]
"""3 success outcomes for golden conversations. AGENT_ERROR excluded (failure mode)."""


class GoldenTurnModel(BaseModel):
    """One verbatim turn from a promoted simulation transcript.

    Frozen: golden YAMLs are immutable artifacts post-commit (D16).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["customer", "agent"]
    """Turn author — customer or agent sides of the conversation."""

    content: str = Field(min_length=1)
    """Verbatim turn text captured from simulation."""

    turn_number: int = Field(ge=0)
    """0-indexed position in the transcript."""

    tool_calls: list[str] | None = None
    """Tool names invoked during this agent turn (None = no tools / customer turn)."""

    latency_ms: int | None = None
    """Observability snapshot from simulation — optional, not required for schema validity."""


class GoldenMetadataModel(BaseModel):
    """Generation provenance + curation audit trail.

    Implements D13 (traceability via simulation_id) + D14 (notes override freeform).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_from_simulation_id: UUID
    """Story B D11 deterministic UUID5 stable — links back to source simulation."""

    generated_at: datetime
    """UTC timestamp when simulation_artifact was generated."""

    curated_by: str = Field(min_length=1)
    """Curator identity — e.g. 'chris'."""

    curated_at: datetime
    """UTC timestamp when promote_golden.py was run."""

    generation_run_id: UUID
    """Links to _artifacts/goldens_generation/{run_id}/ directory."""

    seed: int
    """Deterministic seed for reproducible re-generation (D8)."""

    cost_usd_at_generation: Decimal
    """LLM cost snapshot at generation time (Decimal for precision — no float drift)."""

    notes: str = ""
    """D14 — Chris freeform override. Empty string = no manual override."""


class GoldenScenarioModel(BaseModel):
    """Curated golden conversation — synthetic ground truth for eval suite.

    Schema v1 cement (D6). Future bumps via GOLDEN_SCHEMA_MIGRATIONS registry
    in `_schema_migrations.py`. NEVER mutate v1 field specs in place.

    Tenant isolation: each instance contains data from EXACTLY ONE tenant
    (enforced via GoldenTenantSlug Literal + referential integrity in T-4 tests).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    """Forward-compat version cement (D6). Bumps register migrators in GOLDEN_SCHEMA_MIGRATIONS."""

    id: str = Field(min_length=3, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    """Slug-style identifier — e.g. 'coach-lat-happy-001'. Stable across refreshes."""

    tenant_slug: GoldenTenantSlug
    """Story A tenant seed binding. Exactly 1 tenant per golden (tenant isolation)."""

    persona_kind: GoldenPersonaKind
    """Conversation archetype: happy/nurture/unqualified (D3)."""

    actor_profile_id: str = Field(min_length=3)
    """Story C YAML id — referential integrity verified in T-4."""

    actor_profile_schema_version: Literal[2] = 2
    """D7 — frozen at curation time. Immune to Story C v3+ bumps."""

    dialect_code: str = Field(min_length=2)
    """BCP-47 dialect code — must match dialect_catalog[tenant_slug] (referential integrity T-4)."""

    transcript: list[GoldenTurnModel] = Field(min_length=2)
    """Verbatim conversation transcript. Minimum 2 turns for a realistic exchange."""

    expected_termination_reason: GoldenTerminationReason
    """Auto-derived from simulation result (D14). GOAL_COMPLETION/MAX_TURNS/CUSTOMER_EXIT."""

    expected_voice_attributes: list[str] = Field(min_length=1)
    """Auto-extracted from tenant personality_profile (D14). At least 1 attribute."""

    expected_tools_invoked: list[str] = Field(default_factory=list)
    """Tools expected to fire during the conversation. Empty = no tool use expected."""

    forbidden_tools: list[str] = Field(default_factory=list)
    """D17 — declarative gate per persona_kind. unqualified → 3 close tools blocked."""

    expected_min_distinct_objections_handled: int | None = Field(default=None, ge=1)
    """For nurture persona_kind only — minimum distinct objections handled (D17)."""

    metadata: GoldenMetadataModel
    """Generation provenance + curation audit trail (D13 + D14)."""


__all__ = [
    "GoldenMetadataModel",
    "GoldenPersonaKind",
    "GoldenScenarioModel",
    "GoldenTenantSlug",
    "GoldenTerminationReason",
    "GoldenTurnModel",
]
