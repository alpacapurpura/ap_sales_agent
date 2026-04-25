# Learnings — F4 URL contextual + scratchpad inspirations

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `9b0caaec`)

---

## Resumen 3 líneas

- Tabla `copilot_inspiration` (PK `id`, UNIQUE `(conversation_id, slug)`, FIFO cap 5 visibles + cap absoluto 10/conv) + repo + tool transversal `fetch_url(url, why?)` que pipeline-a httpx → trafilatura 2.0 → LLM FAST analyzer (summary ≤500 chars + sub-elementos + `brand_relevance_score`) → upsert. Tool `pin_to_memory(slug)` promueve un row al `copilot_pinned_memory` (StoreBackend) por `(tenant, user, path)`.
- Inspirations table inyectada via `_build_inspirations_layer(state)` directo en `build_system_prompt` — NO via `ContextInjector` discovered. Razón: el port `inject_for(target_route, tenant_id)` no acepta `conversation_id`, y modificarlo era cambio de superficie sin valor para otras fases. Layer queda entre lighthouse F3 y completion-snapshot, byte-stable (sin timestamps relativos) → preserva cache hit del lighthouse.
- Subagent `URL_ANALYZER_SUBAGENT` registrado en deepagents `subagents=[...]` con `tools=[fetch_url]` (sandbox: NO mutations, NO extraction). Ratchet `copilot → módulo` queda en **22 entradas** (sin grow): el lighthouse fetch va via `discover_providers().summary_provider()` en lugar de import directo.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Persistencia DB nueva** (`copilot_inspiration` table) en lugar de StateBackend deepagents. | El scratchpad ephemeral del deep-agent vive un solo turn. F4 §1.3 pide cross-turn persistence ("rescata testimonios de mujercoraje en turn 7"). Tabla DB es el camino más directo + survives conversation rehydration. | `CompositeBackend(routes={"/inspirations/": StoreBackend(...)})` con StoreBackend custom Postgres. F2 learnings explícitamente recomendaron diferir StoreBackend custom hasta tener el caller real — y resulta que el caller real (este F4) NO necesita el contrato de filesystem virtual de deepagents para nada cross-turn, solo necesita un repo. Agregar el StoreBackend wrapper habría sido infraestructura extra sin uso. |
| **Inspirations layer NO usa `ContextInjector` port**, va directo en `build_system_prompt(state)`. | El port `inject_for(target_route, tenant_id)` (F1/F3) no recibe `conversation_id`. Las inspirations son per-conv, no per-route ni per-tenant. Modificar el port para meter conv_id era un cambio de superficie con un solo consumer (esto). | Extender el port a `inject_for(target_route, tenant_id, conversation_id=None)`. Funciona pero diluye la abstracción — `ContextInjector` queda con un opcional que solo F4 usa, todos los providers existentes ignoran. La decisión refleja que "context injectors" y "state-aware layers" son cosas distintas: el primero es per-tenant/per-route estable, el segundo cambia con la conversación. |
| **Lighthouse fetch via `discover_providers().summary_provider()`** en vez de import directo de `BrandSummaryRepository`. | El primer commit con import directo levantó el ratchet `copilot → brand` a 23 (test_no_new_copilot_module_imports.py rojo). La indirection via providers mantiene el ratchet en 22 y aprovecha exactamente el hook que F3 dejó listo (`BrandSummaryProvider.summary()`). | Allowlist el nuevo import en `KNOWN_COPILOT_TO_MODULE_IMPORTS`. Funciona pero diluye la señal del ratchet, y el provider port hace el trabajo bien. |
| **Validación URL + privacy strip en `validate_url`** (módulo trafilatura_client), no en el tool. | trafilatura_client es la frontera de red — ahí debe vivir la blocklist (localhost/private IPs) + el strip de query string. El tool transversal queda focused en orchestration (rate limit, repo upsert, LLM analyze). | Validar en el tool. Concentraría todo en un módulo pero diluye la responsabilidad: cualquier futuro caller del trafilatura_client (si la fase F-pos quiere reusar el fetch desde otro tool) hereda automáticamente la validación si está en la frontera. |
| **Subagent SOLO con `tools=[fetch_url]`** (sin scratchpad builtins ni extraction tools). | Aislación de scope: cuando el main agent hace `task("url_analyzer", urls=[...])` queremos garantizar que el subagent no puede mutar fields del studio ni encolar extracciones a workers. Con `tools` declarado en el TypedDict deepagents 0.5.3 sustituye los heredados, no los extiende — exactamente lo que necesitamos. | Dejar `tools` ausente y heredar todos los del parent. F2 learnings ya advertían: el `task()` builtin pasa el toolset completo a los subagents salvo que se restrinja explícitamente. Sin override, un fix en el main agent que agregue una mutation tool peligrosa la haría disponible al url_analyzer también. |
| **`default=utc_now` Python-side** en el modelo, no solo `server_default=func.now()`. | SQLite tests: `func.now()` resuelve a `CURRENT_TIMESTAMP` con second precision → multiple inserts dentro del mismo segundo tienen `created_at` idéntico → `ORDER BY created_at DESC` queda no-determinístico → tests FIFO flaky. Python-side `utc_now()` da microsecond precision en ambos engines. | `server_default=func.now()` solo (matching F3 brand_summary). El bug se hace visible recién cuando algún test inserta múltiples rows de orden — F3 no lo necesitó porque el repo es PK por tenant_id (un row). F4 SÍ tiene multi-row por conversación. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **`SessionLocal` apuntado a Postgres real desde imports laz**y en provider scan. `_load_brand_lighthouse` llama `discover_providers()` que importa cada `src.modules.{X}.copilot_provider` — algunos abren conexión a Postgres en module-import time (indirectamente). En el test FIFO eso reventaba con "could not translate host name 'postgres'". **Workaround:** todos los tests del tool aceptan un `lighthouse_fn` inyectable que devuelve `None` en SQLite path. La función real `_load_brand_lighthouse` solo se ejecuta en el path de producción. Cualquier fase futura que dependa de lookups via providers en tools transversales debe seguir el mismo patrón de DI.

