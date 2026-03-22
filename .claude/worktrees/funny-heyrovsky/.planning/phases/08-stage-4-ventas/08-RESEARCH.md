# Phase 8: Stage 4 Ventas - Research

**Researched:** 2026-03-16
**Domain:** Sales metrics dashboard — cross-module offer integration, revenue aggregation, CAC calculation
**Confidence:** HIGH

## Summary

Phase 8 builds the Sales (Ventas) detail panel for Stage 4 of the Growth Studio metrics dashboard. The phase has two main technical challenges: (1) cross-module integration with Offer Studio via an OfferReadPort ABC (following the established ConnectionPort pattern), and (2) revenue aggregation from the CRM `sales` table grouped by offer, tier, and sale stage (CONVERSION/EXPANSION).

The existing codebase provides strong patterns from Phases 5-7 that directly apply. The `SaleModel` already has `offer_id` (FK to `products`), `stage` (CONVERSION/EXPANSION), `amount`, `currency`, and `source` fields. The `OfferRepository` has `get_all_by_tenant()` and `get_by_id()` methods. The `StageCostService` is already generic and can aggregate costs across stages 0-3 for CAC calculation. Frontend follows React Query + mock fallback pattern established in all previous stages.

**Primary recommendation:** Follow the ConnectionPort ABC pattern exactly: define `OfferReadPort` in `analytics/domain/ports.py`, implement `OfferReadPortImpl` in `offer/application/services/`, inject into MetricsService. Query sales directly from `SaleModel` with SQLAlchemy 2.0, join nothing cross-module -- use offer data from the port for enrichment in the application layer.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Two primary groups**: Adquisicion (CONVERSION sales -- new customers) and Expansion (EXPANSION sales -- repeat/upsell)
- **Group header**: shows total revenue + customer count + percentage of total revenue
- **Within each group**: offers sub-grouped by simplified value_level tiers (4 tiers from 7 levels)
- **Simplified Value Level Tiers**: Low Ticket (level 1), Mid Ticket (level 2), High Ticket (levels 3+5+6), Recurrente (level 4), FREE (level 0) excluded
- **Offer rows rendered as cards** -- each offer gets its own card/box for visual distinction
- **Per-Offer Card Layout**: primary line (name + revenue + count), secondary line (source breakdown), third line (subscription new vs renewal, conditional)
- **Currency Display**: all monetary amounts in tenant's currency with USD conversion alongside
- **Header KPIs**: Revenue Total, Nuevos Clientes, CAC
- **Mini Funnel**: Oportunidades -> Ventas = X%
- **CAC Formula**: (Stage 0 + Stage 1 + Stage 2 + Stage 3 costs) / CONVERSION count
- **CAC incomplete data**: show asterisk + "Costos incompletos -- configura en Growth Settings"
- **Bottleneck types**: low_conversion_rate (SQL->Customer) and high_cac_ratio (CAC/AOV)
- **Offer Ladder Adaptability**: no hardcoded offer types in frontend, all groupings from backend DTO, value_level -> tier mapping in backend only, unknown levels default to high_ticket
- **Available (unconnected) channels** shown at bottom with "Configurar" badge
- **Empty states**: no offers -> link to Offer Studio, no sales -> show offer catalog with $0

### Claude's Discretion
- Exact offer card component design (spacing, shadows, border treatment)
- Exchange rate implementation approach (static config vs API lookup)
- OfferReadPort method signatures beyond get_offers_by_tenant() and get_offer_by_id()
- Subscription label naming per OfferType (after researcher investigates offer model and best practices)
- Bottleneck threshold calibration (after researcher investigates conversion and CAC benchmarks)
- Source breakdown formatting in secondary line
- Error/stale UX casuistry for sales-specific scenarios
- Value_level -> tier mapping for edge cases (ULTRA_HIGH, CORPORATE placement)

