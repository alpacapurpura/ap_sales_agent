# Prompt — F5 `ask_tenant_data` subgraph

> Copiar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F5 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: tool transversal `ask_tenant_data(question, output_channel="chat")` que dispara subagent `data_query` (intent_classifier NANO/FAST → entity_resolver pg_trgm → query_builder MINI → executor via repos del provider → state_check → synthesizer MINI channel-aware), permitiendo Q&A natural sobre data del tenant ("dame resumen del programa propósito-prosperidad para WhatsApp", "cuántas personas escribieron esta semana") sin SQL crudo y sin tocar §3.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§6 ask_tenant_data subgraph completo)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F5-ask-tenant-data.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md  ← APRENDIZAJES F4 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 4 queries del mandate F5 §3):
    - "text-to-SQL agentic LangGraph production 2026 entity resolution"
    - "postgres pg_trgm fuzzy search LIKE similarity 2026 best practices"
    - "LLM intent classification natural language queries Spanish 2026"
    - "LangGraph subagent decomposed nodes data retrieval 2026"
  - Tessl tiles: `tessl__fastapi`, `tessl__langgraph`. Si surge tile pg_trgm o dateparser, evaluar instalar.
  - Confirmar versiones: `dateparser` (parsing fechas español LatAm — "esta semana", "ayer", "antier", "Q1 2026"), `langgraph` 1.1.x, `pg_trgm` extensión disponible en Postgres 15.

- **Foco — no scope creep.** F5 entrega UNA cosa: tool `ask_tenant_data` + subagent `data_query` + nodos descompuestos + repos enriquecidos + cache Redis + pg_trgm migration. Channel formatter (F7) NO se mezcla — F5 acepta `output_channel` param pero solo prepara interface. Workflow unification (F6) tampoco.

- **Paso 4 — TDD obligatorio.**
  - Test por nodo: `intent_classifier` (5 categorías + unknown), `entity_resolver` (fuzzy match thresholds), `query_builder` (parsing fechas español), `executor` (repo dispatch correcto), `state_check` (active/archived flags), `synthesizer` (channel-aware basic).
  - Integration: `ask_tenant_data("cuántas personas escribieron esta semana")` → número correcto con stub LLM + repo seed.
  - Integration: `ask_tenant_data("resumen del programa <nombre>")` → fuzzy match + summary.
  - Edge: query ambigua → emit clarify.
  - Edge: 0 resultados → respuesta sugerente.
  - Test invariante: subagent `data_query` `tools=[...]` SOLO read-only repo tools. Sin mutations, sin extraction (patrón F4 url_analyzer).
  - Test golden: si F5 inyecta state-aware fragment al system prompt (resultados cached), debe ir DESPUÉS del lighthouse (F3) y DESPUÉS del inspirations layer (F4), ANTES del completion snapshot. (F4 dejó el patrón en `inspirations_layer.py`).
  - Golden snapshots F1+F2+F3+F4 verdes (correr la suite baseline antes de empezar — comando exacto en learnings F4).

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F4 (~133 tests). Debe ser verde (excepto los flaky heredados `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates`).
  - Después de cada bloque: ruff + golden + arch.
  - Si tocás streaming u orchestrator: correr `test_streaming_integration` aislado primero (heredado F0).
  - Si tocás editable_fields registry: correr `test_editable_fields_ssot` aislado primero (heredado F3).

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card/inspiration_saved) renderean igual.
  - Trace recorder registra eventos nuevos si los hay (`data_query_intent`, `data_query_executed`).
  - 4-tier model router intacto. Subagent `data_query` usa `ModelRole.FAST` para intent_classifier (no inventar `NANO`).
  - Tenant isolation absoluta — repos `search()` siempre filter `tenant_id`.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (intent vs hybrid classifier; pg_trgm threshold; cache invalidation strategy).
  - Gotchas reales: pg_trgm extension creation timing, dateparser español LatAm gotchas, repo `search()` signatures que rompieron tenant_isolation por descuido.
  - Hooks listos para F6 (workflow unification puede reusar el patrón nodos descompuestos), F7 (channel formatter consume `synthesizer` interface) y F8 (routing puede meter `ask_tenant_data` en NANO tier).

