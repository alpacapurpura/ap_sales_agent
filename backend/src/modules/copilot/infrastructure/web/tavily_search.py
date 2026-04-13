"""Tavily web search service — purpose-built for AI agent research."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from src.core.config import settings

logger = structlog.get_logger()

TAVILY_API_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class SearchResult:
    """A single web search result."""

    title: str
    url: str
    content_snippet: str
    relevance_score: float


class TavilySearchService:
    """Web search via Tavily API — purpose-built for AI agents."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize with optional API key override."""
        self.api_key = api_key or settings.TAVILY_API_KEY

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> list[SearchResult]:
        """Search the web and return structured results.

        Args:
            query: Search query describing what to research.
            max_results: Maximum number of results to return.
            search_depth: 'basic' or 'advanced' (deeper, slower).

        Returns:
            List of SearchResult dataclasses sorted by relevance.

        """
        logger.info("tavily_search_start", query=query, max_results=max_results)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content_snippet=r.get("content", ""),
                relevance_score=r.get("score", 0.0),
            )
            for r in data.get("results", [])
        ]

        logger.info("tavily_search_done", query=query, results_count=len(results))
        return results
