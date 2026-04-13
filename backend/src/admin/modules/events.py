"""Streamlit admin: Inteligencia Copilot — cross-tenant event analytics and insights."""

import pandas as pd
import streamlit as st


def render_events_page():
    st.title("🧠 Inteligencia Copilot")

    from src.admin.modules._shared import (
        TOOLTIPS,
        get_tenant_name,
        pct_flag,
        render_tenant_selector,
    )
    from src.core.database import SessionLocal
    from src.modules.copilot.infrastructure.repositories.event_repository import (
        CopilotEventRepository,
    )

    # ── Persistent filters ──
    col_tenant, col_period = st.columns([3, 2])
    with col_tenant:
        selected_tenant = render_tenant_selector(key="intel_tenant", allow_all=True)
    with col_period:
        days = st.slider("Periodo (dias)", 7, 90, 30, key="intel_days")

    is_global = selected_tenant is None

    st.divider()

    # Tabs
    tab_dash, tab_friction, tab_procs, tab_engage, tab_explore = st.tabs(
        [
            "📈 Dashboard",
            "🔥 Friccion",
            "📋 Procedimientos",
            "💡 Engagement",
            "🔍 Explorar",
        ],
    )

    # ── Tab 1: Dashboard ──
    with tab_dash:
        try:
            db = SessionLocal()
            try:
                repo = CopilotEventRepository(db)

                if is_global:
                    summary = repo.get_global_summary(days=days)
                    engagement = repo.get_global_engagement(days=days)
                else:
                    summary = repo.get_tenant_summary(selected_tenant, days=days)
                    engagement = repo.get_engagement_metrics(selected_tenant, days=days)

                total_events = sum(summary.values())

                # Acceptance rate
                accepted = summary.get("proposal_accepted", 0)
                rejected = summary.get("proposal_rejected", 0)
                total_p = accepted + rejected
                acceptance_rate = (
                    f"{round(accepted / total_p * 100)}%" if total_p else "N/A"
                )

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Eventos", total_events, help=TOOLTIPS["total_events"])
                c2.metric(
                    "Usuarios Activos",
                    engagement["active_users"],
                    help="Usuarios unicos con mensajes en el periodo",
                )
                c3.metric(
                    "Msgs/User Avg",
                    engagement["messages_per_user_avg"],
                    help=TOOLTIPS["msgs_per_user"],
                )
                c4.metric(
                    "Aceptacion Propuestas",
                    acceptance_rate,
                    help=TOOLTIPS["proposal_acceptance"],
                )

                # Pie chart: event type distribution
                if summary:
                    st.subheader("Distribucion de Eventos")
                    df_events = pd.DataFrame(
                        [
                            {"Tipo": k, "Cantidad": v}
                            for k, v in sorted(summary.items(), key=lambda x: -x[1])
                        ],
                    )
                    st.bar_chart(df_events.set_index("Tipo"))
                    st.dataframe(df_events, use_container_width=True, hide_index=True)

                # Top tenants by volume (only in global mode)
                if is_global:
                    st.subheader("Top Tenants por Volumen")
                    by_tenant = repo.get_events_grouped_by_tenant(days=days)
                    if by_tenant:
                        tenant_rows = [
                            {
                                "Tenant": get_tenant_name(item["tenant_id"]),
                                "Eventos": item["event_count"],
                            }
                            for item in by_tenant[:10]
                        ]
                        df_t = pd.DataFrame(tenant_rows)
                        st.bar_chart(df_t.set_index("Tenant"))
            finally:
                db.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Tab 2: Friccion ──
    with tab_friction:
        st.caption(TOOLTIPS["friction_score"])
        try:
            db = SessionLocal()
            try:
                repo = CopilotEventRepository(db)
                if is_global:
                    friction = repo.get_global_friction_map(days=days)
                else:
                    friction = repo.get_friction_map(selected_tenant, days=days)

                if friction:
                    total = sum(friction.values())
                    rows = []
                    for route, count in friction.items():
                        pct = round(count / total * 100, 1)
                        rows.append(
                            {
                                "Ruta": route,
                                "Aperturas": count,
                                "% Total": f"{pct}%",
                                "Flag": pct_flag(pct),
                            },
                        )
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Insights
                    high = [r for r in rows if float(r["% Total"].rstrip("%")) > 30]
                    for r in high:
                        st.warning(
                            f"**{r['Ruta']}** concentra {r['% Total']} de las aperturas. "
                            f"Los usuarios necesitan mas ayuda en esa seccion.",
                        )
                else:
                    st.info("Sin datos de aperturas del copilot.")
            finally:
                db.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Tab 3: Procedimientos ──
    with tab_procs:
        st.caption(TOOLTIPS["procedure_completion"])
        try:
            db = SessionLocal()
            try:
                repo = CopilotEventRepository(db)
                if is_global:
                    rates = repo.get_global_procedure_rates(days=days)
                else:
                    rates = repo.get_procedure_completion_rates(
                        selected_tenant,
                        days=days,
                    )

                if rates:
                    rows = []
                    for proc_id, info in rates.items():
                        started = info.get("started", 0)
                        completed = info.get("completed", 0)
                        abandoned = info.get("abandoned", 0)
                        avg_step = info.get("avg_abandoned_step")
                        pct = round(completed / started * 100) if started else 0
                        flag = "🔴" if pct < 50 else "🟡" if pct < 75 else "🟢"
                        rows.append(
                            {
                                "Procedimiento": info.get("name", proc_id),
                                "Iniciados": started,
                                "Completados": completed,
                                "Abandonados": abandoned,
                                "Avg Paso Abandono": avg_step or "—",
                                "% Completado": f"{pct}%",
                                "Flag": flag,
                            },
                        )
                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    low = [
                        r
                        for r in rows
                        if int(r["% Completado"].rstrip("%")) < 50
                        and r["Abandonados"] > 0
                    ]
                    for r in low:
                        st.warning(
                            f"**{r['Procedimiento']}** — {r['% Completado']} completado. "
                            f"Abandono promedio en paso {r['Avg Paso Abandono']}. Considerar simplificar.",
                        )
                else:
                    st.info("Sin datos de procedimientos.")
            finally:
                db.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Tab 4: Engagement ──
    with tab_engage:
        try:
            db = SessionLocal()
            try:
                repo = CopilotEventRepository(db)
                if is_global:
                    engagement = repo.get_global_engagement(days=days)
                    summary = repo.get_global_summary(days=days)
                else:
                    engagement = repo.get_engagement_metrics(selected_tenant, days=days)
                    summary = repo.get_tenant_summary(selected_tenant, days=days)

                sv = engagement["suggested_vs_typed"]

                # Suggested vs Typed
                st.subheader("Sugeridos vs Escritos")
                st.caption(TOOLTIPS["suggested_vs_typed"])
                if sv["suggested"] or sv["typed"]:
                    sv_df = pd.DataFrame(
                        [
                            {"Tipo": "Sugeridos", "Cantidad": sv["suggested"]},
                            {"Tipo": "Escritos", "Cantidad": sv["typed"]},
                        ],
                    )
                    st.bar_chart(sv_df.set_index("Tipo"))
                else:
                    st.info("Sin datos de mensajes.")

                # Proposals
                st.subheader("Propuestas Aceptadas vs Rechazadas")
                st.caption(TOOLTIPS["proposal_acceptance"])
                accepted = summary.get("proposal_accepted", 0)
                rejected = summary.get("proposal_rejected", 0)
                if accepted or rejected:
                    prop_df = pd.DataFrame(
                        [
                            {"Resultado": "Aceptadas", "Cantidad": accepted},
                            {"Resultado": "Rechazadas", "Cantidad": rejected},
                        ],
                    )
                    st.bar_chart(prop_df.set_index("Resultado"))
                else:
                    st.info("Sin datos de propuestas.")

                # Nudge CTR
                st.subheader("Nudge Click-Through")
                st.caption(TOOLTIPS["nudge_ctr"])
                clicked = summary.get("nudge_clicked", 0)
                dismissed = summary.get("nudge_dismissed", 0)
                total_nudge = clicked + dismissed
                if total_nudge:
                    ctr = round(clicked / total_nudge * 100, 1)
                    st.metric(
                        "CTR",
                        f"{ctr}%",
                        help="nudge_clicked / (clicked + dismissed)",
                    )
                    st.write(f"Clicked: {clicked} | Dismissed: {dismissed}")
                else:
                    st.info("Sin datos de nudges.")

                # Knowledge searches
                st.subheader("Knowledge Base")
                kb_count = summary.get("knowledge_searched", 0)
                st.write(f"Busquedas totales: **{kb_count}**")

            finally:
                db.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Tab 5: Explorar ──
    with tab_explore:
        col_type, col_limit = st.columns(2)
        with col_type:
            event_type_filter = st.text_input(
                "Filtrar por Event Type (opcional)",
                key="intel_type",
            )
        with col_limit:
            explore_limit = st.slider("Limite", 10, 500, 100, key="intel_limit")

        try:
            db = SessionLocal()
            try:
                repo = CopilotEventRepository(db)
                if is_global:
                    events = repo.get_recent_events_all(
                        limit=explore_limit,
                        event_type=event_type_filter or None,
                    )
                else:
                    events = repo.get_recent_events(
                        selected_tenant,
                        limit=explore_limit,
                        event_type=event_type_filter or None,
                    )

                if events:
                    rows = []
                    for ev in events:
                        data_str = str(ev.event_data or {})
                        rows.append(
                            {
                                "Fecha": ev.created_at.strftime("%Y-%m-%d %H:%M")
                                if ev.created_at
                                else "—",
                                "Tenant": get_tenant_name(ev.tenant_id),
                                "Usuario": str(ev.user_id)[:8],
                                "Tipo": ev.event_type,
                                "Ruta": ev.route or "—",
                                "Data": data_str[:100]
                                + ("..." if len(data_str) > 100 else ""),
                            },
                        )
                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(f"Mostrando {len(events)} eventos")

                    # Expandable JSON details
                    with st.expander("Ver datos completos de eventos"):
                        for ev in events[:20]:
                            st.json(ev.event_data or {})
                            st.divider()
                else:
                    st.info("Sin eventos.")
            finally:
                db.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")
