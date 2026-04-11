# CONTRACT — Meta Ads Resumen · Unified Offer Filter

**Spec:** `docs/superpowers/specs/2026-04-10-meta-ads-resumen-offer-filter-design.md`
**Plan:** `docs/superpowers/plans/2026-04-10-meta-ads-resumen-offer-filter.md`
**Status:** Fase 1 — architect output. Source of truth para `nicolify-backend` y `nicolify-frontend` en Fase 2.

---

## 1. Verification findings

### 1a) `get_tenant_locale` FastAPI dependency

**EXISTE.** No hay que crear nada — reutilizar lo existente.

- **Archivo:** `backend/src/modules/iam/api/dependencies.py`
- **Definición:** `def get_tenant_locale(db, user) -> TenantLocale` en `:410-419`
- **Helper subyacente:** `_resolve_tenant_locale(db, tenant_id)` en `:395-407`
- **Carga desde:** `TenantModel.default_currency`, `TenantModel.timezone`
- **Fallback:** `TenantLocale(currency="USD", timezone="UTC")` vía `TenantLocale.default()`
- **Tipo de retorno:** `src.shared.domain.locale.TenantLocale` (`@dataclass(frozen=True)`, campos `currency: str`, `timezone: str`)

**Uso actual en `advertising/`:** ninguno. Grep de `TenantLocale` en `backend/src/modules/advertising/` devuelve **0 archivos**. Este feature es el primero que lo inyecta en la ruta `/advertising/metrics-by-offer`.

**Implicación para el backend agent:** no diseñar un nuevo helper. Importar directamente:

```python
from src.modules.iam.api.dependencies import get_tenant_locale
from src.shared.domain.locale import TenantLocale
```

> **Why:** la rule `master-data.md` exige DI, y ya hay una dependency canónica. Crear una paralela romperia el "single source of truth" y obligaria a sincronizar dos puntos en cada cambio de `TenantModel`.

### 1b) `period_metrics` reach availability para `meta-ads`

**Conclusión crítica:** HOY el ETL escribe `reach` para `channel_slug='meta-ads'` **solo a nivel ad-account (campaign_id IS NULL)**. No hay filas con `campaign_id` populado para reach.

**Evidencia:**

- `backend/src/modules/analytics/infrastructure/models/period_metrics_model.py` confirma que las columnas `campaign_id`, `ad_set_id`, `ad_id` existen y son nullables → el modelo soporta per-campaign, pero el ETL no lo aprovecha.
- `backend/src/modules/analytics/infrastructure/providers/meta_provider.py:276-321` (`_extract_meta_ads_period`) hace una sola llamada a `act_{ad_account_id}/insights` con `fields=reach,impressions,frequency` y **sin** `level=campaign`. Construye `ExtractedMetric(provider="meta", channel_slug="meta-ads", metric_name="reach", ...)` **sin setear** `campaign_id`, `ad_set_id` ni `ad_id`.
- `backend/src/modules/analytics/infrastructure/etl/period_pipeline.py:129` pasa `m.campaign_id` al dict upsert, pero como el extractor nunca lo setea, llega como `None`.
- `PeriodMetricsRepository._UPSERT_SQL` usa conflict key con `COALESCE(campaign_id, '')`, lo cual permite filas channel-level sin problemas.

**Consecuencia concreta para este feature:**

| Filtro | Reach disponible |
|---|---|
| **Todas** (`reach_all`) | ✅ Sí — lee la fila channel-level (`campaign_id IS NULL`). |
| **Offer con 1 campaña** | ❌ No hoy — mostrar `—`. Solo funcionará cuando el ETL migre a `level=campaign`. |
| **Offer con ≥2 campañas** | ❌ No (por overlap) — mostrar `—`. |
| **Branding** (típicamente multi-campaign) | ❌ No — mostrar `—`. |
| **Unassigned** | ❌ No — mostrar `—`. |

> **Why no expandir el ETL en este scope:** spec line 372 ("**Riesgo a verificar en Fase 1**") aceptaba que el ETL quede como está y solo cambia *cuántos casos muestran `—`*, no *si la feature bloquea*. El fix del ETL (`level=campaign` en la extracción de period_metrics para meta-ads) es trabajo independiente y va fuera de scope. Se documenta como riesgo abierto (Sección 8).

