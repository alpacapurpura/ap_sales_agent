from typing import List, Dict, Optional, Any, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.core.config import settings
from src.shared.infrastructure.llm.factory import LLMFactory
import logging
from fastembed import SparseTextEmbedding
from flashrank import Ranker, RerankRequest
import uuid

from src.modules.sales_agent.domain.memory.repository import SemanticMemoryStore

logger = logging.getLogger(__name__)

class QdrantVectorStore(SemanticMemoryStore):
    def __init__(self):
        # Initialize Qdrant Client
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
        )
        
        # Initialize Embeddings via Factory (Dense)
        self.embeddings_model = LLMFactory.get_service().get_embedding_model()
        
        # Initialize Sparse Embeddings
        try:
            self.sparse_embedding_model = SparseTextEmbedding(model_name=settings.QDRANT_SPARSE_MODEL)
            logger.info(f"Sparse embedding model loaded: {settings.QDRANT_SPARSE_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load sparse embedding model: {e}")
            self.sparse_embedding_model = None
            
        # Initialize Reranker
        try:
            self.ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/app/model_cache")
            logger.info("Reranker model loaded.")
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            self.ranker = None

    def ensure_collection_exists(self, collection_name: str = settings.QDRANT_COLLECTION_HYBRID):
        """
        Checks if collection exists, if not creates it with Hybrid config.
        """
        collections = self.client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if not exists:
            logger.info(f"Creating Hybrid collection {collection_name}...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=settings.QDRANT_VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                }
            )
            logger.info(f"Collection {collection_name} created.")
        else:
            logger.info(f"Collection {collection_name} already exists.")

    def add_texts(
        self, 
        texts: List[str], 
        metadatas: List[dict], 
        collection_name: str = settings.QDRANT_COLLECTION_HYBRID
    ) -> None:
        """
        Embeds and indexes texts into Qdrant using Hybrid (Dense + Sparse).
        """
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
        for idx, (text, meta, dense, sparse) in enumerate(zip(texts, metadatas, dense_embeddings, sparse_embeddings)):
            # Ensure metadata has content for reranking
            meta["content"] = text
            
            point = models.PointStruct(
                id=str(uuid.uuid4()), # Use UUIDs for points to avoid collision in updates
                vector={
                    "dense": dense,
                    "sparse": sparse.as_object() if sparse else None
                },
                payload=meta
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Indexed {len(texts)} documents (Hybrid).")

    def search_knowledge_base(
        self, 
        query_text: str, 
        tenant_id: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        scope_options: Optional[Dict[str, Any]] = None,
        collection_name: str = settings.QDRANT_COLLECTION_HYBRID,
        enable_rerank: bool = True,
        return_raw: bool = False
    ) -> Union[str, List[Dict]]:
        """
        Search Qdrant using Hybrid Search + Reranking + Dynamic Metadata Filtering.
        """
        try:
            self.ensure_collection_exists(collection_name)
            
            # 1. Embed Query
            dense_query = self.embeddings_model.embed_query(query_text)

            # 2. Build Filter Conditions
            filter_conditions = []
            
            # --- TENANT ISOLATION (SECURITY) ---
            filter_conditions.append(
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=str(tenant_id))
                )
            )
            
            # --- SCOPE MIXING LOGIC ---
            if scope_options:
                scope_should = [
                    models.FieldCondition(key="scope", match=models.MatchValue(value="GLOBAL"))
                ]
                
                if scope_options.get("product_id"):
                    scope_should.append(
                        models.Filter(
                            must=[
                                models.FieldCondition(key="scope", match=models.MatchValue(value="OFFER")),
                                models.FieldCondition(key="product_id", match=models.MatchValue(value=str(scope_options["product_id"])))
                            ]
                        )
                    )
                    
                if scope_options.get("marketing_asset_id"):
                     scope_should.append(
                        models.Filter(
                            must=[
                                models.FieldCondition(key="scope", match=models.MatchValue(value="ASSET")),
                                models.FieldCondition(key="marketing_asset_id", match=models.MatchValue(value=str(scope_options["marketing_asset_id"])))
                            ]
                        )
                    )
                
                filter_conditions.append(models.Filter(should=scope_should))

            # --- STANDARD FILTERS ---
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value)
                            )
                        )
                    else:
                        filter_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )
            
            search_filter = models.Filter(must=filter_conditions) if filter_conditions else None
            
            logger.info(f"🔍 Qdrant Query: '{query_text}'")
            
            # 3. Perform Search (Dense)
            search_limit = limit * 3 if enable_rerank else limit
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=models.NamedVector(
                    name="dense",
                    vector=dense_query
                ),
                query_filter=search_filter,
                limit=search_limit
            )
            
            logger.info(f"Dense search found {len(results)} raw candidates")

            # Map results for Reranker
            passages = []
            for hit in results:
                passages.append({
                    "id": hit.id,
                    "text": hit.payload.get("content", ""),
                    "meta": hit.payload,
                    "score": hit.score
                })
                
            # 4. Reranking (FlashRank)
            if enable_rerank and self.ranker and passages:
                logger.info("Starting reranking...")
                rerank_request = RerankRequest(query=query_text, passages=passages)
                try:
                    reranked_results = self.ranker.rerank(rerank_request)
                except AttributeError:
                    reranked_results = self.ranker.rank(rerank_request)
                
                final_results = reranked_results[:limit]
            else:
                final_results = passages[:limit]

            if not final_results:
                return [] if return_raw else ""
                
            if return_raw:
                return final_results
                
            # Format context
            context_parts = []
            seen_parents = set()
            
            for item in final_results:
                meta = item.get("meta", {})
                source = meta.get("source", "unknown")
                category = meta.get("doc_category", "general")
                
                if isinstance(category, list):
                    category = ",".join(category)
                
                parent_id = meta.get("parent_id")
                parent_content = meta.get("parent_content")
                strategy = meta.get("strategy")
                
                if strategy == "small_to_big_contextual" and parent_content:
                    if parent_id in seen_parents:
                        continue 
                    
                    content = parent_content
                    seen_parents.add(parent_id)
                    source_prefix = f"[PARENT-CTX] (Source: {source})"
                else:
                    content = item.get("text", "")
                    source_prefix = f"(Source: {source})"

                content = content.strip()
                context_parts.append(f"- [{category.upper()}] {content} {source_prefix}")
                
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return ""

    # Additional methods not in interface but useful
    def delete_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
            
    def delete_vectors_by_source(self, collection_name: str, source_filename: str) -> bool:
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="source",
                                match=models.MatchValue(value=source_filename)
                            )
                        ]
                    )
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False
