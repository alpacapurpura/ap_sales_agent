"""Streamlit admin: Auditoría del Agente de Ventas — visualiza interacciones y nodos de LangGraph."""

import streamlit as st

from src.admin.modules._shared import render_tenant_selector
from src.core.database import SessionLocal
from src.modules.sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)


def _format_lead_option(lead_tuple: tuple) -> str:
    # Unpack tuple: first element is LeadModel, second is last_activity
    lead = lead_tuple[0]
    last_act = lead_tuple[1]

    # Intentar obtener el nombre desde customer o desde profile_data
    name = "Sin Nombre"
    if getattr(lead, "customer", None) and getattr(lead.customer, "full_name", None):
        name = lead.customer.full_name
    elif lead.profile_data and isinstance(lead.profile_data, dict):
        name = lead.profile_data.get("name", "Sin Nombre")

    channel = (
        "Telegram"
        if getattr(lead, "telegram_id", None)
        else ("WhatsApp" if getattr(lead, "whatsapp_id", None) else "Web")
    )
    date_str = last_act.strftime("%Y-%m-%d %H:%M") if last_act else "N/A"
    return f"{name} ({channel}) - {date_str}"


def render_sales_audit_page() -> None:
    st.title("🔍 Auditoría Sales Agent")
    st.markdown(
        "Visualiza las conversaciones de los leads y las trazas de ejecución de los nodos del agente.",
    )

    col1, col2 = st.columns(2)

    with col1:
        tenant_id = render_tenant_selector(key="audit_tenant", allow_all=False)

    if not tenant_id:
        st.info("Selecciona un tenant para continuar.")
        return

    db = SessionLocal()
    try:
        repo = AuditRepository(db)

        with col2:
            # Fetch recent leads for the tenant
            # fallback for the fallback: get_recent_users requires tenant_id string usually, let's pass it as str
            leads = repo.get_recent_users(tenant_id=str(tenant_id), limit=200)

            if not leads:
                st.warning("No se encontraron leads recientes para este tenant.")
                return

            selected_lead_tuple = st.selectbox(
                "Seleccionar Lead (busca por nombre)",
                options=leads,
                format_func=_format_lead_option,
                key="audit_lead",
            )

        if not selected_lead_tuple:
            return

        lead = selected_lead_tuple[0]
        lead_id = str(lead.id)

        # Intentar obtener el nombre desde customer o desde profile_data
        lead_name = "Sin Nombre"
        if getattr(lead, "customer", None) and getattr(
            lead.customer,
            "full_name",
            None,
        ):
            lead_name = lead.customer.full_name
        elif lead.profile_data and isinstance(lead.profile_data, dict):
            lead_name = lead.profile_data.get("name", "Sin Nombre")

        st.divider()
        col_title, col_actions = st.columns([3, 1])
        with col_title:
            st.subheader(f"Timeline: {lead_name}")

        with col_actions:
            # Botones para mostrar contexto en el sidebar
            if st.button("Ver Perfil de Lead", use_container_width=True):
                st.session_context_tab = "profile"

            if st.button("Ver Último Estado (Agent State)", use_container_width=True):
                st.session_context_tab = "state"

            if st.button(
                "🗑️ Limpiar Conversación",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state["confirm_clear"] = lead_id

        # Confirmation dialog
        if st.session_state.get("confirm_clear") == lead_id:
            st.warning(
                f"**¿Limpiar TODA la conversación de {lead_name}?**\n\n"
                "Se borrarán: mensajes, trazas, LLM logs, checkpoints, y se resetearán los scores del lead. "
                "Esta acción no se puede deshacer.",
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(
                    "✅ Sí, limpiar",
                    use_container_width=True,
                    type="primary",
                ):
                    repo.clear_user_history(lead_id=lead_id, tenant_id=str(tenant_id))
                    st.session_state.pop("confirm_clear", None)
                    st.success(
                        "Conversación limpiada. El lead empezará de cero en la próxima interacción.",
                    )
                    st.rerun()
            with col_no:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.pop("confirm_clear", None)
                    st.rerun()

        # Mostrar el panel lateral si se presionó algún botón
        if hasattr(st, "session_context_tab") and st.session_context_tab:
            with st.sidebar:
                st.divider()
                st.subheader("📋 Contexto Global")

                if st.session_context_tab == "profile":
                    st.markdown("**Perfil del Lead (Profile Data)**")
                    if lead.profile_data and isinstance(lead.profile_data, dict):
                        st.json(lead.profile_data, expanded=False)
                    else:
                        st.info("Sin datos de perfil (profile_data).")

                    st.markdown("**Historial de Objeciones**")
                    if lead.key_objections_history:
                        st.json(lead.key_objections_history, expanded=False)
                    else:
                        st.info("Sin objeciones registradas.")

                    st.markdown("**Resumen de Conversación**")
                    if lead.conversation_summary:
                        st.info(lead.conversation_summary)
                    else:
                        st.info("Sin resumen.")

                elif st.session_context_tab == "state":
                    st.markdown("**Último Agent State Registrado**")
                    # Forma segura de importar el modelo
                    from src.modules.sales_agent.infrastructure.models.agent_trace_model import (
                        AgentTrace,
                    )

                    last_trace = (
                        repo.db.query(AgentTrace)
                        .filter(AgentTrace.user_id == lead_id)
                        .order_by(AgentTrace.created_at.desc())
                        .first()
                    )

                    if last_trace and last_trace.output_state:
                        st.json(last_trace.output_state, expanded=False)
                    else:
                        st.info(
                            "No hay trazas o estados registrados aún para este lead.",
                        )

                if st.button("Cerrar Contexto", key="close_ctx"):
                    st.session_context_tab = None
                    st.rerun()

        # Fetch timeline
        timeline = repo.get_full_timeline(
            lead_id=lead_id,
            tenant_id=str(tenant_id),
            limit=200,
        )

        # reverse timeline to show oldest first, or keep newest first depending on preference.
        # Frontend usually shows oldest top -> newest bottom. The repo returns newest first (desc).
        # We will reverse it so it reads naturally top-to-bottom.
        timeline_asc = list(reversed(timeline))

        if not timeline_asc:
            st.info("No hay eventos en la línea de tiempo de este lead.")
            return

        # Render timeline
        for event in timeline_asc:
            event_type = event.get("type")
            created_at = event.get("created_at")
            date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""

            if event_type == "message":
                role = event.get("role")
                content = event.get("content")
                with st.chat_message(role):
                    st.markdown(content)
                    st.caption(f"{date_str}")

            elif event_type == "trace":
                node_name = event.get("node")
                exec_time = event.get("execution_time", 0)

                with st.expander(f"⚙️ Nodo: {node_name} - {exec_time:.0f}ms"):
                    st.caption(f"Fecha: {date_str}")

                    tab_in, tab_out, tab_llm = st.tabs(
                        ["Input State", "Output State", "LLM Logs"],
                    )

                    with tab_in:
                        st.json(event.get("input") or {})

                    with tab_out:
                        st.json(event.get("output") or {})

                    with tab_llm:
                        has_llm = bool(event.get("llm_summary"))
                        if not has_llm:
                            st.info("Este nodo no registró interacciones con el LLM.")
                        else:
                            trace_details = repo.get_trace_details(
                                event["id"],
                                str(tenant_id),
                            )
                            if trace_details and trace_details.get("llm_logs"):
                                for log in trace_details["llm_logs"]:
                                    st.markdown(
                                        f"**Modelo:** `{log['model']}` | **Template:** `{log['prompt_template']}`",
                                    )
                                    st.markdown(
                                        f"**Tokens:** In `{log['tokens']['in']}` / Out `{log['tokens']['out']}`",
                                    )

                                    with st.container():
                                        st.markdown("**Prompt Renderizado:**")
                                        st.code(log["prompt"], language="markdown")

                                    with st.container():
                                        st.markdown("**Respuesta:**")
                                        st.code(log["response"], language="markdown")

                                    if log.get("metadata"):
                                        with st.expander("Metadata Adicional"):
                                            st.json(log["metadata"])
                            else:
                                st.warning(
                                    "No se pudieron cargar los detalles del LLM.",
                                )

    finally:
        db.close()
