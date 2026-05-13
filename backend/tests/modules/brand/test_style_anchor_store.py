"""Tests for StyleAnchorStore — tenant-isolated Qdrant store for personality anchors."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from luana_core_brand_studio.infrastructure.qdrant.style_anchor_store import (
    COLLECTION_NAME,
    StyleAnchorStore,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
PROFILE_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
PROFILE_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
FIXED_VECTOR = [0.1] * 1536

_SAMPLE_EXCHANGES = [
    {
        "context_type": "objection",
        "other_message": "No tengo dinero.",
        "author_response": "¡Te entiendo! Tenemos opciones de pago flexible.",
    },
    {
        "context_type": "closing",
        "other_message": "¿Cuándo empieza el programa?",
        "author_response": "¡Hoy mismo! Solo falta un paso.",
    },
]


async def _fixed_embedding_fn(text: str) -> list[float]:
    return FIXED_VECTOR


@pytest.fixture
def mock_qdrant():
    """Mock QdrantClient with all relevant methods."""
    client = MagicMock()
    # get_collections returns a mock with empty .collections list by default
    client.get_collections.return_value = MagicMock(collections=[])
    client.create_collection.return_value = None
    client.upsert.return_value = None
    client.query_points.return_value = MagicMock(points=[])
    client.delete.return_value = None
    return client


@pytest.fixture
def store(mock_qdrant):
    return StyleAnchorStore(
        qdrant_client=mock_qdrant,
        embedding_fn=_fixed_embedding_fn,
    )


# ---------------------------------------------------------------------------
# ensure_collection
# ---------------------------------------------------------------------------


async def test_ensure_collection_creates_when_missing(store, mock_qdrant):
    """ensure_collection should call create_collection when it doesn't exist."""
    mock_qdrant.get_collections.return_value = MagicMock(collections=[])

    await store.ensure_collection()

    mock_qdrant.create_collection.assert_called_once()
    call_kwargs = mock_qdrant.create_collection.call_args
    assert call_kwargs.kwargs["collection_name"] == COLLECTION_NAME


async def test_ensure_collection_skips_when_exists(store, mock_qdrant):
    """ensure_collection should NOT call create_collection if already exists."""
    existing = MagicMock()
    existing.name = COLLECTION_NAME
    mock_qdrant.get_collections.return_value = MagicMock(collections=[existing])

    await store.ensure_collection()

    mock_qdrant.create_collection.assert_not_called()


# ---------------------------------------------------------------------------
# upsert_anchors
# ---------------------------------------------------------------------------


async def test_upsert_returns_count(store, mock_qdrant):
    """upsert_anchors should return the number of exchanges upserted."""
    count = await store.upsert_anchors(TENANT_A, PROFILE_A, _SAMPLE_EXCHANGES)

    assert count == len(_SAMPLE_EXCHANGES)


async def test_upsert_anchors_correct_payload_structure(store, mock_qdrant):
    """Each point upserted must carry tenant_id, profile_id, context_type, other_message, author_response."""
    await store.upsert_anchors(TENANT_A, PROFILE_A, _SAMPLE_EXCHANGES)

    mock_qdrant.upsert.assert_called_once()
    call_kwargs = mock_qdrant.upsert.call_args
    assert call_kwargs.kwargs["collection_name"] == COLLECTION_NAME

    points = call_kwargs.kwargs["points"]
    assert len(points) == len(_SAMPLE_EXCHANGES)

    for point, exchange in zip(points, _SAMPLE_EXCHANGES, strict=True):
        payload = point.payload
        assert payload["tenant_id"] == str(TENANT_A)
        assert payload["profile_id"] == str(PROFILE_A)
        assert payload["context_type"] == exchange["context_type"]
        assert payload["other_message"] == exchange["other_message"]
        assert payload["author_response"] == exchange["author_response"]


async def test_upsert_anchors_embeds_concatenated_text(store, mock_qdrant):
    """Vector should be generated from the concatenation of other_message + author_response."""
    embedded_texts: list[str] = []
    original_fn = _fixed_embedding_fn

    async def recording_fn(text: str) -> list[float]:
        embedded_texts.append(text)
        return await original_fn(text)

    s = StyleAnchorStore(qdrant_client=mock_qdrant, embedding_fn=recording_fn)
    await s.upsert_anchors(TENANT_A, PROFILE_A, _SAMPLE_EXCHANGES)

    assert len(embedded_texts) == len(_SAMPLE_EXCHANGES)
    for text, exchange in zip(embedded_texts, _SAMPLE_EXCHANGES, strict=True):
        assert exchange["other_message"] in text
        assert exchange["author_response"] in text


