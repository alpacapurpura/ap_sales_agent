# CONTRACT — Offer ↔ Campaign Association + Health Check + Multi-offer Chart

**Fecha:** 2026-04-10
**Módulo backend:** `advertising` (nuevo, hoy vacío)
**Feature slug frontend:** `meta-ads` (dentro de growth-studio)
**Objetivo:** permitir asociar campañas Meta (y ad sets) con offers del Offer Studio, mostrar diagnóstico de salud, agrupar métricas del Meta Ads Resumen por offer con el modo natural de cada una, y dejar las bases del futuro Action Trigger de creación de campañas.

---

## 1. Modelo de datos

### 1.1 Nueva tabla `ad_offer_associations`

Vive en `advertising/infrastructure/models/ad_offer_association_model.py`.

```python
class AdOfferAssociationModel(Base):
    __tablename__ = "ad_offer_associations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    provider = Column(String(50), nullable=False, default="meta")

    # 'campaign' or 'ad_set' — soporta CBO (Escuela B del análisis)
    target_type = Column(String(20), nullable=False)

    # external_id del ad_campaigns.external_id o ad_sets.external_id
    target_external_id = Column(String(255), nullable=False)

    # FK lógica a products.id; NULL cuando la asociación es "excluded"
    offer_id = Column(UUID(as_uuid=True), nullable=True)

    # 'manual', 'auto_landing_url', 'auto_keyword', 'auto_objective',
    # 'excluded_branding' (campaña de alcance/branding sin offer),
    # 'suggested' (auto-detectada pero pending confirm)
    association_type = Column(String(50), nullable=False)

    # 'high', 'medium', 'low' para auto-detección; NULL para manual/excluded
    confidence = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_ad_offer_tenant_target",
            "tenant_id", "target_type", "target_external_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_ad_offer_tenant_offer", "tenant_id", "offer_id"),
    )
```

**Reglas:**
- Una misma (tenant, target_type, target_external_id) solo puede tener **UNA** asociación activa (deleted_at IS NULL). Nuevas asociaciones sobre el mismo target hacen soft-delete de la anterior.
- `offer_id NULL` solo permitido cuando `association_type IN ('excluded_branding')`.
- `offer_id NOT NULL` requerido para los demás association_type.
- Soft delete only.

### 1.2 Nueva tabla `ad_campaign_templates` (BASES del Action Trigger futuro)

Vive en `advertising/infrastructure/models/ad_campaign_template_model.py`.

Esta tabla es **solo lectura** por ahora. Guarda templates sugeridos de cómo configurar una campaña Meta según el `archetype` + `onboarding_action` de una offer. Un servicio futuro (no parte de este task) leerá estos templates para crear campañas directamente via Meta Marketing API.

```python
class AdCampaignTemplateModel(Base):
    __tablename__ = "ad_campaign_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Match criteria
    offer_archetype = Column(String(50), nullable=False)  # PRODUCTO / PROGRAMA / SERVICIO / etc.
    offer_onboarding_action = Column(String(50), nullable=True)  # nullable = catchall
    offer_is_lead_magnet = Column(Boolean, nullable=True)  # nullable = either

    # Template payload
    name = Column(String(255), nullable=False)
    description = Column(Text)
    recommended_objective = Column(String(50), nullable=False)  # OUTCOME_SALES etc.
    recommended_optimization_goal = Column(String(100))
    recommended_destination_type = Column(String(100))
    structure_hints = Column(JSONB, server_default="{}")  # ad sets recommendations, creative tips
    priority = Column(Integer, default=0)  # higher = better match

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Seed inicial** (se aplica en la misma migración con INSERT idempotente):

| archetype | onboarding_action | is_lead_magnet | recommended_objective | description |
|---|---|---|---|---|
| PRODUCTO | — | true | OUTCOME_LEADS | "Lead magnet: captá emails con formulario o página de descarga" |
| PRODUCTO | — | false | OUTCOME_SALES | "Producto digital con checkout web: optimizá para compras directas" |
| PROGRAMA | — | false | OUTCOME_SALES | "Curso/cohort: checkout directo o VSL con CTA de compra" |
| SERVICIO | BOOK_KICKOFF_CALL | false | OUTCOME_MESSAGES | "Servicio 1:1: usá WhatsApp/Messenger para calificar y agendar" |
| SERVICIO | FILL_INTAKE_FORM | false | OUTCOME_LEADS | "Servicio con formulario: Lead Forms de Meta" |
| MEMBRESIA | JOIN_COMMUNITY | false | OUTCOME_SALES | "Membresía: optimizá para suscripción vía checkout" |
| MEMBRESIA | INSTANT_ACCESS_EMAIL | false | OUTCOME_LEADS | "Comunidad gratuita: lead capture" |
| EXPERIENCIA | — | false | OUTCOME_SALES | "Evento/retreat: compra de boleto o reserva" |

---

## 2. Dominio

`advertising/domain/enums.py`:

```python
class AssociationTargetType(str, Enum):
    CAMPAIGN = "campaign"
    AD_SET = "ad_set"

