# Phase 8: Stage 4 Ventas - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Sales detail panel showing total revenue broken down by offer type, with clear separation of new vs recurring money. Two primary groups: Adquisicion (CONVERSION — new customers) and Expansion (EXPANSION — repeat/upsell). Within each group, offers are sub-grouped by simplified value_level tiers (Low Ticket, Mid Ticket, High Ticket, Recurrente) and rendered as cards showing the tenant's actual offers from Offer Studio. Backend `/metrics/sales` endpoint with revenue tracking, Offer Ladder integration via OfferReadPort ABC, and CAC calculation aggregating Stages 0-3 investment. Bottleneck banners for low conversion rate and high CAC ratio.

Stage 4 focuses exclusively on **completed sales and revenue** — money that actually came in. Purchase intent signals (checkout-init, abandoned-cart, meetings) belong in Stage 3 (Oportunidad).

</domain>

<decisions>
## Implementation Decisions

### Channel Grouping (Hybrid: Revenue Type + Offer Breakdown)
- **Two primary groups**: Adquisicion (CONVERSION sales — new customers) and Expansion (EXPANSION sales — repeat/upsell)
- **Group header**: shows total revenue + customer count + percentage of total revenue (e.g., "Adquisicion — $85,000 (74%) — 138 clientes")
- **Within each group**: offers sub-grouped by simplified value_level tiers
- **Offer rows rendered as cards** — each offer gets its own card/box for visual distinction
- Available (unconnected) channels shown at bottom with "Configurar" badge

### Simplified Value Level Tiers (4 tiers from 7 levels)
- **Low Ticket**: value_level 1 (TRIPWIRE, SELF_PACED_COURSE, PAID_NEWSLETTER_SUBSCRIPTION, PHYSICAL_MERCH)
- **Mid Ticket**: value_level 2 (HYBRID_MENTORSHIP, COHORT_BASED_COURSE, GROUP_COACHING_PROGRAM)
- **High Ticket**: value_levels 3 + 5 + 6 (VIP_DAY, 1:1_MENTORING, DEEP_DIVE_AUDIT, MASTERMIND, LUXURY_RETREAT, CORPORATE_TRAINING, etc.)
- **Recurrente**: value_level 4 (PRODUCTIZED_SERVICE, ECOMMERCE_DEVELOPMENT, MONTHLY_RETAINER, PERFORMANCE_REV_SHARE)
- **FREE (level 0) excluded** — lead magnets don't generate revenue, tracked in Stage 1 (Captura)
- Empty tiers (no sales in period) are hidden. Tiers with unsold offers show those offers with $0 at bottom of tier group