### Deferred Ideas (OUT OF SCOPE)
- Lead magnet tracking in Stage 1 Captura
- Revenue trend indicators (vs previous period) -- Phase 11
- Configurable bottleneck thresholds per tenant
- Offer Studio reengineering -- future milestone
- Exchange rate API integration -- start with static config
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VEN-01 | Detail panel showing sales broken down by Offer Ladder position using type_offers from Offer Studio | OfferReadPort cross-module pattern, SalesDetailDTO structure, frontend SalesDetail component with TierGroup/OfferCard |
| VEN-02 | Backend endpoint `/metrics/sales` with revenue tracking -- CONVERSION vs EXPANSION split | SaleModel already has `stage` field (CONVERSION/EXPANSION), SaleRepository.get_sales_by_date_range() exists, new SalesMetricsRepository aggregates by stage |
| VEN-03 | Subscription revenue separated into new subscriptions vs renewals | Sale metadata_info can carry subscription event type; PricingStructure.plan_type (ONE_TIME/SUBSCRIPTION/PAYMENT_PLAN) on Offer determines label |
| VEN-04 | Cross-module read of Offer Studio type_offers via shared service or read-only projection | OfferReadPort ABC in analytics/domain/ports.py, OfferReadPortImpl in offer/application/services/, follows ConnectionPort pattern exactly |
| VEN-05 | CAC calculated as Total investment (Stages 0-3) / Total new customers (CONVERSION) | StageCostService already generic, extend with get_total_stage_costs() aggregating across stages 0-3 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | `/metrics/sales` endpoint | Project standard |
| SQLAlchemy 2.0 | existing | Sales aggregation queries | Project standard, async |
| Pydantic v2 | existing | SalesDetailDTO, OfferReadDTO | Project standard |
| React Query | existing | `useSalesDetail` hook | 5-min staleTime pattern established |
| shadcn/Radix | existing | Accordion (TierGroup), Badge, Skeleton | UI-SPEC confirmed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | existing | RefreshCw icon for Recurrente tier | Per UI-SPEC |
| Redis | existing | MetricsCache with 300s TTL for sales stage | Established pattern |

No new dependencies required. Everything uses existing project stack.

## Architecture Patterns

### Recommended Project Structure

```
backend/src/modules/analytics/
  domain/
    ports.py                      # ADD: OfferReadPort ABC alongside ConnectionPort
  application/
    dto/
      sales_dto.py                # NEW: SalesDetailDTO, SalesHeaderKpisDTO, OfferSaleDTO, TierGroupDTO, RevenueGroupDTO
    services/
      metrics_service.py          # EXTEND: add get_sales_metrics() method
      stage_cost_service.py       # EXTEND: add get_total_costs_stages_0_to_3()
  infrastructure/
    repositories/
      sales_metrics_repository.py # NEW: aggregation queries on SaleModel

backend/src/modules/offer/
  application/
    services/
      offer_read_port_impl.py     # NEW: OfferReadPortImpl (implements OfferReadPort)

frontend/src/features/marketing-studio/
  types/metrics.ts                # EXTEND: SalesDetail types
  api/metrics-api.ts              # EXTEND: getSalesDetail()
  api/metrics-mock-data.ts        # EXTEND: MOCK_SALES_DETAIL
  hooks/useSalesDetail.ts         # NEW
  components/metrics-dashboard/
    detail-panels/SalesDetail.tsx  # NEW
    channel-widgets/OfferCard.tsx  # NEW
    channel-widgets/TierGroup.tsx  # NEW
    channel-widgets/RevenueGroupHeader.tsx  # NEW
    MetricsDashboard.tsx           # MODIFY: add VENTAS routing
```

### Pattern 1: OfferReadPort (Cross-Module ABC)

**What:** ABC defined in analytics domain, implemented in offer module. Same pattern as ConnectionPort/ConnectionPortImpl.
**When to use:** Any time analytics needs data from another bounded context.

