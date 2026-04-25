# Prompt — F2 Deep Agents harness

> Pegar el bloque entre los `---` literal en una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F2 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: reemplazar el `agent_node` ReAct simple por un harness `deepagents` (planning tool + filesystem virtual + spawn_subagent) sin romper golden tests F0 ni la SSE v2 existente.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F2-deep-agents-harness.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md  ← APRENDIZAJES F1 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 2 queries):
    - "deepagents 0.5 create_deep_agent custom tools langgraph 2026 production patterns"
    - "langchain BaseTool spawn_subagent context isolation 2026"
    - "deepagents StateBackend filesystem virtual scratchpad pattern 2026"
  - Tessl tiles: revisar `tessl__langgraph` (1.1.x), `tessl__fastapi`. Si hay tile `deepagents` (no había en F0), instalar y leer.
  - Confirmar versión `deepagents` actual (0.5.3 al cierre de F1) sigue siendo última. Si hay 0.6+, leer changelog para ver si introduce breaking changes vs harness signature.
  - Si el research sugiere ajuste al plan F2 → ajustar antes de codear.

- **Foco — no scope creep.** F2 entrega UNA cosa: harness deepagents wrapping al graph existente, planning visible, scratchpad ephemeral, spawn_subagent operativo. URL contextual (F4) y ask_tenant_data (F5) NO van acá.

- **Paso 4 — TDD obligatorio.**
  - Test del harness wrapper (mock LLM, verifica planning tool emit + scratchpad write + done).
  - Test que `write_todos`/scratchpad emit `card_emitted` event correcto en SSE v2.
  - Golden snapshots F1 deben seguir verdes:
    `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/architecture/test_copilot_provider_compliance.py tests/architecture/test_no_new_copilot_module_imports.py -q -o addopts=""`.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar el orchestrator**: `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/architecture/ -q -o addopts="" --timeout=20` — debe ser verde (516+ arch tests + 17 golden).
  - Después de cada bloque: ruff + golden + arch.
  - Test flaky `test_tool_call_produces_tool_events` pasa aislado pero falla en suite full (F0+F1 documentaron). NO bloquea pero correr `tests/modules/copilot/test_streaming_integration.py` aislado tras tocar streaming/orchestrator.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - Trace recorder (`copilot_trace_event`) registra los nuevos events (planning_started, scratchpad_write).
  - 4-tier model router se mantiene; deepagents debe respetarlo (NANO/MINI/REASONING/HEAVY) — no hardcodear modelos en config.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino tomado no era único (e.g. wrap vs replace agent_node, StoreBackend vs StateBackend default).
  - Gotchas reales: si deepagents 0.5.3 tiene bugs con LangGraph 1.1.9, anotarlos.
  - Hooks listos para F3 (brand summary lighthouse) y F4 (URL contextual scratchpad).

- **Paso 8 — Generar `prompts/F3-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f2): deep agents harness + planning + scratchpad`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F2-deep-agents-harness.md` y `prompts/F3-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F2 no aplica por aprendizajes F1 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F2 (de aprendizajes F1)

### Aprendizajes de F1 que F2 debe asumir

- **Paquete real es `deepagents` 0.5.3, no `langchain-deepagents`.** Documentación lo llamaba mal; F0 corrigió y F1 confirmó. Importar via `from deepagents import create_deep_agent`. Retorna compiled LangGraph graph compatible con LangGraph 1.1.9.
- **Provider pattern + discovery activo.** F2 puede consumir `discover_providers()` para spawnear subagentes con tool subsets por provider. NO debe reintroducir imports cross-módulo en `copilot/`.
- **Aggregator de tool groups (`_build_tool_groups`)** ya merge providers + transversales. Si F2 introduce nuevos tools transversales (write_todos, scratchpad ops, pin_to_memory) → agregarlos a `_BASE_TOOL_GROUPS` directamente. Si son específicos de un módulo → exponer via su `ToolProvider.tool_groups()`.
- **`BaseCopilotProvider` ABC disponible** en `copilot/domain/ports.py` con None defaults. Si F2 necesita un provider transversal-only (ej. "deep_agents_meta"), heredar de él.
- **Ratchet `copilot → módulo` frozen en 22 entradas.** F2 NO debe agregar imports. Si necesita acceder data de un módulo, hacerlo via `discover_providers()[module_id].module_data().repo_factory(db)`.
- **`COPILOT_DISCOVERY_V2` flag retirado.** No reintroducir. Discovery es SoT.

### Tests baseline que F2 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/golden/ \
  tests/architecture/test_copilot_provider_compliance.py \
  tests/architecture/test_no_new_copilot_module_imports.py \
  tests/architecture/test_copilot_anchors.py \
  tests/architecture/test_ddd_boundaries.py \
  tests/modules/copilot/test_streaming_integration.py \
  -q -o addopts="" --timeout=20
```

Debe ser verde excepto el flaky `test_tool_call_produces_tool_events` (pasa aislado).

### Archivos clave que F2 modifica (a priori)

- `backend/src/modules/copilot/application/orchestrator/graph.py` — `agent_node` reemplazado por harness.
- `backend/src/modules/copilot/application/orchestrator/deep_agent.py` — nuevo, harness wrapper.
- `backend/src/modules/copilot/tools/deepagents_builtins/{write_todos,scratchpad,pin_to_memory}.py` — nuevos tools transversales.
- `backend/src/modules/copilot/infrastructure/repositories/pinned_memory_repository.py` — nueva (StoreBackend Postgres).
- `backend/src/modules/copilot/application/tools/registry.py::_BASE_TOOL_GROUPS` — agregar grupo `deepagents` con write_todos + scratchpad ops.

### Riesgos que vigilar en F2

- **`langchain-anthropic 1.4.1`** instalado pero no usado al cierre de F1. Si deepagents config requiere modelo Anthropic, listo. Si no, verificar no introduce un fork del LLM provider.
- **State leak persistent en streaming tests** (flaky pre-existente). F2 que toque orchestrator puede empeorarlo. Correr `tests/modules/copilot/test_streaming_integration.py` aislado tras cada bloque.
- **`langchain-core 1.3.x`** stack está en `1.3.2`. Si F2 introduce dep que requiere `1.2.x` (regresión), bloquear. F1 confirmó suite completa pasa con 1.3.2.
- **`ProviderRoute.groups` aún no consumido en `_match_route`.** Si F2 necesita route-aware tool selection dinámico, agregar wire-up en `_match_route` (no inventar otro mecanismo).
