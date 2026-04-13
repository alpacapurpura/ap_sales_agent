from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class WebExtractorState(TypedDict):
    url: str
    content: str | None
    metadata: dict[str, Any] | None
    error: str | None


def extract_node(state: WebExtractorState) -> dict[str, str | dict[str, str]]:
    """
    Placeholder for web extraction logic.
    """
    # In real impl, this would use Firecrawl or similar
    return {
        "content": f"Mock content from {state['url']}",
        "metadata": {"title": "Mock Title"},
    }


workflow = StateGraph(WebExtractorState)
workflow.add_node("extract", extract_node)
workflow.add_edge(START, "extract")
workflow.add_edge("extract", END)

web_extractor_graph = workflow.compile()
