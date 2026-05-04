# Meta Ads Dashboard — Plan de Revisión Completo

**Fecha:** 2026-04-07
**Sesión:** Auditoría integral + fixes de Meta Ads dashboard
**Rama:** `development` (sin commitear aún — 5 archivos modificados + 6 nuevos)

---

## 1. Resumen de lo logrado en esta sesión

### Estado ANTES → DESPUÉS

| Aspecto | Antes | Después |
|---------|-------|---------|
| Dashboard | Spinner infinito (CORS) | Carga datos reales |
| KPIs visibles | 0 | 4: Inversión ($1,359.06), CTR (3.51%), CPC ($0.32), CPM ($11.36) |
| Benchmarks | No existían | CTR "134% mejor que promedio", CPC "73% mejor", CPM "En promedio" |
| Charts | 0 | Inversión vs Resultados (barras diarias, 30d) |
| Funnel | 0 | 119K impressions → 4.2K clics → 1.8K landing → 0 leads → 0 conversiones |
| Demographics | Error 500 | Endpoint funcional (200) |
| Tab Costos | Vacío | CPC + CPM con benchmarks |

### Archivos creados/modificados

**Nuevos:**
- `backend/src/modules/analytics/domain/metric_resolver.py` — Clase pura domain: aliases, recálculo DERIVED/WEIGHTED_AVG, filtro account-level
- `backend/tests/modules/analytics/test_metric_resolver.py` — 33 tests
- `backend/tests/modules/analytics/test_period_metrics_integration.py` — 8 tests
- `frontend/.../meta-ads/__tests__/ResumenTab.test.tsx` — 10 tests
- `frontend/.../meta-ads/__tests__/CostosTab.test.tsx` — 10 tests

**Modificados:**
- `backend/.../channel_dashboard_service.py` — MetricResolver integrado, period_metrics fallback, demographics fix (`deleted_at` eliminado del SQL)
- `backend/.../period_metrics_repository.py` — `get_best_period_metric()` nuevo
- `backend/tests/.../test_channel_dashboard_service.py` — 14 tests nuevos (alias integration + resolver)
- `frontend/.../ResumenTab.tsx` — Graceful degradation para métricas pixel-dependent (ROAS, CPA, conversions muestran "--")
- `frontend/.../CostosTab.tsx` — Graceful degradation + ReferenceLine de benchmark en chart

**Total tests nuevos: 67** | Backend: 1581 pass | Frontend: 490 pass

---

## 2. Pendientes Críticos (impacto directo en el dashboard)

### P1: Metrics sync falla — UniqueViolation en metric_aggregations

**Síntoma:** El sync de Meta extrae data exitosamente pero la transacción se revierte porque IG organic intenta INSERT en `metric_aggregations` con key duplicada.

**Error exacto:**
```
UniqueViolation: duplicate key value violates unique constraint "uq_metric_agg_natural_key"
```

**Constraint:** `(tenant_id, channel_slug, metric_name, period_type, period_start)` en tabla `metric_aggregations`.

**Root cause:** El upsert de `metric_aggregations` usa INSERT sin `ON CONFLICT ... DO UPDATE`. Cuando el sync corre por segunda vez, las mismas combinaciones ya existen.

**Impacto:** Bloquea toda carga de datos nuevos. Los datos en DB son del 2026-03-06 al 2026-03-30 (25 días estáticos). Deberían llegar hasta 2026-04-06.

**Fix propuesto:**
1. Encontrar el INSERT en el service/repo que escribe `metric_aggregations`
2. Cambiar a `INSERT ... ON CONFLICT (tenant_id, channel_slug, metric_name, period_type, period_start) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`
3. Alternativamente, separar la transacción por provider para que un fallo de IG no rollbackee Meta

**Archivos a investigar:**
- `backend/src/modules/analytics/infrastructure/repositories/` — buscar INSERT en metric_aggregations
- `backend/src/modules/analytics/application/services/metrics_sync_service.py` — verificar si hay una transacción compartida multi-provider

**Prioridad:** 🔴 CRÍTICA — sin esto no se cargan datos nuevos.

---

### P2: Campaign sync no pobla ad_campaigns

**Síntoma:** `POST /api/v1/analytics/campaigns/sync` devuelve `{"status": "queued", "job_id": "..."}` (200) pero `ad_campaigns` queda vacía.

**Data actual:** 0 campañas, 0 ads, 0 ad-level metrics.

**Impacto:** Tabs de Campañas y Creativos completamente vacías. Sin campaign data, los metrics a nivel campaign (1240 rows) no se pueden mostrar en breakdown.

**Investigación necesaria:**
1. ¿El job se ejecuta realmente? Revisar si hay un worker/celery/background task
2. ¿El `MetaCampaignProvider` conecta correctamente con la API de Meta?
3. Revisar logs: `docker logs visionarias_brain_dev --tail 100 | grep -i campaign`

