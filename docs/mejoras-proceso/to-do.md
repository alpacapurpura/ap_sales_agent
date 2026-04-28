# Mejoras de Proceso — To Do

Hallazgos detectados por Claude Code durante ejecución. Revisar y resolver.

## Lecciones del Pase a Producción 2026-04-06

### 1. /test-all NO valida migraciones contra BD fresca en CI
- **Problema:** `/test-all` local ejecuta `alembic upgrade head` contra la BD existente (que ya tiene todas las tablas). Las migraciones no-idempotentes pasan porque las tablas ya existen. En CI (BD limpia) fallan.
- **Fix aplicado:** Arregladas migraciones 028, 030, 034, 036 con guards `DO $$ IF EXISTS`.
- [ ] Agregar step en `/test-all` que corra migraciones contra BD fresca (ya existe como step 11 pero no detectó estos errores porque localmente el backend container monta el código actual, no el código commiteado)
- [ ] Crear arch fitness test: escanear migraciones buscando `ALTER TABLE X` sin guard `IF EXISTS(table)` para tablas que no son creadas por migraciones (appointments, messages, agent_state_checkpoints, conversations, channel_connections)

### 2. E2E en CI necesitaba env vars no documentados
- **Problema:** El backend `Settings` requiere 12+ env vars obligatorias (LOG_LEVEL, OPENAI_API_KEY, REDIS_URL, etc). El job E2E solo tenía las de frontend/auth.
- **Fix aplicado:** Agregados dummy values en el workflow.
- [ ] Crear `.env.ci.example` con TODOS los env vars necesarios para CI E2E, documentado y versionado
- [ ] Considerar hacer que Settings tenga defaults para env vars no-críticos en test mode

### 3. `docker compose --wait` no funciona con init containers + tunnel
- **Problema:** `--wait` espera que TODOS los servicios estén healthy. `init_cache` sale con code 0 (esperado) y `cloudflare-tunnel` con token `disabled` tarda 3+ min.
- **Fix aplicado:** Reemplazado con `up -d` + health check manual solo de los servicios necesarios.
- [ ] Considerar crear un `docker-compose.ci.yml` override que excluya tunnel e init_cache

### 4. Tests de arquitectura cross-stack no funcionan en Docker CI
- **Problema:** `test_currency_consistency.py` intentaba leer archivos frontend desde el container backend. En CI el backend corre aislado sin acceso al frontend.
- **Fix aplicado:** Removida dependencia cross-stack, validación solo del backend.
- [ ] Regla: los tests de arquitectura backend NUNCA deben depender de archivos frontend. Si se necesita validación cross-stack, hacerla como step separado nativo.

### 5. Sesiones paralelas de Claude Code pueden interferir
- **Problema:** La sesión paralela (currency-standardization) hizo commit a main con un test roto (`test_currency_consistency`) que rompió quality-gates del pase a producción.
- [ ] Regla: cada sesión de Claude Code DEBE trabajar en su propia feature branch. Solo mergear a main después de pasar /test-all en la feature branch.
- [ ] El protocolo paralelo actual no previene commits rotos de otras sesiones

### 6. E2E smoke local falla por OOM del Next.js container
- **Problema:** Container Next.js dev con 2048MB se cae bajo carga de Playwright (HMR + watchers + compilación + memoria).
- **Fix aplicado:** `shm_size: 2gb` + `--disable-dev-shm-usage` + target `e2e-native-smoke` (sin container Docker).
- [ ] A largo plazo: resolver el bug de `next build` para poder usar `next start` en E2E (3-5x menos memoria)
- [ ] Documentar en CLAUDE.md que E2E preferir `make e2e-native-smoke` sobre `make e2e-smoke` en laptops con poca RAM

## Lecciones del fix `ig_follows_and_unfollows` — 2026-04-11

### 7. Metrics de Meta con breakdown mandatorio devuelven 0 silencioso
- **Problema:** El ETL pedía `follows_and_unfollows` junto a otros metrics sin `breakdown=follow_type`. Meta responde con el metric listado pero SIN `total_value`, y el código hacía `item.get("total_value", {}).get("value", 0)` → 0 silencioso. Resultado: 34 filas diarias con value=0 en producción por ~30 días, dashboard mostrando "Seguidores Netos = 0".
- **Fix aplicado:** Llamada dedicada con `breakdown=follow_type` + parseo de `total_value.breakdowns[0].results` (FOLLOWER/NON_FOLLOWER), emite tres metrics (`gained`, `lost`, `and_unfollows`).
- [ ] Regla nueva: en cualquier provider ETL, cuando se fetcha un metric cuyo valor por default sea 0, emitir warning + sentry si `total_value` está ausente de la respuesta. Un 0 por "no data returned" debe loguearse distinto a un 0 real.
- [ ] Crear arch fitness: los extractors que usan `.get("total_value", {}).get("value", 0)` deben estar explícitamente listados en un allowlist, porque ese patrón esconde data-loss.

