"""Vector Store infrastructure module."""

import logging
import uuid
from typing import Any

from fastembed import SparseTextEmbedding
from flashrank import Ranker, RerankRequest
from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.core.config import settings
from src.modules.sales_agent.domain.memory.repository import SemanticMemoryStore
from src.shared.infrastructure.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class QdrantVectorStore(SemanticMemoryStore):
    """Qdrant Vector Store."""

    def __init__(self) -> None:
        """Initialize instance."""
        # Initialize Qdrant Client
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )

        # Initialize Embeddings via Factory (Dense)
        self.embeddings_model = LLMFactory.get_service().get_embedding_model()

        # Initialize Sparse Embeddings
        try:
            self.sparse_embedding_model = SparseTextEmbedding(
                model_name=settings.QDRANT_SPARSE_MODEL,
            )
            logger.info(
                "Sparse embedding model loaded: %s",
                settings.QDRANT_SPARSE_MODEL,
            )
        except Exception:
            logger.exception("Failed to load sparse embedding model")
            self.sparse_embedding_model = None

        # Initialize Reranker
        try:
            self.ranker = Ranker(
                model_name="ms-marco-MiniLM-L-12-v2",
                cache_dir="/app/model_cache",
            )
            logger.info("Reranker model loaded.")
        except Exception:
            logger.exception("Failed to load reranker")
            self.ranker = None

    def ensure_collection_exists(
        self,
        collection_name: str = settings.QDRANT_COLLECTION_HYBRID,
    ) -> None:
        """Check if collection exists, if not creates it with Hybrid config."""
        collections = self.client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if not exists:
            logger.info("Creating Hybrid collection %s...", collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=models.Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        ),
                    ),
                },
            )
            logger.info("Collection %s created.", collection_name)
        else:
            logger.info("Collection %s already exists.", collection_name)

    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict],
        collection_name: str = settings.QDRANT_COLLECTION_HYBRID,
    ) -> None:
        """Embeds and indexes texts into Qdrant using Hybrid (Dense + Sparse)."""
        self.ensure_collection_exists(collection_name)

        # 1. Generate Dense Embeddings (OpenAI/Gemini)
        dense_embeddings = self.embeddings_model.embed_documents(texts)

        # 2. Generate Sparse Embeddings (BM25/SPLADE)
        if self.sparse_embedding_model:
            sparse_embeddings = list(self.sparse_embedding_model.embed(texts))
        else:
            sparse_embeddings = [None] * len(texts)
            logger.warning("Sparse model not active, skipping sparse vectors.")

        points = []
        for _idx, (text, meta, dense, sparse) in enumerate(
            zip(texts, metadatas, dense_embeddings, sparse_embeddings, strict=False),
        ):
            # Ensure metadata has content for reranking
            meta["content"] = text

            point = models.PointStruct(
                id=str(
                    uuid.uuid4(),
                ),  # Use UUIDs for points to avoid collision in updates
                vector={
                    "dense": dense,
                    "sparse": sparse.as_object() if sparse else None,
                },
                payload=meta,
            )
            points.append(point)

        self.client.upsert(collection_name=collection_name, points=points)
        logger.info("Indexed %d documents (Hybrid).", len(texts))

    def _build_filter_conditions(
        self,
        tenant_id: str,
        scope_options: dict[str, Any] | None,
        filters: dict[str, Any] | None,
    ) -> list:
        """Build Qdrant filter conditions for tenant isolation, scope, and standard filters."""
        conditions = [
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=str(tenant_id)),
            ),
        ]

        if scope_options:
            conditions.append(self._build_scope_filter(scope_options))

        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value),
                        ),
                    )
                else:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        ),
                    )

        return conditions

    @staticmethod
    def _build_scope_filter(scope_options: dict[str, Any]) -> models.Filter:
        """Build scope mixing filter (GLOBAL + optional OFFER/ASSET)."""
        scope_should = [
            models.FieldCondition(key="scope", match=models.MatchValue(value="GLOBAL")),
        ]

        scope_fields = {
            "product_id": ("OFFER", "product_id"),
            "marketing_asset_id": ("ASSET", "marketing_asset_id"),
        }
        for option_key, (scope_val, field_key) in scope_fields.items():
            if scope_options.get(option_key):
                scope_should.append(
                    models.Filter(
                        must=[
                            models.FieldCondition(
                                key="scope",
                                match=models.MatchValue(value=scope_val),
                            ),
                            models.FieldCondition(
                                key=field_key,
                                match=models.MatchValue(
                                    value=str(scope_options[option_key]),
                                ),
                            ),
                        ],
                    ),
                )

        return models.Filter(should=scope_should)

    def _rerank_results(
        self,
        query_text: str,
        passages: list[dict],
        limit: int,
        enable_rerank: bool,
    ) -> list[dict]:
        """Apply reranking if enabled, otherwise return top passages by score."""
        if enable_rerank and self.ranker and passages:
            logger.info("Starting reranking...")
            rerank_request = RerankRequest(query=query_text, passages=passages)
            try:
                reranked_results = self.ranker.rerank(rerank_request)
            except AttributeError:
                reranked_results = self.ranker.rank(rerank_request)
            return reranked_results[:limit]
        return passages[:limit]

    @staticmethod
    def _format_context(results: list[dict]) -> str:
        """Format search results into a context string for the LLM."""
        context_parts = []
        seen_parents: set = set()

        for item in results:
            meta = item.get("meta", {})
            source = meta.get("source", "unknown")
            category = meta.get("doc_category", "general")
            if isinstance(category, list):
                category = ",".join(category)

            parent_id = meta.get("parent_id")
            parent_content = meta.get("parent_content")

            if meta.get("strategy") == "small_to_big_contextual" and parent_content:
                if parent_id in seen_parents:
                    continue
                content = parent_content
                seen_parents.add(parent_id)
                source_prefix = f"[PARENT-CTX] (Source: {source})"
            else:
                content = item.get("text", "")
                source_prefix = f"(Source: {source})"

            context_parts.append(
                f"- [{category.upper()}] {content.strip()} {source_prefix}",
            )

        return "\n".join(context_parts)

    def search_knowledge_base(
        self,
        query_text: str,
        tenant_id: str,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
        scope_options: dict[str, Any] | None = None,
        collection_name: str = settings.QDRANT_COLLECTION_HYBRID,
        enable_rerank: bool = True,
        return_raw: bool = False,
    ) -> str | list[dict]:
        """Search Qdrant using Hybrid Search + Reranking + Dynamic Metadata Filtering."""
        try:
            self.ensure_collection_exists(collection_name)

            dense_query = self.embeddings_model.embed_query(query_text)
            filter_conditions = self._build_filter_conditions(
                tenant_id,
                scope_options,
                filters,
            )
            search_filter = models.Filter(must=filter_conditions) if filter_conditions else None

            logger.info("Qdrant Query: '%s'", query_text)

            search_limit = limit * 3 if enable_rerank else limit
            response = self.client.query_points(
                collection_name=collection_name,
                query=dense_query,
                using="dense",
                query_filter=search_filter,
                limit=search_limit,
            )

            logger.info("Dense search found %d raw candidates", len(response.points))

            passages = [
                {
                    "id": hit.id,
                    "text": hit.payload.get("content", ""),
                    "meta": hit.payload,
                    "score": hit.score,
                }
                for hit in response.points
            ]

            final_results = self._rerank_results(
                query_text,
                passages,
                limit,
                enable_rerank,
            )

            if not final_results:
                return [] if return_raw else ""
            if return_raw:
                return final_results

            return self._format_context(final_results)

        except Exception:
            logger.exception("Error searching Qdrant")
            return ""

    # Additional methods not in interface but useful
    def delete_collection(self, collection_name: str) -> bool:
        """Delete collection."""
        try:
            self.client.delete_collection(collection_name=collection_name)
        except Exception:
            logger.exception("Error deleting collection")
            return False

        else:
            return True

    def delete_vectors_by_source(
        self,
        collection_name: str,
        source_filename: str,
    ) -> bool:
        """Delete vectors by source."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="source",
                                match=models.MatchValue(value=source_filename),
                            ),
                        ],
                    ),
                ),
            )
        except Exception:
            logger.exception("Error deleting vectors")
            return False
        else:
            return True