```python
# In analytics/domain/ports.py (extend existing file)
from pydantic import BaseModel

class OfferReadDTO(BaseModel):
    """Lightweight read-only projection of Offer for analytics."""
    id: UUID
    tenant_id: UUID
    public_name: str
    offer_type: str          # OfferType.value string
    value_level: Optional[str] = None  # OfferValueLevel.value string
    pricing_type: Optional[str] = None  # "one_time" | "subscription" | "payment_plan"
    currency: str = "USD"

class OfferReadPort(ABC):
    @abstractmethod
    async def get_offers_by_tenant(self, tenant_id: UUID) -> List[OfferReadDTO]:
        """All active offers for a tenant (excludes ARCHIVED)."""
        ...

    @abstractmethod
    async def get_offer_by_id(self, offer_id: UUID) -> Optional[OfferReadDTO]:
        """Single offer by ID."""
        ...
```

```python
# In offer/application/services/offer_read_port_impl.py
class OfferReadPortImpl(OfferReadPort):
    def __init__(self, db: Session):
        self.db = db

    async def get_offers_by_tenant(self, tenant_id: UUID) -> List[OfferReadDTO]:
        # Query ProductModel directly, map to OfferReadDTO
        # Filter: tenant_id, status != ARCHIVED, deleted_at IS NULL
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == tenant_id,
            ProductModel.status != "archived",
        )
        result = await asyncio.to_thread(self.db.execute, stmt)
        models = result.scalars().all()
        return [self._to_dto(m) for m in models]

    def _to_dto(self, m: ProductModel) -> OfferReadDTO:
        # Extract primary pricing_type from pricing JSONB
        pricing_type = "one_time"
        if m.pricing:
            for p in m.pricing:
                if isinstance(p, dict) and p.get("plan_type") in ("subscription", "payment_plan"):
                    pricing_type = p["plan_type"]
                    break
        return OfferReadDTO(
            id=m.id,
            tenant_id=m.tenant_id,
            public_name=m.name,
            offer_type=m.type,
            value_level=getattr(m, 'offer_value_level', None) or m.value_level,
            pricing_type=pricing_type,
            currency=m.currency or "USD",
        )
```

### Pattern 2: Sales Metrics Aggregation

**What:** Query SaleModel grouped by stage, offer_id, source. Enrich with offer data from OfferReadPort.
**When to use:** `/metrics/sales` endpoint.

```python
# SalesMetricsRepository pattern
class SalesMetricsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_sales_summary(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[dict]:
        """Aggregate completed sales by stage, offer_id, source."""
        stmt = (
            select(
                SaleModel.stage,
                SaleModel.offer_id,
                SaleModel.source,
                SaleModel.currency,
                func.count(SaleModel.id).label("count"),
                func.sum(SaleModel.amount).label("total_revenue"),
                func.count(func.distinct(SaleModel.customer_id)).label("unique_customers"),
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.occurred_at >= start_date,
                SaleModel.occurred_at <= end_date,
            )
            .group_by(SaleModel.stage, SaleModel.offer_id, SaleModel.source, SaleModel.currency)
        )
        return self.db.execute(stmt).all()
```

### Pattern 3: Value Level to Tier Mapping (Backend Only)

**What:** Single mapping dict translating OfferValueLevel to simplified tier keys. Lives in backend, frontend receives pre-grouped data.

