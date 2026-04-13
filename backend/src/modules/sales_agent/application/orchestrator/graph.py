from typing import Any

from langgraph.graph import END, START, StateGraph

from src.modules.sales_agent.application.agents.sales.graph import sales_app
from src.modules.sales_agent.application.orchestrator.state import AgentState
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node


# Nodes
@trace_node("main_supervisor")
def supervisor_node(state: AgentState) -> dict[str, str]:
    """
    Main entry point. Routes to sub-agents.
    """
    # For now, simple pass-through to Sales Agent
    return {"next_node": "sales_agent"}


@trace_node("sales_agent_subgraph_wrapper")
def sales_agent_node(state: AgentState) -> dict[str, Any]:
    """
    Wraps the Sales Subgraph.
    """
    # Invoke the subgraph here
    result = sales_app.invoke(state)
    return result


# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sales_agent", sales_agent_node)

workflow.add_edge(START, "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_node"],
    {"sales_agent": "sales_agent", "end": END},
)

workflow.add_edge("sales_agent", END)

agent_app = workflow.compile()
