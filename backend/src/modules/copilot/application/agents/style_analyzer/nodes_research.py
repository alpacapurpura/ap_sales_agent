"""Copilot style analyzer research node functions."""

from typing import Any

from src.modules.copilot.application.agents.style_analyzer.state import OnboardingState
from src.modules.copilot.application.tools.research import research_service
from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node


@trace_node("researcher")
def node_researcher(state: OnboardingState) -> dict[str, Any]:
    """Research Agent: Scrapes the target URL to enrich the offer context."""
    target_url = state.get("target_url")

    if not target_url:
        return {"research_summary": "No URL provided for research."}

    try:
        # 1. Search for brand reputation/context
        search_results = research_service.search(
            f"site:{target_url} OR related:{target_url}",
        )

        # 2. Analyze the specific landing page (Mocked in tool for now)
        page_analysis = research_service.analyze_url(target_url)

        summary = f"Landing Page Analysis:\n{page_analysis}\n\nSearch Context:\n{search_results}"

    except Exception as e:  # noqa: BLE001 — copilot resilience
        return {"research_summary": f"Research failed: {e!s}", "error": str(e)}
    else:
        return {"research_summary": summary}