**Regla del servicio (consistente con el spec):**

1. Para `reach_all`, usar `PeriodMetricsRepository.get_best_period_metric(..., metric_name="reach", ...)` → retorna la fila channel-level.
2. Para `offers[].funnel` / `branding.funnel` / `unassigned.funnel`: el campo `reach` de los `secondary_metrics` ya NO vive ahí — se mueve al nivel del DTO (`offer.reach`, `branding.reach`, `unassigned.reach`) y pasa a ser `float | None`. Lógica de null:
   - Si `len(campaign_ids) == 0` → `reach = None`.
   - Si `len(campaign_ids) == 1` → query a `period_metrics` filtrado por ese `campaign_id`; si no hay fila, `reach = None`.
   - Si `len(campaign_ids) >= 2` → `reach = None` siempre (no sumar, no inventar).
3. El campo `reach` histórico dentro de `secondary_metrics` (que sumaba filas diarias de `official_metrics`) **se elimina**. Su valor era sistemáticamente incorrecto.

### 1c) Funnel source today

**Referencia:** `backend/src/modules/analytics/application/services/channel_dashboard_service.py:619-646` (`_build_funnel`).

**Algoritmo actual del funnel global (channel-level):**

1. Recibe `metrics: dict[str, float]` (pre-agregado channel-level) y un `ChannelDashboardConfig` con `funnel_steps: list[tuple[label, metric_name]]`.
2. Para Meta Ads, el fallback config viene de `_CHANNEL_CONFIGS["meta-ads"]`.
3. Itera los steps en orden y para cada uno:
   - `value = metrics.get(metric_name, 0.0)`
   - `conversion_rate_from_previous = round(value / prev_value * 100, 2)` si `prev_value > 0`, sino `None`
4. Retorna `AdFunnelDTO(steps=list[FunnelStepDTO])`.

**Consistencia requerida:** el nuevo `_build_funnel_for_campaigns` debe producir `FunnelStepDTO`s con **exactamente** la misma semántica: misma definición de rate, misma regla de null en el primer paso, mismos `metric_name` canónicos. Los 5 pasos para meta-ads son:

| # | Label | `metric_name` |
|---|---|---|
| 1 | Impresiones | `impressions` |
| 2 | Clics | `clicks` |
| 3 | Visitas a Landing | `meta_landing_page_views` |
| 4 | Leads | `meta_leads` |
| 5 | Compras | `conversions` |

> **Why nuevos DTOs y no importar los de analytics:** cross-module import prohibido (`.claude/rules/backend-ddd.md`). `advertising` ya importa `OfficialMetricModel` de analytics/infra — esa es la única excepción tolerada. Definir `FunnelStepDTO` propio del módulo y construirlo dentro del servicio respeta el límite DDD. La forma es idéntica al DTO de analytics, los consumidores frontend ven el mismo shape, pero no hay acoplamiento de código.

---

## 2. DTOs — Pydantic v2 code (exacto)

**Ubicación:** `backend/src/modules/advertising/application/dto/metrics_by_offer_dto.py`

Reemplazar el contenido actual por el siguiente (manteniendo el `_CamelModel` base que ya existe):

