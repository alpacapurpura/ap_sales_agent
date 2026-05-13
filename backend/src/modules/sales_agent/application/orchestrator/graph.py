"""Graph application module."""

from typing import Any

from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END, START, StateGraph
from luana_core_sales_agent.application.agents.sales.graph import sales_app
from luana_core_sales_agent.application.orchestrator.state import AgentState
from luana_core_sales_agent.infrastructure.monitoring.tracing import trace_node


# Nodes
@trace_node("main_supervisor")
def supervisor_node(state: AgentState) -> dict[str, str]:
    """Route to sub-agents as the main entry point."""
    # For now, simple pass-through to Sales Agent
    return {"next_node": "sales_agent"}


@trace_node("sales_agent_subgraph_wrapper")
def sales_agent_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Invoke the Sales Subgraph.

    LangGraph injects ``config`` (the parent ``RunnableConfig``) when the
    node signature declares it. Forwarding ``config`` to ``sales_app.invoke``
    propagates the observability callback handler bound by the
    orchestrator (``chat.py``) to every nested LLM / tool / chain event
    inside the sales subgraph. Without this forward the nested invoke is
    treated as opaque by LangGraph and the handler never sees the inner
    nodes (qualifier / closer / signal_accumulator / tool_executor).
    """
    return sales_app.invoke(state, config=config)


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