```python
# In sales_dto.py or a dedicated mapping module
# Well-documented mapping for future AI/dev maintenance
#
# TIER MAPPING: 7 OfferValueLevel values -> 4 display tiers
# This mapping is the SINGLE SOURCE OF TRUTH for how offers are grouped in the Sales panel.
# If Offer Studio adds new value_levels, add them here. Unknown levels default to "high_ticket".
#
# Why this simplification:
# - Business owners think in price ranges, not in 7 granular levels
# - "High Ticket" merges levels 3 (VIP/1:1), 5 (Ultra-High), and 6 (Corporate) because
#   they all represent premium, high-touch sales with similar sales processes
# - "Recurrente" is separated because recurring revenue has fundamentally different metrics
#   (new vs renewal split, MRR tracking)

VALUE_LEVEL_TO_TIER: Dict[str, str] = {
    "level_1_low_ticket": "low_ticket",
    "level_2_mid_ticket": "mid_ticket",
    "level_3_high_ticket": "high_ticket",
    "level_4_recurring": "recurrente",
    "level_5_ultra_high": "high_ticket",
    "level_6_corporate": "high_ticket",
}

TIER_DISPLAY_ORDER = ["low_ticket", "mid_ticket", "high_ticket", "recurrente"]
TIER_LABELS = {
    "low_ticket": "Low Ticket",
    "mid_ticket": "Mid Ticket",
    "high_ticket": "High Ticket",
    "recurrente": "Recurrente",
}

def get_tier_for_value_level(value_level: Optional[str]) -> str:
    """Map a value_level string to its display tier. Unknown levels default to high_ticket."""
    if not value_level:
        return "high_ticket"  # Safe fallback per CONTEXT.md
    return VALUE_LEVEL_TO_TIER.get(value_level, "high_ticket")
```

### Pattern 4: CAC Cross-Stage Aggregation

**What:** Extend StageCostService to aggregate total costs across stages 0-3.

```python
# Extend StageCostService
def get_total_funnel_investment(
    self,
    tenant_id: UUID,
    start_date: datetime,
    end_date: datetime,
) -> tuple[float, bool]:
    """Sum all pre-sale funnel investment (Stages 0-3).

    Returns: (total_cost, is_complete)
    - is_complete=False when any stage has zero cost data (likely unconfigured)
    """
    # Stage 0: ad spend from MetricAggregationModel (meta-ads, google-ads, tiktok-ads)
    # Stage 1: capture channel costs (platform + agency)
    # Stage 2: nurture costs (retargeting spend + automation tools)
    # Stage 3: opportunity costs (shopify, scheduling tools)
    all_costs = self.get_channel_costs(tenant_id)
    retargeting_spend = self.get_retargeting_spend(tenant_id, start_date, end_date)
    # ... aggregate
    total = sum(all_costs.values()) + sum(retargeting_spend.values())
    is_complete = len(all_costs) > 0  # at least some costs configured
    return total, is_complete
```

### Anti-Patterns to Avoid
- **Direct ORM join between analytics and offer modules:** Never `join(ProductModel)` from analytics queries. Use OfferReadPort to fetch offer data separately, then merge in application layer.
- **Hardcoded offer types in frontend:** All offer names, tiers, groupings come from the backend DTO. Frontend renders dynamically.
- **Hardcoded value_level -> tier mapping in frontend:** This mapping lives exclusively in backend. Frontend receives `tier_key` and `tier_label` in the DTO.
- **Importing offer domain enums in analytics:** Use plain strings (same as PROVIDER_TO_CHANNEL_TYPES pattern -- DDD boundary).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-module data access | Direct SQL join to products table | OfferReadPort ABC + impl | DDD boundary, Offer Studio reengineering coming |
| Cost aggregation | Custom per-stage cost queries | StageCostService (existing) | Already generic, reusable |
| Cache layer | New Redis keys | MetricsCache with "sales" stage | 300s TTL already configured |
| Frontend data fetching | Custom fetch + state | React Query `useQuery` | Established pattern, 5-min staleTime |
| Accordion UI | Custom collapse/expand | shadcn Accordion | Already in project |
| Bottleneck detection | Custom severity logic | BottleneckDTO (reuse from Phase 7) | Same dual visualization pattern |

**Key insight:** This phase is 90% pattern replication from Phases 5-7 with the novel element being OfferReadPort cross-module integration. The ConnectionPort pattern is the exact blueprint.

## Common Pitfalls

