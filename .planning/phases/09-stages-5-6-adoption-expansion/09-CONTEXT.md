# Phase 9: Stages 5-6 Adoption & Expansion - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Build two post-sale retention panels: **Adopción** (Stage 5) showing customer health post-purchase — who is active, who is inactive, refund signals — and **Expansión** (Stage 6) showing revenue retention — MRR retained, upsell revenue, and churn losses. Backend endpoints `/metrics/adoption` and `/metrics/expansion` sourcing data from CRM customer_profiles, journey_events, sales, and lifecycle_transitions. Bottleneck alerts for high inactivity (churn predictor) and critical churn rate.

Stage 5 focuses on **product adoption and customer health** — are customers using what they bought?
Stage 6 focuses on **recurring revenue and growth** — is money being retained, expanded, or lost?

</domain>

<decisions>
## Implementation Decisions

### Adoption Panel Structure (Dual: Summary + Offer Drill-Down)
- **Top section**: Visual proportional health bar showing active vs inactive ratio (green/yellow segments)
- **Below health bar**: Offer-level cards — each offer the tenant sells gets its own card showing active/inactive cohort
- **Offer cards** (not ChannelRows) — each offer gets a distinct card/box for visual distinction, same concept as Sales panel
- Offers with zero customers in period are hidden
- Data source: CustomerProfileModel filtered by `lifecycle_stage = CUSTOMER` or beyond, grouped by the offer_id from their CONVERSION sale

### Adoption Header KPIs (3 Primary + 2 Secondary)
- **Primary row (3 KPIs)**: Clientes Activos | Clientes Inactivos | Salud % (active/total)
- **Secondary row (2 KPIs)**: TTV Promedio (Time-to-Value in days) | Devoluciones (count + amount refunded)
- Follows the 3-KPI header pattern from Phases 5-8, with secondary line extension

### Adoption Per-Offer Card Layout
- **Primary line**: Offer public_name + total customer count
- **Health breakdown**: Active count (green) + Inactive count (yellow) + health percentage
- **TTV**: Time-to-Value for that specific offer's customers
- Cards use visual health indicator (green/yellow proportion or badge)

### Adoption MiniFunnel
- Claude's discretion on whether to include MiniFunnel for Adoption
- If included, natural flow: Ventas (N) → Activos (M) = X% activation rate
- If omitted, the health bar + KPIs are sufficient for post-sale context

### Refunds / Devoluciones (Adoption Secondary KPI)
- Data source: `SaleModel.status == REFUNDED` — count + total refunded amount
- **Source-agnostic** — no hardcoded Shopify logic. Counts refunds regardless of source (Shopify, Stripe, manual, future sources)
- Refunds are a product health signal (adoption), NOT churn (expansion). Different concepts:
  - Refund = money returned for specific purchase
  - Churn = subscription cancellation (recurring revenue loss)
- Decoupled architecture ready for multiple refund sources in future milestones

### Visual Health Bar
- Horizontal proportional bar: green segment (active %) + yellow segment (inactive %)
- Positioned between header KPIs and offer card drill-down
- Shows absolute counts below the bar: "128 activos | 34 inactivos"

### Expansion Panel Structure (3 Groups + Offer Detail)
- **Three distinct groups**: Retención (MRR retained), Expansión (upsell/cross-sell revenue), Churn (MRR lost)
- **Each group has**: aggregate category header (total count + revenue) THEN offer-level breakdown rows below
- **Churn group**: red accent/border to signal negative metrics
- All monetary amounts in dual currency (tenant currency + USD conversion) — carried from Phase 8

### Expansion Header KPIs (3 KPIs)
- **MRR Neto**: retained + expansion - lost (net recurring revenue)
- **LTV Promedio**: average lifetime_value across active customers
- **Tasa Churn**: cancellations / total active subscriptions percentage
- **User-friendly labels** — plain Spanish names, NOT technical acronyms. Use tooltip hints to explain what each metric means (e.g., hover on "Ingreso Recurrente" shows "Dinero que recibes cada mes de suscripciones activas")
- Researcher should propose the most understandable labels for a micro-business owner / solopreneur

### Expansion MiniFunnel
- **Activos (128) → Expansión (23) = 18%** — shows upsell conversion rate among active customers
- Uses stage names consistent with the funnel chain

### Expansion Retención Group
- Aggregate: total renewals count + revenue + retention rate %
- Offer-level rows below: each subscription offer with its renewal count + revenue
- Data source: SaleModel with stage=EXPANSION + event_name indicating renewal (subscription_cycle)

### Expansion Expansión Group
- Aggregate: total upsell count + revenue + cross-sell count + revenue
- Offer-level rows below: each offer with upsell/cross-sell transactions
- Data source: SaleModel with stage=EXPANSION excluding renewals

### Expansion Churn Group
- Aggregate: cancellation count + MRR lost + churn rate %
- Offer-level rows below: which offers are losing subscribers
- Data source: LifecycleTransitionModel where to_stage=CHURNED + triggered_by=churn_event
- Red visual treatment always (churn is inherently negative)

