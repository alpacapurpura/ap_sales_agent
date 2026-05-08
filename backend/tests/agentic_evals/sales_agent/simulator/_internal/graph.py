"""LangGraph topology for the eval simulator (T-8).

Compiles a single ReAct-style loop:

    customer_node -> agent_bridge -> increment_turn ->
        [conditional should_continue -> customer_node | END]

Anti-duplication §0
===================

Reuses verbatim from prior tickets — zero mirror:

* :func:`customer_node` from ``_internal/customer_node.py`` (T-6)
* :func:`agent_bridge` from ``_internal/agent_bridge.py`` (T-7)
* :class:`SimulationState` from ``simulator/state.py`` (T-4) with the
  ``transcript`` reducer (``Annotated[list, operator.add]``) declared on
  the BaseModel.
* :func:`evaluate_termination` from ``simulator/termination.py`` (T-4) —
  the H8 termination registry's public evaluation surface.

LangGraph cement
================

* NO future-annotations import is allowed (the ``__future__`` /
  ``annotations`` lazy-stringification path breaks LangGraph runtime
  introspection on the BaseModel state + node signatures; story-wide
  cement, same root cause as T-4..T-7).
* Nodes return PARTIAL state dicts; LangGraph applies declared reducers
  (e.g. ``operator.add`` for ``transcript``) and overwrites scalar fields.
* Conditional edges always have an exit branch — defense-in-depth
  ``iterations >= max_turns + 5`` ensures graph terminates even if the
  registry mishandles state.

# voseo-allowed: docstring quotes legacy reference + structlog event names
"""

# Story-wide cement (T-4..T-7): NO future-annotations import. LangGraph
# runtime introspection requires resolved annotations on the state model
# and the async node signatures defined here. The negative-grep verifier
# at the gate-runner level enforces this.

from typing import Any

import structlog
from langgraph.graph import END, StateGraph

from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
    agent_bridge,
)
from tests.agentic_evals.sales_agent.simulator._internal.customer_node import (
    customer_node,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    evaluate_termination,
)

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════
# Internal nodes — increment_turn (T-8 owns; not exported)
# ════════════════════════════════════════════════════════════════════════


async def increment_turn(state: SimulationState) -> dict[str, Any]:
    """LangGraph node: increment ``current_turn`` + ``iterations``.

    Pure async function — bumps the turn counter after the agent has
    responded so ``should_continue`` can apply the ``max_turns`` cap. Also
    increments ``iterations`` (independent counter for the H3 defense-in-
    depth max-iter guard).

    Returns a partial state dict (``current_turn`` + ``iterations``);
    LangGraph overwrites scalar fields. NEVER mutates ``state``.

    Args:
        state: Current :class:`SimulationState`.

    Returns:
        Partial state dict::

            {"current_turn": <state.current_turn + 1>,
             "iterations":   <state.iterations   + 1>}
    """
    return {
        "current_turn": state.current_turn + 1,
        "iterations": state.iterations + 1,
    }


# ════════════════════════════════════════════════════════════════════════
# Routing — conditional edge predicate
# ════════════════════════════════════════════════════════════════════════


def should_continue(state: SimulationState) -> str:
    """Conditional-edge function: return ``"continue"`` to loop or ``"end"``.

    Three exit conditions (in order of evaluation):

    1. **Hard max-iter guard (H3 defense-in-depth)** — if
       ``state.iterations >= state.max_turns + 5`` the graph terminates
       regardless of registry verdicts. Prevents infinite loops if the
       registry mishandles state mutation.
    2. **Already-finished signal** — if a prior node set
       ``state.is_finished = True`` (e.g. agent_bridge failure mode in
       T-7), terminate immediately.
    3. **Termination policy registry (H8)** — call
       :func:`evaluate_termination` which iterates registered policies
       (``max_turns``, ``customer_exit``, ``agent_error``,
       ``goal_completion``). First match → terminate.

    Args:
        state: Current :class:`SimulationState`.

    Returns:
        ``"continue"`` to loop back to ``customer_node`` or ``"end"`` to
        terminate via END.
    """
    # 1. Hard max-iter guard (defense-in-depth — independent of max_turns
    #    so registry bugs cannot infinite-loop the graph).
    if state.iterations >= state.max_turns + 5:
        logger.warning(
            "simulator.should_continue_max_iter_guard",
            simulation_id=str(state.simulation_id),
            iterations=state.iterations,
            max_turns=state.max_turns,
        )
        return "end"

    # 2. Already-finished signal (agent_bridge / customer_node failure modes).
    if state.is_finished:
        return "end"

    # 3. Termination policy registry (H8).
    reason = evaluate_termination(state)
    if reason is not None:
        return "end"

    return "continue"


# ════════════════════════════════════════════════════════════════════════
# Graph compose
# ════════════════════════════════════════════════════════════════════════


def build_simulation_graph() -> Any:
    """Compile the LangGraph ``StateGraph`` for the eval simulator.

    Topology (per 03-arch-agentic § 1):

        START -> customer_node -> agent_bridge -> increment_turn ->
            [should_continue -> customer_node | END]

    Returns:
        A compiled :class:`CompiledStateGraph` ready for ``ainvoke`` /
        ``astream``. NO checkpointer is wired — the eval simulator is
        single-shot per ``simulation_id`` (no resume; deterministic via
        H2 UUID5 + frozen ActorProfile).

        Return type is ``Any`` because LangGraph 0.6's
        ``CompiledStateGraph`` is a complex parametrized generic; mypy
        --strict refuses bare references. The runtime contract is
        ``.ainvoke(state) -> dict`` + ``.astream(state) -> AsyncIterator``.
    """
    g: Any = StateGraph(SimulationState)
    g.add_node("customer_node", customer_node)
    g.add_node("agent_bridge", agent_bridge)
    g.add_node("increment_turn", increment_turn)

    g.set_entry_point("customer_node")
    g.add_edge("customer_node", "agent_bridge")
    g.add_edge("agent_bridge", "increment_turn")
    g.add_conditional_edges(
        "increment_turn",
        should_continue,
        {"continue": "customer_node", "end": END},
    )

    return g.compile()


__all__ = ["build_simulation_graph", "increment_turn", "should_continue"]
