"""Streamlit admin: Comando Central — system-wide KPIs, adoption funnel, alerts."""

from datetime import UTC, datetime

import pandas as pd
import streamlit as st


def render_home_dashboard() -> None:
    st.title("🎯 Comando Central")

    # ── KPIs Row 1 ──
    try:
        from src.admin.modules._shared import (
            TOOLTIPS,
            get_adoption_funnel,
            get_all_tenants_summary,
            get_tenant_name,
            get_tenant_options,
        )
        from src.core.database import SessionLocal
        from src.modules.copilot.infrastructure.repositories.conversation_repository import (
            ConversationRepository,
        )
        from src.modules.copilot.infrastructure.repositories.event_repository import (
            CopilotEventRepository,
        )

        tenants = get_tenant_options()
        tenants_summary = get_all_tenants_summary()

        db = SessionLocal()
        try:
            event_repo = CopilotEventRepository(db)
            conv_repo = ConversationRepository(db)

            engagement_30d = event_repo.get_global_engagement(days=30)
            summary_30d = event_repo.get_global_summary(days=30)
            conv_count = conv_repo.count_all()

            # Active tenants (had events in 7d)
            now = datetime.now(UTC)
            active_tenants = sum(1 for t in tenants_summary if t["last_event"] and (now - t["last_event"]).days < 7)
            total_users = sum(t["user_count"] for t in tenants_summary)
            # Acceptance rate
            accepted = summary_30d.get("proposal_accepted", 0)
            rejected = summary_30d.get("proposal_rejected", 0)
            total_proposals = accepted + rejected
            acceptance_rate = f"{round(accepted / total_proposals * 100)}%" if total_proposals else "N/A"

            # Procedure completion
            proc_rates = event_repo.get_global_procedure_rates(days=30)
            total_started = sum(p.get("started", 0) for p in proc_rates.values())
            total_completed = sum(p.get("completed", 0) for p in proc_rates.values())
            proc_pct = f"{round(total_completed / total_started * 100)}%" if total_started else "N/A"

            # Knowledge docs count
            try:
                from src.modules.copilot.infrastructure.knowledge.vector_store import (
                    CopilotKnowledgeStore,
                )

                store = CopilotKnowledgeStore()
                kb_stats = store.get_collection_stats()
                kb_docs = kb_stats.get("points_count", 0)
            except Exception:  # noqa: BLE001 — Streamlit UI error boundary
                kb_docs = "?"

            # Row 1
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Tenants Total",
                len(tenants),
                help="Tenants registrados en el sistema",
            )
            c2.metric(
                "Tenants Activos 7d",
                active_tenants,
                help=TOOLTIPS["active_tenant"],
            )
            c3.metric(
                "Usuarios Totales",
                total_users,
                help="Usuarios registrados en todos los tenants",
            )
            c4.metric(
                "Sesiones Copilot 30d",
                conv_count,
                help="Conversaciones del copilot en los ultimos 30 dias",
            )

            # Row 2
            c5, c6, c7, c8 = st.columns(4)
            c5.metric(
                "Mensajes 30d",
                engagement_30d["total_messages"],
                help=TOOLTIPS["total_events"],
            )
            c6.metric(
                "Tasa Aceptacion",
                acceptance_rate,
                help=TOOLTIPS["proposal_acceptance"],
            )
            c7.metric(
                "Procedimientos OK",
                proc_pct,
                help=TOOLTIPS["procedure_completion"],
            )
            c8.metric("Knowledge Chunks", kb_docs, help=TOOLTIPS["knowledge_docs"])

        finally:
            db.close()

    except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
        st.error(f"Error cargando dashboard: {e}")
        import traceback

        st.code(traceback.format_exc())
        return

    st.divider()

    # ── Tabs ──
    tab_funnel, tab_alerts, tab_activity = st.tabs(
        [
            "📊 Funnel de Adopcion",
            "🚨 Alertas de Salud",
            "⏱️ Actividad Reciente",
        ],
    )

    # ── Funnel de Adopcion ──
    with tab_funnel:
        st.caption("Muestra en que etapa del onboarding estan tus tenants")
        try:
            funnel = get_adoption_funnel()
            total = funnel.get("total_tenants", 1) or 1

            stages = [
                ("Brand configurado", funnel.get("has_brand", 0)),
                ("Oferta creada", funnel.get("has_offer", 0)),
                ("Conexion activa", funnel.get("has_connection", 0)),
                ("Copilot usado", funnel.get("has_copilot", 0)),
                ("Procedimiento completado", funnel.get("has_procedure_completed", 0)),
            ]

            # Horizontal bar chart using st.bar_chart alternative
            funnel_df = pd.DataFrame(stages, columns=["Etapa", "Tenants"])
            funnel_df["Porcentaje"] = (funnel_df["Tenants"] / total * 100).round(1)

            # Display as progress-style
            for _, row in funnel_df.iterrows():
                col_label, col_bar, col_num = st.columns([3, 6, 2])
                col_label.write(f"**{row['Etapa']}**")
                col_bar.progress(min(row["Tenants"] / total, 1.0))
                col_num.write(f"{int(row['Tenants'])}/{total} ({row['Porcentaje']}%)")

        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Alertas de Salud ──
    with tab_alerts:
        st.caption("Alertas automaticas basadas en reglas estaticas")
        try:
            now = datetime.now(UTC)
            has_alerts = False

            # Alert 1: Tenants inactive >14 days
            for t in tenants_summary:
                if t["last_event"]:
                    days_inactive = (now - t["last_event"]).days
                    if days_inactive > 14:
                        st.error(
                            f"🚫 **{t['name']}** — Inactivo hace {days_inactive} dias (sin eventos de copilot)",
                        )
                        has_alerts = True
                elif t["is_active"]:
                    st.error(f"🚫 **{t['name']}** — Nunca ha usado el copilot")
                    has_alerts = True

            # Alert 2: Procedure abandonment
            db2 = SessionLocal()
            try:
                repo2 = CopilotEventRepository(db2)
                proc_rates = repo2.get_global_procedure_rates(days=30)
                for proc_id, info in proc_rates.items():
                    if info.get("abandoned", 0) >= 3:
                        st.warning(
                            f"⚠️ Procedimiento **{info.get('name', proc_id)}** — "
                            f"{info['abandoned']} abandonos (avg paso {info.get('avg_abandoned_step', '?')})",
                        )
                        has_alerts = True

                # Alert 3: Friction concentration
                friction = repo2.get_global_friction_map(days=30)
                total_opens = sum(friction.values()) if friction else 0
                if total_opens > 0:
                    for route, count in friction.items():
                        pct = count / total_opens * 100
                        if pct > 50:
                            st.warning(
                                f"⚠️ Ruta **{route}** concentra {pct:.0f}% de las aperturas del copilot",
                            )
                            has_alerts = True

            finally:
                db2.close()

            # Alert 4: Tenants without connections
            funnel_data = get_adoption_funnel()
            no_conn = funnel_data.get("total_tenants", 0) - funnel_data.get(
                "has_connection",
                0,
            )
            if no_conn > 0:
                st.info(f"ℹ️ {no_conn} tenant(s) sin conexiones configuradas")
                has_alerts = True

            if not has_alerts:
                st.success("✅ Todo en orden — sin alertas activas")

        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # ── Actividad Reciente ──
    with tab_activity:
        st.caption("Feed en tiempo real de toda la actividad del copilot")
        try:
            db3 = SessionLocal()
            try:
                repo3 = CopilotEventRepository(db3)
                recent = repo3.get_recent_events_all(limit=50)
                if recent:
                    rows = []
                    for ev in recent:
                        data_str = str(ev.event_data or {})
                        rows.append(
                            {
                                "Fecha": ev.created_at.strftime("%Y-%m-%d %H:%M") if ev.created_at else "—",
                                "Tenant": get_tenant_name(ev.tenant_id),
                                "Usuario": str(ev.user_id)[:8],
                                "Tipo": ev.event_type,
                                "Ruta": ev.route or "—",
                                "Detalle": data_str[:80] + ("..." if len(data_str) > 80 else ""),
                            },
                        )
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.caption(f"Mostrando ultimos {len(recent)} eventos")
                else:
                    st.info("Sin eventos recientes.")
            finally:
                db3.close()
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")
