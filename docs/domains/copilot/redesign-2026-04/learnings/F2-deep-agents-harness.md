# Learnings — F2 Deep Agents harness

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `970fcf9d`)

---

## Resumen 3 líneas

- `build_deep_agent_graph(state)` compila por turno un `CompiledStateGraph` vía `deepagents.create_deep_agent` con tools dinámicos (`get_tools_for_context`), system prompt dinámico (`build_system_prompt` + sufijo planning), `AUDIT_INSPECTOR_SUBAGENT` dummy y backend default `StateBackend`. `chat.py::_select_graph` despacha entre legacy `copilot_graph` y harness por flag `COPILOT_DEEP_AGENT_V2` (default off — F4/F5 lo encienden).
- `write_todos` (built-in deepagents) emite mutación de state, NO `ui_action`; sintetizamos `plan_card` block desde **args** del tool call en `_handle_tool_end_v2` (no del output) — el output es `ToolMessage(f"Updated todo list to {todos}")` lossy.
- Migración 067 + `copilot_pinned_memory` + `CopilotPinnedMemoryRepository` listos pero NO usados aún. F4 los enchufa via tool `pin_to_memory(path)` cuando exista el StoreBackend custom Postgres.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Construir el agent fresh por turno** (no module-level cache). | `build_system_prompt` lee snapshot completion + behavior summary + guided/studio layer, todos dependen de state. `get_tools_for_context` filtra tools por route. Cachear el grafo requería middleware `before_model` que rebuilda el SystemMessage cada turn — más código y dos puntos de configuración. Compile cuesta microsegundos vs. la llamada al LLM. | Compilar una vez al import + middleware dinámico — F2 §5.1 sugería esto. Habría duplicado la lógica de prompt building en un lugar nuevo y forzado a F3 a inyectar el "lighthouse" via middleware en lugar del path natural (`build_system_prompt`). |
| **Pasar state como `{"messages": ...}` plano**, no usar `context_schema`. | Los tools del Copilot ya leen `tenant_id`/`user_id` desde contextvars (`src.core.context`) seteados por el middleware FastAPI antes del invoke. Replicar eso en `context_schema` Pydantic era código duplicado. | Definir `CopilotDeepContext` Pydantic + `context_schema=CopilotDeepContext` y reescribir `tool_executor_node` semantics. Habría sido un sub-refactor de F2 fuera de scope. |
| **Sintetizar `plan_card` desde args, no desde output del `write_todos`.** | El output es la string `f"Updated todo list to {todos}"` (Python repr de `Todo` objects con `.content`/`.status`/`.activeForm`) — parsear regex es frágil. Args llegan estructurados (`{"todos": [{"content": "...", "status": "pending"}, ...]}`). | Registrar block_handler estándar para `write_todos` que parsee output. Repr puede cambiar entre versiones de deepagents — más volátil. |
| **`StateBackend` default, NO `CompositeBackend` con `/memories/*` Postgres.** | F2 §5.2 lo sugería, pero la tabla + repo es el 80% del trabajo y los puede consumir F4 sin riesgo. Levantar `StoreBackend` custom Postgres ahora obligaría a wire-up + tests sin tool consumer real. | Implementar `StoreBackend(namespace=...)` + `CompositeBackend(default=StateBackend(), routes={"/memories/": ...})` + tool `pin_to_memory` enseguida. F4 (URL contextual scratchpad) es el caller natural — hacerlo allí evita refactor doble. |
| **Excluir `audit_inspector` del block adapter — solo registro como SubAgent dummy.** | Es plumbing puro: prueba que `task()` tool se monta y ejecuta. Sin tools propios, sin output específico para mostrar. F4/F5 reemplazan por subagentes reales con cards específicas (url_analyzer card, data_query card). | Darle UI propia ahora. El dummy no aporta valor user-visible y agregar card sería ruido en el contrato. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **`create_deep_agent` añade su propio system prompt boilerplate después del nuestro.** Pasamos `system_prompt="Eres Copilot Nicolify..."` y el LLM recibe `SystemMessage` con `"Eres Copilot Nicolify... + You are a Deep Agent..."` (nuestro contenido + ~3KB de prompt deepagents que enseña uso de `write_todos`/scratchpad/`task`). NO sobrescribir desactivando middleware — eso pierde el comportamiento de planning. Si el contexto crece, ese boilerplate cuenta. Confirmado leyendo `langchain.agents.middleware.todo.WRITE_TODOS_SYSTEM_PROMPT`.

