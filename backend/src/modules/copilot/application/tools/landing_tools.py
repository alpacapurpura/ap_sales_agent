"""
Landing page tools — give the copilot access to landing page status.
"""

from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

import structlog

logger = structlog.get_logger()


@tool
def get_landing_pages(status: Optional[str] = None) -> str:
    """Consulta las landing pages del tenant.

    Args:
        status: Filtrar por estado. Opciones: "published", "draft".
                Si no se proporciona, muestra todas.

    Returns:
        Lista de landing pages con su estado, slug y oferta vinculada.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    db = SessionLocal()
    try:
        query = (
            "SELECT lp.id, lp.slug, lp.is_published, lp.offer_id, "
            "lp.created_at, p.name as offer_name "
            "FROM landing_pages lp "
            "LEFT JOIN products p ON p.id = lp.offer_id "
            "WHERE lp.tenant_id = :tid"
        )
        params = {"tid": str(tenant_id)}

        if status == "published":
            query += " AND lp.is_published = true"
        elif status == "draft":
            query += " AND lp.is_published = false"

        query += " ORDER BY lp.created_at DESC"

        rows = db.execute(text(query), params).mappings().all()

        if not rows:
            filter_msg = f" ({status})" if status else ""
            return f"No hay landing pages{filter_msg} configuradas."

        published_count = sum(1 for r in rows if r["is_published"])
        draft_count = len(rows) - published_count

        lines = [f"## Landing Pages ({len(rows)} total: {published_count} publicadas, {draft_count} borradores)\n"]

        for r in rows:
            icon = "✅" if r["is_published"] else "📝"
            state = "publicada" if r["is_published"] else "borrador"
            lines.append(f"{icon} **/{r['slug']}** — {state}")
            if r["offer_name"]:
                lines.append(f"   Oferta: {r['offer_name']}")
            lines.append(f"   Creada: {r['created_at']}")

        return "\n".join(lines)
    except Exception as e:
        logger.error("landing_tools_error", error=str(e))
        return f"Error consultando landing pages: {str(e)}"
    finally:
        db.close()


LANDING_TOOLS = [get_landing_pages]