class AssociationType(str, Enum):
    MANUAL = "manual"
    AUTO_LANDING_URL = "auto_landing_url"
    AUTO_KEYWORD = "auto_keyword"
    AUTO_OBJECTIVE = "auto_objective"
    EXCLUDED_BRANDING = "excluded_branding"
    SUGGESTED = "suggested"  # auto-detected but pending user confirmation

class AssociationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Expected primary metric per offer, derived from archetype + onboarding_action
class OfferExpectedMetric(str, Enum):
    LEAD = "lead"                # cost per lead
    MESSAGE = "message"          # cost per conversation_started
    PURCHASE = "purchase"        # ROAS
    SUBSCRIPTION = "subscription"  # cost per subscriber
    CALL_BOOKED = "call_booked"  # cost per scheduled call
    FORM_SUBMIT = "form_submit"  # cost per form completion

# Map offer (archetype + onboarding_action + is_lead_magnet) -> expected metric
def resolve_expected_metric(
    archetype: str,
    onboarding_action: str | None,
    is_lead_magnet: bool,
    has_checkout_url: bool,
) -> OfferExpectedMetric:
    if is_lead_magnet:
        return OfferExpectedMetric.LEAD
    if onboarding_action == "BOOK_KICKOFF_CALL":
        return OfferExpectedMetric.CALL_BOOKED
    if onboarding_action == "FILL_INTAKE_FORM":
        return OfferExpectedMetric.FORM_SUBMIT
    if onboarding_action == "JOIN_COMMUNITY" and not has_checkout_url:
        return OfferExpectedMetric.LEAD
    if has_checkout_url:
        if archetype == "MEMBRESIA":
            return OfferExpectedMetric.SUBSCRIPTION
        return OfferExpectedMetric.PURCHASE
    # default fallback for services/programs without explicit onboarding
    if archetype == "SERVICIO":
        return OfferExpectedMetric.MESSAGE
    return OfferExpectedMetric.LEAD
