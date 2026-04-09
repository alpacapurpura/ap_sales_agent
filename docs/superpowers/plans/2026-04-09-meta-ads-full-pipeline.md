# Plan: Meta Ads — Pipeline completo de extracción a visualización

**Fecha:** 2026-04-09
**Contexto:** El dashboard Meta Ads tiene UI completa (5 tabs) pero la mayoría de datos no se muestran porque el pipeline de datos tiene gaps. Token Meta recién reconectado.

## Estado actual de datos

| Recurso | Rows | Estado |
|---------|------|--------|
| `official_metrics` (account-level, ad_id=NULL) | 5,130 | Solo métricas agregadas |
| `official_metrics` (campaign-level, campaign_id set) | 0 | Extracción campaign-level no funciona |
| `official_metrics` (ad-level, ad_id set) | 0 | Extracción ad-level no funciona |
| `ad_campaigns` (hierarchy) | 0 | Campaign sync nunca ejecutado |
| Video metrics (`meta_video_*`) | ~200 c/u | Existen, SQL ya corregido |
| Extraction runs | `partial_success`, 2 metrics/run | Solo account-level completa |
| Token Meta | Recién reconectado | Verificar que funciona |

## Arquitectura del pipeline (2 flujos separados)

```
FLUJO A: Campaign Hierarchy Sync (ad_campaigns, ad_sets, ads)
  Trigger: POST /campaigns/sync (manual) o ARQ job run_campaign_sync
  Proveedor: MetaCampaignProvider
  Pipeline: CampaignSyncPipeline → CampaignRepository.upsert_*
  Scheduler: NO está en el scheduler diario ← GAP

FLUJO B: Metrics ETL (official_metrics)
  Trigger: Scheduler 3am → run_tenant_extraction
  Proveedor: MetaProvider.extract_metrics()
    ├─ _extract_meta_ads()            → account-level (funciona, 5130 rows)
    ├─ _extract_meta_ads_campaigns()  → campaign-level (falla silenciosamente)
    ├─ _extract_meta_ads_by_ad()      → ad-level (falla silenciosamente)
    ├─ _extract_meta_ads_breakdowns() → demographics (funciona parcialmente)
    └─ _extract_meta_ads_period()     → reach/frequency periodo (funciona)
  Pipeline: ETLPipeline → staging → official_metrics
```

## Gaps a cerrar (en orden de prioridad)

### Gap 1: Diagnosticar por qué campaign/ad extraction falla

**Archivos:** `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`

El ETL llama `_extract_meta_ads_campaigns()` y `_extract_meta_ads_by_ad()` pero solo se extraen 2 metrics por run. Posibles causas:
- Token sin permisos `ads_read` o `ads_management`
- `ad_account_id` no configurado en credentials
- Rate limiting de Meta API
- Error silencioso en `_safe_extract()` que no loguea el fallo

**Acción:**
1. Verificar que `credentials` tiene `ad_account_id` y `access_token` válidos
2. Ejecutar manualmente la extracción campaign-level y capturar errores
3. Revisar logs: `docker logs visionarias_brain_dev --tail 500 2>&1 | grep -i 'meta\|campaign\|extract'`
4. Si falla por permisos, documentar qué scopes necesita el token

**Test:** Test unitario que mockea Meta API response para campaign-level y verifica que `campaign_id` se propaga a `official_metrics`

### Gap 2: Campaign sync no está en el scheduler

**Archivo:** `backend/src/modules/analytics/workers/scheduler.py`

El scheduler (`run_tick_scheduler`) solo encola `run_tenant_extraction` y `run_period_extraction`. **Nunca encola `run_campaign_sync`.**

**Acción:**
1. Agregar `run_campaign_sync` al scheduler (diario o cada 6h, después del ETL de métricas)
2. Alternativa: llamar campaign sync automáticamente después de cada ETL exitoso
3. Asegurar que el sync es idempotente (ya usa upsert)

**Test:** Test que verifica que `run_tick_scheduler` encola `run_campaign_sync` para tenants con Meta conectado

### Gap 3: Poblar ad_campaigns para llenar Campañas tab

**Archivos:**
- `backend/src/modules/analytics/infrastructure/providers/meta_campaign_provider.py`
- `backend/src/modules/analytics/infrastructure/sync/campaign_sync_pipeline.py`
- `backend/src/modules/analytics/application/services/campaign_service.py`

**Acción:**
1. Trigger manual: `POST /api/v1/analytics/campaigns/sync` desde la UI o curl
2. Verificar que `MetaCampaignProvider` extrae campaigns, ad_sets, y ads con sus metadatos (objective, status, budget, creative_thumbnail_url, etc.)
3. Verificar que `ad_campaigns` se puebla con los datos correctos

**Test:**
- Test de integración: mock Meta Graph API → CampaignSyncPipeline → verificar rows en ad_campaigns
- Test que `get_campaign_performance()` retorna datos cuando `ad_campaigns` + `official_metrics` tienen datos

### Gap 4: Ad-level metrics para Creativos tab

**Archivos:**
- `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` (`_extract_meta_ads_by_ad`)
- `backend/src/modules/analytics/application/services/ad_performance_service.py`

**Acción:**
1. Verificar que `_extract_meta_ads_by_ad()` genera `ExtractedMetric` con `ad_id` poblado
2. Verificar que `transform_staging_to_official()` preserva `ad_id`
3. Verificar que `AdPerformanceService.get_top_ads()` hace JOIN con `ads` table para thumbnails
4. Si ad-level extraction falla por volumen, implementar paginación o límite de ads

