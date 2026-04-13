"""
Knowledge tools — search the copilot knowledge base.
"""

from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id, get_user_id
from src.modules.copilot.infrastructure.knowledge.vector_store import (
    CopilotKnowledgeStore,
)

logger = structlog.get_logger()


def _track_knowledge_search(
    tenant_id: UUID,
    query: str,
    scope: str,
    results_count: int,
) -> None:
    """Best-effort server-side event tracking for knowledge searches."""
    try:
        from src.core.database import SessionLocal
        from src.modules.copilot.infrastructure.repositories.event_repository import (
            CopilotEventRepository,
        )

        user_id = get_user_id()
        if not user_id:
            return
        db = SessionLocal()
        try:
            repo = CopilotEventRepository(db)
            repo.record(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type="knowledge_searched",
                event_data={
                    "query": query,
                    "scope": scope,
                    "results_count": results_count,
                },
            )
            db.commit()
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 — tool execution resilience
        logger.debug("knowledge_search_tracking_error", error=str(e))


@tool
def search_knowledge_base(query: str, scope: str = "all") -> str:
    """Busca en la base de conocimiento del negocio y documentacion de la plataforma.

    Args:
        query: Consulta de busqueda en lenguaje natural.
        scope: "help" (docs plataforma), "business" (docs negocio), "all" (ambos).

    Returns:
        Resultados relevantes formateados como markdown.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    try:
        store = CopilotKnowledgeStore()
        results = store.search(query, str(tenant_id), scope, limit=5)
    except Exception as e:
        logger.exception("knowledge_search_error", error=str(e))
        return "Error buscando en la base de conocimiento."

    if not results:
        _track_knowledge_search(tenant_id, query, scope, 0)
        return "No encontre informacion relevante en la base de conocimiento."

    _track_knowledge_search(tenant_id, query, scope, len(results))

    lines = ["## Resultados de la Base de Conocimiento\n"]
    for item in results:
        meta = item.get("meta", {})
        source = meta.get("source", "desconocido")
        scope_label = meta.get("scope", "")
        content = item.get("text", "").strip()
        if content:
            lines.append(f"**Fuente:** {source} ({scope_label})")
            lines.append(content)
            lines.append("---")

    return "\n".join(lines)


KNOWLEDGE_TOOLS = [search_knowledge_base]
