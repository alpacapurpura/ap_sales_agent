import os
import tempfile
import logging
from typing import List, Dict, Optional, Callable, Any, Union
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document

from src.config import settings
from src.core.llm.factory import LLMFactory
from src.services.vector_store import (
    add_texts, 
    ensure_collection_exists, 
    qdrant_client, 
    delete_vectors_by_source, 
    delete_collection, 
    search_knowledge_base, 
    update_vectors_category, 
    fetch_vectors_by_source
)
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "protocol_boundary", 
    "sales_persuasion", 
    "financial_legal",
    "product_logic", 
    "avatar_psychology", 
    "brand_authority"
]

class KnowledgeService:
    """
    Service for managing the Knowledge Base lifecycle:
    Ingestion, Classification, Management, and Retrieval.
    """
    
    def __init__(self):
        self.llm_service = LLMFactory.get_service()

    def get_valid_categories(self) -> List[str]:
        return VALID_CATEGORIES

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Returns stats about Qdrant collections and Document DB.
        """
        stats = {
            "qdrant_connected": False,
            "vector_count": 0,
            "doc_count": 0,
            "llm_model": settings.OPENAI_MODEL
        }
        
        try:
            collections = qdrant_client.get_collections()
            if settings.QDRANT_COLLECTION_HYBRID in [c.name for c in collections.collections]:
                info = qdrant_client.get_collection(settings.QDRANT_COLLECTION_HYBRID)
                stats["vector_count"] = info.vectors_count
                stats["qdrant_connected"] = True
        except Exception as e:
            logger.error(f"Error fetching Qdrant stats: {e}")
            
        try:
            stats["doc_count"] = len(DocumentService.list_documents())
        except Exception as e:
            logger.error(f"Error fetching DB stats: {e}")
            stats["doc_count"] = -1
            
        return stats

    def extract_preview(self, filename: str, file_content: bytes, limit: int = 2000) -> str:
        """
        Extracts a text preview from a file (PDF or Text) for classification.
        """
        try:
            # Text files
            if not filename.endswith(".pdf"):
                return file_content.decode("utf-8", errors="ignore")[:limit]
            
            # PDF files
            suffix = f".{filename.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
                
            try:
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                text = " ".join([d.page_content for d in docs])
                return text[:limit]
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Error extracting preview from {filename}: {e}")
            return ""

    def classify_preview(self, text_preview: str) -> str:
        """
        Uses LLM to classify the document into one of the VALID_CATEGORIES.
        """
        prompt = f"""
        You are a document classifier for a business knowledge base.
        
        CATEGORIES:
        {", ".join(VALID_CATEGORIES)}
        
        DEFINITIONS:
        - protocol_boundary: Rules, camera requirements, punctuality, filters.
        - sales_persuasion: Sales scripts, objection handling, re-framing.
        - financial_legal: Prices, payments, contracts, guarantees, refunds.
        - product_logic: Dates, schedules, curriculum, platform, deliverables.
        - avatar_psychology: Customer pain points, desires, emotions, identity.
        - brand_authority: Founder stories (Camila/Ileana), philosophy, differentiation.
        
        TASK:
        Analyze the text below and return ONLY the exact category name from the list above that best fits.
        If uncertain, return 'product_logic'.
        
        TEXT PREVIEW:
        {text_preview[:3000]}...
        
        CATEGORY:
        """
        
        try:
            category = self.llm_service.generate_response(messages=[], system_prompt=prompt, max_tokens=20).strip()
            category = category.lower()
            if category not in VALID_CATEGORIES:
                return "product_logic"
            return category
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            return "product_logic"

    def ingest_file(
        self, 
        filename: str, 
        file_content: bytes, 
        categories: List[str], 
        strategy: str,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a file (bytes) -> Temp File -> Load -> Split -> Embed -> Index.
        """
        if on_progress: on_progress("📥 Guardando archivo temporal...")
        
        # Create temp file
        suffix = f".{filename.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            # Load Document
            if on_progress: on_progress("📄 Leyendo contenido del documento...")
            docs = []
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
            else:
                loader = TextLoader(tmp_path)
                docs = loader.load()
            
            # Clean up temp file immediately after loading
            os.unlink(tmp_path)

            full_text = " ".join([d.page_content for d in docs])
            splits = []
            
            # --- CHUNKING LOGIC ---
            if "Básico" in strategy:
                if on_progress: on_progress("🔪 Fragmentando texto (Estrategia Básica)...")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)
            else:
                # Advanced Logic: Small-to-Big + Contextual Retrieval + Semantic Parents
                if on_progress: on_progress("🧠 Analizando estructura (Semantic + Small-to-Big)...")
                
                # 1. Parent Split (Semantic -> Safety Check)
                if on_progress: on_progress("📑 Generando Bloques Padres Semánticos...")
                
                # 1.1 Try Semantic Split
                embeddings = self.llm_service.get_embedding_model()
                semantic_splitter = SemanticChunker(embeddings=embeddings, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90)
                semantic_parents = semantic_splitter.create_documents([full_text])
                
                # 1.2 Safety Check: Recursive Split if too large (Physical Limit)
                final_parent_docs = []
                safety_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                
                for p_doc in semantic_parents:
                    if len(p_doc.page_content) > 2000:
                         # Split this giant semantic chunk into manageable parent chunks
                         sub_parents = safety_splitter.split_documents([p_doc])
                         final_parent_docs.extend(sub_parents)
                    else:
                        final_parent_docs.append(p_doc)
                
                total_parents = len(final_parent_docs)
                if on_progress: on_progress(f"✨ Procesando {total_parents} bloques padres (Híbridos). Generando hijos y contexto...")

                import uuid

                # 2. Child Split & Contextual Retrieval Loop
                child_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
                
                processed_children = 0
                
                for p_idx, p_doc in enumerate(final_parent_docs):
                    p_id = str(uuid.uuid4())
                    p_content = p_doc.page_content
                    
                    # Split Parent into Children
                    child_docs = child_splitter.split_documents([p_doc])
                    
                    for c_idx, chunk in enumerate(child_docs):
                        processed_children += 1
                        if on_progress and (processed_children % 5 == 0):
                             on_progress(f"🧠 Contextualizando hijo {processed_children} (del Padre {p_idx+1}/{total_parents})...")

                        # Contextual Retrieval (Anthropic)
                        # We use the PARENT content as the context source (Gold Standard)
                        prompt_context = f"""
                        <document_context>
                        {p_content}
                        </document_context>
                        
                        <chunk_to_explain>
                        {chunk.page_content}
                        </chunk_to_explain>
                        
                        TASK:
                        Give a short, specific context (2-3 sentences) that situates this specific chunk within the provided document section. 
                        Explain what it is about, using the surrounding text as a guide.
                        Example: "This section outlines the refund policy details found in the Terms of Service, specifically regarding the 30-day guarantee."
                        IMPORTANT: Output the context in the SAME LANGUAGE as the document text provided below (Spanish).
                        
                        CONTEXT:
                        """
                        
                        try:
                            specific_context = self.llm_service.generate_response(messages=[], system_prompt=prompt_context, max_tokens=100).strip()
                        except Exception as e:
                            logger.warning(f"Failed to generate context for child: {e}")
                            specific_context = f"Fragmento del documento {filename}"

                        # Construct Enriched Content for Embedding (Context + Child)
                        enriched_content = f"{specific_context}\n\n{chunk.page_content}"
                        
                        new_meta = chunk.metadata.copy()
                        new_meta.update({
                            "source": filename,
                            "doc_category": categories,
                            "strategy": "small_to_big_contextual",
                            "original_context": specific_context,
                            "parent_id": p_id,
                            "parent_content": p_content # Store Big Chunk for Retrieval
                        })
                        
                        splits.append(Document(page_content=enriched_content, metadata=new_meta))

            # Indexing
            if on_progress: on_progress(f"💾 Indexando {len(splits)} vectores en Qdrant...")
            texts = [s.page_content for s in splits]
            metadatas = [s.metadata for s in splits]
            
            # Normalize metadata
            for m in metadatas:
                if "source" not in m: m["source"] = filename
                if "doc_category" not in m: m["doc_category"] = categories
                
            add_texts(texts, metadatas, collection_name=settings.QDRANT_COLLECTION_HYBRID)
            
            if on_progress: on_progress("📝 Registrando documento en base de datos...")
            doc_record = DocumentService.create_document(
                filename=filename,
                collection_name=settings.QDRANT_COLLECTION_HYBRID,
                chunk_count=len(splits),
                category=",".join(categories),
                metadata={"strategy": strategy}
            )
            
            return {
                "success": True,
                "chunks": len(splits),
                "id": doc_record.id
            }
            
        except Exception as e:
            logger.error(f"Error ingesting file {filename}: {e}")
            # Ensure temp file is deleted if error occurred before unlink
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e

    def update_document_category(self, filename: str, new_categories: List[str]) -> bool:
        """
        Updates category in both DB and Vector Store.
        """
        try:
            # 1. Update Postgres
            new_cat_str = ",".join(new_categories)
            db_success = DocumentService.update_document_category(filename, settings.QDRANT_COLLECTION_HYBRID, new_cat_str)
            
            # 2. Update Qdrant Payloads
            vec_success = update_vectors_category(settings.QDRANT_COLLECTION_HYBRID, filename, new_categories)
            
            return db_success and vec_success
        except Exception as e:
            logger.error(f"Error updating category for {filename}: {e}")
            return False

    def delete_document(self, filename: str) -> bool:
        """
        Deletes document from both DB and Vector Store.
        """
        try:
            vec_success = delete_vectors_by_source(settings.QDRANT_COLLECTION_HYBRID, filename)
            db_success = DocumentService.delete_document_record(filename, settings.QDRANT_COLLECTION_HYBRID)
            return vec_success and db_success
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            return False

    def search(self, query: str, filters: Optional[Dict] = None, limit: int = 5, return_raw: bool = False) -> Union[str, List[Dict]]:
        return search_knowledge_base(query, limit=limit, filters=filters, return_raw=return_raw)

    def list_documents(self):
        return DocumentService.list_documents()

    def fetch_vectors(self, filename: str, limit: int = 1000):
        return fetch_vectors_by_source(settings.QDRANT_COLLECTION_HYBRID, filename, limit)
    
    def sync_from_qdrant(self):
        return DocumentService.sync_from_qdrant(settings.QDRANT_COLLECTION_HYBRID)
    
    def reset_knowledge_base(self):
        delete_collection(settings.QDRANT_COLLECTION_HYBRID)
        ensure_collection_exists(settings.QDRANT_COLLECTION_HYBRID)