### 8. Gap detection en `run_initial_load` enmascaró el bug por semanas
- **Problema:** `get_existing_dates()` devuelve cualquier día que tenga AL MENOS una fila del proveedor. Como los metrics buenos (`ig_views`, `reach`, etc.) sí se grababan, el gap detector consideraba "cargado" cada día y nunca re-extraía `ig_follows_and_unfollows`. El dato roto quedaba ahí indefinidamente sin que ningún mecanismo lo detectara.
- [ ] Mejorar la gap detection: consultar por `(date, metric_name)` en lugar de `(date)`, o al menos tener un comando `alembic`-like para "re-extract metric X en el rango Y..Z sin importar lo ya cargado".
- [ ] Agregar data-quality check que alerte si un metric ADDITIVE tiene >80% de filas en 0 durante un período largo. Es casi siempre un bug del extractor.

### 9. Loop off-by-one en `_extract_instagram_organic_daily`
- **Problema:** `while current < end_date` (half-open). Cuando `run_initial_load` encontraba exactamente un día faltante, llamaba con `start == end` y el loop no ejecutaba ninguna iteración → extraía cero metrics silenciosamente.
- **Fix aplicado:** Cambiado a `while current <= end_date`. Test de regresión que llama con `start == end` y valida que al menos un día sea extraído.
- [ ] Auditar otros extractors con loops `while X < end_date`: `_ig_day_chunks` (legacy), y verificar semántica de cada uno. Ya confirmé que `_extract_meta_retargeting_daily` usa `<=` (correcto).

### 10. Snapshots absolutas (ig_followers_count) no tenían histórico
- **Problema:** Meta's user-node endpoint solo devuelve el valor ACTUAL del contador. Cada ETL run escribía una fila con `date=end_date`. Para backfill de 30 días, se escribía UNA sola fila, imposibilitando mostrar una curva de crecimiento histórico.
- **Fix aplicado:** Reconstrucción hacia atrás usando el snapshot actual como ancla + los deltas diarios recién extraídos. `followers(D-1) = followers(D) - net(D)`. Emite N filas (una por día) durante el backfill. Cuando el ETL diario corre, las filas reales sobreescriben la reconstrucción via upsert.
- [ ] Aplicar el mismo patrón a otros providers con snapshots absolutos: YouTube `subscribers_count`, TikTok, etc., donde exista delta diario correlacionado.
- [ ] Potencial trampa: si el delta feed tiene lag (Meta tarda ~2 días en reportar `follows_and_unfollows`), la reconstrucción será imprecisa en los días recientes. El ETL programado corrigirá esto con el tiempo, pero vale la pena marcar filas reconstruidas vs reales (por ejemplo, en `extra: {"source": "reconstructed"}`).

### 11. Confianza en la data: un 0 no siempre es un 0
- **Principio:** Para metrics de negocio críticas (el usuario toma decisiones con esta data), un valor de 0 puede significar: (a) cero real, (b) no había data todavía, (c) error silencioso de parseo, (d) permiso insuficiente en el API, (e) metric deprecated. Deberíamos distinguir entre estos casos a nivel de DB.
- [ ] Agregar columna `data_quality` o `status` a `official_metrics` (enum: `ok`, `missing`, `partial`, `deprecated`, `auth_error`). Esto permite que el frontend muestre "sin datos" en vez de "0" cuando corresponde.

## Lecciones del Offer Header Refactor — 2026-04-11

### 12. `/nicolify-feature` pipeline no corre `alembic upgrade head` automáticamente
- **Problema:** El pipeline ejecuta Phase 4 (test suite native) que corre pytest, ruff, tsc, etc. Pero NO corre `docker exec ... alembic upgrade head` después de que el backend agent commitee la migración. La migración queda escrita y committeada pero las tablas no existen en la dev DB. El usuario hace click en una tab y obtiene 500 "relation does not exist".
- [ ] Agregar step explícito al pipeline `/nicolify-feature` después de la fase de implementación: si el backend agent creó una alembic migration, correr `docker exec -t visionarias_brain_dev bash -c 'cd /app && alembic upgrade head'` y verificar con `alembic current`.
- [ ] Idealmente: el orchestrator debería detectar nuevos archivos en `backend/alembic/versions/` durante el commit y ejecutar el upgrade como parte del Phase 4 nativo.