### Pitfall 1: Subscription New vs Renewal Detection
**What goes wrong:** No reliable way to distinguish subscription_create from subscription_cycle in current Sale entity.
**Why it happens:** SaleModel.metadata_info may or may not contain subscription event type. Sale.stage only distinguishes CONVERSION (first ever sale by customer) from EXPANSION (any repeat).
**How to avoid:** For VEN-03, use Sale.stage as the primary signal: if stage=CONVERSION and offer.pricing_type=subscription, it's a "new subscription". If stage=EXPANSION and same offer_id appears in customer's history, it's a "renewal". This approximation is sufficient for the dashboard. Store subscription event type in metadata_info when available (Shopify webhooks provide this).
**Warning signs:** If CONVERSION count on subscription offers seems too high, it means customers buying multiple different subscription products are each counted as CONVERSION (correct by business logic -- first purchase = new customer).

### Pitfall 2: Currency Mismatch Between Sales and Offers
**What goes wrong:** Sale.currency and Offer.currency may differ. A sale could be recorded in MXN while the offer is configured in USD.
**Why it happens:** Sale records capture actual transaction currency; offer defines list price currency.
**How to avoid:** Use Sale.currency as the authoritative currency for revenue amounts (it represents actual money received). For dual display, apply exchange rate to convert to USD. Tenant's "home currency" should come from tenant settings or the most common Sale.currency.
**Warning signs:** Revenue totals that seem unreasonably high (MXN amounts displayed without currency label).

### Pitfall 3: Offer Studio Reengineering Fragility
**What goes wrong:** Direct coupling to Offer domain entities breaks when Offer Studio is reengineered.
**Why it happens:** User explicitly warned "probablemente como siguiente milestone hagamos toda una reingenieria".
**How to avoid:** OfferReadPort returns OfferReadDTO (minimal projection), not the full Offer domain entity. If offer table schema changes, only OfferReadPortImpl needs updating. Analytics never sees Offer entity directly.
**Warning signs:** Any import from `src.modules.offer.domain` in analytics module (except through the port pattern).

### Pitfall 4: SaleModel Uses Legacy Query Style
**What goes wrong:** SaleRepository uses `db.query(SaleModel)` (SQLAlchemy 1.x style) instead of `select(SaleModel)` (2.0 style).
**Why it happens:** CRM module was written earlier.
**How to avoid:** New SalesMetricsRepository in analytics module MUST use SQLAlchemy 2.0 `select()` syntax. Don't copy SaleRepository's query style.
**Warning signs:** `db.query(...)` in any new code.

### Pitfall 5: ProductModel Column Name for value_level
**What goes wrong:** ProductModel stores value_level in column named `offer_value_level` (aliased): `Column("offer_value_level", String)`.
**Why it happens:** Column alias in SQLAlchemy model.
**How to avoid:** When querying ProductModel directly in OfferReadPortImpl, reference `ProductModel.value_level` (the Python attribute name), not the column name. SQLAlchemy handles the mapping.
**Warning signs:** Empty value_level in all OfferReadDTOs.

## Code Examples

### SalesDetailDTO Structure (Backend)

