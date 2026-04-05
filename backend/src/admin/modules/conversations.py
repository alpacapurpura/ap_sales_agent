"""Streamlit admin: Explorador de Conversaciones — browse copilot conversations."""

import pandas as pd
import streamlit as st


def render_conversations_page():  # noqa: C901
    st.title("💬 Explorador de Conversaciones")

    from src.admin.modules._shared import (
        TOOLTIPS,
        get_tenant_name,
        render_tenant_selector,
    )
    from src.core.database import SessionLocal
    from src.modules.copilot.infrastructure.repositories.conversation_repository import (
        ConversationRepository,
    )

    # ── Filters ──
    col_tenant, col_search, col_period, col_limit = st.columns([3, 3, 2, 2])
    with col_tenant:
        selected_tenant = render_tenant_selector(key="conv_tenant", allow_all=True)
    with col_search:
        search_query = st.text_input("Buscar en titulo", key="conv_search")
    with col_period:
        # Period placeholder — conversations are ordered by date already
        st.write("")  # spacing
    with col_limit:
        limit = st.slider("Limite", 10, 200, 50, key="conv_limit")

    # ── KPIs ──
    try:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            stats = repo.get_global_stats(days=30)
            total_convs = repo.count_all(tenant_id=selected_tenant)

            # Get conversations for analysis
            convs = repo.list_all_paginated(
                tenant_id=selected_tenant,
                limit=limit,
            )

            # Compute avg msgs and tool usage
            total_msgs = 0
            total_tools = 0
            convs_with_tools = 0
            for conv in convs:
                msgs = conv.messages or []
                total_msgs += len(msgs)
                conv_tool_count = 0
                for msg in msgs:
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        tcs = msg.get("tool_calls", [])
                        if isinstance(tcs, list):
                            conv_tool_count += len(tcs)
                total_tools += conv_tool_count
                if conv_tool_count > 0:
                    convs_with_tools += 1

            avg_msgs = round(total_msgs / len(convs), 1) if convs else 0
            avg_tools = round(total_tools / len(convs), 1) if convs else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Total Conversaciones",
                total_convs,
                help="Conversaciones en el periodo seleccionado",
            )
            c2.metric(
                "Promedio Msgs/Conv",
                avg_msgs,
                help="Promedio de mensajes por conversacion",
            )
            c3.metric(
                "Tenants con Copilot",
                f"{stats['tenants_with_conversations']}/{len(convs)}",
                help="Tenants que han usado el copilot en 30 dias",
            )
            c4.metric("Tools/Conv Avg", avg_tools, help=TOOLTIPS["conversation_tools"])

        finally:
            db.close()
    except Exception as e:
        st.error(f"Error cargando stats: {e}")
        convs = []

    st.divider()

    # ── Conversations Table ──
    if not convs:
        st.info("Sin conversaciones.")
        return

    # Filter by search
    if search_query:
        convs = [c for c in convs if search_query.lower() in (c.title or "").lower()]

    # Build table
    table_rows = []
    for conv in convs:
        msgs = conv.messages or []
        msg_count = len(msgs)
        tool_count = 0
        for msg in msgs:
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                tcs = msg.get("tool_calls", [])
                if isinstance(tcs, list):
                    tool_count += len(tcs)

        title = conv.title or ""
        if not title and msgs:
            first_msg = msgs[0]
            if isinstance(first_msg, dict):
                title = (first_msg.get("content", "") or "")[:50]
        title = title or "Sin titulo"

        table_rows.append(
            {
                "_id": str(conv.id),
                "Tenant": get_tenant_name(conv.tenant_id),
                "Usuario": str(conv.user_id)[:8],
                "Titulo": title,
                "Msgs": msg_count,
                "Tools": tool_count,
                "Fecha": conv.updated_at.strftime("%Y-%m-%d %H:%M")
                if conv.updated_at
                else "—",
            }
        )

    display_df = pd.DataFrame(table_rows)
    st.dataframe(
        display_df.drop(columns=["_id"]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando {len(table_rows)} conversaciones")

    # ── Detail View ──
    st.divider()
    st.subheader("Detalle de Conversacion")

    conv_options = [f"{r['Titulo'][:40]} ({r['Fecha']})" for r in table_rows]
    if not conv_options:
        return

    selected_idx = st.selectbox(
        "Seleccionar conversacion:",
        range(len(conv_options)),
        format_func=lambda i: conv_options[i],
        key="conv_detail_select",
    )

    selected_conv = convs[selected_idx]
    msgs = selected_conv.messages or []

    tab_msgs, tab_tools, tab_context = st.tabs(
        [
            "💬 Mensajes",
            "🔧 Tools Usados",
            "📋 Contexto",
        ]
    )

    # ── Messages Tab ──
    with tab_msgs:
        for msg in msgs:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                st.markdown(f"**🔵 [user]** {content}")
            elif role == "assistant":
                if content:
                    display = content[:500]
                    if len(content) > 500:
                        with st.expander(f"🟢 [assistant] ({len(content)} chars)"):
                            st.write(content)
                    else:
                        st.markdown(f"**🟢 [assistant]** {display}")

                tool_calls = msg.get("tool_calls", [])
                if isinstance(tool_calls, list):
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            args_str = str(tc.get("args", ""))[:80]
                            st.markdown(
                                f"**🟠 [tool_call]** `{tc.get('name', '?')}`({args_str})"
                            )
            elif role == "tool":
                tool_content = content or ""
                if len(tool_content) > 200:
                    with st.expander(
                        f"⚪ [tool_result] {msg.get('name', '')} ({len(tool_content)} chars)"
                    ):
                        st.code(tool_content[:2000])
                else:
                    st.markdown(f"**⚪ [tool_result]** {tool_content[:200]}")

    # ── Tools Tab ──
    with tab_tools:
        tool_counts = {}
        for msg in msgs:
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                tcs = msg.get("tool_calls", [])
                if isinstance(tcs, list):
                    for tc in tcs:
                        if isinstance(tc, dict):
                            name = tc.get("name", "unknown")
                            tool_counts[name] = tool_counts.get(name, 0) + 1

        if tool_counts:
            tool_rows = [
                {"Tool": k, "Invocaciones": v}
                for k, v in sorted(tool_counts.items(), key=lambda x: -x[1])
            ]
            st.dataframe(
                pd.DataFrame(tool_rows), use_container_width=True, hide_index=True
            )
        else:
            st.info("No se usaron tools en esta conversacion.")

    # ── Context Tab ──
    with tab_context:
        ctx = selected_conv.client_context
        if ctx:
            st.json(ctx)
        else:
            st.info("Sin contexto de cliente registrado.")

        st.write(f"**Conversation ID:** `{selected_conv.id}`")
        st.write(f"**Tenant ID:** `{selected_conv.tenant_id}`")
        st.write(f"**User ID:** `{selected_conv.user_id}`")
        st.write(f"**Creada:** {selected_conv.created_at}")
        st.write(f"**Actualizada:** {selected_conv.updated_at}")
