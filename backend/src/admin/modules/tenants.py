import pandas as pd
import streamlit as st

from src.core.database import SessionLocal
from src.modules.iam.application.services.tenant_service import TenantService


def get_tenants():
    db = SessionLocal()
    try:
        service = TenantService(db)
        return service.get_all_tenants()
    finally:
        db.close()


def create_tenant(name, slug, can_use_keys, company_name, agent_persona):
    db = SessionLocal()
    try:
        service = TenantService(db)
        return service.create_tenant(
            name, slug, can_use_keys, company_name, agent_persona
        )
    finally:
        db.close()


def update_tenant(tenant_id, name, slug, can_use_keys, is_active):
    db = SessionLocal()
    try:
        service = TenantService(db)
        return service.update_tenant(tenant_id, name, slug, can_use_keys, is_active)
    finally:
        db.close()


def render_tenants_view():
    st.title("🏢 Gestión de Tenants")

    # Cargar tenants al inicio para usar en todas las pestañas
    tenants = get_tenants()

    # Tabs para organizar
    tab_list, tab_create, tab_edit = st.tabs(
        ["📋 Listado", "➕ Crear Nuevo", "✏️ Editar"]
    )

    # --- TAB 1: LISTADO ---
    with tab_list:
        st.header("Tenants Registrados")

        if not tenants:
            st.info("No hay tenants registrados aún.")
        else:
            # Preparamos datos para mostrar
            data = [
                {
                    "ID": str(t.id),
                    "Nombre": t.name,
                    "Slug": t.slug,
                    "Activo": t.is_active,
                    "Usa Keys Plataforma": t.can_use_platform_keys,
                    "Creado": t.created_at,
                }
                for t in tenants
            ]

            df = pd.DataFrame(data)
            st.dataframe(
                df,
                column_config={
                    "Activo": st.column_config.CheckboxColumn(
                        "Activo",
                        help="Estado del tenant",
                        default=True,
                    ),
                    "Usa Keys Plataforma": st.column_config.CheckboxColumn(
                        "Usa Keys Plataforma",
                        help="¿Puede usar las API keys de la plataforma?",
                        default=False,
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
            st.caption(f"Total: {len(tenants)} tenants")

    # --- TAB 2: CREAR ---
    with tab_create:
        st.header("Nuevo Tenant")

        # Check for success message from previous run
        if "tenant_created_success" in st.session_state:
            st.success(st.session_state.tenant_created_success)
            # Remove from session state so it doesn't persist forever
            del st.session_state.tenant_created_success

        with st.form("create_tenant_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Nombre del Tenant")
                new_slug = st.text_input("Slug (URL identifier)")
            with col2:
                new_company = st.text_input("Nombre de la Empresa (Config)")
                new_persona = st.text_input(
                    "Persona del Agente (Config)",
                    placeholder="Asistente útil y profesional",
                )

            new_use_keys = st.checkbox(
                "¿Permitir uso de Keys de Plataforma?", value=False
            )

            submitted = st.form_submit_button("Crear Tenant")
            if submitted:
                if not new_name or not new_slug:
                    st.error("Nombre y Slug son obligatorios.")
                else:
                    new_tenant, error = create_tenant(
                        name=new_name,
                        slug=new_slug,
                        can_use_keys=new_use_keys,
                        company_name=new_company,
                        agent_persona=new_persona or "Asistente útil y profesional",
                    )

                    if new_tenant:
                        st.session_state.tenant_created_success = (
                            f"✅ Tenant '{new_name}' creado exitosamente!"
                        )
                        st.rerun()
                    else:
                        st.error(error)

    # --- TAB 3: EDITAR ---
    with tab_edit:
        st.header("Editar Tenant")
        tenants_opts = {t.name: t.id for t in tenants} if tenants else {}

        if not tenants_opts:
            st.warning("No hay tenants para editar.")
        else:
            selected_name = st.selectbox(
                "Seleccionar Tenant", list(tenants_opts.keys())
            )
            selected_id = tenants_opts[selected_name]

            # Usamos la lista ya cargada en memoria en lugar de hacer query directa
            # Esto mantiene la consistencia y evita consultas directas a DB desde la vista
            current_tenant = next((t for t in tenants if t.id == selected_id), None)

            if current_tenant:
                with st.form("edit_tenant_form"):
                    edit_name = st.text_input("Nombre", value=current_tenant.name)
                    edit_slug = st.text_input("Slug", value=current_tenant.slug)

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        edit_use_keys = st.checkbox(
                            "Usa Keys Plataforma",
                            value=current_tenant.can_use_platform_keys,
                        )
                    with col_e2:
                        edit_active = st.checkbox(
                            "Activo", value=current_tenant.is_active
                        )

                    submitted_edit = st.form_submit_button("Guardar Cambios")

                    if submitted_edit:
                        updated, error = update_tenant(
                            selected_id,
                            edit_name,
                            edit_slug,
                            edit_use_keys,
                            edit_active,
                        )
                        if updated:
                            st.success("Tenant actualizado correctamente.")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar: {error}")
