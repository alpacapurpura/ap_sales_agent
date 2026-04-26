"""MarketingKbStore — Qdrant wrapper for tenant-agnostic curated marketing KB.

Collection ``nicolify_marketing_kb`` is GLOBAL (no ``tenant_id`` field, no
``tenant_id`` filter). Curated by Nicolify staff; tenants cannot ingest.

Schema metadata
---------------
``category``: framework | playbook | script | checklist | case_study
``methodology``: nicolify_owned | storybrand | hormozi | cialdini | aida | pas
                 | jtbd | fab | 4u
``domain``: brand | offer | copy | objections | pricing | funnel | audience
``tags``: list[str]
``source_doc``: filename of source markdown
``chunk_index``: int
``language``: "es"
``version``: int
``breadcrumb``: list[str]  ← heading hierarchy (contextual retrieval)
``content``: chunk text (with breadcrumb prepended at embed time)

[COPILOT-MARKETING-KB-F10]

Provider scan import side-effects (gotcha F4): the Qdrant client is created
lazily inside ``_client()`` — never at module-import time — so unit tests that
just import this module do not open network connections.
"""

from __future__ import annotations

import hashlib
import uuid as uuid_mod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.core.config import settings

if TYPE_CHECKING:
    from collections.abc import Iterable

    from langchain_core.embeddings import Embeddings

logger = structlog.get_logger()

MARKETING_KB_COLLECTION = "nicolify_marketing_kb"
MARKETING_KB_VECTOR_SIZE = 3072  # text-embedding-3-large default

ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"framework", "playbook", "script", "checklist", "case_study"},
)
ALLOWED_METHODOLOGIES: frozenset[str] = frozenset(
    {
        "nicolify_owned",
        "storybrand",
        "hormozi",
        "cialdini",
        "aida",
        "pas",
        "jtbd",
        "fab",
        "4u",
    },
)
ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {"brand", "offer", "copy", "objections", "pricing", "funnel", "audience"},
)


@dataclass(frozen=True, slots=True)
class KbChunk:
    """Curated marketing KB chunk ready for upsert."""

    content: str
    category: str
    methodology: str
    domain: str
    source_doc: str
    chunk_index: int
    breadcrumb: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    language: str = "es"
    version: int = 1

    def __post_init__(self) -> None:
        """Validate enum fields at construction time."""
        if self.category not in ALLOWED_CATEGORIES:
            msg = f"Unknown category: {self.category!r}"
            raise ValueError(msg)
        if self.methodology not in ALLOWED_METHODOLOGIES:
            msg = f"Unknown methodology: {self.methodology!r}"
            raise ValueError(msg)
        if self.domain not in ALLOWED_DOMAINS:
            msg = f"Unknown domain: {self.domain!r}"
            raise ValueError(msg)

    def stable_id(self) -> str:
        """Deterministic UUIDv5 derived from source_doc + chunk_index + version.

        Idempotent reseed: re-running the seeder produces the same id, so
        upsert overwrites in place instead of creating duplicates.
        """
        seed = f"{self.source_doc}::{self.chunk_index}::{self.version}"
        digest = hashlib.sha1(seed.encode("utf-8"), usedforsecurity=False).hexdigest()
        return str(uuid_mod.UUID(digest[:32]))

    def embed_text(self) -> str:
        """Text fed to the embedder: breadcrumb prefix + content.

        Contextual retrieval (April 2026 best practice): prepending the
        heading path makes the chunk self-contained for embedding similarity,
        without changing the user-facing content stored in payload.
        """
        if not self.breadcrumb:
            return self.content
        prefix = " > ".join(self.breadcrumb)
        return f"# {prefix}\n\n{self.content}"

    def payload(self) -> dict[str, Any]:
        """JSON payload stored in Qdrant. Excludes ``tenant_id`` by design."""
        return {
            "content": self.content,
            "category": self.category,
            "methodology": self.methodology,
            "domain": self.domain,
            "source_doc": self.source_doc,
            "chunk_index": self.chunk_index,
            "breadcrumb": list(self.breadcrumb),
            "tags": list(self.tags),
            "language": self.language,
            "version": self.version,
        }


def _hit_to_dict(hit: object) -> dict[str, Any]:
    """Normalise a qdrant-client ``ScoredPoint`` into the public search dict."""
    payload = hit.payload or {}
    return {
        "id": str(hit.id),
        "score": float(hit.score),
        "content": payload.get("content", ""),
        "category": payload.get("category"),
        "methodology": payload.get("methodology"),
        "domain": payload.get("domain"),
        "breadcrumb": payload.get("breadcrumb") or [],
        "source_doc": payload.get("source_doc"),
        "chunk_index": payload.get("chunk_index"),
        "tags": payload.get("tags") or [],
    }


