"""
Analytics tools — give the copilot access to funnel metrics and sales data.
"""

import json
from datetime import timedelta

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()


@tool
def get_funnel_metrics(period: str | None = None) -> str:
    """Consulta métricas del funnel de ventas (revenue, conversiones, leads).

    Args:
        period: Período a consultar. Opciones: "7d", "30d", "90d".
                Por defecto: "30d".

    Returns:
        Resumen de métricas del funnel.
    """
    from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
        SalesMetricsRepository,
    )

    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant."

    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period or "30d", 30)
    end_date = utc_now()
    start_date = end_date - timedelta(days=days)

    db = SessionLocal()
    try:
        repo = SalesMetricsRepository(db)

        # Sales summary (grouped by stage, offer, source)
        summary = repo.get_sales_summary(tenant_id, start_date, end_date)
        total_conversions = repo.get_total_conversion_customers(
            tenant_id,
            start_date,
            end_date,
        )
        total_sqls = repo.get_total_sql_count(tenant_id, start_date, end_date)

        if not summary and total_conversions == 0:
            return f"No hay datos de métricas en los últimos {days} días."

        lines = [f"## Métricas del Funnel (últimos {days} días)\n"]

        # Aggregate totals
        total_revenue = sum(s.total_revenue for s in summary)
        total_sales = sum(s.count for s in summary)
        unique_customers = sum(s.unique_customers for s in summary)

        lines.append(f"- **Revenue total:** ${total_revenue:,.2f}")
        lines.append(f"- **Ventas completadas:** {total_sales}")
        lines.append(f"- **Clientes únicos:** {unique_customers}")
        lines.append(f"- **Conversiones (CONVERSION stage):** {total_conversions}")
        lines.append(f"- **SQLs (Sales Qualified Leads):** {total_sqls}")

        # Breakdown by stage
        if summary:
            lines.append("\n### Por Etapa")
            stage_agg = {}
            for s in summary:
                stage = s.stage or "N/A"
                if stage not in stage_agg:
                    stage_agg[stage] = {"count": 0, "revenue": 0.0}
                stage_agg[stage]["count"] += s.count
                stage_agg[stage]["revenue"] += s.total_revenue
            for stage, data in stage_agg.items():
                lines.append(
                    f"  - {stage}: {data['count']} ventas, ${data['revenue']:,.2f}",
                )

        # Build ui_action payload for MetricSummaryCard
        ui_metrics = [
            {"label": "Revenue Total", "value": f"${total_revenue:,.2f}"},
            {"label": "Ventas", "value": str(total_sales)},
            {"label": "Clientes Únicos", "value": str(unique_customers)},
            {"label": "Conversiones", "value": str(total_conversions)},
            {"label": "SQLs", "value": str(total_sqls)},
        ]

        return json.dumps(
            {
                "text": "\n".join(lines),
                "ui_action": {
                    "type": "metric_summary",
                    "metrics": ui_metrics,
                },
            },
        )
    except Exception as e:
        logger.error("analytics_tools_error", error=str(e))
        return f"Error consultando métricas: {e!s}"
    finally:
        db.close()


ANALYTICS_TOOLS = [get_funnel_metrics]
