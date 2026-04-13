from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.modules.sales_agent.application.agents.sales.nodes import (
    node_closer,
    node_escalation,
    node_product_expert,
    node_qualifier,
    node_sales_supervisor,
    node_signal_accumulator,
    node_tool_executor,
)
from src.modules.sales_agent.application.orchestrator.state import AgentState


def _route_after_supervisor(state: AgentState) -> str:
    """Route from supervisor to the appropriate specialist or special node."""
    next_node = state.get("next_node", "qualifier")
    valid = {
        "qualifier",
        "product_expert",
        "closer",
        "tool_executor",
        "escalate",
        "respond",
    }
    if next_node in valid:
        return next_node
    return "qualifier"


def _route_after_accumulator(state: AgentState) -> str:
    """Route from signal_accumulator: either output to user (END) or execute a tool."""
    next_node = state.get("next_node", "respond")
    if next_node == "tool_executor":
        return "tool_executor"
    return "respond"


def create_sales_subgraph() -> CompiledStateGraph:
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("supervisor", node_sales_supervisor)
    workflow.add_node("qualifier", node_qualifier)
    workflow.add_node("product_expert", node_product_expert)
    workflow.add_node("closer", node_closer)
    workflow.add_node("signal_accumulator", node_signal_accumulator)
    workflow.add_node("tool_executor", node_tool_executor)
    workflow.add_node("escalation", node_escalation)

    # Entry
    workflow.add_edge(START, "supervisor")

    # Supervisor routes to specialists or special nodes
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "qualifier": "qualifier",
            "product_expert": "product_expert",
            "closer": "closer",
            "tool_executor": "tool_executor",
            "escalate": "escalation",
            "respond": END,
        },
    )

    # Every specialist → signal_accumulator
    workflow.add_edge("qualifier", "signal_accumulator")
    workflow.add_edge("product_expert", "signal_accumulator")
    workflow.add_edge("closer", "signal_accumulator")

    # Signal accumulator routes to END or tool_executor
    workflow.add_conditional_edges(
        "signal_accumulator",
        _route_after_accumulator,
        {
            "respond": END,
            "tool_executor": "tool_executor",
        },
    )

    # Tool executor loops back to supervisor
    workflow.add_edge("tool_executor", "supervisor")

    # Escalation → END
    workflow.add_edge("escalation", END)

    return workflow.compile()


sales_app = create_sales_subgraph()
