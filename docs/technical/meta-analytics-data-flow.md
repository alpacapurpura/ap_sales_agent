# Meta Analytics — Flujo de Datos Completo

Documento de auditoría que describe paso a paso cómo Nicolify extrae, transforma, almacena y presenta los datos de Meta (Instagram, Facebook, Meta Ads) en Growth Studio.

---

## Tabla de Contenidos

1. [Resumen del Pipeline](#1-resumen-del-pipeline)
2. [Paso 1: Conexión OAuth y Obtención de Credenciales](#2-paso-1-conexión-oauth-y-obtención-de-credenciales)
3. [Paso 2: Almacenamiento de Credenciales](#3-paso-2-almacenamiento-de-credenciales)
4. [Paso 3: Scheduling — Cuándo se Extraen los Datos](#4-paso-3-scheduling--cuándo-se-extraen-los-datos)
5. [Paso 4: Extracción (E del ETL)](#5-paso-4-extracción-e-del-etl)
6. [Paso 5: Transformación (T del ETL)](#6-paso-5-transformación-t-del-etl)
7. [Paso 6: Carga (L del ETL)](#7-paso-6-carga-l-del-etl)
8. [Paso 7: Agregaciones Pre-computadas](#8-paso-7-agregaciones-pre-computadas)
9. [Paso 8: Cache (Redis)](#9-paso-8-cache-redis)
10. [Paso 9: API — Cómo el Frontend Consume los Datos](#10-paso-9-api--cómo-el-frontend-consume-los-datos)
11. [Paso 10: Frontend — Presentación en Growth Studio](#11-paso-10-frontend--presentación-en-growth-studio)
12. [Catálogo Completo de Métricas Meta](#12-catálogo-completo-de-métricas-meta)
13. [Esquema de Base de Datos](#13-esquema-de-base-de-datos)
14. [Manejo de Errores y Reintentos](#14-manejo-de-errores-y-reintentos)
15. [Walkthrough: Día Completo de un Tenant](#15-walkthrough-día-completo-de-un-tenant)
16. [Mapa de Archivos](#16-mapa-de-archivos)

---

## 1. Resumen del Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────────┐    ┌─────────┐
│  Meta OAuth  │───>│  Credentials │───>│   Scheduler  │───>│  ETL Pipeline │───>│  Redis  │
│  (Conexión)  │    │  (Encrypted) │    │  (3AM local) │    │  (Extract →   │    │  Cache  │
└─────────────┘    └──────────────┘    └──────────────┘    │   Transform → │    └────┬────┘
                                                           │   Load)       │         │
                                                           └───────┬───────┘    ┌────▼────┐
                                                                   │            │   API   │
                                                           ┌───────▼───────┐    │  REST   │
                                                           │  PostgreSQL   │───>│ /metrics│
                                                           │  (3 tablas)   │    └────┬────┘
                                                           └───────────────┘         │
                                                                               ┌─────▼──────┐
                                                                               │  Frontend   │
                                                                               │  Growth     │
                                                                               │  Studio     │
                                                                               └────────────┘
```

**Sí, es un ETL completo.** El pipeline sigue el patrón clásico Extract-Transform-Load con:
- **Extract:** Llamadas a Meta Graph API v24.0
- **Transform:** Clasificación de cost_type + normalización de métricas
- **Load:** Staging → Official metrics (upsert) → Aggregations

---

## 2. Paso 1: Conexión OAuth y Obtención de Credenciales

**Archivo:** `backend/src/modules/connections/infrastructure/channels/meta.py` — clase `MetaAdapter`

### Flujo OAuth

1. El usuario hace clic en "Conectar Meta" en el frontend
2. `MetaAdapter.get_authorization_url()` genera la URL de Facebook OAuth con estos scopes:
   - `public_profile` — perfil básico
   - `email` — email del usuario
   - `pages_show_list` — listar páginas administradas
   - `pages_read_engagement` — leer métricas de engagement de páginas
   - `instagram_basic` — acceso básico a Instagram Business
   - `ads_read` — leer datos de campañas publicitarias
3. El usuario autoriza en Facebook → recibe un `auth_code`
4. `MetaAdapter.exchange_code(auth_code)` intercambia el código por un **short-lived token** (~1 hora)
5. Se extiende a un **long-lived token** (~60 días) via `GET /oauth/access_token?grant_type=fb_exchange_token`
6. Se hace descubrimiento de activos del usuario:
   - Páginas de Facebook administradas → `page_id`, `page_access_token`
   - Cuentas de Instagram Business vinculadas → `instagram_account_id`
   - Cuentas publicitarias → `ad_account_id`, `currency`

### Sincronización de Activos

**Archivo:** `backend/src/modules/connections/api/meta.py` — función `_sync_assets_for_tenant()`

Se crean registros separados en `channel_connections` por cada activo:

| channel_type | Credenciales almacenadas |
|---|---|
| `FACEBOOK_PAGE` | `page_id`, `page_access_token`, `page_name`, `fan_count`, `category` |
| `INSTAGRAM_ACCOUNT` | `instagram_account_id`, `access_token`, `username`, `followers_count` |
| `META_ADS_ACCOUNT` | `ad_account_id`, `access_token`, `currency`, `account_name` |

### Carga Inicial (Initial Load)

Inmediatamente después de conectar, se dispara un job `run_initial_load`:
- Extrae los **últimos 7 días** de datos
- Esto permite que el usuario vea métricas al instante, sin esperar al cron de las 3 AM

**Archivo:** `backend/src/modules/analytics/workers/tasks.py` — función `run_initial_load()`

---

## 3. Paso 2: Almacenamiento de Credenciales

**Modelo:** `ChannelConnectionModel` en `backend/src/modules/connections/infrastructure/models/channel_connection_model.py`

```
channel_connections
├── id (UUID, PK)
├── tenant_id (UUID) ← aislamiento multitenant
├── channel_type (VARCHAR) ← "meta", "facebook_page", "instagram_account", "meta_ads_account"
├── credentials (EncryptedJSON) ← cifrado Fernet simétrico
│   └── {access_token, page_access_token, ad_account_id, page_id, instagram_account_id, currency}
├── config (JSONB) ← metadata del activo (nombres, categorías, etc.)
├── is_active (BOOLEAN) ← soft delete
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)
```

Las credenciales se almacenan **cifradas** con Fernet (cifrado simétrico). Solo se descifran al momento de hacer las llamadas API.

### Refresh de Token

**Archivo:** `backend/src/modules/connections/application/services/connection_port_impl.py` — clase `ConnectionPortImpl`

- Los tokens de Meta expiran a los ~60 días
- `get_credentials()` verifica la expiración antes de retornar
- Si está por expirar, llama al endpoint de refresh de Meta transparentemente
- El token renovado se persiste de vuelta al modelo

### Puente entre Módulos (DDD Port)

El módulo `analytics` no importa directamente de `connections`. Usa una interfaz (port):

**Puerto:** `backend/src/modules/analytics/domain/ports.py` — `ConnectionPort` (ABC)

```python
class ConnectionPort(ABC):
    async def get_credentials(self, tenant_id: UUID, provider_name: str) -> ConnectionCredentials
    async def list_active_connections(self, tenant_id: UUID) -> List[ConnectionCredentials]
```

**Implementación:** `ConnectionPortImpl` en el módulo `connections` implementa este ABC.

---

## 4. Paso 3: Scheduling — Cuándo se Extraen los Datos

**Archivo:** `backend/src/modules/analytics/workers/scheduler.py` — función `run_tick_scheduler()`

### Extracción Diaria Automática

| Evento | Frecuencia | Qué hace |
|---|---|---|
| `run_tick_scheduler` | Cada minuto | Evalúa si algún tenant necesita extracción |
| Condición de disparo | 3:00 AM hora local del tenant | Encola `run_tenant_extraction` |

**Lógica del scheduler:**
1. Se ejecuta cada minuto via ARQ cron
2. Consulta todos los tenants activos, ordenados por `extraction_priority DESC`
3. Convierte la hora UTC actual a la zona horaria local del tenant
4. Si son las 3:00 AM locales → encola job `run_tenant_extraction(provider="all")`
5. `provider="all"` significa que extrae de **todos** los proveedores conectados (Meta, Google, etc.)

### Extracción Bajo Demanda

El usuario puede forzar una extracción manual:
- Botón "Actualizar" en Growth Studio
- Llama a `POST /etl/retry/{run_id}`
- Cooldown de 15 minutos entre extracciones manuales

---

## 5. Paso 4: Extracción (E del ETL)

### Registro de Proveedores

**Archivo:** `backend/src/modules/analytics/infrastructure/providers/registry.py`

Cada proveedor (Meta, Google, TikTok, etc.) se registra como una subclase de `BaseMetricsProvider`. El registry resuelve `"meta"` → `MetaProvider()` en runtime.

### Interfaz Base

**Archivo:** `backend/src/modules/analytics/infrastructure/providers/base.py`

```python
class BaseMetricsProvider(ABC):
    def provider_name(self) -> str: ...          # "meta"
    def rate_limit_config(self) -> dict: ...     # {"requests_per_minute": 200, "burst_size": 50}
    async def extract_metrics(
        self, tenant_id, credentials, start_date, end_date, stage
    ) -> List[ExtractedMetric]: ...
```

**Valor de transporte:** `ExtractedMetric` (Pydantic model)

```python
class ExtractedMetric(BaseModel):
    provider: str          # "meta"
    channel_slug: str      # "ig-organic", "meta-ads", etc.
    metric_name: str       # "reach", "spend", etc.
    value: float           # 10000.0
    unit: str              # "count", "currency", "percentage", "ratio"
    currency: Optional[str]  # "USD", "MXN", "EUR"
    date: date             # 2026-03-21
    campaign_id: Optional[str]
    ad_set_id: Optional[str]
    ad_id: Optional[str]
    extra: Dict            # {likes: 300, comments: 80}
```

### MetaProvider — Extracción Detallada

**Archivo:** `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`

El MetaProvider enruta por **stage** (etapa del funnel):

```
extract_metrics(stage)
├── stage="attraction" (default)
│   ├── _extract_instagram_organic()  → ig-organic
│   ├── _extract_facebook_organic()   → fb-organic
│   └── _extract_meta_ads()           → meta-ads
│
└── stage="nurturing"
    └── _extract_meta_retargeting()   → meta-retargeting
```

#### 5.1 Instagram Organic (`ig-organic`)

**Método:** `_extract_instagram_organic()`

**Llamadas a la API:**

| # | Endpoint | Parámetros | Dato extraído |
|---|---|---|---|
| 1 | `GET /{ig_account_id}/insights` | `metric=reach, period=day, since/until` | Reach diario (sumado) |
| 2 | `GET /{ig_account_id}/media` | `fields=like_count,comments_count,timestamp, limit=100` | Likes y comments por post |

**Métricas producidas:**

| metric_name | unit | Cómo se calcula |
|---|---|---|
| `reach` | count | Suma de `values[].value` del insight de reach diario |
| `engagement` | count | `total_likes + total_comments` de los últimos 100 posts |

El engagement incluye un breakdown en `extra`: `{likes, comments, shares: 0, saves: 0}` (shares y saves no están disponibles via la API actual).

**Autenticación:** Header `Authorization: Bearer {access_token}` (no en query params).

#### 5.2 Facebook Organic (`fb-organic`)

**Método:** `_extract_facebook_organic()`

**Llamadas a la API:**

| # | Endpoint | Parámetros | Dato extraído |
|---|---|---|---|
| 1 | `GET /{page_id}/insights` | `metric=page_impressions_unique, period=day` | Reach único diario |
| 2 | `GET /{page_id}/insights` | `metric=page_post_engagements, period=day` | Engagements de posts |

**Métricas producidas:**

| metric_name | unit | Cómo se calcula |
|---|---|---|
| `reach` | count | Suma de impresiones únicas diarias |
| `engagement` | count | Suma de engagements de posts diarios |

**Nota:** Usa `page_access_token` si existe, fallback a `access_token`.

#### 5.3 Meta Ads (`meta-ads`)

**Método:** `_extract_meta_ads()`

**Llamada a la API:**

| Endpoint | Parámetros |
|---|---|
| `GET /act_{ad_account_id}/insights` | `fields=reach,impressions,clicks,spend,frequency,ctr,cpm,actions` + `time_range` + `level=account` |

**Parseo de conversiones:**
El campo `actions` de Meta es un array de objetos `{action_type, value}`. Se filtran específicamente:
- `offsite_conversion.fb_pixel_purchase` — compras vía Facebook Pixel
- `onsite_conversion.purchase` — compras dentro de Facebook/IG

Otros action_types (link_click, page_engagement, etc.) se ignoran para el conteo de conversiones.

**Métricas producidas:**

| metric_name | unit | Descripción |
|---|---|---|
| `reach` | count | Personas únicas que vieron los ads |
| `impressions` | count | Total de veces que se mostraron los ads (incluye repeticiones) |
| `clicks` | count | Clicks totales en los ads |
| `ctr` | percentage | Click-through rate (calculado por Meta server-side) |
| `cpm` | currency | Costo por mil impresiones |
| `frequency` | ratio | Promedio de veces que cada persona vio el ad |
| `conversions` | count | Compras atribuidas (pixel + onsite) |
| `spend` | currency | Gasto total en la moneda de la cuenta publicitaria |

**Currency:** Se lee de `credentials.get("currency", "USD")` — viene de la configuración de la cuenta publicitaria del tenant.

#### 5.4 Meta Retargeting (`meta-retargeting`)

**Método:** `_extract_meta_retargeting()` — solo se ejecuta cuando `stage="nurturing"`

**Llamada a la API:**

| Endpoint | Parámetros |
|---|---|
| `GET /act_{ad_account_id}/adsets` | `fields=id,name,targeting,insights.time_range(...){reach,clicks,spend}` + `limit=200` |

**Lógica de filtrado:**
1. Se obtienen TODOS los adsets de la cuenta
2. Para cada adset, se revisa `targeting.custom_audiences`
3. **Solo se incluyen** adsets que tienen custom audiences (retargeting)
4. Los adsets sin custom audiences se descartan

> **Nota técnica:** `targeting.custom_audiences` vive en el nivel de **adset**, no de campaign. Esto es un detalle importante de la Meta API que es fácil pasar por alto.

**Métricas producidas:**

| metric_name | unit | Descripción |
|---|---|---|
| `reach` | count | Personas únicas alcanzadas por retargeting |
| `clicks` | count | Clicks en ads de retargeting |
| `spend` | currency | Gasto en retargeting |

---

## 6. Paso 5: Transformación (T del ETL)

**Archivo:** `backend/src/modules/analytics/infrastructure/etl/pipeline.py` — clase `ETLPipeline`

### 6.1 Clasificación de Cost Type

**Archivo:** `backend/src/modules/analytics/application/cost_type_mapping.py`

Cada combinación `(channel_slug, stage_slug)` se mapea a un tipo de costo:

| channel_slug | stage | CostType | Significado |
|---|---|---|---|
| `ig-organic` | attraction | `NEUTRAL` | Sin costo directo |
| `fb-organic` | attraction | `NEUTRAL` | Sin costo directo |
| `meta-ads` | attraction | `INVESTMENT` | Gasto publicitario con ROI esperado |
| `meta-retargeting` | nurture | `INVESTMENT` | Gasto en retargeting con ROI esperado |

**Enum CostType** (`backend/src/modules/analytics/domain/enums.py`):
- `NEUTRAL` — Canales orgánicos, sin costo
- `EXPENSE` — Herramientas operativas (ej: suscripción a MailerLite)
- `INVESTMENT` — Publicidad pagada (se espera retorno)
- `REVENUE` — Canales de venta/ingreso

### 6.2 Normalización

La transformación convierte cada `ExtractedMetric` en un diccionario preparado para upsert, agregando:
- `cost_type` según el mapping
- `source_extraction_run_id` para trazabilidad
- Timestamps de auditoría

---

## 7. Paso 6: Carga (L del ETL)

### Pipeline Completo (9 pasos atómicos)

**Archivo:** `backend/src/modules/analytics/infrastructure/etl/pipeline.py`

```
ETLPipeline.run()
│
├── 1. Crear ExtractionRun (status=PENDING → RUNNING)
│
├── 2. Obtener credenciales via ConnectionPort
│      └── Descifra tokens + refresh si necesario
│
├── 3. EXTRACT: provider.extract_metrics() → List[ExtractedMetric]
│
├── 4. STAGE: Bulk insert → staging_metrics
│      └── StagingMetricsRepository.bulk_insert()
│
├── 5. TRANSFORM: Aplicar cost_type + preparar dicts
│      └── transform_staging_to_official()
│
├── 6. UPSERT OFFICIAL: INSERT ... ON CONFLICT DO UPDATE
│      └── OfficialMetricsRepository.upsert_from_staging()
│      └── Clave de conflicto: (tenant_id, provider, channel_slug, metric_name, metric_date)
│
├── 7. AGGREGATE: Computar rollups (daily, weekly, monthly, last_30_days)
│      └── compute_aggregations()
│
├── 8. COMMIT: Todo en una transacción
│      └── ExtractionRun → status=SUCCESS, metrics_count, duration_seconds
│
└── 9. INVALIDAR CACHE: Redis DELETE metrics:{tenant_id}:*
       └── Fuera de la transacción DB (eventual consistency)
```

### Atomicidad

- Los pasos 1-8 ocurren en una **única transacción PostgreSQL**
- Si cualquier paso falla → ROLLBACK completo
- El ExtractionRun se marca como `FAILED` con el mensaje de error
- La invalidación de cache (paso 9) ocurre fuera de la transacción

---

## 8. Paso 7: Agregaciones Pre-computadas

**Tabla:** `metric_aggregations`

Después del upsert en `official_metrics`, el pipeline calcula rollups agrupados por `(channel_slug, metric_name, unit, cost_type)`:

| period_type | Descripción |
|---|---|
| `daily` | Valor del día exacto |
| `weekly` | Suma/promedio de la semana (lun-dom) |
| `monthly` | Suma/promedio del mes calendario |
| `last_30_days` | Rolling window de los últimos 30 días |

Estas agregaciones permiten que las consultas del dashboard sean O(1) en lugar de recalcular rangos en cada request.

---

## 9. Paso 8: Cache (Redis)

**Archivo:** `backend/src/modules/analytics/infrastructure/cache/metrics_cache.py` — clase `MetricsCache`

### Estrategia

| Aspecto | Detalle |
|---|---|
| **Key format** | `metrics:{tenant_id}:{stage}:{period}` |
| **TTL attraction** | 3600s (1 hora) — datos de ads cambian con menos frecuencia |
| **TTL otros stages** | 300s (5 minutos) — CRM-driven, necesitan más frescura |
| **Invalidación** | Después de cada ETL exitoso: `DELETE metrics:{tenant_id}:*` |
| **Fallback** | Si Redis falla → se consulta PostgreSQL directamente (silencioso) |

### Comportamiento en errores de Redis

```python
# MetricsCache nunca lanza excepciones
# Si Redis está caído, retorna None → el servicio va directo a PostgreSQL
try:
    return redis.get(key)
except Exception:
    return None  # silencioso, degradación graceful
```

---

## 10. Paso 9: API — Cómo el Frontend Consume los Datos

**Archivo:** `backend/src/modules/analytics/api/metrics.py`

### Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/metrics/attraction` | Clerk JWT + X-Tenant-ID | Métricas de atracción para el dashboard |
| `GET` | `/etl/status` | X-Tenant-ID | Estado de extracción por proveedor |
| `GET` | `/health/etl` | Ninguna (health check) | Estado global del ETL |

### Flujo de `/metrics/attraction`

**Archivo:** `backend/src/modules/analytics/application/services/metrics_service.py` — `get_attraction_metrics()`

```
GET /metrics/attraction
│
├── 1. Verificar cache Redis
│      └── HIT → retornar inmediatamente
│      └── MISS → continuar
│
├── 2. Obtener canales del ChannelRegistry
│      └── get_available_channels(tenant_id, stage="attraction")
│      └── Retorna: {connected: [...], available: [...]}
│
├── 3. Consultar OfficialMetricsRepository
│      └── get_channel_summary(tenant_id, last_30_days)
│      └── SELECT FROM official_metrics WHERE tenant_id AND channel_slug IN (...)
│
├── 4. Construir ChannelMetricDTO por canal
│      └── {slug, name, channelType, connected, metrics: [...], costType, lastUpdated}
│
├── 5. Agrupar en 4 TrafficGroups
│      ├── organic_social: [ig-organic, fb-organic, tiktok-organic, yt-organic]
│      ├── ga4_search: [google-organic, direct, ai-search-organic]
│      ├── paid: [meta-ads, google-ads, tiktok-ads, yt-ads]
│      └── outbound: [cold-contact]
│
├── 6. Calcular totales por grupo
│      └── Suma de reach, engagement, spend, clicks, etc.
│
├── 7. Cachear resultado en Redis (TTL 1 hora)
│
└── 8. Retornar AttractionDetailDTO
```

### Channel Registry

**Archivo:** `backend/src/modules/analytics/application/services/channel_registry.py`

El registry define estáticamente qué canales existen por stage y qué métricas se esperan de cada uno:

```python
# Canales Meta en stage "attraction"
{"slug": "ig-organic",  "provider_name": "meta", "metric_names": ["reach", "engagement"]}
{"slug": "fb-organic",  "provider_name": "meta", "metric_names": ["reach", "engagement"]}
{"slug": "meta-ads",    "provider_name": "meta", "metric_names": ["reach", "impressions", "clicks", "ctr", "cpm", "frequency", "conversions", "spend"]}
```

El registry cruza esta definición estática con las conexiones activas del tenant para marcar cada canal como `connected: true/false`.

---

## 11. Paso 10: Frontend — Presentación en Growth Studio

### Hook de Datos

**Archivo:** `frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts`

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['attraction-detail', tenantId],
  queryFn: () => metricsApi.getAttractionDetail(token),
  staleTime: 5 * 60 * 1000,  // 5 minutos de cache en frontend
});
```

### Cliente API

**Archivo:** `frontend/src/features/marketing-studio/api/metrics-api.ts`

- Llama `GET /metrics/attraction` con Bearer token (Clerk)
- Mapea snake_case → camelCase (`organic_social` → `organicSocial`)

### Componente de Dashboard

**Archivo:** `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx`

**Estructura visual:**

```
┌──────────────────────────────────────────────────────┐
│  KPIs Principales                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Visitantes│  │  Reach   │  │  Spend   │           │
│  │  Total    │  │  Total   │  │  Total   │           │
│  └──────────┘  └──────────┘  └──────────┘           │
├──────────────────────────────────────────────────────┤
│  Social Orgánico                                      │
│  ┌─────────────────┐  ┌─────────────────┐           │
│  │ Instagram        │  │ Facebook         │           │
│  │ Reach: 5,000     │  │ Reach: 3,000     │           │
│  │ Engagement: 1,200│  │ Engagement: 800  │           │
│  │ ● Conectado      │  │ ● Conectado      │           │
│  └─────────────────┘  └─────────────────┘           │
├──────────────────────────────────────────────────────┤
│  Paid                                                 │
│  ┌─────────────────────────────────────┐             │
│  │ Meta Ads                             │             │
│  │ Reach: 10,000  │ Impressions: 25,000│             │
│  │ Clicks: 500    │ CTR: 1.11%         │             │
│  │ CPM: $2.74     │ Frequency: 4.5     │             │
│  │ Conversions: 12│ Spend: $150.00     │             │
│  │ ● Conectado                          │             │
│  └─────────────────────────────────────┘             │
├──────────────────────────────────────────────────────┤
│  Canales Disponibles (No Conectados)                  │
│  ┌──────────┐  ┌──────────┐                          │
│  │ TikTok   │  │ YouTube  │                          │
│  │ Ads      │  │ Ads      │                          │
│  │ Configurar│  │ Configurar│                         │
│  └──────────┘  └──────────┘                          │
├──────────────────────────────────────────────────────┤
│  Actualizado: 21 mar, 08:00          [↻ Actualizar] │
└──────────────────────────────────────────────────────┘
```

### Estructuras de Datos del Frontend

```typescript
interface AttractionDetail {
  period: string;               // "last_30_days"
  lastUpdated?: string;         // ISO timestamp del último ETL exitoso
  organicSocial: TrafficGroup;
  ga4Search: TrafficGroup;
  paid: TrafficGroup;
  outbound: TrafficGroup;
  available?: { channels: ChannelMetric[] };  // Canales no conectados
}

interface TrafficGroup {
  totals: Record<string, number>;  // {reach: 18000, engagement: 2000, spend: 150}
  channels: ChannelMetric[];
}

interface ChannelMetric {
  slug: string;            // "meta-ads"
  name: string;            // "Meta Ads"
  channelType: string;     // "paid"
  sourceLabel: string;     // "Meta Ads"
  connected: boolean;
  metrics: MetricValue[];
  costType?: string;       // "investment"
  lastUpdated?: string;
  stale: boolean;
  errorMessage?: string;
}

interface MetricValue {
  name: string;            // "reach"
  value: number;           // 10000
  unit: string;            // "count"
  currency?: string;       // "MXN"
  breakdown?: Record<string, number>;  // {likes: 300, comments: 80}
}
```

---

## 12. Catálogo Completo de Métricas Meta

### Instagram Organic (`ig-organic`) — Stage: Attraction

| Métrica | Unit | Fuente API | Notas |
|---|---|---|---|
| `reach` | count | `/{ig_id}/insights?metric=reach&period=day` | Suma de valores diarios en el rango |
| `engagement` | count | `/{ig_id}/media?fields=like_count,comments_count` | likes + comments de últimos 100 posts. Breakdown en `extra` |

### Facebook Organic (`fb-organic`) — Stage: Attraction

| Métrica | Unit | Fuente API | Notas |
|---|---|---|---|
| `reach` | count | `/{page_id}/insights?metric=page_impressions_unique` | Impresiones únicas diarias |
| `engagement` | count | `/{page_id}/insights?metric=page_post_engagements` | Engagements totales de posts |

### Meta Ads (`meta-ads`) — Stage: Attraction

| Métrica | Unit | Fuente API | Notas |
|---|---|---|---|
| `reach` | count | `/act_{id}/insights` campo `reach` | Personas únicas alcanzadas |
| `impressions` | count | `/act_{id}/insights` campo `impressions` | Total de impresiones (incluye repeticiones) |
| `clicks` | count | `/act_{id}/insights` campo `clicks` | Clicks totales |
| `ctr` | percentage | `/act_{id}/insights` campo `ctr` | Click-through rate, calculado por Meta |
| `cpm` | currency | `/act_{id}/insights` campo `cpm` | Costo por mil impresiones |
| `frequency` | ratio | `/act_{id}/insights` campo `frequency` | Promedio de veces que cada persona vio el ad |
| `conversions` | count | `/act_{id}/insights` → `actions[]` | Filtro: `offsite_conversion.fb_pixel_purchase` + `onsite_conversion.purchase` |
| `spend` | currency | `/act_{id}/insights` campo `spend` | Gasto total, currency de la cuenta |

### Meta Retargeting (`meta-retargeting`) — Stage: Nurturing

| Métrica | Unit | Fuente API | Notas |
|---|---|---|---|
| `reach` | count | `/act_{id}/adsets` → insights | Solo adsets con `targeting.custom_audiences` |
| `clicks` | count | `/act_{id}/adsets` → insights | Solo adsets con custom audiences |
| `spend` | currency | `/act_{id}/adsets` → insights | Solo adsets con custom audiences |

---

## 13. Esquema de Base de Datos

**Migración:** `backend/alembic/versions/ab8346fd2c09_add_etl_infrastructure_tables_and_tenant_priority.py`

### Tabla: `staging_metrics` (Landing zone — datos crudos)

```sql
CREATE TABLE IF NOT EXISTS staging_metrics (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,                    -- INDEX
    provider VARCHAR NOT NULL,                  -- INDEX
    channel_slug VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR NOT NULL,
    currency VARCHAR,
    metric_date DATE NOT NULL,                  -- INDEX
    spend JSONB,                                -- Encrypted
    revenue JSONB,                              -- Encrypted
    campaign_id VARCHAR,
    ad_set_id VARCHAR,
    ad_id VARCHAR,
    extra JSONB DEFAULT '{}',
    extraction_run_id UUID REFERENCES extraction_runs(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- INDEX: (tenant_id, provider, metric_date)
```

### Tabla: `official_metrics` (Datos validados para dashboards)

```sql
CREATE TABLE IF NOT EXISTS official_metrics (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,                    -- INDEX
    provider VARCHAR NOT NULL,
    channel_slug VARCHAR NOT NULL,              -- INDEX
    metric_name VARCHAR NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR NOT NULL,
    currency VARCHAR,
    metric_date DATE NOT NULL,                  -- INDEX
    spend JSONB,
    revenue JSONB,
    campaign_id VARCHAR,
    ad_set_id VARCHAR,
    ad_id VARCHAR,
    cost_type VARCHAR,                          -- "neutral", "investment", "expense", "revenue"
    extra JSONB DEFAULT '{}',
    source_extraction_run_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- INDEX: (tenant_id, channel_slug, metric_date)
-- UPSERT KEY: (tenant_id, provider, channel_slug, metric_name, metric_date)
```

### Tabla: `metric_aggregations` (Rollups pre-computados)

```sql
CREATE TABLE IF NOT EXISTS metric_aggregations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    channel_slug VARCHAR NOT NULL,
    metric_name VARCHAR NOT NULL,
    period_type VARCHAR NOT NULL,               -- "daily", "weekly", "monthly", "last_30_days"
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR NOT NULL,
    currency VARCHAR,
    cost_type VARCHAR,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    extraction_run_id UUID
);
```

### Tabla: `extraction_runs` (Trazabilidad del ETL)

```sql
CREATE TABLE IF NOT EXISTS extraction_runs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    provider VARCHAR NOT NULL,
    status VARCHAR NOT NULL,                    -- "pending", "running", "success", "failed", "retrying"
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    metrics_count INTEGER DEFAULT 0,
    rows_extracted INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    rate_limit_headroom FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 14. Manejo de Errores y Reintentos

### Validación de Respuestas HTTP

Cada llamada a Meta API pasa por `_raise_for_meta_error()`:

```python
def _raise_for_meta_error(response, context):
    if response.status_code >= 400:
        logger.error("meta_api_error context=%s status=%s body=%s",
                      context, response.status_code, response.text[:500])
        response.raise_for_status()  # Lanza httpx.HTTPStatusError
```

Esto previene el problema de "métricas silenciosamente en 0" — si Meta devuelve un error (token expirado, rate limit, cuenta suspendida), se lanza una excepción en vez de parsear un JSON vacío.

### Clasificación de Errores

| Tipo de Error | Comportamiento |
|---|---|
| `ConnectionRevokedException` | Fallo permanente, sin reintentos. El token fue revocado por el usuario. |
| Errores transitorios (500, timeout) | Reintento con Fibonacci backoff: 1, 1, 2, 3, 5, 8, 13 minutos |
| Rate limit (429) | Capturado por el catch general → reintento |
| Max 5 reintentos | Después del 5to fallo → status `FAILED` permanente |

### Atomicidad en Fallos

- Si cualquier paso del pipeline falla → ROLLBACK de toda la transacción
- El ExtractionRun se marca como `FAILED` con el mensaje de error completo
- No quedan datos parciales en staging ni en official_metrics

---

## 15. Walkthrough: Día Completo de un Tenant

### Escenario: Usuario conecta Meta a las 9 PM y ve el dashboard al día siguiente

```
═══ DÍA 1 — 9:00 PM (hora del tenant) ═══

[1] Usuario hace clic en "Conectar Meta" en Ecosystem Config
    └── Frontend redirige a Facebook OAuth

[2] Usuario autoriza → callback con auth_code
    └── MetaAdapter.exchange_code() → short-lived token
    └── Extensión a long-lived token (~60 días)

[3] _sync_assets_for_tenant()
    └── Descubre: 1 página FB, 1 cuenta IG, 1 cuenta Ads
    └── Crea 3 registros en channel_connections (credenciales cifradas)

[4] run_initial_load() se encola automáticamente
    └── Extrae últimos 7 días de datos
    └── Pipeline completo: Extract → Stage → Transform → Upsert → Aggregate
    └── 9 métricas insertadas (2 IG + 2 FB + 8 Ads - 3 sin datos = ~9)
    └── Cache invalidado

═══ DÍA 2 — 3:00 AM (hora del tenant) ═══

[5] run_tick_scheduler() detecta que son las 3 AM
    └── Encola run_tenant_extraction(provider="all")

[6] Worker procesa el job
    └── ETLService.run_extraction("meta")
    └── ConnectionPort.get_credentials() → descifra tokens
    └── MetaProvider.extract_metrics(yesterday, yesterday)
    │
    ├── _extract_instagram_organic()
    │   └── GET /{ig_id}/insights → reach=5000
    │   └── GET /{ig_id}/media → likes=300, comments=80
    │   └── → 2 ExtractedMetric
    │
    ├── _extract_facebook_organic()
    │   └── GET /{page_id}/insights?metric=page_impressions_unique → reach=3000
    │   └── GET /{page_id}/insights?metric=page_post_engagements → engagement=800
    │   └── → 2 ExtractedMetric
    │
    └── _extract_meta_ads()
        └── GET /act_{id}/insights → reach=10000, impressions=25000,
        │   clicks=500, ctr=1.11, cpm=2.74, frequency=4.5, spend=150,
        │   actions=[{purchase: 12}]
        └── → 8 ExtractedMetric

    Total: 12 ExtractedMetric

[7] Pipeline ETL
    └── Bulk insert 12 rows → staging_metrics
    └── Transform: cost_type mapping (NEUTRAL para orgánico, INVESTMENT para ads)
    └── Upsert 12 rows → official_metrics (ON CONFLICT actualiza)
    └── Compute aggregations → daily, weekly, monthly, last_30_days
    └── ExtractionRun → status=SUCCESS, metrics_count=12, duration=2.3s
    └── Redis: DELETE metrics:{tenant_id}:*

═══ DÍA 2 — 10:00 AM (hora del tenant) ═══

[8] Usuario abre Growth Studio
    └── Frontend: useQuery(['attraction-detail', tenantId])
    └── GET /metrics/attraction (Bearer token + X-Tenant-ID)

[9] Backend: MetricsService.get_attraction_metrics()
    └── Redis cache → MISS (expiró o fue invalidado)
    └── ChannelRegistry → {connected: [ig-organic, fb-organic, meta-ads], available: [...]}
    └── OfficialMetricsRepository.get_channel_summary()
    └── SELECT FROM official_metrics WHERE tenant_id=X
    │
    └── Resultado:
        ig-organic:  {reach: 5000, engagement: 1200}
        fb-organic:  {reach: 3000, engagement: 800}
        meta-ads:    {reach: 10000, impressions: 25000, clicks: 500,
                      ctr: 1.11, cpm: 2.74, frequency: 4.5,
                      conversions: 12, spend: 150}
    │
    └── Agrupar en TrafficGroups:
        organicSocial: {totals: {reach: 8000, engagement: 2000}, channels: [ig, fb]}
        paid: {totals: {reach: 10000, clicks: 500, spend: 150}, channels: [meta-ads]}
    │
    └── Cache en Redis (TTL 1 hora)
    └── Retornar AttractionDetailDTO

[10] Frontend renderiza:
     ┌────────────────────────────────┐
     │ Total Reach: 18,000            │
     │ Total Spend: $150.00 MXN       │
     ├────────────────────────────────┤
     │ Social Orgánico                │
     │  Instagram: 5k reach, 1.2k eng│
     │  Facebook: 3k reach, 800 eng  │
     ├────────────────────────────────┤
     │ Paid                           │
     │  Meta Ads: 10k reach, 500      │
     │  clicks, $150 spend, 12 conv  │
     ├────────────────────────────────┤
     │ Actualizado: 21 mar, 03:02    │
     └────────────────────────────────┘
```

---

## 16. Mapa de Archivos

### Backend — Extracción

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` | Llamadas a Meta Graph API |
| `backend/src/modules/analytics/infrastructure/providers/base.py` | Interfaz base + ExtractedMetric DTO |
| `backend/src/modules/analytics/infrastructure/providers/registry.py` | Resolución provider_name → clase |

### Backend — ETL Pipeline

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/analytics/infrastructure/etl/pipeline.py` | Orquestación E→T→L atómica |
| `backend/src/modules/analytics/application/services/etl_service.py` | Servicio de aplicación para ETL |
| `backend/src/modules/analytics/application/cost_type_mapping.py` | Clasificación de costos |

### Backend — Scheduling

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/analytics/workers/scheduler.py` | Cron scheduler (3 AM por tenant) |
| `backend/src/modules/analytics/workers/tasks.py` | Jobs ARQ (extracción + initial load) |

### Backend — API

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/analytics/api/metrics.py` | Endpoints REST |
| `backend/src/modules/analytics/application/services/metrics_service.py` | Lógica de consulta + agrupación |
| `backend/src/modules/analytics/application/services/channel_registry.py` | Definición de canales por stage |

### Backend — Conexiones

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/connections/infrastructure/channels/meta.py` | OAuth + asset discovery |
| `backend/src/modules/connections/application/services/connection_port_impl.py` | Puente de credenciales |
| `backend/src/modules/connections/infrastructure/models/channel_connection_model.py` | Modelo de persistencia |

### Backend — Cache

| Archivo | Responsabilidad |
|---|---|
| `backend/src/modules/analytics/infrastructure/cache/metrics_cache.py` | Cache Redis con fallback silencioso |

### Frontend

| Archivo | Responsabilidad |
|---|---|
| `frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts` | React Query hook |
| `frontend/src/features/marketing-studio/api/metrics-api.ts` | Cliente HTTP |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx` | Componente visual |

### Database

| Archivo | Responsabilidad |
|---|---|
| `backend/alembic/versions/ab8346fd2c09_add_etl_infrastructure_tables_and_tenant_priority.py` | Migración de tablas ETL |

---

## 17. Carga Inicial Incremental — Botón "Cargar datos Meta"

### Problema

Cuando un usuario conecta Meta vía OAuth, no ve métricas hasta la ejecución del cron a las 3 AM. Además, el `extract_metrics()` original agrega todo el rango en una sola fila (`date=end_date`), impidiendo gap detection per-day.

### Solución: `extract_metrics_daily()` + `run_initial_load()`

#### Extracción diaria (`MetaProvider.extract_metrics_daily()`)

Nuevos métodos `_daily` que retornan un `ExtractedMetric` por día:

| Canal | Estrategia | API Calls |
|---|---|---|
| IG Organic | Parsea `values[]` del endpoint `insights?period=day` — cada entry tiene `end_time` | 1 call (array) |
| FB Organic | Misma estrategia: parsea `values[]` per-day | 2 calls (reach + engagement) |
| Meta Ads | Agrega `time_increment=1` al request → Meta retorna un row por día | 1 call (array) |
| Meta Retargeting | Itera día por día llamando al método original con `start=day, end=day` | N calls (1 per day) |

**Total worst case 30 días:** ~36 API calls. Muy dentro del rate limit de 200/min.

#### Gap detection (`ETLService.run_initial_load()`)

```
1. end_date = yesterday, start_date = today - days
2. existing = official_repo.get_existing_dates(tenant_id, provider, start, end)
3. missing_days = all_days - existing
4. Si missing_days vacío → return {loaded: 0, skipped: N}
5. Llamar extract_metrics_daily(min_missing, max_missing)
6. Filtrar resultados: solo métricas cuyo date ∈ missing_days
7. Pipeline normal: staging → transform → upsert → aggregate
```

**Idempotencia:** Garantizada por doble mecanismo:
1. Gap detection evita re-extraer días existentes
2. ON CONFLICT upsert key `(tenant_id, provider, channel_slug, metric_name, metric_date)` como safety net

#### Comportamiento al incrementar `days`

```
Click 1: days=7  → carga 7 días
Click 2: days=7  → loaded=0, skipped=7 (idempotente)
Click 3: days=14 → loaded=7, skipped=7 (solo días nuevos)
```

### Endpoint API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/metrics/meta/initial-load?days=30` | Ejecuta carga inicial (sync, 2-5s). Cooldown 15 min. |
| `GET` | `/metrics/meta/initial-load/status` | Lee progreso desde Redis (para futuro polling si se migra a async). |

### Frontend

**Botón:** En la sidebar de AttractionDetail, antes de "Gestionar Atracción":
- Estado idle: "Cargar datos Meta" con ícono Download
- Estado loading: "Cargando datos Meta..." con spinner
- Estado completado: "Datos Meta cargados" con CheckCircle + resumen "X días cargados, Y ya existían"
- Estado error: mensaje del backend en rojo

**Hook:** `useMetaInitialLoad()` — mutation que llama al endpoint POST e invalida `attraction-detail` queries on success.
