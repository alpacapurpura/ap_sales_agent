import streamlit as st
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.domain.models import Persona
from src.domain.enums import Budget, Urgency, Expertise, CommunicationStyle
from src.infrastructure.database import get_session
from src.infrastructure.repositories import PersonaRepository

st.set_page_config(page_title="Personas", page_icon="👤", layout="wide")
st.title("👤 Personas")

session = get_session()
repo = PersonaRepository(session)


# --- Seed loader ---
def load_seeds():
    seed_path = Path(__file__).parent.parent.parent.parent / "src" / "seeds" / "personas.yaml"
    if not seed_path.exists():
        st.error(f"Seed file not found: {seed_path}")
        return
    with open(seed_path) as f:
        data = yaml.safe_load(f)
    count = 0
    for item in data:
        persona = Persona(**item)
        repo.save(persona)
        count += 1
    st.success(f"✅ {count} personas importadas")
    st.rerun()


col1, col2 = st.columns([3, 1])
with col2:
    if st.button("📥 Importar Seeds", use_container_width=True):
        load_seeds()

# --- List existing personas ---
personas = repo.list_all()

if not personas:
    st.info("No hay personas. Importa los seeds o crea una nueva.")
else:
    for p in personas:
        with st.expander(f"**{p.name}** — {p.demographics} | {p.budget.value} | {p.urgency.value}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**ID:** `{p.id}`")
                st.write(f"**Estilo:** {p.communication_style.value}")
                st.write(f"**Expertise:** {p.expertise.value}")
                st.write(f"**Objetivo oculto:** {p.hidden_goal}")
            with col_b:
                st.write("**Pain Points:**")
                for pp in p.pain_points:
                    st.write(f"  - {pp}")
                st.write("**Objeciones:**")
                st.write(", ".join(p.objection_tendency))
                st.write("**Triggers:**")
                st.write(", ".join(p.triggers))

            if st.button(f"🗑️ Eliminar {p.id}", key=f"del_{p.id}"):
                repo.delete(p.id)
                st.rerun()

# --- Create new persona ---
st.divider()
st.subheader("Crear Nueva Persona")

with st.form("new_persona"):
    pid = st.text_input("ID", placeholder="persona_custom_01")
    name = st.text_input("Nombre", placeholder="Clara - Coach Fitness")
    demographics = st.text_input("Demografía", placeholder="30 años, coach fitness, Lima")
    budget = st.selectbox("Presupuesto", [b.value for b in Budget])
    urgency = st.selectbox("Urgencia", [u.value for u in Urgency])
    expertise = st.selectbox("Expertise", [e.value for e in Expertise])
    comm_style = st.selectbox("Estilo de comunicación", [c.value for c in CommunicationStyle])
    hidden_goal = st.text_area("Objetivo oculto")
    pain_points = st.text_area("Pain points (uno por línea)")
    objections = st.text_input("Objeciones (separadas por coma)")
    triggers = st.text_input("Triggers (separados por coma)")
    traits = st.text_input("Rasgos de personalidad (separados por coma)")

    if st.form_submit_button("Crear Persona"):
        if pid and name:
            persona = Persona(
                id=pid,
                name=name,
                demographics=demographics,
                budget=Budget(budget),
                urgency=Urgency(urgency),
                expertise=Expertise(expertise),
                communication_style=CommunicationStyle(comm_style),
                hidden_goal=hidden_goal,
                pain_points=[p.strip() for p in pain_points.split("\n") if p.strip()],
                objection_tendency=[o.strip() for o in objections.split(",") if o.strip()],
                triggers=[t.strip() for t in triggers.split(",") if t.strip()],
                personality_traits=[t.strip() for t in traits.split(",") if t.strip()],
            )
            repo.save(persona)
            st.success(f"✅ Persona '{name}' creada")
            st.rerun()
        else:
            st.error("ID y Nombre son requeridos")

session.close()