### Time-to-Value Calculation
- **TTV = days from first_conversion_at to first journey_event after purchase**
- Universal calculation — any journey_event post-purchase counts as "activation"
- Works for all product types: course (first lesson viewed), coaching (first message), membership (first login)
- Displayed per-offer in cards + as average in secondary KPI
- **Researcher must investigate** micro-business / solopreneur best practices for TTV and adapt the calculation. User delegates everything to the system — must be understandable at a glance

### Active vs Inactive Definition
- **Universal 14-day rule** using existing `is_inactive` flag and `last_activity_at` on CustomerProfileModel
- Active = any journey_event in last 14 days
- Inactive = no events for 14+ days
- Applies to ALL customers regardless of product type (course, coaching, subscription)
- Threshold already configurable in INACTIVITY_CONFIG.inactive_days (Phase 3)
- Researcher calibrates threshold based on micro-business retention best practices

### Bottleneck Visualization — Adoption
- **Dual pattern**: panel-level banner + inline badge on worst-health offers
- Banner appears when overall health % drops below threshold (researcher calibrates, e.g., <70%)
- Inline badge on specific offer cards with health below threshold
- Yellow severity (warning, not critical — inactivity predicts churn but isn't churn yet)
- Context-aware tips based on data patterns

### Bottleneck Visualization — Expansion
- **Dual pattern**: panel-level banner + inline badge on Churn group
- Banner appears when churn rate exceeds 5% (EXP-04 requirement)
- **Red severity** (critical — actual revenue loss happening)
- Context-aware tips:
  - High churn + low TTV → "Mejora tu proceso de onboarding"
  - High churn + normal TTV → "Revisa la calidad y satisfacción de tu producto/servicio"
  - High inactivity in Adoption + high churn → "Tus clientes no están usando el producto antes de cancelar"
- Researcher investigates micro-business retention best practices to build context-aware tip library

### Currency Display
- Dual currency on all monetary amounts (carried from Phase 8)
- Tenant currency primary + USD conversion secondary
- Same formatting pattern as Sales panel

### Claude's Discretion
- Adoption MiniFunnel inclusion decision
- Exact offer card component design (spacing, shadows, health indicator styling)
- Health bar component implementation (CSS proportional bar vs chart library)
- User-friendly KPI label naming for Expansion metrics (after researcher investigates)
- Tooltip/hint content for technical metrics
- Context-aware tip library (after researcher investigates retention best practices)
- Bottleneck threshold calibration (after researcher investigates benchmarks)
- Renewal vs upsell classification logic from SaleModel data
- Channel registry entries for adoption/expansion stages
- Error/stale UX for post-sale specific scenarios
- Whether to show "Configurar" badge for unconnected post-sale channels (delivery, retention)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Analytics Pattern (Phase 5-8 reference)
- `backend/src/modules/analytics/api/metrics.py` — /metrics/capture, /metrics/nurturing, /metrics/opportunity, /metrics/sales endpoint patterns to follow
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/sales_dto.py` — SalesDetailDTO structure (most comprehensive: header KPIs, mini funnel, revenue groups, tier groups, offer cards, bottlenecks)
- `backend/src/modules/analytics/application/dto/opportunity_dto.py` — OpportunityDetailDTO with BottleneckDTO pattern
- `backend/src/modules/analytics/application/dto/capture_dto.py` — CaptureDetailDTO with MiniFunnelDTO pattern
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP (add "adoption" and "expansion" entries)

### CRM Data Sources (Core for Phase 9)
- `backend/src/modules/crm/infrastructure/models/customer_model.py` — CustomerProfileModel: lifecycle_stage, lifetime_value, is_inactive, last_activity_at, first_conversion_at, computed_traits
- `backend/src/modules/crm/infrastructure/models/customer_model.py` — JourneyEventModel: event_name, occurred_at, properties (TTV calculation source)
- `backend/src/modules/crm/infrastructure/models/sale_model.py` — SaleModel: stage (CONVERSION/EXPANSION), status (REFUNDED), amount, customer_id, offer_id, source
- `backend/src/modules/crm/infrastructure/models/lifecycle_transition_model.py` — LifecycleTransitionModel: from_stage, to_stage, triggered_by, occurred_at (churn audit trail)
- `backend/src/modules/crm/domain/enums.py` — LifecycleStage enum (CUSTOMER, CHURNED), SaleStage (CONVERSION, EXPANSION), SaleStatus (REFUNDED)

### Lifecycle & Inactivity Services
- `backend/src/modules/crm/application/services/lifecycle_service.py` — handle_sale_completed (CONVERSION/EXPANSION), handle_churn_event, reactivation logic
- `backend/src/modules/crm/application/services/inactivity_service.py` — Batch inactivity detection (14-day threshold), is_inactive flag, recovery logic
- `backend/src/modules/crm/domain/scoring.py` — INACTIVITY_CONFIG, DECAY_CONFIG thresholds

### Cross-Module Ports
- `backend/src/modules/analytics/domain/ports/connection_port.py` — ConnectionPort ABC pattern (reference for any new ports)
- `backend/src/modules/analytics/domain/ports/offer_read_port.py` — OfferReadPort ABC (reuse from Phase 8 for offer grouping)
- `backend/src/modules/offer/application/services/offer_read_port_impl.py` — OfferReadPortImpl (already implemented)

### Cost Service
- `backend/src/modules/analytics/application/services/stage_cost_service.py` — StageCostService (generic, reusable — no post-sale cost aggregation needed for this phase)

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/SalesDetail.tsx` — Latest detail panel with offer cards (closest pattern for Adoption)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/OpportunityDetail.tsx` — BottleneckBanner pattern
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/BottleneckBanner.tsx` — Shared bottleneck alert component
- `frontend/src/features/marketing-studio/hooks/useSalesDetail.ts` — Hook pattern for data fetching (useAuth + metricsApi)
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId, StageSummary types (add ADOPCION, EXPANSION)
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` — Mock data for development
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add ADOPCION and EXPANSION cases)

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OfferReadPort` + `OfferReadPortImpl`: Already built in Phase 8 — reuse for offer grouping in Adoption cards
- `MiniFunnelDTO`: Reuse from capture_dto.py for Expansion panel funnel
- `BottleneckDTO` + `BottleneckBanner.tsx`: Reuse for both Adoption (yellow) and Expansion (red) alerts
- `StageCostService`: Not needed for post-sale costs in this phase, but available
- `MetricsCache` with per-stage TTL: adoption/expansion stages use 300s default
- `EventBus` + `SaleCompletedEvent` + `ChurnEvent`: Already emitted — analytics can listen
- `SalesDetail.tsx` offer card pattern: Adapt for Adoption offer health cards
- VALUE_LEVEL_TO_TIER mapping: Reuse from Phase 8 if needed for tier grouping in Expansion

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- 3 header KPIs pattern (Phases 5-8)
- Mini funnel at panel top (Phases 5-8)
- Bottleneck banners with severity thresholds and context-aware tips (Phase 7-8)
- Cross-module port pattern: ABC in analytics, impl in source module (Phase 2, 8)
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks
- Dual currency formatting via Intl.NumberFormat (Phase 8)
- is_inactive batch detection via InactivityService (Phase 3)

### Integration Points
- `MetricsDashboard.tsx`: Add ADOPCION and EXPANSION stage routing (replace PlaceholderDetail)
- `StageSummary` mock data: Set `hasDetail: true` for ADOPCION and EXPANSION stages
- `metrics.py` router: Register `/metrics/adoption` and `/metrics/expansion` endpoints
- `STAGE_CHANNEL_MAP`: Add "adoption" and "expansion" entries (currently has stubs: "delivery", "retention", "referral")
- `analytics/application/dto/`: Add `adoption_dto.py` and `expansion_dto.py`
- `analytics/infrastructure/repositories/`: Add adoption and expansion repositories querying CRM data

</code_context>

<specifics>
## Specific Ideas

- "Agregale TTV y devoluciones" — user specifically wants Time-to-Value and Refunds visible in Adoption panel as secondary KPIs
- "En otro milestone habrá otras formas de registrar refunds por lo que debes desacoplar" — refund tracking must be source-agnostic, not hardcoded to Shopify. Multiple refund sources coming in future milestones
- "Busques en internet las mejores practicas y la adaptes para un microempresario y/o solopreneur que delegará todo a este sistema" — researcher MUST investigate micro-business/solopreneur best practices for TTV, inactivity thresholds, and retention metrics. User delegates everything to the system — everything must be understandable at a glance
- "Trata de poner nombres que entienda y/o usar hints de ayuda" — all metric labels must be in plain Spanish a micro-business owner understands. Technical terms (MRR, LTV, churn rate) need tooltip hints explaining what they mean
- Offer cards for Adoption (visual distinction per product, same concept as Sales panel)
- Context-aware bottleneck tips that change based on what the data shows (not static generic messages)
- Aggregate + offer drill-down in Expansion groups (category totals visible at group level, individual offers below)

</specifics>

<deferred>
## Deferred Ideas

- Configurable inactivity thresholds per offer type (course vs coaching vs subscription) — use universal 14-day rule for now
- Configurable bottleneck thresholds per tenant — use researched defaults
- Revenue trend indicators (vs previous period) — Phase 11 (Frontend Unification)
- Separate RefundEvent with reason codes — future milestone when multiple refund sources exist
- Product-type aware TTV calculation (different activation criteria per offer type) — future enhancement
- Post-sale cost tracking (support, hosting, retention tools) — not needed for this phase's metrics

</deferred>

---

*Phase: 09-stages-5-6-adoption-expansion*
*Context gathered: 2026-03-16*
