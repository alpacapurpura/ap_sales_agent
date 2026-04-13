"""
Sales Agent tools — give the copilot access to the AI sales agent status.
"""

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()


@tool
def get_sales_agent_status() -> str:
    """Obtiene el estado del agente de ventas IA: conversaciones activas, mensajes recientes, rendimiento.

    Returns:
        Resumen del estado y actividad del agente de ventas.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    db = SessionLocal()
    try:
        # Total conversations (unique leads with messages)
        total_convs = (
            db.execute(
                text(
                    "SELECT COUNT(DISTINCT user_id) FROM messages "
                    "WHERE tenant_id = :tid",
                ),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )

        # Recent conversations (last 7 days)
        recent_convs = (
            db.execute(
                text(
                    "SELECT COUNT(DISTINCT user_id) FROM messages "
                    "WHERE tenant_id = :tid AND created_at > NOW() - INTERVAL '7 days'",
                ),
                {"tid": str(tenant_id)},
            ).scalar()
            or 0
        )

        # Message counts by role (last 30 days)
        msg_counts = (
            db.execute(
                text(
                    "SELECT role, COUNT(*) as cnt FROM messages "
                    "WHERE tenant_id = :tid AND created_at > NOW() - INTERVAL '30 days' "
                    "GROUP BY role",
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )

        role_counts = {r["role"]: r["cnt"] for r in msg_counts}

        # Channel distribution
        channel_dist = (
            db.execute(
                text(
                    "SELECT COALESCE(channel, 'unknown') as ch, COUNT(DISTINCT user_id) as cnt "
                    "FROM messages WHERE tenant_id = :tid "
                    "GROUP BY channel",
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )

        if total_convs == 0:
            return "El agente de ventas no tiene conversaciones registradas aún."

        lines = ["## Estado del Agente de Ventas\n"]
        lines.append(f"- **Conversaciones totales:** {total_convs}")
        lines.append(f"- **Activas (últimos 7 días):** {recent_convs}")
        lines.append("- **Mensajes (últimos 30 días):**")
        lines.append(f"  - Del usuario: {role_counts.get('user', 0)}")
        lines.append(f"  - Del agente: {role_counts.get('assistant', 0)}")
        lines.append(f"  - Sistema: {role_counts.get('system', 0)}")

        if channel_dist:
            lines.append("\n### Por Canal")
            lines.extend(f"  - {ch['ch']}: {ch['cnt']} leads" for ch in channel_dist)

        return "\n".join(lines)
    except Exception as e:
        logger.error("sales_agent_tools_error", error=str(e))
        return f"Error consultando agente de ventas: {e!s}"
    finally:
        db.close()


SALES_AGENT_TOOLS = [get_sales_agent_status]
