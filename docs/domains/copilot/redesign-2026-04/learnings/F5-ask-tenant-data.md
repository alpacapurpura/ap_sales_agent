# Learnings — F5 ask_tenant_data subgraph

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `333767c1`)

---

## Resumen 3 líneas

- Tool transversal `ask_tenant_data(question, output_channel)` + subagent `DATA_QUERY_SUBAGENT` con `tools=[ask_tenant_data]` aislado. Pipeline determinístico de 6 pasos (intent_classifier → query_builder → executor → state_check → synthesizer + cache wrapper) con SOLO 2 LLM calls (intent + synth, ambos FAST). Cobertura: 3 kinds (`offer_lookup` / `lead_count` / `conversation_count`) consumidos via nuevo port `DataAccessProvider` — cero imports cross-module nuevos, ratchet `copilot → módulo` sigue en **22**.
- Decisión no obvia: el port toma `context: Mapping[str, Any]` con `db` opcional en lugar de inyectar `Session` por constructor. Tests pasan `db` desde la fixture; producción abre `SessionLocal()` una vez en el tool y la propaga a todos los accessors. Evita el lío "provider abre/cierra su propia session" que F4 sí padeció (DI de `db_factory` en cada tool).
- Listo para F6: el patrón "pipeline determinístico con LLM calls puntuales en bordes + dispatcher central" que usa F5 es exactamente lo que F6 (workflow unification) puede generalizar para reemplazar guided/procedure/extraction. F7 conecta el `synthesizer.SUPPORTED_OUTPUT_CHANNELS` registry con `ChannelFormat` real; F8 puede asignar `intent_classifier` al tier NANO cuando exista.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Pipeline determinístico de 6 pasos dentro de UN tool** (no LangGraph subgraph LLM-driven). | El text-to-sql-agent oficial de deepagents 0.5.3 usa un único `create_deep_agent` con SQL toolkit y planning — sin subgrafo, sin nodos LangGraph. Replicar nodos LangGraph aquí significa 4-6 LLM calls por pregunta cuando 2 alcanzan. Pipeline determinístico permite testar cada stage sin red, costo predecible (~2 calls FAST), y es cacheable end-to-end con TTL 60s. | Subgrafo con nodos LangGraph (intent_node → entity_node → plan_node → ...). Habría duplicado la lógica del orchestrator existente, agregado 4+ LLM calls por turn, y hecho el cache de respuestas mucho más complejo (cachear en cada nodo o sólo en la salida final). |
| **Port `DataAccessProvider` con `supports(kind)` + `execute(*, tenant_id, plan, context)`**, NO interface methods tipadas (`search_offers`/`count_leads`/`count_conversations`). | Una interface concreta crece linealmente con cada nueva pregunta (Sprint 8 quiere "ventas en el mes" → otra method). Despacho por `kind` mantiene el port estable: el módulo nuevo solo declara qué kinds soporta y la dispatcher itera. Reduce la frontera del port a 2 métodos. | `class DataAccessProvider: search_offers(...); count_leads(...); count_conversations(...)`. Cada provider implementaría todos los métodos (la mayoría devolviendo `NotImplementedError`). Provider nuevo = método nuevo = recompilar el port. |
| **`context: Mapping[str, Any]` con `db` opcional vs. `db` en `__init__`**. | F4 puso `db_factory` en `__init__` y eso obliga a abrir/cerrar session en cada provider. Cuando 3 providers responden a 3 kinds en el mismo turno (compose multi-pregunta), abrirías 3 sessions. Con context-pass-through, el tool abre 1 session y la pasa a todos los providers. Tests pasan `context={"db": db}` directo. | Provider con `db` en `__init__`. Más agresivo de probar (cada provider necesita un fixture session) y caro en producción. |
| **`ConversationDataAccessProvider` vive en `copilot/application/data_access/`** (NO en un `copilot/copilot_provider/` recursivo) y se registra **directo** en el dispatcher del tool (no via discovery). | Crear `copilot_provider/` dentro del propio módulo copilot es semánticamente raro (el provider pattern es para módulos externos al copilot). Registrar el accessor own-module directo en el dispatcher (`_default_accessors` lo prepende a la tupla) deja la discovery limpia para módulos externos. | `copilot/copilot_provider/data_access.py` cargado via discovery. El registry trataría a copilot como uno más entre los 9 módulos descubiertos, y discovery debería evitar cargar al propio copilot — patrón frágil. |
| **Migration 070 NO usa `DO $$ EXCEPTION ... END $$;` para `CREATE EXTENSION pg_trgm`**. Falla fuerte si Postgres rechaza. | Si en algún env futuro el role no tiene privilegio para crear pg_trgm, el silent-degrade dejaría `OfferRepository.search` con seq scan en producción sin que nadie se entere hasta que las queries se vuelvan lentas. Mejor que la migración falle ruidosamente para detectar el problema en deploy. | Wrap en `DO $$ ... EXCEPTION WHEN insufficient_privilege ... END $$;`. F4 documentó este patrón para "production safety", pero acá la consecuencia (perf silenciosa degradada) es peor que el fail-fast. |
| **Cache wrapper: TTL 60s puro, sin invalidation granular**. | Mutaciones de offers/leads/conversations son raras dentro de una ventana de 60s. Implementar invalidation requiere hookear cada mutation tool (offer.update, lead.create, ...) — alta superficie, alto riesgo de drift. F8 puede medir si el caso "user pregunta lo mismo 2 veces seguidas" justifica invalidation granular. | Bust cache on mutation events (subscribir a EventBus). Costo de implementación + mantenimiento alto vs. el caso de uso real (preguntar lo mismo dos veces en 60s es raro, y la diferencia es 1 turn). |
| **Anchor budget: SOLO `COPILOT-ASK-TENANT-DATA-F5` agregado** (1 anchor, llega a 25/25). | F5 toca varios archivos pero el anchor es semánticamente uno: "F5 introdujo el subgraph de Q&A". Anchors per-stage (intent_classifier, executor, etc) inflan el registry sin ROI; los stages se descubren navegando desde el tool. F6 que añada anchors va a tener que bumpiar el límite a 26+. | 3-5 anchors per-stage. Inflación del registry y obliga a bumpiar el límite igual. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **El test `test_provider_ports.py::TestProtocolCompliance::test_root_provider_protocol` rompió silencioso al agregar `data_access` al Protocol `CopilotProvider`.** El `_StubProvider` allí declara explícitamente todos los sub-port methods; agregar uno nuevo al Protocol invalida el isinstance check porque Python `runtime_checkable` chequea presencia de TODOS los métodos. Cualquier fase que agregue un nuevo sub-port al Protocol (F6 puede agregar `data_access` análogos para workflows persistidos) DEBE actualizar `_StubProvider` con un `def <new_port>(self) -> object | None: return None`. El error es `assert isinstance(_StubProvider(), CopilotProvider) → False` y no menciona qué método falta — debugging tiene que ser por inspección.

