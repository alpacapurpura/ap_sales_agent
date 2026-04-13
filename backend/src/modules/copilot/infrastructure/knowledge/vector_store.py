"""
CopilotKnowledgeStore — Qdrant wrapper for copilot knowledge base.

Uses a SEPARATE collection (copilot_knowledge) from sales_agent.
Hybrid search: dense (OpenAI 3072d) + sparse (BM25) + FlashRank reranking.
"""

import uuid as uuid_mod

import structlog
from fastembed import SparseTextEmbedding
from flashrank import Ranker, RerankRequest
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.core.config import settings
from src.shared.infrastructure.llm.factory import LLMFactory

logger = structlog.get_logger()


class CopilotKnowledgeStore:
    """Isolated Qdrant store for copilot knowledge (DDD boundary)."""

    COLLECTION = "copilot_knowledge"

    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self.embeddings_model = LLMFactory.get_service().get_embedding_model()

        try:
            self.sparse_model = SparseTextEmbedding(
                model_name=settings.QDRANT_SPARSE_MODEL,
            )
        except Exception as e:
            logger.error("copilot_knowledge_sparse_init_error", error=str(e))
            self.sparse_model = None

        try:
            self.ranker = Ranker(
                model_name="ms-marco-MiniLM-L-12-v2",
                cache_dir="/app/model_cache",
            )
        except Exception as e:
            logger.error("copilot_knowledge_ranker_init_error", error=str(e))
            self.ranker = None

    def ensure_collection(self) -> None:
        """Create collection if it doesn't exist (dense 3072 + sparse)."""
        collections = self.client.get_collections()
        if any(c.name == self.COLLECTION for c in collections.collections):
            return

        logger.info("copilot_knowledge_creating_collection", collection=self.COLLECTION)
        self.client.create_collection(
            collection_name=self.COLLECTION,
            vectors_config={
                "dense": models.VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False),
                ),
            },
        )

    def search(
        self,
        query: str,
        tenant_id: str,
        scope: str = "all",
        limit: int = 5,
    ) -> list[dict]:
        """Hybrid search with tenant isolation and optional scope filter."""
        self.ensure_collection()

        dense_query = self.embeddings_model.embed_query(query)

        # Build filter
        filter_conditions = [
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=str(tenant_id)),
            ),
        ]
        if scope != "all":
            filter_conditions.append(
                models.FieldCondition(
                    key="scope",
                    match=models.MatchValue(value=scope),
                ),
            )

        search_filter = models.Filter(must=filter_conditions)
        search_limit = limit * 3 if self.ranker else limit

        response = self.client.query_points(
            collection_name=self.COLLECTION,
            query=dense_query,
            using="dense",
            query_filter=search_filter,
            limit=search_limit,
        )

        passages = [
            {
                "id": hit.id,
                "text": hit.payload.get("content", ""),
                "meta": hit.payload,
                "score": hit.score,
            }
            for hit in response.points
        ]

        # Rerank
        if self.ranker and passages:
            try:
                rerank_req = RerankRequest(query=query, passages=passages)
                try:
                    reranked = self.ranker.rerank(rerank_req)
                except AttributeError:
                    reranked = self.ranker.rank(rerank_req)
                passages = reranked[:limit]
            except Exception as e:
                logger.warning("copilot_knowledge_rerank_error", error=str(e))
                passages = passages[:limit]
        else:
            passages = passages[:limit]

        return passages

    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict],
        tenant_id: str,
    ) -> int:
        """Embed and upsert documents. Returns number of points indexed."""
        self.ensure_collection()

        dense_embeddings = self.embeddings_model.embed_documents(texts)

        if self.sparse_model:
            sparse_embeddings = list(self.sparse_model.embed(texts))
        else:
            sparse_embeddings = [None] * len(texts)

        points = []
        for text, meta, dense, sparse in zip(
            texts,
            metadatas,
            dense_embeddings,
            sparse_embeddings,
            strict=False,
        ):
            meta["content"] = text
            meta["tenant_id"] = str(tenant_id)
            points.append(
                models.PointStruct(
                    id=str(uuid_mod.uuid4()),
                    vector={
                        "dense": dense,
                        "sparse": sparse.as_object() if sparse else None,
                    },
                    payload=meta,
                ),
            )

        self.client.upsert(collection_name=self.COLLECTION, points=points)
        logger.info("copilot_knowledge_indexed", count=len(points))
        return len(points)

    def delete_by_document_id(self, tenant_id: str, document_id: str) -> bool:
        """Delete all points with matching document_id for a tenant."""
        try:
            self.client.delete(
                collection_name=self.COLLECTION,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="tenant_id",
                                match=models.MatchValue(value=str(tenant_id)),
                            ),
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id),
                            ),
                        ],
                    ),
                ),
            )
            return True
        except Exception as e:
            logger.error("copilot_knowledge_delete_error", error=str(e))
            return False

    def get_collection_stats(self) -> dict:
        """Get collection stats for admin dashboard."""
        try:
            self.ensure_collection()
            info = self.client.get_collection(self.COLLECTION)
            return {
                "collection": self.COLLECTION,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            logger.error("copilot_knowledge_stats_error", error=str(e))
            return {"collection": self.COLLECTION, "error": str(e)}

    def list_documents(
        self,
        tenant_id: str | None = None,
        scope: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List documents with optional tenant/scope filter (for admin)."""
        try:
            self.ensure_collection()
            filter_conditions = []
            if tenant_id:
                filter_conditions.append(
                    models.FieldCondition(
                        key="tenant_id",
                        match=models.MatchValue(value=str(tenant_id)),
                    ),
                )
            if scope:
                filter_conditions.append(
                    models.FieldCondition(
                        key="scope",
                        match=models.MatchValue(value=scope),
                    ),
                )

            scroll_filter = (
                models.Filter(must=filter_conditions) if filter_conditions else None
            )
            points, _ = self.client.scroll(
                collection_name=self.COLLECTION,
                scroll_filter=scroll_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

            return [
                {
                    "id": str(p.id),
                    "content": p.payload.get("content", "")[:200],
                    "scope": p.payload.get("scope", ""),
                    "source": p.payload.get("source", ""),
                    "tenant_id": p.payload.get("tenant_id", ""),
                    "document_id": p.payload.get("document_id", ""),
                }
                for p in points
            ]
        except Exception as e:
            logger.error("copilot_knowledge_list_error", error=str(e))
            return []
