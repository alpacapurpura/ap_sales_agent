"""Admin module — Costo Copilot dashboard.

Surface the per-tenant LLM cost in the Nicolify 25-25 billing cycle.
Three views, switchable via tabs:

1. **Comando Central** — table of every tenant active in the cycle, KPIs
   on top, filter + CSV export below.
2. **Detalle por tenant** — pick a tenant; see series temporales, model
   breakdown and KPIs vs the previous cycle.
3. **Top conversaciones** — drill-down to the 20 most expensive
   conversations of the active cycle.

User-facing copy: español neutro LatAm (tuteo, sin voseo) per
``.claude/rules/spanish-text.md``.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

import altair as alt
import pandas as pd
import streamlit as st

from src.admin.modules._shared import (
    get_tenant_name,
    get_tenant_options,
)
from src.core.database import SessionLocal
from src.modules.copilot.observability.reporting.cost_aggregator import (
    CostAggregator,
)
from src.shared.agent_observability.reporting.billing_cycle_service import (
    BillingCycleService,
)

if TYPE_CHECKING:
    from src.modules.copilot.observability.reporting.cost_aggregator import (
        ModelCostRow,
        TenantCostRow,
        TenantDetailRow,
    )


# ── Helpers ─────────────────────────────────────────────────────────────


def _format_money(value: Decimal | float | None, currency: str | None = "USD") -> str:
    if value is None:
        return "—"
    amount = Decimal(str(value))
    return f"{amount:,.4f} {currency or 'USD'}"


def _format_window(start: dt.date, end: dt.date) -> str:
    return f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}"


def _shift_window(
    svc: BillingCycleService,
    tenant_id: UUID,
    pivot: dt.date,
    delta_cycles: int,
) -> tuple[dt.date, dt.date]:
    """Return the window ``delta_cycles`` cycles away from ``pivot`` for ``tenant_id``."""
    if delta_cycles == 0:
        return svc.compute_window(tenant_id, pivot)

    # Move the pivot forward/backward 30 days at a time and recompute.
    step = 30 * delta_cycles
    target = pivot + dt.timedelta(days=step)
    return svc.compute_window(tenant_id, target)


def _all_tenant_options() -> list[tuple[str, UUID]]:
    return [(t["name"], UUID(t["id"])) for t in get_tenant_options()]


def _select_anchor_tenant() -> UUID | None:
    """Pick the first active tenant as the default cycle anchor.

    The cycle window is per-tenant; this seed lets the dashboard render
    even before a user picks a specific tenant in the detail view.
    """
    tenants = _all_tenant_options()
    if not tenants:
        return None
    return tenants[0][1]


# ── Vista 1: Comando Central ────────────────────────────────────────────


def _render_command_center(
    svc: BillingCycleService,
    agg: CostAggregator,
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    st.markdown(f"### Ciclo activo · `{_format_window(cycle_start, cycle_end)}`")

    rows = agg.tenants_summary(start=cycle_start, end=cycle_end)
    if not rows:
        st.info(
            "Sin datos de costo en este ciclo. Cuando los tenants empiecen a usar el copilot, "
            "esta tabla se llena automáticamente.",
        )
        return

    total_cost = sum((r.cost_usd for r in rows), Decimal(0))
    total_calls = sum(r.call_count for r in rows)
    total_turns = sum(r.turn_count for r in rows)
    total_convs = sum(r.conversation_count for r in rows)
    avg_cost_per_turn = total_cost / total_turns if total_turns else Decimal(0)
    total_errors = sum(r.error_count for r in rows)

    cols = st.columns(6)
    cols[0].metric("Tenants activos", len(rows))
    cols[1].metric("Costo total (USD)", f"${total_cost:.4f}")
    cols[2].metric("Conversaciones", total_convs)
    cols[3].metric("Turnos", total_turns)
    cols[4].metric("Llamadas LLM", total_calls)
    cols[5].metric("Costo prom. / turno", f"${avg_cost_per_turn:.4f}")

    if total_errors:
        st.warning(f"⚠ Se registraron {total_errors} llamadas con error en el ciclo.")

    # Table
    df = _tenant_rows_to_df(rows)
    st.dataframe(df, hide_index=True, width="stretch")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Exportar CSV (ciclo actual)",
        data=csv_bytes,
        file_name=f"costo-copilot_{cycle_start.isoformat()}_{cycle_end.isoformat()}.csv",
        mime="text/csv",
        key="costo_copilot_csv",
    )


def _tenant_rows_to_df(rows: list[TenantCostRow]) -> pd.DataFrame:
    table: list[dict[str, Any]] = [
        {
            "Tenant": get_tenant_name(r.tenant_id),
            "tenant_id": str(r.tenant_id),
            "Conversaciones": r.conversation_count,
            "Turnos": r.turn_count,
            "Llamadas LLM": r.call_count,
            "Costo USD": float(r.cost_usd),
            "Costo local": float(r.cost_tenant_currency or 0),
            "Moneda": r.tenant_currency or "USD",
            "Errores": r.error_count,
        }
        for r in rows
    ]
    return pd.DataFrame(table)


# ── Vista 2: Detalle por tenant ─────────────────────────────────────────


def _render_tenant_detail(
    svc: BillingCycleService,
    agg: CostAggregator,
    tenants: list[tuple[str, UUID]],
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    if not tenants:
        st.info("Aún no hay tenants registrados.")
        return

    names = [name for name, _ in tenants]
    selected_idx = st.selectbox(
        "Tenant",
        options=list(range(len(tenants))),
        format_func=lambda i: names[i],
        key="costo_detail_tenant",
    )
    tenant_id = tenants[selected_idx][1]

    detail = agg.tenant_detail(tenant_id=tenant_id, start=cycle_start, end=cycle_end)
    prev_start, prev_end = svc.previous_cycle_window(tenant_id)
    prev_detail = agg.tenant_detail(tenant_id=tenant_id, start=prev_start, end=prev_end)

    tabs = st.tabs(["Resumen", "Series temporales", "Modelos"])

    with tabs[0]:
        _render_detail_summary(detail, prev_detail, cycle_start, cycle_end, prev_start, prev_end)

    with tabs[1]:
        _render_detail_timeseries(agg, tenant_id, cycle_start, cycle_end)

    with tabs[2]:
        _render_detail_models(detail.by_model)


def _render_detail_summary(
    current: TenantDetailRow,
    previous: TenantDetailRow,
    cycle_start: dt.date,
    cycle_end: dt.date,
    prev_start: dt.date,
    prev_end: dt.date,
) -> None:
    st.markdown(
        f"**Ciclo actual:** `{_format_window(cycle_start, cycle_end)}` · "
        f"**Anterior:** `{_format_window(prev_start, prev_end)}`",
    )

    delta_cost = float(current.cost_usd - previous.cost_usd)
    delta_calls = current.call_count - previous.call_count

    cols = st.columns(4)
    cols[0].metric(
        "Costo USD",
        f"${current.cost_usd:.4f}",
        f"{delta_cost:+.4f} vs ciclo anterior",
    )
    cols[1].metric(
        "Conversaciones",
        current.conversation_count,
        delta=f"{current.conversation_count - previous.conversation_count:+}",
    )
    cols[2].metric(
        "Turnos",
        current.turn_count,
        delta=f"{current.turn_count - previous.turn_count:+}",
    )
    cols[3].metric(
        "Llamadas LLM",
        current.call_count,
        delta=f"{delta_calls:+}",
    )

    if current.error_count:
        st.warning(f"⚠ {current.error_count} llamadas con error en el ciclo activo.")


def _render_detail_timeseries(
    agg: CostAggregator,
    tenant_id: UUID,
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    # 60-day window ending at cycle_end gives context beyond the current cycle.
    window_start = cycle_end - dt.timedelta(days=60)
    series = agg.daily_series(tenant_id=tenant_id, start=window_start, end=cycle_end)
    if not series:
        st.info("Sin datos en los últimos 60 días.")
        return

    df = pd.DataFrame(
        [
            {
                "Día": pt.day,
                "Costo USD": float(pt.cost_usd),
                "Llamadas": pt.call_count,
            }
            for pt in series
        ],
    )

    line = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(x="Día:T", y="Costo USD:Q")
        .properties(title="Costo USD diario (últimos 60 días)", height=320)
    )
    st.altair_chart(line, use_container_width=True)

    st.markdown("##### Llamadas LLM por día")
    bars = alt.Chart(df).mark_bar().encode(x="Día:T", y="Llamadas:Q").properties(height=240)
    st.altair_chart(bars, use_container_width=True)


def _render_detail_models(models: list[ModelCostRow]) -> None:
    if not models:
        st.info("Sin llamadas LLM en este ciclo.")
        return

    df = pd.DataFrame(
        [
            {
                "Modelo": m.model,
                "Proveedor": m.provider,
                "Rol": m.role,
                "Llamadas": m.call_count,
                "Costo USD": float(m.cost_usd),
                "Tokens entrada (prom)": m.avg_input_tokens,
                "Tokens salida (prom)": m.avg_output_tokens,
            }
            for m in models
        ],
    )
    st.dataframe(df, hide_index=True, width="stretch")

    pie_df = df[df["Costo USD"] > 0]
    if not pie_df.empty:
        pie = (
            alt.Chart(pie_df)
            .mark_arc(outerRadius=120)
            .encode(
                theta=alt.Theta(field="Costo USD", type="quantitative"),
                color=alt.Color(field="Modelo", type="nominal"),
                tooltip=["Modelo", "Costo USD"],
            )
            .properties(title="Distribución del costo por modelo", height=320)
        )
        st.altair_chart(pie, use_container_width=True)


# ── Vista 3: Top conversaciones ─────────────────────────────────────────


def _render_top_conversations(
    agg: CostAggregator,
    tenants: list[tuple[str, UUID]],
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    if not tenants:
        st.info("Aún no hay tenants registrados.")
        return

    names = [name for name, _ in tenants]
    selected_idx = st.selectbox(
        "Tenant",
        options=list(range(len(tenants))),
        format_func=lambda i: names[i],
        key="costo_top_conv_tenant",
    )
    tenant_id = tenants[selected_idx][1]

    rows = agg.top_conversations_by_cost(
        tenant_id=tenant_id,
        start=cycle_start,
        end=cycle_end,
        limit=20,
    )
    if not rows:
        st.info("Sin conversaciones costosas en este ciclo.")
        return

    df = pd.DataFrame(
        [
            {
                "Conversación": str(r.conversation_id)[:8],
                "conversation_id": str(r.conversation_id),
                "Llamadas": r.call_count,
                "Turnos": r.turn_count,
                "Costo USD": float(r.cost_usd),
                "Última actividad": r.last_seen.strftime("%Y-%m-%d %H:%M") if r.last_seen else "—",
            }
            for r in rows
        ],
    )
    st.dataframe(df, hide_index=True, width="stretch")
    st.caption("Para inspeccionar el detalle de una conversación, copia el `conversation_id` y abre `/trazas`.")


# ── Page entrypoint ─────────────────────────────────────────────────────


def render_costo_copilot() -> None:
    """Render the costo-copilot dashboard."""
    st.title("💰 Costo Copilot")
    st.caption(
        "Costo agregado por tenant en el ciclo de facturación 25 → 25. "
        "Datos de ``copilot_llm_call`` (snapshot de pricing) y "
        "``tenant_billing_config`` (anclaje del ciclo).",
    )

    db = SessionLocal()
    try:
        svc = BillingCycleService(db)
        agg = CostAggregator(db)

        anchor = _select_anchor_tenant()
        if anchor is None:
            st.info("Aún no hay tenants registrados.")
            return

        # Cycle navigation pivot stored in session_state.
        if "costo_pivot_date" not in st.session_state:
            st.session_state.costo_pivot_date = dt.datetime.now(tz=dt.UTC).date()
        pivot: dt.date = st.session_state.costo_pivot_date

        nav = st.columns([1, 5, 1])
        if nav[0].button("◀ Anterior", key="costo_prev"):
            st.session_state.costo_pivot_date = pivot - dt.timedelta(days=30)
            st.rerun()
        nav[1].markdown(
            f"<div style='text-align:center;font-size:1.05rem'>"
            f"Ciclo del <code>{pivot.strftime('%Y-%m-%d')}</code>"
            "</div>",
            unsafe_allow_html=True,
        )
        if nav[2].button("Siguiente ▶", key="costo_next"):
            st.session_state.costo_pivot_date = pivot + dt.timedelta(days=30)
            st.rerun()

        cycle_start, cycle_end = svc.compute_window(anchor, pivot)
        tenants = _all_tenant_options()

        view_tabs = st.tabs(["Comando Central", "Detalle por tenant", "Top conversaciones"])
        with view_tabs[0]:
            _render_command_center(svc, agg, cycle_start, cycle_end)
        with view_tabs[1]:
            _render_tenant_detail(svc, agg, tenants, cycle_start, cycle_end)
        with view_tabs[2]:
            _render_top_conversations(agg, tenants, cycle_start, cycle_end)

    finally:
        db.close()


__all__ = ["render_costo_copilot"]