### 13. CONTRACT.md y URL paths reales del backend pueden divergir
- **Problema:** El architect agent escribió CONTRACT.md con paths `/api/v1/offer/offers/{id}/...`. Frontend Chunk 1 los copió tal cual. Backend Chunk 4a, al implementar, descubrió que el módulo `offer` históricamente monta su router bajo el prefix legacy `/api/v1/offer/products` (porque la tabla DB se llama `products`). BE eligió respetar el legacy. FE quedó apuntando a paths inexistentes. 14 URLs rotas en 6 adapters, descubierto solo cuando el usuario clickeó por primera vez.
- [ ] Regla: el architect agent debe verificar los mounts existentes en `backend/src/main.py` ANTES de escribir CONTRACT.md, y usar los prefijos legacy si existen. Documentar la divergencia entre nombre del módulo y prefix HTTP.
- [ ] Backend audit: el `nicolify-backend-auditor` debería comparar las paths declaradas en CONTRACT.md con las paths reales mounteadas en `main.py` y reportar discrepancias como WARN.
- [ ] Frontend agent debería leer `backend/src/main.py` (solo los `app.include_router` calls) ANTES de escribir API adapters, y usar los prefijos reales en lugar de los del CONTRACT cuando difieran.

### 14. Tooltip sin TooltipProvider no rompe en tests, sí en runtime
- **Problema:** `OfferStatusSwitcher` usaba `<Tooltip>` sin envolver en `<TooltipProvider>`. Los unit tests pasaban porque happy-dom tolera el contexto faltante. En runtime real, Radix Tooltip crashea la página entera.
- [ ] Crear arch fitness frontend: AST scan que detecte `import { Tooltip }` sin un `TooltipProvider` correspondiente en el mismo archivo o en algún ancestor. Mismo patrón aplica a otros Radix primitives.
- [ ] Considerar smoke tests E2E que mountee la pantalla completa para detectar este tipo de errores de contexto faltante.

### 15. `usePathname()` en client layouts puede hidratar inconsistente con Turbopack
- **Problema:** Después de cambiar la lista de full-width patterns en el dashboard layout, Turbopack dev sirvió un bundle SSR stale mientras el cliente fast-refreshed con código nuevo. Hydration mismatch sin posibilidad de reconciliación.
- **Fix aplicado:** Diferir la decisión a `useEffect` (initial render = false, flip post-mount).
- [ ] Patrón general: cuando un client layout decide rendering basado en `usePathname()`, usar useState+useEffect para evitar cache staleness en dev. El "single-frame flash" es preferible al crash.

## Stubs y mejoras pendientes extraídas de TODO comments — 2026-04-13

### 16. Shopify GDPR compliance endpoints son stubs
- `connections/api/shopify_compliance.py`: los 3 endpoints (`customers/data_request`, `customers/redact`, `shop/redact`) solo loguean y devuelven 200. No ejecutan export ni deletion real.
- [ ] Implementar workflow de data export para `customers/data_request`
- [ ] Implementar workflow de data deletion para `customers/redact` y `shop/redact`

### 17. MailerLite sync_contacts y sync_events son stubs
- `connections/infrastructure/marketing_connectors/mailerlite.py`: ambos métodos devuelven `[]`.
- [ ] Implementar `sync_contacts` con la API real de MailerLite
- [ ] Implementar `sync_events` con la API real de MailerLite (aperturas, clics, etc.)

### 18. CRM: update/merge de traits no implementado
- `crm/application/services/customer_service.py` y `crm/infrastructure/engines/identity.py`: cuando se encuentra un perfil existente, no se actualizan traits (merge).
- [ ] Implementar lógica de merge de traits al encontrar perfil existente (en customer_service y identity engine)

### 19. Offer campaigns adapter es stub
- `advertising/application/services/offer_campaigns_read_adapter.py`: devuelve KPIs vacíos. Necesita que advertising exponga `offer_id` en sus tablas de campaign/ad.
- [ ] Wire real aggregation cuando advertising exponga `offer_id` en campaign/ad tables

### 20. Capture repository: session tracking para conversaciones
- `analytics/infrastructure/repositories/capture_repository.py`: usa `distinct profile_id` como aproximación de conversaciones únicas.
- [ ] Agregar session tracking a JourneyEventModel para conteos de conversación más precisos

