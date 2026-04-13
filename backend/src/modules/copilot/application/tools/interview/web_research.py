"""Web research tool for the Interview Engine.

Allows the interview agent to search the web for competitor analysis,
pricing benchmarks, and niche insights during offer/buyer-persona interviews.
"""

from __future__ import annotations

import json

from langchain_core.tools import tool

from src.modules.copilot.infrastructure.web.tavily_search import TavilySearchService


@tool
async def web_research(query: str, max_results: int = 5) -> str:
    """Search the web for competitor analysis, pricing benchmarks, and niche insights.

    Use this tool to research the user's market: competitor offers, pricing,
    best practices, and industry trends. Returns structured search results.

    Args:
        query: Search query describing what to research.
        max_results: Maximum number of results to return (default 5).
    """
    service = TavilySearchService()
    results = await service.search(query=query, max_results=max_results)

    return json.dumps(
        {
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content_snippet,
                    "relevance": r.relevance_score,
                }
                for r in results
            ]
        },
        ensure_ascii=False,
    )