**Archivos a investigar:**
- `backend/src/modules/analytics/infrastructure/providers/meta_campaign_provider.py`
- `backend/src/modules/analytics/application/services/campaign_sync_service.py` (o similar)
- `backend/src/modules/analytics/api/` — endpoint de campaign sync

**Prioridad:** 🔴 ALTA — desbloquea 2 tabs completas.

---

### P3: Datos detenidos en 2026-03-30 (7 días desactualizados)

**Estado actual de datos en DB:**

| Tabla | Rows | Rango fechas | Niveles |
|-------|------|-------------|---------|
| official_metrics (meta-ads) | 1853 | 03-06 → 03-30 | 613 acct + 1240 camp + 0 ad |
| period_metrics | 0 | — | — |
| ad_campaigns | 0 | — | — |
| ads | 0 | — | — |
| metric_aggregations | 916 | — | — |

**Causa:** P1 (UniqueViolation) bloquea la inserción de datos nuevos. Si se arregla P1, el sync debería traer 2026-03-31 → 2026-04-06.

**Prioridad:** 🟡 Se resuelve automáticamente al arreglar P1.

---

### P4: KPIs faltantes en tab Resumen

**Frontend espera (RESUMEN_KPIS):** `['spend', 'ROAS', 'conversions', 'CPA', 'CTR', 'reach']`
**Backend hero_metrics (meta-ads):** `['spend', 'ROAS', 'CPL', 'CTR', 'CPC', 'CPM', 'CPA', 'conversions']`

**Qué aparece y qué no:**

| KPI | ¿Aparece? | ¿Por qué? |
|-----|-----------|-----------|
| spend | ✅ | ADDITIVE, datos disponibles |
| CTR | ✅ | DERIVED, recalculado por MetricResolver (clicks/impressions×100) |
| ROAS | ❌ "—" | DERIVED, necesita `meta_purchase_value` ÷ `spend`. `meta_purchase_value` NO existe en DB (0 purchase events en Meta) |
| conversions | ❌ "—" | NO existe como métrica en catalog ni en DB. El provider guarda `meta_purchases` pero no `conversions` |
| CPA | ❌ "—" | DERIVED, necesita `conversions` que no existe |
| reach | ❌ 0.0 | NON_AGGREGABLE, existe en DB pero MetricResolver puede no estar resolviéndolo correctamente para el frontend list |
| CPC | ✅ (solo en Costos) | Aparece en Costos hero_metrics pero NO está en RESUMEN_KPIS |
| CPM | ✅ (solo en Costos) | Aparece en Costos hero_metrics pero NO está en RESUMEN_KPIS |

**Acciones:**
1. **`conversions` alias:** Crear mapping `"conversions" → "meta_purchases"` en ALIAS_MAP (si es que la cuenta de Meta tiene purchases)
2. **`reach` en Resumen:** Verificar que `reach` se agrega correctamente al dict `current_metrics` con la clave "reach" (no un alias)
3. **ROAS será "—" legitimamente** hasta que la cuenta de Meta tenga un pixel con eventos de compra configurados. El frontend ya maneja esto con graceful degradation.

**Prioridad:** 🟡 MEDIA — CPC/CPM ya funcionan; ROAS/CPA/conversions dependen del pixel de Meta.

---

### P5: Tab Costos incompleta

**Estado actual:** Solo muestra 2 KPIs (CPC $0.32, CPM $11.36). Falta:
1. **CPL** — `meta_cost_per_lead` existe en DB pero con valor 0 (no hay leads). El frontend ya muestra "--" para 0.
2. **CPA** — Depende de conversiones (ver P4).
3. **Chart de evolución de costos** — El frontend tiene el componente de LineChart pero no recibe `time_series` data para CPC/CPM. Necesita verificar si `timeseries_metrics` incluye estos y si el backend los devuelve.
4. **CPA por campaña (tabla)** — Sin campaign data (P2), la tabla no puede renderizarse.

**Acciones:**
1. Verificar que `_build_time_series()` recibe datos de `cpc` y `cpm` del daily data
2. El daily data viene del repo — revisar si filtra correctamente solo las métricas en `timeseries_metrics`

**Prioridad:** 🟡 MEDIA — parcialmente funcional.

---

### P6: Demographics sin datos (frontend muestra "Próximamente")

**Estado:** El endpoint ahora retorna 200 (no 500), pero los 3 cards (edad, género, placement) muestran "Próximamente" porque no hay demographics data en DB.

**Root cause:** Los breakdowns de demografía se extraen en el sync general, pero éste falló por P1.

**Para verificar:** Después de arreglar P1 y re-sincronizar, ¿el provider de Meta extrae breakdowns? Buscar en el provider:
- `breakdown=age` + `breakdown=gender` para distribución demográfica
- `breakdown=publisher_platform,platform_position` para placement

