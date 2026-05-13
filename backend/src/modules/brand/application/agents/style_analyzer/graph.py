"""Style analyzer agent graph definition.

Two compiled graphs are exported:

``onboarding_app``
    Legacy 4-node graph (janitor → psychologist → researcher → architect → simulator).
    Used by the existing ``brand/api/style.py`` endpoint.  Not modified.

``personality_app``
    New 6-node graph for the Personality Engine:
    parser → janitor → psychologist → architect → embedder → simulator.
    Uses the structured PERSONALITY_PSYCHOLOGIST_PROMPT and PersonalityCompiler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph
from luana_core_brand_studio.application.agents.style_analyzer.nodes import (
    node_architect,
    node_embedder,
    node_janitor,
    node_parser,
    node_psychologist,
    node_simulator,
)
from luana_core_brand_studio.application.agents.style_analyzer.nodes_research import (
    node_researcher,
)
from luana_core_brand_studio.application.agents.style_analyzer.state import OnboardingState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def create_onboarding_graph() -> CompiledStateGraph:
    """Create legacy 4-node onboarding graph.

    Flow: janitor → psychologist → researcher → architect → simulator
    Entry point: START → janitor (raw_input must be set in state).
    """
    workflow = StateGraph(OnboardingState)

    # Add Nodes
    workflow.add_node("janitor", node_janitor)
    workflow.add_node("psychologist", node_psychologist)
    workflow.add_node("researcher", node_researcher)
    workflow.add_node("architect", node_architect)
    workflow.add_node("simulator", node_simulator)

    # Set Entry Point
    workflow.add_edge(START, "janitor")

    # Define Edges (Sequential)
    workflow.add_edge("janitor", "psychologist")
    workflow.add_edge("psychologist", "researcher")
    workflow.add_edge("researcher", "architect")
    workflow.add_edge("architect", "simulator")
    workflow.add_edge("simulator", END)

    return workflow.compile()


def create_personality_graph() -> CompiledStateGraph:
    """Create 6-node Personality Engine graph.

    Flow: parser → janitor → psychologist → architect → embedder → simulator

    - ``parser``: auto-detects format (WhatsApp/IG/Telegram) and sets parsed_messages
    - ``janitor``: LLM-based PII removal (uses cleaned_input set by parser)
    - ``psychologist``: uses PERSONALITY_PSYCHOLOGIST_PROMPT → personality_* fields
    - ``architect``: uses PersonalityCompiler.compile() → deterministic system_instruction
    - ``embedder``: upserts sample_exchanges as Qdrant style anchors (graceful degradation)
    - ``simulator``: generates example responses for validation

    Backward compatibility: ``node_psychologist`` and ``node_architect`` detect
    ``parsed_messages`` in state and switch automatically to the new path.
    """
    workflow = StateGraph(OnboardingState)

    # Add all 6 nodes
    workflow.add_node("parser", node_parser)
    workflow.add_node("janitor", node_janitor)
    workflow.add_node("psychologist", node_psychologist)
    workflow.add_node("architect", node_architect)
    workflow.add_node("embedder", node_embedder)
    workflow.add_node("simulator", node_simulator)

    # Set Entry Point
    workflow.add_edge(START, "parser")

    # Define Edges
    workflow.add_edge("parser", "janitor")
    workflow.add_edge("janitor", "psychologist")
    workflow.add_edge("psychologist", "architect")
    workflow.add_edge("architect", "embedder")
    workflow.add_edge("embedder", "simulator")
    workflow.add_edge("simulator", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------------------

# Legacy — used by brand/api/style.py (do not rename or remove)
onboarding_app = create_onboarding_graph()

# New Personality Engine graph
personality_app = create_personality_graph()
