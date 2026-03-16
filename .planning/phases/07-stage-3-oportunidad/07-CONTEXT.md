# Phase 7: Stage 3 Oportunidad - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Opportunity detail panel showing the sales pipeline: who is about to buy and where friction is causing drop-off. Three channel groups: Checkout (Shopify checkout-init, abandoned-cart), Payment Links (Sales Agent payment links + landing page checkout placeholder), and Qualification (meetings booked via scheduling module). Backend `/metrics/opportunity` endpoint tracking SQL pipeline from checkout initiations and meeting bookings. Bottleneck banners for high abandoned-cart and no-show ratios. Shopify dev store with test orders for development (app pending approval).

Stage 3 focuses exclusively on **purchase intent signals** — people actively trying to buy or qualifying for high-ticket offers. Actual completed sales belong in Stage 4 (Ventas).

</domain>

<decisions>
## Implementation Decisions

### Channel Grouping (3 Groups)
- **Checkout**: checkout-init (Shopify) + abandoned-cart (Shopify). Tracks web transactional friction
- **Payment Links**: link-enviado (Sales Agent sends payment links) + checkout-lp (landing page checkout — "Proximamente" badge for now). Extensible design for future payment gateways (MercadoPago, PayPal)
- **Qualification**: meeting-booked (scheduling module). Tracks high-ticket qualification pipeline
- Available (unconnected) channels shown at bottom with "Configurar" badge

### Per-Channel Metrics
- Each channel row shows: **count + monetary value (where applicable) + conversion from Stage 2**
- Checkout Initiated: count + total cart value ($) + "de X MQLs = Y%"
- Abandoned Cart: count + abandoned value ($) + "X% del checkout" (abandonment ratio)
- Payment Link Sent: count + total link value ($) + "de X MQLs = Y%"
- Meetings Booked: 24 reuniones + secondary lines: "18 completadas (75%)", "3 no-show (12.5%)", "3 reprogramadas" + "de X MQLs = Y%"
- Meeting data must show: total booked, completed (star metric), no-shows, rescheduled count, attendance rate, no-show rate

### Mini Funnel & Header KPIs
- Mini funnel: **MQLs (210) → SQLs (69) = 32.9%**
- Header KPIs: **Total SQLs | Conversion Rate (MQL→SQL) | Cost per SQL** (3 KPIs, consistent with Stage 1-2)

### Shopify Test Data Strategy
- Shopify connector already built, app pending Shopify approval
- Use **Shopify development store** (free) with test orders for development
- Register webhook topics: `checkouts/create`, `checkouts/update`, `orders/create`
- Generate test orders via Shopify Admin API — real webhook structure, real event flow
- Use **Shopify Dev MCP** (`mcp__shopify-dev-mcp__*`) during development for API queries, GraphQL validation, webhook payload reference
- Researcher must investigate Shopify dev store setup and test order generation best practices

### Shopify Webhook Handler
- **Real-time processing**: webhook → parse event → find/create CustomerProfile → create JourneyEvent → EventBus.publish → scoring → stage transition
- Profile matching: **match by email, create if missing** — use CustomerService.identify(). Direct Shopify buyers who skipped Stage 0-2 get lead_source='shopify' and lifecycle_stage=SQL directly
- Webhook topics handled:
  1. `checkouts/create` → `checkout_initiated` journey_event → +8.0 pts (checkout_started)
  2. `checkouts/update` (abandoned) → `cart_abandoned` journey_event → detected when no order within 1h window
  3. `orders/create` → `checkout_completed` journey_event → feeds Stage 4 (Ventas) → SaleCompletedEvent
- HMAC signature verification on all webhooks (existing pattern in marketing_webhooks.py)
- ENABLE_MOCKS toggle for fallback when dev store unavailable

### Meeting Booking Bridge (EventBus Pattern)
- Scheduling module publishes events via EventBus:
  - `AppointmentBookedEvent` → journey_event `meeting_booked`
  - `AppointmentCompletedEvent` → journey_event `meeting_completed`
  - `AppointmentRescheduledEvent` → journey_event `meeting_rescheduled`
  - `AppointmentNoShowEvent` → journey_event `meeting_no_show`