- **Migración 069: idempotency NO viene gratis solo con `IF NOT EXISTS`** — viene de la combinación con `downgrade NO-OP`. Si en el futuro alguien implementa downgrade real (DROP TABLE), la idempotencia se pierde porque `alembic downgrade && alembic upgrade` daría un estado limpio que reintenta el CREATE — pero los **datos** no sobreviven. Dejé downgrade como NO-OP explícito + comentario; cualquier rollback en prod solo revierte schema en el peor caso, nunca destruye filas de inspirations capturadas.

- **`discover_providers()` con lru_cache + tests con `reset_discovery()`**. F3 usaba la fixture `_reset_provider_discovery` autouse en sus tests para evitar que el cache entre tests filtre estado. F4 sigue el patrón. Si una fase futura agrega un test que NO llama `reset_discovery()` y los providers cambian, va a ver el registry stale.

- **`brand_relevance_score` como `NUMERIC(3,2)`**. Postgres devuelve `Decimal`, no `float`. Tests deben hacer `float(row.brand_relevance_score)` antes de `pytest.approx`. Sub-bug que tropecé: si el LLM devuelve "0.75" como float, persistir requiere `Decimal(str(round(value, 2)))` para evitar precision drift al UPSERT (que se compara byte-a-byte para `index_elements`).

- **Tool `_BASE_TOOL_GROUPS` accepts plain `[fetch_url, pin_to_memory]`** vía `_register_tool_groups` que valida por `id()`. Ningún wrapper. Pero registry import-time crece con la lista de imports — fetch_url + pin_to_memory + url_inspiration_analyzer + trafilatura_client llegan todos al import inicial del registry. Si el module-load empieza a doler, F-pos que migre tools a providers ad-hoc puede shrink import-time.

- **El sufijo deep-agent F2 importa funciones desde graph.py** — modificar `build_system_prompt` siempre afecta el harness. Verificar el invariant `combined.endswith(_DEEP_AGENT_SUFFIX_ES)` en cualquier cambio al builder. F4 lo agregó como assertion en `test_inspirations_layer.py::test_deep_agent_suffix_still_tail`.

- **Test flaky `test_streaming_integration` heredado de F0/F1/F2/F3** sigue activo. F4 NO tocó streaming — corrió el test sweep con `--ignore=tests/modules/copilot/test_streaming_integration.py`. Cualquier fase que toque streaming/orchestrator debe correrlo aislado primero. (En `docs/mejoras-proceso/to-do.md` hay deuda explícita).

- **El test `test_editable_fields_ssot::test_no_cross_domain_duplicates` heredado de F3 sigue flaky**. F4 no tocó editable_fields registry. F-pos que toque ese registry debe correrlo aislado.

