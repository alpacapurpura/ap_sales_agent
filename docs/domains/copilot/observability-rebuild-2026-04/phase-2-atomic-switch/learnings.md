# Phase 2 — Learnings

> Llenado durante ejecución. Última actualización al cerrar fase.

---

## Research findings (executed 2026-04-26)

### LangGraph `astream_events(version="v2")` + RunnableConfig callbacks

- **Status:** vigente. Pattern soportado tal como diseñamos.
- **Pattern confirmado:** `graph.astream_events(state, version="v2", config={"callbacks": [handler]})`. La config se propaga a sub-runnables y herramientas (Python ≥3.11 lo hace automático en async + cuando se pasa el config explícitamente).
- **Verificado en repo:** `langchain_core` 1.3.2 ya en `backend/.venv`. `BaseCallbackHandler` con métodos sync coexiste con stream async (LangChain ejecuta callbacks en pool propio).
- **Notas:** issue 6105 (LangGraph nested en Runnable) NO aplica — usamos el graph "top-level" (`build_deep_agent_graph(state).astream_events(...)`).

### Callback propagation a tools (deep_agent harness)

- **Status:** correcto out-of-the-box. `langgraph` ≥0.2 propaga `RunnableConfig.callbacks` a cada `Tool` via `Runnable.invoke(config=...)`. No requiere wrapping manual.
- **Pattern confirmado:** ningún tool define `callback_handler=` propio; todos heredan del config root.
- **Riesgo residual:** subagentes lanzados via `task` tool corren en sub-graph compilado. Reciben los callbacks por defecto pero `stream_provenance.policy_for(...)` ya filtra los stream events para evitar leak a UI. El callback handler escribe llm_call rows aunque el stream event drop → cost del subagente queda imputado al mismo `turn_id` (deseado).

### Event bus decision

- **Elegido:** `src/shared/domain/events.py:EventBus` existente (in-process sync, `_handlers: dict[str, list[Callable]]`, `publish(event, session=None)`).
- **Razón:**
  1. Cohesión con módulos hermanos (`SaleCompletedEvent`, `LeadCapturedEvent`) que ya lo usan.
  2. `dispatch_custom_event` de LangGraph acopla el evento al stream — peor para cards emitidas por workers ARQ que NO corren dentro del stream del copilot.
  3. Sincronía + best-effort match con principio 4 (no rompe turn).
  4. Ya tiene guard de idempotencia en `_subscribe_once` (mismo pattern usado en `domain_subscribers.py`).
- **Subscribers se invocan con `session=None`** (dispatch inmediato) en publishers del copilot porque el orchestrator no tiene "after_commit" claro — la sesión hace commits parciales durante el stream.

### SQLAlchemy session lifecycle en callbacks

- **Pattern confirmado:** session per write — exactamente lo que el callback handler de Phase 1 hace via `LlmCallRepository.add()` + `session.flush()` al final del turn (en `_aggregate_totals`). No reutilizar la session async del request HTTP en el callback (el callback corre en el pool de threads).
- **Repos del módulo obs reciben una `Session` sync inyectada** (no `AsyncSession`). Phase 2 wiring construye esa session bajo demanda en `ObservabilityContext.start(...)` → `SessionLocal()`.

### ARQ event bus

- **Elegido:** in-process. Subscribers ejecutan sincrónicos en el mismo proceso del FastAPI worker.
- **Razón:** latencia mínima (no queue hop), best-effort consistente con principio 4, no requiere ARQ disponible en startup.

### Test mocking — `FakeListChatModel` / `FakeListLLM`

- **Verificado:** `langchain_core.language_models.fake_chat_models.FakeListChatModel` está disponible. API:
  ```python
  from langchain_core.language_models.fake_chat_models import FakeListChatModel
  llm = FakeListChatModel(responses=["...", "..."])
  ```
- **Limitación:** `FakeListChatModel` NO emite `usage_metadata` por default. Para test del callback handler con tokens reales hay que envolverlo o usar `RunnableLambda` que emita un AIMessage con `usage_metadata` poblado. Phase 1 test `test_e2e_isolated.py` ya lo hace; reusable.

### Sesiones paralelas — chequeo previo al commit grande

- `git status --short` antes de empezar T2.5: limpio (allowlist commiteada en T2.0).
- `git log -3 --oneline -- backend/src/modules/copilot/application/orchestrator/chat.py`:
  - aefe3c71 fix(copilot): subagent stream isolation L0-L5
  - 5a707507 perf(copilot-fpos3): routing classifier parallel a model warm-up
  - 31d36a5d feat(copilot-fpos2): channel intent middleware + force-bind