### 21. Landing service usa Session (sync) en vez de AsyncSession
- `landing/application/landing_service.py`: necesita migración a AsyncSession.
- [ ] Migrar landing_service.py de Session sync a AsyncSession

### 22. Shopify abandoned cart detection
- `connections/api/marketing_webhooks.py`: la detección de carritos abandonados (checkouts >1h sin order) no está implementada.
- [ ] Implementar background task para detectar abandoned carts (checkouts >1h sin matching order)
[] BuyerPersonaPersister._create_new: pasar user_id real cuando el Interview Engine lo propague (actualmente usa tenant_id como fallback)
[] sales_agent/test_conversation_context.py: ImportError preexistente — `merge_history_with_current` eliminada de `chat.py` sin actualizar el test (Sprint 2.D no lo tocó)
[] copilot/test_dynamic_interview_config.py + test_interview_service_dynamic.py: 10 tests fallan por regresión preexistente en bloques del Interview Engine (archetypes programa/servicio/experiencia producen config incorrecta)
[] lib/form-runtime/hooks/use-auto-save.test.ts: 6 tests fallan con ReferenceError: document is not defined pese a happy-dom global. El test setup no está cargando el environment — probablemente requiere docblock `@vitest-environment happy-dom` por file o verify setup.ts invoca al plugin React correctamente. Preexistente.
[] Migrar textarea-as-array a array real en service-details.schema.ts (deliverables_list, scope_excluded) y location.schema.ts (photos_urls, hours_of_operation) — form-runtime-array.md regla §Prohibido.
[] admin `_shared.render_tenant_selector(allow_all=False)` crashea con lista vacía: `options.index(None)` ValueError. Renderizar empty-state `st.info("No hay tenants")` y devolver None.
[] admin `users.py` y `tenants.py` usan `db.query(Model)...` (SA 1.x) — viola regla DDD `.claude/rules/backend-ddd.md`. Migrar a `select(Model).where(...)` o usar `TenantService`/`UserService`.
[] Dedupe brand+offer extraction: `brand/application/extraction_service.py::BrandExtractionService._run_section/_render_prompt/_append_schema_instruction` están duplicados 1:1 con `offer/application/offer_extraction_service.py::OfferExtractionService`. Extraer `shared/application/extraction/section_runner.py` con `SectionRunner` por composición. Mantener tests module existentes verdes (import re-exports backwards-compat). Sin cambio de comportamiento. Follow-up PR aislado.
[] `copilot/application/tools/interview/offer_alternatives.py` cap 4 vs `shared_tools/clarify.py` cap 4 unificados — documentar invariante en rule `.claude/rules/copilot-resilience.md` (límite botones = min(max ventana render, 4)).
[] `tests/modules/copilot/test_streaming_integration.py::TestProcessStreamEvent::test_tool_result_truncated_at_500_chars` falla pre-existente (aserción `len(result_value) <= 500` — valor real 1000). Test o productivo desalineado sobre truncado. Investigar si se trunca en otro lugar o si el test espera valor viejo.
[] `tests/modules/copilot/test_streaming_integration.py` + `test_sse_v2_events.py` flakean en bulk-run (~13 fallos extra) pero pasan aislados — test pollution con pytest-randomly. Agregar fixture reset event-bus/recorder per test o marcar `pytest.mark.serial`.
[] Refactor studio-sections lazy-loading Fase 4: bajar `visionarias_client_dev` memory limit 5GB → 4GB (docker-compose.yml). Post Fases 0-3 el split homologado eliminó el OOM loop que crasheaba el container en cada visita a `/offer-studio/offer/[id]/editor/[section]`; con 5GB se navegan 5+ secciones seguidas sin reinicios. Turbopack sigue acumulando ~4.9GB tras varios compiles, y `offer-studio/schemas/testimonials.schema.ts` cold compile tarda ~61s (12 sub-fields en split mode). Antes de revertir a 4GB investigar footprint del barrel `components/form-runtime/` (4.6k líneas) y el cost del itemSchema de testimonials. Hasta entonces, 5GB queda como parche operativo documentado.
[] Extender `offer_completion_service` con los 13 narrative fields cuando se defina el umbral por sección. Hoy los ratios de completitud de tenants existentes se calculan sin los narrativos — agregarlos directamente puede romper baselines. Requiere decisión de producto sobre qué peso dan a cada campo y en qué sección se contabilizan. Archivo: `backend/src/modules/offer/application/services/offer_completion_service.py`. No bloquea Fase 7 (CONTRACT §4 nota explícita).
[] Landing service (`generate_landing_for_offer`): integrar campos narrativos `before_state`, `after_state`, `measurable_outcomes` en el copy generado. Hoy la query SQL solo selecciona `name, headline_promise, primary_outcome, marketing_pain_points, preset_id`. Los campos narrativos ya existen en DB — solo falta incluirlos en el SELECT y pasarlos al content builder. Archivo: `backend/src/modules/landing/application/landing_service.py` líneas 151–192. Estimado: 30 min. Requiere decidir cómo surfacear `before_state`/`after_state` en el template por archetype (seguimiento: CONTRACT §14 "Impactos que NO deben romperse").
[] Reducir `KNOWN_UNRESOLVED_PATHS` en `frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts` a medida que Fases 01-05 cierren (cap arranca en 59 por ADR-007 en `docs/refactors/field-contract-ssot/DECISIONS.md`, shrink-only).
[] Rename `SubscriptionDetails.billing_cycle → billing_frequency` + `content_update_freq → content_update_frequency` con migration idempotente. Drift BE/FE detectado durante Fase 00 del refactor field-contract-ssot. Programado Fase 02.
[] Modelar `PlatformDetails` en `backend/src/modules/offer/domain/details.py` + 6ta entry en `ARCHETYPE_TO_DETAILS_MAPPING`. PLATFORM archetype declara 14 paths en `platform-details.schema.ts` sin contraparte BE. Programado Fase 02.
[] Regla nueva candidata para `.claude/rules/backend-ddd.md`: scripts standalone que abran sesión SA DEBEN importar `src.shared.infrastructure.model_registry` antes de cualquier query, o fallan resolviendo `LeadModel`/otras relaciones string. Documentar si aparece tercer caso (hoy: `scripts/capture_offer_a96403b5_baseline.py`, precedente `main.py`, `admin/app.py`).