### Per-Offer Card Layout
- **Primary line**: Offer public_name + total revenue + sales count (e.g., "Curso Intensivo — $45,000 — 120 ventas")
- **Secondary line**: Source breakdown showing WHERE sales closed (e.g., "Shopify: 60 | Agent: 15 | Manual: 5")
- Sales Agent source: appears in breakdown only when it has real sales data. If no agent sales exist, source line shows only Shopify + Manual (no "Proximamente" badge needed — it's a data filter, not a channel)
- **Subscription offers**: inline new vs renewal split on a third line (e.g., "45 nuevas ($13,500) | 15 renovaciones ($4,500)"). Exact labels depend on OfferType — researcher must review offer model and propose best-practice labels per type

### Currency Display
- All monetary amounts displayed in **tenant's currency** with USD conversion shown alongside
- Format: "$45,000 MXN (~$2,500 USD)" or similar dual-display pattern
- If tenant's currency IS USD, no conversion needed
- Exchange rate handling: Claude's discretion on implementation (static config vs API)

### Empty States
- **No offers configured**: Friendly empty state "Configura tu Offer Ladder para ver ventas por producto" with link to Offer Studio
- **No sales in period**: Show offer catalog from Offer Studio with $0 values
- **Unsold offers**: Appear at bottom of their tier group with "$0 — 0 ventas"

### Header KPIs (3 KPIs)
- **Revenue Total**: Combined Adquisicion + Expansion revenue (tenant currency + USD)
- **Nuevos Clientes**: CONVERSION count (new customers acquired in period)
- **CAC**: Customer Acquisition Cost = Total Stages 0-3 investment / CONVERSION count

### Mini Funnel
- **Oportunidades (850) → Ventas (450) = 52.9%**
- Uses stage names (Oportunidades/Ventas) rather than lifecycle labels (SQLs/Clientes)
- Continues funnel chain: Stage 1 (Visitors→Leads), Stage 2 (Leads→MQLs), Stage 3 (MQLs→SQLs), Stage 4 (Oportunidades→Ventas)

### CAC Calculation (VEN-05)
- **Formula**: CAC = (Stage 0 spend + Stage 1 costs + Stage 2 costs + Stage 3 costs) / CONVERSION count
- Uses StageCostService to aggregate all pre-sale funnel investment
- Stage 0: ad platform spend (Meta/Google/TikTok APIs — automatic)
- Stage 1: capture channel costs (platform + agency + LLM — manual + automatic)
- Stage 2: nurturing costs (retargeting spend + automation tools — automatic + manual)
- Stage 3: opportunity costs (Shopify, scheduling tools — manual)
- If any stage cost data is missing, CAC shows with asterisk and note "Costos incompletos — configura en Growth Settings"

### Bottleneck Visualization (Dual: Banner + Inline)
- **Two bottleneck types for Stage 4**:
  1. **Low conversion rate**: SQL→Customer conversion below threshold
     - Researcher to calibrate with industry best practices
     - Tip: "Baja conversion de oportunidades a ventas — revisa tu proceso de cierre"
  2. **High CAC ratio**: CAC exceeds threshold relative to AOV (e.g., CAC > 50% of AOV)
     - Researcher to calibrate with SaaS/creator economy benchmarks
     - Tip: "Tu costo de adquisicion es alto respecto al ticket promedio — optimiza tu funnel"
- Same dual visualization as Phase 7: panel-level banner + inline badge
- Multiple banners can appear if both thresholds are crossed

### Offer Ladder Adaptability (CRITICAL)
- **Offer Studio is actively evolving** — OfferTypes, xxxService groupings, and value_levels will change
- Sales panel must render dynamically based on whatever offers exist in DB
- **No hardcoded offer types in frontend** — all offer names, tiers, and groupings come from backend DTO
- Value_level → tier mapping lives in backend (single place to update when levels change)
- Well-structured comments in code explaining the mapping so future AI/dev knows how to update
- If a new value_level is added, it should fall into "High Ticket" by default (safe fallback)

### Revenue Trends
- Deferred to Phase 11 (Frontend Unification & Dashboard Polish)
- No period comparison or trend arrows in this phase

### Claude's Discretion
- Exact offer card component design (spacing, shadows, border treatment)
- Exchange rate implementation approach (static config vs API lookup)
- OfferReadPort method signatures beyond get_offers_by_tenant() and get_offer_by_id()
- Subscription label naming per OfferType (after researcher investigates offer model and best practices)
- Bottleneck threshold calibration (after researcher investigates conversion and CAC benchmarks)
- Source breakdown formatting in secondary line
- Error/stale UX casuistry for sales-specific scenarios
- Value_level → tier mapping for edge cases (ULTRA_HIGH, CORPORATE placement)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Analytics Pattern (Phase 5-7 reference)
- `backend/src/modules/analytics/api/metrics.py` — /metrics/capture, /metrics/nurturing, /metrics/opportunity endpoint patterns to follow
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/opportunity_dto.py` — OpportunityDetailDTO structure (header KPIs, mini funnel, groups, bottlenecks)
- `backend/src/modules/analytics/application/dto/capture_dto.py` — CaptureDetailDTO with TrafficGroupDTO pattern
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP["sales"] (currently sales-agent + shopify)

### Cost Service
- `backend/src/modules/analytics/application/services/stage_cost_service.py` — StageCostService (generic, reusable — extend for CAC aggregation across stages 0-3)

### CRM & Sales Domain
- `backend/src/modules/crm/domain/sale.py` — Sale entity with CONVERSION/EXPANSION stage, amount, source, offer_id
- `backend/src/modules/crm/application/services/sale_service.py` — SaleService.create_sale() with CONVERSION/EXPANSION detection (previous sales count)
- `backend/src/modules/crm/domain/events.py` — SaleCompletedEvent with sale_id, customer_id, stage, amount, offer_id
- `backend/src/modules/crm/infrastructure/repositories/sale_repository.py` — get_sales_by_date_range(), count_sales_by_customer()

### Offer Studio (Cross-Module Read)
- `backend/src/modules/offer/domain/offer.py` — Offer entity: OfferType enum (21 types), OfferValueLevel (7 levels), DeliveryModel (DIY/DWY/DFY/HYBRID), PricingStructure (ONE_TIME/SUBSCRIPTION/PAYMENT_PLAN)
- `backend/src/modules/offer/infrastructure/models/` — Offer ORM models (for OfferReadPort implementation reference)
- `backend/src/modules/offer/infrastructure/repositories/` — Existing repository methods (reference for port implementation)

### ConnectionPort Pattern (Reference for OfferReadPort)
- `backend/src/modules/analytics/domain/ports/connection_port.py` — ConnectionPort ABC definition pattern
- `backend/src/modules/connections/application/services/connection_port_impl.py` — ConnectionPortImpl lives in connections module (same pattern: OfferReadPortImpl lives in offer module)

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx` — Latest detail panel pattern (header KPIs, mini funnel, bottleneck banners, channel groups)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/NurtureDetail.tsx` — Alternative reference
- `frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts` — Hook pattern for data fetching
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId, StageSummary types
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add VENTAS case)

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TrafficGroupDTO` + `ChannelMetricDTO`: Reusable for offer-based groups (adapt channels → offers)
- `BottleneckDTO`: Reuse from Phase 7 for conversion rate and CAC bottleneck banners
- `MiniFunnelDTO`: Reuse pattern (Oportunidades → Ventas)
- `StageCostService`: Extend for CAC cross-stage aggregation
- `EventBus` + `SaleCompletedEvent`: Already emitted by SaleService — analytics can listen for real-time updates
- `MetricsCache` with per-stage TTL: sales stage uses 300s default
- `OpportunityDetail.tsx` + `ChannelGroup` + `ChannelRow`: Frontend pattern ready for adaptation (offer cards instead of channel rows)
- `ConnectionPort` ABC pattern: Reference for building OfferReadPort

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- Multi-metric rows with secondary lines (Phases 4-7) — adapt for source breakdown
- 3 header KPIs pattern (Phases 5-7)
- Mini funnel at panel top (Phases 5-7)
- Bottleneck banners with severity thresholds (Phase 7)
- Cross-module port pattern: ConnectionPort ABC in analytics, impl in connections (Phase 2)
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks

### Integration Points
- `MetricsDashboard.tsx`: Add `activeStage === 'VENTAS' ? <SalesDetail /> : ...` routing
- `StageSummary` mock data: Set `hasDetail: true` for VENTAS stage
- `metrics.py` router: Register new `/metrics/sales` endpoint
- `STAGE_CHANNEL_MAP["sales"]`: May need expansion or adaptation for offer-based grouping
- `analytics/domain/ports/`: Add `offer_read_port.py` (OfferReadPort ABC)
- `offer/application/services/`: Add `offer_read_port_impl.py` (implementation)
- Dependency injection: Wire OfferReadPort in MetricsService or SalesMetricsRepository

</code_context>

<specifics>
## Specific Ideas

- "Cada offer debe ser un cuadrado o un card" — offers rendered as distinct cards, not generic rows. UX must be good
- "Debes ver la forma de que al momento de mostrar los productos no se rompa cuando creemos un nuevo offertype o un nuevo service o un nuevo nivel" — dynamic rendering from DB, no hardcoded offer types. Well-structured comments for future AI/dev
- "Todo en la moneda del tenant pero siempre acompanado de su conversion a dolares" — dual currency display on all monetary amounts
- "Revisa bien este detalle al momento de la revision del codigo para que entiendas mejor y me propongas algo de acuerdo a las mejores practicas del mercado" — subscription renewal labels depend on OfferType, researcher must investigate and propose
- Lead magnets (FREE tier) excluded from Stage 4 — they belong in the funnel stage that corresponds to their engagement (Stage 1 Captura for downloads/signups)
- Offer Studio xxxService groupings and value_levels are actively evolving — the sales panel must be resilient to these changes
- "Probablemente como siguiente milestone hagamos toda una reingenieria" — Offer Studio reengineering coming, so minimal coupling is critical

</specifics>

<deferred>
## Deferred Ideas

- Lead magnet tracking (downloads, signups) in Stage 1 Captura — free offers don't generate revenue but engagement should be tracked in the appropriate funnel stage
- Revenue trend indicators (vs previous period) — Phase 11 (Frontend Unification)
- Configurable bottleneck thresholds per tenant — use researched defaults for now
- Offer Studio reengineering — future milestone, current phase must survive it
- Exchange rate API integration — start with static config, future enhancement

</deferred>

---

*Phase: 08-stage-4-ventas*
*Context gathered: 2026-03-16*
