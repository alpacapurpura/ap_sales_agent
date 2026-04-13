"""Streamlit admin: Salud de Tenants — cross-tenant health overview with drill-down."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _get_module_completion(db: Session, tenant_id: object, module_id: str, registry: object) -> float:
    """Return 0.0-1.0 completion for a module."""
    from src.modules.copilot.domain.schema_introspection import (
        check_section_completion,
        get_model_sections,
    )

    descriptor = registry.get(module_id)
    if not descriptor or not descriptor.repo_factory:
        return 0.0
    try:
        repo = descriptor.repo_factory(db)
        data = descriptor.read_fn(repo, tenant_id)
    except Exception:  # noqa: BLE001 — Streamlit UI error boundary
        return 0.0
    if not data:
        return 0.0
    if isinstance(data, list):
        return 1.0 if len(data) > 0 else 0.0
    if descriptor.model_class and hasattr(data, "model_dump"):
        raw = data.model_dump(mode="json")
        sections = get_model_sections(descriptor.model_class)
        completion = check_section_completion(raw, sections)
        if not completion:
            return 0.0
        configured = sum(1 for s in completion.values() if s.is_configured)
        return configured / len(completion) if completion else 0.0
    return 1.0


def render_tenant_health() -> None:
    """Render the cross-tenant health overview with drill-down."""
    st.title("🏥 Salud de Tenants")

    from src.admin.modules._shared import (
        TOOLTIPS,
        completion_flag,
        get_all_tenants_summary,
        get_tenant_options,
        health_flag,
    )
    from src.core.database import SessionLocal

    # ── Filters ──
    col_search, col_status, col_sort, col_period = st.columns(4)
    with col_search:
        search = st.text_input("Buscar tenant", key="health_search")
    with col_status:
        status_filter = st.selectbox(
            "Estado",
            ["Todos", "Activos", "Inactivos"],
            key="health_status",
        )
    with col_sort:
        sort_by = st.selectbox(
            "Ordenar",
            ["Mas activo", "Menos activo", "Mas reciente"],
            key="health_sort",
        )
    with col_period:
        period = st.slider("Periodo (dias)", 7, 90, 30, key="health_period")

    # ── Main Table ──
    try:
        tenants_data = get_all_tenants_summary()
        now = datetime.now(UTC)

        db = SessionLocal()
        try:
            from src.modules.copilot.infrastructure.repositories.event_repository import (
                CopilotEventRepository,
            )

            event_repo = CopilotEventRepository(db)
            from src.modules.copilot.domain.module_registry import get_module_registry

            registry = get_module_registry()

            rows = []
            for t in tenants_data:
                tid = t["id"]

                # Filter by search
                if search and search.lower() not in t["name"].lower():
                    continue
                # Filter by status
                if status_filter == "Activos" and not t["is_active"]:
                    continue
                if status_filter == "Inactivos" and t["is_active"]:
                    continue

                # Compute days inactive
                if t["last_event"]:
                    days_inactive = (now - t["last_event"]).days
                    last_act = t["last_event"].strftime("%Y-%m-%d") if days_inactive > 1 else "Hoy"
                else:
                    days_inactive = 999
                    last_act = "Nunca"

                # Module completion (batch — lightweight)
                brand_ratio = _get_module_completion(db, tid, "brand", registry)
                offer_ratio = _get_module_completion(db, tid, "offer", registry)
                conn_ratio = _get_module_completion(db, tid, "connections", registry)

                # Message count for period
                summary = event_repo.get_tenant_summary(tid, days=period)
                msg_count = summary.get("message_sent", 0)

                rows.append(
                    {
                        "_id": str(tid),
                        "_days_inactive": days_inactive,
                        "_msg_count": msg_count,
                        "Tenant": t["name"],
                        "Estado": health_flag(days_inactive),
                        "Brand": brand_ratio,
                        "Offer": offer_ratio,
                        "Conn": conn_ratio,
                        "Msgs": msg_count,
                        "Users": t["user_count"],
                        "Ultima Act.": last_act,
                    },
                )

            # Sort
            if sort_by == "Mas activo":
                rows.sort(key=lambda r: -r["_msg_count"])
            elif sort_by == "Menos activo":
                rows.sort(key=lambda r: r["_msg_count"])
            elif sort_by == "Mas reciente":
                rows.sort(key=lambda r: r["_days_inactive"])

            if rows:
                display_df = pd.DataFrame(rows)
                display_df = display_df.drop(
                    columns=["_id", "_days_inactive", "_msg_count"],
                )

                st.dataframe(
                    display_df,
                    column_config={
                        "Brand": st.column_config.ProgressColumn(
                            "Brand",
                            min_value=0,
                            max_value=1,
                            format="%.0f%%",
                            help=TOOLTIPS["module_completion"],
                        ),
                        "Offer": st.column_config.ProgressColumn(
                            "Offer",
                            min_value=0,
                            max_value=1,
                            format="%.0f%%",
                            help=TOOLTIPS["module_completion"],
                        ),
                        "Conn": st.column_config.ProgressColumn(
                            "Conn",
                            min_value=0,
                            max_value=1,
                            format="%.0f%%",
                            help=TOOLTIPS["module_completion"],
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(f"Mostrando {len(rows)} tenants")
            else:
                st.info("Sin tenants que coincidan con los filtros.")

        finally:
            db.close()

    except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
        st.error(f"Error: {e}")
        import traceback

        st.code(traceback.format_exc())
        return

    # ── Drill-down ──
    st.divider()
    st.subheader("Detalle por Tenant")

    tenant_opts = get_tenant_options()
    if not tenant_opts:
        return

    tenant_names = [t["name"] for t in tenant_opts]
    selected_name = st.selectbox(
        "Ver detalle de:",
        tenant_names,
        key="health_detail_tenant",
    )
    selected_tenant = next((t for t in tenant_opts if t["name"] == selected_name), None)

    if not selected_tenant:
        return

    sel_tid = UUID(selected_tenant["id"])

    tab_modules, tab_copilot, tab_users, tab_convs = st.tabs(
        [
            "📦 Modulos",
            "🧠 Uso Copilot",
            "👥 Usuarios",
            "💬 Conversaciones",
        ],
    )

    # ── Tab: Modulos ──
    with tab_modules:
        db_detail = SessionLocal()
        try:
            from src.modules.copilot.domain.module_registry import get_module_registry
            from src.modules.copilot.domain.schema_introspection import (
                check_section_completion,
                get_model_sections,
            )

            registry = get_module_registry()

            for mod_id in ["brand", "offer", "connections", "landing"]:
                descriptor = registry.get(mod_id)
                if not descriptor or not descriptor.repo_factory:
                    continue

                ratio = _get_module_completion(db_detail, sel_tid, mod_id, registry)
                flag = completion_flag(ratio)
                st.write(f"**{descriptor.label}** {flag} {int(ratio * 100)}%")

                # Detailed sections for brand (Pydantic model)
                if mod_id == "brand" and descriptor.model_class:
                    try:
                        repo = descriptor.repo_factory(db_detail)
                        data = descriptor.read_fn(repo, sel_tid)
                        if data and hasattr(data, "model_dump"):
                            raw = data.model_dump(mode="json")
                            sections = get_model_sections(descriptor.model_class)
                            completion = check_section_completion(raw, sections)
                            for sec_name, sec_status in completion.items():
                                icon = "✅" if sec_status.is_configured else "❌"
                                st.caption(f"  {icon} {sec_name}")
                    except Exception:  # noqa: BLE001 — Streamlit UI error boundary
                        pass

                # Count for list-based modules
                if mod_id in ("offer", "connections", "landing"):
                    try:
                        repo = descriptor.repo_factory(db_detail)
                        data = descriptor.read_fn(repo, sel_tid)
                        count = len(data) if isinstance(data, list) else 0
                        st.caption(f"  {count} items")
                    except Exception:  # noqa: BLE001 — Streamlit UI error boundary
                        pass
        finally:
            db_detail.close()

    # ── Tab: Uso Copilot ──
    with tab_copilot:
        db_copilot = SessionLocal()
        try:
            from src.modules.copilot.infrastructure.repositories.event_repository import (
                CopilotEventRepository,
            )

            repo_cp = CopilotEventRepository(db_copilot)

            # Engagement KPIs
            eng = repo_cp.get_engagement_metrics(sel_tid, days=period)
            c1, c2, c3 = st.columns(3)
            c1.metric("Usuarios Activos", eng["active_users"])
            c2.metric("Mensajes", eng["total_messages"])
            c3.metric("Msgs/User", eng["messages_per_user_avg"])

            # Event summary bar chart
            summary = repo_cp.get_tenant_summary(sel_tid, days=period)
            if summary:
                st.subheader("Eventos por Tipo")
                df_ev = pd.DataFrame(
                    [{"Tipo": k, "Cantidad": v} for k, v in sorted(summary.items(), key=lambda x: -x[1])],
                )
                st.bar_chart(df_ev.set_index("Tipo"))

            # Friction map
            friction = repo_cp.get_friction_map(sel_tid, days=period)
            if friction:
                st.subheader("Mapa de Friccion")
                total_f = sum(friction.values())
                friction_rows = []
                for route, count in friction.items():
                    pct = round(count / total_f * 100, 1)
                    flag = "🔴" if pct > 20 else "🟡" if pct > 10 else "🟢"
                    friction_rows.append(
                        {
                            "Ruta": route,
                            "Aperturas": count,
                            "%": f"{pct}%",
                            "Flag": flag,
                        },
                    )
                st.dataframe(
                    pd.DataFrame(friction_rows),
                    use_container_width=True,
                    hide_index=True,
                )

            # Procedure rates
            proc = repo_cp.get_procedure_completion_rates(sel_tid, days=period)
            if proc:
                st.subheader("Procedimientos")
                proc_rows = []
                for pid, info in proc.items():
                    started = info.get("started", 0)
                    completed = info.get("completed", 0)
                    pct = round(completed / started * 100) if started else 0
                    proc_rows.append(
                        {
                            "Procedimiento": info.get("name", pid),
                            "Iniciados": started,
                            "Completados": completed,
                            "% OK": f"{pct}%",
                        },
                    )
                st.dataframe(
                    pd.DataFrame(proc_rows),
                    use_container_width=True,
                    hide_index=True,
                )
        finally:
            db_copilot.close()

    # ── Tab: Usuarios ──
    with tab_users:
        st.caption("Usuarios registrados en este tenant y su actividad de copilot")
        db_users = SessionLocal()
        try:
            from sqlalchemy import text

            result = db_users.execute(
                text("""
                SELECT
                    u.id, u.full_name, u.email, u.role,
                    COUNT(ce.id) AS msg_count,
                    MAX(ce.created_at) AS last_activity
                FROM users u
                INNER JOIN user_tenants ut ON ut.user_id = u.id AND ut.tenant_id = :tid AND ut.is_active = true
                LEFT JOIN copilot_events ce ON ce.user_id = u.id
                    AND ce.tenant_id = :tid
                    AND ce.event_type = 'message_sent'
                    AND ce.deleted_at IS NULL
                WHERE u.is_active = true
                GROUP BY u.id, u.full_name, u.email, u.role
                ORDER BY msg_count DESC
            """),
                {"tid": sel_tid},
            )
            user_rows = []
            for r in result:
                row = dict(r._mapping)
                last = row["last_activity"]
                user_rows.append(
                    {
                        "Nombre": row["full_name"] or "—",
                        "Email": row["email"] or "—",
                        "Rol": row["role"] or "—",
                        "Msgs": row["msg_count"],
                        "Ultima Act.": last.strftime("%Y-%m-%d") if last else "—",
                    },
                )
            if user_rows:
                st.dataframe(
                    pd.DataFrame(user_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Sin usuarios para este tenant.")
        finally:
            db_users.close()

    # ── Tab: Conversaciones ──
    with tab_convs:
        db_conv = SessionLocal()
        try:
            from src.modules.copilot.infrastructure.repositories.conversation_repository import (
                ConversationRepository,
            )

            conv_repo = ConversationRepository(db_conv)
            convs = conv_repo.list_by_tenant(sel_tid, limit=10)
            if convs:
                for conv in convs:
                    msgs = conv.messages or []
                    title = conv.title or (msgs[0].get("content", "")[:50] if msgs else "Sin titulo")
                    with st.expander(
                        f"💬 {title} ({len(msgs)} msgs)"
                        f" — {conv.updated_at.strftime('%Y-%m-%d %H:%M') if conv.updated_at else ''}",
                    ):
                        for msg in msgs[:20]:
                            if isinstance(msg, dict):
                                role = msg.get("role", "?")
                                content = msg.get("content", "")
                                if role == "user":
                                    st.markdown(f"**🔵 User:** {content}")
                                elif role == "assistant":
                                    display = content[:500] if content else ""
                                    st.markdown(f"**🟢 Assistant:** {display}")
                                    tool_calls = msg.get("tool_calls", [])
                                    if tool_calls:
                                        for tc in tool_calls:
                                            if isinstance(tc, dict):
                                                st.caption(
                                                    f"🔧 {tc.get('name', '?')}({str(tc.get('args', ''))[:80]})",
                                                )
            else:
                st.info("Sin conversaciones para este tenant.")
        finally:
            db_conv.close()