- [x] Tests copilot flaky con pytest-randomly: `test_tool_call_produces_tool_events` (streaming_integration) falla en orden aleatorio, pasa aislado en 12s. F0+F1 confirmaron pre-existente, no causado por langchain-core 1.2→1.3 bump. Aislar conftest fixtures order-dependent (probable model resolution side-effect en test_mutation_journal_repository). Seed `--randomly-seed=last` ayuda repro. **Resuelto 2026-04-25 (TP1 setup)**: dos bugs encadenados — (1) `tests/conftest.py` no importaba `model_registry` antes de `Base.metadata.create_all`, dejando SA mappers parciales y rompiendo `relationship("AppointmentModel")` en orden randomly; (2) `trace_recorder.py` hardcodeaba `SessionLocal` ignorando DI, lo que en tests nativos WSL bloqueaba 30s+ por DNS retry psycopg2 al hostname Docker `postgres`. Fix: conftest reorder + import registry + API pluggable `set_session_factory` en recorder. Suite seed=12345 y seed=99999: 4953 passed, 0 failed.

- [ ] **PROD recorder DNS-retry latente**: `trace_recorder.py` usa `_session_factory()` per-event (sync I/O dentro de async streaming). Si Postgres está down o DNS lento, cada turn bloquea ~10s × N writes — degrada UX aún siendo "best-effort". Opciones: (a) `create_engine(..., connect_args={"connect_timeout": 1})` en `src/core/database.py` para fail-fast; (b) mover writes a background task ARQ; (c) batch writes per-turn con timeout ceiling. Detectado durante TP1 setup 2026-04-25 al fixear flakiness — revelado pero no bloqueaba TP1 (PROD funciona porque postgres siempre responde). Prioridad media.

## Lecciones del TP1 testing-2026-04 — 2026-04-25

### 23. System prompt copilot 17.5k tokens bloquea throughput bajo OpenAI tier 1
- **Problema:** `compose_system_prompt` rinde ~17.5k tokens por turn (5 fragments cacheable + 3 volatile + tools schema). OpenAI org está en tier 1 (TPM gpt-4o = 30k). Cualquier batch >1.7 turns/min gatilla 429 con backoff, degrada latencia 1.5s → 30-43s, y rompe medición confiable de p50/p95 por tier en TPs siguientes (TP2 brand variations, TP9 deep_agent multi-step). Detectado durante TP1 corrida 2026-04-25 — los `turn_end` de turns rate-limited reportan `total_tokens=0` porque el LLM call falla midstream sin gatillar `on_chat_model_end`.
- **Mitigación temporal:** espaciar ≥35s entre turns en testing manual.
- [ ] Bumpear org tier OpenAI (target tier 3+ con TPM ≥150k) — decisión de billing, fuera de scope código.
- [ ] **Spike "system prompt compresión" antes de aplicar global**: auditar `compose_system_prompt` fragments + identificar el más pesado (sospechoso: `_modules.j2` + `_editable.j2` con catálogos verbosos). Comprimir 1 fragment a la vez usando estilo caveman (drop articles, fragments OK, short synonyms — preserva semántica técnica) y A/B con `CopilotJudge` (heredado F9) sobre 20 escenarios cross-tier. Aceptar fragment comprimido sólo si `judge_avg ≥ 4.0` y voseo=0 leak al output (regla 11). Riesgo a vigilar: el LLM agente puede empezar a responder caveman al user → mala UX. NO aplicar global sin validación per-fragment. Estimado: 4-6h spike + decisión.
- [ ] Validación cruzada: si la compresión gana ≥40% tokens sin degrade quality, prefix cacheable cae bajo umbral 1024 tokens en algunos tenants (sin lighthouse, sin editable_catalog rico) — agregar arch test que mida `len(compose_system_prompt(static_only_fragments).encode("utf-8")) // 4 >= 1024` (recomendación heredada F8).