---

## Recomendaciones accionables para F5

1. **Antes de empezar:** correr la suite F0-F4 (~133 tests verdes):
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

2. **`ask_tenant_data` puede leer las inspirations como contexto fuzzy.** Cuando el user pregunta "¿qué inspiraciones cargué este mes?" o "¿alguna de las páginas que pegué tiene testimonios fuertes?", `ask_tenant_data` puede consultar `copilot_inspiration` por tenant + ventana temporal. Hook listo: `CopilotInspirationRepository.list_active_for_conversation` + un nuevo método `list_for_tenant(tenant_id, since, limit)` que F5 puede agregar sin tocar F4.

3. **F5 SubAgent `data_query` debe seguir el patrón de `URL_ANALYZER_SUBAGENT`:** `tools=[...]` explícito declarando solo las repo-bound tools de query (read-only). Sin esa restricción, el subagent hereda mutations + extraction tools del parent — peligroso para un subgraph que el LLM dispara con frecuencia.

4. **No agregar `conversation_id` al port `ContextInjector`.** F4 ya pasó por esa decisión. Si F5 necesita state-aware layers (probable), seguir el patrón nuevo: función standalone en `application/orchestrator/<feature>_layer.py` que acepta `state: CopilotState` y la llama `build_system_prompt`. Mantiene `ContextInjector` como contrato per-tenant/per-route.

5. **Trafilatura tile no instalado en Tessl** — ningún tile cubre `trafilatura` ni `httpx`. Las decisiones del cliente vinieron de WebSearch directo. Si F-pos agrega más fetchers (Playwright fallback, oEmbed), considerar tile propio o documentar en `docs/domains/copilot/redesign-2026-04/web-fetch.md`.

6. **El frontend renderer `inspiration_saved` card NO se implementó en F4.** El tool ya emite `ui_action: {type: "inspiration_saved", payload: {...}}` y el handler de SSE v2 lo reenvía al cliente. El componente FE quedó como nota: F-pos UX o el sprint que cierre la "Claude Code de Marketing" UX hace el ScreenshotCard. El JSON está estable, no requiere coordinación cross-stack para ese delivery.

7. **Si F5 introduce un nuevo `[COPILOT-*]` anchor**, agregarlo a `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY`. F4 dejó 24 entradas (límite 25) con `COPILOT-INSPIRATION-F4` y `COPILOT-FETCH-URL-F4`.

---

## Riesgos abiertos

- **Cache hit rate del system prompt no medido.** Mismo riesgo que F3 — F8 mide `cache_creation_input_tokens` vs `cache_read_input_tokens`. Si las inspirations se invalidan demasiado seguido (e.g. user pega URL nuevo cada turn → re-render del bloque), el lighthouse arriba sigue cacheable pero todo lo de abajo no. F8 puede decidir mover el inspirations layer DESPUÉS del completion_snapshot si el caso "URL pegado cada turno" pesa más que el caso "snapshot stable, inspirations changing". Hoy el invariant es "inspirations cambian poco; snapshot cambia cada turn", así que el orden actual maximiza prefix cache; medir antes de re-ordenar.

- **Trafilatura en JS-heavy / paywall sites.** El cliente devuelve `FetchUrlError` con copy "JS-heavy" cuando trafilatura returns empty — el user ve el error, no hay fallback Playwright. F4 §7 lo aplazó conscientemente. El día que un tenant pida "fetch dinámico" (Hotmart pages, Notion HTML exports) hay que evaluar Playwright o un servicio externo (browserless). Documentar en `docs/mejoras-proceso/to-do.md` cuando aparezca el primer reporte real.

- **`MAX_INSPIRATIONS_PER_CONVERSATION = 10`** es hardcoded como constante module-level. Si un tenant power-user satura, el error message le dice "promové con `pin_to_memory` las importantes". Pero no hay UI para `delete_inspiration(slug)`. F-pos UX puede agregar el botón "descartar" que llame un nuevo `delete_inspiration` tool. No urgente pero queda como friction conocido.

- **`copilot_inspiration.brand_relevance_score` no se re-evalúa cuando el brand_lighthouse cambia.** F3 regenera el lighthouse en cada `BrandSectionUpdated`. F4 NO subscribe a ese evento, así que un row capturado con relevance 0.4 (cuando el brand era débil) no se re-scoring cuando el brand mejora. Si vale la pena: subscribir un handler `regen_inspiration_relevance` análogo al `regen_brand_summary`. Hoy: no urgente — el user ve relevance "vieja" pero el row se sobrescribe en next pin/fetch.

