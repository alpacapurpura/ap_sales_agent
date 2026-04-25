# Learnings — F6 Workflow unification

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `08894f7a`)

---

## Resumen 3 líneas

- Domain `Workflow` declarativo + `WorkflowEngine` Python deterministic + aggregator `collect_workflows` + migration 071 idempotente (`ADD COLUMN workflow_state JSONB IF NOT EXISTS` + backfill desde `procedure_state`, **sin DROP**) + pilots brand (`setup_brand_minimal`) y offer (`design_offer_from_url`) wired via `WorkflowProvider.workflows()`. Coexistencia 4 sistemas garantizada — guided/procedure/extraction_card_flow intactos.
- Decisión clave: el engine NO usa LangGraph subgraph (research abril 2026 valida F5 — pipelines deterministic con LLM calls puntuales beat 2-4× subgraphs LLM-driven cuando dispatch es enumerable). Engine es Python puro + `importlib` resolución lazy de handlers. F-pos absorbe la lógica viva de `guided/block_generator.py` etc nodo-a-nodo en los pilots placeholders.
- Anchor budget bumped 25 → 26 (`COPILOT-WORKFLOW-F6`). Ratchet `copilot → módulo` sigue **22** (provider port consume `Workflow` types desde `copilot.domain.workflow`, agregado a `_PROVIDER_CONTRACT_IMPORTS` en `test_ddd_boundaries.py` siguiendo el mismo patrón de inversión de dependencia que `domain.ports`).

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **`handler_ref: str` (dotted path) en vez de `Callable` directo en `WorkflowNode`.** | (a) Mantiene `Workflow` instance hashable + serialisable + frozen-dataclass-friendly. (b) Evita circular-import traps cuando un módulo registra workflow cuyo handler vive en el mismo paquete (importarlo en module-load time del provider explotaría la discovery). (c) Permite arch test que valida `every handler resolves at import time` — confidence absoluta antes de runtime. | `Callable[[dict, Mapping], Awaitable[NodeOutput]]` directo. Funciona pero rompe el frozen=True por falta de hashabilidad confiable y obliga a importar todo el grafo de handlers al boot. |
| **`ADD COLUMN workflow_state JSONB IF NOT EXISTS` + backfill, NUNCA `RENAME COLUMN`.** | Plan F6 §5.2 sugería rename idempotente, pero PG no permite rename en JSONB column durante write traffic sin lock. ADD COLUMN + backfill + dual-read fallback (en `get_workflow_state(..., fallback_to_procedure=True)`) es safer y permite rollback granular. F-pos cutover en una migration separada cuando confirmemos que código no lee `procedure_state`. | RENAME COLUMN. Live conversations en prod tendrían blackout durante el lock. |
| **Engine ejecuta handlers vía `importlib.import_module` lazy** (no eager imports de todos los handlers en module-load). | Evita el bug F4 documentado: provider scan abre conexiones DB en module-import time si los handlers viven en módulos que tocan ORM. Lazy resolution = primer step paga el import cost, subsequent steps amortizado. | Pre-resolve todos los handlers en `Workflow.__post_init__`. Tendría peor cold-start + bug de DB connections en boot replicado del F4. |
| **`extra="forbid"` en `WorkflowExecutionState` Pydantic config.** | Migración eventual de `procedure_state` (que tiene shape libre) requerirá schema disciplinado: forbid extra keys ahora previene drift silente cuando F-pos migra payloads legacy. | `extra="ignore"`. Acepta payloads malformados pero pierde la señal de "esto no es F6 state, es procedure_state legacy" en el rehydration. |
| **`StrEnum` para `WorkflowTrigger`, no `Enum(str)`.** | Ruff `UP042` enforce desde py311+. `StrEnum` es la API moderna y semánticamente igual. | `class WorkflowTrigger(str, Enum)`. Funciona pero falla el ruff. |
| **Workflow types agregados a `_PROVIDER_CONTRACT_IMPORTS` en test_ddd_boundaries**, NO a `KNOWN_CROSS_MODULE_IMPORTS`. | F1 estableció el patrón: provider contracts (importes desde `{module}/copilot_provider/`) son inversión de dependencia, no acoplamiento. `Workflow`/`WorkflowNode`/`NodeOutput` son parte del contrato — el ratchet sigue stable en 22 sin agregar 4 entradas al allowlist. | Agregar 4 entries a `KNOWN_CROSS_MODULE_IMPORTS`. Diluye la señal del ratchet y obliga a editarlo cada vez que un nuevo provider declare workflow. |
| **Pilots con handlers placeholder (return `NodeOutput()` shape correcto, NO migración real de la lógica viva).** | F6 entrega declarative skeleton + 2 pilots (per prompt): "F7/F8 NO se mezclan". La migración real de `guided/block_generator` etc es trabajo cutover de F-pos. Placeholders preservan el contrato end-to-end (arch tests verifican handlers resuelven, engine ejecuta synthetically) sin tocar la lógica live que sigue corriendo en paralelo. | Migrar la lógica real ahora. Rompería el principio "cada fase entrega una cosa" y abriría riesgo de regresar el sistema live. |
| **Snapshot golden `route_tool_selection.json` reparado inline (F5 leftover).** | F5 agregó `ask_tenant_data` a `ALWAYS_AVAILABLE_GROUPS` pero olvidó `UPDATE_GOLDEN=1`. Sin baseline verde, F6 no puede detectar regresiones. Reparado dentro del commit F6 con una nota explícita. | Reportar y dejarlo para fix separado. Habría bloqueado el TDD F6 hasta merge previo. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **`DDD boundaries` test rechaza imports `brand → copilot` Y `offer → copilot` cuando el módulo agrega `copilot_provider/workflows.py` o `workflow_handlers.py` que importan `Workflow`/`WorkflowNode`/`NodeOutput`/`WorkflowTrigger` desde `copilot.domain.workflow`.** F1 dejó este patrón documentado para `copilot.domain.ports` (vía `_PROVIDER_CONTRACT_IMPORTS` allowlist en `test_ddd_boundaries.py:60`). F6 extiende el mismo registry con `copilot.domain.workflow`. Cualquier fase futura que agregue módulos nuevos a `copilot.domain.*` que sean parte del provider contract (ej. F7 podría hacer `copilot.domain.output_channels` consumido por providers) debe replicar.