### 24. `usage_tracking.calculate_cost` no aplica discount a `cached_input_tokens`
- **Problema:** Fórmula actual multiplica el total `prompt_tokens` por `prices["input"]` sin separar la fracción cacheada. OpenAI cobra `cached_input_tokens × cached_rate` (≈50% del input rate). Con cache hit rate observado 99% post-warmup, el `cost_usd` logueado en `copilot_turn_usage` + persistido en `turn_end.data` está sobreestimado ~50%. Detectado TP1 S1.7.
- [ ] Update `_PRICING` con keys `cached_input` per modelo (gpt-4o $1.25/1M, gpt-4o-mini $0.075/1M, opus $7.50/1M, etc.). Cambiar signature `calculate_cost(prompt_tokens, completion_tokens, model, cached_input_tokens=0)`. Update `UsageAccumulator.cost_usd` property + tests `test_usage_tracking_cache.py` con asserts costo cached vs uncached. Estimado: 1-2h.

### 25. `routing_log.tier_selected` ≠ modelo realmente bound al graph (F11.1 telemetry-only)
- **Problema:** F11 wired `build_default_router` como **telemetría-only** — `chat.py::_record_routing_decision` persiste el tier en `copilot_routing_log` pero el `LLMFactory.get_service().get_client(...)` que el deep_agent usa sigue devolviendo el modelo default (gpt-4o = MINI). Cualquier assertion de cost/latency per tier vía routing_log es engañosa. Documented en `learnings/F11-housekeeping.md` como decisión deliberada (no cambiar comportamiento prod sin baseline).
- [ ] **Cutover F-pos**: agregar `tier_to_role: dict[ModelTier, ModelRole]` en `domain/routing_policy.py` o `application/router/`. En `chat.py::stream_chat` antes de `build_deep_agent_graph(state)`, resolver `decision.tier → ModelRole` y pasar al `LLMFactory.get_service().get_client(role=...)` que el deep_agent debe consumir (refactor inputs del harness). Tests: A/B sobre 50 turns mixed scenarios — confirmar que NANO tier ahora cuesta ~$0.003 (vs $0.044 hoy) y latencia NANO p50 baja a ~800ms. Estimado: 4-6h + validación. Bloqueante para TP-followup que valide cost real per tier.
- [ ] Detection signal admin: agregar a `/copilot-routing` métrica "tier-vs-model alignment" que cuente turns donde `routing_log.tier_selected` no matchea `data->>'model'` real — proxy para detectar regresión post-cutover.

### 26. Recorder emite `turn_end` con `total_tokens=0` cuando stream falla midstream
- **Problema:** Cuando `LLM call` excepciona (rate limit 429, network blip, tool error que el deep_agent harness trapea via `langgraph.prebuilt.tool_node._handle_tool_error`), el `usage.update_from_event()` no captura el AIMessage y el `turn_end` se emite con `total_tokens=0, model="gpt-4o" (default)`. Comportamiento técnicamente correcto (emite turn_end → trace completo) pero data shape rota para análisis cost/latency. TP1 detectó 22% turns en este estado durante batch sequential.
- [ ] Agregar tab "Rate-limit / stream-failure pressure" al admin `/copilot-routing` que cuente `turn_end con total_tokens=0 AND duration_ms>10000` por hora. Proxy temprano de degradación antes que el user reporte "no responde".
- [ ] Considerar agregar field `data->>'stream_status'` en `turn_end` (`ok` / `rate_limited` / `tool_error` / `timeout`) detectando exception type en el except handler del stream. Permite filtrar analytics sin guess basado en `total_tokens=0`. Estimado: 2-3h con tests.