- **Compiled graph state de deepagents NO acepta keys extra de `CopilotState`.** Schema = `{messages, jump_to, structured_response, files}`. Pasarle `tenant_id`/`client_context`/`guided_state` directo no rompe (LangGraph filtra) pero tampoco los ve. Si una fase futura necesita pasarlos al subagent o a middleware: usar `context_schema` o leer via contextvar. **No** intentar mezclar agent state + CopilotState.

- **`on_conflict_do_update(constraint=...)` rompe SQLite tests; usar `index_elements=[...]`.** El test conftest usa SQLite in-memory; el `pg_insert.on_conflict_do_update` con `constraint="uq_..."` genera SQL `ON CONFLICT (uq_...)` que SQLite parsea como nombre de columna. Pasar `index_elements=["tenant_id", "user_id", "path"]` genera `ON CONFLICT (col1, col2, col3)` que ambos motores aceptan. Aplica a cualquier upsert PG nuevo.

- **Modelos nuevos requieren registro en `tests/conftest.py::db_engine` para evitar pre-existing flake.** El test_streaming_integration deja state que fuerza SQLA a configurar TODOS los mappers cuando un test posterior commitea. `LeadModel` declara `relationship("TenantModel")` (string lazy) y falla si TenantModel no fue importado. La fila importadora en conftest **no es opcional** — sin ella, el repo nuevo passes solo y falla suite. Replicar ese pattern para cada `*_model.py` que F# añada.

- **Test flaky pre-existente no fixeado** — heredado F0/F1. Combo `test_streaming_integration → cualquier test con db.commit()` rompe con `InvalidRequestError: Mapper[LeadModel] failed to locate 'TenantModel'`. F2 corre quality gates con `--ignore=tests/modules/copilot/test_streaming_integration.py` y verifica streaming en aislamiento. Anotado en `docs/mejoras-proceso/to-do.md` (heredado F0). NO bloqueante para merge.

- **`deepagents.SubAgent` es un `TypedDict`**, no clase. Pasar `subagents=[AUDIT_INSPECTOR_SUBAGENT]` con dict literal funciona. `model:` (override) acepta `'provider:model-name'` o `BaseChatModel`. F4/F5 que necesiten subagent con tools propios o modelo distinto: agregar `tools: [...]` y/o `model: 'openai:gpt-4o-mini'` al dict.

---

## Recomendaciones accionables para F3 (Brand summary lighthouse)

1. **Antes de empezar:** correr `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/architecture/test_copilot_provider_compliance.py tests/architecture/test_no_new_copilot_module_imports.py tests/architecture/test_copilot_anchors.py tests/architecture/test_deep_agent_harness_invariants.py tests/modules/copilot/test_deep_agent_harness.py tests/modules/copilot/test_plan_card_emission.py tests/modules/copilot/test_pinned_memory_repository.py -q -o addopts="" --timeout=30` (60+ tests verdes, incluye F1 + F2 baseline).

2. **F3 debe inyectar el brand_summary en `build_system_prompt`, NO en el harness deep_agent.** Razón: tanto legacy como deep_agent rebuildean prompt por turn y ambos llaman a `build_system_prompt(state)`. Inyectar allí cubre los dos paths con un único punto.

3. **Hook listo:** `BrandContextInjector.inject_for(target_route, tenant_id) -> str | None` ya existe en `brand/copilot_provider/context_inject.py` (F1) devolviendo `None`. F3 lo implementa fetcheando `brand_summary` de DB. `build_system_prompt` debe llamarlo via `provider_registry.context_injectors_for(route_or_tenant)` y prependerlo como prefix estable cacheable.

4. **Modelo NANO para regen:** `ModelRole` no expone NANO hoy — `AGENT`/`FAST`/`REASONING`/`VISION`/`EMBEDDING`. F8 introduce el 4-tier router NANO/MINI/REASONING/HEAVY. F3 puede usar `ModelRole.FAST` (gpt-4o-mini) hasta que F8 separe NANO. NO inventar `ModelRole.NANO`.

5. **Migración brand_summary:** copiar pattern de `alembic/versions/067_copilot_pinned_memory.py` (CREATE TABLE IF NOT EXISTS + raw SQL). Recordar registrar el nuevo modelo en `tests/conftest.py::db_engine`.

6. **Si F3 introduce nuevo `[COPILOT-*]` anchor**, agregarlo a `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY`. Límite 25 entradas (F2 dejó 21, agregando `COPILOT-DEEP-AGENT-V2`).

