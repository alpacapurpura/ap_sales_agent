"""Admin module — Copilot quality dashboard (F9 §4.3).

# [COPILOT-LLM-JUDGE-F9]

Reads ``copilot_workflow_metric`` (precomputed by the weekly ARQ task)
and surfaces:

* KPIs per workflow_id: started count, judge avg score, sample size,
  avg turns to completion.
* Recent metric rows for spot-checking regressions.
* Trace event distribution (errors / node_enter / card_emitted) over the
  same window — pulled from ``copilot_trace_event``.

Never invokes the LLM at render time — page load stays <1s. The judge runs
asynchronously via the cron + admin button (manual re-run on demand).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import streamlit as st
from sqlalchemy import text

from src.admin.modules._shared import render_tenant_selector
from src.core.database import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _fetch_workflow_kpis(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
) -> list[dict]:
    """Aggregate per-workflow KPIs across all stored periods."""
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    workflow_id,
                    SUM(started_count) AS started,
                    SUM(judge_sample_size) AS sampled,
                    AVG(NULLIF(judge_avg_score, 0)) AS avg_judge,
                    AVG(avg_turns_to_completion) AS avg_turns,
                    MAX(period_end) AS last_window_end
                FROM copilot_workflow_metric
                WHERE period_start >= NOW() - INTERVAL '60 days'
                {tenant_filter_sql}
                GROUP BY workflow_id
                ORDER BY started DESC
                """,
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_recent_metric_rows(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
    limit: int = 100,
) -> list[dict]:
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    workflow_id,
                    period_start,
                    period_end,
                    started_count,
                    judge_sample_size,
                    judge_avg_score,
                    avg_turns_to_completion
                FROM copilot_workflow_metric
                WHERE period_start >= NOW() - INTERVAL '60 days'
                {tenant_filter_sql}
                ORDER BY period_start DESC
                LIMIT :limit
                """,
            ),
            {**params, "limit": limit},
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _fetch_trace_event_breakdown(
    db: Session,
    tenant_filter_sql: str,
    params: dict[str, Any],
) -> list[dict]:
    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    event_type,
                    COUNT(*) AS n,
                    AVG(duration_ms) AS avg_duration_ms
                FROM copilot_trace_event
                WHERE created_at >= NOW() - INTERVAL '7 days'
                  AND event_type IN ('node_enter', 'node_exit', 'tool_call', 'card_emitted', 'error')
                {tenant_filter_sql}
                GROUP BY event_type
                ORDER BY n DESC
                """,
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(r) for r in rows]


def _render_kpi_cards(rows: list[dict]) -> None:
    if not rows:
        st.info(
            "Sin métricas de calidad todavía. La tarea semanal "
            "``weekly_copilot_quality_eval`` corre los lunes 05:00 UTC y "
            "puebla esta tabla."
        )
        return
    for row in rows:
        with st.container(border=True):
            cols = st.columns(4)
            cols[0].metric("Workflow", row["workflow_id"])
            cols[1].metric("Conversaciones (sample)", int(row.get("sampled") or 0))
            score = row.get("avg_judge")
            cols[2].metric(
                "Judge avg (1-5)",
                f"{float(score):.2f}" if score is not None else "—",
            )
            avg_turns = row.get("avg_turns")
            cols[3].metric(
                "Turnos promedio",
                f"{float(avg_turns):.1f}" if avg_turns is not None else "—",
            )


