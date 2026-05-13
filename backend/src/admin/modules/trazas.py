"""Streamlit admin: Trazas Copilot — turn-by-turn trace explorer.

Reads from ``copilot_trace_event`` (populated by
``application/observability/trace_recorder``) and reconstructs a
per-conversation timeline of LLM calls, tool calls, card emissions and
errors. The UI is the operator's first stop when a copilot response
surprises the user: expand a turn, inspect each event, see the exact
args/outputs that caused the observed behavior.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st
from luana_core_platform.core.database import SessionLocal
from sqlalchemy import text

from src.admin.modules._shared import (
    get_tenant_name,
    render_tenant_selector,
)

if TYPE_CHECKING:
    from uuid import UUID

# ── Formatting helpers ───────────────────────────────────────────────────

_STATUS_ICON: dict[str, str] = {
    "ok": "✅",
    "error": "❌",
    "cancelled": "🟡",
}

_EVENT_ICON: dict[str, str] = {
    "turn_start": "▶️",
    "turn_end": "⏹️",
    "llm_call": "🧠",
    "tool_call": "🔧",
    "card_emitted": "🪪",
    "node_enter": "➡️",
    "node_exit": "⬅️",
    "error": "💥",
}


def _format_duration(ms: int | None) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.2f}s"


def _format_payload(payload: object) -> str:
    try:
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(payload)


# ── Data fetchers ────────────────────────────────────────────────────────


def _fetch_recent_turns(
    tenant_id: UUID | None,
    limit: int,
    status_filter: str,
) -> list[dict]:
    """Return recent turn_start events, optionally filtered to errors only.

    One row per turn. Joins on a ``turn_end`` sibling (if present) to show
    total duration; when there's no end row the turn is still in flight or
    crashed mid-stream.
    """
    where_clauses = ["starts.event_type = 'turn_start'"]
    params: dict[str, object] = {"limit": limit}
    if tenant_id is not None:
        where_clauses.append("starts.tenant_id = :tenant_id")
        params["tenant_id"] = str(tenant_id)
    if status_filter == "con_error":
        where_clauses.append(
            "EXISTS (SELECT 1 FROM copilot_trace_event e2 WHERE e2.turn_id = starts.turn_id AND e2.status = 'error')"
        )
    where_sql = " AND ".join(where_clauses)

    sql = text(
        f"""
        SELECT
            starts.turn_id,
            starts.conversation_id,
            starts.tenant_id,
            starts.user_id,
            starts.data,
            starts.created_at,
            ends.duration_ms AS total_duration_ms,
            (SELECT COUNT(*) FROM copilot_trace_event e
                WHERE e.turn_id = starts.turn_id AND e.event_type = 'tool_call') AS tool_calls,
            (SELECT COUNT(*) FROM copilot_trace_event e
                WHERE e.turn_id = starts.turn_id AND e.event_type = 'llm_call') AS llm_calls,
            (SELECT COUNT(*) FROM copilot_trace_event e
                WHERE e.turn_id = starts.turn_id AND e.status = 'error') AS error_count
        FROM copilot_trace_event starts
        LEFT JOIN copilot_trace_event ends
            ON ends.turn_id = starts.turn_id AND ends.event_type = 'turn_end'
        WHERE {where_sql}
        ORDER BY starts.created_at DESC
        LIMIT :limit
        """
    )

    db = SessionLocal()
    try:
        rows = db.execute(sql, params).mappings().all()
        return [dict(r) for r in rows]
    finally:
        db.close()


def _fetch_turn_timeline(turn_id: UUID) -> list[dict]:
    """Return every event for ``turn_id`` in creation order.

    Joins ``copilot_llm_call`` by ``span_id`` so rows of
    ``event_type='llm_call'`` carry the typed cost columns from the
    event-sourced LLM-call log (post Phase 2 atomic switch). Other
    event rows simply have ``cost_usd = NULL``.
    """
    sql = text(
        """
        SELECT
            e.id, e.event_type, e.name, e.status, e.duration_ms,
            e.data, e.span_id, e.parent_span_id, e.created_at,
            c.cost_usd, c.input_tokens, c.output_tokens,
            c.cached_read_tokens, c.model_responded, c.provider
        FROM copilot_trace_event e
        LEFT JOIN copilot_llm_call c ON c.span_id = e.span_id
        WHERE e.turn_id = :turn_id
        ORDER BY e.created_at ASC
        """
    )
    db = SessionLocal()
    try:
        rows = db.execute(sql, {"turn_id": str(turn_id)}).mappings().all()
        return [dict(r) for r in rows]
    finally:
        db.close()


# ── Page renderer ────────────────────────────────────────────────────────


def render_trazas_page() -> None:
    """Render the per-turn trace explorer page."""
    st.title("🔬 Trazas Copilot")
    st.caption(
        "Reconstrucción turn-a-turn de cada interacción con el copilot. "
        "Cada turn tiene un envelope (turn_start/turn_end) y una timeline de "
        "llamadas al LLM, tool calls y cards emitidas. Usa esto cuando el "
        "copilot responde algo inesperado: abre el turn, inspecciona el evento."
    )

    col_tenant, col_status, col_limit = st.columns([3, 2, 2])
    with col_tenant:
        selected_tenant = render_tenant_selector(key="traces_tenant", allow_all=True)
    with col_status:
        status_filter = st.selectbox(
            "Estado",
            ["todos", "con_error"],
            key="traces_status",
        )
    with col_limit:
        limit = st.slider("Límite de turns", 5, 100, 20, key="traces_limit")

    turns = _fetch_recent_turns(selected_tenant, limit, status_filter)

    if not turns:
        st.info("Sin trazas aún. Envía un mensaje al copilot y refresca — cada turn deja rastro automáticamente.")
        return

    # Summary KPIs
    total_turns = len(turns)
    with_errors = sum(1 for t in turns if (t.get("error_count") or 0) > 0)
    avg_duration = sum((t.get("total_duration_ms") or 0) for t in turns) / total_turns if total_turns else 0
    total_tools = sum((t.get("tool_calls") or 0) for t in turns)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Turns", total_turns)
    c2.metric("Con error", with_errors)
    c3.metric("Duración promedio", _format_duration(int(avg_duration)))
    c4.metric("Tool calls", total_tools)

    st.divider()

    for turn in turns:
        _render_turn_card(turn)


def _render_turn_card(turn: dict) -> None:
    """Render one collapsible card per turn with its timeline."""
    turn_id = turn["turn_id"]
    conv_id = turn["conversation_id"]
    tenant = get_tenant_name(turn["tenant_id"])
    data = turn.get("data") or {}
    message_preview = data.get("message_preview", "(sin mensaje)")
    errors = turn.get("error_count") or 0
    status_icon = "💥" if errors else "✅"
    duration = _format_duration(turn.get("total_duration_ms"))
    created = turn["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    header = (
        f"{status_icon} **{created}** · `{tenant}` · {duration} · "
        f"{turn.get('tool_calls') or 0} tools · {turn.get('llm_calls') or 0} LLM · "
        f"msg: _{message_preview[:120]}_"
    )

    with st.expander(header, expanded=False):
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"**turn_id**: `{turn_id}`  \n"
                f"**conversation_id**: `{conv_id}`  \n"
                f"**user_id**: `{turn.get('user_id', '—')}`"
            )
        with meta_col2:
            route = data.get("current_route") or "—"
            guided = data.get("guided_mode", False)
            attach = data.get("attachment_count", 0)
            st.markdown(f"**ruta**: `{route}`  \n**guided**: {'sí' if guided else 'no'}  \n**adjuntos**: {attach}")

        timeline = _fetch_turn_timeline(turn_id)
        if not timeline:
            st.warning("Sin eventos registrados para este turn_id.")
            return

        _render_timeline_table(timeline)
        st.divider()
        _render_event_details(timeline)


def _render_timeline_table(events: list[dict]) -> None:
    """Compact table row-per-event for quick scan."""
    rows = [
        {
            "#": idx + 1,
            "evento": f"{_EVENT_ICON.get(e['event_type'], '·')} {e['event_type']}",
            "nombre": e.get("name") or "—",
            "estado": f"{_STATUS_ICON.get(e['status'], '·')} {e['status']}",
            "duración": _format_duration(e.get("duration_ms")),
            "costo USD": (f"${float(e['cost_usd']):.6f}" if e.get("cost_usd") is not None else "—"),
            "ts": e["created_at"].strftime("%H:%M:%S.%f")[:-3],
        }
        for idx, e in enumerate(events)
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
    )


def _render_event_details(events: list[dict]) -> None:
    """Per-event expander with the full JSONB payload — where the real debugging happens."""
    st.markdown("##### Detalle por evento")
    for idx, evt in enumerate(events):
        icon = _EVENT_ICON.get(evt["event_type"], "·")
        status_icon = _STATUS_ICON.get(evt["status"], "·")
        label = f"{idx + 1}. {icon} {evt['event_type']} · {evt.get('name') or '—'} · {status_icon}"
        with st.expander(label, expanded=evt["status"] == "error"):
            payload = evt.get("data") or {}
            st.caption(f"span_id: `{evt['span_id']}` · parent: `{evt.get('parent_span_id') or '—'}`")
            st.code(_format_payload(payload), language="json")
