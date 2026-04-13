"""Style analyzer agent graph definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from src.modules.brand.application.agents.style_analyzer.nodes import (
    node_architect,
    node_janitor,
    node_psychologist,
    node_simulator,
)
from src.modules.brand.application.agents.style_analyzer.nodes_research import (
    node_researcher,
)
from src.modules.brand.application.agents.style_analyzer.state import OnboardingState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def create_onboarding_graph() -> CompiledStateGraph:
    """Create onboarding graph."""
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
    workflow.add_edge("psychologist", "researcher")
    workflow.add_edge("researcher", "architect")
    workflow.add_edge("architect", "simulator")
    workflow.add_edge("simulator", END)

    return workflow.compile()


# Singleton instance
onboarding_app = create_onboarding_graph()