def _render_recent_table(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Últimas métricas semanales")
    st.dataframe(
        [
            {
                "Workflow": row["workflow_id"],
                "Periodo": f"{row['period_start']:%Y-%m-%d} → {row['period_end']:%Y-%m-%d}",
                "Sample": row["judge_sample_size"],
                "Judge avg": (
                    f"{float(row['judge_avg_score']):.2f}" if row.get("judge_avg_score") is not None else "—"
                ),
                "Turnos avg": (
                    f"{float(row['avg_turns_to_completion']):.1f}"
                    if row.get("avg_turns_to_completion") is not None
                    else "—"
                ),
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def _fetch_latest_rag_eval(db: Session) -> dict | None:
    """Return the most recent ``_rag_eval`` row (tenant-agnostic).

    F11.5: weekly RAG eval persists one aggregate row per Monday under
    sentinel tenant ``00000000-0000-0000-0000-000000000000`` + workflow
    ``_rag_eval``. The admin tab reads the precomputed row — never invokes
    the KB at render time.
    """
    row = (
        db.execute(
            text(
                """
                SELECT
                    period_start,
                    period_end,
                    started_count,
                    abandoned_count,
                    judge_sample_size,
                    judge_avg_score,
                    extra_metadata
                FROM copilot_workflow_metric
                WHERE workflow_id = '_rag_eval'
                ORDER BY period_start DESC
                LIMIT 1
                """,
            ),
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def _render_rag_eval_section(rag_row: dict | None) -> None:
    """Render the F11.5 RAG retrieval block (latest weekly eval)."""
    st.markdown("---")
    st.markdown("### 🔎 RAG retrieval (curated marketing KB)")
    st.caption(
        "Resultado del último ``weekly_copilot_rag_eval`` — corre los lunes "
        "06:00 UTC. Mide recall por golden, latencia y judge multi-dim sobre "
        "los frameworks curados (StoryBrand, Hormozi, Cialdini, AIDA, ...)."
    )
    if rag_row is None:
        st.info(
            "Sin runs todavía. La tarea ``weekly_copilot_rag_eval`` corre los lunes 06:00 UTC y poblará esta sección."
        )
        return

    meta = rag_row.get("extra_metadata") or {}
    cols = st.columns(4)
    recall = meta.get("retrieval_recall_avg")
    cols[0].metric(
        "Recall promedio",
        f"{float(recall):.2f}" if recall is not None else "—",
    )
    cols[1].metric(
        "Goldens evaluados",
        int(rag_row.get("started_count") or 0),
    )
    judge_avg = rag_row.get("judge_avg_score")
    cols[2].metric(
        "Judge avg (1-5)",
        f"{float(judge_avg):.2f}" if judge_avg is not None else "—",
    )
    latency = meta.get("retrieval_latency_ms_avg")
    cols[3].metric(
        "Latencia avg (ms)",
        int(latency) if latency is not None else "—",
    )

    failed = meta.get("failed_golden_ids") or []
    if failed:
        st.warning(f"Goldens fallidos esta corrida: {', '.join(failed)}")

    judge_dims = meta.get("judge_dimensions") or {}
    if judge_dims:
        st.markdown("#### Dimensiones del judge")
        st.dataframe(
            [
                {
                    "Dimensión": dim,
                    "Score (1-5)": f"{float(score):.2f}" if score is not None else "—",
                }
                for dim, score in judge_dims.items()
            ],
            hide_index=True,
            width="stretch",
        )

    per_golden = meta.get("per_golden_recall") or {}
    if per_golden:
        st.markdown("#### Recall por golden")
        st.dataframe(
            [{"Golden": gid, "Recall": float(recall)} for gid, recall in per_golden.items()],
            hide_index=True,
            width="stretch",
        )

    citations = meta.get("kb_citations") or []
    if citations:
        st.caption(
            f"Fuentes citadas únicas en esta corrida: {len(citations)} — "
            f"{', '.join(citations[:8])}" + (" …" if len(citations) > 8 else "")
        )


def _render_trace_breakdown(rows: list[dict]) -> None:
    if not rows:
        return
    st.markdown("### Eventos de traza (últimos 7 días)")
    st.dataframe(
        [
            {
                "Tipo": row["event_type"],
                "N": row["n"],
                "Duración promedio (ms)": (
                    int(row["avg_duration_ms"]) if row.get("avg_duration_ms") is not None else None
                ),
            }
            for row in rows
        ],
        hide_index=True,
        width="stretch",
    )


def render_copilot_quality() -> None:
    """Render the Copilot quality dashboard (F9 §4.3)."""
    st.title("🎓 Calidad del Copilot")
    st.caption(
        "Métricas LLM-judge precomputadas por workflow y trazas de los últimos"
        " 7 días. La evaluación corre los lunes 05:00 UTC."
    )

    tenant_id = render_tenant_selector("copilot_quality_tenant", allow_all=True)
    tenant_filter_sql = "AND tenant_id = :tenant_id" if tenant_id is not None else ""
    params: dict[str, Any] = {"tenant_id": str(tenant_id)} if tenant_id is not None else {}

    db = SessionLocal()
    try:
        kpi_rows = _fetch_workflow_kpis(db, tenant_filter_sql, params)
        recent_rows = _fetch_recent_metric_rows(db, tenant_filter_sql, params)
        trace_rows = _fetch_trace_event_breakdown(db, tenant_filter_sql, params)
        rag_row = _fetch_latest_rag_eval(db)
    finally:
        db.close()

    st.markdown("### Indicadores por workflow (últimos 60 días)")
    _render_kpi_cards(kpi_rows)
    _render_recent_table(recent_rows)
    _render_trace_breakdown(trace_rows)
    _render_rag_eval_section(rag_row)
