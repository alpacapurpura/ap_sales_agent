import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.database import get_session
from src.infrastructure.repositories import (
    PersonaRepository,
    ScenarioRepository,
    SimulationRepository,
)

st.set_page_config(page_title="Replay", page_icon="💬", layout="wide")
st.title("💬 Replay de Conversaciones")

session = get_session()
sim_repo = SimulationRepository(session)
persona_repo = PersonaRepository(session)
scenario_repo = ScenarioRepository(session)

simulations = sim_repo.list_all()

if not simulations:
    st.info("No hay simulaciones. Ejecuta una desde el Runner.")
    session.close()
    st.stop()

# Build lookup maps
personas = {p.id: p for p in persona_repo.list_all()}
scenarios = {s.id: s for s in scenario_repo.list_all()}

# Simulation selector
sim_options = {}
for sim in simulations:
    persona_name = personas.get(sim.persona_id, None)
    persona_label = persona_name.name if persona_name else sim.persona_id
    scenario_name = scenarios.get(sim.scenario_id, None)
    scenario_label = scenario_name.name if scenario_name else sim.scenario_id
    status = sim.status.value
    label = f"{sim.id} | {persona_label} × {scenario_label} | {status} | {len(sim.turns)} turnos"
    sim_options[sim.id] = label

selected_sim_id = st.selectbox(
    "Selecciona simulación",
    options=list(sim_options.keys()),
    format_func=lambda x: sim_options[x],
)

sim = sim_repo.get(selected_sim_id)
if not sim:
    st.error("Simulación no encontrada")
    session.close()
    st.stop()

# --- Metadata ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Turnos", len(sim.turns))
with col2:
    st.metric("Status", sim.status.value)
with col3:
    st.metric("Razón fin", sim.finish_reason.value if sim.finish_reason else "N/A")
with col4:
    duration = ""
    if sim.started_at and sim.completed_at:
        delta = sim.completed_at - sim.started_at
        duration = f"{delta.total_seconds():.0f}s"
    st.metric("Duración", duration or "N/A")

st.divider()

# --- Chat bubbles ---
for turn in sim.turns:
    if turn.role == "customer":
        with st.chat_message("user"):
            st.markdown(turn.content)
            st.caption(f"Turno {turn.turn_number} | {turn.timestamp.strftime('%H:%M:%S')}")
    else:
        with st.chat_message("assistant"):
            st.markdown(turn.content)
            st.caption(f"Turno {turn.turn_number} | {turn.timestamp.strftime('%H:%M:%S')}")

# --- Export ---
st.divider()
if st.button("📋 Exportar conversación (JSON)"):
    import json

    export = {
        "simulation_id": sim.id,
        "persona_id": sim.persona_id,
        "scenario_id": sim.scenario_id,
        "status": sim.status.value,
        "finish_reason": sim.finish_reason.value if sim.finish_reason else None,
        "turns": [
            {"turn": t.turn_number, "role": t.role, "content": t.content}
            for t in sim.turns
        ],
    }
    st.json(export)

session.close()