# ---------------------------------------------------------------------------
# search_similar — tenant + profile isolation
# ---------------------------------------------------------------------------


async def test_search_similar_filters_by_tenant(store, mock_qdrant):
    """search_similar must pass a filter that includes tenant_id."""
    mock_qdrant.query_points.return_value = MagicMock(points=[])

    await store.search_similar(TENANT_A, PROFILE_A, "¿Cuánto cuesta?", top_k=3)

    mock_qdrant.query_points.assert_called_once()
    call_kwargs = mock_qdrant.query_points.call_args
    search_filter = call_kwargs.kwargs["query_filter"]

    # Flatten all filter conditions to check tenant_id is present
    filter_str = str(search_filter)
    assert str(TENANT_A) in filter_str


async def test_search_similar_filters_by_profile(store, mock_qdrant):
    """search_similar must pass a filter that includes profile_id."""
    mock_qdrant.query_points.return_value = MagicMock(points=[])

    await store.search_similar(TENANT_A, PROFILE_A, "¿Cuánto cuesta?", top_k=3)

    call_kwargs = mock_qdrant.query_points.call_args
    search_filter = call_kwargs.kwargs["query_filter"]
    filter_str = str(search_filter)

    assert str(PROFILE_A) in filter_str


async def test_search_similar_different_profiles_isolated(store, mock_qdrant):
    """Searching for PROFILE_A should not include PROFILE_B in the filter."""
    mock_qdrant.query_points.return_value = MagicMock(points=[])

    await store.search_similar(TENANT_A, PROFILE_A, "test query", top_k=3)

    call_kwargs = mock_qdrant.query_points.call_args
    filter_str = str(call_kwargs.kwargs["query_filter"])

    assert str(PROFILE_A) in filter_str
    assert str(PROFILE_B) not in filter_str


async def test_search_similar_returns_formatted_results(store, mock_qdrant):
    """search_similar should map hit payload to expected dict keys."""
    hit = MagicMock()
    hit.payload = {
        "context_type": "objection",
        "other_message": "No tengo tiempo.",
        "author_response": "¡Entiendo!",
        "tenant_id": str(TENANT_A),
        "profile_id": str(PROFILE_A),
    }
    hit.score = 0.95
    mock_qdrant.query_points.return_value = MagicMock(points=[hit])

    results = await store.search_similar(TENANT_A, PROFILE_A, "tiempo", top_k=3)

    assert len(results) == 1
    assert results[0]["context_type"] == "objection"
    assert results[0]["other_message"] == "No tengo tiempo."
    assert results[0]["author_response"] == "¡Entiendo!"
    assert results[0]["score"] == 0.95


async def test_search_similar_uses_collection(store, mock_qdrant):
    """search_similar must query the correct collection."""
    mock_qdrant.query_points.return_value = MagicMock(points=[])

    await store.search_similar(TENANT_A, PROFILE_A, "query", top_k=5)

    call_kwargs = mock_qdrant.query_points.call_args
    assert call_kwargs.kwargs["collection_name"] == COLLECTION_NAME


# ---------------------------------------------------------------------------
# delete_by_profile
# ---------------------------------------------------------------------------


async def test_delete_by_profile_filters_tenant_and_profile(store, mock_qdrant):
    """delete_by_profile filter must include BOTH tenant_id and profile_id."""
    await store.delete_by_profile(TENANT_A, PROFILE_A)

    mock_qdrant.delete.assert_called_once()
    call_kwargs = mock_qdrant.delete.call_args
    assert call_kwargs.kwargs["collection_name"] == COLLECTION_NAME

    selector = call_kwargs.kwargs["points_selector"]
    filter_str = str(selector)
    assert str(TENANT_A) in filter_str
    assert str(PROFILE_A) in filter_str


async def test_delete_by_profile_does_not_delete_other_profiles(store, mock_qdrant):
    """Deleting PROFILE_A must not reference PROFILE_B in filter."""
    await store.delete_by_profile(TENANT_A, PROFILE_A)

    call_kwargs = mock_qdrant.delete.call_args
    filter_str = str(call_kwargs.kwargs["points_selector"])

    assert str(PROFILE_B) not in filter_str
