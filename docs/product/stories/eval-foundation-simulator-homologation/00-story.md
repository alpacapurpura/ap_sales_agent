---
story_id: eval-foundation-simulator-homologation
type: service-story
subtype: refactor-homologation
module: sales_agent
capability: sales-conversational-engine  # eval suite infrastructure
estimate: 2-3d
priority: 2  # post tenant-seed
links:
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  pre_requisite: "../eval-foundation-tenant-seed-data/checkpoint.md"
  legacy_simulator: "../../../../client_simulator/"
  target_path: "backend/tests/agentic_evals/sales_agent/simulator/"
  consumers:
    - "../sales-agent-personas-instrumented-runtime/"
    - "../sales-agent-goldens-3-tenants-dataset/"
---

# Story — Eval Foundation B: Homologar `client_simulator/` a estructura backend canónica

## Job-To-Be-Done

**Como** equipo eval que va a generar conversaciones simuladas para producir goldens + correr CI gate
**Quiero** que el simulator dual-LLM (1 LLM = user persona, 1 LLM = sales_agent real) viva DENTRO de `backend/tests/agentic_evals/sales_agent/simulator/` (no como proyecto raíz paralelo `client_simulator/`)
**Para** que el runner existente (`backend/tests/agentic_evals/sales_agent/runner/`) consuma el simulator nativamente, los tests corran con `pytest` sin Docker compose extra, y el código siga DDD del backend

## Por qué importa

Hoy hay **3 silos no conectados**:

1. `client_simulator/` (raíz) — proyecto Python paralelo con LangGraph dual-LLM, judge, rubrics. Incompleto, ~1 mes sin tocar, NUNCA probado en runtime.
2. `backend/tests/agentic_evals/sales_agent/runner/` — runner + golden_loader + assertions + trajectory_spy. Funciona con 1 smoke golden hardcoded.
3. `docs/specs/personas/` + `docs/specs/rubrics/` — YAMLs canónicas pero no instrumentables sin código que las cargue.

Sin homologación, no podemos:
- Correr simulaciones tenant×persona en CI (`client_simulator/` necesita Docker compose propio)
- Generar goldens automáticamente desde transcripts simulados
- Wirear MAJ-EVAL judges contra trayectorias del simulator
- Tener trazabilidad: simulator output → runner consume → judge evalúa → golden checked-in

Esta story hace los 3 silos **uno**. Sin ella, el resto de la sub-épica eval-foundation-* no escala.

## Outcome esperado

### Estructura final

```
backend/tests/agentic_evals/sales_agent/
├── runner/                            # ya existe — preservar
│   ├── golden_loader.py
│   ├── assertions.py
│   ├── trajectory_spy.py
│   ├── regenerate_golden.py
│   └── artifacts.py
├── simulator/                         # NEW — homologado desde client_simulator/
│   ├── __init__.py
│   ├── customer_node.py               # LLM = user persona (LangGraph node)
│   ├── agent_bridge.py                # LLM = sales_agent runtime (real, no mock)
│   ├── graph.py                       # LangGraph graph compose customer_node ↔ agent_bridge
│   ├── state.py                       # SimulationState (messages + persona + tenant + termination)
│   ├── termination.py                 # criterios: goal_completion | max_turns | adversarial_detected
│   └── actor_profile.py               # ActorProfile schema (Strands pattern: traits + context + actor_goal)
├── fixtures/                          # ya existe — extender
│   ├── synthetic_tenant.py            # ya existe — extender para los 3 archetypes seed
│   ├── persona_loader.py              # NEW — carga docs/specs/personas/*.yaml a ActorProfile
│   └── conftest.py                    # fixture orquestador
├── goldens/                           # ya existe — placeholder
└── test_simulator_smoke.py            # NEW — corre 1 simulación tenant_coach_lat × lead-frio-impaciente, verifica termination + transcript no vacío
```

### Migración del legacy `client_simulator/`

