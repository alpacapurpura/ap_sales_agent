"""Eval simulator — public API surface (Story B / T-9 + Story E / T-8 cement).

Story B exported EXACTLY 7 names per H9 (``03-arch-agentic.md §6``).
Story E (``sales-agent-voice-fidelity-grader-runtime``) expands the surface
to EXACTLY 8 names — single addition: ``grade_transcript_maj_eval`` (the
MAJ-EVAL multi-judge runtime grader entrypoint, defined in
``grader/_internal/maj_eval.py``).

Anything more = leakage; anything less = missing deliverable. Downstream
stories F/G/H/I consume ONLY these 8 names. Arch fitness gates
``test_simulator_public_api_surface.py`` (8-name frozen invariant) and
``test_grader_public_api_surface.py`` (grader package cero re-exports —
D-AG-16 cement) enforce together.

Public surface (frozen — 8 names post Story E)
==============================================

Functions
---------

* :func:`run_simulation` — async orchestrator (D1, Story B T-8). Drives
  one full eval simulation end-to-end.
* :func:`register_termination_policy` — H8 Strategy-pattern entry point
  for stories I/H/E to append predicates without touching core.
* :func:`grade_transcript_maj_eval` — async MAJ-EVAL multi-judge grader
  (Story E T-5). 3 heterogeneous judges (Sonnet/GPT-4o/Kimi) Round 1
  parallel + Round 2 conditional debate on variance > 0.15.

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
prompt v1, semaphore, llm roles registry) or ``grader/_internal/``
(judge registry, cache, judge prompts builder, MAJ-EVAL state machine).
The arch fitness gates ``test_simulator_no_mirrors_shared.py`` +
``test_grader_no_mirrors_shared.py`` police both ``_internal/`` trees
for accidental mirror duplication of shared abstractions.

Public surface frozen 8 names post Story E (H9 expand 7→8 — single
addition ``grade_transcript_maj_eval``). Future expansion requires
bumping H9 invariant in ``03-arch.md §3.6 / §4.10`` ratification cycle.

# voseo-allowed: docstring quotes downstream story names + dialect rule
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

from tests.agentic_evals.sales_agent.grader._internal.maj_eval import (
    grade_transcript_maj_eval,
)
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
# ``test_simulator_public_api_surface.py``. EXACTLY 8 names post Story E
# (H9 expand 7→8 — single addition ``grade_transcript_maj_eval``); sorted
# alphabetically for audit trail. NEVER add or remove without bumping H9
# invariant in ``03-arch.md §3.6 / §4.10`` ratification cycle.
__all__ = [
    "ActorProfile",
    "AgentErrorSubtype",
    "SimulationResult",
    "SimulationState",
    "TerminationReason",
    "grade_transcript_maj_eval",
    "register_termination_policy",
    "run_simulation",
]