```

`advertising/domain/ad_offer_association.py` — Pydantic domain entity.

---

## 3. Application services

### 3.1 `OfferDetectionService`

`advertising/application/services/offer_detection_service.py`.

Entrada: `tenant_id`.
Salida: `list[AssociationSuggestionDTO]`.

Estrategias (en orden de prioridad):

1. **Landing URL match** (confidence HIGH)
   - Para cada ad set activo del tenant, obtener ads children desde `ads` table
   - Normalizar `ads.creative_link_url` (lowercase, strip protocol, strip trailing slash, strip query params except the identifier path)
   - Normalizar `offer.landing_page_config.url` y `offer.checkout_page_url` de todas las offers activas
   - Match = URL normalizada del ad contiene el path principal de la offer URL, o viceversa
   - Si hay match → sugerir asociación al nivel ad_set con confidence HIGH

2. **Keyword match en nombre** (confidence MEDIUM)
   - Normalizar nombres: lowercase, strip punctuation, remover stopwords ES (de, la, el, para, con, ...)
   - Tokenizar y calcular Jaccard similarity entre tokens del campaign/ad_set name vs offer.public_name, offer.internal_sku
   - Similarity ≥ 0.5 → sugerir al nivel campaign (o ad_set si el ad_set name tiene mejor match que el campaign name)

3. **Objective heuristic** (confidence LOW)
   - Solo se dispara si las estrategias 1 y 2 no encontraron match Y el tenant tiene exactamente UNA offer cuyo expected_metric coincide con el objective de la campaign
   - Ej: campaign con objective=OUTCOME_MESSAGES + 1 sola offer con expected_metric=MESSAGE → sugerir

**Reglas importantes:**
- La auto-detección NO persiste directamente (no crea rows en `ad_offer_associations`). Devuelve sugerencias que el usuario confirma.
- Si un target ya tiene una asociación activa (manual o auto confirmada), la detección lo skipea.
- El service tiene que ser idempotente: correrlo 2 veces seguidas produce el mismo output.

### 3.2 `HealthCheckService`

`advertising/application/services/health_check_service.py`.

Entrada: `tenant_id, provider="meta"`.
Salida: `MetaHealthCheckDTO` con:
- `active_campaigns: list[CampaignHealthDTO]` — cada una con: external_id, name, objective, offer_asignada_resumen, esperable_segun_objective, has_pixel_event_expected, pixel_event_reporting_but_missing (warning si objective=SALES y 0 purchases 7d)
- `offers_coverage: list[OfferCoverageDTO]` — cada offer activa con: offer_id, name, archetype, expected_metric, tiene_campana_asociada (bool), campañas_asociadas (ids), alerts
- `unassigned_targets: list[UnassignedTargetDTO]` — campaigns/ad_sets sin asociación activa
- `recommendations: list[RecommendationDTO]` — acciones sugeridas
- `overall_status: 'healthy' | 'needs_attention' | 'critical'`

Cross-checks que el service debe detectar:

1. **Expectativa rota**: campaign con objective=OUTCOME_SALES pero ventas reportadas = 0 en los últimos 7 días → warning "pixel may be misconfigured"
2. **Offer sin campaña**: offer activa sin ninguna asociación → recomendación "crear campaña para esta offer"
3. **Offer con campaña de objetivo equivocado**: ej offer con expected_metric=PURCHASE asociada a campaign con objective=OUTCOME_TRAFFIC → warning "esta campaña busca clicks, no compras. Considerá cambiar el objective"
4. **Unassigned activo**: campaign activa sin offer ni `excluded_branding` → recomendación "asignar a offer o marcar como branding"

### 3.3 `MetricsByOfferService`

`advertising/application/services/metrics_by_offer_service.py`.

Entrada: `tenant_id, period (7d/30d/90d)`.
Salida: `MetricsByOfferDTO` con:
- `offers: list[OfferMetricsDTO]` — cada una con:
  - `offer_id, offer_name, archetype, expected_metric`
  - `total_spend, currency`
  - `primary_result_count` (leads / messages / purchases / etc. según expected_metric)
  - `primary_cost_per_result` (CPL, CPM msg, CPA, etc.)
  - `roas` (solo si expected_metric=PURCHASE o SUBSCRIPTION)
  - `secondary_metrics: dict[str, float]` — CTR, CPC, reach, impressions
  - `timeseries: list[TimeSeriesPointDTO]` — dailies de spend + primary_result_count
- `unassigned: UnassignedAggregateDTO` — spend + metrics de campaigns sin asociación
- `branding_only: BrandingAggregateDTO` — spend de campaigns marcadas excluded_branding
- `period, start_date, end_date`

**Lógica de agregación:**
- Para cada offer asociada, identificar los external_ids de campaigns/ad_sets asociados
- Filtrar `official_metrics.campaign_id` (y `ad_set_id` si la asociación es a nivel ad_set) contra esos external_ids
- Agregar spend, impressions, clicks, y la "primary_result_count" según expected_metric:
  - LEAD → `meta_leads` + fallback `CompleteRegistration` actions
  - MESSAGE → `meta_conversations_started` (del `_META_ACTION_MAP`)
  - PURCHASE → `conversions` (events type purchase)
  - CALL_BOOKED → `meta_conversations_started` (proxy until Nicolify scheduling integration)
  - FORM_SUBMIT → `meta_leads`
  - SUBSCRIPTION → `conversions`
- primary_cost_per_result = total_spend / primary_result_count (si > 0)
- Si result_count = 0 y expected_metric requiere pixel → devolver null y marcar `metric_unavailable_reason = "no_events_reported"`

### 3.4 `CampaignTemplateService` (BASES del Action Trigger futuro)

`advertising/application/services/campaign_template_service.py`.

**Solo lectura por ahora.** Un método:

```python
async def get_template_for_offer(
    self, offer: OfferReadDTO
) -> AdCampaignTemplateDTO | None:
    """Return the best matching template for this offer (read-only for now)."""