### 27. [copilot-obs] PII redaction async con Presidio + spaCy es_core_news_md
- **Contexto:** Phase 3 T3.8 implementó regex-only sync (email, phone LATAM con keyword anchor, API tokens). Cubre ~90% del PII. NER de Presidio cubre el 10% restante (nombres propios, direcciones libres, IDs nacionales formato sin separador).
- **Por qué no se incluyó:** Presidio + spaCy `es_core_news_md` agrega ~600MB al image worker y la latencia 2026 no está medida. Callback handler corre en hot path SSE y necesita <10ms p99. Sin benchmark verificado, no se introduce.
- [ ] Implementar como worker ARQ post-write que lee `copilot_trace_event` rows de la última hora con `data->>'input_messages'` no vacío, aplica Presidio analyzer, y reescribe `data` JSONB con anonymized output. Diferir hasta primer reporte real de PII no redactado. Estimado: 4-6h (instalar Presidio + spaCy en worker image + worker + tests).

### 28. [copilot-obs] Email / Slack delivery para cost alerts
- **Contexto:** Phase 3 T3.10 emite `cost_alert_threshold_exceeded` como structlog warning. Para llegar a humanos hace falta infra de email transaccional o webhook Slack que el repo aún no tiene.
- [ ] Cuando el primer ticket de "no me enteré que un tenant superó su quota" llegue, agregar deliveries: webhook Slack via env `COPILOT_OBS_SLACK_WEBHOOK`, email opcional via SES/Postmark. Hook en `cost_alert_service.check_cost_alerts` post-warning. Estimado: 2h por canal.

### 29. [copilot-obs] Bootstrap automático de tenant_billing_config para tenants nuevos
- **Contexto:** Phase 3 dejó la tabla con 0 rows para los 11 tenants existentes (decisión D3.2: bootstrap perezoso, defaults del 25-25 / USD vienen de `compute_cycle_start` SQL function + `BillingCycleService.resolve_currency`).
- [ ] Cuando se cree un tenant nuevo (`iam.tenant_service`), insertar una row default en `tenant_billing_config` para que el dashboard `/costo-copilot` lo muestre con su moneda y anchor explícitos desde el primer turno. Estimado: 1h con tests.

### 30. [copilot-obs] Borrar `_legacy_compat_keys` del JSONB de `turn_end`
- **Contexto:** Phase 2 dejó `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_input_tokens`, `cache_hit_rate`, `cost_usd`, `response_length`, `message_count`, `block_count` por compat. Phase 3 ya migró `/trazas` y `/copilot-routing` a leer de `copilot_llm_call` directo.
- [ ] Verificar via `git grep` que ningún consumer FE/streamlit/external lee esos keys. Si nadie → borrar de `turn_envelope._write_turn_end` y de cualquier test que los chequee. Estimado: 30min + grep audit.

## Lecciones del fix loop bug + max_output_tokens — 2026-04-27

### 31. [llm-providers] Unificar Gemini bajo el mismo helper de kwargs
- **Contexto:** El bug del 2026-04-27 (`Completions.create() got an unexpected keyword argument 'max_output_tokens'`) se resolvió con un helper compartido `providers/_kwargs.py::normalize_openai_protocol_kwargs` que ahora consume `OpenAIService` + `OpenAICompatibleService` (DeepSeek/Kimi/Qwen). Gemini quedó fuera porque NO habla protocolo OpenAI — usa `langchain_google_genai.ChatGoogleGenerativeAI` con shape distinto (Vertex AI / Gemini API). Hoy nadie ruteo critical depende de Gemini para `generate_response` con `max_output_tokens`, pero si en el futuro se enchufa Gemini como fallback en `LLMRouter`, repetiremos el bug con otro nombre (Gemini sí entiende `max_output_tokens` literal, así que el fallo será silente — la traducción rota lo enviaría como `max_tokens` y Gemini lo ignoraría).
- **Por qué no ahora:** Gemini no es fallback activo en producción. Forzarlo dentro del helper hoy implicaría:
  - Crear `_gemini_kwargs.py` con la traducción inversa (Nicolify usa `max_output_tokens` y Gemini también lo usa nativo, así que la traducción es no-op para max-tokens — pero `temperature` está OK, y otros params como `top_k` solo existen en Gemini).
  - Auditar `GeminiService.generate_response` (no leí su impl actual).
  - Decidir si el helper se vuelve `normalize_kwargs(kwargs, target_protocol="openai" | "gemini")` (cleaner) o si cada protocolo tiene su propio helper (más simple, evita un argumento).
