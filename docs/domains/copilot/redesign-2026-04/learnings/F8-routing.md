# Learnings — F8 Routing + Cost Optimization

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `9be27776`)

---

## Resumen 3 líneas

- F8 entrega 5 piezas: `LLMClassifier` NANO fallback + `build_default_router` factory; reorden cache-friendly del system prompt vía `system_prompt_layout::compose_system_prompt` (5 fragments cacheable + 3 volatile + boundary marker); deletion total de la ruta ReAct legacy + flag `COPILOT_DEEP_AGENT_V2` (deep_agent harness es ahora el único graph runtime); migración FE a SSE v2 `block_*` + remoción de `text_chunk` BE; admin Streamlit `/copilot-routing` con tier distribution + classifier breakdown + cache hit rate + p50/p95 latencia.
- Decisión no obvia: el reorden movió `lighthouse` (F3) DESDE el head absoluto del prompt HACIA el slot 3 del bloque cacheable (después de identity + tools_hint). Esto rompe la suposición F3 de "lighthouse first" pero gana cacheabilidad cross-tenant del header estático universal — multi-tenant cache wins. Tests F3/F4 actualizados para validar el orden F8.
- Hooks listos para F9: telemetría `cached_input_tokens` + `cache_hit_rate` per turn vía `UsageAccumulator.as_log_dict()` (logged en `copilot_turn_usage` + admin page); golden tests F1-F7 + nuevos F8 (~926 backend + 245 FE) son baseline para LLM-judge harness.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Llave única `cache_read` en `usage_metadata.input_token_details`** (no `cache_creation_input_tokens`). | Mandate del prompt usaba el nombre Anthropic (`cache_creation_input_tokens`); LangChain normaliza ambos providers a `usage_metadata["input_token_details"]["cache_read"]`. Ese es el nombre correcto en abril 2026 — confirmado vía web search + lectura directa LangChain v1.2. | Capturar `cache_creation_input_tokens` literal. Habría dado siempre 0 (campo Anthropic raw, no expuesto por LangChain abstraction layer). |
| **Reorden movió `lighthouse` al slot 3 del cacheable** (después de identity + tools_hint), NO al slot 1. | F8 §5.2 explícito: static instructions universalmente cacheable cross-tenant van primero — el prefix más estable maximiza el hit rate global. Lighthouse es per-tenant; viene después del bloque universal pero antes del editable_catalog/modules_list. | Mantener `lighthouse` primero (orden F3). Habría perdido el hit cross-tenant del header static universal y limitado el cache a per-tenant. |
| **`PromptFragment` enum + `compose_system_prompt(fragments)`** como SSoT del orden, NO una concat string en `build_system_prompt`. | El orden es un invariant del producto — debe vivir en un módulo testeable + freezeable. Arch test `test_system_prompt_order.py` lo congela; agregar un fragment requiere actualizar el snapshot deliberadamente. Side effect: hace el composer thread-safe, sin estado, y reusable por cualquier futuro builder. | Concat inline en `build_system_prompt`. Funciona pero el orden vive disperso entre `+` y `if/else`; cualquier refactor lo rompe en silencio. |
| **5 templates Jinja split** (`copilot_system_static.j2`, `_tools_hint.j2`, `_modules.j2`, `_editable.j2`, `_volatile.j2`, `_snapshot.j2`) — el monolito `copilot_system.j2` borrado. | Cada slot del enum mapea a UN template renderizable individualmente. Cuando un fragment falla (DB down → snapshot vacío) el resto sigue renderizando. Mantenibilidad: tocar el editable_catalog ya no requiere abrir un Jinja de 162 líneas. | Mantener `copilot_system.j2` pasando `lighthouse_block` como param y reordenar inline. Funciona pero las dependencias de cada slot quedan acopladas en un solo archivo. |
| **`LLMClassifier` sync `classify`**, no async. | El `IntentClassifier` Protocol es sync (F0/F1). Cambiarlo cascada a `RuleClassifier` + `ModelRouter` + 6 callsites. NANO p95 ~300ms es aceptable inline porque solo se invoca cuando rule classifier devolvió `None` (~10% de turns). | Async `classify` con `asyncio.run` interno. Habría requerido refactor del Protocol y propagación a callsites — scope F8 explosivo. |
| **Threshold default 0.7** en LLMClassifier (configurable vía constructor). | Research abril 2026 (Label Your Data, Prospeo) confirmó el patrón "auto-act ≥0.85, clarify 0.6-0.85, fallback <0.6". F8 router NO clarifica — solo fallback. 0.7 es el midpoint defensivo: alto suficiente para evitar misroutes con baja confidence, bajo suficiente para no caer al MINI default por defecto. | 0.85 como en producto. Habría caído al default con demasiada frecuencia, desperdiciando la inversión NANO. |
| **`ModelRole.NANO` agregado a `core/enums.py` + default `gpt-4o-mini`**. | F5 dejó hook explícito ("F8 introduce NANO"). Default a un modelo real (`gpt-4o-mini`) para que el LLMClassifier NUNCA falle por modelo inexistente; envs override `AI_MODEL_NANO` cuando el catálogo OpenAI exponga un tier más barato. Activé el F5 hook (`intent_classifier.py:126` FAST→NANO) en el mismo commit. | Dejar NANO=`gpt-5.4-nano` (el `model_name` declarado en `TIER_METADATA`). Modelo no existe en producción; cualquier env sin override explícito habría roto LLM calls. |
| **Borrar ReAct legacy + flag `COPILOT_DEEP_AGENT_V2` completo en F8**, no progressive. | El flag default-False habría dejado un branch muerto que nadie sabe si está cubierto por tests; cualquier env nuevo que se levantara con flag-off habría revivido el código zombie. F8 corre baseline 872 verde con el flag-off path; tests con monkeypatch a `chat.copilot_graph` adaptados a `chat.build_deep_agent_graph`. | Mantener flag default-True + delete branch en F-pos. Habría dejado dead code observable durante semanas + dos puntos de configuración para olvidar. |
| **FE: `text_chunk` queda en `SSEEventType` union pero el switch lo handlea como no-op-tolerable**. | Después del deploy, FE bundles cacheados en browsers viejos pueden seguir esperando text_chunk. Mantener el case del switch (que ahora delega a un opcional `onTextChunk`) evita errores silenciosos en la consola. Tests cubren el path como "legacy compat path". | Borrar `text_chunk` del union enum + handler. Habría dado errores TS en cualquier código FE legacy que aún lo referencie. |
| **`compose_system_prompt` retorna prompt SIN deep-agent suffix** (el suffix lo agrega `_build_combined_system_prompt` en `deep_agent.py`). | F2 owns el suffix; F8 no debe duplicarlo ni absorberlo. Test `test_deep_agent_suffix_stays_at_tail` valida que el suffix sigue al final del combined prompt — F8 no toca esa invariant. | Mover el suffix a `compose_system_prompt`. Habría duplicado el contrato de F2 y roto el path legacy fallback (cuando deep_agent no estaba disponible). Después de §5.3 el legacy se borró pero eso no invierte la decisión. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **OpenAI NO usa `cache_creation_input_tokens`** (eso es Anthropic). LangChain normaliza ambos providers a `usage_metadata["input_token_details"]["cache_read"]`. El mandate del prompt F8 usaba el nombre Anthropic — flag obligatorio antes de implementar. Reproduce: en una session real con OpenAI, `usage.input_token_details = {"cache_read": N, "audio": 0}`.