- **`replace_all` en `ruff format` reformateó test files que escondían `propósito` con tilde**, y luego `replace_all=true` en mi Edit reemplazó todas las apariciones, incluyendo el `name_query="propósito"` (el query que SÍ debía tener tilde para matchear el seed `"Programa Propósito y Prosperidad"` en SQLite ILIKE). SQLite ILIKE es **accent-sensitive**, mientras que pg_trgm en producción normaliza trigramas (case-insensitive, accent-aware). El test rompe en SQLite pero pasaría en Postgres — engañoso. Patrón para tests de fuzzy match: dejar el query con la grafía exacta del seed (`name_query="Propósito"`) + comentario explicando la divergencia SQLite vs PG. La regla aún más simple: separar los strings que tienen significado semántico (el query real del usuario) de los identificadores Python (`proposito` ASCII).

- **`dateparser` 1.4.0 con `RELATIVE_BASE=anchor.replace(tzinfo=None)`** es el patrón correcto para inyectar un "now" — la lib no acepta tz-aware como base. Si pasás tz-aware, parsea pero el offset se pierde en cálculos relativos ("hace 2 días" desde 14:00 UTC se vuelve 14:00 local del sistema). En tests determinísticos: siempre `replace(tzinfo=None)` para `RELATIVE_BASE` y luego `replace(tzinfo=timezone.utc)` en el output.