- **`extra="forbid"` en Pydantic state schemas hace que `engine.start(..., initial_data={"unknown_field": ...})` retorne `ValueError`**, NO el ValidationError raw. Mi engine envuelve el `model_validate` en `try/except Exception` y re-raise como ValueError. Si una fase futura agrega un schema con campos opcionales que se setean dinámicamente, recordar que el strict mode trasciende la signature del workflow. Para flexibilidad post-cutover, considerar `model_config = {"extra": "allow"}` en schemas que necesiten merge con state legacy de procedure_state.

- **`@dataclass(frozen=True, slots=True)` sobre `Workflow` con `nodes: tuple[WorkflowNode, ...]`** funciona porque las tuplas son inmutables y los nodos son frozen también. Pero si una fase futura quiere mutación in-place del workflow (ej. F8 reordenando nodos basado en heurística), el frozen rompe. Solución: crear nuevo Workflow via `dataclasses.replace()` — frozen instances soportan replace.

- **Test `test_workflow_state_persistence.py` requiere `CopilotConversationModel` import en `tests/conftest.py::db_engine`.** Heredé el patrón F2/F3/F4. Mi primera corrida pasó por casualidad (algún test previo había importado el modelo); siguiendo el ratchet F2/F3 lo agregué explicit a la fila 131 del conftest para que la suite sea robusta a randomización.

- **`F5` dejó leftover en golden snapshot `route_tool_selection.json`** (ask_tenant_data en `ALWAYS_AVAILABLE_GROUPS` sin actualizar el snapshot). Detectado en mi baseline pre-F6 — el commit F5 declaraba "Suite full 4368+ verde" pero ese golden test fallaba aislado desde el commit F5. Reparé en el commit F6 con `UPDATE_GOLDEN=1`. Cualquier fase futura que toque `_BASE_TOOL_GROUPS` o `ALWAYS_AVAILABLE_GROUPS` o `ROUTE_TOOL_MAP` debe correr el golden test antes de cerrar y aceptar el diff explícitamente, no asumir que la suite full lo cubre.

