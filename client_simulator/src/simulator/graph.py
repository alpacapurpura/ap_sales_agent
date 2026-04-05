import uuid
from datetime import datetime

import structlog
from langgraph.graph import END, StateGraph

from src.domain.enums import FinishReason, SimulationStatus
from src.domain.models import ConversationTurn, Simulation
from src.simulator.agent_bridge import agent_bridge
from src.simulator.customer_node import customer_node
from src.simulator.state import SimulationState
from src.simulator.termination import determine_finish_reason, should_continue

logger = structlog.get_logger()


def _increment_turn(state: SimulationState) -> dict:
    """Increment the turn counter after agent responds."""
    return {"current_turn": state["current_turn"] + 1}


def _route(state: SimulationState) -> str:
    return should_continue(state)


def build_simulation_graph() -> StateGraph:
    """Build the LangGraph simulation workflow."""
    graph = StateGraph(SimulationState)

    graph.add_node("customer_node", customer_node)
    graph.add_node("agent_bridge", agent_bridge)
    graph.add_node("increment_turn", _increment_turn)

    graph.set_entry_point("customer_node")
    graph.add_edge("customer_node", "agent_bridge")
    graph.add_edge("agent_bridge", "increment_turn")

    graph.add_conditional_edges(
        "increment_turn",
        _route,
        {
            "continue": "customer_node",
            "end": END,
        },
    )

    return graph.compile()


async def run_simulation(
    persona: dict,
    scenario: dict,
    simulation_id: str | None = None,
) -> Simulation:
    """Execute a full simulation and return the result."""
    sim_id = simulation_id or f"sim_{uuid.uuid4().hex[:8]}"
    user_id = f"sim_{uuid.uuid4().hex[:6]}"

    initial_state: SimulationState = {
        "simulation_id": sim_id,
        "persona": persona,
        "scenario": scenario,
        "turns": [],
        "current_turn": 0,
        "max_turns": scenario.get("max_turns", 20),
        "simulated_user_id": user_id,
        "is_finished": False,
        "finish_reason": None,
        "last_agent_response": "",
    }

    logger.info(
        "simulation_started",
        simulation_id=sim_id,
        persona=persona["name"],
        scenario=scenario["name"],
    )

    started_at = datetime.utcnow()
    graph = build_simulation_graph()

    try:
        final_state = await graph.ainvoke(initial_state)

        finish_reason_str = determine_finish_reason(final_state)
        finish_reason = FinishReason(finish_reason_str)

        turns = [
            ConversationTurn(
                turn_number=t["turn_number"],
                role=t["role"],
                content=t["content"],
                timestamp=datetime.fromisoformat(t["timestamp"])
                if isinstance(t["timestamp"], str)
                else t["timestamp"],
                metadata=t.get("metadata"),
            )
            for t in final_state["turns"]
        ]

        simulation = Simulation(
            id=sim_id,
            persona_id=persona["id"],
            scenario_id=scenario["id"],
            status=SimulationStatus.COMPLETED,
            turns=turns,
            finish_reason=finish_reason,
            started_at=started_at,
            completed_at=datetime.utcnow(),
        )

        logger.info(
            "simulation_completed",
            simulation_id=sim_id,
            turns=len(turns),
            finish_reason=finish_reason_str,
        )

        return simulation

    except Exception as e:
        logger.error("simulation_failed", simulation_id=sim_id, error=str(e))
        return Simulation(
            id=sim_id,
            persona_id=persona["id"],
            scenario_id=scenario["id"],
            status=SimulationStatus.FAILED,
            turns=[],
            finish_reason=FinishReason.AGENT_ERROR,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            error_message=str(e),
        )
