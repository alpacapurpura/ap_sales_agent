# FP3 — Routing classifier parallel a model warm-up (B25-TP11)

**Bug origen:** TP11 J1.T1 TTFB block_start ~2770ms > target 1500ms (2026 conversational breaking point).
**TP origen:** `results/TP11-2026-04-26.md §B25-TP11`.
**Tiempo estimado:** 1 día.
**Pre-req hard:** FP2 cerrado (mismo orchestrator file).
**Capa stack:** Backend (chat orchestrator routing flow + concurrency).

---

## Misión

Reducir TTFB block_start de ~2770ms a ≤800ms p50 ejecutando el LLMClassifier NANO call en paralelo al model warm-up + bind tools, en vez de sequencialmente. H1 inmediatez PASS.

---

## Research mandate

Queries:

- `"asyncio gather race condition LLM streaming agent 2026"` — patterns para concurrent LLM calls con coalesce.
- `"langgraph speculative tool binding 2026 swap mid-stream"` — si LangGraph soporta swap de tools mid-stream.
- `"llm tier classifier eager vs lazy decision 2026"` — best practice tier decision timing.

Tessl tiles: `tessl__langgraph` (concurrency hooks).

---

## Acceptance criteria

| AC | Descripción | Evidence pre-fix | Evidence post-fix |
|---|---|---|---|
| **AC1** | TTFB block_start p50 ≤800ms en short messages (<50 chars) | ~2770ms en J1.T1 | ≤800ms re-run |
| **AC2** | TTFB block_start p95 ≤2000ms en cualquier message | ~2900ms | ≤2000ms |
| **AC3** | Routing decision se ejecuta en paralelo a model warm-up + bind tools (no secuencial) | trace events: routing_decision precede node_enter model | routing_decision concurrent con node_enter model (timestamps overlap) |
| **AC4** | Si tier change cambia tools binding mid-flight, NO race condition (no missing tools en bound set) | n/a | test integración con simulated tier change passes |
| **AC5** | `copilot_routing_log` sigue populating correctamente post-refactor | rows insertan | rows insertan + `tier_selected` correcto |
| **AC6** | NO regression en quality (judge avg ≥4.0 mantained) post-refactor | baseline | judge sample 10 turns post-refactor confirma |

---

## Procedimiento por AC

### Setup
- TP11 J1.T1 trace `f35bc21a-...` para baseline metrics (turn_start → routing_decision → node_enter timing).

### AC1-AC3 — parallelism implementation

1. **Investigar code path actual:**
   - `grep -rn "_record_routing_decision\|_get_default_router\|build_default_router" backend/src/modules/copilot/`.
   - Localizar puntos secuencial actual: probable `chat.py::CopilotOrchestrator.run` con `routing_decision = await self._record_routing_decision(...)` ANTES de `await build_deep_agent_graph(...)`.

2. **Diseño parallelism:**
   ```python
   # ANTES (secuencial):
   routing_decision = await self._record_routing_decision(state, msg)
   tier = routing_decision.tier_selected
   client = LLMFactory.get_service().get_client(role=tier_to_role(tier))
   tools = get_tools_for_context(state, route)
   graph = build_deep_agent_graph(state, llm=client, tools=tools)
   
   # DESPUÉS (parallel):
   routing_task = asyncio.create_task(self._record_routing_decision(state, msg))
   # Eager bind con tier "default" (AGENT) + broad tool set (superset incluye possibles tier-specific)
   default_client = LLMFactory.get_service().get_client(role=ModelRole.AGENT)
   default_tools = get_tools_for_context(state, route)
   default_graph = build_deep_agent_graph(state, llm=default_client, tools=default_tools)
   
   # Esperar routing decision (probablemente ya completó por timing)
   routing_decision = await routing_task
   tier = routing_decision.tier_selected
   
   # Si tier diferente al default, swap antes del primer block_delta
   if tier_to_role(tier) != ModelRole.AGENT:
       client = LLMFactory.get_service().get_client(role=tier_to_role(tier))
       tools = get_tools_for_context(state, route, tier_filter=tier)
       graph = build_deep_agent_graph(state, llm=client, tools=tools)
   else:
       graph = default_graph
   ```

3. **Mitigación race condition AC4:**
   - Bind broad superset al inicio (incluye tools de TODOS los tiers posibles).
   - Si classifier elige tier que requiere tool subset distinto, **no swap del graph** — mejor: filter tools dynamically en first model invocation.
   - O: bloquear primer block_delta hasta routing decisión confirmar binding consistent.

4. **Test RED:** unit test mock classifier delay 2s + assert que graph build started antes del classifier complete.

5. **Test GREEN:** implementar.

6. **Live re-run J1.T1 (mismo "hola, soy nuevo"):**
   - Performance trace TTFB block_start.
   - Trace events SQL: timestamps de `routing_decision` vs `node_enter model` deberían overlap (concurrent), no sequential.

### AC5 — routing log integrity

1. Verify `copilot_routing_log` row inserta post-refactor con `tier_selected`, `classifier_used`, `confidence`, `reason`, `tools_available`.
2. Test BE: assert row insertada per turn.

### AC6 — quality regression

1. Re-run J3 + J4 + J5 selectivos (mismas prompts TP11) post-refactor.
2. Manual review respuestas: quality consistente con TP11 baseline.
3. Si possible, judge invocation con muestra de 10 turns: `RUN_LLM_JUDGE=1 .venv/bin/pytest tests/quality/...`. Confirmar judge avg ≥4.0.

---

## Tests / archivos a crear / modificar

### Backend
- `backend/src/modules/copilot/application/orchestrator/chat.py` (UPDATE — refactor `run` method para parallelism)
- `backend/src/modules/copilot/application/routing/router_factory.py` (UPDATE si needed — async-friendly)
- `backend/tests/modules/copilot/test_routing_parallel.py` (NEW — integration test mocked classifier delay)
- `backend/tests/modules/copilot/test_chat_orchestrator_ttfb.py` (NEW — measure TTFB con `time.monotonic_ns()` deltas)

---

## Failure playbook

- **Race condition tools binding:** si classifier dice "tier X requiere tool Y no en superset", agregar Y al broad initial bind. Documentar en results.
- **`build_deep_agent_graph` heavy + síncrono:** si graph build domina latency más que classifier, refactor secundario para lazy graph compile. F-pos siguiente si exceeds scope.
- **Quality regression:** si judge avg cae, root cause hipótesis: tools subset diferente entre tiers cambia behavior. Ajustar superset.
- **Memory pressure:** broad tool bind = más tools en LLM context. Verificar tokens/turn no explote >25k. Si lo hace, tier-specific binding mantain pero hacer routing DECISION sync rápido (eager NANO con cache prefix F8).

---

## Sub-bugs descubiertos durante FP3

> Append-only.

- (none yet)

---

## Output esperado (FP3 = ÚLTIMO del batch F-pos)

`results/FP3-{fecha}.md` con:
- Pre-research insights
- AC1-AC6 checklist con before/after evidence (TTFB ms numbers)
- Tests added
- Sub-bugs
- Métricas: TTFB delta + tokens delta + cost delta
- **§Cierre F-pos batch:** resumen agregado de FP1-FP4 + score post-fixes (target 8/8) + recomendación de re-run TP11 selectivo (J1, J2, J4) para confirmar score sí alcanzado.

**NO se genera `prompts/FP4-start.md`** — FP3 cierra el batch (FP4 ya ejecutado en paralelo con FP1).

Si re-run TP11 confirma score 8/8, archivar plan `fpos-2026-04/` + actualizar `redesign-2026-04/learnings/F-pos-summary.md`.
