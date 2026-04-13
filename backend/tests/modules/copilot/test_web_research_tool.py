"""Tests for web_research interview tool."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.copilot.application.tools.interview.web_research import (
    web_research,
)
from src.modules.copilot.infrastructure.web.tavily_search import (
    SearchResult,
)


@pytest.mark.asyncio
async def test_web_research_returns_results() -> None:
    """Test web_research returns parsed search results."""
    mock_results = [
        SearchResult(
            title="Coaching pricing 2026",
            url="https://example.com",
            content_snippet="Programs range $500-$2000",
            relevance_score=0.9,
        ),
        SearchResult(
            title="Online course pricing guide",
            url="https://example2.com",
            content_snippet=("Typical prices for digital products"),
            relevance_score=0.7,
        ),
    ]

    with patch(
        "src.modules.copilot.application.tools"
        ".interview.web_research.TavilySearchService",
    ) as mock_cls:
        mock_service = MagicMock()
        mock_service.search = AsyncMock(
            return_value=mock_results,
        )
        mock_cls.return_value = mock_service

        result = await web_research.ainvoke(
            {
                "query": "coaching pricing",
                "max_results": 3,
            },
        )
        parsed = json.loads(result)

        assert "results" in parsed
        assert len(parsed["results"]) == 2
        assert parsed["results"][0]["title"] == "Coaching pricing 2026"
        assert parsed["results"][0]["url"] == "https://example.com"
        assert parsed["results"][0]["content"] == "Programs range $500-$2000"
        assert parsed["results"][0]["relevance"] == 0.9

        mock_cls.assert_called_once()
        mock_service.search.assert_called_once_with(
            query="coaching pricing",
            max_results=3,
        )


@pytest.mark.asyncio
async def test_web_research_empty_results() -> None:
    """Test web_research with no results."""
    with patch(
        "src.modules.copilot.application.tools"
        ".interview.web_research.TavilySearchService",
    ) as mock_cls:
        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=[])
        mock_cls.return_value = mock_service

        result = await web_research.ainvoke(
            {
                "query": "nonexistent topic",
                "max_results": 5,
            },
        )
        parsed = json.loads(result)

        assert parsed["results"] == []


@pytest.mark.asyncio
async def test_web_research_default_max_results() -> None:
    """Test web_research defaults to 5 max results."""
    with patch(
        "src.modules.copilot.application.tools"
        ".interview.web_research.TavilySearchService",
    ) as mock_cls:
        mock_service = MagicMock()
        mock_service.search = AsyncMock(return_value=[])
        mock_cls.return_value = mock_service

        await web_research.ainvoke({"query": "test"})

        mock_service.search.assert_called_once_with(
            query="test",
            max_results=5,
        )


def test_web_research_is_a_tool() -> None:
    """Verify web_research is a LangChain tool."""
    assert hasattr(web_research, "name")
    assert web_research.name == "web_research"
