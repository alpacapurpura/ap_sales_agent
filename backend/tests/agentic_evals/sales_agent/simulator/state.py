"""SimulationState — LangGraph Pydantic state for dual-LLM simulator.

Decisión D4 (spec): Pydantic-first state machine (NO TypedDict) con
schema_version forward-compat. State graph runtime introspection
funciona OK con Pydantic (LangGraph 0.2+ tested — `tessl__langgraph` skill
SSoT). NO `from __future__ import annotations` en este file ni en
simulator/_internal/graph.py — rompe LangGraph runtime introspection
(caso `nodes.py` cementado en copilot redesign 2026-04 + sales-agent S6).

Public — exported via simulator/__init__.py per H9 (T-9 finaliza el surface).

LangGraph reducers (state mutation contract):
- `transcript: Annotated[list[ConversationTurn], operator.add]` — append-only
  reducer. Each node returns partial state dict `{"transcript": [new_turn]}`,
  LangGraph applies operator.add to merge.
- `iterations: int` — overwrite (no reducer); incremented monotonically by
  `_internal/increment_turn.py` (T-8 implements).

# voseo-allowed: docstring references `actor.dialect_code='es-AR'` voseo escape
"""

# NO `from __future__ import annotations` — explicit cement (story-wide).
# This file MUST NOT lazy-stringify annotations; LangGraph runtime introspection
# requires resolved annotations on the BaseModel class.

import operator
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import ConversationTurn
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
)


class SimulationState(BaseModel):
    """LangGraph state — single instance per simulation_id, immutable field
    order across schema versions (H1 — bumps register migrator entry).

    Tenant isolation: `tenant_id` MANDATORY. Every observability write inherits
    via callback handler subclass (T-5 implements `EvalSimulatorCallbackHandler`).

    Concurrency-safe (H3): graph nodes return PARTIAL state dicts, never mutate
    in place. LangGraph applies operator.add reducer for `transcript`.
    """

    # NOTE: extra="forbid" rejects unknown keys at construction. If LangGraph
    # adds protocol keys via Command(update={...}) in a future release that
    # are NOT declared here, change to "allow" with explicit known additions.
    # As of LangGraph 0.6 (May 2026), node returns are merged into declared
    # fields only — extra="forbid" is safe.
    model_config = ConfigDict(extra="forbid")

    # ────────────────────────────────────────────────────────────────────
    # Schema versioning (H1)
    # ────────────────────────────────────────────────────────────────────

    schema_version: int = 1
    """Bumps register migrator in `_internal/schema_migrations.py`."""

    # ────────────────────────────────────────────────────────────────────
    # Identity (H2 idempotency — UUID5 deterministic from runner)
    # ────────────────────────────────────────────────────────────────────

    simulation_id: UUID
    """uuid5(NS_DNS, f"{run_id}_{slug}_{actor.id}_{trial_n}") — deterministic re-run."""

    run_id: UUID
    """Parent eval invocation. 1 run → N simulations."""

    tenant_id: UUID
    """Synthetic tenant — `uuid5(NS_DNS, f"eval-{slug}")`. Tenant isolation invariant."""

    archetype_slug: str
    """FK to 5 valid archetype slugs. Runner validates membership at entry (T-8)."""

    actor_profile: ActorProfile
    """Persona driving customer turns. Frozen → safe to reference cross-node."""

    trial_n: int = Field(default=0, ge=0)
    """Trial counter. Story F multi-trial pass^k; Story B always 0."""

    # ────────────────────────────────────────────────────────────────────
    # Transcript + turn counter (LangGraph reducer)
    # ────────────────────────────────────────────────────────────────────

    transcript: Annotated[list[ConversationTurn], operator.add] = Field(default_factory=list)
    """Append-only reducer. Nodes return `{"transcript": [new_turn]}` partials."""

    current_turn: int = Field(default=0, ge=0)
    """0-indexed turn counter. Bumped by `_internal/increment_turn.py` (T-8)."""

    max_turns: int = Field(default=10, ge=1, le=20)
    """Hard cap — runner accepts user override at construction; upper bound 20."""

    # ────────────────────────────────────────────────────────────────────
    # Termination state (H3 max-iter guard + H8 registry signaling)
    # ────────────────────────────────────────────────────────────────────

    iterations: int = Field(default=0, ge=0)
    """Defense-in-depth max-iter — independent from current_turn so single
    simulation cannot infinite-loop even if customer/agent nodes mishandle
    transcript append. `should_continue` (T-8) checks `iterations >= max_turns + 5`.
    """

    is_finished: bool = False
    """Set True by terminal node (graph.add_conditional_edges → END)."""

    termination_reason: TerminationReason | None = None
    """Set by `evaluate_termination(state)` when registry matches."""

    error_subtype: AgentErrorSubtype | None = None
    """Set by agent_bridge or customer_node failure paths (H7 taxonomy)."""

    # ────────────────────────────────────────────────────────────────────
    # Last agent response cache (used by `_goal_completion_predicate` heuristic)
    # ────────────────────────────────────────────────────────────────────

    last_agent_response: str = ""
    """Last agent text for fast heuristic checks without scanning transcript."""

    # ────────────────────────────────────────────────────────────────────
    # Observability metadata (H5 — propagated to every callback write)
    # ────────────────────────────────────────────────────────────────────

    eval_metadata: dict[str, str | int] = Field(default_factory=dict)
    """Mandatory keys (set by runner at construction):
        - eval_run_kind: "simulator"
        - archetype_slug: str
        - actor_profile_id: str
        - trial_n: int
        - simulation_id: str(UUID)
        - run_id: str(UUID)

    Empty by default — runner populates pre-graph-invoke. Callback handler
    subclass (T-5) reads from state.config metadata, NOT from this field.
    Stored here for round-trip audit / artifact JSON.
    """


__all__ = ["SimulationState"]
