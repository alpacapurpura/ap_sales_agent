from typing import List, Dict, Optional, Any, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import settings
from src.core.llm.factory import LLMFactory
import logging
from fastembed import SparseTextEmbedding
from flashrank import Ranker, RerankRequest
import uuid

logger = logging.getLogger(__name__)

# Initialize Qdrant Client
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
)

# Initialize Embeddings via Factory (Dense)
embeddings_model = LLMFactory.get_service().get_embedding_model()

# Initialize Sparse Embeddings (Lazy loading recommended, but here global for simplicity)
try:
    sparse_embedding_model = SparseTextEmbedding(model_name=settings.QDRANT_SPARSE_MODEL)
    logger.info(f"Sparse embedding model loaded: {settings.QDRANT_SPARSE_MODEL}")
except Exception as e:
    logger.error(f"Failed to load sparse embedding model: {e}")
    sparse_embedding_model = None

# Initialize Reranker
try:
    # Small, fast model for reranking
    ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/app/model_cache")
    logger.info("Reranker model loaded.")
except Exception as e:
    logger.error(f"Failed to load reranker: {e}")
    ranker = None

def update_vectors_category(collection_name: str, source_filename: str, new_categories: List[str]) -> bool:
    """
    Updates the 'doc_category' field in the payload of all vectors matching the source filename.
    """
    try:
        # qdrant_client.set_payload updates specific keys, leaving others intact
        qdrant_client.set_payload(
            collection_name=collection_name,
            payload={
                "doc_category": new_categories
            },
            points=models.FilterSelector(
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
        logger.info(f"Updated category for {source_filename} to {new_categories}")
        return True
    except Exception as e:
        logger.error(f"Error updating vector categories: {e}")
        return False

def fetch_vectors_by_source(collection_name: str, source_filename: str, limit: int = 1000) -> List[Dict]:
    """
    Retrieves vectors (payloads) associated with a specific source file.
    Returns a list of dicts with 'id', 'content', and 'metadata'.
    """
    try:
        ensure_collection_exists(collection_name)
        
        # Scroll logic to get points
        points, _ = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source",
                        match=models.MatchValue(value=source_filename)
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for p in points:
            results.append({
                "id": p.id,
                "content": p.payload.get("content", ""),
                "metadata": p.payload
            })
            
        logger.info(f"Fetched {len(results)} chunks for {source_filename}")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching vectors for {source_filename}: {e}")
        return []

def delete_collection(collection_name: str) -> bool:
    """
    Deletes an entire collection. Use with caution.
    """
    try:
        qdrant_client.delete_collection(collection_name=collection_name)
        logger.info(f"Collection {collection_name} deleted.")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {e}")
        return False

def delete_vectors_by_source(collection_name: str, source_filename: str) -> bool:
    """
    Deletes all vectors in a collection that match metadata.source == source_filename.
    """
    try:
        qdrant_client.delete(
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
        logger.info(f"Deleted vectors for source: {source_filename} in {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting vectors by source: {e}")
        return False

def ensure_collection_exists(collection_name: str = settings.QDRANT_COLLECTION_HYBRID):
    """
    Checks if collection exists, if not creates it with Hybrid config.
    """
    collections = qdrant_client.get_collections()
    exists = any(c.name == collection_name for c in collections.collections)
    
    if not exists:
        logger.info(f"Creating Hybrid collection {collection_name}...")
        qdrant_client.create_collection(
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
        # We could check config here, but skipping for speed
        logger.info(f"Collection {collection_name} already exists.")

def add_texts(texts: List[str], metadatas: List[dict], collection_name: str = settings.QDRANT_COLLECTION_HYBRID):
    """
    Embeds and indexes texts into Qdrant using Hybrid (Dense + Sparse).
    """
    ensure_collection_exists(collection_name)
    
    # 1. Generate Dense Embeddings (OpenAI/Gemini)
    dense_embeddings = embeddings_model.embed_documents(texts)
    
    # 2. Generate Sparse Embeddings (BM25/SPLADE)
    if sparse_embedding_model:
        sparse_embeddings = list(sparse_embedding_model.embed(texts))
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
    
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    logger.info(f"Indexed {len(texts)} documents (Hybrid).")

def search_knowledge_base(
    query_text: str, 
    limit: int = 5, # Fetch more for reranking (Recal@K)
    client_id: str = "visionarias",
    collection_name: str = settings.QDRANT_COLLECTION_HYBRID,
    filters: Optional[Dict[str, Any]] = None,
    enable_rerank: bool = True,
    return_raw: bool = False
) -> Union[str, List[Dict]]:
    """
    Search Qdrant using Hybrid Search + Reranking + Dynamic Metadata Filtering.
    
    Args:
        filters: Dictionary of metadata filters. Example:
                 {"doc_category": "financial_legal"} or {"doc_category": ["financial_legal", "sales_persuasion"]}
        return_raw: If True, returns List[Dict] with full metadata and scores instead of formatted string.
    """
    try:
        ensure_collection_exists(collection_name)
        
        # 1. Embed Query
        dense_query = embeddings_model.embed_query(query_text)
        sparse_query = None
        if sparse_embedding_model:
            sparse_query = list(sparse_embedding_model.query_embed(query_text))[0]
            # sparse_query is intentionally unused; sparse search disabled for now

        # 2. Build Filter Conditions
        # Note: We temporarily disable strict client_id filtering to allow finding legacy documents
        # that were indexed without this field.
        filter_conditions = []
        
        # if client_id:
        #     filter_conditions.append(
        #         models.FieldCondition(
        #             key="client_id",
        #             match=models.MatchValue(value=client_id)
        #         )
        #     )
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    # OR condition for list of values
                    # Check if doc_category in Qdrant is stored as a list or string
                    # If it's stored as a list, MatchAny works.
                    # If it's stored as a string, we might need multiple MatchValues in a Should clause.
                    
                    # Assuming doc_category is stored as a list in Qdrant payload
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        )
                    )
                else:
                    # Exact match for single value
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
        
        search_filter = models.Filter(must=filter_conditions)
        
        # --- DEBUG LOGGING ---
        logger.info(f"🔍 Qdrant Query: '{query_text}'")
        logger.info(f"🔍 Filter: {search_filter}")
        # ---------------------
        
        # 3. Perform Search (Dense)
        # Using Dense Search as primary candidate generator
        # If reranking is enabled, we fetch more candidates (3x limit) to allow reranker to reorder
        search_limit = limit * 3 if enable_rerank else limit
        
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=models.NamedVector(
                name="dense",
                vector=dense_query
            ),
            query_filter=search_filter,
            limit=search_limit
        )
        
        logger.info(f"Dense search found {len(results)} raw candidates (limit={search_limit})")

        
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
        if enable_rerank and ranker and passages:
            logger.info("Starting reranking...")
            rerank_request = RerankRequest(query=query_text, passages=passages)
            try:
                # Try new API first (v0.2.0+)
                reranked_results = ranker.rerank(rerank_request)
            except AttributeError:
                # Fallback to old API
                reranked_results = ranker.rank(rerank_request)
            
            logger.info(f"Reranking complete. Candidates: {len(reranked_results)}")
            # Take top 'limit' after reranking
            final_results = reranked_results[:limit]
        else:
            logger.info("Reranking skipped or not needed.")
            final_results = passages[:limit]

        if not final_results:
            logger.warning("No results found after search/rerank.")
            return [] if return_raw else ""
            
        if return_raw:
            return final_results
            
        # Format context
        context_parts = []
        seen_parents = set()
        
        for item in final_results:
            # item is dict from FlashRank or manual
            meta = item.get("meta", {})
            source = meta.get("source", "unknown")
            category = meta.get("doc_category", "general")
            
            # Handle list category
            if isinstance(category, list):
                category = ",".join(category)
            
            # --- Small-to-Big Retrieval Logic ---
            # If we have parent_content, use it! But deduplicate.
            parent_id = meta.get("parent_id")
            parent_content = meta.get("parent_content")
            strategy = meta.get("strategy")
            
            if strategy == "small_to_big_contextual" and parent_content:
                if parent_id in seen_parents:
                    continue # Skip duplicate parent
                
                content = parent_content
                seen_parents.add(parent_id)
                source_prefix = f"[PARENT-CTX] (Source: {source})"
            else:
                # Fallback to standard content (Child)
                content = item.get("text", "")
                source_prefix = f"(Source: {source})"

            # Clean up content a bit if needed
            content = content.strip()
            
            context_parts.append(f"- [{category.upper()}] {content} {source_prefix}")
            
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error searching Qdrant: {e}")
        return ""