- **OpenAI prefix cache requiere ≥1024 tokens contiguos sin cambios**. Si el prefix queda en 900 tokens, NO hay cache — no hay degrade gradual. F8 §5.2 garantiza prefix grande dejando los 5 fragments cacheable consecutivos antes del CACHE_BOUNDARY_MARKER. Para validar post-deploy: monitorear `cache_hit_rate` en el admin page; si 0% durante >24h con conversaciones reales, el prefix está debajo del umbral.

- **FE `copilot-api.ts` NO tenía handlers `block_*`** al iniciar F8 — solo `text_chunk` + tool/status/done/error. Borrar `text_chunk` del BE sin migrar el FE = streaming roto end-to-end. Esto bloqueó §5.4 hasta que F8 hizo la migración FE inline (Task 6 antes de Task 7). **Cualquier fase futura que toque protocolo SSE debe grep el FE por handlers ANTES de tocar el BE**.

- **`@dataclass(frozen=True, slots=True)` + `Mapping` import dentro `TYPE_CHECKING`** rompió `compose_system_prompt` con `NameError` en runtime. Lección: `from collections.abc import Mapping` es evaluado en runtime cuando se usa como anotación function-arg (incluso con `from __future__ import annotations`, si Python re-resuelve para introspección). Solución: dejar el import en TYPE_CHECKING y validar con tests; runtime `Mapping[X, Y]` se evalúa lazy gracias al `__future__` annotations. Confirmado: ruff TC003 lint pasa, pytest pasa.