7. **Test contract fijo:** golden tests F1 + nuevo `test_deep_agent_harness_invariants.py` deben seguir verdes. NO romper la dispatch flag — si F3 quiere `brand_summary` siempre, inyecta en el path común antes del split, no después.

---

## Riesgos abiertos

- **Cache hit rate del system prompt va a empeorar con harness ON.** El sufijo deep-agent es estable, pero `build_system_prompt` tiene snapshots dinámicos (completion %, behavior summary). Cuando F3 pre-pendea brand_summary cacheable + F8 reordena el prompt para maximizar prefix cache, evaluar mover el sufijo deep-agent al inicio (después de brand_summary, antes de snapshots). Métrica baseline a tomar en F8: `cache_creation_input_tokens` vs `cache_read_input_tokens` con flag ON vs OFF.

- **Tools del registry pasan al deep agent SIN filtrar por compatibilidad.** El built-in `task()` puede llamar `audit_inspector` con cualquier tool del parent (heredados via `default_tools`). No hay sandboxing por subagent en F2. F4/F5 que añadan subagents con tools sensibles (mutación/escritura) deben declarar `tools=[...]` explícito en el SubAgent dict para restringir scope.

- **`langchain-anthropic 1.4.1` instalado y NO usado todavía.** Heredado F1. Si F3 no lo requiere, F4 puede evaluar quitarlo o seguir como dep transitiva de deepagents 0.5.3 (probablemente no removible sin fork). NO bloquea.

- **Streaming de `on_tool_start` para `write_todos` no genera `block_start` separado.** Hoy emitimos solo `block_append` en `on_tool_end`. El usuario ve el plan_card aparecer atómicamente, no la "barra de planificación". Si F3 o F4 requieren feedback de "está pensando" más temprano, agregar `block_start` con type `plan_card` partial vacío en `on_tool_start` + `block_delta` en end. Hoy no es prioridad — el plan_card aparece en <1s.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/application/orchestrator/deep_agent.py::build_deep_agent_graph(state, *, llm=None, tools=None)` — F4/F5 pueden inyectar `tools` (override) en tests. En prod, route-aware automatic.
- `backend/src/modules/copilot/application/orchestrator/subagents/__init__.py` — agregar nuevos `SubAgent` dicts (F4: `URL_ANALYZER_SUBAGENT`, F5: `DATA_QUERY_SUBAGENT`) y exportarlos. `deep_agent.py` los pasa a `subagents=[...]` con un `extend()`.
- `backend/src/modules/copilot/infrastructure/repositories/pinned_memory_repository.py::CopilotPinnedMemoryRepository` — CRUD listo. F4 implementa `pin_to_memory(path)` tool que llama `repo.upsert(...)` con tenant/user del contextvar.
- `_write_todos_to_plan_card(tool_input)` en `chat.py` — helper público (módulo-level). Si F4/F5 necesitan otros plan_card-like blocks (subagent_progress_card), copiar el patrón.
- `tests/architecture/test_deep_agent_harness_invariants.py` — 5 fitness tests. F4/F5 que toquen el harness deben dejarlos verdes; agregar nuevos invariants (subagent allowlist, tool sandboxing) acá.
- `COPILOT_DEEP_AGENT_V2` flag — Settings. F4/F5 corren con flag ON en su entorno de dev. Encender en prod cuando F4 + F5 estén estables (F2 §5.6).

---

## Fuentes research útiles

- [Deep Agents overview · LangChain Docs](https://docs.langchain.com/oss/python/deepagents/overview) — confirmó signature exacta `create_deep_agent(model, tools, system_prompt, subagents, backend, ...)` y que retorna `CompiledStateGraph`.
- [Backends · LangChain Docs](https://docs.langchain.com/oss/python/deepagents/backends) — confirmó `StateBackend` default (ephemeral) + `CompositeBackend(default=..., routes={"/memories/": StoreBackend(...)})` para persist. Decidió posponer el composite a F4.
- [`deepagents` 0.5.3 PyPI release 2026-04-15](https://pypi.org/project/deepagents/) — confirmó última versión, sin breaking changes desde 0.5.0.
- Inspección directa `deepagents.middleware.subagents.SubAgent` — confirmó que es `TypedDict` con `{name, description, system_prompt}` requeridos + `{tools, model, middleware, ...}` opcionales. Esto guió el shape del `AUDIT_INSPECTOR_SUBAGENT`.
- Inspección directa `langchain.agents.middleware.todo.write_todos` — confirmó que el tool retorna `Command(update={"todos": ..., "messages": [ToolMessage(...)]})`. Esto motivó usar **args** (no output) para sintetizar el plan_card.
