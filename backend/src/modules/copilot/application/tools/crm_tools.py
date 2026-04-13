"""
CRM tools — give the copilot access to lead and sales pipeline data.
"""

import json

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()


@tool
def get_lead_summary(temperature: str | None = None, limit: int = 10) -> str:
    """Consulta un resumen de leads del CRM.

    Args:
        temperature: Filtrar por temperatura. Opciones: "HOT", "WARM", "COLD".
                     Si no se proporciona, muestra todos.
        limit: Máximo de leads a retornar (default: 10).

    Returns:
        Resumen de leads con scoring e información relevante.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    db = SessionLocal()
    try:
        # Build query
        query = (
            "SELECT id, profile_data, fit_score, intent_score, temperature, "
            "last_interaction_date, conversation_summary "
            "FROM leads WHERE tenant_id = :tid"
        )
        params = {"tid": str(tenant_id), "lim": limit}

        if temperature:
            query += " AND temperature = :temp"
            params["temp"] = temperature.upper()

        query += " ORDER BY intent_score DESC, fit_score DESC LIMIT :lim"

        rows = db.execute(text(query), params).mappings().all()

        if not rows:
            filter_msg = f" con temperatura {temperature}" if temperature else ""
            return f"No hay leads{filter_msg} en el CRM."

        # Count totals
        count_query = "SELECT temperature, COUNT(*) as cnt FROM leads WHERE tenant_id = :tid GROUP BY temperature"
        counts = db.execute(text(count_query), {"tid": str(tenant_id)}).mappings().all()
        temp_counts = {r["temperature"]: r["cnt"] for r in counts}

        lines = ["## Resumen de Leads\n"]
        total = sum(temp_counts.values())
        lines.append(f"**Total:** {total} leads")
        for temp, cnt in sorted(temp_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {temp}: {cnt}")

        lines.append(
            f"\n### Top {len(rows)} Leads"
            + (f" ({temperature})" if temperature else ""),
        )

        for r in rows:
            profile = r["profile_data"] or {}
            if isinstance(profile, str):
                try:
                    profile = json.loads(profile)
                except (json.JSONDecodeError, TypeError):
                    profile = {}

            name = profile.get("name") or profile.get("first_name", "Sin nombre")
            lines.append(f"\n- **{name}** (temp: {r['temperature']})")
            lines.append(f"  Fit: {r['fit_score']} | Intent: {r['intent_score']}")
            if r["last_interaction_date"]:
                lines.append(f"  Última interacción: {r['last_interaction_date']}")
            if r["conversation_summary"]:
                summary = str(r["conversation_summary"])[:150]
                lines.append(f"  Resumen: {summary}")

        return "\n".join(lines)
    except Exception as e:
        logger.exception("crm_tools_lead_error", error=str(e))
        return f"Error consultando leads: {e!s}"
    finally:
        db.close()


@tool
def get_pipeline_overview() -> str:
    """Obtiene un panorama del pipeline de ventas: ventas por etapa, revenue, métodos de pago.

    Returns:
        Resumen del pipeline de ventas.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    db = SessionLocal()
    try:
        # Sales by stage
        rows = (
            db.execute(
                text(
                    "SELECT stage, status, COUNT(*) as cnt, "
                    "COALESCE(SUM(amount), 0) as total_amount, "
                    "currency "
                    "FROM sales WHERE tenant_id = :tid "
                    "GROUP BY stage, status, currency "
                    "ORDER BY stage, status",
                ),
                {"tid": str(tenant_id)},
            )
            .mappings()
            .all()
        )

        if not rows:
            return "No hay ventas registradas en el pipeline."

        lines = ["## Pipeline de Ventas\n"]

        total_revenue = sum(float(r["total_amount"]) for r in rows)
        total_count = sum(r["cnt"] for r in rows)
        lines.append(f"**Total:** {total_count} ventas, ${total_revenue:,.2f}\n")

        lines.append("### Por Etapa y Estado")
        lines.extend(
            f"  - {r['stage']} / {r['status']}: "
            f"{r['cnt']} ventas, "
            f"${float(r['total_amount']):,.2f} {r['currency']}"
            for r in rows
        )

        return "\n".join(lines)
    except Exception as e:
        logger.exception("crm_tools_pipeline_error", error=str(e))
        return f"Error consultando pipeline: {e!s}"
    finally:
        db.close()


CRM_TOOLS = [get_lead_summary, get_pipeline_overview]
