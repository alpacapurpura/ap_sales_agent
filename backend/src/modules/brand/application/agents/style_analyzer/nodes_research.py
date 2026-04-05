from typing import Any

from src.modules.brand.application.agents.style_analyzer.state import OnboardingState


class _ResearchService:
    """Placeholder research service for style analyzer."""

    def search(self, query: str) -> str:
        return f"Mock search results for: {query}"

    def analyze_url(self, url: str) -> str:
        return f"Mock analysis for: {url}"


_research_service = _ResearchService()


def node_researcher(state: OnboardingState) -> dict[str, Any]:
    """
    Research Agent: Scrapes the target URL to enrich the offer context.
    """
    target_url = state.get("target_url")

    if not target_url:
        return {"research_summary": "No URL provided for research."}

    try:
        search_results = _research_service.search(
            f"site:{target_url} OR related:{target_url}"
        )
        page_analysis = _research_service.analyze_url(target_url)
        summary = f"Landing Page Analysis:\n{page_analysis}\n\nSearch Context:\n{search_results}"
        return {"research_summary": summary}

    except Exception as e:
        return {"research_summary": f"Research failed: {e!s}", "error": str(e)}