- **Provider scan import side-effects.** `discover_providers()` carga 9 módulos provider en module-import time (cada uno trae sus repos/tools). Cualquier import que toque DB en module-load corrompe los unit tests. F4 tropezó con esto en el test FIFO. Patrón para evitar: cualquier nuevo provider debe diferir DB connections hasta `__call__` time, nunca import-time.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/infrastructure/repositories/inspiration_repository.py::CopilotInspirationRepository` — CRUD + tenant isolation + FIFO. F5 (`ask_tenant_data`) puede leer rows por conversation + window temporal. Falta solo agregar `list_for_tenant(tenant_id, since, limit)` cuando lo necesite.

- `backend/src/modules/copilot/application/tools/url_inspiration_analyzer.py::analyze` — pipeline LLM puro (sin DB, sin red). F-pos que necesite re-analyze (brand cambió) puede llamar directo con `content_md` ya cached.

- `backend/src/modules/copilot/application/tools/url_inspiration_analyzer.py::parse_llm_output` — parser tolerante (fenced code blocks, prose-around-json, voseo strip). Re-utilizable en cualquier tool que pida JSON al LLM y necesite resilience.

- `backend/src/modules/copilot/infrastructure/web/trafilatura_client.py` — fetch + extract + privacy strip + private-IP blocklist. F-pos que agregue otro fetch use-case (e.g. "leer doc de Notion público") usa el mismo cliente.

- `backend/src/modules/copilot/application/orchestrator/inspirations_layer.py::build_inspirations_layer(state)` — patrón reusable para state-aware system-prompt fragments. F5 puede crear `<feature>_layer.py` similar para "data query results cached" o "active workflow snapshot".

- `URL_ANALYZER_SUBAGENT` con `tools=[fetch_url]` explícito — patrón de subagent con sandbox. F5 `DATA_QUERY_SUBAGENT` debe declarar `tools=[ask_tenant_data, ...read-only repo tools]` similar.

- Migration 069 + `CopilotInspirationModel` registrada en `tests/conftest.py::db_engine` (fila 134-136). El patrón sigue el F2/F3 — modelos nuevos REQUIEREN registro o suite full puede flake.

- `ALWAYS_AVAILABLE_GROUPS` ahora incluye `url_context`. Cualquier nueva tool transversal (knowledge_search F10, format_for_channel F7) sigue el patrón: agregar group propio + meterlo en ALWAYS_AVAILABLE si debe estar en todas las routes.

---

## Fuentes research útiles

- [Trafilatura 2.0.0 docs · Read the Docs](https://trafilatura.readthedocs.io/en/latest/usage-python.html) — confirmé `output_format="markdown"` + `with_metadata=True` + `favor_precision=True`. La opción `favor_precision` reduce ruido a costa de recall — apropiado para inspiration use case (queremos lo central, no el long tail).
- [SIGIR benchmarks article-extraction-benchmark](https://github.com/scrapinghub/article-extraction-benchmark) — confirmó trafilatura F1 0.937 (mejor F1 de los open-source 2026) vs Newspaper3k 0.912 + readability 0.922. La elección estaba bien justificada en F4 doc; el research solo confirmó. Newspaper3k descartado por mantenimiento intermitente (newspaper4k recogió el bastón pero menos integrado).
- [HTTPX retry guide · Bright Data 2026](https://brightdata.com/blog/web-data/web-scraping-with-httpx) — patrón `httpx.AsyncHTTPTransport(retries=N)` para connect/timeout retries sin re-implementar. Decidió usar `retries=1` (un retry total) en lugar de tenacity — sufficient para low-volume inspiration use case y evita dependency.
- [LLM Brand Citation tracking · AirOps 2026](https://www.airops.com/blog/llm-brand-citation-tracking) — confirmé el pattern "LLM judge + score 0..1 con tiers semánticos" para `brand_relevance_score`. Los tiers (0.9+, 0.5-0.8, <0.4) los puse en el system prompt del analyzer siguiendo el framework LCRS.

Tessl tiles consultados: `tessl__fastapi`, `tessl__pytest-api-testing`. No instalé tile nuevo — ni `trafilatura` ni `httpx` están en el registry. La decisión se sostuvo con docs oficiales + benchmarks.