- `git log -3 --oneline -- backend/src/modules/copilot/application/extraction_card_flow.py`:
  - 23f09ffc fix(offer,copilot): section pill URLs + badge grouping
  - 4d2369f7 refactor(copilot,offer,shared): close tech-debt plan post 8d0a63d3
- **Conclusión:** todo committeado, sin WIP ajeno, ventana clara para el switch.

### Cambios al diseño respecto a ARCHITECTURE.md

Ninguno bloqueante. Ajustes documentados:

1. **Domain events son `DomainEvent` subclasses, no frozen dataclasses sueltas.** El plan T2.3 mostraba `@dataclass(frozen=True) class TurnStarted: tenant_id: UUID; turn_id: UUID; ...`. Decisión: alinear con pattern existente (`SaleCompletedEvent`, `LeadCapturedEvent` extienden `DomainEvent` con `payload: dict`). Razón:
   - El subscriber genérico en `domain_subscribers.py` ya consume `event.payload.get(...)`.
   - El bus existente (`EventBus.subscribe(event_name, handler)`) llavea por `event_name` string — los frozen dataclasses sueltos rompen el dispatch.
   - Type-safety se preserva via `@classmethod create(...)` que recibe parámetros tipados.
2. **`obs.observe_turn(...)` se mantiene como entrypoint principal** (en lugar del `event_bus.publish(TurnStarted(...))` literal del plan). Razón:
   - El context manager garantiza pareo `turn_start`/`turn_end` incluso bajo excepción (try/except/else).
   - Igualmente publica `TurnStarted`/`TurnEnded` events para que otros consumers (admin tracking futuro, copilot quality) puedan reaccionar.
   - `_write_turn_end` se extiende para incluir keys de compat (`model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_input_tokens`, `cache_hit_rate`, `cost_usd`, `response_length`, `message_count`, `block_count`) además de los nuevos (`llm_call_count`, `total_*`, `total_cost_usd`).
3. **Plan menciona "borrar" el autouse `_isolate_trace_recorder_db` en `tests/conftest.py:115`** — confirmado, se borra en el commit del switch (la nueva `ObservabilityContext` se construye explícitamente en tests que la requieren; no necesita autouse global porque DI está bien escupida).

No fue necesario pausar/consultar al usuario.

---

## Items de Fase 1 deferred-debt incorporados a Fase 2

- ✅ **Wireup de chat.py es de 4 puntos** — eliminamos `_isolate_trace_recorder_db` autouse al borrar `trace_recorder.py`.
- ✅ **Domain events tipados** — `TurnStarted/TurnEnded/CardEmitted/RoutingDecided` definidos en T2.3 como `DomainEvent` subclasses con `create(...)` classmethods.
- ⏸️ **Cron `sync_litellm_pricing` sin estado** — diferido a Fase 3 (no bloquea switch).
- ⏸️ **`copilot_llm_call.parent_span_id`** — diferido a Fase 3 (deja NULL hoy; útil cuando reconstruimos el árbol completo en `/trazas` Phase 3).

---

## Decisiones tomadas

### D2.1 — Single writer para turn rows (`observe_turn`), no subscriber

- **Contexto:** plan T2.5.1 mostraba `event_bus.publish(TurnStarted/TurnEnded)` + el subscriber genérico de `domain_subscribers.py` escribe rows. Eso provocaría doble-escritura por turn (uno desde `observe_turn._write_turn_*`, otro desde el subscriber).
- **Opciones:**
  - (A) Sólo el subscriber escribe; mover la agregación de `copilot_llm_call` ahí dentro.
  - (B) Sólo `observe_turn` escribe; borrar los handlers de turn events del registrador.
- **Elegida:** B. Razón:
  - `observe_turn` ya tenía la lógica de agregación (`_aggregate_totals`) en Fase 1 con tests verdes. Migrarla al subscriber agregaría riesgo (sesión nueva, queries cross-thread) sin beneficio.
  - El context manager garantiza pareo `turn_start`/`turn_end` incluso bajo excepción — el subscriber tendría que duplicar esa coreografía.
  - Si Phase 3 agrega un segundo consumer (telemetría, quality), publica `TurnStarted/TurnEnded` de todos modos via `observe_turn` y solo registra otro handler — no requiere refactor.
