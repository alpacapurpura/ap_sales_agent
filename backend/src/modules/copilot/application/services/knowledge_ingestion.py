"""KnowledgeIngestionService — Chunk, embed, and upsert documents into copilot knowledge."""

import uuid

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import ModuleDescriptor, get_module_registry
from src.modules.copilot.infrastructure.knowledge.vector_store import (
    CopilotKnowledgeStore,
)

logger = structlog.get_logger()


def _summarize_brand(registry: dict[str, ModuleDescriptor], db: Session, tenant_id: str) -> list[str]:
    """Summarize brand data into markdown lines."""
    parts: list[str] = []
    brand_desc = registry.get("brand")
    if not brand_desc or not brand_desc.repo_factory or not brand_desc.read_fn:
        return parts

    repo = brand_desc.repo_factory(db)
    data = brand_desc.read_fn(repo, tenant_id)
    if not data:
        return parts

    raw = data.model_dump(mode="json") if hasattr(data, "model_dump") else {}
    if not raw:
        return parts

    parts.append("## Brand Studio\n")
    for key, val in raw.items():
        if val and not isinstance(val, (dict, list)):
            parts.append(f"- **{key}**: {val}")
        elif isinstance(val, dict):
            non_empty = {k: v for k, v in val.items() if v}
            if non_empty:
                parts.append(f"### {key}")
                for k, v in non_empty.items():
                    parts.append(f"- {k}: {v}")
    return parts


def _summarize_offers(registry: dict[str, ModuleDescriptor], db: Session, tenant_id: str) -> list[str]:
    """Summarize offer data into markdown lines."""
    parts: list[str] = []
    offer_desc = registry.get("offer")
    if not offer_desc or not offer_desc.repo_factory or not offer_desc.read_fn:
        return parts

    repo = offer_desc.repo_factory(db)
    offers = offer_desc.read_fn(repo, tenant_id)
    if not offers:
        return parts

    parts.append("\n## Ofertas")
    for o in offers if isinstance(offers, list) else [offers]:
        name = getattr(o, "name", None) or getattr(o, "title", "Sin nombre")
        parts.append(f"- {name}")
    return parts


def _summarize_connections(registry: dict[str, ModuleDescriptor], db: Session, tenant_id: str) -> list[str]:
    """Summarize active connections into markdown lines."""
    parts: list[str] = []
    conn_desc = registry.get("connections")
    if not conn_desc or not conn_desc.repo_factory or not conn_desc.read_fn:
        return parts

    repo = conn_desc.repo_factory(db)
    conns = conn_desc.read_fn(repo, tenant_id)
    if not conns:
        return parts

    parts.append("\n## Conexiones Activas")
    for c in conns if isinstance(conns, list) else [conns]:
        ch_type = getattr(c, "channel_type", "unknown")
        active = getattr(c, "is_active", False)
        if active:
            parts.append(f"- {ch_type}")
    return parts


class KnowledgeIngestionService:
    """Handles document chunking, embedding, and upsert into Qdrant."""

    def __init__(self) -> None:
        """Initialize knowledge ingestion service."""
        self.store = CopilotKnowledgeStore()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
        )

    def ingest_document(
        self,
        tenant_id: str,
        content: str,
        source: str = "upload",
        scope: str = "business",
    ) -> dict:
        """Chunk text, embed, and upsert. Returns document_id and chunk count."""
        document_id = str(uuid.uuid4())
        chunks = self.splitter.split_text(content)

        if not chunks:
            return {"document_id": document_id, "chunks_indexed": 0}

        metadatas = [
            {
                "document_id": document_id,
                "scope": scope,
                "source": source,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        count = self.store.add_documents(chunks, metadatas, tenant_id)
        logger.info(
            "knowledge_ingested",
            tenant_id=tenant_id,
            document_id=document_id,
            chunks=count,
            scope=scope,
        )
        return {"document_id": document_id, "chunks_indexed": count}

    def ingest_product_summary(self, tenant_id: str) -> dict:
        """Auto-generate a summary from Brand+Offer+Connections and ingest as help scope."""
        registry = get_module_registry()
        db = SessionLocal()
        parts: list[str] = []

        try:
            parts.extend(_summarize_brand(registry, db, tenant_id))
            parts.extend(_summarize_offers(registry, db, tenant_id))
            parts.extend(_summarize_connections(registry, db, tenant_id))
        finally:
            db.close()

        if not parts:
            return {"document_id": "", "chunks_indexed": 0}

        summary_text = "\n".join(parts)
        return self.ingest_document(
            tenant_id=tenant_id,
            content=summary_text,
            source="auto_summary",
            scope="help",
        )

    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete all chunks for a document."""
        return self.store.delete_by_document_id(tenant_id, document_id)