- **Test flaky heredado `test_streaming_integration` sigue ahí.** F6 NO tocó streaming/orchestrator pero el sweep full lo deja como unique-failure-aislado. Misma operativa heredada F2-F5: correrlo standalone después del sweep.

- **Test flaky heredado `test_editable_fields_ssot::test_no_cross_domain_duplicates`** sigue ahí. F6 NO tocó editable_fields. Operativa: standalone passes, dentro de la suite full FAIL por order-dep.

- **`workflow_handlers.py` separado de `workflows.py`.** Plan inicial era todo en un archivo, pero los handlers (async functions con state mutations) son más larga vida y se editan independientemente del workflow declaration. Separarlos:
  - mantiene el `workflows.py` como SSoT declarativo legible (pure data).
  - permite arch test que verifica handler_ref resolution sin cargar handler bodies (más rápido).
  - simplifica F-pos cutover: absorber lógica viva en handlers no toca el workflow declaration.

---

## Recomendaciones accionables para F7

1. **Antes de empezar:** correr la suite F0-F6 baseline (~821 verde):
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/golden/ \
     tests/architecture/ \
     tests/modules/copilot/test_workflow_dataclass.py \
     tests/modules/copilot/test_workflow_engine.py \
     tests/modules/copilot/test_workflow_registry.py \
     tests/modules/copilot/test_workflow_state_persistence.py \
     tests/modules/copilot/test_deep_agent_harness.py \
     tests/modules/copilot/test_plan_card_emission.py \
     tests/modules/copilot/test_pinned_memory_repository.py \
     tests/modules/copilot/test_inspiration_repository.py \
     tests/modules/copilot/test_inspirations_layer.py \
     tests/modules/copilot/test_data_access_port.py \
     tests/modules/copilot/test_conversation_data_access_provider.py \
     tests/modules/copilot/test_ask_tenant_data_intent_classifier.py \
     tests/modules/copilot/test_ask_tenant_data_synthesizer.py \
     tests/modules/copilot/test_ask_tenant_data_executor.py \
     tests/modules/copilot/test_ask_tenant_data_query_builder.py \
     tests/modules/copilot/test_ask_tenant_data_state_check.py \
     tests/modules/copilot/test_ask_tenant_data_integration.py \
     tests/modules/copilot/test_ask_tenant_data_date_parser.py \
     tests/modules/copilot/test_data_query_cache.py \
     tests/modules/copilot/test_conversation_repository_count_window.py \
     tests/modules/copilot/domain/test_provider_ports.py \
     tests/modules/offer/test_offer_repository_search.py \
     tests/modules/offer/test_offer_data_access_provider.py \
     tests/modules/crm/test_lead_repository_count_inbound.py \
     tests/modules/crm/test_crm_data_access_provider.py \
     tests/modules/brand/test_brand_summary_repository.py \
     tests/modules/brand/test_brand_section_updated_event.py \
     tests/modules/brand/test_brand_context_injector.py \
     tests/shared/workers/test_brand_summary_regen.py \
     tests/shared/application/test_brand_summary_event_handlers.py \
     tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
     tests/modules/copilot/test_fetch_url_tool.py \
     tests/modules/copilot/test_pin_to_memory_tool.py \
     tests/modules/copilot/test_trafilatura_client.py \
     tests/modules/copilot/test_url_inspiration_analyzer.py \
     -q -o addopts="" --timeout=60
   ```

2. **F7 reemplaza `_CHANNEL_HINTS` en `application/tools/ask_tenant_data/synthesizer.py`** con el `ChannelFormat` registry real. La signature `synthesize_answer(..., output_channel: str)` está congelada — F7 sólo edita el dict + agrega el registry domain. F5 dejó `SUPPORTED_OUTPUT_CHANNELS = frozenset({"chat", "whatsapp", "email", "sms"})` como hook estable.

3. **`output_channels.py` debe ir en `copilot/domain/`** (donde el plan F7 lo ubica), NO en cada provider. El registry es agnóstico — providers que registren canales propios usan `register_channel(format)` (extension hook). Si F7 hace `output_channels.py` parte del provider contract (e.g. providers declaran canales), agregar `src.modules.copilot.domain.output_channels` a `_PROVIDER_CONTRACT_IMPORTS` en `test_ddd_boundaries.py` (mirror del F6 pattern).

4. **Si F7 introduce sub-port nuevo en `CopilotProvider` Protocol** (e.g. `channel_provider()`), actualizar `tests/modules/copilot/domain/test_provider_ports.py::_StubProvider` con el método return-None. F5 documentó este gotcha + F6 no lo tocó (no nuevos sub-ports), pero F7 podría.

5. **Anchor budget está en 26/26 (techo bumpeado a 26 por F6).** Si F7 introduce `COPILOT-CHANNEL-FORMATTER-F7`, bumpear `assert len(ANCHOR_REGISTRY) <= 27` en `tests/architecture/test_copilot_anchors.py:87`.

6. **F7 puede consumir `WorkflowExecutionState.data["output_channel"]`** si un workflow node necesita formatter info — el state schema es per-workflow (Pydantic BaseModel) y cada workflow declara qué campos guarda. La integración natural: handler escribe `output_channel` en data, synthesizer lo lee.

7. **El test flaky `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates` siguen heredados.** Si F7 toca synthesizer/streaming, correr aislado primero. F-housekeeping eventual debe atacarlos.

---

## Riesgos abiertos

- **Coexistencia 4 sistemas (guided + procedure + extraction_card_flow + Workflow nuevo) NO está orchestrada todavía.** F6 ship el motor + pilots, pero el chat orchestrator (`copilot/application/orchestrator/chat.py`) aún consume `procedure_state` y rutea via guided/procedure. F-pos cutover es responsable de cambiar el orchestrator para leer `workflow_state` + ejecutar `WorkflowEngine.step` en cada turn. Sin esa fase, los workflows F6 son zombie (declarados pero no ejecutados live).

- **Backfill `workflow_state = procedure_state`** copia payloads legacy SIN transformación. La migration trata `procedure_state` JSONB como opaco — no lo convierte a `WorkflowExecutionState` shape. Cuando F-pos cutover lea `workflow_state` con dual-fallback y aplique `WorkflowExecutionState.from_jsonb_dict()`, los rows legacy retornarán `None` (falta `workflow_id` + `current_node`). Comportamiento esperado y aceptable: el fallback path explícito `fallback_to_procedure=True` deja a guided/procedure runner manejarlo. F-pos puede añadir un script de transformación batch si decide migrar formalmente. NO urgente.

- **`WorkflowEngine.run` tiene `max_iterations=32` hardcoded por defecto.** Si F-pos absorbe workflows con clarify loops largos (>32 turnos), pasar `max_iterations` al constructor en el callsite. Plan F6 §5.4 mencionaba `ClarifyLoopController` con cap 5 — eso conscientemente diferí porque "F6 entrega una cosa" + el cap por workflow está en `Workflow.max_clarify_questions` (no consumido aún).

- **`RUF002` ambiguous unicode (`×`) detectado y reemplazado por `x` en docstring** de workflow.py. Cualquier fase futura que escriba docstrings con multiplicación matemática debe usar ASCII `x` o agregar `# noqa: RUF002` en línea. Ruff es estricto con confusables.

