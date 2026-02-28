from langgraph.graph import StateGraph, END
from src.modules.sales_agent.application.orchestrator.state import AgentState

# Nodes
def supervisor_node(state: AgentState):
    """
    Main entry point. Routes to sub-agents.
    """
    # For now, simple pass-through to Sales Agent
    return {"next_node": "sales_agent"}

def sales_agent_node(state: AgentState):
    """
    Wraps the Sales Subgraph.
    """
    # In a real scenario, we'd invoke the subgraph here
    # result = sales_app.invoke(state)
    # return result
    
    # Placeholder behavior for initialization
    return {"messages": state["messages"]}

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sales_agent", sales_agent_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda x: x["next_node"],
    {
        "sales_agent": "sales_agent",
        "end": END
    }
)

workflow.add_edge("sales_agent", END)

agent_app = workflow.compile()
