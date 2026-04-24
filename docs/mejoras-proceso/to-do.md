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