```python
"""DTOs for metrics grouped by offer."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )


# ── Shared ────────────────────────────────────────────────────────────────


class FunnelStepDTO(_CamelModel):
    """One step of the Meta Ads conversion funnel.

    Mirrors the shape of `analytics.AdFunnelDTO.steps[i]` but lives in
    advertising to respect DDD boundaries. `conversion_rate_from_previous`
    is a percentage (0-100), or null for the first step / when previous=0.
    """

    label: str
    metric_name: str
    value: float
    conversion_rate_from_previous: float | None = None


# ── Per-offer ──────────────────────────────────────────────────────────────


class OfferTimeSeriesPointDTO(_CamelModel):
    date: str
    spend: float
    primary_result: float


class OfferMetricsDTO(_CamelModel):
    offer_id: UUID
    offer_name: str
    archetype: str
    expected_metric: str
    expected_metric_label_es: str
    total_spend: float
    currency: str
    primary_result_count: float
    primary_cost_per_result: float | None = None
    primary_metric_name: str
    primary_metric_unit: str  # "currency" | "count"
    roas: float | None = None

    # Secondary metrics — flattened out of the old dict so each field is
    # individually typed and nullable when semantically unreliable.
    impressions: float
    clicks: float
    ctr: float           # percentage 0-100
    cpm: float           # in `currency`
    cpc: float           # in `currency`
    reach: float | None = None          # null unless unambiguous (1 campaign + period_metrics row)
    frequency: float | None = None      # null unless reach is not null

    # New: funnel filtered to the offer's associated campaigns.
    funnel: list[FunnelStepDTO]

    timeseries: list[OfferTimeSeriesPointDTO]
    metric_unavailable_reason: str | None = None


# ── Branding aggregate ────────────────────────────────────────────────────


class BrandingAggregateDTO(_CamelModel):
    target_count: int
    total_spend: float
    impressions: float
    clicks: float
    ctr: float
    cpm: float
    cpc: float
    reach: float | None = None          # null in multi-campaign case
    frequency: float | None = None      # null when reach is null
    funnel: list[FunnelStepDTO]


# ── Unassigned aggregate ──────────────────────────────────────────────────


class UnassignedAggregateDTO(_CamelModel):
    target_count: int
    total_spend: float
    impressions: float
    clicks: float
    ctr: float
    cpm: float
    cpc: float
    reach: float | None = None          # null when multi-campaign
    funnel: list[FunnelStepDTO]


# ── Root response ─────────────────────────────────────────────────────────


class MetricsByOfferDTO(_CamelModel):
    period: str
    start_date: date
    end_date: date
    currency: str | None = None
    offers: list[OfferMetricsDTO]
    unassigned: UnassignedAggregateDTO
    branding_only: BrandingAggregateDTO

    # New: "Todas" context — used when the segmenter selection is `all`.
    funnel_all: list[FunnelStepDTO]
    reach_all: float | None = None
```

**Nota sobre `secondary_metrics`:** el campo `secondary_metrics: dict[str, float]` del DTO actual se **elimina** y se reemplaza por campos individuales tipados. Es un **breaking change** del DTO. Frontend debe migrar todos los lectores (sección 3).

> **Why romper el dict:** (a) elimina el `Any`-adjacente que hace difícil de tipar en frontend; (b) permite que `reach`/`frequency` sean correctamente nullable; (c) se alinea con `.claude/rules/standards.md` ("sin dicts magicos"). El costo es re-wirear los componentes de frontend que leían `offer.secondaryMetrics.ctr` — ya identificados en Fase 2B.

---

## 3. TypeScript types (frontend mirror)

**Ubicación:** `frontend/src/features/growth-studio/types/offer-association.ts`

Cambios (delta sobre el archivo existente):

```typescript
// ---------------------------------------------------------------------------
// Funnel (shared)
// ---------------------------------------------------------------------------

export interface FunnelStep {
  label: string;
  metricName: string;
  value: number;
  conversionRateFromPrevious: number | null;
}

// ---------------------------------------------------------------------------
// Metrics by Offer — UPDATED (breaking change vs previous version)
// ---------------------------------------------------------------------------

export interface OfferTimeSeriesPoint {
  date: string;
  spend: number;
  primaryResult: number;
}

export interface OfferMetrics {
  offerId: string;
  offerName: string;
  archetype: string;
  expectedMetric: ExpectedMetric;
  expectedMetricLabelEs: string;
  totalSpend: number;
  currency: string;
  primaryResultCount: number;
  primaryCostPerResult: number | null;
  primaryMetricName: string;
  primaryMetricUnit: 'currency' | 'count' | 'ratio';
  roas: number | null;

  // Individual typed secondary metrics (was `secondaryMetrics: Record<string, number>`)
  impressions: number;
  clicks: number;
  ctr: number;            // percentage 0-100
  cpm: number;
  cpc: number;
  reach: number | null;
  frequency: number | null;

  funnel: FunnelStep[];
  timeseries: OfferTimeSeriesPoint[];
  metricUnavailableReason: string | null;
}

export interface UnassignedAggregate {
  targetCount: number;
  totalSpend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpm: number;
  cpc: number;
  reach: number | null;
  funnel: FunnelStep[];
}

export interface BrandingAggregate {
  targetCount: number;
  totalSpend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpm: number;
  cpc: number;
  reach: number | null;
  frequency: number | null;
  funnel: FunnelStep[];
}

export interface MetricsByOffer {
  period: string;
  startDate: string;
  endDate: string;
  currency: string | null;
  offers: OfferMetrics[];
  unassigned: UnassignedAggregate;
  brandingOnly: BrandingAggregate;

  // NEW: aggregate context for the "Todas" segmenter state
  funnelAll: FunnelStep[];
  reachAll: number | null;
}
```