**Archivos a investigar:**
- `backend/src/modules/analytics/infrastructure/providers/meta_ads_provider.py` — método de breakdowns
- `backend/src/modules/analytics/application/services/channel_dashboard_service.py` — `_DEMOGRAPHICS_SQL`

**Prioridad:** 🟡 MEDIA — se resuelve probablemente al arreglar P1.

---

## 3. Pendientes Menores (calidad / polish)

### P7: period_metrics tabla vacía

**Estado:** 0 rows. El provider de Meta debería escribir period-level metrics (weekly/monthly reach, frequency) pero la tabla está vacía. El `get_best_period_metric()` que creamos funciona pero no tiene data.

**Investigación:** ¿El provider escribe a `period_metrics`? ¿Solo `metric_aggregations`?

**Impacto:** Reach y frequency usan latest daily value en vez del valor correcto del período.

---

### P8: time_series data no incluye derived metrics

**Observación:** `_build_time_series()` recibe raw daily rows del repo. Las métricas DERIVED (CPC, CPM, CTR, ROAS) existen a nivel diario en `official_metrics` (columnas `cpc`, `cpm`, `ctr`), pero la query del repo filtra por `metric_name IN (timeseries_metrics)`. Si `timeseries_metrics` contiene aliases ("CPC") pero DB tiene "cpc", los alias no matchean.

**Fix:** Resolver aliases en la query del time series.

---

### P9: Funnel "Leads" muestra 0

**Estado:** `meta_leads` no existe como metric_name en DB. Las métricas que existen son `meta_conversations_started` (13 filas). Puede necesitar:
1. Mapear `meta_leads` → `meta_conversations_started` o al metric correcto
2. O aceptar 0 leads porque la cuenta de Meta no tiene Lead Ads configuradas

---

### P10: CORS — fix temporal

**Qué hicimos:** Vaciamos `NEXT_PUBLIC_API_URL` en `.env` para que el frontend use rutas relativas. El container se recrea con env vacío.

**Riesgo:** Si alguien commitea `.env` con el valor viejo, vuelve el problema. El `.env` no está en git (es gitignored), así que solo afecta localmente.

**Acción permanente:** Asegurar que `docker-compose.yml` tiene `NEXT_PUBLIC_API_URL=` vacío y que la rewrite en `next.config.js` `/api/:path*` → `http://api_dev:8000/api/:path*` funciona correctamente (ya funciona).

---

## 4. Hallazgos y Oportunidades de Mejora

### H1: Transacción compartida multi-provider en sync

**Hallazgo:** Un solo provider fallando (IG organic) revienta TODO el sync. Esto es un design smell — cada provider debería tener su propia transacción.

**Mejora:** Wrapping individual por provider con `try/except` + commit parcial. Reportar errores individuales sin bloquear los demás.

---

### H2: metric_aggregations usa INSERT en vez de upsert

**Hallazgo:** La tabla `metric_aggregations` tiene un unique constraint pero el código usa INSERT simple. Esto debería ser INSERT ON CONFLICT DO UPDATE desde el inicio.

**Patrón correcto (ya usado en official_metrics):**
```sql
INSERT INTO metric_aggregations (...)
VALUES (...)
ON CONFLICT (tenant_id, channel_slug, metric_name, period_type, period_start)
DO UPDATE SET value = EXCLUDED.value, updated_at = now()
```

---

### H3: Alias mismatch entre frontend y backend

**Hallazgo:** El frontend usa `metricName` strings arbitrarios (`'spend'`, `'ROAS'`, `'CTR'`) y los compara con lo que el backend devuelve en `kpi.metric_name`. Esto funciona SOLO porque la integración MetricResolver ahora usa el mismo alias como `metric_name` en el response. Pero es frágil.

**Mejora a futuro:** Definir un enum/constante compartida (ej: en CONTRACT.md) con los metric_names canónicos que ambos lados usan.

---

### H4: ResumenTab y CostosTab no comparten KPI list

**Hallazgo:** `RESUMEN_KPIS = ['spend', 'ROAS', 'conversions', 'CPA', 'CTR', 'reach']` en ResumenTab vs `COSTOS_KPIS = ['CPC', 'CPM', 'CPL', 'CPA']` en CostosTab. Ambos son arrays hardcodeados. Si el backend cambia `hero_metrics`, el frontend se desincroniza.

**Mejora:** El backend ya devuelve `kpis[]` con todos los metrics. El frontend podría usar la lista del backend en vez de filtrar por un array local.

---

### H5: Daily metrics terminan en 2026-03-30 (stale data)

**Hallazgo:** Solo 25 días de datos (03-06 → 03-30). El sync del 2026-04-07 extrajo nuevos datos (vi `meta_video_30sec` con fecha 04-05 y 04-06 en los logs) pero la transacción se revirtió por P1.

