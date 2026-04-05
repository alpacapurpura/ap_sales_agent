import asyncio

import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.database import get_session
from src.infrastructure.repositories import (
    EvaluationRepository,
    PersonaRepository,
    ScenarioRepository,
    SimulationRepository,
)
from src.evaluation.judge import evaluate_simulation
from src.evaluation.aggregator import aggregate_scores, build_heatmap_data, count_failures
from src.evaluation.rubrics import EVALUATION_DIMENSIONS

st.set_page_config(page_title="Evaluaciones", page_icon="📊", layout="wide")
st.title("📊 Evaluaciones")

session = get_session()
sim_repo = SimulationRepository(session)
eval_repo = EvaluationRepository(session)
persona_repo = PersonaRepository(session)
scenario_repo = ScenarioRepository(session)

# --- Run evaluations on unevaluated simulations ---
simulations = sim_repo.list_all()
completed_sims = [s for s in simulations if s.status.value == "completed"]
evaluated_sim_ids = {ev.simulation_id for ev in eval_repo.list_all()}
unevaluated = [s for s in completed_sims if s.id not in evaluated_sim_ids]

if unevaluated:
    st.info(f"{len(unevaluated)} simulaciones sin evaluar")
    if st.button(f"🧠 Evaluar {len(unevaluated)} simulaciones", type="primary"):
        personas_map = {p.id: p for p in persona_repo.list_all()}
        scenarios_map = {s.id: s for s in scenario_repo.list_all()}

        progress = st.progress(0)

        async def evaluate_all():
            for i, sim in enumerate(unevaluated):
                persona = personas_map.get(sim.persona_id)
                scenario = scenarios_map.get(sim.scenario_id)
                if persona and scenario:
                    ev = await evaluate_simulation(
                        simulation=sim,
                        persona=persona.model_dump(),
                        scenario=scenario.model_dump(),
                    )
                    eval_repo.save(ev)
                progress.progress((i + 1) / len(unevaluated))

        asyncio.run(evaluate_all())
        st.success("✅ Evaluaciones completadas")
        st.rerun()

# --- Display evaluations ---
evaluations = eval_repo.list_all()

if not evaluations:
    st.info("No hay evaluaciones aún. Ejecuta simulaciones y evalúalas.")
    session.close()
    st.stop()

# --- Aggregate stats ---
agg = aggregate_scores(evaluations)
st.subheader(f"Score General: {agg['overall']}/10 ({agg['count']} evaluaciones)")

# Dimension breakdown
dim_display = {d["name"]: d["display"] for d in EVALUATION_DIMENSIONS}
cols = st.columns(len(agg["dimensions"]))
for i, (dim, stats) in enumerate(agg["dimensions"].items()):
    with cols[i % len(cols)]:
        label = dim_display.get(dim, dim)
        st.metric(label, f"{stats['mean']}/10", help=f"Min: {stats['min']}, Max: {stats['max']}")

st.divider()

# --- Heatmap ---
st.subheader("Heatmap: Persona × Dimensión")

personas_map = {p.id: p for p in persona_repo.list_all()}
sim_persona_map = {}
for sim in simulations:
    sim_persona_map[sim.id] = sim.persona_id
persona_names = {pid: p.name for pid, p in personas_map.items()}

heatmap = build_heatmap_data(evaluations, sim_persona_map, persona_names)

if heatmap["personas"] and heatmap["dimensions"]:
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap["z"],
            x=[dim_display.get(d, d) for d in heatmap["dimensions"]],
            y=heatmap["personas"],
            colorscale="RdYlGn",
            zmin=0,
            zmax=10,
            text=heatmap["z"],
            texttemplate="%{text}",
            textfont={"size": 12},
        )
    )
    fig.update_layout(
        height=max(400, len(heatmap["personas"]) * 50),
        xaxis_title="Dimensión",
        yaxis_title="Persona",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Datos insuficientes para generar heatmap")

# --- Failure counts ---
st.divider()
st.subheader("Categorías de Fallos")

failures = count_failures(evaluations)
if failures:
    fig_bar = go.Figure(
        data=go.Bar(
            x=list(failures.keys()),
            y=list(failures.values()),
            marker_color="#ff6b6b",
        )
    )
    fig_bar.update_layout(
        xaxis_title="Categoría",
        yaxis_title="Cantidad",
        height=350,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.success("No se detectaron fallos")

# --- Per-simulation detail ---
st.divider()
st.subheader("Detalle por Simulación")

for ev in evaluations:
    sim = sim_repo.get(ev.simulation_id)
    persona_name = persona_names.get(sim.persona_id, sim.persona_id) if sim else ev.simulation_id
    with st.expander(f"**{ev.simulation_id}** — {persona_name} — Score: {ev.overall_score}/10"):
        for score in ev.scores:
            label = dim_display.get(score.dimension, score.dimension)
            st.write(f"**{label}:** {score.score}/10 — {score.reasoning}")
        if ev.failure_categories:
            st.write(f"**Fallos:** {', '.join(f.value for f in ev.failure_categories)}")
        st.write(f"**Resumen:** {ev.summary}")

session.close()
