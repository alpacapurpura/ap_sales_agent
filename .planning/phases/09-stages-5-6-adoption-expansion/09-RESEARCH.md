# Phase 9: Stages 5-6 Adoption & Expansion - Research

**Researched:** 2026-03-16
**Domain:** Post-sale customer health metrics (Adoption) and revenue retention metrics (Expansion)
**Confidence:** HIGH

## Summary

Phase 9 builds two post-sale analytics panels within the existing Growth Studio metrics dashboard. The **Adoption** panel (Stage 5) tracks customer health after purchase -- who is actively using the product vs. who has gone silent -- using the existing `is_inactive` flag and `last_activity_at` on `CustomerProfileModel`. The **Expansion** panel (Stage 6) tracks revenue retention -- MRR from renewals, upsell/cross-sell revenue, and churn losses -- using `SaleModel` (stage=EXPANSION), `LifecycleTransitionModel` (to_stage=CHURNED), and `CustomerProfileModel.lifetime_value`.

Both panels follow the established pattern from Phases 5-8: backend repository + MetricsService method + DTO + API endpoint + React Query hook + detail panel component. The CRM data models already contain all the fields needed. No new database tables or migrations are required. The key challenge is writing efficient aggregate queries across `customer_profiles`, `journey_events`, `sales`, and `lifecycle_transitions` tables with proper tenant isolation.

**Primary recommendation:** Follow the exact MetricsService pattern from Phase 8 (get_sales_metrics). Create two new repositories (`AdoptionMetricsRepository`, `ExpansionMetricsRepository`), two new DTOs (`adoption_dto.py`, `expansion_dto.py`), two new MetricsService methods, two new API endpoints, and two new frontend detail panel components. Reuse `OfferReadPort`, `MiniFunnelDTO`, `BottleneckDTO`, dual currency formatting, and the `MetricsCache` pattern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Adoption panel: dual structure with summary health bar + per-offer drill-down cards
- Adoption header: 3 primary KPIs (Clientes Activos, Clientes Inactivos, Salud %) + 2 secondary KPIs (TTV Promedio, Devoluciones)
- Adoption per-offer cards: offer public_name + total customers + active/inactive counts + health % + TTV
- Refunds: source-agnostic via SaleModel.status == REFUNDED (no hardcoded Shopify logic)
- Visual health bar: horizontal proportional green/yellow segments between KPIs and offer cards
- Active/Inactive: universal 14-day rule using existing is_inactive flag and last_activity_at
- Expansion panel: 3 groups (Retencion, Expansion/Crecimiento, Cancelaciones) with offer drill-down
- Expansion header: 3 KPIs with tooltip hints in plain Spanish (Ingreso Recurrente Neto, Valor Promedio por Cliente, Tasa de Cancelacion)
- Expansion MiniFunnel: Activos (N) -> Expansion (M) = X% expansion rate
- Churn group: red visual treatment, data from LifecycleTransitionModel where to_stage=CHURNED
- Dual currency on all monetary amounts (tenant currency + USD conversion)
- All labels in plain Spanish with tooltip hints for technical metrics
- TTV = days from first_conversion_at to first journey_event after purchase
- Bottleneck: adoption health < 70% = yellow warning; churn rate > 5% = red critical
- Context-aware bottleneck tips that change based on data patterns

### Claude's Discretion
- Adoption MiniFunnel inclusion decision (DECIDED: include, per UI-SPEC)
- Exact offer card component design (spacing, shadows, health indicator styling)
- Health bar component implementation (CSS proportional bar vs chart library)
- User-friendly KPI label naming for Expansion metrics (DECIDED in UI-SPEC)
- Tooltip/hint content for technical metrics (DECIDED in UI-SPEC copywriting contract)
- Context-aware tip library (DECIDED in UI-SPEC)
- Bottleneck threshold calibration (DECIDED in UI-SPEC: 70% health, 5% churn critical, 3% churn warning)
- Renewal vs upsell classification logic from SaleModel data
- Channel registry entries for adoption/expansion stages
- Error/stale UX for post-sale specific scenarios

