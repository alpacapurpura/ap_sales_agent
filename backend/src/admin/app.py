import os
import sys

import streamlit as st

# Add project root to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# --- Bootstrap all models so SQLAlchemy mapper resolves cross-module relationships ---
import src.shared.infrastructure.model_registry  # noqa: F401
from src.admin.modules.tenants import render_tenants_view
from src.admin.modules.users import render_users_view

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=os.getenv("ADMIN_TITLE", "SaaS Admin Panel"),
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS STYLES ---
st.markdown(
    """
<style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def main():
    st.sidebar.title("🛠️ Panel Admin")
    st.sidebar.caption(f"Env: {os.getenv('PROFILE', 'dev')}")
    st.sidebar.divider()

    menu_options = {
        "🎯 Comando Central": "home",
        "🏥 Salud de Tenants": "health",
        "🧠 Inteligencia Copilot": "events",
        "💬 Conversaciones": "conversations",
        "🔍 Auditoría Sales Agent": "sales_audit",
        "📚 Knowledge Base": "knowledge",
        "🔧 Capacidades Copilot": "capabilities",
        "📅 Calendario Comercial": "commercial_calendar",
        "🏢 Tenants (Clientes)": "tenants",
        "👥 Usuarios": "users",
    }

    selection = st.sidebar.radio(
        "Navegación",
        list(menu_options.keys()),
        index=0,
    )

    page = menu_options[selection]

    if page == "home":
        from src.admin.modules.home_dashboard import render_home_dashboard

        render_home_dashboard()
    elif page == "health":
        from src.admin.modules.tenant_health import render_tenant_health

        render_tenant_health()
    elif page == "events":
        from src.admin.modules.events import render_events_page

        render_events_page()
    elif page == "conversations":
        from src.admin.modules.conversations import render_conversations_page

        render_conversations_page()
    elif page == "sales_audit":
        from src.admin.modules.sales_audit import render_sales_audit_page

        render_sales_audit_page()
    elif page == "knowledge":
        from src.admin.modules.knowledge import render_knowledge_page

        render_knowledge_page()
    elif page == "capabilities":
        from src.admin.modules.capability_catalog import render_capability_catalog

        render_capability_catalog()
    elif page == "commercial_calendar":
        from src.admin.modules.commercial_calendar import (
            render_commercial_calendar_page,
        )

        render_commercial_calendar_page()
    elif page == "tenants":
        render_tenants_view()
    elif page == "users":
        render_users_view()


if __name__ == "__main__":
    main()
