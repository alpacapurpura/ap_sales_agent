"""Admin module — Sales Agent routing analytics dashboard (S12).

Cierra el watchpoint S4 ``Closer temperature 0.4 clamped a 0.6 por Kimi
K2.6``: surface tier / specialist distribution + cost + latency per
``(provider, model_responded)`` desde ``sales_agent_routing_log`` +
``sales_agent_llm_call``. Operadores pueden cazar drift cuando un
modelo nuevo (Kimi K2.6, DeepSeek-V4, etc.) entra en producción y la
mezcla cambia bruscamente.

Conversion-rate-vs-baseline alert sigue dependiendo de volumen real
multi-tenant; la página entrega los building blocks (per-model cost,
latency, sample) y delega el alerta a structlog warning helper que se
dispara cuando el costo cross-model varía >5% week-over-week.

# [SALES-AGENT-ROUTING-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import streamlit as st
from sqlalchemy import text

from src.admin.modules._shared import render_tenant_selector
from src.core.database import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _fetch_tier_distribution(db: Session, tenant_filter_sql: str, params: dict[str, Any]) -> list[dict]:
    """Return tier_selected → count rows for the active filter."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT tier_selected, COUNT(*) AS n
                FROM sales_agent_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY tier_selected
                ORDER BY n DESC
                """,
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_specialist_breakdown(db: Session, tenant_filter_sql: str, params: dict[str, Any]) -> list[dict]:
    """Return specialist_routed → count rows for the active filter."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    specialist_routed,
                    stage,
                    COUNT(*) AS n,
                    AVG(NULLIF(confidence, 0)) AS avg_confidence
                FROM sales_agent_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY specialist_routed, stage
                ORDER BY n DESC
                """,
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_model_breakdown(db: Session, tenant_filter_sql: str, params: dict[str, Any]) -> list[dict]:
    """Per-model cost + latency from ``sales_agent_llm_call``.

    Surfaces drift when a new model enters production (Kimi K2.6,
    DeepSeek-V4) — operator sees calls / cost / p50 / p95 grouped by
    ``(provider, model_responded)`` over 30 days.
    """
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    provider,
                    model_responded AS model,
                    COUNT(*) AS n,
                    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
                    SUM(cost_usd) AS total_cost_usd,
                    AVG(input_tokens)::INT AS avg_input_tokens,
                    AVG(output_tokens)::INT AS avg_output_tokens
                FROM sales_agent_llm_call
                WHERE started_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY provider, model_responded
                ORDER BY n DESC
                """,
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_recent_decisions(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
    limit: int = 50,
) -> list[dict]:
    """Return the last ``limit`` routing decisions for the current filter."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    tier_selected,
                    specialist_routed,
                    stage,
                    lead_score,
                    reason,
                    confidence,
                    channel_type,
                    created_at
                FROM sales_agent_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                ORDER BY created_at DESC
                LIMIT :limit
                """,
            ),
            {**params, "limit": limit},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _render_tier_distribution(rows: list[dict]) -> None:
    if not rows:
        st.info("Sin decisiones de routing del sales_agent en los últimos 30 días.")
        return
    total = sum(r["n"] for r in rows) or 1
    cols = st.columns(len(rows))
    for col, row in zip(cols, rows, strict=False):
        share = row["n"] / total
        col.metric(f"Tier {row['tier_selected']}", row["n"], f"{share:.0%}")


def _render_specialist_breakdown(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Specialist enrutado por stage")
    st.dataframe(
        [
            {
                "Specialist": row["specialist_routed"],
                "Stage": row["stage"],
                "Decisiones": row["n"],
                "Confianza promedio": (
                    f"{float(row['avg_confidence']):.2f}" if row.get("avg_confidence") is not None else "—"
                ),
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_model_breakdown(rows: list[dict]) -> None:
    if not rows:
        st.info(
            "Sin LLM calls registrados en ``sales_agent_llm_call`` para la"
            " ventana 30d. Si el callback handler S1 está activo y hay"
            " tráfico, esto debería poblarse en horas.",
        )
        return
    st.markdown("### Modelos en uso (últimos 30 días)")
    st.caption(
        "Mezcla de modelos por proveedor — alerta visual cuando un modelo"
        " nuevo (Kimi K2.6, DeepSeek-V4) absorbe la mayoría del tráfico"
        " sin que la mezcla esperada lo soporte.",
    )
    st.dataframe(
        [
            {
                "Proveedor": row["provider"],
                "Modelo": row["model"] or "—",
                "Llamadas": row["n"],
                "p50 ms": int(row["p50_ms"]) if row.get("p50_ms") is not None else None,
                "p95 ms": int(row["p95_ms"]) if row.get("p95_ms") is not None else None,
                "Costo USD (30d)": (
                    f"${float(row['total_cost_usd']):.4f}" if row.get("total_cost_usd") is not None else "—"
                ),
                "Tokens entrada (prom)": row.get("avg_input_tokens") or 0,
                "Tokens salida (prom)": row.get("avg_output_tokens") or 0,
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_recent_decisions(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Últimas 50 decisiones")
    st.dataframe(
        [
            {
                "Hora": row["created_at"],
                "Tier": row["tier_selected"],
                "Specialist": row["specialist_routed"],
                "Stage": row["stage"],
                "Score": row.get("lead_score") or "—",
                "Canal": row.get("channel_type") or "—",
                "Razón": row["reason"],
                "Confianza": (float(row["confidence"]) if row.get("confidence") is not None else None),
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def render_sales_routing() -> None:
    """Render the Sales Agent routing analytics dashboard (S12)."""
    st.title("🧭 Routing del Sales Agent")
    st.caption(
        "Distribución de tiers, specialists y modelos LLM de los últimos"
        " 30 días. Datos de ``sales_agent_routing_log`` +"
        " ``sales_agent_llm_call``. Útil para cazar drift cuando un modelo"
        " nuevo entra en producción.",
    )

    tenant_id = render_tenant_selector("sales_routing_tenant", allow_all=True)
    tenant_filter_sql = "AND tenant_id = :tenant_id" if tenant_id is not None else ""
    params: dict[str, Any] = {"tenant_id": str(tenant_id)} if tenant_id is not None else {}

    db = SessionLocal()
    try:
        tier_rows = _fetch_tier_distribution(db, tenant_filter_sql, params)
        specialist_rows = _fetch_specialist_breakdown(db, tenant_filter_sql, params)
        model_rows = _fetch_model_breakdown(db, tenant_filter_sql, params)
        recent_rows = _fetch_recent_decisions(db, tenant_filter_sql, params)
    finally:
        db.close()

    st.markdown("### Distribución por tier")
    _render_tier_distribution(tier_rows)
    _render_specialist_breakdown(specialist_rows)
    _render_model_breakdown(model_rows)
    _render_recent_decisions(recent_rows)


__all__ = ["render_sales_routing"]
