import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.domain.enums import FailureCategory
from src.infrastructure.database import get_session
from src.infrastructure.repositories import (
    EvaluationRepository,
    PersonaRepository,
    ScenarioRepository,
    SimulationRepository,
)

st.set_page_config(page_title="Fallos", page_icon="⚠️", layout="wide")
st.title("⚠️ Explorador de Fallos")

session = get_session()
eval_repo = EvaluationRepository(session)
sim_repo = SimulationRepository(session)
persona_repo = PersonaRepository(session)
scenario_repo = ScenarioRepository(session)

evaluations = eval_repo.list_all()

if not evaluations:
    st.info("No hay evaluaciones. Ejecuta simulaciones y evalúalas primero.")
    session.close()
    st.stop()

personas_map = {p.id: p for p in persona_repo.list_all()}
scenarios_map = {s.id: s for s in scenario_repo.list_all()}

# --- Filters ---
col1, col2, col3 = st.columns(3)

with col1:
    all_failure_cats = sorted({fc.value for ev in evaluations for fc in ev.failure_categories})
    selected_categories = st.multiselect(
        "Categoría de fallo",
        options=all_failure_cats,
        default=all_failure_cats,
    )

with col2:
    persona_options = ["Todas"] + [p.name for p in personas_map.values()]
    selected_persona = st.selectbox("Persona", persona_options)

with col3:
    score_range = st.slider("Score máximo", 0.0, 10.0, 10.0, 0.5)

# --- Filter evaluations ---
filtered = []
for ev in evaluations:
    # Category filter
    ev_cats = {fc.value for fc in ev.failure_categories}
    if selected_categories and not ev_cats.intersection(selected_categories):
        continue

    # Score filter
    if ev.overall_score > score_range:
        continue

    # Persona filter
    if selected_persona != "Todas":
        sim = sim_repo.get(ev.simulation_id)
        if sim:
            persona = personas_map.get(sim.persona_id)
            if persona and persona.name != selected_persona:
                continue

    filtered.append(ev)

st.write(f"**{len(filtered)} evaluaciones con fallos encontradas**")
st.divider()

# --- Results ---
for ev in filtered:
    sim = sim_repo.get(ev.simulation_id)
    if not sim:
        continue

    persona = personas_map.get(sim.persona_id)
    scenario = scenarios_map.get(sim.scenario_id)
    persona_label = persona.name if persona else sim.persona_id
    scenario_label = scenario.name if scenario else sim.scenario_id

    failure_tags = " | ".join(f"`{fc.value}`" for fc in ev.failure_categories)

    with st.expander(
        f"**{ev.overall_score}/10** — {persona_label} × {scenario_label} — {failure_tags}"
    ):
        # Summary
        st.write(f"**Resumen:** {ev.summary}")

        # Score details
        st.write("**Scores por dimensión:**")
        for score in ev.scores:
            color = "🟢" if score.score >= 7 else "🟡" if score.score >= 4 else "🔴"
            st.write(f"{color} **{score.dimension}:** {score.score}/10 — {score.reasoning}")

        # Conversation replay
        st.divider()
        st.write("**Conversación:**")
        for turn in sim.turns:
            if turn.role == "customer":
                with st.chat_message("user"):
                    st.write(turn.content)
            else:
                with st.chat_message("assistant"):
                    st.write(turn.content)

session.close()