- **Provider scan import side-effects** (heredado F4) sigue siendo el riesgo más alto. F6 mitigó con handlers via `handler_ref` lazy, pero workflows nuevos en futuro pueden tropezar si:
  - el `state_schema` Pydantic toca DB en `model_validate` (ej. ForeignKey lookup en validators).
  - el `metadata` field carga datos al definir el Workflow.
  Patrón seguro: schemas son tipos puros, validators son sintácticos, metadata es estático. Cargar dinámicamente solo en handlers.

- **No existe arch test que valide `state_schema` no toca DB.** Considerar agregarlo en F-pos cuando el primer workflow real se migre desde guided.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/domain/workflow.py::Workflow` — dataclass declarativo. F-pos absorbe lógica viva poblando los handler placeholders + agregando workflows reales (ej. `setup_offer`, `extract_to_offer_from_doc`).

- `backend/src/modules/copilot/application/workflows/engine.py::WorkflowEngine` — stateless, reusable. F-pos cutover instancia uno en chat orchestrator y llama `engine.step(workflow, state, context={"db": db})` por turn.

- `backend/src/modules/copilot/application/workflows/registry.py::collect_workflows` — aggregator. F-pos lo invoca al boot del orchestrator para tener `{workflow_id: Workflow}` lookup.

- `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py::update_workflow_state` + `get_workflow_state(..., fallback_to_procedure=True)` — repo accessors. F-pos reemplaza llamadas a `update_procedure_state` paso a paso.

- `backend/src/modules/{brand,offer}/copilot_provider/workflow_handlers.py` — pilots placeholder. F-pos absorbe `copilot/application/guided/block_generator.py` adentro de `probe_brand` + `ask_next_section` + `finalize_summary`. La lógica viva sigue funcionando paralelamente hasta el cutover.

- `tests/architecture/test_workflow_compliance.py` — 5 fitness tests (every workflow valid + handlers resolve + ids globally unique + no cross-module imports en `application/workflows/` + migration preserva procedure_state). F-pos no debe romperlos al absorber lógica.

- `tests/architecture/test_ddd_boundaries.py::_PROVIDER_CONTRACT_IMPORTS` ahora incluye `copilot.domain.workflow`. Patrón replicable para F7 si `output_channels.py` también es parte del provider contract.

- `WorkflowExecutionState.from_jsonb_dict()` — tolerante a payloads legacy malformados (returns None). F-pos puede usarlo para detectar conversaciones que necesitan transformación batch vs ones ready.

- Migration 071 + dual-read fallback en repo. F-pos cutover puede:
  1. Eliminar `fallback_to_procedure` flag + dejar siempre `fallback_to_procedure=False`.
  2. Crear migration 0XX que `DROP COLUMN procedure_state` (idempotente con `IF EXISTS`).
  3. Cleanup en código: remove `update_procedure_state` callers, etc.

---

## Fuentes research útiles

- [Deep Agents text-to-sql-agent example (heredado F5)](https://github.com/langchain-ai/deepagents/tree/main/examples/text-to-sql-agent) — confirmó que F5 + F6 hacen bien en NO usar subgrafo LangGraph LLM-driven. El patrón "tool transversal con stages internos en Python + LLM calls puntuales en bordes" es válido y el oficial deepagents text-to-sql-agent también lo usa.

- [LangGraph 2.0 production patterns 2026](https://dev.to/richard_dillon_b9c238186e/langgraph-20-the-definitive-guide-to-building-production-grade-ai-agents-in-2026-4j2b) — confirmó que LangGraph 1.x sigue siendo standard pero los hybrid patterns "Temporal + LangGraph" son overkill para Nicolify (no tenemos requisitos de durabilidad cross-process). JSONB postgres + dual-read fallback alcanza.

- [AI Agent workflow state persistence 2026 (fastio)](https://fast.io/resources/ai-agent-workflow-state-persistence/) — confirmó "Session State vs Workflow State" — short-term en memoria vs durable JSONB. Validó nuestro modelo `procedure_state → workflow_state` JSONB column.

- [Pydantic v2 state machine validation 2026](https://docs.pydantic.dev/latest/concepts/validators/) — confirmó que Pydantic v2 NO tiene state machine dedicado (usar `@field_validator` + `@model_validator` para transiciones). Validó nuestra decisión de usar Pydantic SOLO para validar el state schema (no como engine).

- Inspección directa F1+F5 learnings — `_PROVIDER_CONTRACT_IMPORTS` pattern + `_StubProvider` requirements. F6 replicó ambos sin sorpresa.

Tessl tiles consultados: `tessl__fastapi`, `tessl__langgraph`. No instalé tile nuevo — F5 ya determinó "los patterns LangGraph que necesitábamos están cubiertos en el deepagents repo + docs oficiales", reafirmado por F6 (no usamos LangGraph subgraph).