### Deferred Ideas (OUT OF SCOPE)
- Configurable inactivity thresholds per offer type (course vs coaching vs subscription)
- Configurable bottleneck thresholds per tenant
- Revenue trend indicators (vs previous period) -- Phase 11
- Separate RefundEvent with reason codes
- Product-type aware TTV calculation
- Post-sale cost tracking
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADO-01 | Detail panel showing customer health cohort per service sold: active vs inactive users | Adoption DTO with per-offer OfferHealthDTO containing active_count, inactive_count, health_pct. Frontend OfferHealthCard component. Data source: CustomerProfileModel.is_inactive grouped by offer_id from SaleModel CONVERSION |
| ADO-02 | Backend endpoint `/metrics/adoption` tracking product usage via journey_events post-purchase | AdoptionMetricsRepository queries CustomerProfileModel joined with SaleModel for offer grouping + JourneyEventModel for TTV. MetricsService.get_adoption_metrics() method. API route in metrics.py |
| ADO-03 | Time-to-Value indicator: days from purchase to first meaningful engagement event | TTV calculation: first JourneyEventModel.occurred_at after CustomerProfileModel.first_conversion_at per profile. Averaged per offer and globally. Displayed as "{N} dias" |
| ADO-04 | Inactivity as bottleneck: high inactive ratio predicts churn, flagged visually | BottleneckDTO reuse with type="low_adoption_health". Threshold: overall health < 70% = warning. Per-offer < 60% = inline badge. Context-aware tips based on TTV + inactive ratio combo |
| EXP-01 | Detail panel showing renewal events (MRR retained), upsell events (revenue expansion), and churn (MRR lost) | ExpansionDetailDTO with three ExpansionGroupDTO instances (retencion, crecimiento, cancelaciones). Per-offer rows within each group. Frontend ExpansionGroup + ExpansionOfferRow components |
| EXP-02 | Backend endpoint `/metrics/expansion` tracking MRR retained vs lost and upsell revenue | ExpansionMetricsRepository queries SaleModel(stage=EXPANSION) for renewals/upsells, LifecycleTransitionModel(to_stage=CHURNED) for churn count, SaleModel(status=REFUNDED) excluded from revenue. MetricsService.get_expansion_metrics() method |
| EXP-03 | lifetime_value updated on customer_profiles for each EXPANSION event | Already implemented in LifecycleService.handle_sale_completed() -- EXPANSION branch adds amount to lifetime_value. Expansion endpoint reads lifetime_value for LTV average KPI |
| EXP-04 | Churn rate calculated: subscription cancellations / total active subscriptions; >5% flagged as critical bottleneck | Churn rate = count(LifecycleTransition to_stage=CHURNED in period) / count(CustomerProfile lifecycle_stage in [CUSTOMER, EVANGELIST]). BottleneckDTO with type="high_churn_rate", severity="critical" when >5%, "warning" when >3% |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | API endpoints for /metrics/adoption and /metrics/expansion | Project standard |
| SQLAlchemy 2.0 | existing | CRM queries with select() syntax | Project standard, mandatory |
| Pydantic v2 | existing | DTOs for adoption and expansion responses | Project standard |
| React 18+ / Next.js 14 | existing | Frontend detail panels | Project standard |
| @tanstack/react-query | existing | Data fetching hooks (useSalesDetail pattern) | Established in Phases 5-8 |
| Tailwind CSS | existing | Styling with space-y-2 panel rhythm | Project standard |
| shadcn/ui | existing | Skeleton, Tooltip components | Established in prior phases |
| lucide-react | existing | Icons (AlertTriangle, Info) | Established in prior phases |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Intl.NumberFormat | browser API | Dual currency formatting (es-MX / en-US) | All monetary amounts |
| Radix Tooltip | via shadcn | KPI hint tooltips on Expansion panel | Expansion header KPIs |

### Alternatives Considered
None. This phase uses the exact same stack as Phases 5-8 with zero new dependencies.

