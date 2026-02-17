from langgraph.graph import StateGraph, END
from src.core.agents.web_extractor.state import WebExtractorState
from src.core.agents.web_extractor.nodes import fetch_html, extract_structured

def scheduler_node(state: WebExtractorState):
    """
    Picks the next URL from the queue to process.
    If queue is empty, sets current_url to None to signal end.
    """
    queue = state.get("queue", [])
    
    # If queue is empty, we are done crawling
    if not queue:
        return {"current_url": None}
    
    # Pop the next URL (BFS)
    next_url = queue[0]
    new_queue = queue[1:]
    
    # Determine depth
    # If it's the base_url, depth is 0.
    # Otherwise, it's a discovered link, so depth is at least 1.
    # Since we only support 1-level deep crawling effectively without tuple-queue,
    # we assume everything else is depth 1.
    depth = 0 if next_url == state.get("base_url") else 1
    
    return {"current_url": next_url, "queue": new_queue, "depth": depth}

def router_after_scheduler(state: WebExtractorState):
    """
    Decides whether to fetch the next URL or proceed to extraction.
    """
    if state.get("current_url") is None:
        return "extract_structured"
    return "fetch_html"

# Define the graph
workflow = StateGraph(WebExtractorState)

# Add nodes
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("fetch_html", fetch_html)
workflow.add_node("extract_structured", extract_structured)

# Set entry point
workflow.set_entry_point("scheduler")

# Add edges
workflow.add_conditional_edges(
    "scheduler",
    router_after_scheduler,
    {
        "fetch_html": "fetch_html",
        "extract_structured": "extract_structured"
    }
)

workflow.add_edge("fetch_html", "scheduler")
workflow.add_edge("extract_structured", END)

# Compile
web_extractor_graph = workflow.compile()