```python
# Source: Follows OpportunityDetailDTO pattern from Phase 7
from pydantic import BaseModel
from typing import List, Optional

class OfferSaleDTO(BaseModel):
    """Single offer's sales data within a tier group."""
    offer_id: str
    public_name: str
    offer_type: str
    pricing_type: str  # "one_time" | "subscription" | "payment_plan"
    total_revenue: float
    sales_count: int
    currency: str
    usd_revenue: Optional[float] = None  # converted amount
    source_breakdown: dict  # {"SHOPIFY": 60, "MANUAL": 15, "API": 5}
    # Subscription split (only for subscription/payment_plan offers)
    new_subscriptions: Optional[int] = None
    new_subscription_revenue: Optional[float] = None
    renewals: Optional[int] = None
    renewal_revenue: Optional[float] = None

class TierGroupDTO(BaseModel):
    """Group of offers in same value_level tier."""
    tier_key: str        # "low_ticket" | "mid_ticket" | "high_ticket" | "recurrente"
    tier_label: str      # "Low Ticket" | "Mid Ticket" | "High Ticket" | "Recurrente"
    offers: List[OfferSaleDTO]

class RevenueGroupDTO(BaseModel):
    """Top-level group: Adquisicion or Expansion."""
    group_key: str       # "adquisicion" | "expansion"
    group_label: str     # "Adquisicion" | "Expansion"
    total_revenue: float
    total_revenue_usd: Optional[float] = None
    customer_count: int
    revenue_percentage: float  # of total revenue
    currency: str
    tiers: List[TierGroupDTO]

class SalesHeaderKpisDTO(BaseModel):
    total_revenue: float
    total_revenue_usd: Optional[float] = None
    currency: str
    new_customers: int  # CONVERSION count
    cac: Optional[float] = None
    cac_incomplete: bool = False  # True when cost data missing

class SalesDetailDTO(BaseModel):
    header_kpis: SalesHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Oportunidades -> Ventas
    adquisicion: RevenueGroupDTO
    expansion: RevenueGroupDTO
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### Frontend SalesDetail Type

```typescript
// Source: Follows OpportunityDetail type pattern
export interface OfferSaleData {
  offerId: string;
  publicName: string;
  offerType: string;
  pricingType: 'one_time' | 'subscription' | 'payment_plan';
  totalRevenue: number;
  salesCount: number;
  currency: string;
  usdRevenue: number | null;
  sourceBreakdown: Record<string, number>;
  newSubscriptions: number | null;
  newSubscriptionRevenue: number | null;
  renewals: number | null;
  renewalRevenue: number | null;
}

export interface TierGroupData {
  tierKey: string;
  tierLabel: string;
  offers: OfferSaleData[];
}

export interface RevenueGroupData {
  groupKey: 'adquisicion' | 'expansion';
  groupLabel: string;
  totalRevenue: number;
  totalRevenueUsd: number | null;
  customerCount: number;
  revenuePercentage: number;
  currency: string;
  tiers: TierGroupData[];
}

export interface SalesHeaderKpis {
  totalRevenue: number;
  totalRevenueUsd: number | null;
  currency: string;
  newCustomers: number;
  cac: number | null;
  cacIncomplete: boolean;
}

export interface SalesDetail {
  headerKpis: SalesHeaderKpis;
  miniFunnel: MiniFunnelData;
  adquisicion: RevenueGroupData;
  expansion: RevenueGroupData;
  bottlenecks: BottleneckData[];
  period: string;
  lastUpdated?: string;
}
```

### Bottleneck Threshold Calibration

```python
# Source: Industry benchmarks for creator economy / B2C digital products

# Low Conversion Rate: SQL -> Customer
# B2C creator economy close rates: 15-30% typical
# SaaS sales-qualified close: 20-30%
# E-commerce cart-to-purchase: 20-40%
# Conservative threshold for mixed creator business:
LOW_CONVERSION_THRESHOLDS = {
    "normal": 20.0,    # >= 20% is healthy
    "warning": 10.0,   # 10-20% needs attention
    "critical": 10.0,  # < 10% is critical
}

# High CAC Ratio: CAC / AOV
# Standard: 3:1 LTV:CAC ratio is healthy
# Without full LTV data, AOV as proxy:
# CAC < 33% of AOV -> healthy (3:1)
# CAC 33-50% of AOV -> warning (2:1)
# CAC > 50% of AOV -> critical (less than 2:1)
HIGH_CAC_THRESHOLDS = {
    "normal": 0.33,    # CAC < 33% of AOV
    "warning": 0.50,   # CAC 33-50% of AOV
    "critical": 0.50,  # CAC > 50% of AOV
}
```

### Exchange Rate: Static Config Approach

```python
# Static exchange rates stored in tenant settings or a simple config table.
# Per CONTEXT.md: "start with static config, future enhancement" for API lookup.
#
# Approach: tenant's Sale records already contain currency field.
# Use a simple dict mapping or tenant_settings.exchange_rate_to_usd field.