- **`langchain_core` `tool` decorator es síncrono cuando lo llamás como `@tool` sin args.** Ambos `ask_tenant_data` (F5) y `fetch_url` (F4) lo usan como `@tool async def ...` directamente — funciona porque langchain detecta async via `inspect.iscoroutinefunction`. Si una fase futura quiere `@tool("name", args_schema=Pydantic)` con async, también funciona; no usé args_schema porque la signature simple `(question: str, output_channel: str = "chat")` ya genera el schema correcto.

- **`ALWAYS_AVAILABLE_GROUPS` con `data_query`** = el LLM lo ve en cada turn de cada ruta, agregando ~80 tokens al prompt fijo. Vale la pena (Q&A debe ser transversal), pero medir el impacto en cache hit rate cuando F8 instrumente. Si crece el toolset transversal, considerar mover algunas tools a "lazy bind" (sólo cuando una keyword aparece en el último mensaje del user) — F8 territory.

- **El ratchet `KNOWN_COPILOT_TO_MODULE_IMPORTS` SIGUIÓ en 22 entradas**, no shrunk. F5 no migró offer/crm tools al provider pattern (solo agregó `data_access` accessor). Si F-pos migra `offer_section_tools.py` (5 imports de `copilot → brand/scheduling/social_proof`) podría shrink el ratchet a ~17. Mismo argumento para `crm_tools.py`.

---

## Recomendaciones accionables para F6

