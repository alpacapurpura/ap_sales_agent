"""Qdrant client for personality style anchors.

Collection: personality_style_anchors
Each point = one conversation exchange (prospect message + user response).
Used for per-turn RAG injection to prevent personality drift in long conversations.

Design constraints:
- ALL queries filter by tenant_id (tenant isolation, non-negotiable).
- ALL queries also filter by profile_id (each profile is an isolated anchor set).
- The embedding_fn is injected so callers can swap models without changing this class.
- Qdrant client is injected to allow unit testing with mocks.
- Sync Qdrant calls are wrapped in asyncio.to_thread() to avoid blocking FastAPI event loop.
"""

from __future__ import annotations

import asyncio
import uuid as uuid_mod
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from qdrant_client.http import models

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from qdrant_client import QdrantClient

logger = structlog.get_logger()

COLLECTION_NAME = "personality_style_anchors"
VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small


class StyleAnchorStore:
    """Qdrant-backed store for per-profile personality style anchors.

    Parameters
    ----------
    qdrant_client:
        Pre-configured QdrantClient instance (sync).
    embedding_fn:
        Async callable that receives a text string and returns a list of floats
        (the embedding vector). Defaults to None — caller must inject one.
    vector_size:
        Dimensionality of the embedding vectors. Defaults to VECTOR_SIZE (1536).
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_fn: Callable[[str], Coroutine[Any, Any, list[float]]] | None = None,
        vector_size: int = VECTOR_SIZE,
    ) -> None:
        """Initialize the store with a Qdrant client and optional embedding function."""
        self._client = qdrant_client
        self._embedding_fn = embedding_fn
        self._vector_size = vector_size

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        collections = await asyncio.to_thread(self._client.get_collections)
        exists = any(c.name == COLLECTION_NAME for c in collections.collections)
        if exists:
            return

        logger.info("style_anchor_store.creating_collection", collection=COLLECTION_NAME)
        await asyncio.to_thread(
            self._client.create_collection,
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=self._vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def upsert_anchors(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        exchanges: list[dict],
    ) -> int:
        """Embed and upsert conversation exchanges as style anchor points.

        Parameters
        ----------
        tenant_id:
            Owning tenant — stored in payload and used for isolation.
        profile_id:
            The personality profile these anchors belong to.
        exchanges:
            List of dicts with keys: context_type, other_message, author_response.

        Returns:
        -------
        int
            Number of points upserted.
        """
        await self.ensure_collection()

        if self._embedding_fn is None:
            msg = "embedding_fn must be provided to upsert anchors"
            raise ValueError(msg)

        points: list[models.PointStruct] = []
        for exchange in exchanges:
            combined_text = f"{exchange['other_message']} {exchange['author_response']}"
            vector = await self._embedding_fn(combined_text)

            point = models.PointStruct(
                id=str(uuid_mod.uuid4()),
                vector=vector,
                payload={
                    "tenant_id": str(tenant_id),
                    "profile_id": str(profile_id),
                    "context_type": exchange.get("context_type", ""),
                    "other_message": exchange.get("other_message", ""),
                    "author_response": exchange.get("author_response", ""),
                },
            )
            points.append(point)

        await asyncio.to_thread(
            self._client.upsert,
            collection_name=COLLECTION_NAME,
            points=points,
        )
        logger.info(
            "style_anchor_store.upserted",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
            count=len(points),
        )
        return len(points)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def search_similar(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        query_text: str,
        top_k: int = 3,
    ) -> list[dict]:
        """Find the most similar style anchors for the given conversation context.

        CRITICAL: filters by BOTH tenant_id and profile_id for strict isolation.

        Parameters
        ----------
        tenant_id:
            Owning tenant — mandatory isolation filter.
        profile_id:
            The personality profile to restrict the search to.
        query_text:
            The incoming prospect message (or conversation context) to match against.
        top_k:
            Maximum number of anchors to return.

        Returns:
        -------
        list[dict]
            Each item contains: context_type, other_message, author_response, score.
        """
        await self.ensure_collection()

        if self._embedding_fn is None:
            msg = "embedding_fn must be provided to search anchors"
            raise ValueError(msg)
        query_vector = await self._embedding_fn(query_text)

        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=str(tenant_id)),
                ),
                models.FieldCondition(
                    key="profile_id",
                    match=models.MatchValue(value=str(profile_id)),
                ),
            ],
        )

        response = await asyncio.to_thread(
            self._client.query_points,
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=search_filter,
            limit=top_k,
        )

        results = [
            {
                "context_type": hit.payload.get("context_type", ""),
                "other_message": hit.payload.get("other_message", ""),
                "author_response": hit.payload.get("author_response", ""),
                "score": hit.score,
            }
            for hit in response.points
        ]

        logger.info(
            "style_anchor_store.search_similar",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
            query_length=len(query_text),
            results_count=len(results),
        )
        return results

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_by_profile(
        self,
        tenant_id: UUID,
        profile_id: UUID,
    ) -> None:
        """Delete all style anchors belonging to a specific profile.

        Filters by BOTH tenant_id and profile_id to prevent cross-tenant deletion.

        Parameters
        ----------
        tenant_id:
            Owning tenant — mandatory isolation filter.
        profile_id:
            The personality profile whose anchors should be removed.
        """
        await asyncio.to_thread(
            self._client.delete,
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="tenant_id",
                            match=models.MatchValue(value=str(tenant_id)),
                        ),
                        models.FieldCondition(
                            key="profile_id",
                            match=models.MatchValue(value=str(profile_id)),
                        ),
                    ],
                ),
            ),
        )
        logger.info(
            "style_anchor_store.deleted_by_profile",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )
