import asyncio
import uuid

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
from src.simulator.graph import run_simulation

st.set_page_config(page_title="Runner", page_icon="▶️", layout="wide")
st.title("▶️ Runner")

session = get_session()
persona_repo = PersonaRepository(session)
scenario_repo = ScenarioRepository(session)
sim_repo = SimulationRepository(session)

personas = persona_repo.list_all()
scenarios = scenario_repo.list_all()

if not personas or not scenarios:
    st.warning("Necesitas al menos 1 persona y 1 escenario. Ve a las páginas de Personas y Escenarios.")
    session.close()
    st.stop()

# --- Mode selection ---
mode = st.radio("Modo", ["Single", "Batch"], horizontal=True)

if mode == "Single":
    col1, col2 = st.columns(2)
    with col1:
        persona_names = {p.id: p.name for p in personas}
        selected_persona_id = st.selectbox(
            "Persona",
            options=[p.id for p in personas],
            format_func=lambda x: persona_names[x],
        )
    with col2:
        scenario_names = {s.id: s.name for s in scenarios}
        selected_scenario_id = st.selectbox(
            "Escenario",
            options=[s.id for s in scenarios],
            format_func=lambda x: scenario_names[x],
        )

    if st.button("🚀 Ejecutar Simulación", type="primary", use_container_width=True):
        persona = persona_repo.get(selected_persona_id)
        scenario = scenario_repo.get(selected_scenario_id)

        if persona and scenario:
            sim_id = f"sim_{uuid.uuid4().hex[:8]}"
            with st.spinner(f"Ejecutando simulación {sim_id}..."):
                result = asyncio.run(
                    run_simulation(
                        persona=persona.model_dump(),
                        scenario=scenario.model_dump(),
                        simulation_id=sim_id,
                    )
                )
                sim_repo.save(result)

            st.success(
                f"✅ Simulación completada: {len(result.turns)} turnos, "
                f"razón: {result.finish_reason.value if result.finish_reason else 'N/A'}"
            )

            # Quick preview
            with st.expander("Preview de la conversación"):
                for turn in result.turns:
                    if turn.role == "customer":
                        st.markdown(f"🧑 **Cliente:** {turn.content}")
                    else:
                        st.markdown(f"🤖 **Agente:** {turn.content}")

else:  # Batch mode
    st.subheader("Selecciona combinaciones Persona × Escenario")

    # Matrix selection
    selected_combos = []
    cols = st.columns(len(scenarios) + 1)
    cols[0].write("**Persona \\ Escenario**")
    for i, s in enumerate(scenarios):
        cols[i + 1].write(f"**{s.name[:15]}...**" if len(s.name) > 15 else f"**{s.name}**")

    for p in personas:
        cols = st.columns(len(scenarios) + 1)
        cols[0].write(p.name[:25])
        for i, s in enumerate(scenarios):
            key = f"batch_{p.id}_{s.id}"
            if cols[i + 1].checkbox("", key=key, label_visibility="collapsed"):
                selected_combos.append((p.id, s.id))

    st.write(f"**{len(selected_combos)} combinaciones seleccionadas**")

    max_parallel = st.slider("Paralelismo", 1, 10, 3)

    if st.button(
        "🚀 Ejecutar Batch", type="primary", disabled=len(selected_combos) == 0, use_container_width=True,
    ):
        progress = st.progress(0, text="Preparando...")
        status_area = st.empty()

        async def run_batch():
            semaphore = asyncio.Semaphore(max_parallel)
            results = []
            total = len(selected_combos)
            completed = 0

            async def run_one(persona_id, scenario_id):
                nonlocal completed
                async with semaphore:
                    persona = persona_repo.get(persona_id)
                    scenario = scenario_repo.get(scenario_id)
                    if not persona or not scenario:
                        return None
                    sim_id = f"sim_{uuid.uuid4().hex[:8]}"
                    result = await run_simulation(
                        persona=persona.model_dump(),
                        scenario=scenario.model_dump(),
                        simulation_id=sim_id,
                    )
                    sim_repo.save(result)
                    completed += 1
                    progress.progress(
                        completed / total,
                        text=f"Completada {completed}/{total}: {persona.name} × {scenario.name}",
                    )
                    return result

            tasks = [run_one(pid, sid) for pid, sid in selected_combos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if r and not isinstance(r, Exception)]

        results = asyncio.run(run_batch())
        st.success(f"✅ Batch completado: {len(results)} simulaciones ejecutadas")

session.close()