**Installation:**
```bash
# Only if Tooltip not already installed in shadcn:
npx shadcn add tooltip
```

## Architecture Patterns

### Backend Structure (new files)
```
backend/src/modules/analytics/
  application/
    dto/
      adoption_dto.py          # AdoptionDetailDTO, AdoptionHeaderKpisDTO, OfferHealthDTO
      expansion_dto.py         # ExpansionDetailDTO, ExpansionHeaderKpisDTO, ExpansionGroupDTO, ExpansionOfferDTO
    services/
      metrics_service.py       # ADD: get_adoption_metrics(), get_expansion_metrics()
      channel_registry.py      # ADD: "adoption" and "expansion" entries to STAGE_CHANNEL_MAP
  infrastructure/
    repositories/
      adoption_repository.py   # AdoptionMetricsRepository (NEW)
      expansion_repository.py  # ExpansionMetricsRepository (NEW)
  api/
    metrics.py                 # ADD: /metrics/adoption, /metrics/expansion endpoints
```

### Frontend Structure (new files)
```
frontend/src/features/marketing-studio/
  components/metrics-dashboard/
    detail-panels/
      AdoptionDetail.tsx       # NEW: Stage 5 panel
      ExpansionDetail.tsx      # NEW: Stage 6 panel
    channel-widgets/
      HealthBar.tsx            # NEW: proportional green/yellow bar
      OfferHealthCard.tsx      # NEW: per-offer health card
      ExpansionGroup.tsx       # NEW: category header + offer rows
      ExpansionOfferRow.tsx    # NEW: single offer within expansion group
      KpiTooltip.tsx           # NEW: tooltip hint for metric labels
  hooks/
    useAdoptionDetail.ts       # NEW: React Query hook
    useExpansionDetail.ts      # NEW: React Query hook
  types/
    metrics.ts                 # ADD: AdoptionDetail, ExpansionDetail types
  api/
    metrics-api.ts             # ADD: getAdoptionDetail(), getExpansionDetail()
    metrics-mock-data.ts       # ADD: MOCK_ADOPTION_DETAIL, MOCK_EXPANSION_DETAIL
```

### Pattern 1: MetricsService Method (follow get_sales_metrics exactly)
**What:** Each stage gets a dedicated async method on MetricsService that checks cache, queries repository, builds DTO, caches result, and returns.
**When to use:** Both adoption and expansion endpoints.
**Example:**
```python
# Source: backend/src/modules/analytics/application/services/metrics_service.py (Phase 8 pattern)
async def get_adoption_metrics(
    self, tenant_id: UUID, start_date: datetime, end_date: datetime
) -> AdoptionDetailDTO:
    # 1. Check cache
    if self.cache is not None:
        cached = await self.cache.get(str(tenant_id), "adoption", "last_30_days")
        if cached is not None:
            return AdoptionDetailDTO(**cached)

    # 2. Query repository
    repo = AdoptionMetricsRepository(self.db)
    # ... queries ...

    # 3. Build DTO
    result = AdoptionDetailDTO(...)

    # 4. Cache and return
    if self.cache is not None:
        await self.cache.set(str(tenant_id), "adoption", "last_30_days", result.model_dump())
    return result
```

### Pattern 2: Repository Aggregate Query (follow SalesMetricsRepository)
**What:** Repository classes with typed query methods using SQLAlchemy 2.0 select() syntax, tenant-filtered, returning typed tuples.
**When to use:** All CRM data aggregation for adoption and expansion.
**Example:**
```python
# Source: backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py
class AdoptionMetricsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_customer_health_by_offer(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[tuple]:
        """Count active vs inactive customers grouped by offer_id from their CONVERSION sale."""
        stmt = (
            select(
                SaleModel.offer_id,
                func.count(distinct(CustomerProfileModel.id)).label("total"),
                func.count(distinct(CustomerProfileModel.id)).filter(
                    CustomerProfileModel.is_inactive == False
                ).label("active"),
                func.count(distinct(CustomerProfileModel.id)).filter(
                    CustomerProfileModel.is_inactive == True
                ).label("inactive"),
            )
            .join(CustomerProfileModel, SaleModel.customer_id == CustomerProfileModel.id)
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.stage == SaleStage.CONVERSION,
                CustomerProfileModel.lifecycle_stage.in_([
                    LifecycleStage.CUSTOMER,
                    LifecycleStage.EVANGELIST,
                    LifecycleStage.CHURNED,
                ]),
            )
            .group_by(SaleModel.offer_id)
        )
        return self.db.execute(stmt).all()
```