**Dato clave encontrado en logs:** El sync SÍ extrae data fresca de Meta — el token es válido y la API responde. El único blocker es el bug de upsert (P1).

---

### H6: Credenciales E2E desactualizadas

**Hallazgo:** La contraseña del usuario `e2e-test@nicolify.com` en código (`E2eTest!2026secure`) no coincide con la real en Clerk. Tuvimos que usar las credenciales personales de Chris.

**Acción:** Actualizar la contraseña del usuario E2E en Clerk para que coincida con lo que dice el código, o actualizar el código.

---

### H7: campaign sync es fire-and-forget sin feedback

**Hallazgo:** `POST /api/v1/analytics/campaigns/sync` devuelve `{"status": "queued", "job_id": "..."}` pero no hay forma de verificar si el job se completó ni su resultado.

**Mejora:** Agregar endpoint `GET /api/v1/analytics/campaigns/sync/{job_id}/status` o al menos logs estructurados con el job_id para debugging.

---

### H8: Demographics SQL tenía `deleted_at IS NULL` inexistente

**Hallazgo:** El SQL de demographics incluía `AND deleted_at IS NULL` pero la tabla `official_metrics` no tiene esa columna. Esto causaba el 500. Ya fue arreglado.

**Pattern smell:** Copiar SQL de otros contextos sin verificar el schema. Puede existir en otros SQL raw queries del analytics module.

**Acción:** Grep por `deleted_at` en todos los SQL raw del módulo analytics para verificar que no hay más instancias.

---

### H9: Copilot muestra "1 Issue" badge

**Hallazgo:** En todos los screenshots se ve un badge rojo "1 Issue" en la esquina inferior izquierda (del copilot). Probablemente un error del copilot nudge que persiste.

---

### H10: Google Analytics token revocado

**Hallazgo:** El sync de GA4 falla con `invalid_scope: Bad Request`. El OAuth token está expirado/revocado.

**Acción:** Re-autenticar la conexión de Google Analytics en Configuración → Conexiones.

---

## 5. Orden de ejecución recomendado

```
Sesión 1 (Backend — bugs bloqueantes):
├── P1: Fix upsert metric_aggregations (INSERT ON CONFLICT)
├── P1b: Separar transacciones por provider (IG no bloquea Meta)
├── Re-sync: Verificar que datos nuevos (04-01 → 04-06) se cargan
└── P2: Investigar + fix campaign sync

Sesión 2 (Backend — data quality):
├── P4: Agregar alias "conversions" → "meta_purchases" (si aplica)
├── P8: Resolver aliases en query de time_series
├── P9: Verificar meta_leads mapping
├── P7: Verificar si provider escribe a period_metrics
└── P6: Verificar demographics tras re-sync exitoso

Sesión 3 (Frontend — polish):
├── P5: Chart de evolución de costos (depende de P8)
├── P10: Documentar CORS fix definitivo
├── H4: Considerar usar kpis del backend en vez de arrays hardcoded
└── H6: Actualizar credenciales E2E

Sesión 4 (Mejora de proceso):
├── H1: Refactor transacciones por provider
├── H3: CONTRACT.md con metric names canónicos
├── H7: Status endpoint para campaign sync
└── H8: Audit de SQL raw para deleted_at fantasma
```

---

## 6. Cómo commitear lo de esta sesión

Los cambios actuales son estables (1581 backend tests + 490 frontend tests pasan). Se pueden commitear como:

```
feat(analytics): integrate MetricResolver for correct KPI calculation

- Create MetricResolver domain class (aliases, DERIVED/WEIGHTED_AVG recalculation, account-level filtering)
- Integrate into ChannelDashboardService for KPI + time series resolution
- Add period_metrics fallback for NON_AGGREGABLE metrics (reach, frequency)
- Fix demographics 500 (removed non-existent deleted_at column from SQL)
- Add graceful degradation in ResumenTab/CostosTab for pixel-dependent metrics
- 67 new tests (33 metric_resolver + 14 period_metrics + 20 frontend)
```

---

## 7. Datos de contexto para la próxima sesión

**Tenant:** Visionarias (`6347e21e-8112-4aa1-80d3-6adaa73bf6f9`)
**Token Meta:** ✅ Activo (validado 2026-04-07, extracción exitosa antes del rollback)
**Token GA4:** ❌ Revocado (`invalid_scope`)
**Auth usuario:** `christian.revilla.m@gmail.com` / autenticado via Playwright, auth state guardado en `playwright/.clerk/user.json`
**Containers:** `visionarias_brain_dev` (API), `visionarias_client_dev` (Next.js con NEXT_PUBLIC_API_URL vacío), `visionarias_postgres`
**Variable CORS:** `NEXT_PUBLIC_API_URL=` (vacío en `.env`, container recreado)