- **Implicancia:** `register_subscribers` en `domain_subscribers.py` solo cubre `EVENT_CARD_EMITTED` + `EVENT_ROUTING_DECIDED`. Tests `test_register_does_not_persist_turn_events` lo enforza.

### D2.2 — `_legacy_compat_keys` en `_write_turn_end`, no en subscriber

- **Contexto:** plan T2.5.7 dice "subscriber agrega summary al JSONB con shape similar al actual". Pero D2.1 ya decidió que el subscriber NO escribe turn rows.
- **Elegida:** mover la proyección compat al `_write_turn_end` directamente — junto a los nuevos keys agregados (llm_call_count, total_*, total_cost_usd) emitir también los legacy (`model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_input_tokens`, `cache_hit_rate`, `cost_usd`, `response_length`, `message_count`, `block_count`).
- **Razón:** misma única-fuente-de-verdad. Si el shape compat divergiera de los aggregates en producción significaría un bug en la proyección, no un race entre dos writers.
- **Stream summary se inyecta** vía `obs.set_turn_summary(response_length=..., message_count=..., block_count=...)` que el orchestrator llama justo antes de salir del `async with obs.observe_turn(...)`.

### D2.3 — `os.environ.setdefault(COPILOT_OBS_REBUILD_DISABLED, "1")` como fallback en `_build_observability_context`

- **Contexto:** la construcción del contexto puede fallar (falta migración, repos rotos en setup raros). Si no se cubre, `obs` queda `None` y el `async with` rompe.
- **Opciones:** (A) Devolver un noop ad-hoc, (B) Reusar el flag de rollback como mecanismo único.
- **Elegida:** B. Razón: un solo path de "obs apagado" — el flag controla tanto rollback explícito como degradación silenciosa por error de setup. Documentado en logs (`obs_context_init_failed`) para no enmascarar el bug subyacente.

### D2.4 — autouse `_disable_copilot_observability` global + override local en `tests/modules/copilot/observability/conftest.py`

- **Contexto:** la fixture autouse anterior (`_isolate_trace_recorder_db`) parcheaba el factory del recorder legacy. Reemplazo: setear `COPILOT_OBS_REBUILD_DISABLED=1` en cada test global, y deshacerlo en los tests del módulo obs.
- **Razón:** la mayoría del test suite no necesita observabilidad; el container Postgres no resuelve fuera de Docker (DNS) y los writes burn 30s de retries. Apagarla via env var es más limpio que monkeypatch a internals.
- **Tests del módulo obs** levantan SQLite in-memory + repos reales — el override del env var (autouse en su propio conftest) los re-habilita.

### D2.5 — `RoutingDecided` se publica con `EventBus.publish(..., session=None)`

- **Contexto:** la sesión del orchestrator hace `.commit()` parcial durante el stream. Pasar `session=self.db` al publish dispararía el dispatch en un `after_commit` ambiguo (¿qué commit?).
- **Elegida:** `session=None` → dispatch inmediato. El `RoutingLogRepository.insert` + `self.db.commit()` ya pasaron, así que el handler ve estado consistente.
- **Aplica también a `CardEmitted`** porque card emission no tiene transacción "principal" tampoco.

---

## Sorpresas / atajos descubiertos

- **`os` ya estaba importado** en `chat.py` (para `COPILOT_STREAM_TIMEOUT_SECONDS`), entonces `os.environ.setdefault` no costó import nuevo.
- **6 tests obsoletos** en lugar de 5 — `test_extraction_card_flow_trace.py` también testeaba el path del recorder en extraction_card_flow, y se borró junto.
- **`test_sse_v2_events.py::test_tool_call_trace_event_records_duration_ms`** se borró completo (no se reemplazó por su equivalente en `test_callback_handler.py`) — ese test ya existe en Phase 1 cubierto por `test_on_tool_end_persists_tool_call_row_with_duration_ms`. Documentado in-line como nota.
- **`fake_*_stream` mocks** en 4 archivos de test necesitaron `config: dict | None = None` agregado a la firma. Si LangGraph 2.x cambia la signature de `astream_events`, estos mocks tendrán que evolucionar — son los primeros que romperían.
- **El conftest local de observabilidad** (`tests/modules/copilot/observability/conftest.py`) es el patrón más limpio para "este folder testea X que el suite global desactivó". Vale la pena usarlo para Phase 3 retention + Streamlit tests.
- **`_isolate_trace_recorder_db` autouse era load-bearing** para muchos tests que ni saben que existían. Sin él, `trace_recorder.start()` intentaba conectar a Postgres en cada test → 30s de DNS retries × N writes. El reemplazo via `COPILOT_OBS_REBUILD_DISABLED=1` cubre el mismo objetivo.