### Pattern 3: Frontend Hook + API (follow useSalesDetail exactly)
**What:** React Query hook using useAuth + metricsApi pattern with 5-min staleTime and mock fallback.
**When to use:** Both adoption and expansion data fetching.
**Example:**
```typescript
// Source: frontend/src/features/marketing-studio/hooks/useSalesDetail.ts
export function useAdoptionDetail() {
  const { getToken } = useAuth();
  return useQuery<AdoptionDetail>({
    queryKey: ['adoption-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getAdoptionDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
```

### Pattern 4: API Endpoint (follow get_sales_metrics route)
**What:** FastAPI GET endpoint with auth dependency, cache + ports injection, response_model typing.
**When to use:** Both /metrics/adoption and /metrics/expansion.
**Example:**
```python
# Source: backend/src/modules/analytics/api/metrics.py
@router.get("/adoption", response_model=AdoptionDetailDTO)
async def get_adoption_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port, offer_port=offer_port)
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_adoption_metrics(user.tenant_id, start_date, now)
```

### Anti-Patterns to Avoid
- **Direct ORM joins across bounded contexts:** Never import CRM models directly in analytics API. Use repository pattern within analytics module that queries CRM tables.
- **Hardcoded refund source:** CONTEXT.md explicitly states refunds must be source-agnostic. Query `SaleModel.status == REFUNDED` without filtering by source.
- **Forgetting tenant_id filter:** Every single query MUST include `tenant_id == tenant_id` where clause.
- **Building custom health bar with a charting library:** Use CSS proportional widths (simple div with flex or percentage width). No chart library needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Currency formatting | Custom formatter | `Intl.NumberFormat` with `formatDualCurrency` from SalesDetail.tsx | Already built, handles edge cases |
| Bottleneck alerts | Custom alert component | `BottleneckDTO` + `BottleneckBanner.tsx` | Already built with severity styling |
| Mini funnel | Custom funnel viz | `MiniFunnelDTO` + `MiniFunnel.tsx` | Reusable, accepts any labels |
| Offer enrichment | Direct ORM join to products | `OfferReadPort` + `OfferReadPortImpl` | DDD boundary pattern, already tested |
| Cache layer | Custom caching | `MetricsCache` with per-stage TTL | Already built with Redis integration |
| Tooltip hints | Custom popover | shadcn `Tooltip` component | Standard Radix-based, accessible |
| Loading states | Custom skeleton | shadcn `Skeleton` component | Already used in all prior panels |

**Key insight:** Phase 9 is a pattern replication phase. Every structural pattern already exists from Phases 5-8. The only novel components are the HealthBar (CSS proportional bar) and the ExpansionGroup (new layout for 3 category groups).

## Common Pitfalls

### Pitfall 1: TTV Calculation Edge Cases
**What goes wrong:** TTV query returns NULL or infinity for customers with no post-purchase journey_events.
**Why it happens:** Not all customers generate journey_events after purchase. Some products track engagement outside the system.
**How to avoid:** Exclude customers with no post-purchase events from TTV average (as specified in UI-SPEC). Use COALESCE and conditional aggregation. Only count events with `occurred_at > first_conversion_at`.
**Warning signs:** TTV shows as 0 or extremely high values.