- **Paso 8 — Generar `prompts/F6-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f5): ask_tenant_data subgraph + decomposed nodes`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F5-ask-tenant-data.md` y `prompts/F6-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F5 no aplica por aprendizajes F4 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F5 (de aprendizajes F4)

### Aprendizajes F4 que F5 debe asumir

- **Patrón "state-aware system-prompt layer" ya validado.** F4 introdujo `inspirations_layer.py::build_inspirations_layer(state)` — función standalone llamada directo desde `build_system_prompt`. NO usa `ContextInjector` port porque ese contrato es per-tenant/per-route (no per-conv). Si F5 quiere inyectar "resultados de últimas queries" o "context conversational acumulado" en el system prompt, replica ese patrón en `application/orchestrator/<feature>_layer.py` y la inserción en `build_system_prompt` después del inspirations layer y antes del base prompt.
- **Orden cacheable preservado:** `lighthouse → inspirations → [F5 layer si lo agrega] → completion_snapshot/behavior/guided/studio → deep-agent suffix`. Cualquier nuevo layer F5 va ANTES del snapshot volátil.
- **Cross-module imports prohibidos.** Ratchet `copilot → módulo` frozen en **22**. Para acceder a repos de otros módulos, usar `discover_providers()` + provider port `tool_provider().tool_groups()` o crear un nuevo port (e.g. `RepoSearchProvider`) en `copilot/domain/ports.py`. El antipatrón es importar `OfferRepository` directo desde el subagent — eso levanta el ratchet a 23+.
- **Subagent sandbox via `tools=[...]` explícito.** F4 url_analyzer bind solo `fetch_url`. F5 `data_query` debe bind solo el conjunto de tools read-only que el plan permite — el TypedDict de deepagents 0.5.3 SUSTITUYE el toolset del parent cuando declarás `tools` (no extiende). Sin override, hereda mutations + extractions.
- **`CopilotInspirationRepository` puede ser fuente de Q&A.** Cuando user pregunta "¿qué inspiraciones cargué?" o "¿hay testimonios fuertes en las páginas que pegué?", F5 puede agregar `list_for_tenant(tenant_id, since, limit)` al repo F4 sin tocar F4. Repo ya tiene tenant isolation correcta.
- **Modelos nuevos requieren registro en `tests/conftest.py::db_engine`.** F5 si agrega `CopilotQueryCacheModel` o similar, replicar el patrón.
- **`pg_insert.on_conflict_do_update` SIEMPRE con `index_elements=[...]`.** SQLite no entiende `constraint="..."`. Heredado F2.
- **Python-side `default=utc_now` para timestamps multi-row.** SQLite tests con second-precision rompen ordering por `created_at`. Heredado F4.
- **`brand_relevance_score` y similares numeric → cast `float()` en tests** (postgres devuelve `Decimal`).
- **DI de collaborators en tools** (patrón F4): el tool `ask_tenant_data` debe aceptar `db=None`, `llm=None`, `repos=None` para que tests SQLite no toquen `discover_providers()` (que carga 9 módulos provider y abre Postgres).
- **`url_context` group + ALWAYS_AVAILABLE_GROUPS** ya en place. F5 agrega su tool al `_BASE_TOOL_GROUPS["data_query"]` (o reusa "shared_tools" si la fase decide). Si va en ALWAYS_AVAILABLE, mismo patrón.

### Tests baseline que F5 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/golden/ \
  tests/architecture/test_copilot_provider_compliance.py \
  tests/architecture/test_no_new_copilot_module_imports.py \
  tests/architecture/test_copilot_anchors.py \
  tests/architecture/test_deep_agent_harness_invariants.py \
  tests/architecture/test_ddd_boundaries.py \
  tests/modules/copilot/test_deep_agent_harness.py \
  tests/modules/copilot/test_plan_card_emission.py \
  tests/modules/copilot/test_pinned_memory_repository.py \
  tests/modules/copilot/test_inspiration_repository.py \
  tests/modules/copilot/test_trafilatura_client.py \
  tests/modules/copilot/test_url_inspiration_analyzer.py \
  tests/modules/copilot/test_fetch_url_tool.py \
  tests/modules/copilot/test_pin_to_memory_tool.py \
  tests/modules/copilot/test_inspirations_layer.py \
  tests/modules/brand/test_brand_summary_repository.py \
  tests/modules/brand/test_brand_section_updated_event.py \
  tests/modules/brand/test_brand_context_injector.py \
  tests/shared/workers/test_brand_summary_regen.py \
  tests/shared/application/test_brand_summary_event_handlers.py \
  tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
  -q -o addopts="" --timeout=60
