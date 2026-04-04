---
module: Analytics
status: active
---

# Analytics

Extrae, transforma y consolida metricas de 11+ proveedores externos e internos para visualizar el estado completo del negocio en un funnel Bowtie de 8 etapas. Dominio de solo lectura (CQRS) — nunca modifica datos de otros modulos.

## Conceptos de Dominio

- **Bowtie Funnel:** 8 etapas (attraction, capture, nurture, opportunity, sales, adoption, expansion, evangelization) + summary + timeseries. Cada etapa tiene su propio stage service y DTO.
- **MetricDefinition (metric_catalog):** Contrato semantico para cada metrica: nombre, unidad, tipo de agregacion, formula (si es derivada), peso (si es weighted), proveedor. Es la fuente de verdad — no inventar metricas fuera del catalogo.
- **AggregationType:** Controla como se agrega en periodos multi-dia. ADDITIVE (SUM seguro), WEIGHTED_AVERAGE (requiere denominador), DERIVED (recalcular de componentes), NON_AGGREGABLE (solo diario, personas unicas), SNAPSHOT (ultimo valor del periodo).
- **STAGE_CHANNEL_MAP (channel_registry):** Mapa declarativo stage -> canales con metadata completa (slug, provider_name, metric_names). Determina que canales muestra cada etapa y si estan conectados.

## Decisiones de Arquitectura

- **Pipeline atomico:** El ETL (extract -> stage -> transform -> official -> aggregate -> invalidate cache) corre en una sola transaccion. Si falla cualquier paso, todo hace rollback. La invalidacion de cache es best-effort fuera de la transaccion.
- **Providers como adaptadores:** 11 providers registrados en PROVIDER_REGISTRY (meta, google_analytics, google_ads, tiktok, youtube, crm_internal, shopify, manychat, mailerlite, meta_pixel, search_console). Se resuelven por nombre en runtime — agregar un provider nuevo requiere solo implementar BaseMetricsProvider y registrarlo.
- **Cache por etapa con TTL diferenciado:** Redis con key `metrics:{tenant_id}:{stage}:{period}`. Attraction tiene TTL largo (1h, datos pagados cambian lento), summary tiene TTL corto (1min). Cache falla silenciosamente — Redis es solo optimizacion.
- **Scheduler timezone-aware:** Un cron cada minuto evalua todos los tenants y encola extraccion cuando son las 3am en la zona horaria local del tenant. Los tenants con mayor extraction_priority se procesan primero.
- **ConnectionPort (DDD boundary):** Analytics nunca importa directamente del modulo connections. Usa un puerto `ConnectionPort` para obtener credenciales — esto mantiene la frontera DDD limpia.

## Reglas de Negocio

- Toda metrica DEBE existir en el metric_catalog con su AggregationType correcta antes de ser extraida. Sumar metricas NON_AGGREGABLE cross-day produce numeros inflados.
- Los periodos (weekly, monthly, quarterly) respetan la configuracion del tenant (weekly_start_day, fiscal_year_start_month) via TenantPeriodConfig.
- El cooldown de refresh por proveedor es 15 minutos (PER_PROVIDER_REFRESH_COOLDOWN). El global es 2 minutos. Ignorar estos limites satura las APIs externas.
- CostType (NEUTRAL, EXPENSE, INVESTMENT, REVENUE) se asigna via cost_type_mapping y afecta los calculos de ROI en el frontend.

## Casos Borde

- **Retry con Fibonacci backoff:** Los jobs ARQ reintentan con intervalos [1, 1, 2, 3, 5, 8, 13] minutos. ConnectionRevokedException NO reintenta (falla permanente).
- **PARTIAL_SUCCESS:** Si un provider extrae algunas metricas pero falla en sub-extractors, el pipeline registra partial_success (no pierde lo que si se obtuvo).
- **Period extraction separada:** Las metricas NON_AGGREGABLE (unique users, reach) requieren un pipeline de periodo dedicado (run_period_extraction) que se dispara al cruzar fronteras de semana/mes/trimestre.
- **Desfase de datos:** Si el scheduler o worker fallan, el dashboard muestra datos del dia anterior sin aviso visible al usuario.

## CRITICAL — No Violar

- NUNCA sumar metricas NON_AGGREGABLE entre dias — usar solo el pipeline de periodo.
- NUNCA agregar un provider sin registrarlo en PROVIDER_REGISTRY — el pipeline no lo encontrara.
- NUNCA hacer queries de metricas sin filtrar por tenant_id — el cache key incluye tenant_id, pero la DB no tiene RLS.
- Las tablas staging se borran por tenant+provider antes de cada extraccion (delete_by_tenant_provider) — esto es intencional, no es un bug.