---

## Manejo del switch atómico

- **Commit del switch:** `3d5ff66f` `feat(copilot-obs): atomic switch — wire callback handler, delete legacy paths`.
- **Diff:** 24 files changed, 654 insertions(+), 2022 deletions(-).
- **Archivos eliminados (3 src + 6 tests):**
  - `src/modules/copilot/application/observability/trace_recorder.py`
  - `src/modules/copilot/application/observability/node_trace.py`
  - `src/modules/copilot/application/orchestrator/usage_tracking.py`
  - `tests/modules/copilot/test_trace_recorder.py`
  - `tests/modules/copilot/test_node_trace_emission.py`
  - `tests/modules/copilot/test_usage_tracking.py`
  - `tests/modules/copilot/test_usage_tracking_cache.py`
  - `tests/modules/copilot/test_turn_end_trace_data.py`
  - `tests/modules/copilot/test_extraction_card_flow_trace.py`
- **Hubo necesidad de revert?** No.
- **Soak de 24-48h:** ⏳ pendiente, ver `deferred-debt.md`.

---

## Plan de borrado del feature flag

- **Fecha planificada:** 24-48h después del commit `3d5ff66f` con el soak limpio (ver `deferred-debt.md` T2.8).
- **Hash commit del borrado:** TBD (próximo agente). Mensaje: `chore(copilot-obs): remove temporary rollback flag`.
- **Pasos detallados:** ver `deferred-debt.md` § "T2.8".

---

## Items para `.claude/rules/`

Cuando T2.8 cierre + Phase 3 promueva el reporte:

- [ ] **Actualizar `.claude/rules/copilot-resilience.md`** §"Debug copilot": apuntar a `copilot_llm_call` como fuente de verdad de cost/tokens (en vez de `copilot_trace_event.turn_end.data`). Documentar que `event_type='llm_call'` ahora se emite de verdad.
- [ ] **Agregar nota** que `test_master_data.py::ALLOWED_USD_DEFAULT_FILES` incluye `chat.py` post-Phase-2 — el fallback `currency = "USD"` del `_build_observability_context` es legítimo (mismo rol que `iam/domain/tenant.py`).
- [ ] (No urgente) **Patrón `_disable_copilot_observability` + conftest local** vale la pena documentar como pattern para módulos best-effort cuya autouse global afecta producción.

---

## Métrica final fase

- **Commits de Fase 2 (en orden):**
  - `a9edf2d2` test(copilot-obs): allowlist USD defaults in Phase 1 obs seams (T2.0 — Phase 1 leftover)
  - `a3455ebf` feat(copilot-obs): add domain events module + register hook (T2.2 + T2.3 + T2.4)
  - `3d5ff66f` feat(copilot-obs): atomic switch — wire callback handler, delete legacy paths (T2.5 + T2.6)
  - **TBD** chore(copilot-obs): remove temporary rollback flag (T2.8 — post-soak)
  - **TBD** docs(copilot-obs): close phase 2 — fill learnings + deferred-debt (T2.10)
- **Diff total Fase 2:** 24 files changed (commit `3d5ff66f`) + 5 files (commit `a3455ebf` 650 ins) + 1 file (commit `a9edf2d2` 10 ins) ≈ ~660 ins / 2022 dels netas (-1372 LOC).
- **Tests añadidos:** 11 (events) + 6 (register) + 11 (atomic_switch) = **28 tests nuevos** en `tests/modules/copilot/`.
- **Tests borrados:** **36 tests** (6 archivos legacy completos + 1 test deletion en test_sse_v2_events.py).
- **Coverage backend:** **67%** (gate ≥43% holgado; baseline Phase 1 67.48%, sin regresión material — la diferencia es 36 tests menos).
- **Quality gates:**
  - Ruff lint clean.
  - Ruff format clean.
  - 575 architecture tests verdes (sin nuevos cross-module imports, USD allowlist actualizada).
  - 5240 passed / 7 skipped / 11 deselected en full pytest.
  - E2E smoke ⏳ pendiente (containers requeridos, ver `deferred-debt.md`).
- **Verificación ratchet:** `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches. ✓
- **Tiempo real ejecución:** ~3 horas wall-clock (research + 2 commits prep + atomic switch + recovery de 8 tests rotos + lint cleanup + docs).
