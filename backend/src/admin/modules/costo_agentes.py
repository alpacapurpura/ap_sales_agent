"""Admin module — Costo Agentes (cross-agent dashboard).

S2 evolution of ``costo-copilot``: shows per-tenant cost across every
registered agent (copilot, sales_agent, …) in the Nicolify 25-25
billing cycle. Three tabs:

1. **Total** — KPI panel + table of every tenant active in the cycle,
   with a per-agent breakdown bar chart by tenant.
2. **Por agente** — pick an agent_kind via the shared selector, drill
   into per-model breakdown + 60-day timeseries.
3. **Top leads (sales_agent)** — sales-specific drilldown by lead_id.
   Hidden when the selected agent has no ``lead_id`` column.

Data source: ``CrossAgentCostAggregator`` over the per-agent
``*_llm_call`` tables. The cross-agent MV
``mv_daily_llm_cost_per_tenant_v2`` is the Postgres-side performance
booster the aggregator falls back to scanning when the MV is stale.

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
from luana_core_observability.registry import (
    agent_observability_registry,
    get_spec,
)
from luana_core_observability.reporting.billing_cycle_service import (
    BillingCycleService,
)
from luana_core_observability.reporting.cost_aggregator import (
    CostAggregator,
    CrossAgentCostAggregator,
)
from luana_core_platform.core.database import SessionLocal

from src.admin.modules._shared import (
    get_tenant_name,
    get_tenant_options,
    render_agent_kind_selector,
)

if TYPE_CHECKING:
    from luana_core_observability.reporting.cost_aggregator import (
        ModelCostRow,
        TenantCostRow,
    )


# ── Helpers ─────────────────────────────────────────────────────────────


def _format_money(value: Decimal | float | None, currency: str | None = "USD") -> str:
    if value is None:
        return "—"
    amount = Decimal(str(value))
    return f"{amount:,.4f} {currency or 'USD'}"


def _format_window(start: dt.date, end: dt.date) -> str:
    return f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}"


def _all_tenant_options() -> list[tuple[str, UUID]]:
    return [(t["name"], UUID(t["id"])) for t in get_tenant_options()]


def _select_anchor_tenant() -> UUID | None:
    tenants = _all_tenant_options()
    if not tenants:
        return None
    return tenants[0][1]


# ── Tab 1: Total cross-agent ────────────────────────────────────────────


def _render_total_tab(
    cross: CrossAgentCostAggregator,
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    st.markdown(f"### Ciclo activo · `{_format_window(cycle_start, cycle_end)}`")

    summary_by_agent = cross.tenants_summary_by_agent(start=cycle_start, end=cycle_end)

    # Aggregate KPIs cross-agent.
    all_rows: list[tuple[str, TenantCostRow]] = [(kind, row) for kind, rows in summary_by_agent.items() for row in rows]
    if not all_rows:
        st.info(
            "Sin datos de costo cross-agent en este ciclo. "
            "Cuando los agentes empiecen a escribir, esta tabla se llena automáticamente.",
        )
        return

    tenants_in_cycle = {row.tenant_id for _, row in all_rows}
    total_cost = sum((row.cost_usd for _, row in all_rows), Decimal(0))
    total_calls = sum(row.call_count for _, row in all_rows)
    total_turns = sum(row.turn_count for _, row in all_rows)

    cols = st.columns(5)
    cols[0].metric("Tenants activos", len(tenants_in_cycle))
    cols[1].metric("Costo total (USD)", f"${total_cost:.4f}")
    cols[2].metric("Llamadas LLM", total_calls)
    cols[3].metric("Turnos", total_turns)
    cols[4].metric(
        "Agentes activos",
        sum(1 for kind in summary_by_agent if summary_by_agent[kind]),
    )

    # Per-tenant breakdown table.
    table: list[dict[str, Any]] = []
    for tenant_id in tenants_in_cycle:
        per_kind: dict[str, Decimal] = {}
        for kind, rows in summary_by_agent.items():
            for row in rows:
                if row.tenant_id == tenant_id:
                    per_kind[kind] = row.cost_usd
        row_dict: dict[str, Any] = {
            "Tenant": get_tenant_name(tenant_id),
            "tenant_id": str(tenant_id),
            "Total USD": float(sum(per_kind.values(), Decimal(0))),
        }
        for kind in summary_by_agent:
            row_dict[f"{kind} USD"] = float(per_kind.get(kind, Decimal(0)))
        table.append(row_dict)

    df = pd.DataFrame(table).sort_values("Total USD", ascending=False)
    st.dataframe(df, hide_index=True, width="stretch")

    # Stacked bar chart: cost by tenant by agent.
    chart_long = []
    for r in table:
        for kind in summary_by_agent:
            chart_long.append(  # noqa: PERF401 — readability
                {
                    "Tenant": r["Tenant"],
                    "Agente": kind,
                    "Costo USD": r[f"{kind} USD"],
                },
            )
    chart_df = pd.DataFrame(chart_long)
    if not chart_df.empty and chart_df["Costo USD"].sum() > 0:
        bars = (
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X("Tenant:N", sort="-y"),
                y="Costo USD:Q",
                color="Agente:N",
                tooltip=["Tenant", "Agente", "Costo USD"],
            )
            .properties(title="Costo por tenant (apilado por agente)", height=320)
        )
        st.altair_chart(bars, use_container_width=True)


# ── Tab 2: Por agente ───────────────────────────────────────────────────


def _render_per_agent_tab(
    svc: BillingCycleService,
    cross: CrossAgentCostAggregator,
    tenants: list[tuple[str, UUID]],
    cycle_start: dt.date,
    cycle_end: dt.date,
) -> None:
    if not tenants:
        st.info("Aún no hay tenants registrados.")
        return

    agent_kind = render_agent_kind_selector(
        key="costo_agentes_agent_kind",
        default="sales_agent",
    )
    spec = get_spec(agent_kind)

    names = [name for name, _ in tenants]
    selected_idx = st.selectbox(
        "Tenant",
        options=list(range(len(tenants))),
        format_func=lambda i: names[i],
        key=f"costo_agentes_tenant_{agent_kind}",
    )
    tenant_id = tenants[selected_idx][1]

    agg = cross.aggregators_by_kind()[agent_kind]

    detail = agg.tenant_detail(tenant_id=tenant_id, start=cycle_start, end=cycle_end)
    prev_start, prev_end = svc.previous_cycle_window(tenant_id)
    prev_detail = agg.tenant_detail(tenant_id=tenant_id, start=prev_start, end=prev_end)

    delta_cost = float(detail.cost_usd - prev_detail.cost_usd)
    cols = st.columns(4)
    cols[0].metric(
        "Costo USD",
        f"${detail.cost_usd:.4f}",
        f"{delta_cost:+.4f} vs ciclo anterior",
    )
    cols[1].metric("Llamadas LLM", detail.call_count, delta=f"{detail.call_count - prev_detail.call_count:+}")
    cols[2].metric("Turnos", detail.turn_count, delta=f"{detail.turn_count - prev_detail.turn_count:+}")
    cols[3].metric("Errores", detail.error_count)

    st.markdown(f"##### Tabla por modelo · agente `{agent_kind}`")
    _render_models_table(detail.by_model)

    st.markdown("##### Series temporales (60 días)")
    _render_timeseries(agg, tenant_id=tenant_id, end=cycle_end)

    if spec.has_lead_id:
        st.markdown("##### Top leads del ciclo")
        _render_top_leads(agg, tenant_id=tenant_id, start=cycle_start, end=cycle_end)


def _render_models_table(models: list[ModelCostRow]) -> None:
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


def _render_timeseries(agg: CostAggregator, *, tenant_id: UUID, end: dt.date) -> None:
    window_start = end - dt.timedelta(days=60)
    series = agg.daily_series(tenant_id=tenant_id, start=window_start, end=end)
    if not series:
        st.info("Sin datos en los últimos 60 días.")
        return
    df = pd.DataFrame(
        [{"Día": p.day, "Costo USD": float(p.cost_usd), "Llamadas": p.call_count} for p in series],
    )
    line = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(x="Día:T", y="Costo USD:Q")
        .properties(title="Costo USD diario (últimos 60 días)", height=280)
    )
    st.altair_chart(line, use_container_width=True)


def _render_top_leads(
    agg: CostAggregator,
    *,
    tenant_id: UUID,
    start: dt.date,
    end: dt.date,
) -> None:
    rows = agg.top_leads_by_cost(tenant_id=tenant_id, start=start, end=end, limit=20)
    if not rows:
        st.info("Sin leads costosos en este ciclo.")
        return
    df = pd.DataFrame(
        [
            {
                "Lead": str(r.lead_id)[:8],
                "lead_id": str(r.lead_id),
                "Llamadas": r.call_count,
                "Turnos": r.turn_count,
                "Costo USD": float(r.cost_usd),
                "Última actividad": r.last_seen.strftime("%Y-%m-%d %H:%M") if r.last_seen else "—",
            }
            for r in rows
        ],
    )
    st.dataframe(df, hide_index=True, width="stretch")
    st.caption(
        "Para inspeccionar la conversación de un lead, copia el `lead_id` y abre `/auditoria`.",
    )


# ── Page entrypoint ─────────────────────────────────────────────────────


def render_costo_agentes() -> None:
    """Render the cross-agent cost dashboard."""
    st.title("📊 Costo Agentes")
    registered = ", ".join(spec.agent_kind for spec in agent_observability_registry())
    st.caption(
        "Costo agregado cross-agent por tenant en el ciclo de facturación 25 → 25. "
        f"Agentes registrados: `{registered}`. "
        "Datos de cada `*_llm_call` (snapshot de pricing).",
    )

    db = SessionLocal()
    try:
        svc = BillingCycleService(db)
        cross = CrossAgentCostAggregator(db)

        anchor = _select_anchor_tenant()
        if anchor is None:
            st.info("Aún no hay tenants registrados.")
            return

        if "costo_agentes_pivot_date" not in st.session_state:
            st.session_state.costo_agentes_pivot_date = dt.datetime.now(tz=dt.UTC).date()
        pivot: dt.date = st.session_state.costo_agentes_pivot_date

        nav = st.columns([1, 5, 1])
        if nav[0].button("◀ Anterior", key="costo_agentes_prev"):
            st.session_state.costo_agentes_pivot_date = pivot - dt.timedelta(days=30)
            st.rerun()
        nav[1].markdown(
            f"<div style='text-align:center;font-size:1.05rem'>"
            f"Ciclo del <code>{pivot.strftime('%Y-%m-%d')}</code>"
            "</div>",
            unsafe_allow_html=True,
        )
        if nav[2].button("Siguiente ▶", key="costo_agentes_next"):
            st.session_state.costo_agentes_pivot_date = pivot + dt.timedelta(days=30)
            st.rerun()

        cycle_start, cycle_end = svc.compute_window(anchor, pivot)
        tenants = _all_tenant_options()

        tabs = st.tabs(["Total", "Por agente"])
        with tabs[0]:
            _render_total_tab(cross, cycle_start, cycle_end)
        with tabs[1]:
            _render_per_agent_tab(svc, cross, tenants, cycle_start, cycle_end)
    finally:
        db.close()


__all__ = ["render_costo_agentes"]
