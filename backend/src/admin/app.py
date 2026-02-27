import streamlit as st
import os
import sys

# Add project root to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# --- BOOTSTRAP MODELS (CRITICAL) ---
# Import all models to ensure SQLAlchemy Registry is fully populated before any query

from src.admin.modules.tenants import render_tenants_view
from src.admin.modules.users import render_users_view

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=os.getenv("ADMIN_TITLE", "SaaS Admin Panel"),
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLES ---
st.markdown("""
<style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("🛠️ Panel Admin")
    st.sidebar.caption(f"Env: {os.getenv('PROFILE', 'dev')}")
    st.sidebar.divider()

    # Navigation
    menu_options = {
        "🏢 Tenants (Clientes)": "tenants",
        "👥 Usuarios": "users"
    }
    
    selection = st.sidebar.radio(
        "Navegación",
        list(menu_options.keys()),
        index=0
    )
    
    page = menu_options[selection]

    # Router
    if page == "tenants":
        render_tenants_view()
    elif page == "users":
        render_users_view()

if __name__ == "__main__":
    main()