**Migración consumers actuales:**

Grep `secondaryMetrics` en `frontend/src/features/growth-studio/` antes de tocar nada. Cada lectura `offer.secondaryMetrics.X` → `offer.X`. El hook nuevo `useResumenViewData` puede encapsular la mayoría.

---

## 4. Service method signatures

**Archivo:** `backend/src/modules/advertising/application/services/metrics_by_offer_service.py`

```python
class MetricsByOfferService:
    def __init__(
        self,
        db: Session,
        offer_read_port: OfferReadPort,
    ) -> None: ...

    async def run(
        self,
        tenant_id: UUID,
        period: str = "30d",
        tenant_locale: TenantLocale | None = None,
    ) -> MetricsByOfferDTO:
        """Compose the full metrics-by-offer response.

        If `tenant_locale` is None, falls back to TenantLocale.default().
        The locale drives timezone-aware period window resolution.
        """
        ...

    # ── New helpers ──

    def _build_funnel_for_campaigns(
        self,
        rows: list[MetricRow],
        campaign_ids: set[str],
        ad_set_ids: set[str] | None = None,
    ) -> list[FunnelStepDTO]:
        """Build a 5-step funnel from official_metrics rows filtered to
        the given campaigns/ad_sets. When both sets are empty, builds a
        global funnel (all rows). Steps are the canonical Meta Ads funnel:
        impressions → clicks → meta_landing_page_views → meta_leads → conversions.
        """
        ...

    def _compute_reach_for_campaigns(
        self,
        period_reach_rows: list[PeriodMetricModel],
        campaign_ids: set[str],
    ) -> float | None:
        """Return a reliable reach value for the given campaigns.

        Rules:
          - len(campaign_ids) == 0 → None
          - len(campaign_ids) == 1 → value from the matching period_metrics row,
            or None if no row for that campaign_id exists
          - len(campaign_ids) >= 2 → None (audience overlap makes sum invalid)
        """
        ...

    def _compute_reach_all(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
    ) -> float | None:
        """Reach at channel level (campaign_id IS NULL) — used for the
        'Todas' segmenter state and for the `reachAll` field."""
        ...
```

**Archivo:** `backend/src/modules/advertising/infrastructure/repositories/metrics_repository.py`

```python
def resolve_period_window(
    period: str,
    tz: str = "UTC",
) -> tuple[date, date]:
    """Translate a '7d'|'30d'|'90d' period to a (start, end) tuple in the
    tenant's timezone. Falls back to UTC when `tz` is invalid.

    Uses zoneinfo.ZoneInfo + datetime.now(tz).date() to get "today"
    in the tenant's local time — critical for tenants far from UTC
    (e.g., America/Lima is UTC-5) where date.today() would be off-by-one
    near midnight.
    """
    ...
```

> **Why default `tz="UTC"`:** permite llamar a la función sin locale (mantiene compatibilidad con callers legacy como scripts / tests unitarios que no tienen un tenant). El caller que sí tiene locale (el servicio) pasa explicitamente `tenant_locale.timezone`.

---

## 5. SQL queries (SQLAlchemy 2.0)

El servicio necesita cargar filas de `period_metrics` filtradas por tenant, channel_slug, metric_name y período. Usa el repo existente `PeriodMetricsRepository.get_period_metrics(...)` que ya implementa el SELECT con todos esos filtros. No hace falta SQL nuevo para el caso channel-level.

### 5a) Reach rows para el período (channel-level + campaign-level, en un solo query)

**Caller:** `MetricsByOfferService.run()` — una sola vez por request, carga TODAS las filas de reach para el período y luego se distribuyen in-memory a cada offer.

