"""Unit tests for ``knowledge_search`` tool (F10 refactor).

Verifies the new signature (``query, domain?, methodology?, limit``),
the markdown citation-friendly output, and the fail-soft error path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.modules.copilot.application.tools.knowledge_search import (
    KNOWLEDGE_SEARCH_TOOLS,
    knowledge_search,
    knowledge_search_impl,
)
from src.modules.copilot.application.tools.knowledge_tools import KNOWLEDGE_TOOLS

if TYPE_CHECKING:
    import pytest


class _FakeStore:
    """Spy + canned responses store for tool tests."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[dict[str, Any]] = []
        self.raise_on_search: Exception | None = None

    def search(
        self,
        query: str,
        *,
        domain: str | None = None,
        methodology: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            {"query": query, "domain": domain, "methodology": methodology, "limit": limit},
        )
        if self.raise_on_search is not None:
            raise self.raise_on_search
        return self.results


def _result(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "abc",
        "score": 0.91,
        "content": "Hormozi value equation: dream outcome × likelihood / (delay × effort).",
        "category": "framework",
        "methodology": "hormozi",
        "domain": "offer",
        "breadcrumb": ["Hormozi", "Value Equation"],
        "source_doc": "02_hormozi_value_equation.md",
        "chunk_index": 0,
        "tags": [],
    }
    base.update(overrides)
    return base


def test_tool_signature_in_registry() -> None:
    """The tool exported by ``knowledge_tools`` is the new ``knowledge_search``."""
    assert [knowledge_search] == KNOWLEDGE_TOOLS
    assert [knowledge_search] == KNOWLEDGE_SEARCH_TOOLS
    assert knowledge_search.name == "knowledge_search"
    args_schema = knowledge_search.args_schema
    assert args_schema is not None
    assert "query" in args_schema.model_fields
    assert "domain" in args_schema.model_fields
    assert "methodology" in args_schema.model_fields
    assert "limit" in args_schema.model_fields
    assert "scope" not in args_schema.model_fields  # F10 retired ``scope``


def test_tool_returns_markdown_with_methodology_label() -> None:
    store = _FakeStore(results=[_result()])
    output = knowledge_search_impl(
        "cómo construyo un grand slam offer",
        store=store,
    )
    assert "Hormozi" in output
    assert "value equation" in output.lower()
    assert "Cita el método aplicado" in output
    assert store.calls == [
        {
            "query": "cómo construyo un grand slam offer",
            "domain": None,
            "methodology": None,
            "limit": 5,
        },
    ]


def test_tool_passes_domain_methodology_filters_through() -> None:
    store = _FakeStore(results=[_result()])
    knowledge_search_impl(
        "manejo objeciones precio",
        domain="objections",
        methodology="cialdini",
        limit=3,
        store=store,
    )
    assert store.calls[0]["domain"] == "objections"
    assert store.calls[0]["methodology"] == "cialdini"
    assert store.calls[0]["limit"] == 3


def test_tool_caps_limit_to_ten() -> None:
    store = _FakeStore(results=[_result()])
    knowledge_search_impl("x", limit=999, store=store)
    assert store.calls[0]["limit"] == 10


def test_tool_handles_empty_query() -> None:
    store = _FakeStore(results=[])
    output = knowledge_search_impl("   ", store=store)
    assert "Pregunta vacía" in output
    assert store.calls == []  # no query sent to store


def test_tool_handles_no_results() -> None:
    store = _FakeStore(results=[])
    output = knowledge_search_impl("tema raro sin chunks", store=store)
    assert "No encontré material curado" in output


def test_tool_handles_store_error_softly() -> None:
    store = _FakeStore(results=[])
    store.raise_on_search = RuntimeError("qdrant timeout")
    output = knowledge_search_impl("hormozi", store=store)
    assert "No pude consultar la base" in output


def test_tool_rejects_invalid_filters_gracefully() -> None:
    store = _FakeStore(results=[])
    output = knowledge_search_impl("x", domain="ufo", store=store)
    assert "Dominio inválido" in output
    output2 = knowledge_search_impl("x", methodology="not_a_method", store=store)
    assert "Metodología inválida" in output2


def test_tool_decorator_invocable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The wrapped LangChain tool must be invocable end-to-end (sanity).

    Stub ``MarketingKbStore`` so the test never opens a Qdrant connection.
    """
    fake = _FakeStore(results=[_result()])

    def _factory(*_a: Any, **_kw: Any) -> _FakeStore:
        return fake

    monkeypatch.setattr(
        "src.modules.copilot.application.tools.knowledge_search.MarketingKbStore",
        _factory,
    )
    result = knowledge_search.invoke(
        {"query": "test", "domain": None, "methodology": None, "limit": 5},
    )
    assert isinstance(result, str)
    assert "Hormozi" in result
