import streamlit as st
import pandas as pd
import time
from sqlalchemy.exc import IntegrityError
from src.services.database import SessionLocal
from src.services.db.models.user import User
from src.services.db.models.tenant import Tenant
from src.services.clerk import ClerkService

def get_tenants():
    """Fetch all active tenants for the dropdown."""
    db = SessionLocal()
    try:
        return db.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.name).all()
    finally:
        db.close()

def get_users(tenant_id):
    """Fetch users belonging to a specific tenant."""
    db = SessionLocal()
    try:
        return db.query(User).filter(User.tenant_id == tenant_id).order_by(User.created_at.desc()).all()
    finally:
        db.close()

def render_users_view():
    st.title("👥 Gestión de Usuarios")

    # 1. Select Tenant
    tenants = get_tenants()
    if not tenants:
        st.warning("⚠️ No hay tenants activos. Cree un tenant primero en la sección de Tenants.")
        return

    # Tenant Selection Logic
    tenant_options = {t.name: t.id for t in tenants}
    
    # Use columns for better layout
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_tenant_name = st.selectbox("🏢 Seleccionar Tenant", list(tenant_options.keys()))
    
    selected_tenant_id = tenant_options[selected_tenant_name]
    
    # Display current tenant info
    current_tenant = next((t for t in tenants if t.id == selected_tenant_id), None)
    if current_tenant:
        st.caption(f"Gestión de usuarios para: **{current_tenant.name}** ({current_tenant.slug})")

    st.divider()

    # Tabs for organized view
    tab_list, tab_create = st.tabs(["📋 Lista de Usuarios", "➕ Crear Nuevo Usuario"])

    # --- TAB 1: LIST USERS ---
    with tab_list:
        users = get_users(selected_tenant_id)
        
        if not users:
            st.info(f"ℹ️ No hay usuarios registrados para {selected_tenant_name}.")
        else:
            # Prepare Data for Table
            data = []
            for u in users:
                data.append({
                    "ID": str(u.id),
                    "Nombre": u.full_name,
                    "Email": u.email,
                    "Rol": u.role,
                    "Estado": "✅ Activo" if u.is_active else "🚫 Bloqueado",
                    "Clerk ID": u.clerk_id,
                    "Creado": u.created_at.strftime("%Y-%m-%d")
                })
            
            df = pd.DataFrame(data)
            st.dataframe(
                df, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Email": st.column_config.TextColumn("Email", width="medium"),
                    "Estado": st.column_config.TextColumn("Estado", width="small"),
                }
            )
            st.caption(f"Total: {len(users)} usuarios")

            # --- ACTIONS SECTION ---
            st.divider()
            st.subheader("🔧 Acciones de Usuario")
            
            # User Selector for Actions
            user_options_map = {f"{u.full_name or 'Sin Nombre'} ({u.email})": u.id for u in users}
            selected_user_label = st.selectbox("Seleccionar Usuario para modificar", list(user_options_map.keys()))
            selected_user_id = user_options_map[selected_user_label]

            # Fetch fresh user object for actions
            db = SessionLocal()
            target_user = db.query(User).filter(User.id == selected_user_id).first()
            
            if target_user:
                col_act1, col_act2 = st.columns(2)
                
                # Action: Change Password
                with col_act1:
                    with st.container(border=True):
                        st.markdown("#### 🔐 Cambiar Contraseña")
                        with st.form("change_pwd_form"):
                            new_pass = st.text_input("Nueva Contraseña", type="password", help="Mínimo 8 caracteres")
                            submit_pass = st.form_submit_button("Actualizar Password")
                            
                            if submit_pass:
                                if not new_pass or len(new_pass) < 8:
                                    st.error("La contraseña debe tener al menos 8 caracteres.")
                                elif not target_user.clerk_id:
                                    st.error("❌ Este usuario no tiene Clerk ID vinculado. No se puede cambiar password.")
                                else:
                                    clerk = ClerkService()
                                    try:
                                        if clerk.update_user_password(target_user.clerk_id, new_pass):
                                            st.success("✅ Contraseña actualizada exitosamente en Clerk.")
                                        else:
                                            st.error("❌ Error al actualizar en Clerk. Verifique logs (Posible password débil o pwned).")
                                    except Exception as e:
                                        st.error(f"❌ Error Clerk: {e}")

                # Action: Block/Unblock
                with col_act2:
                    with st.container(border=True):
                        st.markdown("#### 🚫 Gestión de Acceso")
                        status_label = "Activo" if target_user.is_active else "Bloqueado"
                        status_color = "green" if target_user.is_active else "red"
                        st.markdown(f"Estado Actual: :{status_color}[**{status_label}**]")
                        
                        clerk = ClerkService()
                        
                        if target_user.is_active:
                            if st.button("🔴 Bloquear (Banear) Usuario", type="primary", use_container_width=True):
                                # 1. Ban in Clerk
                                clerk_success = True
                                if target_user.clerk_id:
                                    if not clerk.ban_user(target_user.clerk_id):
                                        st.warning("⚠️ No se pudo banear en Clerk (o no existe), pero se bloqueará localmente.")
                                        clerk_success = False
                                
                                # 2. Update DB Local
                                target_user.is_active = False
                                db.commit()
                                
                                if clerk_success:
                                    st.success("Usuario baneado en Clerk y DB local.")
                                else:
                                    st.success("Usuario bloqueado localmente (Fallo en Clerk).")
                                    
                                time.sleep(1)
                                st.rerun()
                        else:
                            if st.button("🟢 Desbloquear (Reactivar) Usuario", type="secondary", use_container_width=True):
                                # 1. Unban in Clerk
                                clerk_success = True
                                if target_user.clerk_id:
                                    if not clerk.unban_user(target_user.clerk_id):
                                        st.warning("⚠️ No se pudo desbanear en Clerk, pero se activará localmente.")
                                        clerk_success = False
                                
                                # 2. Update DB Local
                                target_user.is_active = True
                                db.commit()
                                
                                if clerk_success:
                                    st.success("Usuario reactivado en Clerk y DB local.")
                                else:
                                    st.success("Usuario reactivado localmente.")
                                    
                                time.sleep(1)
                                st.rerun()
            db.close()

    # --- TAB 2: CREATE USER ---
    with tab_create:
        st.header(f"Nuevo Usuario para {selected_tenant_name}")
        st.info("El usuario se creará en Clerk (Auth) y en la Base de Datos local.")
        
        with st.form("create_user_form_new"):
            col_new1, col_new2 = st.columns(2)
            with col_new1:
                new_name = st.text_input("Nombre Completo")
                new_email = st.text_input("Correo Electrónico")
            with col_new2:
                new_pass = st.text_input("Contraseña Inicial", type="password")
                new_role = st.selectbox("Rol", ["admin", "member", "viewer"], index=0)

            submitted_create = st.form_submit_button("🚀 Crear Usuario")
            
            if submitted_create:
                if not new_name or not new_email or not new_pass:
                    st.error("❌ Todos los campos son obligatorios.")
                else:
                    db = SessionLocal()
                    clerk = ClerkService()
                    created_clerk_id = None
                    
                    try:
                        # 1. Check Local DB first
                        existing_user = db.query(User).filter(User.email == new_email).first()
                        if existing_user:
                            st.error(f"❌ El usuario {new_email} ya existe en la base de datos local (Tenant: {existing_user.tenant_id}).")
                            db.close()
                        else:
                            # 2. Create in Clerk
                            with st.spinner("Creando usuario en Clerk..."):
                                try:
                                    # Create user returns Dict
                                    clerk_user = clerk.create_user(new_email, new_pass, new_name)
                                    created_clerk_id = clerk_user.get("id")
                                    
                                    # Update Metadata immediately
                                    if created_clerk_id:
                                        clerk.update_user_metadata(created_clerk_id, {
                                            "tenant_id": str(selected_tenant_id),
                                            "role": new_role
                                        })
                                        
                                except Exception as e_clerk:
                                    # Handle "User already exists" gracefully if needed, but for now we treat as error
                                    if "ya existe" in str(e_clerk):
                                        st.warning("⚠️ El usuario ya existía en Clerk. Intentando vincular localmente...")
                                        # Fetch ID
                                        u_clerk = clerk.get_user_by_email(new_email)
                                        if u_clerk:
                                            created_clerk_id = u_clerk.get("id")
                                            # Update metadata
                                            clerk.update_user_metadata(created_clerk_id, {
                                                "tenant_id": str(selected_tenant_id),
                                                "role": new_role
                                            })
                                    else:
                                        raise e_clerk

                            # 3. Create in Local DB (Atomic Transaction)
                            if created_clerk_id:
                                try:
                                    new_db_user = User(
                                        full_name=new_name,
                                        email=new_email,
                                        clerk_id=created_clerk_id,
                                        role=new_role,
                                        tenant_id=selected_tenant_id,
                                        is_active=True
                                    )
                                    db.add(new_db_user)
                                    db.commit()
                                    st.success(f"✅ Usuario {new_name} creado exitosamente!")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as db_e:
                                    # ROLLBACK CLERK IF DB FAILS
                                    db.rollback()
                                    st.error(f"❌ Error al guardar en DB Local: {db_e}")
                                    st.warning("🔄 Revirtiendo creación en Clerk (Eliminando usuario)...")
                                    
                                    if clerk.delete_user(created_clerk_id):
                                        st.info("✅ Rollback exitoso: Usuario eliminado de Clerk.")
                                    else:
                                        st.error("⚠️ Falló el Rollback en Clerk. El usuario quedó huérfano en Clerk.")
                            else:
                                st.error("❌ No se pudo obtener el ID de Clerk.")
                                
                    except Exception as e:
                        st.error(f"❌ Error del proceso: {str(e)}")
                    finally:
                        db.close()