```python
# Inside MetricsByOfferService.run()
from src.modules.analytics.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)
from sqlalchemy import select

period_reach_stmt = (
    select(PeriodMetricModel)
    .where(
        PeriodMetricModel.tenant_id == tenant_id,
        PeriodMetricModel.channel_slug == "meta-ads",
        PeriodMetricModel.metric_name == "reach",
        # Match any period that starts on/after and ends on/before the window.
        # A tighter match is enforced in-memory when selecting the "best" row.
        PeriodMetricModel.period_start >= start_date,
        PeriodMetricModel.period_end <= end_date,
    )
    .order_by(PeriodMetricModel.period_start.desc())
)
period_reach_rows: list[PeriodMetricModel] = list(
    self._db.execute(period_reach_stmt).scalars().all()
)
```

**Predicate summary:**

| Column | Predicate |
|---|---|
| `tenant_id` | `= tenant_id` (required — tenant isolation) |
| `channel_slug` | `= "meta-ads"` |
| `metric_name` | `= "reach"` |
| `period_start` | `>= start_date` |
| `period_end` | `<= end_date` |

After loading, partition in Python:
- `reach_channel = [r for r in rows if r.campaign_id is None]` → pick first → `reach_all`
- `reach_by_campaign = {r.campaign_id: r.value for r in rows if r.campaign_id}` → used by `_compute_reach_for_campaigns`

> **Why cargar todo en un query y particionar en Python:** un solo roundtrip al DB. El volumen es trivial — como mucho decenas de filas por tenant/período. Evita N queries (una por offer).

### 5b) Frequency reach channel-level fallback (opcional, mismo viaje)

El servicio NO carga `metric_name="frequency"` de `period_metrics`. Se recompute en Python como `impressions / reach` cuando ambos son confiables, porque el `reach` que manda es el que ya vino del query anterior. Esto mantiene consistencia semántica: la frequency del payload siempre cuadra con el reach del payload.

---

## 6. DI wiring diff

**Archivo:** `backend/src/modules/advertising/api/routes.py`

**Import adicional (añadir junto a `get_current_user`):**

```python
from src.modules.iam.api.dependencies import get_current_user, get_tenant_locale
from src.shared.domain.locale import TenantLocale
```

**Endpoint diff:**

```python
@router.get("/metrics-by-offer", response_model=MetricsByOfferDTO)
async def get_metrics_by_offer(
    period: str = Query(default="30d"),
    user: User = Depends(get_current_user),
    tenant_locale: TenantLocale = Depends(get_tenant_locale),   # NEW
    db: Session = Depends(get_db),
) -> MetricsByOfferDTO:
    """Return Meta ads metrics aggregated per offer."""
    if period not in {"7d", "30d", "90d"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid period — must be one of 7d, 30d, 90d",
        )
    tenant = _tenant_id(user)
    port = _get_offer_port(db)
    svc = MetricsByOfferService(db, port)
    return await svc.run(tenant, period=period, tenant_locale=tenant_locale)   # UPDATED
```

> **Why `Depends(get_tenant_locale)` y no resolverlo dentro del servicio:** mantiene el servicio agnóstico de FastAPI (capa application debe seguir framework-free). Resolver el locale en la capa `api/` es idéntico al patrón ya usado en `analytics/api/metrics.py` según `master-data.md`.

---

## 7. Decisions + Why

1. **Reach se mueve de `secondary_metrics` dict a campo tipado nullable en el DTO.**
   *Why:* el bug raíz es que `reach` nunca debió ser aditivo; exponerlo como `float | None` obliga al frontend a manejar el caso "no disponible" explícitamente. El dict `Record<string, number>` hacía que null no existiera como estado.

2. **`secondary_metrics: dict` se elimina en favor de campos individuales.**
   *Why:* tipado explícito end-to-end (regla `standards.md` — "no Any ni dicts mágicos"), refactor único, frontend más simple. Es un breaking change pero ambos extremos se deployan juntos.

3. **`FunnelStepDTO` se define localmente en `advertising` aunque `analytics` tiene uno casi idéntico.**
   *Why:* cross-module imports de `analytics.api.dto` a `advertising` están prohibidos por `.claude/rules/backend-ddd.md`. La única excepción existente es `OfficialMetricModel`. El costo de duplicar este DTO (15 líneas) es bajísimo comparado con el costo arquitectural de acoplar las APIs de dos módulos.

