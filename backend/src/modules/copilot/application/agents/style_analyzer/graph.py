from langgraph.graph import StateGraph, START, END
from src.modules.copilot.application.agents.style_analyzer.state import OnboardingState
from src.modules.copilot.application.agents.style_analyzer.nodes import (
    node_janitor,
    node_psychologist,
    node_architect,
    node_simulator
)
from src.modules.copilot.application.agents.style_analyzer.nodes_research import node_researcher

def create_onboarding_graph():
    workflow = StateGraph(OnboardingState)
    
    # Add Nodes
    workflow.add_node("janitor", node_janitor)
    workflow.add_node("psychologist", node_psychologist)
    workflow.add_node("researcher", node_researcher)
    workflow.add_node("architect", node_architect)
    workflow.add_node("simulator", node_simulator)
    
    # Set Entry Point
    workflow.add_edge(START, "janitor")
    
    # Define Edges (Sequential for now)
    workflow.add_edge("janitor", "psychologist")
    workflow.add_edge("psychologist", "researcher") # Research after style analysis
    workflow.add_edge("researcher", "architect")    # Architect needs both
    workflow.add_edge("architect", "simulator")
    workflow.add_edge("simulator", END)
    
    return workflow.compile()

# Singleton instance
onboarding_app = create_onboarding_graph()