- CRM listener creates journey_events from these events
- LifecycleService.recalculate_score() called → meeting_requested: +10.0 pts (existing weight)
- All appointment statuses count for metrics — COMPLETED is the star metric
- Must be compatible with existing scheduling module (Calendly clone) — Sales Agent sends booking link, user schedules, system tracks attendance
- Researcher must investigate scheduling best practices and healthy attendance benchmarks

### Bottleneck Visualization (Dual: Banner + Inline)
- **Panel-level bottleneck banner** at top of panel when thresholds crossed — shows metric + threshold status + generic actionable tip
- **Inline badge** on the channel row itself (red/yellow coloring)
- Both shown simultaneously for maximum visibility
- Abandoned cart thresholds (researcher to calibrate with industry best practices):
  - ≤ 30% = normal (no badge)
  - 31-50% = yellow warning
  - > 50% = red critical
  - Tip: "Revisa tu proceso de pago y considera email de recuperacion de carrito"
- Meeting no-show thresholds (researcher to calibrate with best practices):
  - ≤ 20% = normal
  - 21-40% = yellow warning
  - > 40% = red critical
  - Tip: "Considera recordatorios automaticos antes de la reunion"
- Multiple banners can appear if both thresholds are crossed

### Payment Gateway Extensibility
- Design the "Payment Links" group to accommodate future payment gateways beyond Shopify
- Current: Sales Agent sends Shopify payment links via chat
- Future: MercadoPago, PayPal, direct landing page checkout, multiple gateway selection by user
- Channel registry entries should use generic provider pattern (not hardcoded to Shopify)
- Landing page checkout shows "Proximamente" badge until landing page generation milestone is complete

### Claude's Discretion
- Shopify dev store setup specifics and test order generation approach
- Exact bottleneck threshold calibration after researcher investigates industry benchmarks
- Bottleneck banner component design (animation, dismissibility)
- Generic tip content per bottleneck type
- Meeting rescheduling tracking implementation details
- Abandoned cart detection window (1h suggested, researcher may adjust)
- Payment link tracking implementation in sales_agent module
- Available channels list for opportunity stage
- Error/stale UX casuistry for opportunity-specific scenarios

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Analytics Pattern (Phase 5-6 reference)
- `backend/src/modules/analytics/api/metrics.py` — /metrics/capture and /metrics/nurturing endpoint patterns to follow
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/capture_dto.py` — CaptureDetailDTO structure (header KPIs, mini funnel, groups)
- `backend/src/modules/analytics/application/dto/nurture_dto.py` — NurtureDetailDTO structure (same pattern)
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP (add "opportunity" entries)

### Cost Service
- `backend/src/modules/analytics/application/services/stage_cost_service.py` — StageCostService (generic, reusable for Stage 3)

### CRM & Lifecycle
- `backend/src/modules/crm/domain/scoring.py` — Scoring weights: checkout_started=8.0, meeting_requested=10.0
- `backend/src/modules/crm/domain/enums.py` — LifecycleStage.OPPORTUNITY already defined
- `backend/src/modules/crm/domain/events.py` — SaleCompletedEvent pattern for new event types
- `backend/src/modules/crm/application/services/lifecycle_service.py` — EventBus subscription and scoring recalculation
- `backend/src/modules/crm/application/services/customer_service.py` — CustomerService.identify() for profile matching

### Shopify Integration
- `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py` — ShopifyConnector (OAuth, HMAC verification, API version 2026-01)
- `backend/src/modules/connections/api/marketing_webhooks.py` — POST /webhooks/shopify placeholder (needs real event parsing)
- `backend/src/modules/connections/api/shopify.py` — Shopify connection management endpoints

### Scheduling Module
- `backend/src/modules/scheduling/domain/appointment.py` — Appointment entity with SCHEDULED/COMPLETED/CANCELLED/NO_SHOW statuses
- `backend/src/modules/scheduling/infrastructure/models/appointment_model.py` — AppointmentModel (appointments table, lead_id FK)
- `backend/src/modules/scheduling/infrastructure/repositories/appointment_repository.py` — get_appointments_by_date_range()

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/NurtureDetail.tsx` — Detail panel pattern to replicate
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx` — Alternative reference
- `frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts` — Hook pattern for data fetching
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId, StageSummary types
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add OPORTUNIDAD case)

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

### Development Tools
- Shopify Dev MCP (`mcp__shopify-dev-mcp__*`) — Use during development for API queries, GraphQL validation, webhook payload reference

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseMetricsProvider` ABC + `ProviderRegistry`: Need ShopifyCheckoutProvider (or internal provider reading journey_events)
- `ChannelRegistry.get_available_channels()`: Add "opportunity" stage entries
- `MetricsCache` with per-stage TTL: opportunity stage uses 300s default
- `NurtureDetail.tsx` + `ChannelGroup` + `ChannelRow`: Frontend pattern ready for replication
- `EventBus` (Phase 3): Class-level handler registry for new appointment events
- `CustomerService.identify()`: Profile matching for Shopify checkout emails
- `StageCostService`: Generic cost calculation, reusable for Stage 3

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- Multi-metric ChannelRow with secondary lines (Phase 4-6) — reuse for meeting status breakdown
- Mini funnel: Source → Target = X% at panel top (Phase 5-6)
- 3 header KPIs pattern (Phase 5-6)
- Webhook → JourneyEvent → EventBus → Scoring (Phase 6 Mailerlite pattern)
- ConnectionPort for DDD-safe credential access
- ENABLE_MOCKS fallback in frontend API layer