```

Busca en `ad_campaign_templates` el row con mejor match (archetype + onboarding_action + is_lead_magnet) ordenado por priority descendente. Sin match → None.

---

## 4. API endpoints

Todos bajo `/api/v1/advertising/`. Router montado en `main.py`.

### 4.1 Asociaciones

```
POST /api/v1/advertising/associations
  body: AssociationCreateDTO {
    target_type: "campaign" | "ad_set"
    target_external_id: str
    offer_id: UUID | None
    association_type: "manual" | "excluded_branding"  # user actions only
    notes: str | None
  }
  response: AssociationDTO
  status: 201

DELETE /api/v1/advertising/associations/{association_id}
  response: 204

GET /api/v1/advertising/associations
  query: target_type? offer_id?
  response: list[AssociationDTO]

POST /api/v1/advertising/associations/auto-detect
  body: {}
  response: list[AssociationSuggestionDTO]  # not persisted

POST /api/v1/advertising/associations/apply-suggestions
  body: list[{ target_type, target_external_id, offer_id, association_type, confidence }]
  response: list[AssociationDTO]
```

### 4.2 Health check

```
GET /api/v1/advertising/health-check?provider=meta
  response: MetaHealthCheckDTO
```

### 4.3 Metrics by offer

```
GET /api/v1/advertising/metrics-by-offer?period=30d
  response: MetricsByOfferDTO
```

### 4.4 Campaign templates (read-only base para Action Trigger futuro)

```
GET /api/v1/advertising/campaign-templates/suggest?offer_id=<uuid>
  response: AdCampaignTemplateDTO | 404
```

### 4.5 Campaigns with offers (enriquece lo que ya devuelve el endpoint de campaigns)

```
GET /api/v1/advertising/campaigns-with-offers?period=30d
  response: CampaignsWithOffersDTO {
    campaigns: list[CampaignWithOfferDTO]  # extends existing CampaignWithMetrics with offer_association
    ad_sets: list[AdSetWithOfferDTO]       # only ad sets that have an association at ad_set level
    offers: list[OfferSummaryDTO]          # active offers list (for dropdown)
  }
```

Este endpoint NO reemplaza los existentes — los complementa. El frontend lo usa para enriquecer la Campaigns tab.

---

## 5. DTOs (Pydantic v2)

`advertising/application/dto/` (un archivo por módulo).

Todos los DTOs usan `ConfigDict(from_attributes=True, populate_by_name=True)`.
Camel case en el output JSON (`alias_generator=to_camel`).
`response_model=` obligatorio en cada endpoint (regla PII).

### AssociationDTO
```python
class AssociationDTO(BaseModel):
    id: UUID
    tenant_id: UUID
    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    offer_id: UUID | None
    offer_name: str | None  # resolved server-side via JOIN
    offer_archetype: str | None
    association_type: str
    confidence: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
```

### AssociationSuggestionDTO
```python
class AssociationSuggestionDTO(BaseModel):
    target_type: Literal["campaign", "ad_set"]
    target_external_id: str
    target_name: str       # campaign/ad_set name for display
    suggested_offer_id: UUID
    suggested_offer_name: str
    association_type: Literal["auto_landing_url", "auto_keyword", "auto_objective"]
    confidence: Literal["high", "medium", "low"]
    reason: str            # human-readable, e.g. "Landing URL del ad match con offer 'MasterClass'"
