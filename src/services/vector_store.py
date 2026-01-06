from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import settings
from src.core.llm.factory import LLMFactory
import logging

logger = logging.getLogger(__name__)

# Initialize Qdrant Client
# Assuming Qdrant is running in the 'web_gateway' network or accessible via URL
# If running locally in dev, might need localhost. Docker-to-Docker uses service name.
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
)

# Initialize Embeddings via Factory
embeddings_model = LLMFactory.get_service().get_embedding_model()

VECTOR_SIZE = 1536 # Dimensions should ideally come from config or model introspection

def ensure_collection_exists(collection_name: str = settings.QDRANT_COLLECTION):
    """
    Checks if collection exists, if not creates it.
    """
    collections = qdrant_client.get_collections()
    exists = any(c.name == collection_name for c in collections.collections)
    
    if not exists:
        logger.info(f"Creating collection {collection_name}...")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        logger.info(f"Collection {collection_name} created.")
    else:
        logger.info(f"Collection {collection_name} already exists.")

def add_texts(texts: List[str], metadatas: List[dict], collection_name: str = settings.QDRANT_COLLECTION):
    """
    Embeds and indexes texts into Qdrant.
    """
    ensure_collection_exists(collection_name)
    
    embeddings = embeddings_model.embed_documents(texts)
    
    points = [
        models.PointStruct(
            id=idx, # In production, use UUIDs
            vector=embedding,
            payload=metadata
        )
        for idx, (embedding, metadata) in enumerate(zip(embeddings, metadatas))
    ]
    
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )
    logger.info(f"Indexed {len(texts)} documents.")

def search_knowledge_base(
    query_text: str, 
    limit: int = 3, 
    client_id: str = "visionarias",
    collection_name: str = settings.QDRANT_COLLECTION
) -> str:
    """
    Search Qdrant for relevant context.
    Returns a formatted string of context.
    """
    try:
        ensure_collection_exists(collection_name)
        
        query_vector = embeddings_model.embed_query(query_text)
        
        # Filter by client_id for multi-tenancy
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="client_id",
                    match=models.MatchValue(value=client_id)
                )
            ]
        )
        
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit
        )
        
        if not results:
            return ""
            
        # Format context
        context_parts = []
        for hit in results:
            content = hit.payload.get("content", "")
            source = hit.payload.get("source", "unknown")
            context_parts.append(f"- {content} (Source: {source})")
            
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error searching Qdrant: {e}")
        return ""