### Pitfall 2: Double-Counting Customers Across Offers
**What goes wrong:** A customer who bought two offers appears in both offer cards, inflating totals.
**Why it happens:** Join between sales and profiles produces multiple rows per customer.
**How to avoid:** Use `DISTINCT profile_id` in aggregations. For total KPIs, count distinct profiles across all offers (not sum of per-offer counts).
**Warning signs:** Header KPI total != sum of offer card totals.

### Pitfall 3: Renewal vs Upsell Classification
**What goes wrong:** All EXPANSION sales lumped together without distinguishing renewals from upsells.
**Why it happens:** SaleModel has stage=EXPANSION for both, and there is no explicit `event_name` field differentiating subscription_cycle from new upsell.
**How to avoid:** Use `metadata_info` JSONB field on SaleModel. The CONTEXT.md specifies renewals have event_name "subscription_cycle" in metadata. Check `metadata_info->>'event_name'` to classify. If metadata is empty/missing, classify as "upsell" (safe default for manual entries).
**Warning signs:** Retention group shows 0 renewals while Expansion group is inflated.

### Pitfall 4: Churn Rate Denominator
**What goes wrong:** Churn rate calculated against wrong denominator (all customers vs active subscribers).
**Why it happens:** Denominator should be "total active subscriptions" but there is no subscription count field.
**How to avoid:** Denominator = count of CustomerProfileModel with `lifecycle_stage IN (CUSTOMER, EVANGELIST)` for the tenant. Numerator = count of LifecycleTransitionModel with `to_stage = CHURNED` in period. This matches the CONTEXT.md definition.
**Warning signs:** Churn rate seems impossibly low or high.

### Pitfall 5: LifecycleStage Enum Filter
**What goes wrong:** Using string comparison instead of enum for lifecycle_stage queries.
**Why it happens:** SQLAlchemy PG Enum requires using the Python enum member, not the string value.
**How to avoid:** Always use `LifecycleStage.CUSTOMER`, never `"customer"` in where clauses. The Phase 8 decision note confirms: "SaleStatus.COMPLETED and SaleStage enum members used directly for PG enum column filtering".
**Warning signs:** Empty query results despite data existing.

### Pitfall 6: MetricsDashboard.tsx Stage Routing
**What goes wrong:** New panels don't render when clicking ADOPCION or EXPANSION stage cards.
**Why it happens:** MetricsDashboard.tsx uses conditional rendering and currently falls through to PlaceholderDetail for ADOPCION and EXPANSION.
**How to avoid:** Add explicit cases for `activeStage === 'ADOPCION'` and `activeStage === 'EXPANSION'` in the conditional chain, plus import the new components.
**Warning signs:** Clicking stage card shows "Proximamente" placeholder instead of real panel.

## Code Examples

### DTO: AdoptionDetailDTO
```python
# Pattern from sales_dto.py and opportunity_dto.py
from pydantic import BaseModel
from typing import List, Optional
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO

class OfferHealthDTO(BaseModel):
    """Per-offer customer health card."""
    offer_id: str
    public_name: str
    total_customers: int
    active_count: int
    inactive_count: int
    health_pct: float  # 0-100
    ttv_days: Optional[float] = None  # average TTV for this offer's customers

class AdoptionHeaderKpisDTO(BaseModel):
    """3 primary + 2 secondary KPIs."""
    active_customers: int
    inactive_customers: int
    health_pct: float  # active / total * 100
    avg_ttv_days: Optional[float] = None
    refund_count: int = 0
    refund_amount: float = 0.0
    refund_currency: str = "USD"
    refund_amount_usd: Optional[float] = None

class AdoptionDetailDTO(BaseModel):
    """Full adoption stage (Stage 5) detail response."""
    header_kpis: AdoptionHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Ventas -> Activos
    offers: List[OfferHealthDTO]
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### DTO: ExpansionDetailDTO
```python
class ExpansionOfferDTO(BaseModel):
    """Single offer within an expansion group."""
    offer_id: str
    public_name: str
    count: int
    revenue: float
    currency: str
    usd_revenue: Optional[float] = None