def _rest_point_to_dict(point: dict[str, Any]) -> dict[str, Any]:
    """Normalise a raw REST ``/points/search`` hit into the public search dict."""
    payload = point.get("payload") or {}
    return {
        "id": str(point["id"]),
        "score": float(point["score"]),
        "content": payload.get("content", ""),
        "category": payload.get("category"),
        "methodology": payload.get("methodology"),
        "domain": payload.get("domain"),
        "breadcrumb": payload.get("breadcrumb") or [],
        "source_doc": payload.get("source_doc"),
        "chunk_index": payload.get("chunk_index"),
        "tags": payload.get("tags") or [],
    }


class MarketingKbStore:
    """Tenant-agnostic Qdrant wrapper for the curated marketing KB.

    Heavy resources (Qdrant client, embedding model) are created lazily so
    that ``import`` time stays cheap and unit tests can stub them out via
    constructor injection (``client=``, ``embedder=``).
    """

    COLLECTION = MARKETING_KB_COLLECTION
    VECTOR_SIZE = MARKETING_KB_VECTOR_SIZE

    def __init__(
        self,
        *,
        client: QdrantClient | None = None,
        embedder: Embeddings | None = None,
    ) -> None:
        """Wire optional client + embedder; otherwise build lazily on first use."""
        self._client = client
        self._embedder = embedder

    def _get_client(self) -> QdrantClient:
        """Open a Qdrant connection on demand.

        Diferred to ``__call__`` time per F4 gotcha — avoids opening a
        connection at module-import time which would break unit tests.
        """
        if self._client is None:
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
            )
        return self._client

    def _get_embedder(self) -> Embeddings:
        """Resolve the embedding model on demand."""
        if self._embedder is None:
            from src.shared.infrastructure.llm.factory import LLMFactory

            self._embedder = LLMFactory.get_service().get_embedding_model()
        return self._embedder

    def ensure_collection(self) -> None:
        """Create the marketing kb collection if missing.

        Hardcodes the dim invariant: any future embedding model with a
        different dimension forces a deliberate breaking change here +
        in the arch test ``test_marketing_kb_vector_size_invariant``.
        """
        client = self._get_client()
        collections = client.get_collections()
        if any(c.name == self.COLLECTION for c in collections.collections):
            return

        logger.info("marketing_kb_creating_collection", collection=self.COLLECTION)
        client.create_collection(
            collection_name=self.COLLECTION,
            vectors_config=models.VectorParams(
                size=self.VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

    def search(
        self,
        query: str,
        *,
        domain: str | None = None,
        methodology: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Dense cosine search over curated chunks.

        No ``tenant_id`` filter — corpus is global. Optional filters on
        ``domain`` / ``methodology`` enable focused queries (e.g. "search
        only Hormozi material" via ``methodology='hormozi'``).
        """
        if not query.strip():
            return []

        self.ensure_collection()
        client = self._get_client()
        embedder = self._get_embedder()

        dense_query = embedder.embed_query(query)

        filter_conditions: list[models.FieldCondition] = []
        if domain is not None:
            if domain not in ALLOWED_DOMAINS:
                msg = f"Unknown domain filter: {domain!r}"
                raise ValueError(msg)
            filter_conditions.append(
                models.FieldCondition(
                    key="domain",
                    match=models.MatchValue(value=domain),
                ),
            )
        if methodology is not None:
            if methodology not in ALLOWED_METHODOLOGIES:
                msg = f"Unknown methodology filter: {methodology!r}"
                raise ValueError(msg)
            filter_conditions.append(
                models.FieldCondition(
                    key="methodology",
                    match=models.MatchValue(value=methodology),
                ),
            )

        search_filter = models.Filter(must=filter_conditions) if filter_conditions else None

        try:
            response = client.query_points(
                collection_name=self.COLLECTION,
                query=dense_query,
                query_filter=search_filter,
                limit=limit,
            )
            points = response.points
        except UnexpectedResponse as exc:
            # B12-TP7: dev Qdrant server pinned to v1.7.3 (docker-compose.yml)
            # while qdrant-client>=1.13.3 emits the v1.10+ ``query_points``
            # endpoint → 404. Fall back to the deprecated-but-stable REST
            # ``/points/search`` endpoint that exists since Qdrant 1.0.
            # F-pos: drop this branch when docker-compose bumps Qdrant to a
            # server compatible with qdrant-client major (≥1.16).
            if "404" not in str(exc):
                raise
            return self._search_via_rest(dense_query, filter_conditions, limit)

        return [_hit_to_dict(hit) for hit in points]

    def _search_via_rest(
        self,
        dense_query: list[float],
        filter_conditions: list[models.FieldCondition],
        limit: int,
    ) -> list[dict[str, Any]]:
        """REST ``/points/search`` fallback for legacy Qdrant servers (<1.10).

        Uses raw httpx so we do not depend on the qdrant-client API surface
        which changed between 1.7 and 1.17. Same payload shape as the
        ``query_points`` path so callers see identical dicts.
        """
        body: dict[str, Any] = {
            "vector": dense_query,
            "limit": limit,
            "with_payload": True,
        }
        if filter_conditions:
            body["filter"] = {
                "must": [
                    {
                        "key": cond.key,
                        "match": {"value": cond.match.value},
                    }
                    for cond in filter_conditions
                ],
            }
        headers = {"api-key": settings.QDRANT_API_KEY} if settings.QDRANT_API_KEY else {}
        url = f"{settings.QDRANT_URL.rstrip('/')}/collections/{self.COLLECTION}/points/search"
        resp = httpx.post(url, json=body, headers=headers, timeout=30.0)
        resp.raise_for_status()
        return [_rest_point_to_dict(point) for point in resp.json().get("result", [])]

    def upsert_chunks(self, chunks: Iterable[KbChunk]) -> int:
        """Embed and upsert curated chunks. Returns number indexed.

        Idempotent: chunks reuse ``stable_id()`` derived from
        ``source_doc + chunk_index + version`` so re-running the seeder
        overwrites in place.
        """
        chunks_list = list(chunks)
        if not chunks_list:
            return 0

        self.ensure_collection()
        client = self._get_client()
        embedder = self._get_embedder()

        texts = [c.embed_text() for c in chunks_list]
        vectors = embedder.embed_documents(texts)

        points = [
            models.PointStruct(
                id=chunk.stable_id(),
                vector=vector,
                payload=chunk.payload(),
            )
            for chunk, vector in zip(chunks_list, vectors, strict=True)
        ]

        client.upsert(collection_name=self.COLLECTION, points=points)
        logger.info(
            "marketing_kb_upserted",
            count=len(points),
            sources=sorted({c.source_doc for c in chunks_list}),
        )
        return len(points)

    def delete_by_source_doc(self, source_doc: str) -> bool:
        """Remove all chunks for a given ``source_doc`` (admin re-index flow)."""
        try:
            client = self._get_client()
            client.delete(
                collection_name=self.COLLECTION,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="source_doc",
                                match=models.MatchValue(value=source_doc),
                            ),
                        ],
                    ),
                ),
            )
        except Exception as exc:
            logger.exception("marketing_kb_delete_error", error=str(exc))
            return False
        else:
            return True

    def stats(self) -> dict[str, Any]:
        """Lightweight collection stats for the admin dashboard."""
        try:
            self.ensure_collection()
            client = self._get_client()
            info = client.get_collection(self.COLLECTION)
        except Exception as exc:
            logger.exception("marketing_kb_stats_error", error=str(exc))
            return {"collection": self.COLLECTION, "error": str(exc)}
        else:
            # B14-TP8 — qdrant-client 1.17 dropped ``CollectionInfo.vectors_count``.
            # ``points_count`` is the canonical row count for dense single-vector
            # points (our payload). Admin renders it as "Vectores" semantically.
            return {
                "collection": self.COLLECTION,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown",
            }

    def list_sources(self, limit: int = 200) -> list[dict[str, Any]]:
        """List distinct ``source_doc`` values with chunk counts (admin view)."""
        try:
            self.ensure_collection()
            client = self._get_client()
            points, _ = client.scroll(
                collection_name=self.COLLECTION,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:
            logger.exception("marketing_kb_list_error", error=str(exc))
            return []

        grouped: dict[str, dict[str, Any]] = {}
        for point in points:
            payload = point.payload or {}
            source = payload.get("source_doc") or "unknown"
            entry = grouped.setdefault(
                source,
                {
                    "source_doc": source,
                    "chunks": 0,
                    "category": payload.get("category"),
                    "methodology": payload.get("methodology"),
                    "domain": payload.get("domain"),
                },
            )
            entry["chunks"] += 1
        return sorted(grouped.values(), key=lambda r: r["source_doc"])
