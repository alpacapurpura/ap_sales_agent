from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.core.nodes import (
    node_entry_point,
    node_router,
    node_state_manager,
    node_response_generation,
    node_financial_enforcer
)

def route_logic(state: AgentState):
    """
    Determines the next step after the Router.
    """
    outcome = state.get("router_outcome", "sales_flow")
    
    if outcome == "critical_objection" or outcome == "handled_safety" or outcome == "direct_response":
        # Skip cognitive load (Manager) and go straight to Generator (Script/Response)
        return "generator"
    else:
        # Normal flow: Go to Manager for analysis
        return "manager"

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("entry", node_entry_point)
    workflow.add_node("router", node_router)
    workflow.add_node("manager", node_state_manager)
    workflow.add_node("generator", node_response_generation)
    workflow.add_node("financial", node_financial_enforcer)
    
    # Define edges
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "router")
    
    # Conditional Edge: Router -> Manager OR Generator
    workflow.add_conditional_edges(
        "router",
        route_logic,
        {
            "manager": "manager",
            "generator": "generator"
        }
    )
    
    workflow.add_edge("manager", "generator")
    workflow.add_edge("generator", "financial")
    workflow.add_edge("financial", END)
    
    return workflow.compile()

agent_app = create_agent_graph()
