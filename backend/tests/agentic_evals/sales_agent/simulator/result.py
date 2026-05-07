"""SimulationResult + ConversationTurn + CostSummary — Pydantic v2 frozen.

Public — exported via simulator/__init__.py per H9 (T-9 finaliza the surface).

ConversationTurn lives here (NOT in state.py) because:
- LangGraph state imports `ConversationTurn` from `.result` (no cycle).
- Round-trip to JSON artifacts uses `ConversationTurn` deserialization.
- Frozen golden v1 fixture (T-9) materializes SimulationResult.transcript = list[ConversationTurn].

Schema versioning H1: every Pydantic class carries `schema_version: int = 1`. Bumps
register migrators in `_internal/schema_migrations.py::SCHEMA_MIGRATIONS`.

# voseo-allowed: comments document `actor.dialect_code='es-AR'` voseo escape
"""

# NO `from __future__ import annotations` — explicit cement (story-wide).

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
)


# ════════════════════════════════════════════════════════════════════════
# ConversationTurn — single turn in transcript (frozen, append-only via reducer)
# ════════════════════════════════════════════════════════════════════════


class ConversationTurn(BaseModel):
    """One turn (customer or agent) in the simulation transcript.

    Empty `content` is rejected (`min_length=1`) — empty agent output marks
    `AgentErrorSubtype.EMPTY_RESPONSE` BEFORE this turn would be appended.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    """H1 forward-compat — version per ConversationTurn schema."""

    turn_number: int = Field(ge=0)
    """0-indexed turn ordering (0 = customer initial_message)."""

    role: Literal["customer", "agent"]
    """Turn author — drives prompt adapter selection in customer_node + agent_bridge."""

    content: str = Field(min_length=1)
    """Turn message verbatim. Empty content rejected at construction time."""

    timestamp: datetime
    """UTC explicit (master-data rule). Caller MUST pass tz-aware datetime."""

    metadata: dict[str, str | int | bool | None] = Field(default_factory=dict)
    """Per-turn meta — `generated: bool` flag, `simulation_id` echo, etc."""


# ════════════════════════════════════════════════════════════════════════
# CostSummary — per-simulation cost split (D9 — $0.05 indiv / $0.30 suite)
# ════════════════════════════════════════════════════════════════════════


def _default_llm_call_count_split() -> dict[Literal["sales_agent", "eval_simulator"], int]:
    """Factory for ``CostSummary.llm_calls_count_split`` default zero state.

    Module-level (not lambda) so mypy resolves the Literal keys precisely.
    """
    return {"sales_agent": 0, "eval_simulator": 0}


class CostSummary(BaseModel):
    """Per-simulation cost summary.

    D9 enforced via arch fitness gate `agentic_cost_budget_baseline` (T-10):
    - Individual `<$0.05/run`
    - Suite total `<$0.30` for 9 scenarios

    Decimal used (not float) for currency precision. Default zero allows the
    runner to construct an empty summary before observability rows aggregate.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    """H1 forward-compat — version per CostSummary schema."""

    agent_cost_usd: Decimal = Decimal(0)
    """Cost of `sales_agent_llm_call` rows (production agent)."""

    simulator_cost_usd: Decimal = Decimal(0)
    """Cost of `eval_simulator_llm_call` rows (customer + ancillary)."""

    total_cost_usd: Decimal = Decimal(0)
    """Sum of agent + simulator cost. Caller computes; Pydantic does not auto-sum."""

    llm_calls_count_split: dict[Literal["sales_agent", "eval_simulator"], int] = Field(
        default_factory=_default_llm_call_count_split,
    )
    """Call count per agent_kind discriminator — drives observability rollup."""


# ════════════════════════════════════════════════════════════════════════
# SimulationResult — runner final output (returned + JSON-artifact source)
# ════════════════════════════════════════════════════════════════════════


class SimulationResult(BaseModel):
    """Returned by `run_simulation(...)` — D10 spec.

    Also serialized to `_artifacts/{run_id}/simulator/{simulation_id}/transcript.json`
    via Pydantic `model_dump_json()`. T-10 frozen golden v1 fixture materializes
    this exact shape — schema bumps require migrator entry.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    """H1 forward-compat — bumps register migrator."""

    simulation_id: UUID
    """Deterministic UUID5 — H2 idempotency."""

    run_id: UUID
    """Parent eval run identifier (1 run → N simulations)."""

    tenant_id: UUID
    """Synthetic eval tenant — `uuid5(NS_DNS, f"eval-{slug}")` deterministic."""

    archetype_slug: str
    """One of 5 valid eval archetypes (validated en runner T-8)."""

    actor_profile_id: str
    """Stable `ActorProfile.id` — drives reproducibility."""

    trial_n: int
    """Trial counter (Story F multi-trial; Story B always 0)."""

    transcript: list[ConversationTurn]
    """Full conversation history append-only (snapshot — frozen)."""

    termination_reason: TerminationReason
    """Why the simulation ended (StrEnum coerced from str)."""

    error_subtype: AgentErrorSubtype | None = None
    """Set when termination_reason == AGENT_ERROR (H7 taxonomy)."""

    total_turns: int = Field(ge=0)
    """`len(transcript)` snapshot (validated by runner pre-construction)."""

    cost_summary: CostSummary
    """Per-simulation cost (computed from observability rows in T-8 runner)."""

    started_at: datetime
    """UTC tz-aware — runner sets at simulation entry."""

    completed_at: datetime
    """UTC tz-aware — runner sets at simulation exit (success or error)."""

    artifact_path: str = Field(min_length=1)
    """Relative path `_artifacts/{run_id}/simulator/{simulation_id}/transcript.json`."""


__all__ = [
    "ConversationTurn",
    "CostSummary",
    "SimulationResult",
]
