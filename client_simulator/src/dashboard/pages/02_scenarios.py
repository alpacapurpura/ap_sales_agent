import streamlit as st
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.domain.models import Scenario
from src.domain.enums import ExpectedOutcome, Difficulty
from src.infrastructure.database import get_session
from src.infrastructure.repositories import ScenarioRepository

st.set_page_config(page_title="Escenarios", page_icon="🎬", layout="wide")
st.title("🎬 Escenarios")

session = get_session()
repo = ScenarioRepository(session)


def load_seeds():
    seed_path = Path(__file__).parent.parent.parent.parent / "src" / "seeds" / "scenarios.yaml"
    if not seed_path.exists():
        st.error(f"Seed file not found: {seed_path}")
        return
    with open(seed_path) as f:
        data = yaml.safe_load(f)
    count = 0
    for item in data:
        scenario = Scenario(**item)
        repo.save(scenario)
        count += 1
    st.success(f"✅ {count} escenarios importados")
    st.rerun()


col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📥 Importar Seeds", use_container_width=True):
        load_seeds()

# --- List ---
scenarios = repo.list_all()

if not scenarios:
    st.info("No hay escenarios. Importa los seeds o crea uno nuevo.")
else:
    for s in scenarios:
        with st.expander(
            f"**{s.name}** — {s.entry_channel} | {s.expected_outcome.value} | {s.difficulty.value}"
        ):
            st.write(f"**ID:** `{s.id}`")
            st.write(f"**Mensaje inicial:** {s.initial_message}")
            if s.campaign_name:
                st.write(f"**Campaña:** {s.campaign_name}")
            st.write(f"**Max turnos:** {s.max_turns}")
            if s.context_instructions:
                st.write(f"**Contexto:** {s.context_instructions}")

            if st.button(f"🗑️ Eliminar {s.id}", key=f"del_{s.id}"):
                repo.delete(s.id)
                st.rerun()

# --- Create ---
st.divider()
st.subheader("Crear Nuevo Escenario")

with st.form("new_scenario"):
    sid = st.text_input("ID", placeholder="scenario_custom_01")
    name = st.text_input("Nombre", placeholder="Llegó por LinkedIn")
    entry_channel = st.text_input("Canal de entrada", placeholder="linkedin")
    campaign_name = st.text_input("Nombre de campaña (opcional)")
    initial_message = st.text_area("Mensaje inicial del cliente")
    expected_outcome = st.selectbox("Resultado esperado", [o.value for o in ExpectedOutcome])
    max_turns = st.number_input("Máximo de turnos", value=20, min_value=3, max_value=50)
    difficulty = st.selectbox("Dificultad", [d.value for d in Difficulty])
    context_instructions = st.text_area("Instrucciones de contexto (opcional)")

    if st.form_submit_button("Crear Escenario"):
        if sid and name and initial_message:
            scenario = Scenario(
                id=sid,
                name=name,
                entry_channel=entry_channel,
                campaign_name=campaign_name or None,
                initial_message=initial_message,
                expected_outcome=ExpectedOutcome(expected_outcome),
                max_turns=int(max_turns),
                difficulty=Difficulty(difficulty),
                context_instructions=context_instructions,
            )
            repo.save(scenario)
            st.success(f"✅ Escenario '{name}' creado")
            st.rerun()
        else:
            st.error("ID, Nombre y Mensaje inicial son requeridos")

session.close()