4. **`resolve_period_window(period, tz="UTC")` con default UTC en vez de hacer `tz` obligatorio.**
   *Why:* compat con callers legacy (si los hay) y con tests que no siempre inyectan locale. Cuando el servicio llama, pasa explícitamente `tenant_locale.timezone`, así en el flujo real siempre se respeta el timezone del tenant.

5. **Reach se calcula en un solo SELECT sobre `period_metrics` y se particiona en memoria.**
   *Why:* una request = un roundtrip. Volumen pequeño. Evita N+1 por offer.

6. **Para offers con multiples campaigns, `reach = None` siempre (no se suma, no se "aproxima").**
   *Why:* línea directa del spec ("atributo no negociable: confiabilidad de datos"). Reach de dos audiencias solapables no es aditiva. Mostrar `—` con tooltip es la única respuesta honesta.

7. **El endpoint `/metrics-by-offer` es la única fuente del funnel para el Resumen — no se consume `/channel-dashboard/meta-ads` para el funnel.**
   *Why:* evita inconsistencias de timezone y semántica entre ambos endpoints, permite que "Todas" y "[Offer X]" se construyan con idéntica lógica, y reduce el frontend a un solo fetch para todo el Resumen.

8. **Frequency se recompute en Python (`impressions / reach`) y es nullable cuando reach es nullable.**
   *Why:* garantiza que los dos campos siempre cuadren en el mismo payload; evita una segunda query de frequency a period_metrics.

---

## 8. Open risks (verificación en runtime / trabajo futuro)

1. **ETL period_metrics no genera reach a campaign-level para meta-ads.** Hoy todos los offers mostrarán `reach = —` excepto el global "Todas". Cuando el ETL se actualice para agregar `level=campaign` al insights call y setear `m.campaign_id`, los offers de 1 campaña automáticamente empezarán a mostrar reach real — sin cambios al contrato. **Fuera de scope de este feature** pero documentar en `docs/mejoras-proceso/to-do.md`.

2. **`meta_landing_page_views` en official_metrics** — asumido disponible por `channel_dashboard_service._build_funnel` que lo usa en el funnel global. Backend agent debe verificar en los tests que las filas existen para los tenants de test; si faltan, el paso 3 del funnel aparecerá en cero (no es un bug del feature — es ausencia de evento en el source).

3. **Compatibilidad de locale inválido:** `ZoneInfo("foo")` lanza `ZoneInfoNotFoundError`. `resolve_period_window` debe atrapar la excepción genéricamente y caer a UTC sin warning ruidoso (usa `structlog.warn` una vez, no por cada request).

4. **Frontend consumers de `offer.secondaryMetrics.X`.** Antes de implementar, el frontend agent debe correr:
   ```
   cd frontend && grep -rn 'secondaryMetrics' src/features/growth-studio/
   ```
   Cada lectura necesita migración. No hay vía de compatibilidad — el campo no existe más en el response.

5. **`metric_unavailable_reason` vs null en funnel steps.** Si el pixel está off y `conversions=0`, el funnel step "Compras" tendrá `value=0` (no null) y `conversion_rate_from_previous=0.0`. La UI debe detectar el estado "pixel off" vía `metric_unavailable_reason` y NO via el funnel (son dos señales independientes).

6. **`get_best_period_metric` vs la query custom propuesta:** el repo ya expone `get_best_period_metric(tenant_id, channel_slug, metric_name, start_date, end_date)` que retorna un solo float (el "mejor" row que cubre el período). Para `reach_all` es suficiente. Pero para `_compute_reach_for_campaigns` NECESITAMOS las filas crudas con `campaign_id` — por eso el query de la sección 5 usa `select(PeriodMetricModel)` directamente. Es intencional; no reutilizar `get_best_period_metric` en ese caso.

7. **Worker / async concerns:** el servicio usa `Session` síncrono (`sqlalchemy.orm.Session`), no `AsyncSession`. El método `run()` sigue siendo `async` solo porque consume `offer_read_port.get_offers_by_tenant()` que es async. Las nuevas queries sobre `PeriodMetricModel` usan `self._db.execute(...)` sync. **No migrar a AsyncSession en este feature** — es un refactor mayor y fuera de scope.

---

**End of CONTRACT.**