DEFAULT_EXCHANGE_RATES = {
    "USD": 1.0,
    "MXN": 0.058,  # ~17.2 MXN per USD
    "EUR": 1.08,
    "COP": 0.00024,
    "ARS": 0.0011,
    "BRL": 0.19,
}

def convert_to_usd(amount: float, currency: str) -> Optional[float]:
    """Convert amount to USD using static rates. Returns None if rate unknown."""
    rate = DEFAULT_EXCHANGE_RATES.get(currency)
    if rate is None:
        return None
    return round(amount * rate, 2)
```

### Subscription Label Resolution

```python
# Source: Derived from PaymentPlanType enum and OfferType context
# Per UI-SPEC subscription labels:

SUBSCRIPTION_LABELS = {
    "subscription": {
        "new_label": "nuevas suscripciones",
        "renewal_label": "renovaciones",
    },
    "payment_plan": {
        "new_label": "nuevos planes",
        "renewal_label": "cuotas cobradas",
    },
    "one_time": None,  # No split for one-time purchases
}

# For Level 4 Recurring offers (MONTHLY_RETAINER, PRODUCTIZED_SERVICE, etc.):
# These are services, not subscriptions, so use "contratos" labels
RECURRING_SERVICE_TYPES = {
    "productized_service", "ecommerce_development",
    "monthly_retainer", "performance_rev_share",
}

def get_subscription_labels(pricing_type: str, offer_type: str) -> Optional[dict]:
    """Get new/renewal labels based on pricing type and offer type."""
    if pricing_type == "one_time":
        return None
    if offer_type in RECURRING_SERVICE_TYPES:
        return {"new_label": "nuevos contratos", "renewal_label": "renovaciones"}
    return SUBSCRIPTION_LABELS.get(pricing_type)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct ORM joins across modules | Port/Adapter ABC pattern | Phase 2 (ConnectionPort) | DDD boundary preservation |
| Hardcoded channel lists | ChannelRegistry + dynamic rendering | Phase 2 | Extensible without code changes |
| Per-stage cost services | Generic StageCostService | Phase 6 | Reusable for CAC aggregation |
| SQLAlchemy 1.x `db.query()` | SQLAlchemy 2.0 `select()` | Project standard | New code must use 2.0 syntax |

**Deprecated/outdated:**
- SaleRepository.get_sales_by_date_range(): Uses 1.x query style. New sales aggregation queries in SalesMetricsRepository should use 2.0 style.

## Open Questions

1. **Subscription renewal detection accuracy**
   - What we know: Sale.stage (CONVERSION/EXPANSION) distinguishes first-ever vs repeat customers. Offers have pricing_type.
   - What's unclear: For a customer who buys multiple different subscription products, each first purchase of a new product is CONVERSION (correct by CRM logic). The renewal split is an approximation based on EXPANSION + same offer_id in history.
   - Recommendation: Accept approximation for v1. Shopify/Stripe webhooks can provide precise subscription_create vs subscription_cycle in metadata_info for future refinement.

2. **Tenant home currency**
   - What we know: Sale.currency stores actual transaction currency. Offer.currency stores list price currency.
   - What's unclear: Where tenant's "preferred display currency" is stored. No tenant_settings table was found with currency preference.
   - Recommendation: Use the most common Sale.currency for the tenant as their display currency. If no sales exist, fall back to "USD". Could also add a currency field to tenant config in future.

