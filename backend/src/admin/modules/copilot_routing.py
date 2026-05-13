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
from luana_core_platform.core.database import SessionLocal
from sqlalchemy import text

from src.admin.modules._shared import render_tenant_selector

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
    """Latency p50 / p95 per model + cost — reads ``copilot_llm_call`` directly.

    Post Phase 2 atomic switch every LLM invocation is logged in the
    typed event-sourced ``copilot_llm_call`` table. We aggregate
    ``duration_ms`` and ``cost_usd`` per ``model_responded`` so the
    routing dashboard surfaces both latency and per-model cost without
    parsing JSONB shapes.
    """
    # The shared SQL fragment uses ``tenant_id = :tenant_id``; rebind it
    # to the llm-call table's column for this query.
    llm_filter_sql = tenant_filter_sql.replace(
        "tenant_id = :tenant_id",
        "tenant_id = :tenant_id",
    )
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    model_responded AS model,
                    provider,
                    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
                    SUM(cost_usd) AS total_cost_usd,
                    AVG(input_tokens)::INT AS avg_input_tokens,
                    AVG(output_tokens)::INT AS avg_output_tokens,
                    COUNT(*) AS n
                FROM copilot_llm_call
                WHERE started_at >= NOW() - INTERVAL '30 days'
                {llm_filter_sql}
                GROUP BY model_responded, provider
                ORDER BY n DESC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_runaway_output_alerts(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
    *,
    runaway_threshold: int = 4000,
) -> list[dict[str, Any]]:
    """Count LLM calls whose output exceeded the runaway threshold.

    Groups by ``(provider, model_responded)``. Heuristic detection of
    the silent ``max_tokens → max_completion_tokens``
    rewrite documented in TODO #32 — when the rewrite leaks through to
    a partner endpoint that does not honour the new key, the model
    generates well past the intended cap. ``4000`` is a deliberately
    generous default: most Nicolify caps land at ``2000`` or below, so
    output above ``4000`` for a capped role is suspicious.
    """
    llm_filter_sql = tenant_filter_sql.replace(
        "tenant_id = :tenant_id",
        "tenant_id = :tenant_id",
    )
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    provider,
                    model_responded AS model,
                    COUNT(*)        AS runaway_calls,
                    MAX(output_tokens) AS max_output_tokens
                FROM copilot_llm_call
                WHERE started_at >= NOW() - INTERVAL '30 days'
                  AND output_tokens >= :threshold
                {llm_filter_sql}
                GROUP BY provider, model_responded
                ORDER BY runaway_calls DESC
                """,
            ),
            {**params, "threshold": runaway_threshold},
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
    st.markdown("### Latencia + costo por modelo (copilot_llm_call)")
    st.dataframe(
        [
            {
                "Modelo": row.get("model") or "—",
                "Proveedor": row.get("provider") or "—",
                "p50 ms": int(row["p50_ms"]) if row.get("p50_ms") is not None else None,
                "p95 ms": int(row["p95_ms"]) if row.get("p95_ms") is not None else None,
                "Costo USD (30d)": (
                    f"${float(row['total_cost_usd']):.4f}" if row.get("total_cost_usd") is not None else "—"
                ),
                "Tokens entrada (prom)": row.get("avg_input_tokens") or 0,
                "Tokens salida (prom)": row.get("avg_output_tokens") or 0,
                "Llamadas": row["n"],
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_runaway_output_alerts(rows: list[dict]) -> None:
    """Surface output-tokens spikes per (provider, model).

    Heuristic proxy for the silent ``max_tokens`` rewrite breaking
    partner endpoints (TODO #32).
    """
    if not rows:
        st.success(
            "✅ Sin tokens de salida runaway en los últimos 30 días"
            " (umbral 4000). Cap respetado por todos los proveedores.",
        )
        return
    st.warning(
        "⚠️ Detectados tokens de salida >= 4000 — posible silent rewrite"
        " ``max_tokens → max_completion_tokens`` (TODO #32). Revisar antes"
        " de que escale en costo.",
    )
    st.dataframe(
        [
            {
                "Proveedor": row["provider"],
                "Modelo": row["model"],
                "Llamadas runaway": row["runaway_calls"],
                "Máx tokens de salida": row["max_output_tokens"],
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
        runaway_rows = _fetch_runaway_output_alerts(db, tenant_filter_sql, params)
        recent_rows = _fetch_recent_decisions(db, tenant_filter_sql, params)
    finally:
        db.close()

    st.markdown("### Distribución por tier")
    _render_tier_distribution(tier_rows)

    _render_classifier_breakdown(classifier_rows)
    _render_cache_metrics(cache_metrics)
    _render_latency_table(latency_rows)
    _render_runaway_output_alerts(runaway_rows)
    _render_recent_decisions(recent_rows)