```

### MetaHealthCheckDTO
```python
class MetaHealthCheckDTO(BaseModel):
    overall_status: Literal["healthy", "needs_attention", "critical"]
    active_campaigns: list[CampaignHealthDTO]
    offers_coverage: list[OfferCoverageDTO]
    unassigned_targets: list[UnassignedTargetDTO]
    recommendations: list[RecommendationDTO]
    summary_text: str  # 1-line narrative for the card header

class CampaignHealthDTO(BaseModel):
    external_id: str
    name: str
    objective: str | None
    objective_label_es: str  # "Tráfico", "Ventas", "Mensajes" — Spanish label
    status: str | None
    offer_association: AssociationDTO | None
    expected_outcome_es: str  # what to expect given the objective
    has_issue: bool
    issue_text: str | None

class OfferCoverageDTO(BaseModel):
    offer_id: UUID
    offer_name: str
    archetype: str
    expected_metric: str  # from OfferExpectedMetric enum
    expected_metric_label_es: str  # Spanish label
    has_active_campaign: bool
    associated_targets: list[AssociationDTO]

class UnassignedTargetDTO(BaseModel):
    target_type: Literal["campaign", "ad_set"]
    external_id: str
    name: str
    objective: str | None
    status: str | None

class RecommendationDTO(BaseModel):
    type: str  # "create_campaign" | "fix_objective" | "configure_pixel" | "assign_offer"
    severity: Literal["info", "warning", "critical"]
    title: str
    body: str
    action_label: str
    action_url: str | None
    related_offer_id: UUID | None
    related_target_id: str | None
```

### MetricsByOfferDTO
```python
class MetricsByOfferDTO(BaseModel):
    period: str
    start_date: date
    end_date: date
    currency: str | None
    offers: list[OfferMetricsDTO]
    unassigned: UnassignedAggregateDTO
    branding_only: BrandingAggregateDTO

class OfferMetricsDTO(BaseModel):
    offer_id: UUID
    offer_name: str
    archetype: str
    expected_metric: str
    expected_metric_label_es: str
    total_spend: float
    currency: str
    primary_result_count: float
    primary_cost_per_result: float | None
    primary_metric_name: str       # e.g. "Costo por Mensaje"
    primary_metric_unit: str       # "currency" | "count"
    roas: float | None             # only for PURCHASE / SUBSCRIPTION
    secondary_metrics: dict[str, float]  # CTR, CPC, CPM, reach, impressions, clicks
    timeseries: list[OfferTimeSeriesPointDTO]
    metric_unavailable_reason: str | None

class OfferTimeSeriesPointDTO(BaseModel):
    date: str      # ISO date
    spend: float
    primary_result: float

class UnassignedAggregateDTO(BaseModel):
    target_count: int
    total_spend: float
    impressions: float
    clicks: float

class BrandingAggregateDTO(BaseModel):
    target_count: int
    total_spend: float
    reach: float
    impressions: float
```

### AdCampaignTemplateDTO
```python
class AdCampaignTemplateDTO(BaseModel):
    id: UUID
    offer_archetype: str
    offer_onboarding_action: str | None
    offer_is_lead_magnet: bool | None
    name: str
    description: str
    recommended_objective: str
    recommended_objective_label_es: str
    recommended_optimization_goal: str | None
    recommended_destination_type: str | None
    structure_hints: dict
    priority: int
```

---

## 6. Frontend contracts

### 6.1 TypeScript types

`frontend/src/features/meta-ads/types.ts` (nuevo).

```ts
export type TargetType = 'campaign' | 'ad_set';
export type AssociationType =
  | 'manual' | 'auto_landing_url' | 'auto_keyword'
  | 'auto_objective' | 'excluded_branding' | 'suggested';
