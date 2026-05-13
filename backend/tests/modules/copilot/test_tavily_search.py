"""Tests for TavilySearchService — infrastructure layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_copilot.infrastructure.web.tavily_search import (
    SearchResult,
    TavilySearchService,
)


@pytest.mark.asyncio
async def test_search_returns_results() -> None:
    """Test search returns parsed results."""
    mock_response = {
        "results": [
            {
                "title": "Coaching pricing 2026",
                "url": "https://example.com/pricing",
                "content": ("Average coaching program costs $500-$2000"),
                "score": 0.95,
            },
        ],
    }
    with patch(
        "luana_core_copilot.infrastructure.web.tavily_search.httpx.AsyncClient",
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        service = TavilySearchService(api_key="test-key")
        results = await service.search(
            "coaching pricing benchmark",
        )

        assert len(results) == 1
        assert results[0].title == "Coaching pricing 2026"
        assert results[0].url == "https://example.com/pricing"
        assert results[0].content_snippet == ("Average coaching program costs $500-$2000")
        assert results[0].relevance_score == 0.95


@pytest.mark.asyncio
async def test_search_with_empty_results() -> None:
    """Test search with no results returns empty list."""
    mock_response = {"results": []}
    with patch(
        "luana_core_copilot.infrastructure.web.tavily_search.httpx.AsyncClient",
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        service = TavilySearchService(api_key="test-key")
        results = await service.search(
            "nonexistent topic xyz",
        )

        assert results == []


@pytest.mark.asyncio
async def test_search_passes_correct_params() -> None:
    """Test search passes API key and params correctly."""
    mock_response = {"results": []}
    with patch(
        "luana_core_copilot.infrastructure.web.tavily_search.httpx.AsyncClient",
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        service = TavilySearchService(api_key="my-api-key")
        await service.search(
            "test query",
            max_results=3,
            search_depth="advanced",
        )

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.tavily.com/search"
        body = call_args[1]["json"]
        assert body["api_key"] == "my-api-key"
        assert body["query"] == "test query"
        assert body["max_results"] == 3
        assert body["search_depth"] == "advanced"


def test_search_result_dataclass() -> None:
    """Test SearchResult dataclass fields."""
    result = SearchResult(
        title="Test",
        url="https://example.com",
        content_snippet="Test content",
        relevance_score=0.8,
    )
    assert result.title == "Test"
    assert result.url == "https://example.com"
    assert result.content_snippet == "Test content"
    assert result.relevance_score == 0.8


def test_search_result_is_frozen() -> None:
    """Test SearchResult is immutable."""
    result = SearchResult(
        title="Test",
        url="https://example.com",
        content_snippet="Test content",
        relevance_score=0.8,
    )
    with pytest.raises(AttributeError):
        result.title = "Changed"
