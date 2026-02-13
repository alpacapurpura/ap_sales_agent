from langgraph.graph import StateGraph, END
from src.core.agents.web_extractor.state import WebExtractorState
from src.core.agents.web_extractor.nodes import fetch_html, extract_structured

def route_after_fetch(state: WebExtractorState):
    """
    If fetch failed, stop. Else proceed to extraction.
    """
    if state.get("error"):
        return END
    return "extract_structured"

# Define the graph
workflow = StateGraph(WebExtractorState)

# Add nodes
workflow.add_node("fetch_html", fetch_html)
workflow.add_node("extract_structured", extract_structured)

# Set entry point
workflow.set_entry_point("fetch_html")

# Add edges
workflow.add_conditional_edges(
    "fetch_html",
    route_after_fetch,
    {
        "extract_structured": "extract_structured",
        END: END
    }
)

workflow.add_edge("extract_structured", END)

# Compile
web_extractor_graph = workflow.compile()