3. **Stage 0-3 cost completeness**
   - What we know: StageCostService queries channel_cost_settings and MetricAggregationModel.
   - What's unclear: Whether all 4 stages have consistent cost tracking. Stage 0 uses ad spend from ETL; Stage 1 uses manual + automatic costs; Stages 2-3 are partially configured.
   - Recommendation: Sum whatever costs are available. Show asterisk on CAC when total is $0 or any stage returns zero (heuristic for "unconfigured").

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend), n/a (frontend -- no test infrastructure yet) |
| Config file | pytest.ini or pyproject.toml in backend |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/test_sales_metrics.py -x` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VEN-01 | Sales DTO groups offers by tier within CONVERSION/EXPANSION | unit | `pytest tests/test_sales_dto.py -x` | No -- Wave 0 |
| VEN-02 | /metrics/sales returns grouped revenue with stage split | integration | `pytest tests/test_sales_endpoint.py -x` | No -- Wave 0 |
| VEN-03 | Subscription offers show new vs renewal split | unit | `pytest tests/test_subscription_split.py -x` | No -- Wave 0 |
| VEN-04 | OfferReadPort returns offer data without cross-module import | unit | `pytest tests/test_offer_read_port.py -x` | No -- Wave 0 |
| VEN-05 | CAC = stages 0-3 costs / CONVERSION count | unit | `pytest tests/test_cac_calculation.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/ -x --tb=short`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_sales_metrics.py` -- covers VEN-01, VEN-02, VEN-03
- [ ] `tests/test_offer_read_port.py` -- covers VEN-04
- [ ] `tests/test_cac_calculation.py` -- covers VEN-05
- [ ] Test fixtures for SaleModel, ProductModel with tenant_id

## Sources

### Primary (HIGH confidence)
- `backend/src/modules/crm/domain/sale.py` -- Sale entity with stage, offer_id, amount, currency, source
- `backend/src/modules/crm/infrastructure/models/sale_model.py` -- SaleModel with FK to products, CONVERSION/EXPANSION enum
- `backend/src/modules/crm/application/services/sale_service.py` -- CONVERSION/EXPANSION detection logic
- `backend/src/modules/offer/domain/offer.py` -- Offer entity with OfferType, OfferValueLevel, PricingStructure
- `backend/src/modules/offer/domain/enums.py` -- Full enum definitions (7 value levels, 23 offer types)
- `backend/src/modules/offer/infrastructure/repositories/offer_repository.py` -- get_all_by_tenant(), get_by_id()
- `backend/src/modules/offer/infrastructure/models/product_model.py` -- ProductModel (table: products)
- `backend/src/modules/analytics/domain/ports.py` -- ConnectionPort ABC pattern
- `backend/src/modules/connections/application/services/connection_port_impl.py` -- ConnectionPortImpl reference
- `backend/src/modules/analytics/application/services/stage_cost_service.py` -- Generic StageCostService
- `backend/src/modules/analytics/application/dto/opportunity_dto.py` -- OpportunityDetailDTO, BottleneckDTO
- `backend/src/modules/analytics/application/services/channel_registry.py` -- STAGE_CHANNEL_MAP["sales"]
- `backend/src/modules/analytics/api/metrics.py` -- Endpoint registration pattern
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx` -- Panel layout pattern
- `frontend/src/features/marketing-studio/types/metrics.ts` -- Type definitions
- `frontend/src/features/marketing-studio/api/metrics-api.ts` -- API client with mock fallback
- `frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts` -- React Query hook pattern
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` -- Stage routing
- `.planning/phases/08-stage-4-ventas/08-UI-SPEC.md` -- Visual contract, bottleneck thresholds, copy
- `.planning/phases/08-stage-4-ventas/08-CONTEXT.md` -- Locked decisions

### Secondary (MEDIUM confidence)
- Bottleneck thresholds (20% conversion, 33% CAC/AOV) -- based on SaaS/creator economy industry benchmarks documented in UI-SPEC research

### Tertiary (LOW confidence)
- Static exchange rates -- approximate values, need periodic update or future API integration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are project-existing, no new dependencies
- Architecture: HIGH -- OfferReadPort follows exact ConnectionPort pattern from Phase 2
- Pitfalls: HIGH -- verified against actual codebase (SaleModel fields, ProductModel column aliases, SaleRepository query style)
- Bottleneck thresholds: MEDIUM -- industry benchmarks, not project-specific validation
- Exchange rates: LOW -- static approximations, explicitly deferred to future enhancement

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable -- no external API dependencies, all internal patterns)