- **`replace_all=true` en `Edit` reemplaza TODAS las ocurrencias del string literal exacto**, no por línea ni por contexto. Tropecé al refactorizar `db: Any` → `db: Session`: `replace_all` solo encontró los `db: Any,` (con coma) y dejó intactos los `db: Any)` (con paréntesis). Lección: cuando refactorizas un parámetro de signatura, leer las firmas exactas (single-line vs multi-line) antes de un replace_all.

- **Test flaky `test_editable_fields_ssot::test_no_cross_domain_duplicates` heredado** — confirmado standalone PASS (8/8) post-F8, dentro de `pytest -x -q` full FAIL por order-dep. Mismo síntoma que F3-F7 documentaron. F9 que NO toque `editable_fields`: ignorar. F-housekeeping eventual debe atacar la order-dep.

- **Test flaky `test_streaming_integration` heredado** — F8 LO TOCÓ porque borró ReAct + dual SSE; aislado 26/26 PASS post-F8. La fragility persiste pero F8 no la empeoró.

- **`prompt_loader.render` es lazy + cacheable** (FileSystemLoader). Borrar `copilot_system.j2` físicamente requiere `rm`; si quedaba un test importándolo por nombre fallaba sin pista clara (`TemplateNotFound`). F-pos que renombre templates: borrar el archivo físico explícitamente y grep por el name string.

- **`HumanMessage`/`SystemMessage`/`ToolMessage` import en chat.py `_handle_tool_end` eran necesarios incluso después de borrar agent_node.** Ruff reportó "unused" temporalmente; pero `_handle_tool_end_v2` y `_handle_tool_end` SÍ los usan. Lección: `ruff check --fix` puede quitar imports usados via `getattr` o passing-through tests; siempre re-correr la suite después de un fix automático.

- **Anchor budget**: subí de 27 a 30 (margin para F9/F10) en lugar de strict 28. Tres anchors F8: `COPILOT-LLM-CLASSIFIER-F8`, `COPILOT-CACHE-PREFIX-F8`, `COPILOT-SSE-V2-ONLY-F8`. F9 puede agregar 1-2 sin bumpiar.

---

## Recomendaciones accionables para F9 (Quality + observability)

1. **Antes de empezar:** correr la suite F0-F8 baseline. Espera `BE: 3019 passed, 4 skipped` (excluyendo flakies aislados) + `FE copilot: 245 passed (28 files)` + `FE arch: 38 passed (18 files)`.
   ```bash
   cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/ tests/admin/ tests/modules/brand/ tests/modules/offer/ tests/modules/crm/ tests/shared/ -q -o addopts="" --timeout=120
   cd frontend && npx vitest run src/features/copilot/ src/__tests__/architecture/
   ```
   Flakies aislados (heredados):
   ```bash
   cd backend && .venv/bin/pytest tests/modules/copilot/test_streaming_integration.py tests/architecture/test_editable_fields_ssot.py -q -o addopts=""
   ```

2. **Cache hit rate observability ya está instrumentado.** F9 LLM-judge harness puede leer `copilot_trace_event.data->>'cache_hit_rate'` directamente en el admin page (`/copilot-routing` ya lo muestra) — no hay que inventar la pipa.

