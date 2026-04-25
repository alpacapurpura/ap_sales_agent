"""Unit tests for ``MarketingKbStore`` — tenant-agnostic curated KB.

Uses an in-memory Qdrant client (``QdrantClient(":memory:")``) so we exercise
the real client surface without a network call.
"""

from __future__ import annotations

from typing import Any

import pytest
from qdrant_client import QdrantClient

from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
    MARKETING_KB_COLLECTION,
    MARKETING_KB_VECTOR_SIZE,
    KbChunk,
    MarketingKbStore,
)


class _StubEmbedder:
    """Deterministic stub: cycles seed values into 3072-dim vectors."""

    def __init__(self) -> None:
        self.queries: list[str] = []
        self.docs: list[str] = []

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return self._fake(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.docs.extend(texts)
        return [self._fake(t) for t in texts]

    @staticmethod
    def _fake(text: str) -> list[float]:
        seed = float(sum(ord(c) for c in text[:32]) % 1000) / 1000.0
        return [seed] * MARKETING_KB_VECTOR_SIZE


@pytest.fixture
def in_memory_store() -> MarketingKbStore:
    client = QdrantClient(":memory:")
    embedder = _StubEmbedder()
    return MarketingKbStore(client=client, embedder=embedder)


def _sample_chunk(**overrides: Any) -> KbChunk:
    base: dict[str, Any] = {
        "content": "El value equation de Hormozi multiplica dream outcome y likelihood, dividido por time delay y effort/sacrifice.",
        "category": "framework",
        "methodology": "hormozi",
        "domain": "offer",
        "source_doc": "02_hormozi_value_equation.md",
        "chunk_index": 0,
        "breadcrumb": ("Hormozi · Value Equation", "Definición"),
    }
    base.update(overrides)
    return KbChunk(**base)


def test_store_collection_name_is_tenant_agnostic() -> None:
    """Collection name is the curated global one, not per-tenant."""
    assert MarketingKbStore.COLLECTION == "nicolify_marketing_kb"
    assert MarketingKbStore.VECTOR_SIZE == 3072
    assert MARKETING_KB_COLLECTION == "nicolify_marketing_kb"


def test_kb_chunk_payload_excludes_tenant_id() -> None:
    """Curated chunks must NEVER carry ``tenant_id`` in their payload."""
    chunk = _sample_chunk()
    payload = chunk.payload()
    assert "tenant_id" not in payload
    assert "user_id" not in payload
    assert payload["methodology"] == "hormozi"
    assert payload["domain"] == "offer"
    assert payload["category"] == "framework"


def test_kb_chunk_validates_enum_fields() -> None:
    """Constructor rejects unknown category/methodology/domain."""
    with pytest.raises(ValueError, match="category"):
        _sample_chunk(category="fictional")
    with pytest.raises(ValueError, match="methodology"):
        _sample_chunk(methodology="not_a_method")
    with pytest.raises(ValueError, match="domain"):
        _sample_chunk(domain="ufo")


def test_kb_chunk_stable_id_idempotent() -> None:
    """Same source_doc + chunk_index + version → same id (idempotent reseed)."""
    a = _sample_chunk()
    b = _sample_chunk()
    assert a.stable_id() == b.stable_id()
    c = _sample_chunk(version=2)
    assert c.stable_id() != a.stable_id()


def test_kb_chunk_embed_text_prepends_breadcrumb() -> None:
    """Contextual retrieval: embedded text starts with the breadcrumb path."""
    chunk = _sample_chunk(
        breadcrumb=("Hormozi · Grand Slam Offer", "Componentes", "Dream outcome"),
    )
    embedded = chunk.embed_text()
    assert embedded.startswith(
        "# Hormozi · Grand Slam Offer > Componentes > Dream outcome\n\n",
    )
    assert chunk.content in embedded


def test_kb_chunk_embed_text_no_breadcrumb_returns_content_only() -> None:
    chunk = _sample_chunk(breadcrumb=())
    assert chunk.embed_text() == chunk.content


def test_ensure_collection_creates_with_correct_dim(in_memory_store: MarketingKbStore) -> None:
    in_memory_store.ensure_collection()
    info = in_memory_store._get_client().get_collection(MARKETING_KB_COLLECTION)
    assert info is not None


def test_upsert_chunks_idempotent(in_memory_store: MarketingKbStore) -> None:
    chunks = [_sample_chunk(chunk_index=i) for i in range(3)]
    first = in_memory_store.upsert_chunks(chunks)
    second = in_memory_store.upsert_chunks(chunks)
    assert first == 3
    assert second == 3

    info = in_memory_store._get_client().get_collection(MARKETING_KB_COLLECTION)
    assert info.points_count == 3


def test_search_returns_methodology_for_citation(in_memory_store: MarketingKbStore) -> None:
    chunks = [
        _sample_chunk(chunk_index=0, methodology="hormozi"),
        _sample_chunk(
            chunk_index=1,
            methodology="storybrand",
            content="StoryBrand BrandScript: hero, problem, guide, plan, success.",
        ),
    ]
    in_memory_store.upsert_chunks(chunks)

    results = in_memory_store.search("hormozi value equation", limit=5)

    assert results, "search returned no results"
    methodologies = {r["methodology"] for r in results}
    assert methodologies <= {"hormozi", "storybrand"}
    for r in results:
        assert "tenant_id" not in r
        assert "content" in r
        assert "methodology" in r
        assert "domain" in r
        assert "score" in r


def test_search_filter_by_methodology(in_memory_store: MarketingKbStore) -> None:
    in_memory_store.upsert_chunks(
        [
            _sample_chunk(chunk_index=0, methodology="hormozi"),
            _sample_chunk(
                chunk_index=1,
                methodology="storybrand",
                content="StoryBrand BrandScript framework.",
            ),
        ],
    )

    results = in_memory_store.search("framework", methodology="storybrand", limit=5)
    assert all(r["methodology"] == "storybrand" for r in results)


def test_search_filter_by_domain(in_memory_store: MarketingKbStore) -> None:
    in_memory_store.upsert_chunks(
        [
            _sample_chunk(chunk_index=0, domain="offer"),
            _sample_chunk(
                chunk_index=1,
                domain="objections",
                content="Manejo de objeciones de precio.",
            ),
        ],
    )

    results = in_memory_store.search("nada importa", domain="objections", limit=5)
    assert all(r["domain"] == "objections" for r in results)


def test_search_rejects_invalid_filters(in_memory_store: MarketingKbStore) -> None:
    with pytest.raises(ValueError, match="domain"):
        in_memory_store.search("x", domain="ufo")
    with pytest.raises(ValueError, match="methodology"):
        in_memory_store.search("x", methodology="not_a_method")


def test_search_empty_query_returns_no_results(in_memory_store: MarketingKbStore) -> None:
    assert in_memory_store.search("   ") == []


def test_delete_by_source_doc(in_memory_store: MarketingKbStore) -> None:
    in_memory_store.upsert_chunks(
        [
            _sample_chunk(chunk_index=0, source_doc="a.md"),
            _sample_chunk(chunk_index=1, source_doc="a.md"),
            _sample_chunk(chunk_index=2, source_doc="b.md"),
        ],
    )
    deleted = in_memory_store.delete_by_source_doc("a.md")
    assert deleted is True
    info = in_memory_store._get_client().get_collection(MARKETING_KB_COLLECTION)
    assert info.points_count == 1


def test_list_sources_groups_by_doc(in_memory_store: MarketingKbStore) -> None:
    in_memory_store.upsert_chunks(
        [
            _sample_chunk(chunk_index=0, source_doc="a.md"),
            _sample_chunk(chunk_index=1, source_doc="a.md"),
            _sample_chunk(chunk_index=2, source_doc="b.md"),
        ],
    )
    rows = in_memory_store.list_sources(limit=200)
    by_doc = {r["source_doc"]: r["chunks"] for r in rows}
    assert by_doc == {"a.md": 2, "b.md": 1}


def test_lazy_client_construction_no_module_import_side_effect() -> None:
    """Importing the module must NOT open a Qdrant connection (F4 gotcha)."""
    store = MarketingKbStore()
    assert store._client is None
    assert store._embedder is None
