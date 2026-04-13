import time

import pandas as pd
import streamlit as st
import structlog

from src.core.database import SessionLocal
from src.modules.iam.infrastructure.models.tenant_model import TenantModel as Tenant
from src.modules.iam.infrastructure.models.user_model import UserModel as User
from src.modules.iam.infrastructure.models.user_tenant_model import (
    UserTenantModel as UserTenant,
)
from src.shared.infrastructure.external.clerk import ClerkService

logger = structlog.get_logger()


def get_tenants():
    """Fetch all active tenants for the dropdown."""
    db = SessionLocal()
    try:
        return db.query(Tenant).filter(Tenant.is_active.is_(True)).order_by(Tenant.name).all()
    finally:
        db.close()


def get_users(tenant_id):
    """Fetch users belonging to a specific tenant."""
    db = SessionLocal()
    try:
        # Return Tuple (User, Role)
        return (
            db.query(User, UserTenant.role)
            .join(UserTenant)
            .filter(UserTenant.tenant_id == tenant_id)
            .filter(UserTenant.is_active.is_(True))
            .order_by(User.created_at.desc())
            .all()
        )
    finally:
        db.close()


def render_users_view():
    st.title("👥 Gestión de Usuarios")

    # 1. Select Tenant
    tenants = get_tenants()
    if not tenants:
        st.warning(
            "⚠️ No hay tenants activos. Cree un tenant primero en la sección de Tenants.",
        )
        return

    # Tenant Selection Logic
    tenant_options = {t.name: t.id for t in tenants}

    # Use columns for better layout
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_tenant_name = st.selectbox(
            "🏢 Seleccionar Tenant",
            list(tenant_options.keys()),
        )

    selected_tenant_id = tenant_options[selected_tenant_name]

    # Display current tenant info
    current_tenant = next((t for t in tenants if t.id == selected_tenant_id), None)
    if current_tenant:
        st.caption(
            f"Gestión de usuarios para: **{current_tenant.name}** ({current_tenant.slug})",
        )

    st.divider()

    # Tabs for organized view
    tab_list, tab_create = st.tabs(
        ["📋 Lista de Usuarios", "➕ Crear / Asignar Usuario"],
    )

    # --- TAB 1: LIST USERS ---
    with tab_list:
        users_result = get_users(selected_tenant_id)

        if not users_result:
            st.info(f"ℹ️ No hay usuarios registrados para {selected_tenant_name}.")
        else:
            # Prepare Data for Table
            data = []
            for u, role in users_result:
                data.append(
                    {
                        "ID": str(u.id),
                        "Nombre": u.full_name,
                        "Email": u.email,
                        "Rol (Tenant)": role,
                        "Estado": "✅ Activo" if u.is_active else "🚫 Bloqueado",
                        "Clerk ID": u.clerk_id,
                        "Creado": u.created_at.strftime("%Y-%m-%d") if u.created_at else "N/A",
                    },
                )

            df = pd.DataFrame(data)
            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Email": st.column_config.TextColumn("Email", width="medium"),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                },
            )
            st.caption(f"Total: {len(users_result)} usuarios")

            # --- ACTIONS SECTION ---
            st.divider()
            st.subheader("🔧 Acciones de Usuario")

            # User Selector for Actions
            # Map full_name to User ID. We iterate over users_result (tuples)
            user_options_map = {f"{u.full_name or 'Sin Nombre'} ({u.email})": u.id for u, _ in users_result}
            selected_user_label = st.selectbox(
                "Seleccionar Usuario para modificar",
                list(user_options_map.keys()),
            )
            selected_user_id = user_options_map[selected_user_label]

            # Fetch fresh user object for actions
            db_actions = SessionLocal()
            try:
                target_user = db_actions.query(User).filter(User.id == selected_user_id).first()

                if target_user:
                    col_act1, col_act2, col_act3 = st.columns(3)

                    # Action: Change Password
                    with col_act1:
                        with st.container(border=True):
                            st.markdown("#### 🔐 Cambiar Contraseña")
                            with st.form("change_pwd_form"):
                                new_pass = st.text_input(
                                    "Nueva Contraseña",
                                    type="password",
                                    help="Mínimo 8 caracteres",
                                )
                                submit_pass = st.form_submit_button(
                                    "Actualizar Password",
                                )

                                if submit_pass:
                                    if not new_pass or len(new_pass) < 8:
                                        st.error(
                                            "La contraseña debe tener al menos 8 caracteres.",
                                        )
                                    elif not target_user.clerk_id:
                                        st.error(
                                            "❌ Este usuario no tiene Clerk ID vinculado."
                                            " No se puede cambiar password.",
                                        )
                                    else:
                                        clerk = ClerkService()
                                        try:
                                            if clerk.update_user_password(
                                                target_user.clerk_id,
                                                new_pass,
                                            ):
                                                st.success(
                                                    "✅ Contraseña actualizada exitosamente en Clerk.",
                                                )
                                            else:
                                                st.error(
                                                    "❌ Error al actualizar en Clerk."
                                                    " Verifique logs (Posible password débil o pwned).",
                                                )
                                        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                                            st.error(f"❌ Error Clerk: {e}")

                    # -- Block/Unblock (Global) --
                    with col_act2:
                        with st.container(border=True):
                            st.markdown("#### 🚫 Gestión de Acceso")
                            status_label = "Activo" if target_user.is_active else "Bloqueado"
                            status_color = "green" if target_user.is_active else "red"
                            st.markdown(
                                f"Estado Actual: :{status_color}[**{status_label}**]",
                            )

                            clerk = ClerkService()

                            if target_user.is_active:
                                if st.button(
                                    "🔴 Bloquear (Banear) Usuario",
                                    type="primary",
                                    use_container_width=True,
                                ):
                                    # 1. Ban in Clerk
                                    clerk_success = True
                                    if target_user.clerk_id:
                                        if not clerk.ban_user(target_user.clerk_id):
                                            st.warning(
                                                "⚠️ No se pudo banear en Clerk (o no existe),"
                                                " pero se bloqueará localmente.",
                                            )
                                            clerk_success = False

                                    # 2. Update DB Local
                                    target_user.is_active = False
                                    db_actions.commit()

                                    if clerk_success:
                                        st.success(
                                            "Usuario baneado en Clerk y DB local.",
                                        )
                                    else:
                                        st.success(
                                            "Usuario bloqueado localmente (Fallo en Clerk).",
                                        )

                                    time.sleep(1)
                                    st.rerun()
                            elif st.button(
                                "🟢 Desbloquear (Reactivar) Usuario",
                                type="secondary",
                                use_container_width=True,
                            ):
                                # 1. Unban in Clerk
                                clerk_success = True
                                if target_user.clerk_id:
                                    if not clerk.unban_user(target_user.clerk_id):
                                        st.warning(
                                            "⚠️ No se pudo desbanear en Clerk, pero se activará localmente.",
                                        )
                                        clerk_success = False

                                # 2. Update DB Local
                                target_user.is_active = True
                                db_actions.commit()

                                if clerk_success:
                                    st.success(
                                        "Usuario reactivado en Clerk y DB local.",
                                    )
                                else:
                                    st.success("Usuario reactivado localmente.")

                                time.sleep(1)
                                st.rerun()

                    # Action: Remove from Tenant (Soft-Delete)
                    with col_act3:
                        with st.container(border=True):
                            st.markdown("#### 🗑️ Eliminar del Tenant")
                            st.caption(
                                "Remueve al usuario de este tenant sin afectar su cuenta global ni otros tenants.",
                            )

                            # Check if this is the last active admin
                            active_admin_count = (
                                db_actions.query(UserTenant)
                                .filter(
                                    UserTenant.tenant_id == selected_tenant_id,
                                    UserTenant.role == "admin",
                                    UserTenant.is_active.is_(True),
                                )
                                .count()
                            )

                            # Get current user's role in this tenant
                            target_link = (
                                db_actions.query(UserTenant)
                                .filter(
                                    UserTenant.user_id == target_user.id,
                                    UserTenant.tenant_id == selected_tenant_id,
                                    UserTenant.is_active.is_(True),
                                )
                                .first()
                            )

                            is_last_admin = target_link and target_link.role == "admin" and active_admin_count <= 1

                            if is_last_admin:
                                st.warning(
                                    "⚠️ No se puede eliminar: es el ultimo admin activo de este tenant.",
                                )
                            else:
                                confirm_remove = st.checkbox(
                                    "Confirmo que quiero eliminar este usuario del tenant",
                                    key="confirm_remove_tenant",
                                )
                                if st.button(
                                    "🗑️ Eliminar del Tenant",
                                    type="primary",
                                    use_container_width=True,
                                    disabled=not confirm_remove,
                                ):
                                    if target_link:
                                        target_link.is_active = False
                                        db_actions.commit()
                                        st.success(
                                            f"✅ Usuario eliminado de {selected_tenant_name}."
                                            " Sus datos se preservan para auditoria.",
                                        )
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(
                                            "❌ No se encontro la relacion usuario-tenant.",
                                        )

            finally:
                db_actions.close()

    # --- TAB 2: CREATE / ASSIGN USER ---
    with tab_create:
        st.header(f"Nuevo Usuario para {selected_tenant_name}")
        st.info("Puede crear un nuevo usuario o asignar uno existente por su email.")

        with st.form("create_user_form_new"):
            col_new1, col_new2 = st.columns(2)
            with col_new1:
                new_email = st.text_input("Correo Electrónico (Obligatorio)")
                new_name = st.text_input("Nombre Completo (Solo para nuevos)")
            with col_new2:
                new_pass = st.text_input(
                    "Contraseña Inicial (Solo para nuevos)",
                    type="password",
                    help=(
                        "Solo aplica al crear usuarios nuevos. Para existentes,"
                        " use 'Cambiar Contraseña' en la pestaña de usuarios."
                    ),
                )
                new_role = st.selectbox(
                    "Rol en este Tenant",
                    ["admin", "member", "viewer"],
                    index=0,
                )

            submitted_create = st.form_submit_button("🚀 Crear o Asignar Usuario")

            if submitted_create:
                if not new_email:
                    st.error("❌ El email es obligatorio.")
                else:
                    db = SessionLocal()
                    clerk = ClerkService()

                    try:
                        # 1. Check if user exists locally
                        existing_user = db.query(User).filter(User.email == new_email).first()

                        if existing_user:
                            # --- ASSIGN EXISTING USER ---
                            st.info(
                                f"ℹ️ El usuario {new_email} ya existe. Intentando asignar a este tenant...",
                            )

                            # Check if already in tenant
                            existing_link = (
                                db.query(UserTenant)
                                .filter_by(
                                    user_id=existing_user.id,
                                    tenant_id=selected_tenant_id,
                                )
                                .first()
                            )

                            if existing_link and existing_link.is_active:
                                st.warning(
                                    f"⚠️ El usuario ya pertenece a este tenant con el rol: {existing_link.role}.",
                                )
                            elif existing_link and not existing_link.is_active:
                                # Reactivate inactive link
                                try:
                                    existing_link.is_active = True
                                    if new_role:
                                        existing_link.role = new_role
                                    db.commit()

                                    if existing_user.clerk_id:
                                        clerk.update_user_metadata(
                                            existing_user.clerk_id,
                                            {
                                                "tenant_id": str(selected_tenant_id),
                                                "role": existing_link.role,
                                            },
                                        )

                                    st.success(
                                        "✅ Usuario reactivado en"
                                        f" {selected_tenant_name} con rol: {existing_link.role}",
                                    )
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e_react:  # noqa: BLE001 — Streamlit UI error boundary
                                    db.rollback()
                                    st.error(
                                        f"❌ Error al reactivar usuario: {e_react}",
                                    )
                            else:
                                # Create Link
                                try:
                                    new_link = UserTenant(
                                        user_id=existing_user.id,
                                        tenant_id=selected_tenant_id,
                                        role=new_role,
                                    )
                                    db.add(new_link)
                                    db.commit()

                                    # Update Clerk metadata
                                    if existing_user.clerk_id:
                                        clerk.update_user_metadata(
                                            existing_user.clerk_id,
                                            {
                                                "tenant_id": str(selected_tenant_id),
                                                "role": new_role,
                                            },
                                        )

                                    # Warn if admin entered a password — it won't be used for existing users
                                    if new_pass:
                                        st.warning(
                                            "⚠️ La contraseña no se actualizó porque el usuario ya existe."
                                            " Use la sección 'Cambiar Contraseña'"
                                            " en la pestaña de usuarios.",
                                        )

                                    st.success(
                                        f"✅ Usuario existente asignado correctamente a {selected_tenant_name}!",
                                    )

                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e_link:  # noqa: BLE001 — Streamlit UI error boundary
                                    db.rollback()
                                    st.error(f"❌ Error al asignar usuario: {e_link}")

                        # --- CREATE NEW USER ---
                        elif not new_pass or not new_name:
                            st.error(
                                "❌ Para crear un usuario NUEVO, nombre y contraseña son obligatorios.",
                            )
                        else:
                            created_clerk_id = None
                            # 2. Create in Clerk
                            with st.spinner("Creando usuario en Clerk..."):
                                try:
                                    clerk_user = clerk.create_user(
                                        new_email,
                                        new_pass,
                                        new_name,
                                    )
                                    created_clerk_id = clerk_user.get("id")

                                    if created_clerk_id:
                                        clerk.update_user_metadata(
                                            created_clerk_id,
                                            {
                                                "tenant_id": str(selected_tenant_id),
                                                "role": new_role,
                                            },
                                        )

                                except Exception as e_clerk:
                                    if "ya existe" in str(e_clerk) or "already exists" in str(e_clerk).lower():
                                        st.warning(
                                            "⚠️ El usuario existe en Clerk pero no en DB Local. Intentando recuperar...",
                                        )
                                        u_clerk = clerk.get_user_by_email(new_email)
                                        if u_clerk:
                                            created_clerk_id = u_clerk.get("id")
                                            # Set the password the admin intended
                                            if new_pass and created_clerk_id:
                                                clerk.update_user_password(
                                                    created_clerk_id,
                                                    new_pass,
                                                )
                                    else:
                                        raise

                            # 3. Create in Local DB
                            if created_clerk_id:
                                try:
                                    new_db_user = User(
                                        full_name=new_name,
                                        email=new_email,
                                        clerk_id=created_clerk_id,
                                        role=new_role,
                                        is_active=True,
                                    )
                                    db.add(new_db_user)
                                    db.flush()

                                    # Link to Tenant
                                    new_link = UserTenant(
                                        user_id=new_db_user.id,
                                        tenant_id=selected_tenant_id,
                                        role=new_role,
                                    )
                                    db.add(new_link)
                                    db.commit()

                                    st.success(
                                        f"✅ Usuario {new_name} creado y asignado exitosamente!",
                                    )

                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as db_e:  # noqa: BLE001 — Streamlit UI error boundary
                                    db.rollback()
                                    st.error(f"❌ Error al guardar en DB Local: {db_e}")
                            else:
                                st.error("❌ No se pudo obtener ID de Clerk.")

                    except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                        st.error(f"❌ Error del proceso: {e!s}")
                    finally:
                        db.close()