3. **`build_default_router()` está expuesto como factory en `application/router/__init__.py`.** F9 que necesite mockear el routing para tests de golden: pasar `enable_llm_fallback=False` para chains deterministas (solo rule + default).

4. **Validar prefix ≥1024 tokens post-deploy.** El reorden F8 supuso que static_identity + tools_hint + lighthouse + editable_catalog + modules_list suman ≥1024 tokens. En tenants nuevos sin lighthouse, sin editable catalog rico, ese piso puede caer. F9 puede agregar una assertion en arch test: `len(compose_system_prompt(static_only_fragments).encode("utf-8")) // 4 >= 1024`.

5. **Cuando F9 introduzca golden tests sobre el output del LLM**, NO hardcodear el orden de fragments en los goldens — referenciar `PROMPT_FRAGMENT_ORDER` desde `system_prompt_layout`. Si F-pos reordena, los goldens se actualizan automáticamente con el snapshot.

6. **Anchor budget está en 30/30 con 3 F8 entries.** Si F9 agrega `COPILOT-LLM-JUDGE-F9` u otros, sólo bumpea si necesita pasar 30 — la cap está en línea 89 de `tests/architecture/test_copilot_anchors.py`.

7. **El admin page `/copilot-routing` ya consulta `copilot_routing_log` + `copilot_trace_event.turn_end`.** F9 LLM-judge dashboard puede agregar otra section al mismo módulo o un page hermana — el patrón está cementado en `src/admin/modules/copilot_routing.py`.

8. **NO existe consumer de `RoutingLogRepository.insert` en runtime todavía.** El factory `build_default_router` está expuesto pero el orchestrator chat NO lo invoca aún. F9 (o F-pos cutover) debe wirearlo: en `chat.py` antes del graph stream, llamar `router.select(req)` + persistir vía `RoutingLogRepository`. Sin esto, el admin page ve tabla vacía aunque el código de arriba esté listo.

9. **F9 LLM-judge harness debe usar NANO** (no FAST). El hook está en `LLMClassifier._resolve_llm()`; copiar el pattern para `BrandJudge`, `MisrouteSamplerJudge`, etc.

---

## Riesgos abiertos

- **`build_default_router` no está wired al orchestrator chat.** El factory está listo pero `chat.py::stream_chat` no llama `router.select()`. Sin este wiring, `copilot_routing_log` queda vacío en producción y el admin page no tiene data. F9 cutover (o F-pos urgente) debe cerrarlo. El admin page muestra "Sin decisiones de routing" como empty-state — informativo pero diluye la value prop.

- **`LLMClassifier` invoca NANO sync = bloquea ~300ms p95**. Solo en ~10% de turns (cuando rule classifier defers), pero p99 puede escalar si la red OpenAI parpadea. Mitigación: el classifier devuelve `None` en cualquier exception (logged) → cae al default tier MINI silenciosamente. No es regresión, pero F9 podría medir el latency hit: agregar trace event `routing_decision` con `duration_ms` per classifier.

- **Prefix cache nunca verificado en producción real.** El reorden F8 supone ≥1024 tokens en el prefix; si en algún tenant la `editable_catalog` o el `modules_list` colapsan a vacío + `lighthouse` ausente (brand sin summary), el prefix puede caer abajo del umbral. Mitigación: ya logged en `copilot_turn_usage`. F9 debe alertar si `cache_hit_rate` < 30% durante una semana en un tenant.

- **Templates Jinja nuevos NO tienen smoke test dedicado.** Si alguien edita `copilot_system_static.j2` con sintaxis errada, el `_safe_render` log-and-skip lo enmascara — el LLM recibe un prompt sin identity. Mitigación: F9 puede agregar arch test `test_every_static_template_renders` que llama cada template con un kwargs sample y assert no-empty.

- **Admin Streamlit page asume Postgres + tablas con datos.** El smoke test mockea la session devolviendo cursors vacíos — render path verde pero "happy path" no se ejerce. F9 LLM-judge dashboard puede tropezar con el mismo gap; recomendación: factorize el cursor stub a `tests/admin/conftest.py` con `mappings_response` configurable.

