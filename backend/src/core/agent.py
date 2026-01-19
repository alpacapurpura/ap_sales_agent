from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.core.nodes import (
    node_entry_point,
    node_router,
    node_state_manager,
    node_response_generation,
    node_safety_layer,
    node_exit_point
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
    workflow.add_node("safety_layer", node_safety_layer) # Renamed from 'financial'
    workflow.add_node("exit_point", node_exit_point) # Final persistence layer
    
    # Edges
    workflow.set_entry_point("entry")
    
    # Entry -> Router
    workflow.add_edge("entry", "router")
    
    # Router Logic
    workflow.add_conditional_edges(
        "router",
        route_logic,
        {
            "manager": "manager",
            "generator": "generator",
            "end": END
        }
    )
    
    # Manager -> Generator
    workflow.add_edge("manager", "generator")
    
    # Generator -> Safety Layer (Final Check)
    workflow.add_edge("generator", "safety_layer")
    
    # Safety Layer -> Exit Point (Persistence)
    workflow.add_edge("safety_layer", "exit_point")
    
    # Exit Point -> END
    workflow.add_edge("exit_point", END)
    
    return workflow.compile()

agent_app = create_agent_graph()
