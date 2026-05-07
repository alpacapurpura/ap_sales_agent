"""Termination policy registry — Strategy pattern (H8).

Public API (H9): `register_termination_policy(name, predicate)` + `TerminationReason`
+ `AgentErrorSubtype`.

Default 4 policies registered at module import time:
    - goal_completion_predicate
    - max_turns_predicate
    - customer_exit_predicate
    - agent_error_predicate

Story I appends `register_termination_policy("adversarial_detected", adversarial_predicate)`.
Story H appends `register_termination_policy("budget_exceeded", budget_predicate)`.

Decision D5 (spec): 6-value TerminationReason enum + 4-value AgentErrorSubtype.
Both StrEnum (Python 3.11+) for trivial string round-tripping in JSON artifacts.

# voseo-allowed: comments documentation reference dialect glossary explicitly
"""

# NO `from __future__ import annotations` — keeps runtime introspection simple
# for arch-fitness gates that lookup TerminationPredicate type.

from enum import StrEnum
from typing import TYPE_CHECKING
from collections.abc import Callable

if TYPE_CHECKING:
    from tests.agentic_evals.sales_agent.simulator.state import SimulationState


# ════════════════════════════════════════════════════════════════════════
# Enums per spec decision D5
# ════════════════════════════════════════════════════════════════════════


class TerminationReason(StrEnum):
    """Why the simulation ended.

    Values pre-allocated for Story B (4 active) + Story I (adversarial_detected)
    + Story H (budget_exceeded). Adding a value DOES NOT touch core — story
    appends own predicate to TERMINATION_POLICIES.
    """

    GOAL_COMPLETION = "goal_completion"
    MAX_TURNS = "max_turns"
    CUSTOMER_EXIT = "customer_exit"
    AGENT_ERROR = "agent_error"
    ADVERSARIAL_DETECTED = "adversarial_detected"
    BUDGET_EXCEEDED = "budget_exceeded"


class AgentErrorSubtype(StrEnum):
    """Failure-mode taxonomy when termination_reason == AGENT_ERROR (H7).

    Mapped 1:1 from agent_bridge failure paths (T-7 implements):
    - TIMEOUT — agent_app.ainvoke exceeded wallclock
    - EMPTY_RESPONSE — agent returned blank string (silent failure)
    - HTTP_ERROR — upstream LLM provider 5xx / network error
    - INVALID_STATE — state shape rejected by agent_app or unexpected exception
    """

    TIMEOUT = "timeout"
    EMPTY_RESPONSE = "empty_response"
    HTTP_ERROR = "http_error"
    INVALID_STATE = "invalid_state"


# ════════════════════════════════════════════════════════════════════════
# Registry per hardening invariant H8 (Strategy pattern)
# ════════════════════════════════════════════════════════════════════════

# Predicate signature: receives full SimulationState → returns matching reason
# (or None when no match). Registered policies are evaluated in registration
# order until one returns a reason.
TerminationPredicate = Callable[["SimulationState"], "TerminationReason | None"]


# Public dict — story I/H append to it directly OR via register_termination_policy.
# Insertion order preserved (Python 3.7+ dict guarantee) → evaluation order
# matches registration order.
TERMINATION_POLICIES: dict[str, TerminationPredicate] = {}


def register_termination_policy(name: str, predicate: TerminationPredicate) -> None:
    """Register (or overwrite) a termination policy.

    Idempotent on `name` — re-registration overrides previous predicate.
    Predicate must be callable; non-callable raises TypeError.

    Args:
        name: stable identifier (e.g., "max_turns", "budget_exceeded").
        predicate: ``Callable[[SimulationState], TerminationReason | None]``
            returning the matched reason or None when no match.

    Raises:
        TypeError: when ``predicate`` is not callable.
    """
    if not callable(predicate):
        msg = f"predicate must be callable, got {type(predicate).__name__}"
        raise TypeError(msg)
    TERMINATION_POLICIES[name] = predicate


# ════════════════════════════════════════════════════════════════════════
# Default predicates (registered at module import)
# ════════════════════════════════════════════════════════════════════════


def _max_turns_predicate(state: "SimulationState") -> "TerminationReason | None":
    """Hard cap on turns — primary termination signal."""
    if state.current_turn >= state.max_turns:
        return TerminationReason.MAX_TURNS
    return None


def _customer_exit_predicate(state: "SimulationState") -> "TerminationReason | None":
    """Customer wrote `[EXIT]` token in latest turn (declared abandonment)."""
    if not state.transcript:
        return None
    last = state.transcript[-1]
    if last.role == "customer" and "[EXIT]" in last.content:
        return TerminationReason.CUSTOMER_EXIT
    return None


def _agent_error_predicate(state: "SimulationState") -> "TerminationReason | None":
    """Agent_bridge or customer_node already flagged an unrecoverable error.

    Sets `is_finished=True` + `termination_reason=AGENT_ERROR` on the state
    when downstream node signals failure (via partial state return). This
    predicate echoes that decision so the runtime termination evaluation
    surface remains uniform.
    """
    if state.is_finished and state.termination_reason == TerminationReason.AGENT_ERROR:
        return TerminationReason.AGENT_ERROR
    # Also catch: when error_subtype is set but is_finished mounted via different node
    if state.error_subtype is not None:
        return TerminationReason.AGENT_ERROR
    return None


def _goal_completion_predicate(_state: "SimulationState") -> "TerminationReason | None":
    """Story B baseline: predicate stub.

    Heuristic-based goal-completion signal (e.g., agent emits closing language)
    is reserved for Story E (MAJ-EVAL multi-judge debate grader). Story B
    registers the slot but always returns None — termination falls through to
    max_turns or customer_exit.

    NOTE: keeping this stub here is intentional — gives Story I/H/E a stable
    handle (`register_termination_policy("goal_completion", ...)` overrides
    via idempotent name) without needing to mutate the default-policy list.
    """
    return None


# Default policies registered at import (idempotent — re-import safe)
register_termination_policy("max_turns", _max_turns_predicate)
register_termination_policy("customer_exit", _customer_exit_predicate)
register_termination_policy("agent_error", _agent_error_predicate)
register_termination_policy("goal_completion", _goal_completion_predicate)


# ════════════════════════════════════════════════════════════════════════
# Public evaluation surface (used by `_internal/routing.should_continue` in T-8)
# ════════════════════════════════════════════════════════════════════════


def evaluate_termination(state: "SimulationState") -> "TerminationReason | None":
    """Iterate registered policies in registration order; return first match.

    Returns:
        TerminationReason if any policy matches; None when graph should continue.
    """
    for predicate in TERMINATION_POLICIES.values():
        reason = predicate(state)
        if reason is not None:
            return reason
    return None


__all__ = [
    "TERMINATION_POLICIES",
    "AgentErrorSubtype",
    "TerminationPredicate",
    "TerminationReason",
    "evaluate_termination",
    "register_termination_policy",
]