**Test:**
- Test unitario: mock response de Meta Ads Insights con `level=ad` → verificar que `ad_id` se propaga
- Test de servicio: dados `official_metrics` con `ad_id` + `ads` table con thumbnails → `get_top_ads()` retorna AdMetrics completos

### Gap 5: Format comparison necesita ad-level data

**Archivo:** `backend/src/modules/analytics/application/services/ad_performance_service.py`

`get_format_comparison()` agrupa por `format_type` de la tabla `ads`. Sin rows en `ads`, retorna vacío.

**Acción:** Se resuelve automáticamente cuando Gap 3 (campaign sync) y Gap 4 (ad metrics) funcionan. Solo verificar que `_detect_format_type()` clasifica correctamente (video/carousel/image).

**Test:** Test que dados 3 ads (video, carousel, image) con métricas, `get_format_comparison()` retorna 3 formatos con CTR, CPA, ROAS calculados correctamente

### Gap 6: Logging de fallos de extracción

**Archivo:** `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`

`_safe_extract()` captura excepciones pero `sub_extractor_failures` muestra `[]`. Mejorar logging.

**Acción:**
1. Asegurar que `_safe_extract()` registra el nombre del sub-extractor y el error en `failures`
2. Agregar `structlog` info para cada sub-extractor que inicia/completa/falla
3. Verificar que `extraction_runs.sub_extractor_failures` se popula correctamente

**Test:** Test que cuando `_extract_meta_ads_campaigns` lanza excepción, `sub_extractor_failures` contiene el error

## Tests end-to-end requeridos

### Backend (pytest)

| Test | Qué verifica |
|------|-------------|
| `test_meta_campaign_extraction` | Mock Meta API → MetaCampaignProvider extrae campaigns/ads correctamente |
| `test_campaign_sync_pipeline` | CampaignSyncPipeline puebla ad_campaigns con upsert idempotente |
| `test_campaign_level_metrics_extraction` | MetaProvider campaign-level → official_metrics con campaign_id |
| `test_ad_level_metrics_extraction` | MetaProvider ad-level → official_metrics con ad_id |
| `test_campaign_performance_service` | campaign metrics + ad_campaigns → CampaignPerformanceData completa |
| `test_ad_performance_service` | ad metrics + ads table → top ads con thumbnails y métricas |
| `test_format_comparison` | ads con distintos formats → agrupación correcta con derived metrics |
| `test_video_retention_correct_names` | Ya existe (corregido), verificar con datos reales |
| `test_scheduler_enqueues_campaign_sync` | Scheduler encola campaign sync para tenants Meta |
| `test_sub_extractor_failure_logging` | Fallo en sub-extractor se registra en extraction_runs |

### Frontend (vitest)

| Test | Qué verifica |
|------|-------------|
| `test_campaigns_tab_renders_data` | CampaignsTab muestra tabla con campaigns cuando hay datos |
| `test_creativos_top_ads` | CreativosTab muestra cards de ads con thumbnails |
| `test_creativos_format_comparison` | FormatRow renderiza 3 formatos (video/carousel/image) |
| `test_creativos_video_retention` | Video retention bars se renderizan con datos reales |
| `test_creativos_video_kpis` | "Vistas 30s+" y "Duración promedio" muestran valores |

## Orden de ejecución

```
1. Gap 1: Diagnosticar (exploración, no código)
   → Verificar token + credentials + logs
   → Trigger manual de extracción y observar errores

2. Gap 6: Logging (pre-requisito para diagnosticar)
   → Mejorar _safe_extract logging
   → Re-run extracción y leer failures

3. Gap 2: Scheduler (backend)
   → Agregar campaign sync al scheduler
   → Test

4. Gap 3: Campaign sync (verificar que funciona)
   → Trigger manual → verificar ad_campaigns poblado
   → Tests de integración

5. Gap 4: Ad-level metrics (probablemente se resuelve con Gap 1)
   → Si el diagnóstico revela el problema, fix + test

6. Gap 5: Format comparison (se resuelve solo)
   → Verificar después de Gaps 3+4

7. Tests e2e frontend
   → Una vez que hay datos reales, verificar visualmente
```

## Archivos clave

| Archivo | Para qué |
|---------|----------|
| `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` | ETL Meta: extract_metrics, _safe_extract |
| `backend/src/modules/analytics/infrastructure/providers/meta_campaign_provider.py` | Campaign hierarchy sync |
| `backend/src/modules/analytics/infrastructure/sync/campaign_sync_pipeline.py` | Orchestrates campaign sync |
| `backend/src/modules/analytics/workers/scheduler.py` | Daily scheduler (needs campaign sync) |
| `backend/src/modules/analytics/workers/tasks.py` | ARQ tasks (run_campaign_sync) |
| `backend/src/modules/analytics/application/services/campaign_service.py` | Campaign performance queries |
| `backend/src/modules/analytics/application/services/ad_performance_service.py` | Ad-level performance |
| `backend/src/modules/analytics/api/campaigns.py` | Campaign API routes |
| `frontend/src/features/growth-studio/api/campaigns-api.ts` | Frontend API hooks |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/` | 5 dashboard tabs |

## Verificación final

Después de implementar todos los gaps, el dashboard debe mostrar:

- **Resumen:** 6 KPIs con datos reales + chart con línea ROAS + funnel completo
- **Campañas:** Tabla con campaigns reales (status, budget, métricas por campaña)
- **Creativos:** Top 3 ads con thumbnails + format comparison + video retention con datos reales
- **Audiencia:** Demographics reales (edad, género, placement)
- **Costos:** 4 KPIs de costo con benchmarks + CPA por campaña real