- [ ] Cuando Gemini se promueva a primary o fallback en `LLMRouter`, audit + agregar:
  - `providers/_kwargs.py::normalize_gemini_protocol_kwargs(kwargs)` (o renombrar a `normalize_kwargs(kwargs, target=...)`).
  - Test parametrizado en `test_kwargs_normalization.py` para los kwargs Gemini-only (`top_k`, `safety_settings`).
  - Update `GeminiService.generate_response` para llamarlo (revisar signature actual).
  - Considerar si `metadata` y otros Nicolify-internal keys también se popean en Gemini (sí — son universales).
- **Decisión:** dejar el helper Gemini-agnóstico hasta que haya un caller real. Forzar la abstracción ahora generaría YAGNI y testería un path sin uso. Estimado cuando se active: 2-3h con tests.

### 32. [llm-compat] LangChain `ChatOpenAI` reescribe `max_tokens` → `max_completion_tokens`, rompe DeepSeek silente
- **Contexto:** `langchain_openai.ChatOpenAI` (todas las versiones desde Sept-2024) reescribe automáticamente `max_tokens` a `max_completion_tokens` en el HTTP payload para alinearse con la deprecation de OpenAI Chat Completions. DeepSeek, Kimi y Qwen siguen aceptando solo `max_tokens` literal — el rewrite los rompe **silente** (no TypeError, sino: el cap se ignora y el modelo genera tokens hasta el techo del contexto). Issue upstream `langchain-ai/langchain#29283` cerrado "not planned" — LangChain considera que es problema de los compat providers, no suyo.
- **Por qué importa para Nicolify:** Si en algún momento se setea un cap real (`max_output_tokens=512` para limitar costo de extracciones largas), DeepSeek/Kimi/Qwen lo van a ignorar y vamos a generar respuestas de 4-8K tokens cuando esperábamos 512. Costo en tokens 8-16x el presupuestado. No genera errores, solo plata quemada.
- **Por qué no se arregla hoy:** La traducción de `_kwargs.py` corre ANTES de que LangChain haga su rewrite, así que el TypeError inmediato (`max_output_tokens`) está cubierto. El rewrite secundario `max_tokens → max_completion_tokens` ocurre dentro de `ChatOpenAI._stream`, fuera de nuestro control. El fix correcto requiere o bien:
  - (a) Migrar a `langchain_deepseek.ChatDeepSeek` (paquete oficial separado) para DeepSeek, y similares para Kimi/Qwen cuando existan. Refactor mediano: cambiar `_get_chat_model` per provider.
  - (b) Subclassear `ChatOpenAI` con un override de `_get_request_payload` que invierta el rewrite cuando `base_url != openai.com`. Frágil — depende de internals de LangChain.
  - (c) Esperar a que cada compat provider acepte `max_completion_tokens` como alias (DeepSeek API roadmap incluye esto en V4).
- [ ] **Detección temprana**: agregar check al admin `/copilot-routing` o `/costo-copilot` que warneee cuando `output_tokens > 1.5 * max_output_tokens_intended` para tenants con presupuesto explícito. Tablero compara `model_responded` con la lib LangChain usada para detectar el caso. Estimado: 2h. (Activa la alarma sin requerir migración.)
- [ ] **Cuando dolga**: Si vemos costo real burned por esto en `mv_daily_llm_cost_per_tenant`, migrar DeepSeek a `langchain_deepseek.ChatDeepSeek`. Ya está en `requirements.txt`? auditar. Estimado: 4-6h con regression test que confirma `max_tokens` honra el cap.
- **Referencia:** [langchain-ai/langchain#29283](https://github.com/langchain-ai/langchain/issues/29283), [langchain-ai/langchain#30113](https://github.com/langchain-ai/langchain/issues/30113).


- [x] **Pre-existing flakiness**: `tests/modules/copilot/test_ask_tenant_data_integration.py::test_lead_count_question_returns_number` y `::test_conversation_count_question`. Resuelto 2026-04-27 commit `b91201ab` — el seed usaba `days=i % 5` que rompía el assert de "esta semana" cada lunes (ISO week reset). Migrado a `minutes=i`.
- [x] **Pre-existing tsc error**: `frontend/src/components/form-runtime/CollapsibleFieldGroup.tsx:32 — Property 'group' does not exist on type 'never'`. Resuelto 2026-04-27 commit `b91201ab` — refactor del bucketing loop con `MutableBucket` interno y look-back via `buckets[buckets.length - 1]`.
