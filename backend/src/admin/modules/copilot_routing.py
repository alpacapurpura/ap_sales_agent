"""Admin module — Copilot routing analytics dashboard.

Reads ``copilot_routing_log`` (per-turn tier decision) cross-joined with
``copilot_trace_event`` (per-turn cost / latency / cache_hit_rate) and
surfaces the F8 §5.5 KPIs:

* Tier distribution (count + %).
* Classifier breakdown (rule vs llm vs default).
* Average confidence per classifier.
* Cache hit rate over time (from trace ``turn_end`` rows).
* Latency p50 / p95 per tier (from trace ``llm_call`` rows).
* Recent decisions table — last 100 rows for spot-checking misroutes.

[COPILOT-LLM-CLASSIFIER-F8]: routing fallback chain.
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
                FROM copilot_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY tier_selected
                ORDER BY n DESC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_classifier_breakdown(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
) -> list[dict]:
    """Return classifier_used → (count, avg_confidence) rows."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    classifier_used,
                    COUNT(*) AS n,
                    AVG(confidence) AS avg_confidence
                FROM copilot_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY classifier_used
                ORDER BY n DESC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_cache_metrics(db: Session, tenant_filter_sql: str, params: dict[str, Any]) -> dict:
    """Aggregate cache_hit_rate from ``turn_end`` trace rows.

    The recorder writes ``data.cache_hit_rate`` (F8) for each turn. We fold
    them into a single average across the window. Rows that pre-date the
    F8 instrumentation simply lack the field and are skipped.
    """
    row = (
        db.execute(
            text(
                f"""
                SELECT
                    AVG(NULLIF((data ->> 'cache_hit_rate')::float, 0)) AS avg_cache_hit_rate,
                    COUNT(*) FILTER (WHERE (data ->> 'cache_hit_rate') IS NOT NULL) AS sampled_turns,
                    AVG((data ->> 'total_tokens')::int) AS avg_total_tokens
                FROM copilot_trace_event
                WHERE event_type = 'turn_end'
                  AND created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                """
            ),
            params,
        )
        .mappings()
        .first()
    )
    return dict(row) if row else {}


def _fetch_latency_per_tier(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
) -> list[dict]:
    """Latency p50 / p95 per tier — joins routing_log with trace turn_end on conversation+turn proximity.

    The turn_end row carries ``duration_ms`` for the end-to-end turn. We
    aggregate by the model name recorded in ``data->>'model'`` since it's
    the most stable cross-table join key today (F-pos can wire ``message_id``
    into the trace once we standardise it).
    """
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    data ->> 'model' AS model,
                    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
                    COUNT(*) AS n
                FROM copilot_trace_event
                WHERE event_type = 'turn_end'
                  AND duration_ms IS NOT NULL
                  AND created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                GROUP BY data ->> 'model'
                ORDER BY n DESC
                """
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
    limit: int = 100,
) -> list[dict]:
    """Return the last ``limit`` routing decisions for the current filter."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    tier_selected,
                    classifier_used,
                    reason,
                    confidence,
                    user_msg_length,
                    tools_available,
                    created_at
                FROM copilot_routing_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
                {tenant_filter_sql}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {**params, "limit": limit},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _render_tier_distribution(rows: list[dict]) -> None:
    if not rows:
        st.info("Sin decisiones de routing en los últimos 30 días.")
        return
    total = sum(r["n"] for r in rows) or 1
    cols = st.columns(len(rows))
    for col, row in zip(cols, rows, strict=False):
        share = row["n"] / total
        col.metric(f"Tier {row['tier_selected']}", row["n"], f"{share:.0%}")


def _render_classifier_breakdown(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Clasificador que decidió")
    for row in rows:
        avg_conf = row.get("avg_confidence")
        conf_str = f" · confianza promedio {float(avg_conf):.2f}" if avg_conf is not None else ""
        st.markdown(f"- **{row['classifier_used']}**: {row['n']} decisiones{conf_str}")


def _render_cache_metrics(metrics: dict) -> None:
    if not metrics or not metrics.get("sampled_turns"):
        st.info(
            "Aún no hay datos de cache hit rate. Las trazas con instrumentación F8"
            " (campo ``data.cache_hit_rate`` en ``turn_end``) empiezan a poblarse"
            " tras el deploy."
        )
        return
    cols = st.columns(3)
    cache_rate = metrics.get("avg_cache_hit_rate")
    cols[0].metric(
        "Cache hit rate (avg)",
        f"{float(cache_rate):.1%}" if cache_rate is not None else "—",
    )
    cols[1].metric("Turns muestreados", metrics.get("sampled_turns") or 0)
    avg_tokens = metrics.get("avg_total_tokens")
    cols[2].metric(
        "Tokens promedio / turn",
        f"{float(avg_tokens):,.0f}" if avg_tokens is not None else "—",
    )


def _render_latency_table(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Latencia por modelo (turn_end)")
    st.dataframe(
        [
            {
                "Modelo": row.get("model") or "—",
                "p50 ms": int(row["p50_ms"]) if row.get("p50_ms") is not None else None,
                "p95 ms": int(row["p95_ms"]) if row.get("p95_ms") is not None else None,
                "Turnos": row["n"],
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_recent_decisions(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Últimas 100 decisiones")
    st.dataframe(
        [
            {
                "Hora": row["created_at"],
                "Tier": row["tier_selected"],
                "Classifier": row["classifier_used"],
                "Razón": row["reason"],
                "Confianza": float(row["confidence"]) if row.get("confidence") is not None else None,
                "Long. msg": row["user_msg_length"],
                "# tools": row["tools_available"],
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def render_copilot_routing() -> None:
    """Render the Copilot routing analytics dashboard (F8 §5.5)."""
    st.title("🧭 Routing del Copilot")
    st.caption(
        "Distribución de tiers, latencia y cache hit rate de los últimos 30 días."
        " Datos de ``copilot_routing_log`` + ``copilot_trace_event``."
    )

    tenant_id = render_tenant_selector("copilot_routing_tenant", allow_all=True)
    tenant_filter_sql = "AND tenant_id = :tenant_id" if tenant_id is not None else ""
    params: dict[str, Any] = {"tenant_id": str(tenant_id)} if tenant_id is not None else {}

    db = SessionLocal()
    try:
        tier_rows = _fetch_tier_distribution(db, tenant_filter_sql, params)
        classifier_rows = _fetch_classifier_breakdown(db, tenant_filter_sql, params)
        cache_metrics = _fetch_cache_metrics(db, tenant_filter_sql, params)
        latency_rows = _fetch_latency_per_tier(db, tenant_filter_sql, params)
        recent_rows = _fetch_recent_decisions(db, tenant_filter_sql, params)
    finally:
        db.close()

    st.markdown("### Distribución por tier")
    _render_tier_distribution(tier_rows)

    _render_classifier_breakdown(classifier_rows)
    _render_cache_metrics(cache_metrics)
    _render_latency_table(latency_rows)
    _render_recent_decisions(recent_rows)
