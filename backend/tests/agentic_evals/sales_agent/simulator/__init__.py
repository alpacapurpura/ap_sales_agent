"""Eval simulator — public API surface (Story B / T-9 cement).

Story B exports EXACTLY 7 names per H9 (``03-arch-agentic.md §6``).
Anything more = leakage; anything less = missing deliverable. Downstream
stories C/D/E/F/G/H/I consume ONLY these 7 names. Arch fitness gate
``test_simulator_public_api_surface.py`` enforces.

Public surface (frozen)
=======================

Functions
---------

* :func:`run_simulation` — async orchestrator (D1, T-8). Drives one
  full eval simulation end-to-end.
* :func:`register_termination_policy` — H8 Strategy-pattern entry point
  for stories I/H/E to append predicates without touching core.

Types
-----

* :class:`SimulationResult` — Pydantic v2 frozen result returned by
  ``run_simulation``. Also serialized to ``_artifacts/...`` JSON.
* :class:`SimulationState` — LangGraph Pydantic state machine (D4).
* :class:`ActorProfile` — Strands ActorProfile pattern (D7).
* :class:`TerminationReason` — StrEnum 6 values (D5).
* :class:`AgentErrorSubtype` — StrEnum 4 values (H7 taxonomy).

Internal namespace
==================

Anything else lives under ``simulator/_internal/`` (graph compose,
nodes, observability subclasses, schema migrations registry, customer
prompt v1, semaphore, llm roles registry). The arch fitness gate
``test_simulator_no_mirrors_shared.py`` polices the ``_internal/`` tree
for accidental mirror duplication of shared abstractions.

# voseo-allowed: docstring quotes downstream story names + dialect rule
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

from tests.agentic_evals.sales_agent.simulator._internal.runner import (
    run_simulation,
)
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import SimulationResult
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
    register_termination_policy,
)


# Frozen public surface — H9 cement enforced by arch fitness gate
# ``test_simulator_public_api_surface.py``. EXACTLY 7 names; sorted
# alphabetically for audit trail. NEVER add or remove without bumping
# H9 invariant in ``03-arch-agentic.md §6``.
__all__ = [
    "ActorProfile",
    "AgentErrorSubtype",
    "SimulationResult",
    "SimulationState",
    "TerminationReason",
    "register_termination_policy",
    "run_simulation",
]
