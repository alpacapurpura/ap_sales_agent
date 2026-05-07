"""Eval simulator — public API surface.

T-4 STUB: T-9 finalizes the public ``__all__`` per H9 (exact 7 names).
Story B intermediate deliverable — currently exposes only the foundational
Pydantic classes + termination registry needed by T-5..T-8 builders.

T-9 will bind ``run_simulation`` (from ``_internal/runner.py``) to complete
the surface:

    __all__ = [
        "run_simulation",       # T-9 binds — runner orchestrator
        "SimulationResult",
        "SimulationState",
        "ActorProfile",
        "TerminationReason",
        "AgentErrorSubtype",
        "register_termination_policy",
    ]

Arch fitness gate ``test_simulator_public_api_surface.py`` (T-9 deliverable)
enforces the final exact 7-name surface.

# voseo-allowed: docstring nota dialect rule arch fitness gate
"""

# T-4 partial public surface — used by T-5..T-8 internal builders.
# T-9 will replace this stub with run_simulation + frozen __all__ list.

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    CostSummary,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
    register_termination_policy,
)


# T-4 stub surface — T-9 will bind run_simulation and freeze to exactly 7 names.
__all__ = [
    "ActorProfile",
    "AgentErrorSubtype",
    "ConversationTurn",
    "CostSummary",
    "SimulationResult",
    "SimulationState",
    "TerminationReason",
    "register_termination_policy",
]