```

Debe ser ~133 verde. Los flaky heredados (`test_streaming_integration` + `test_editable_fields_ssot::test_no_cross_domain_duplicates`) se corren **aislados** post-cambios.

### Archivos clave que F5 modifica (a priori)

- `backend/src/modules/copilot/application/tools/ask_tenant_data.py` — tool transversal nuevo.
- `backend/src/modules/copilot/application/orchestrator/subagents/data_query.py` — subagent dict (TypedDict deepagents) + lógica.
- `backend/src/modules/copilot/application/orchestrator/subagents/__init__.py` — agregar `DATA_QUERY_SUBAGENT` al export, `deep_agent.py` lo `extend()`s en `subagents=[...]`.
- `backend/src/modules/copilot/application/orchestrator/nodes/intent_router.py` — nuevo (subgraph nodes).
- `backend/src/modules/copilot/application/orchestrator/nodes/<entity_resolver|query_builder|executor|state_check|synthesizer>.py` — uno por nodo.
- `backend/src/modules/copilot/infrastructure/repositories/query_cache_repository.py` o Redis wrapper en `infrastructure/cache/`.
- Migration `070_pg_trgm.py` con `CREATE EXTENSION IF NOT EXISTS pg_trgm` + indices `gin_trgm_ops` en `products.name`, `copilot_conversations.title`, etc.
- Repos `OfferRepository.search`, `CrmContactRepository.count_inbound`, `ConversationRepository.search` enriquecidos en sus respectivos módulos (NO en copilot — eso violaría DDD).
- `backend/src/modules/copilot/application/tools/registry.py` — nuevo group `"data_query"` o agregar al existente, evaluar si va en `ALWAYS_AVAILABLE_GROUPS`.
- Frontend `inspiration_saved` card pendiente F4 NO se mezcla — F5 puede agregar nuevas cards (`data_query_result`) si scope lo permite, sino nota para F-pos.

### Riesgos que vigilar en F5

- **pg_trgm extension creation puede fallar en environments sin permisos.** Migration debe validar via `DO $$ BEGIN CREATE EXTENSION IF NOT EXISTS pg_trgm; EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE ...; END $$;` para no romper deploy si Postgres se restringe. Documentar en learnings.
- **dateparser** español LatAm: "ayer"/"antier"/"esta semana"/"el lunes pasado" — armar suite de tests con 30+ casos reales antes de declarar GREEN.
- **Cache Redis invalidation** es fácil de subestimar. Si F5 cachea results y un mutation tool cambia los datos, el cache stale aparece como bug "el copilot dice 5 personas pero hay 6". Mejor TTL bajo (60s plan F5) y skip invalidación granular hasta que aparezca el caso real. Documentar en learnings.
- **Repo `search()` signatures pueden romper tenant isolation por descuido.** Cualquier nuevo método debe filter `tenant_id` desde el primer commit. Test arch `test_tenant_isolation_in_search_methods` no existe hoy — si F5 agrega 3+ search methods, considerar agregar fitness test.
- **Cross-module import temptation.** Es fácil meter `from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository` en el subagent. Eso levanta el ratchet. Solución correcta: provider port `RepoSearchProvider` en `copilot/domain/ports.py` que cada módulo implementa, y el subagent recibe lista de repos via `discover_providers()`. Si parece overkill para F5, evaluar pragmáticamente — pero documentar la decisión en learnings.
- **Test flaky `test_streaming_integration`** heredado F0/F1/F2/F3/F4. Si F5 toca el orchestrator: correr aislado. Si NO toca, ignore con `--ignore=tests/modules/copilot/test_streaming_integration.py`.
- **Test flaky `test_editable_fields_ssot::test_no_cross_domain_duplicates`** heredado F3. Mismo tratamiento si F5 toca editable_fields.
- **Cache prefix degradation.** Si F5 inyecta nueva layer en system prompt entre lighthouse y completion_snapshot, evaluar byte-stability. F4 demostró: representación con `:.2f` en scores y orden estable preservó cache. F5 debe replicar — sin timestamps relativos, sin contadores volátiles.