export type AssociationConfidence = 'high' | 'medium' | 'low';
export type ExpectedMetric =
  | 'lead' | 'message' | 'purchase'
  | 'subscription' | 'call_booked' | 'form_submit';

export interface Association {
  id: string;
  tenantId: string;
  targetType: TargetType;
  targetExternalId: string;
  offerId: string | null;
  offerName: string | null;
  offerArchetype: string | null;
  associationType: AssociationType;
  confidence: AssociationConfidence | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface AssociationSuggestion {
  targetType: TargetType;
  targetExternalId: string;
  targetName: string;
  suggestedOfferId: string;
  suggestedOfferName: string;
  associationType: AssociationType;
  confidence: AssociationConfidence;
  reason: string;
}

export interface CampaignHealth { /* mirror backend */ }
export interface OfferCoverage { /* mirror backend */ }
export interface MetaHealthCheck {
  overallStatus: 'healthy' | 'needs_attention' | 'critical';
  activeCampaigns: CampaignHealth[];
  offersCoverage: OfferCoverage[];
  unassignedTargets: UnassignedTarget[];
  recommendations: Recommendation[];
  summaryText: string;
}
export interface OfferMetrics { /* mirror backend */ }
export interface MetricsByOffer {
  period: string;
  startDate: string;
  endDate: string;
  currency: string | null;
  offers: OfferMetrics[];
  unassigned: UnassignedAggregate;
  brandingOnly: BrandingAggregate;
}
```

### 6.2 React Query hooks

`frontend/src/features/meta-ads/api/`:

```ts
// associations-api.ts
export function useAssociations(filters?);
export function useCreateAssociation();
export function useDeleteAssociation();
export function useAutoDetectSuggestions();  // returns suggestions, does not persist
export function useApplySuggestions();

// health-check-api.ts
export function useMetaHealthCheck(period);

// metrics-by-offer-api.ts
export function useMetricsByOffer(period);

// campaign-templates-api.ts
export function useCampaignTemplateForOffer(offerId);
```

Todos usan `fetchClient` (injecta X-Tenant-ID).

### 6.3 Componentes nuevos / modificados

**Nuevos:**
- `sidebar/meta-ads/MetaAdsHealthCheckPanel.tsx` — panel de diagnóstico arriba del chart en Resumen
- `sidebar/meta-ads/OfferAssignmentDrawer.tsx` — drawer lateral con lista de offers + sugerencias
- `sidebar/meta-ads/OfferSegmenter.tsx` — chips para filtrar por offer en Resumen
- `sidebar/meta-ads/MetaAdsOnboardingModal.tsx` — wizard de primera conexión
- `sidebar/meta-ads/BestPracticesBlock.tsx` — contenido educativo reusable (dentro de drawer y onboarding)
- `sidebar/meta-ads/UnassignedBanner.tsx` — banner persistente "Tenés N campañas sin asignar"

**Modificados:**
- `tabs/CampaignsTab.tsx` — agregar columna "Offer asignada" + trigger drawer, filter chips, botón "Auto-detectar"
- `tabs/ResumenTab.tsx` — agregar `MetaAdsHealthCheckPanel`, `UnassignedBanner`, `OfferSegmenter`, y el chart ahora usa `useMetricsByOffer` cuando hay una offer filtrada
- `InversionChart.tsx` — soportar prop `mode: 'traffic' | 'leads' | 'messages' | 'purchases' | 'subscriptions'` que adapta colores, break-even, tooltip labels
- `MetaAdsDashboard.tsx` — detectar first-connect (via localStorage key + query de associations existentes) para trigger del onboarding modal

**Rutas de navegación:**
- Desde `MetaAdsHealthCheckPanel` el botón "Asociar campañas →" hace `router.push('...?tab=campanas')` y abre el drawer automáticamente (via query param `?assign=true`)
- El segmentador del Resumen escribe al URL `?offer=<slug>` para deep-linking

---

## 7. Comportamiento del Resumen (flujo integrado)

Cuando el usuario entra a `/growth-studio/atraccion-captura/meta-ads`:

1. **Load simultáneo**:
   - `useChannelDashboard('meta-ads', period)` (lo que ya había)
   - `useMetaHealthCheck(period)` (nuevo)
   - `useMetricsByOffer(period)` (nuevo)

2. **Render orden vertical**:
   ```
   [Header con period selector y botón sync]
   [ConnectionHealthBanner si hay issues de conexión]
   ---
   [Onboarding modal si first-connect y no se cerró antes]  ← overlay
   ---
   [MetaAdsHealthCheckPanel]                                 ← arriba del chart
     - Si overall_status=healthy: card verde compacta
     - Si needs_attention/critical: card expandida con warnings + recommendations
     - Botón "Asociar campañas →" si hay unassigned_targets
   [UnassignedBanner] (si hay unassigned con status=active)
   [KPI grid — RESUMEN_KPIS adaptado al expected_metric dominante]
   [OfferSegmenter]                                          ← nuevo
     - chips: "Todas" | offer1 | offer2 | ... | "Sin asignar" | "Branding"
   [InversionChart]
     - Con mode dinámico según selección del segmenter
     - "Todas" → agrega todos los modes, muestra breakdown narrativo
     - offer específica → modo de esa offer (purchase/lead/message/etc.)
   [Funnel]
   [Alertas / Recommendations viejas]
   ```

3. **Filtrado por segmenter**: cuando el usuario selecciona una offer, el chart llama a `useMetricsByOffer(period)` y filtra en cliente a esa offer. El modo del chart cambia según `expected_metric` de la offer seleccionada.

### Adaptación del modo del chart según `expected_metric`:

| expected_metric | Barras coloreadas por | Línea principal | Break-even / meta |
|---|---|---|---|
| `purchase` | ROAS (verde ≥1, rojo <1) | ROAS | 1.0x |
| `subscription` | ROAS | ROAS | 1.0x |
| `lead` | CPL vs meta | CPL | Meta CPL (de config tenant o promedio histórico) |
| `message` | Costo por msg vs meta | Costo por msg | Meta |
| `call_booked` | Costo por llamada | Costo por llamada | Meta |
| `form_submit` | Costo por form | Costo por form | Meta |

"Todas": el chart muestra solo spend diario como barras (todas gris neutro), sin línea — porque no hay una métrica común para todas las offers. El subtítulo narrativo lista cada offer con sus números.

"Sin asignar": solo spend + CTR + CPC (como el modo "Tráfico" del mockup).

"Branding": solo spend + reach + frequency (modo alcance).

---

## 8. Migración Alembic

**Nombre del archivo:** `alembic/versions/{rev}_add_ad_offer_associations_and_templates.py`
**Downgrade:** drop tables + indexes.
**Upgrade:** idempotente con raw SQL:

```python
def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_offer_associations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            target_type VARCHAR(20) NOT NULL,
            target_external_id VARCHAR(255) NOT NULL,
            offer_id UUID,
            association_type VARCHAR(50) NOT NULL,
            confidence VARCHAR(20),
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_ad_offer_tenant_target
        ON ad_offer_associations (tenant_id, target_type, target_external_id)
        WHERE deleted_at IS NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_offer_tenant_offer
        ON ad_offer_associations (tenant_id, offer_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaign_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            offer_archetype VARCHAR(50) NOT NULL,
            offer_onboarding_action VARCHAR(50),
            offer_is_lead_magnet BOOLEAN,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            recommended_objective VARCHAR(50) NOT NULL,
            recommended_optimization_goal VARCHAR(100),
            recommended_destination_type VARCHAR(100),
            structure_hints JSONB DEFAULT '{}'::jsonb,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
    """)

    # Seed templates — idempotent upsert via ON CONFLICT requires unique key.
    # Use DELETE+INSERT pattern guarded by a distinctive row:
    op.execute("""
        INSERT INTO ad_campaign_templates
          (offer_archetype, offer_onboarding_action, offer_is_lead_magnet,
           name, description, recommended_objective, priority)
        SELECT * FROM (VALUES
          ('PRODUCTO', NULL, true,
           'Lead Magnet - Captar emails',
           'Lead magnet: captá emails con formulario o página de descarga',
           'OUTCOME_LEADS', 100),
          ('PRODUCTO', NULL, false,
           'Producto Digital - Venta directa',
           'Producto digital con checkout web: optimizá para compras directas',
           'OUTCOME_SALES', 100),
          -- ... all 8 rows
        ) AS t(archetype, onboarding, lead, name, descr, obj, prio)
        WHERE NOT EXISTS (
          SELECT 1 FROM ad_campaign_templates
          WHERE offer_archetype = t.archetype
            AND COALESCE(offer_onboarding_action, '') = COALESCE(t.onboarding, '')
            AND COALESCE(offer_is_lead_magnet::text, '') = COALESCE(t.lead::text, '')
        );
    """)
```

---

## 9. Tests (TDD obligatorio)

### Backend
- `tests/modules/advertising/test_offer_detection_service.py`
  - Fixtures: mock tenant con offers activas + ad_campaigns + ad_sets + ads
  - Casos: landing URL match, keyword match, objective heuristic, empty input, existing association skipped, confidence ranking
- `tests/modules/advertising/test_health_check_service.py`
  - Casos: tenant sin campañas, tenant con campañas pero sin offers, tenant con mismatch objective↔offer, expectativa rota (SALES + 0 purchases 7d), healthy state
- `tests/modules/advertising/test_association_repository.py`
  - Casos: create, soft delete, unique constraint en target activo, list by filter
- `tests/modules/advertising/test_metrics_by_offer_service.py`
  - Casos: offer con purchases, offer con messages, offer sin events, unassigned spend, branding spend
- `tests/modules/advertising/test_api_associations.py`
  - Happy paths + tenant isolation + auth
- `tests/modules/advertising/test_api_health_check.py`
  - Happy path
- `tests/modules/advertising/test_api_metrics_by_offer.py`
  - Happy path
- `tests/modules/advertising/test_campaign_template_service.py`
  - Casos: match exacto, match parcial, sin match

### Frontend
- `features/meta-ads/api/__tests__/associations-api.test.ts` — mock fetchClient
- `features/growth-studio/.../__tests__/MetaAdsHealthCheckPanel.test.tsx`
- `features/growth-studio/.../__tests__/OfferAssignmentDrawer.test.tsx`
- `features/growth-studio/.../__tests__/OfferSegmenter.test.tsx`
- `features/growth-studio/.../__tests__/InversionChart.test.tsx` — extender tests existentes para los nuevos modes
- `features/growth-studio/.../__tests__/CampaignsTab.test.tsx` — extender tests existentes

---

## 10. Restricciones y reglas

- **DDD strict**: `advertising` es un módulo nuevo, no importa directo de `offer` ni `analytics`. Usa el `OfferReadPort` que ya existe para consultar offers. Para leer campaigns/ad_sets/ads/official_metrics debe usar sus propios repositorios internos que importan los **models** de analytics (excepción documentada — similar a como copilot importa de otros módulos).
- **Tenant isolation**: toda query filtra por tenant_id, todos los endpoints validan `X-Tenant-ID`.
- **response_model** obligatorio en cada endpoint.
- **PII**: ninguno de los DTOs expone datos personales (emails, etc.). Solo metadata de campañas y offers.
- **Migración idempotente** (raw SQL + IF NOT EXISTS + unique index condicional).
- **Soft delete only**.
- **Pydantic v2, SQLAlchemy 2.0 syntax**.
- **Spanish con tildes** en todos los strings visibles al usuario (labels del health check, recommendations, etc.).
- **No cross-feature imports** en frontend (salvo copilot exception). `meta-ads` feature puede vivir en `frontend/src/features/meta-ads/` O expandir el existente en `growth-studio/.../meta-ads/` — elegir uno y ser consistente. Recomendación: **expandir el existente** para mantener cohesión con el dashboard actual.
- **Tests-first** (TDD obligatorio). Cada service, repositorio y componente tiene test antes de implementación.