class ExpansionGroupDTO(BaseModel):
    """Category group: retencion, crecimiento, or cancelaciones."""
    group_key: str  # "retencion" | "crecimiento" | "cancelaciones"
    group_label: str
    group_subtitle: str
    total_count: int
    total_revenue: float
    total_revenue_usd: Optional[float] = None
    currency: str
    rate_pct: Optional[float] = None  # retention rate, expansion rate, or churn rate
    offers: List[ExpansionOfferDTO]

class ExpansionHeaderKpisDTO(BaseModel):
    """Net MRR, Avg LTV, Churn Rate."""
    net_mrr: float
    net_mrr_usd: Optional[float] = None
    currency: str
    avg_ltv: float
    avg_ltv_usd: Optional[float] = None
    churn_rate_pct: float  # 0-100

class ExpansionDetailDTO(BaseModel):
    """Full expansion stage (Stage 6) detail response."""
    header_kpis: ExpansionHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Activos -> Expansion
    retencion: ExpansionGroupDTO
    crecimiento: ExpansionGroupDTO
    cancelaciones: ExpansionGroupDTO
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### Repository: TTV Calculation
```python
# Time-to-Value: days from first_conversion_at to first journey_event after purchase
def get_avg_ttv_by_offer(
    self, tenant_id: UUID, start_date: datetime, end_date: datetime
) -> Dict[str, float]:
    """Average TTV per offer_id for customers converted in period."""
    # Subquery: first post-purchase event per customer
    first_event = (
        select(
            JourneyEventModel.profile_id,
            func.min(JourneyEventModel.occurred_at).label("first_event_at"),
        )
        .where(JourneyEventModel.tenant_id == tenant_id)
        .group_by(JourneyEventModel.profile_id)
        .subquery()
    )

    stmt = (
        select(
            SaleModel.offer_id,
            func.avg(
                func.extract("epoch", first_event.c.first_event_at - CustomerProfileModel.first_conversion_at) / 86400
            ).label("avg_ttv"),
        )
        .join(CustomerProfileModel, SaleModel.customer_id == CustomerProfileModel.id)
        .outerjoin(first_event, CustomerProfileModel.id == first_event.c.profile_id)
        .where(
            SaleModel.tenant_id == tenant_id,
            SaleModel.stage == SaleStage.CONVERSION,
            SaleModel.status == SaleStatus.COMPLETED,
            CustomerProfileModel.first_conversion_at.isnot(None),
            first_event.c.first_event_at > CustomerProfileModel.first_conversion_at,
        )
        .group_by(SaleModel.offer_id)
    )
    results = self.db.execute(stmt).all()
    return {str(row[0]): round(float(row[1]), 1) for row in results if row[1] is not None}
```