- **`text_chunk` SSEEventType FE sigue declarado** aunque BE no lo emite. Si F-pos lo limpia, OK; si queda años, es noise. Bajo costo, no urgente.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/application/router/__init__.py::build_default_router(...)` — factory canónico. F9/F10/F-pos solo necesitan importarlo y pasar `llm` para tests / `enable_llm_fallback=False` para deterministic chains. La signature está congelada.

- `backend/src/modules/copilot/application/router/classifiers/llm_classifier.py::LLMClassifier(threshold=0.7)` — sync, IntentClassifier-protocol-compatible. F9 LLM-judge puede COPIAR el patrón (NANO + structured JSON + threshold gating) sin reescribir.

- `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py::compose_system_prompt(fragments)` — pure data, idempotente. F9 que necesite rendering alternativo (ej. "judge prompt" basado en el system prompt) puede invocarlo y luego sufijar lo suyo.

- `backend/src/modules/copilot/application/orchestrator/usage_tracking.py::UsageAccumulator` — ahora con `cached_input_tokens` + `cache_hit_rate`. F9 puede leerlos directamente en el LLM-judge harness para correlacionar quality vs cache hit.

- `backend/src/admin/pages/copilot-routing.py` + `backend/src/admin/modules/copilot_routing.py` — admin Streamlit completa. F9 LLM-judge dashboard puede ser un page hermano (`copilot-quality.py`) reusando `_shared.render_tenant_selector` + el patrón fetch-from-trace.

- `tests/architecture/test_system_prompt_order.py` — 5 fitness tests congelan F8 §5.2. F9 que reordene (improbable) edita los `EXPECTED_*` snapshots.

- `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY` con cap 30. F9 puede agregar 1-2 anchors sin bump.

- `frontend/src/features/copilot/api/copilot-api.ts::CopilotChatCallbacks` — interfaz canónica única. F9 que agregue handlers (e.g. `onJudgeFeedback`) la extiende sin tocar el switch del parser.

- F5 `intent_classifier.py:126` quedó migrado a `ModelRole.NANO` en F8. Cualquier nueva tool que necesite intent classification puede importar `from src.core.enums import ModelRole` + usar `ModelRole.NANO` directo.

- Dock `_build_default_router` accept `enable_llm_fallback=False` — F9 golden tests pueden activar este modo para snapshot-test los rule decisions sin depender de OpenAI.

---

## Fuentes research útiles

- [Prompt Caching | OpenAI API](https://platform.openai.com/docs/guides/prompt-caching) — confirmó ≥1024 tokens umbral + 128-token incrementos; latencia ↓80%, cost ↓90% al hit. Validó la decisión de garantizar prefix ≥1024 vía 5 fragments cacheable consecutivos.
- [SurePrompts Prompt Caching Guide 2026](https://sureprompts.com/blog/prompt-caching-guide-2026) — confirmó "stable first, variable last; nada rotando en la región cacheable". Fundamentó el orden F8 §5.2.
- [LangGraph node-level caching — LangChain Changelog](https://changelog.langchain.com/announcements/node-level-caching-in-langgraph) — descartó el feature para F8: agrega complejidad y NO resuelve el cache hit del system prompt (que es server-side OpenAI). F-pos puede evaluar si la latencia per-node lo justifica.
- [Intent Classification 2026 Techniques | Label Your Data](https://labelyourdata.com/articles/machine-learning/intent-classification) — confirmó threshold 0.85-0.95 para auto-act; bajé a 0.7 porque F8 NO clarifica (solo fallback al default). Justificación documentada en LLMClassifier.
- [DeepAgents text-to-sql-agent example (heredado F5)](https://github.com/langchain-ai/deepagents/tree/main/examples/text-to-sql-agent) — confirmó que el patrón "structured output sync + threshold" es el canónico, no async LangGraph subgraph.

Tessl tiles consultados: `tessl__fastapi`, `tessl__langgraph`. No instalé tile nuevo — el patrón de routing + cache instrumentation está cubierto en docs oficiales OpenAI + LangChain.