1. **Antes de empezar:** correr la suite F0-F5 para baseline:
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/golden/ \
     tests/architecture/ \
     tests/modules/copilot/test_deep_agent_harness.py \
     tests/modules/copilot/test_plan_card_emission.py \
     tests/modules/copilot/test_pinned_memory_repository.py \
     tests/modules/copilot/test_inspiration_repository.py \
     tests/modules/copilot/test_trafilatura_client.py \
     tests/modules/copilot/test_url_inspiration_analyzer.py \
     tests/modules/copilot/test_fetch_url_tool.py \
     tests/modules/copilot/test_pin_to_memory_tool.py \
     tests/modules/copilot/test_inspirations_layer.py \
     tests/modules/copilot/test_data_access_port.py \
     tests/modules/copilot/test_conversation_data_access_provider.py \
     tests/modules/copilot/test_ask_tenant_data_*.py \
     tests/modules/copilot/test_data_query_cache.py \
     tests/modules/copilot/test_conversation_repository_count_window.py \
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
     -q -o addopts="" --timeout=60
   ```
   Debe ser ~250+ verde (F0-F5 acumulado).

2. **Workflow unificado puede reusar el patrón pipeline F5.** F5 demostró que un tool puede orquestar internamente (intent → plan → execute → synth) sin necesidad de exponerse como subgrafo LangGraph. F6 puede convertir cada Workflow en un tool transversal que internamente corre nodos Python, con UN único punto de LLM call (planning) en lugar de un nodo-LLM por step. Esto preserva el cache hit rate del system prompt y minimiza tool calls visibles al main agent.

3. **Si F6 agrega un sub-port nuevo a `CopilotProvider` Protocol** (probable: `WorkflowProvider` ya existe pero F6 lo va a expandir), actualizar `tests/modules/copilot/domain/test_provider_ports.py::_StubProvider` con un método return-None para el nuevo port. Sin esto, `test_root_provider_protocol` rompe sin dejar pista clara.

4. **Anchor budget agotado (25/25).** Si F6 introduce anchors `[COPILOT-WORKFLOW-F6]`, bumpiar `assert len(ANCHOR_REGISTRY) <= 26` (o 27/28 si va a ser una fase con varios anchors) en `tests/architecture/test_copilot_anchors.py`. Documentar el bump en el commit.

5. **`output_channel` parameter en `ask_tenant_data` ya viaja end-to-end al `synthesizer.SUPPORTED_OUTPUT_CHANNELS` registry.** F7 (channel formatter) puede reemplazar `_CHANNEL_HINTS` en `synthesizer.py` con el `ChannelFormat` registry real sin tocar la signature del tool. La interface está congelada: `output_channel: str` con fallback a `"chat"` si el canal no está soportado.

6. **No agregar más LLM calls al pipeline F5.** Si F6 quiere que `ask_tenant_data` también explique "por qué dió esa respuesta", esa explicación debe vivir en el prompt del synthesizer (un solo call), no en un nodo nuevo. La regla F5 es: **2 calls FAST por pregunta, máximo**.

7. **Hook listo para F8 (NANO tier):** cuando F8 introduzca `ModelRole.NANO`, cambiar la línea `llm = LLMFactory.get_service().get_client(ModelRole.FAST)` en `intent_classifier.py:126` por `ModelRole.NANO`. El intent classification es trivial (~80 tokens output, JSON estructurado) y NANO basta. El synthesizer puede quedarse en FAST porque genera prosa.

---

## Riesgos abiertos

- **Cache hit rate del system prompt no medido** (riesgo heredado de F3+F4). Agregar `data_query` a `ALWAYS_AVAILABLE_GROUPS` aumenta tokens fijos del prompt en ~80 tokens. F8 cuando instrumente debe revisar antes/después de F5 si el cache_hit cambió materialmente. Si cae > 5%, considerar mover `data_query` a un route map subset (no transversal).

- **`OfferRepository.search` es accent-sensitive en SQLite tests pero accent-aware en pg_trgm prod.** Tests pasan en local con grafías exactas pero un usuario en prod podría escribir "proposito" sin tilde y matchear "Propósito" — comportamiento divergente entre test y prod que podría enmascarar regresiones. Solución cuando pese: instalar `unaccent` extension PG y usar `unaccent(name) % unaccent(query)` para igualar el comportamiento. Documentar en `docs/mejoras-proceso/to-do.md` cuando aparezca el primer ticket.

- **`pg_trgm.similarity_threshold` default 0.3 hardcoded en repo.** Para programas con nombres muy cortos (≤6 chars) el umbral 0.3 es demasiado permisivo — devuelve ofertas no relacionadas. F-pos UX puede agregar un slider en admin Streamlit para tunear por tenant, pero hoy no urgente — los tests muestran 0 falsos positivos con queries ≥4 chars.

- **F5 NO modifica `extract_from_doc.py` ni `extraction_tools.py`** — estos son sistemas paralelos (F4 / F2 / pre-redesign). F6 (workflow unification) puede unificar `ask_tenant_data` + `extract_from_doc` + `fetch_url` bajo un mismo `Workflow` concept, pero F5 deliberadamente no lo intenta para mantener el scope cerrado.

- **El `_default_accessors` opens session via `SessionLocal()`** dentro del tool — funciona pero significa que si una request abierta del orchestrator tiene su propia session, el tool abre OTRA session paralela. Para reads (puro select) está bien, pero si en F6 alguna mutation tool entra al pipeline, hay riesgo de double-commit. F6 debe revisar si conviene propagar la session del orchestrator via contextvar al tool.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/domain/ports.py::DataAccessProvider` + `DataQueryPlan` + `DataQueryResult` — port estable. F6/F8 nuevas kinds (`sale_lookup`, `revenue_metric`) solo necesitan: enriquecer un repo del módulo dueño + crear `<module>/copilot_provider/data_access.py` que `supports(new_kind)`.