### Frontend: HealthBar Component
```typescript
// CSS proportional bar -- no chart library needed
interface HealthBarProps {
  activeCount: number;
  inactiveCount: number;
}

export function HealthBar({ activeCount, inactiveCount }: HealthBarProps) {
  const total = activeCount + inactiveCount;
  const activePct = total > 0 ? (activeCount / total) * 100 : 100;
  const inactivePct = total > 0 ? (inactiveCount / total) * 100 : 0;

  return (
    <div className="px-3 py-2">
      <div className="flex h-3 w-full rounded-full overflow-hidden bg-muted">
        <div
          className="bg-emerald-500 transition-all"
          style={{ width: `${Math.max(activePct, total > 0 ? 1 : 0)}%` }}
        />
        <div
          className="bg-yellow-400 transition-all"
          style={{ width: `${Math.max(inactivePct, total > 0 ? 1 : 0)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground mt-1">
        <span className="text-emerald-600 dark:text-emerald-400">{activeCount} activos</span>
        <span className="text-yellow-600 dark:text-yellow-400">{inactiveCount} inactivos</span>
      </div>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Point-in-time health checks | Trend-based health scoring (4+ weeks declining) | 2025 industry shift | Current phase uses point-in-time (is_inactive flag) which is sufficient for v1 micro-business context |
| Simple churn = cancellation count | Net Revenue Retention (NRR) as primary health metric | 2025 SaaS standard | Expansion panel tracks net MRR (retained + expansion - lost) which is the NRR pattern |
| Fixed inactivity windows | Segment-specific thresholds | Ongoing | Deferred -- universal 14-day rule for now per user decision |

## Micro-Business Retention Best Practices

Research findings relevant to the user's explicit request for solopreneur best practices:

### Time-to-Value Benchmarks
- For infoproducts (courses, coaching, memberships), first engagement should happen within 7 days of purchase
- TTV < 3 days: Excellent activation (no intervention needed)
- TTV 3-7 days: Normal range
- TTV > 7 days: Slow activation -- triggers onboarding improvement tip
- Source: Industry consensus for product-led growth; onboarding dropoff rates of 30-50% concentrate in the first week

### Inactivity Threshold Calibration
- 14-day universal threshold is appropriate for micro-business infoproducts
- Rationale: courses and memberships expect weekly engagement; 2 weeks without activity is a strong churn predictor
- 43% of SMB customer losses occur in the first 90 days, making early inactivity detection critical
- The existing `INACTIVITY_CONFIG.inactive_days = 14` is well-calibrated

### Churn Rate Benchmarks
- SMB SaaS average monthly churn: 3-5%
- Above 5% monthly churn is critical for micro-businesses with small customer bases
- Above 3% monthly churn is a warning signal worth surfacing
- For a solopreneur with 50-200 customers, even 5% churn (2-10 customers/month) needs immediate attention

### User-Friendly Labels (decided in UI-SPEC)
- "Ingreso Recurrente Neto" instead of "Net MRR"
- "Valor Promedio por Cliente" instead of "Average LTV"
- "Tasa de Cancelacion" instead of "Churn Rate"
- Each with tooltip explaining in plain Spanish what the number means

## Renewal vs Upsell Classification Logic

**Decision (Claude's discretion):** Classify EXPANSION sales based on whether the same offer was previously purchased by the same customer.

```python
# Renewal: same customer + same offer_id + stage=EXPANSION
# Upsell/Cross-sell: same customer + different offer_id + stage=EXPANSION

# Alternative approach using metadata_info:
# If metadata_info contains event_name="subscription_cycle" -> renewal
# Otherwise -> upsell/cross-sell
```

The metadata_info approach is more reliable because the LifecycleService already stores `event_name` in sale metadata. However, a fallback to offer_id comparison handles manual EXPANSION entries that lack metadata. Use both: check metadata first, fall back to offer comparison.

## Channel Registry Entries

**Decision (Claude's discretion):** Add minimal channel entries since adoption/expansion are CRM-native (no external providers).

```python
# In STAGE_CHANNEL_MAP:
"adoption": [
    {"slug": "product-usage", "name": "Uso del Producto", "channel_type": "engagement", "source_label": "CRM", "provider_name": "internal"},
],
"expansion": [
    {"slug": "renewals", "name": "Renovaciones", "channel_type": "recurring", "source_label": "CRM", "provider_name": "internal"},
    {"slug": "upsell", "name": "Ventas Adicionales", "channel_type": "growth", "source_label": "CRM", "provider_name": "internal"},
],
```

Note: These stages don't use the ChannelRegistry connected/available pattern since all data comes from internal CRM. The entries exist for consistency with the registry pattern but won't drive "Configurar" badges.

## Open Questions

1. **Subscription identification from SaleModel**
   - What we know: SaleModel has `metadata_info` JSONB that can contain `event_name`. LifecycleService stores sale metadata.
   - What's unclear: Whether all EXPANSION sales consistently have metadata_info populated with event_name.
   - Recommendation: Use defensive coding -- check metadata_info first, fall back to offer_id duplicate check. Log cases where classification is ambiguous.

2. **MRR Calculation for Non-Subscription Offers**
   - What we know: "Net MRR" label implies monthly recurring revenue, but some offers are one-time upsells.
   - What's unclear: Whether one-time upsells should be included in the "Net MRR" KPI or excluded.
   - Recommendation: Include all EXPANSION revenue in the net figure. The label "Ingreso Recurrente Neto" is a simplification for the business owner -- they care about total post-sale revenue flow, not the strict SaaS definition. The tooltip can clarify: "Total de ingresos recibidos de clientes existentes menos cancelaciones."

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inside Docker container) |
| Config file | backend/pytest.ini or pyproject.toml |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py -x` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADO-01 | Adoption health cohort per offer | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_health_by_offer -x` | Wave 0 |
| ADO-02 | /metrics/adoption endpoint | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_endpoint.py -x` | Wave 0 |
| ADO-03 | TTV calculation | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_ttv_calculation -x` | Wave 0 |
| ADO-04 | Bottleneck detection for low health | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_bottleneck_low_health -x` | Wave 0 |
| EXP-01 | Expansion groups (retention, growth, churn) | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_expansion_groups -x` | Wave 0 |
| EXP-02 | /metrics/expansion endpoint | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_endpoint.py -x` | Wave 0 |
| EXP-03 | lifetime_value read for LTV average | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_ltv_average -x` | Wave 0 |
| EXP-04 | Churn rate calculation + bottleneck | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_churn_rate_bottleneck -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py tests/modules/analytics/test_expansion_metrics.py -x`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/analytics/test_adoption_metrics.py` -- covers ADO-01, ADO-03, ADO-04
- [ ] `tests/modules/analytics/test_adoption_endpoint.py` -- covers ADO-02
- [ ] `tests/modules/analytics/test_expansion_metrics.py` -- covers EXP-01, EXP-03, EXP-04
- [ ] `tests/modules/analytics/test_expansion_endpoint.py` -- covers EXP-02
- Existing `conftest.py` with `test_tenant_id`, `sample_offer_id`, `sample_customer_id` fixtures covers shared needs

## Sources

### Primary (HIGH confidence)
- Codebase: `backend/src/modules/analytics/application/services/metrics_service.py` -- MetricsService pattern for all 5 existing stages
- Codebase: `backend/src/modules/analytics/application/dto/sales_dto.py` -- most comprehensive DTO pattern (closest to Phase 9 needs)
- Codebase: `backend/src/modules/crm/infrastructure/models/customer_model.py` -- CustomerProfileModel fields (is_inactive, last_activity_at, first_conversion_at, lifetime_value)
- Codebase: `backend/src/modules/crm/infrastructure/models/sale_model.py` -- SaleModel fields (stage, status, offer_id, amount, currency, metadata_info)
- Codebase: `backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py` -- churn audit trail
- Codebase: `backend/src/modules/crm/domain/scoring.py` -- INACTIVITY_CONFIG.inactive_days = 14
- Codebase: `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx` -- frontend panel pattern
- Phase 9 UI-SPEC: `.planning/phases/09-stages-5-6-adoption-expansion/09-UI-SPEC.md` -- visual contract, copywriting, thresholds

### Secondary (MEDIUM confidence)
- [Vitally B2B SaaS Churn Benchmarks](https://www.vitally.io/post/saas-churn-benchmarks) -- 3-5% monthly churn for SMB SaaS
- [Gainsight Customer Health Scores](https://www.gainsight.com/blog/customer-health-scores/) -- health score methodology
- [SaaS User Activation Strategies](https://www.saasfactor.co/blogs/saas-user-activation-proven-onboarding-strategies-to-increase-retention-and-mrr) -- TTV and activation best practices

### Tertiary (LOW confidence)
- None. All findings verified against codebase or established industry benchmarks.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - identical stack to Phases 5-8, no new dependencies
- Architecture: HIGH - exact pattern replication from MetricsService/SalesDetail
- Pitfalls: HIGH - identified from actual codebase patterns and edge cases in existing queries
- Retention best practices: MEDIUM - web search findings consistent across multiple sources, calibrated for micro-business context

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable patterns, no external API dependencies)