### Integration Points
- `MetricsDashboard.tsx`: Add `activeStage === 'OPORTUNIDAD' ? <OpportunityDetail /> : ...` routing
- `StageSummary` mock data: Set `hasDetail: true` for OPORTUNIDAD stage
- `metrics.py` router: Register new `/metrics/opportunity` endpoint
- `STAGE_CHANNEL_MAP`: Add "opportunity" entries (checkout-init, abandoned-cart, link-enviado, checkout-lp, meeting-booked)
- `marketing_webhooks.py`: Upgrade Shopify webhook handler from placeholder to real event processing
- Scheduling module: Add EventBus event publishing for appointment lifecycle
- `main.py` or event registration: Register CRM listeners for appointment events

</code_context>

<specifics>
## Specific Ideas

- Three groups instead of two — Checkout, Payment Links, Qualification — to properly separate commerce friction from direct sales and high-ticket qualification
- "Proximamente" badge on Checkout LP channel — makes extensibility visible to the user, signals that landing page checkout is coming
- Payment gateway extensibility: user will eventually choose between MercadoPago, PayPal, and others. Sales Agent sends link, user pays. Design for this from day one
- "La idea es que el usuario en un futuro cercano prefiera que la pasarela de pago este en nuestra landing page" — landing page will have embedded checkout with user-selected payment gateways
- Meeting data must show full pipeline: booked, completed (star), no-show, rescheduled — "compatible con el modulo de scheduling donde vive el clon de Calendly"
- Sales Agent sends scheduling link, user books, system tracks attendance and follows up on no-shows
- Bottleneck banners with actionable tips — not just flagging the problem but giving direction (generic tips, not action triggers)
- "Revisa en internet las mejores practicas" — researcher must investigate industry benchmarks for cart abandonment rates and meeting attendance rates from top performers
- Both banner + inline badge for bottleneck visualization — maximum visibility for the business owner

</specifics>

<deferred>
## Deferred Ideas

- MercadoPago/PayPal gateway integration — future milestone (payment gateway selection)
- Landing page embedded checkout — future milestone (landing page generation)
- Action Triggers (click-to-act on bottleneck banners) — deferred per PROJECT.md
- Configurable bottleneck thresholds per tenant — future enhancement (use researched defaults for now)
- Abandoned cart recovery email automation — Stage 2 (Nurturing) enhancement, not Stage 3

</deferred>

---

*Phase: 07-stage-3-oportunidad*
*Context gathered: 2026-03-16*
