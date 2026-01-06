from langgraph.graph import StateGraph, END
from src.core.state import AgentState
from src.core.nodes import (
    node_entry_point,
    node_guardrails,
    node_intent_classifier,
    node_state_manager,
    node_response_generation,
    node_financial_enforcer
)

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("entry", node_entry_point)
    workflow.add_node("guardrails", node_guardrails)
    workflow.add_node("router", node_router) # Replaced classifier
    workflow.add_node("manager", node_state_manager)
    workflow.add_node("generator", node_response_generation)
    workflow.add_node("financial", node_financial_enforcer)
    
    # Define edges
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "guardrails")
    workflow.add_edge("guardrails", "router")
    
    # Conditional Edges from Router could be added here, but for now 
    # we channel everything through manager -> generator to keep it simple 
    # and let generator dispatch internal logic.
    # A more complex graph would branch here:
    # workflow.add_conditional_edges("router", route_logic)
    
    workflow.add_edge("router", "manager")
    workflow.add_edge("manager", "generator")
    workflow.add_edge("generator", "financial")
    workflow.add_edge("financial", END)
    
    return workflow.compile()

agent_app = create_agent_graph()