- `backend/src/modules/copilot/application/tools/ask_tenant_data/intent_classifier.py::SUPPORTED_KINDS` — frozenset que el LLM debe respetar. F-pos que agregue un nuevo kind debe extender este set + actualizar el system prompt + añadir el provider correspondiente.

- `backend/src/modules/copilot/application/tools/ask_tenant_data/synthesizer.py::SUPPORTED_OUTPUT_CHANNELS` + `_CHANNEL_HINTS` — F7 reemplaza `_CHANNEL_HINTS` con el registry real `ChannelFormat`. La función `synthesize_answer` es estable; F7 sólo edita el dict.

- `backend/src/modules/copilot/infrastructure/cache/data_query_cache.py::DataQueryCache` + `make_cache_key` — F-pos puede reusar el wrapper para cachear otras tools transversales (knowledge_search F10) cambiando solo el prefijo de la key.

- `backend/src/modules/copilot/application/orchestrator/subagents/data_query.py::DATA_QUERY_SUBAGENT` — patrón "subagent con 1 tool sandbox" replicable. F-pos que agregue `pin_to_memory_subagent` o `revenue_subagent` debe seguir el mismo TypedDict shape: `{name, description, system_prompt, tools=[ONE_TOOL]}`.

- `backend/src/modules/copilot/application/data_access/__init__.py` — directorio para accessors own-module (no via discovery). F-pos que agregue `MutationJournalDataAccessProvider` o `InspirationDataAccessProvider` (Q&A sobre las inspirations F4) puede agregarlos acá y registrarlos en el `_default_accessors` del tool.

- `backend/alembic/versions/070_pg_trgm_indices.py` — patrón idempotente para CREATE EXTENSION + GIN indices. F-pos que agregue fuzzy-match a otra tabla copia este pattern (ej: `customer_profiles.full_name` para "buscame a María Pérez").

---

## Fuentes research útiles

- [deepagents text-to-sql-agent example](https://github.com/langchain-ai/deepagents/tree/main/examples/text-to-sql-agent) — confirmó que el patrón oficial NO usa subgrafo con nodos LLM-driven, usa un único `create_deep_agent` con SQL toolkit. Esto cambió mi enfoque inicial (subgrafo LangGraph) hacia "pipeline determinístico dentro del tool" con solo 2 LLM calls. Decisión clave de F5 nace acá.

- [PostgreSQL pg_trgm 18 docs](https://www.postgresql.org/docs/current/pgtrgm.html) — confirmó que `similarity()` operator usa lower-cased trigrams internally (case-insensitive sin `lower()`) pero NO accent-aware sin `unaccent`. Por eso mismo el SQLite ILIKE en tests es accent-sensitive divergente — gotcha documentado en sorpresas.

- [DateParser 1.4.0 docs](https://dateparser.readthedocs.io/en/latest/) — confirmó que `RELATIVE_BASE` requiere naive datetime (sin tzinfo). Si pasás tz-aware, parsea pero las relativas se rompen. Patrón aplicado en `date_parser.py`.

- [LangGraph Text-to-SQL patterns 2026](https://docs.langchain.com/oss/python/langgraph/sql-agent) — confirmó que la arquitectura "decomposed nodes" del plan F5 (intent → entity → plan → execute → check → synth) es el patrón canónico LangGraph, pero **también** que se puede colapsar a 2 LLM calls cuando el dispatch es por enum cerrado (el caso F5: 3 kinds), no SQL libre. Validó nuestra decisión de no usar subgrafo.

Tessl tiles consultados: `tessl__fastapi`, `tessl__langgraph` (no instalé tile nuevo — los patterns LangGraph que necesitábamos están cubiertos en el deepagents repo + docs oficiales).
