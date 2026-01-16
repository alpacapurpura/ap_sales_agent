from typing import List, Optional
from sqlalchemy.orm import Session
from src.services.models import Document
from src.services.database import SessionLocal
import uuid

from src.services.vector_store import qdrant_client
from qdrant_client.http import models as qmodels

class DocumentService:
    @staticmethod
    def sync_from_qdrant(collection_name: str) -> dict:
        """
        Rebuilds Postgres document index from Qdrant vectors.
        Returns stats: {created: int, skipped: int, errors: int}
        """
        stats = {"created": 0, "skipped": 0, "errors": 0}
        db: Session = SessionLocal()
        
        try:
            # 1. Scroll all points (this can be heavy for millions, but fine for <10k)
            # We only need payloads, specifically 'source' and 'doc_category'
            offset = None
            unique_docs = {} # filename -> {chunks: int, category: str}
            
            while True:
                scroll_result = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=None,
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset
                )
                points, offset = scroll_result
                
                if not points:
                    break
                    
                for p in points:
                    payload = p.payload or {}
                    source = payload.get("source")
                    
                    if not source:
                        continue
                        
                    # Aggregate stats
                    if source not in unique_docs:
                        # Handle category: could be list or string in payload
                        cat_raw = payload.get("doc_category", "uncategorized")
                        if isinstance(cat_raw, list):
                            cat_str = ",".join(cat_raw)
                        else:
                            cat_str = str(cat_raw)
                            
                        unique_docs[source] = {
                            "chunks": 0,
                            "category": cat_str,
                            "strategy": payload.get("strategy", "unknown")
                        }
                    
                    unique_docs[source]["chunks"] += 1
            
            # 2. Reconcile with DB
            for filename, info in unique_docs.items():
                # Check if exists
                exists = db.query(Document).filter(
                    Document.filename == filename,
                    Document.collection_name == collection_name
                ).first()
                
                if not exists:
                    try:
                        new_doc = Document(
                            filename=filename,
                            collection_name=collection_name,
                            chunk_count=info["chunks"],
                            category=info["category"],
                            metadata_info={"strategy": info["strategy"], "restored": True}
                        )
                        db.add(new_doc)
                        stats["created"] += 1
                    except Exception as e:
                        print(f"Error restoring {filename}: {e}")
                        stats["errors"] += 1
                else:
                    # Update chunk count just in case
                    if exists.chunk_count != info["chunks"]:
                        exists.chunk_count = info["chunks"]
                    stats["skipped"] += 1
            
            db.commit()
            return stats
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def create_document(
        filename: str, 
        collection_name: str, 
        chunk_count: int, 
        category: str,
        metadata: dict = None
    ) -> Document:
        db: Session = SessionLocal()
        try:
            doc = Document(
                filename=filename,
                collection_name=collection_name,
                chunk_count=chunk_count,
                category=category,
                metadata_info=metadata or {}
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return doc
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def list_documents(collection_name: Optional[str] = None) -> List[Document]:
        db: Session = SessionLocal()
        try:
            query = db.query(Document)
            if collection_name:
                query = query.filter(Document.collection_name == collection_name)
            return query.order_by(Document.upload_date.desc()).all()
        finally:
            db.close()

    @staticmethod
    def update_document_category(filename: str, collection_name: str, new_category: str) -> bool:
        """
        Updates the category of a document in Postgres.
        """
        db: Session = SessionLocal()
        try:
            doc = db.query(Document).filter(
                Document.filename == filename,
                Document.collection_name == collection_name
            ).first()
            
            if doc:
                doc.category = new_category
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    def delete_document_record(filename: str, collection_name: str) -> bool:
        """
        Deletes the record from Postgres. 
        Note: Does not delete from Qdrant (that logic is in vector_store).
        """
        db: Session = SessionLocal()
        try:
            # Delete all entries with this filename in this collection
            # (In case of duplicates, though we should avoid them)
            docs = db.query(Document).filter(
                Document.filename == filename,
                Document.collection_name == collection_name
            ).all()
            
            for doc in docs:
                db.delete(doc)
            
            db.commit()
            return len(docs) > 0
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