- **Mantener:** `client_simulator/` raíz **NO se elimina** — queda como dashboard/standalone tooling para evolución futura (ej. eval suite UI). Solo se reusa el código de simulator/* migrándolo (no copiándolo) a `backend/tests/agentic_evals/sales_agent/simulator/`.
- **Refactor:** los archivos `customer_node.py`, `agent_bridge.py`, `graph.py`, `state.py`, `termination.py` se MUEVEN a `backend/tests/agentic_evals/sales_agent/simulator/` con git mv (R9 — separar mv de scope expansion en commits distintos).
- **Adapter agent_bridge:** el `agent_bridge.py` debe llamar al `sales_agent` runtime REAL (no mockear). Carga el módulo via import absoluto + invoca `LangGraphRunner` o equivalente con `tenant_id` injected desde fixture.
- **Eval/Judge:** los archivos `client_simulator/src/evaluation/{judge.py,aggregator.py,rubrics.py}` se EVALÚAN per story E (voice-fidelity-grader-runtime) — NO en esta story (esta solo wirea simulator, no graders).

### Capability link

- Story bumpea `capability: sales-conversational-engine` con campo `eval.simulator_path: "backend/tests/agentic_evals/sales_agent/simulator/"` + `eval.dual_llm_pattern: true`

## Antecedentes / Contexto

- **Origen:** discovery 2026-05-06 — Chris reveló existencia de `client_simulator/` legacy y pidió homologación
- **Stack legacy:** `client_simulator/` raíz tiene LangGraph + pydantic + sqlite local DB. Stack canónico backend es FastAPI + SQLA 2.0 + LangGraph + pytest. Compatible — solo mover.
- **Stack nuevo target:** `backend/tests/agentic_evals/sales_agent/simulator/` consume DDD del backend (shared/agent_observability, sales_agent runtime, brand/offer fixtures)
- **Stakeholder primario:** /architect + /dev-team eval suite
- **Skills que cargar:** `tessl__langgraph` (LangGraph patterns), `sales-agent-expert` (POST audit story 1), `tessl__pytest-api-testing` (test estructura)
- **Patrón canónico research mayo 2026:** AWS Strands Evals — ActorProfile (traits + context + actor_goal) — adoptarlo

## Out of scope (explícito)

- NO escribir personas-as-simulators todavía (story C carga `docs/specs/personas/*.yaml` → ActorProfile)
- NO escribir goldens (story D corre simulator + curación)
- NO graders/judges (story E)
- NO eliminar `client_simulator/` raíz (queda como dashboard standalone)
- NO refactorizar `runner/` existente (preservar — el runner consume simulator, no se acopla)
- NO cambiar el agente real `sales_agent` (solo agent_bridge wirea contra él)

## Riesgos / Asunciones

- **Riesgo:** `client_simulator/` legacy tiene drift de pydantic v1→v2 o de imports `from client_simulator.x` que rompen al mover. **Mitigación:** primero git mv puro (R9 commit 1), luego refactor imports (R9 commit 2), luego ejecutar smoke (R9 commit 3 si necesita más fix).
- **Riesgo:** `agent_bridge.py` legacy llamaba a un mock — el real `sales_agent` runtime puede tardar más + costar más por turno. **Mitigación:** smoke test con max_turns=3 + trial 1 (no pass^k todavía) — costo controlado.
- **Riesgo:** LangGraph state machine del legacy tiene bugs no detectados (nunca corrió). **Mitigación:** smoke test detecta ASAP; si falla, escalar a Chris para decidir patch vs rewrite.
- **Asunción:** dual-LLM pattern es el patrón correcto (research mayo 2026 confirma — τ-Bench, Strands, MLflow, Bloom).

## Próximo paso

`→ Espera eval-foundation-tenant-seed-data refined → /po lee 00-story + skill sales-agent-expert + tessl__langgraph → redacta 01-spec.md service-story con scenarios:
  happy (simulator corre 1 conversación tenant_coach_lat × lead-frio-impaciente, termination=goal_completion, transcript ≥ 3 turns),
  negative (tenant seed inexistente → loader raises informativo),
  edge (max_turns alcanzado sin goal → termination=max_turns, transcript captured),
  adversarial (persona simulator intenta jailbreak prompt → sales_agent declina, termination=adversarial_detected o continúa según política)`
