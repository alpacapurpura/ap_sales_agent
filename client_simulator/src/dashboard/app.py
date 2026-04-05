import streamlit as st
from pathlib import Path
import sys

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.database import init_db

st.set_page_config(
    page_title="Nicolify Client Simulator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB on first load
init_db()

st.title("Nicolify Client Simulator")
st.markdown("""
Simulador de clientes para testing del sales agent.

**Páginas:**
- **Personas** — CRUD de perfiles de clientes simulados
- **Escenarios** — Configuración de situaciones de venta
- **Runner** — Ejecutar simulaciones (single o batch)
- **Replay** — Visor de conversaciones
- **Evaluaciones** — Scores y heatmap de desempeño
- **Fallos** — Explorador de categorías de fallo

---
*Usa el menú lateral para navegar entre páginas.*
""")

# Show quick stats
from src.infrastructure.database import get_session
from src.infrastructure.repositories import (
    PersonaRepository,
    ScenarioRepository,
    SimulationRepository,
    EvaluationRepository,
)

session = get_session()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Personas", PersonaRepository(session).count())
with col2:
    st.metric("Escenarios", ScenarioRepository(session).count())
with col3:
    st.metric("Simulaciones", SimulationRepository(session).count())
with col4:
    st.metric("Evaluaciones", EvaluationRepository(session).count())
session.close()
