"""
Connections tools — give the copilot access to integration status details.
"""

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()


@tool
def get_connections_detail() -> str:
    """Obtiene el detalle de integraciones/conexiones externas del tenant.

    Returns:
        Lista de conexiones configuradas con su estado (activa/inactiva),
        tipo de canal y fecha de configuración.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    "SELECT channel_type, is_active, config, created_at, updated_at "
                    "FROM channel_connections WHERE tenant_id = :tid "
                    "ORDER BY channel_type",
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )

        if not rows:
            return (
                "No hay conexiones configuradas.\n\n"
                "Conexiones disponibles: Meta/Instagram, WhatsApp, Shopify, "
                "Google Calendar, Gmail, MailerLite, YouTube, Google Analytics, Google Ads.\n\n"
                "Recomendación: empieza por Meta/Instagram y WhatsApp para activar tu agente de ventas."
            )

        active = [r for r in rows if r["is_active"]]
        inactive = [r for r in rows if not r["is_active"]]

        lines = [
            f"## Conexiones ({len(active)} activa(s), {len(inactive)} inactiva(s))\n",
        ]

        for r in rows:
            icon = "✅" if r["is_active"] else "❌"
            status = "activa" if r["is_active"] else "inactiva"
            lines.append(f"{icon} **{r['channel_type']}** — {status}")
            if r["updated_at"]:
                lines.append(f"   Última actualización: {r['updated_at']}")

        # Suggest missing connections
        configured_types = {r["channel_type"].lower() for r in rows}
        suggested = []
        key_connections = [
            ("meta", "Meta/Instagram"),
            ("whatsapp", "WhatsApp"),
            ("shopify", "Shopify"),
            ("google_analytics", "Google Analytics"),
        ]
        for key, label in key_connections:
            if key not in configured_types:
                suggested.append(label)

        if suggested:
            lines.append("\n### Conexiones Sugeridas")
            lines.extend(f"  - {s}" for s in suggested)

        return "\n".join(lines)
    except Exception as e:
        logger.error("connections_tools_error", error=str(e))
        return f"Error consultando conexiones: {e!s}"
    finally:
        db.close()


CONNECTIONS_TOOLS = [get_connections_detail]
