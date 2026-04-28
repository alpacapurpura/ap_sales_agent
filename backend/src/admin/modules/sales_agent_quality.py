"""Admin module — Sales Agent quality dashboard (S10).

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Lee ``sales_agent_workflow_metric`` (precomputado por
``weekly_sales_agent_quality_eval`` cron). Surfaces:

* KPIs por bucket (golden category): sample size, judge avg score,
  drift_alert si la última corrida bajó >5% week-over-week.
* Tabla histórica de las últimas semanas por bucket.
* Per-dimension breakdown del último run (5 dims sales).

Nunca invoca el LLM en render — la corrida real corre via cron Mondays
07:00 UTC + admin button (manual re-run on demand). Esto mantiene page
load <1s.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import streamlit as st
from sqlalchemy import text

from src.core.database import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


SENTINEL_TENANT_ID: str = "00000000-0000-0000-0000-000000000000"


def _fetch_bucket_kpis(db: Session) -> list[dict]:
    """Aggregate per-bucket KPIs across the last 60 days."""
    rows = (
        db.execute(
            text(
                """
                SELECT
                    bucket_id,
                    SUM(judge_sample_size) AS sampled,
                    AVG(NULLIF(judge_avg_score, 0)) AS avg_judge,
                    MAX(period_end) AS last_window_end,
                    MAX(period_start) AS last_window_start
                FROM sales_agent_workflow_metric
                WHERE period_start >= NOW() - INTERVAL '60 days'
                  AND tenant_id = :tenant_id
                GROUP BY bucket_id
                ORDER BY bucket_id
                """,
            ),
            {"tenant_id": SENTINEL_TENANT_ID},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_recent_metric_rows(db: Session, limit: int = 100) -> list[dict]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                    bucket_id,
                    period_start,
                    period_end,
                    judge_sample_size,
                    judge_avg_score,
                    extra_metadata
                FROM sales_agent_workflow_metric
                WHERE tenant_id = :tenant_id
                  AND period_start >= NOW() - INTERVAL '90 days'
                ORDER BY period_start DESC
                LIMIT :limit
                """,
            ),
            {"tenant_id": SENTINEL_TENANT_ID, "limit": limit},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_latest_run(db: Session) -> dict | None:
    row = (
        db.execute(
            text(
                """
                SELECT period_start, period_end, MAX(judge_avg_score) AS best,
                       MIN(judge_avg_score) AS worst,
                       AVG(judge_avg_score) AS overall_avg,
                       COUNT(*) AS buckets,
                       SUM(judge_sample_size) AS total_samples
                FROM sales_agent_workflow_metric
                WHERE tenant_id = :tenant_id
                GROUP BY period_start, period_end
                ORDER BY period_start DESC
                LIMIT 1
                """,
            ),
            {"tenant_id": SENTINEL_TENANT_ID},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def _fetch_drift_alerts(db: Session) -> list[dict]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                    bucket_id,
                    period_start,
                    judge_avg_score,
                    extra_metadata
                FROM sales_agent_workflow_metric
                WHERE tenant_id = :tenant_id
                  AND period_start >= NOW() - INTERVAL '60 days'
                  AND extra_metadata ? 'drift_alert'
                  AND (extra_metadata->>'drift_alert')::boolean = TRUE
                ORDER BY period_start DESC
                """,
            ),
            {"tenant_id": SENTINEL_TENANT_ID},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _render_overall(latest: dict | None) -> None:
    st.markdown("### Última corrida (cron weekly)")
    if latest is None:
        st.info(
            "Sin corridas todavía. ``weekly_sales_agent_quality_eval`` corre los"
            " lunes 07:00 UTC y poblará esta tabla. Para test local: stub mode"
            " emite 4.0 fijo; opt-in real LLM con ``RUN_LLM_JUDGE=1``.",
        )
        return
    cols = st.columns(4)
    avg = latest.get("overall_avg")
    cols[0].metric(
        "Avg score (1-5)",
        f"{float(avg):.2f}" if avg is not None else "—",
    )
    cols[1].metric("Buckets evaluados", int(latest.get("buckets") or 0))
    cols[2].metric("Total muestras", int(latest.get("total_samples") or 0))
    period = latest.get("period_start")
    cols[3].metric(
        "Período",
        f"{period:%Y-%m-%d}" if period is not None else "—",
    )


def _render_bucket_kpis(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### KPIs por categoría (60 días)")
    for row in rows:
        with st.container(border=True):
            cols = st.columns(4)
            cols[0].metric("Categoría", row["bucket_id"])
            cols[1].metric("Samples", int(row.get("sampled") or 0))
            score = row.get("avg_judge")
            cols[2].metric(
                "Judge avg (1-5)",
                f"{float(score):.2f}" if score is not None else "—",
            )
            last = row.get("last_window_end")
            cols[3].metric(
                "Último período",
                f"{last:%Y-%m-%d}" if last is not None else "—",
            )


def _render_drift_alerts(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### ⚠️ Drift alerts (60 días)")
    for row in rows:
        meta: dict[str, Any] = row.get("extra_metadata") or {}
        pct = meta.get("drift_pct")
        previous = meta.get("previous_avg_score")
        st.warning(
            f"**{row['bucket_id']}** — {row['period_start']:%Y-%m-%d}: "
            f"score actual {float(row['judge_avg_score']):.2f}, previo "
            f"{float(previous):.2f if previous else 0.0}"
            f" → drop "
            f"{(float(pct) * 100):.1f}%"
            if pct is not None
            else f"**{row['bucket_id']}** — {row['period_start']:%Y-%m-%d}: drift detectado.",
        )


def _render_recent_table(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Histórico semanal")
    st.dataframe(
        [
            {
                "Categoría": row["bucket_id"],
                "Período": f"{row['period_start']:%Y-%m-%d} → {row['period_end']:%Y-%m-%d}",
                "Sample": row["judge_sample_size"],
                "Judge avg": (
                    f"{float(row['judge_avg_score']):.2f}" if row.get("judge_avg_score") is not None else "—"
                ),
                "Drift": ("⚠️" if (row.get("extra_metadata") or {}).get("drift_alert") else ""),
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _render_per_dim_breakdown(rows: list[dict]) -> None:
    """Last-run per-dimension scores across categories."""
    if not rows:
        return
    # Agrupar last period_start.
    latest_period = max(row["period_start"] for row in rows)
    latest_rows = [row for row in rows if row["period_start"] == latest_period]
    per_dim_data: list[dict[str, Any]] = []
    for row in latest_rows:
        meta = row.get("extra_metadata") or {}
        per_dim = meta.get("per_dim_scores") or {}
        for dim, score in per_dim.items():
            per_dim_data.append(
                {
                    "Categoría": row["bucket_id"],
                    "Dimensión": dim,
                    "Score (1-5)": f"{float(score):.2f}" if score is not None else "—",
                },
            )
    if not per_dim_data:
        return
    st.markdown("### Per-dim breakdown — última corrida")
    st.dataframe(per_dim_data, hide_index=True, width="stretch")


def render_sales_agent_quality() -> None:
    """Render the Sales Agent quality dashboard (S10)."""
    st.title("🎯 Calidad del Sales Agent")
    st.caption(
        "Métricas LLM-judge precomputadas sobre los goldens canónicos. La"
        " evaluación corre los lunes 07:00 UTC. Stub default; opt-in real"
        " LLM con ``RUN_LLM_JUDGE=1``."
    )

    db = SessionLocal()
    try:
        latest = _fetch_latest_run(db)
        bucket_rows = _fetch_bucket_kpis(db)
        recent_rows = _fetch_recent_metric_rows(db)
        drift_rows = _fetch_drift_alerts(db)
    finally:
        db.close()

    _render_overall(latest)
    _render_drift_alerts(drift_rows)
    _render_bucket_kpis(bucket_rows)
    _render_per_dim_breakdown(recent_rows)
    _render_recent_table(recent_rows)
