# Phase 7: Stage 3 Oportunidad - Research

**Researched:** 2026-03-16
**Domain:** Sales pipeline metrics (Shopify checkout webhooks, scheduling module integration, bottleneck detection)
**Confidence:** HIGH

## Summary

Phase 7 builds the Opportunity detail panel -- the third stage in the Growth Studio metrics dashboard. It tracks **purchase intent signals**: people actively trying to buy (checkout, payment links) or qualifying for high-ticket offers (meeting bookings). The backend endpoint `/metrics/opportunity` aggregates data from Shopify webhooks (checkout events) and the internal scheduling module (appointment lifecycle). The frontend replicates the established NurtureDetail panel pattern with three channel groups (Checkout, Payment Links, Qualification) plus bottleneck banners.

The existing codebase provides strong foundations: the Shopify webhook endpoint exists as a stub (`marketing_webhooks.py`), HMAC verification is already implemented, the EventBus pattern is established, CRM scoring weights already include `checkout_started` (8.0 pts) and `meeting_requested` (10.0 pts), the scheduling module has `AppointmentModel` with all required statuses (SCHEDULED/COMPLETED/CANCELLED/NO_SHOW), and the frontend detail panel pattern (NurtureDetail) is directly replicable. The main new work is: (1) real Shopify webhook event parsing with CustomerProfile matching, (2) appointment EventBus bridge from scheduling to CRM, (3) OpportunityMetricsRepository for SQL pipeline queries, and (4) the OpportunityDetail frontend panel with bottleneck banners.

**Primary recommendation:** Follow the exact Phase 5-6 pattern (DTO + Repository + MetricsService method + API endpoint + frontend detail panel) and add two new integration layers: Shopify webhook event handler and scheduling EventBus bridge.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **3 Channel Groups**: Checkout (checkout-init + abandoned-cart from Shopify), Payment Links (link-enviado from Sales Agent + checkout-lp with "Proximamente" badge), Qualification (meeting-booked from scheduling module)
- **Per-Channel Metrics**: count + monetary value (where applicable) + conversion from Stage 2
- **Mini Funnel**: MQLs -> SQLs = X%
- **Header KPIs**: Total SQLs | Conversion Rate (MQL->SQL) | Cost per SQL (3 KPIs)
- **Shopify Test Data Strategy**: Use Shopify development store with test orders; webhook topics: checkouts/create, checkouts/update, orders/create; ENABLE_MOCKS toggle for fallback
- **Shopify Webhook Handler**: Real-time processing: webhook -> parse -> find/create CustomerProfile -> create JourneyEvent -> EventBus -> scoring -> stage transition; Profile matching by email, create if missing; Direct Shopify buyers get lead_source='shopify' and lifecycle_stage=SQL
- **Meeting Booking Bridge**: Scheduling module publishes AppointmentBookedEvent, AppointmentCompletedEvent, AppointmentRescheduledEvent, AppointmentNoShowEvent via EventBus; CRM listener creates journey_events
- **Bottleneck Visualization**: Dual banner + inline badge; abandoned cart thresholds and meeting no-show thresholds with calibrated defaults
- **Payment Gateway Extensibility**: Generic provider pattern, not hardcoded to Shopify; Landing page checkout shows "Proximamente" badge
- **Available (unconnected) channels shown at bottom with "Configurar" badge**

### Claude's Discretion
- Shopify dev store setup specifics and test order generation approach
- Exact bottleneck threshold calibration after investigating industry benchmarks
- Bottleneck banner component design (animation, dismissibility)
- Generic tip content per bottleneck type
- Meeting rescheduling tracking implementation details
- Abandoned cart detection window (1h suggested, may adjust)
- Payment link tracking implementation in sales_agent module
- Available channels list for opportunity stage
- Error/stale UX casuistry for opportunity-specific scenarios

### Deferred Ideas (OUT OF SCOPE)
- MercadoPago/PayPal gateway integration
- Landing page embedded checkout
- Action Triggers (click-to-act on bottleneck banners)
- Configurable bottleneck thresholds per tenant
- Abandoned cart recovery email automation
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OPO-01 | Detail panel showing two groups: Web Transactional Friction and High-Ticket Qualification | CONTEXT.md expands to 3 groups (Checkout, Payment Links, Qualification). Frontend NurtureDetail pattern directly replicable. ChannelGroup + ChannelRow components exist. |
| OPO-02 | Backend endpoint `/metrics/opportunity` tracking SQL pipeline -- checkout initiations + meeting bookings | Follow `/metrics/nurturing` pattern. OpportunityMetricsRepository queries journey_events for checkout_initiated, meeting_booked. Count SQLs from lifecycle_transitions. |
| OPO-03 | Shopify webhook integration for checkout events (use test data given known connection issues) | Existing stub at `marketing_webhooks.py`. HMAC verification exists. Must implement real event parsing for checkouts/create, checkouts/update, orders/create. Shopify dev store for testing. |
| OPO-04 | Meeting booked count from internal scheduling module (CRM leads with meeting_booked events) | AppointmentModel has SCHEDULED/COMPLETED/CANCELLED/NO_SHOW statuses. EventBus bridge needed: scheduling publishes events, CRM listener creates journey_events. Scoring weight meeting_requested=10.0 already defined. |
| OPO-05 | Abandoned cart as bottleneck indicator -- high abandoned-cart vs checkout-init ratio flagged visually | Research provides calibrated thresholds. Industry average abandonment: 70%. For Nicolify context (custom checkout, not typical ecommerce): 30% normal, 31-50% warning, >50% critical. Dual banner + inline badge pattern. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | `/metrics/opportunity` endpoint | Project standard |
| SQLAlchemy 2.0 | existing | OpportunityMetricsRepository queries | Project standard, select() syntax |
| Pydantic v2 | existing | OpportunityDetailDTO | Project standard |
| React/Next.js 14 | existing | OpportunityDetail panel component | Project standard |
| TanStack Query | existing | useOpportunityDetail hook | Established pattern in useCaptureDetail, useNurtureDetail |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| structlog | existing | Webhook handler logging | Shopify webhook processing |
| Redis (redis-py) | existing | MetricsCache for opportunity stage | 300s TTL (default) |

### Alternatives Considered
None -- this phase uses exclusively existing libraries and patterns.

**Installation:**
No new dependencies required.

## Architecture Patterns

### Recommended Project Structure
```
backend/src/modules/
  analytics/
    application/
      dto/
        opportunity_dto.py          # OpportunityDetailDTO (NEW)
      services/
        metrics_service.py          # Add get_opportunity_metrics() method
    infrastructure/
      repositories/
        opportunity_repository.py   # OpportunityMetricsRepository (NEW)
    api/
      metrics.py                    # Add /metrics/opportunity endpoint
  connections/
    api/
      marketing_webhooks.py         # Upgrade Shopify webhook handler
  crm/
    domain/
      events.py                     # Add AppointmentBookedEvent etc.
    application/
      services/
        lifecycle_service.py        # Register appointment event handlers
  scheduling/
    application/
      services/                     # Add EventBus publishing to appointment service

frontend/src/features/marketing-studio/
  components/metrics-dashboard/
    detail-panels/
      OpportunityDetail.tsx         # NEW
      BottleneckBanner.tsx          # NEW
  hooks/
    useOpportunityDetail.ts         # NEW
  types/
    metrics.ts                      # Add OpportunityDetail types
  api/
    metrics-api.ts                  # Add getOpportunityDetail
    metrics-mock-data.ts            # Add MOCK_OPPORTUNITY_DETAIL
```

### Pattern 1: Shopify Webhook -> JourneyEvent Pipeline
**What:** Real-time webhook processing that creates CRM journey events and triggers scoring
**When to use:** For all external platform webhooks that should feed the CRM lifecycle
**Example:**
```python
# Source: existing marketing_webhooks.py Mailerlite pattern
@router.post("/shopify", status_code=status.HTTP_200_OK)
async def shopify_webhook(
    request: Request,
    verified: bool = Depends(verify_shopify_signature),
    db: Session = Depends(get_db),
):
    payload = await request.json()
    topic = request.headers.get("X-Shopify-Topic", "")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")

    # Resolve tenant from shop_domain via connections table
    tenant_id = await _resolve_tenant(db, shop_domain)

    # Map topic to handler
    if topic == "checkouts/create":
        await _handle_checkout_created(db, tenant_id, payload)
    elif topic == "checkouts/update":
        await _handle_checkout_updated(db, tenant_id, payload)
    elif topic == "orders/create":
        await _handle_order_created(db, tenant_id, payload)

    return {"status": "processed", "topic": topic}
```

### Pattern 2: EventBus Bridge (Scheduling -> CRM)
**What:** Scheduling module publishes appointment lifecycle events, CRM listener creates journey_events
**When to use:** When a bounded context needs to notify CRM of lifecycle-relevant events
**Example:**
```python
# In scheduling service (publisher side):
from src.shared.domain.events import EventBus, DomainEvent

class AppointmentService:
    def complete_appointment(self, appointment_id, ...):
        # ... update appointment status ...
        EventBus.publish(DomainEvent(
            event_name="appointment_completed",
            tenant_id=tenant_id,
            payload={
                "appointment_id": str(appointment_id),
                "lead_id": str(lead_id),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        ), session=self.db)

# In CRM (subscriber side, registered at app startup):
EventBus.subscribe("appointment_booked", lifecycle_service.handle_appointment_booked)
EventBus.subscribe("appointment_completed", lifecycle_service.handle_appointment_completed)
EventBus.subscribe("appointment_no_show", lifecycle_service.handle_appointment_no_show)
```

### Pattern 3: OpportunityMetricsRepository (CRM-Based Counting)
**What:** SQL queries against journey_events and lifecycle_transitions for opportunity stage metrics
**When to use:** Same pattern as NurtureMetricsRepository -- counts from CRM tables
**Example:**
```python
# Source: nurture_repository.py pattern
class OpportunityMetricsRepository:
    def count_new_sqls(self, tenant_id, start_date, end_date) -> int:
        """Count profiles that transitioned TO SQL stage."""
        stmt = select(func.count(func.distinct(LifecycleTransitionModel.profile_id))).where(
            LifecycleTransitionModel.tenant_id == tenant_id,
            LifecycleTransitionModel.to_stage == LifecycleStage.SQL,
            LifecycleTransitionModel.occurred_at >= start_date,
            LifecycleTransitionModel.occurred_at <= end_date,
        )
        return int(self.db.execute(stmt).scalar() or 0)

    def count_checkout_events(self, tenant_id, start_date, end_date) -> dict:
        """Count checkout_initiated and cart_abandoned journey_events."""
        # ...similar to nurture count_email_events pattern...

    def count_meeting_events(self, tenant_id, start_date, end_date) -> dict:
        """Count meeting_booked, meeting_completed, meeting_no_show, meeting_rescheduled."""
        # ...query journey_events by event_name...
```

### Anti-Patterns to Avoid
- **Querying scheduling module directly from analytics:** Use journey_events in CRM as the single source of truth. The EventBus bridge writes meeting events there; analytics reads from there. Never import scheduling models into analytics.
- **Hardcoding Shopify as the only checkout provider:** Use generic event names (checkout_initiated, cart_abandoned) in journey_events properties. The `source` property distinguishes providers.
- **Synchronous abandoned cart detection in the webhook handler:** Do NOT block the webhook response to detect abandonment. The 1h detection window requires a background check (cron or delayed task), not synchronous processing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Webhook HMAC verification | Custom signature checker | `verify_shopify_signature` (existing) | Already handles edge cases, tested |
| Profile identity resolution | Custom email lookup | `CustomerService.identify()` | Handles user_id/email/phone priority, creates if missing |
| Lead score recalculation | Manual score calculation | `LifecycleService.recalculate_score()` | Handles weights, thresholds, transitions, audit trail |
| Metrics caching | Custom Redis logic | `MetricsCache` with 300s TTL | Existing cache infrastructure with per-stage TTL |
| Channel connected/available split | Manual connection check | `ChannelRegistry.get_available_channels()` | Uses ConnectionPort, handles internal providers |
| Cost per SQL calculation | Custom cost logic | `StageCostService.calculate_cost_per_mql()` (rename param) | Generic -- works for any stage's cost/count ratio |
| Frontend channel rendering | Custom channel components | `ChannelGroup` + `ChannelRow` | Established pattern with secondary lines support |

**Key insight:** Phase 7 is architecturally identical to Phase 5-6 (DTO + Repository + Service + API + Panel). The only genuinely new pieces are the Shopify webhook parser and the scheduling EventBus bridge.

## Common Pitfalls

### Pitfall 1: Abandoned Cart Detection Timing
**What goes wrong:** Treating `checkouts/update` as abandoned immediately, when the customer might still complete the purchase
**Why it happens:** Shopify doesn't send an explicit "abandoned" event. You detect abandonment by checking if a checkout was NOT followed by an order within a time window.
**How to avoid:** On `checkouts/create`, record the checkout with status "initiated". On `orders/create`, match by checkout_token and mark as completed. Run a periodic background check (every 15-30 min) that flags checkouts older than 1 hour without a matching order as abandoned. Do NOT create the `cart_abandoned` journey_event in the webhook handler itself.
**Warning signs:** If you see cart_abandoned events appearing instantly after checkout_initiated events.

### Pitfall 2: Tenant Resolution for Shopify Webhooks
**What goes wrong:** Shopify webhooks don't include tenant_id. Without tenant resolution, events can't be attributed.
**Why it happens:** Shopify sends shop_domain in the `X-Shopify-Shop-Domain` header, but the system needs a UUID tenant_id.
**How to avoid:** Look up the tenant by shop_domain in the connections table (channel_connections where channel_type='shopify'). Cache this mapping. Return 200 OK even if tenant not found (Shopify retries on 4xx/5xx).
**Warning signs:** Shopify webhook retries piling up in the Shopify admin.

### Pitfall 3: Appointment lead_id vs CRM profile_id Mismatch
**What goes wrong:** The scheduling module's `AppointmentModel.lead_id` is a FK to `leads` table, but CRM uses `customer_profiles`. These are different tables.
**Why it happens:** The scheduling module was built before the CRM CDP pattern (Phase 3). The `leads` table is a legacy model.
**How to avoid:** In the EventBus bridge, resolve the CRM `profile_id` from the `lead_id`. Check if there's a mapping in `customer_profiles` via email or a direct FK. If not found, create the journey_event with the lead_id stored in properties for later reconciliation.
**Warning signs:** Meeting events not appearing in customer profile journey timelines.

### Pitfall 4: Double-Counting SQLs from Multiple Sources
**What goes wrong:** A checkout AND a meeting booking both push the same profile to SQL, counting it twice.
**Why it happens:** Both events trigger `recalculate_score()` which might cross the SQL threshold independently.
**How to avoid:** The lifecycle_transitions table already handles this -- count `DISTINCT profile_id` where `to_stage = SQL`. The transition is recorded only once per profile (the first time the threshold is crossed).
**Warning signs:** SQL count exceeding the sum of checkout + meeting events.

### Pitfall 5: Shopify Webhook Responding with Non-2xx
**What goes wrong:** If the webhook handler throws an exception, Shopify receives a non-200 response and retries up to 19 times over 48 hours.
**Why it happens:** Unhandled exceptions in event processing.
**How to avoid:** Always wrap processing in try/except and return 200 OK regardless. Log errors but don't propagate them. Idempotency: check for existing journey_events before creating duplicates (use Shopify checkout_token as dedup key in properties).
**Warning signs:** Shopify admin showing "webhook delivery failures" and duplicate events in journey_events.

## Code Examples

### OpportunityDetailDTO (Backend)
```python
# Source: nurture_dto.py pattern
from pydantic import BaseModel
from typing import Optional
from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO, TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO

class OpportunityHeaderKpisDTO(BaseModel):
    total_sqls: int
    conversion_rate: float  # MQL -> SQL percentage 0-100
    cost_per_sql: Optional[float] = None

class BottleneckDTO(BaseModel):
    type: str  # "abandoned_cart" or "meeting_no_show"
    metric_label: str  # "Tasa de Abandono" or "Tasa de No-Show"
    current_rate: float  # percentage 0-100
    severity: str  # "normal", "warning", "critical"
    threshold: float  # threshold crossed
    tip: str  # actionable tip in Spanish

class OpportunityDetailDTO(BaseModel):
    header_kpis: OpportunityHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # MQLs -> SQLs
    checkout: TrafficGroupDTO
    payment_links: TrafficGroupDTO
    qualification: TrafficGroupDTO
    bottlenecks: list[BottleneckDTO] = []
    available: Optional[AvailableChannelsDTO] = None
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### Shopify Webhook Event Handler
```python
# Source: marketing_webhooks.py Mailerlite pattern + Shopify webhook docs
async def _handle_checkout_created(db: Session, tenant_id: UUID, payload: dict):
    email = payload.get("email")
    if not email:
        return

    # Identity resolution
    customer_svc = CustomerService(db)
    profile = customer_svc.identify(
        tenant_id=tenant_id,
        traits={"email": email, "name": payload.get("billing_address", {}).get("name")},
        identities={}
    )

    # Set lead_source for direct Shopify buyers
    if not profile.lead_source:
        profile.lead_source = "shopify"

    # Create journey_event
    total_price = float(payload.get("total_price", 0))
    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name="checkout_initiated",
        event_type="track",
        properties={
            "source": "shopify",
            "checkout_token": payload.get("token", ""),
            "total_price": total_price,
            "currency": payload.get("currency", "USD"),
            "line_items_count": len(payload.get("line_items", [])),
        },
    )
    db.add(journey_event)

    # Recalculate score (checkout_started = +8.0 pts)
    lifecycle_svc = LifecycleService(db)
    lifecycle_svc.recalculate_score(profile.id, tenant_id)
    db.commit()
```

### Bottleneck Banner Frontend Component
```tsx
// Source: NurtureDetail pattern + CONTEXT.md bottleneck spec
interface BottleneckBannerProps {
  type: 'abandoned_cart' | 'meeting_no_show';
  metricLabel: string;
  currentRate: number;
  severity: 'warning' | 'critical';
  tip: string;
}

function BottleneckBanner({ type, metricLabel, currentRate, severity, tip }: BottleneckBannerProps) {
  const bgColor = severity === 'critical' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200';
  const textColor = severity === 'critical' ? 'text-red-800' : 'text-yellow-800';

  return (
    <div className={`rounded-lg border p-3 ${bgColor}`}>
      <div className="flex items-center gap-2">
        <AlertTriangle className={`h-4 w-4 ${textColor}`} />
        <span className={`text-sm font-medium ${textColor}`}>
          {metricLabel}: {currentRate.toFixed(1)}%
        </span>
      </div>
      <p className="text-xs text-muted-foreground mt-1">{tip}</p>
    </div>
  );
}
```

### Channel Registry Entries for Opportunity Stage
```python
# Add to STAGE_CHANNEL_MAP in channel_registry.py
"opportunity": [
    # Checkout group
    {"slug": "checkout-init", "name": "Checkout Iniciado", "channel_type": "checkout", "source_label": "Shopify", "provider_name": "shopify", "metric_names": ["count", "value"]},
    {"slug": "abandoned-cart", "name": "Carrito Abandonado", "channel_type": "checkout", "source_label": "Shopify", "provider_name": "shopify", "metric_names": ["count", "value", "abandonment_rate"]},
    # Payment Links group
    {"slug": "link-enviado", "name": "Link de Pago Enviado", "channel_type": "payment_link", "source_label": "Sales Agent", "provider_name": "internal", "metric_names": ["count", "value"]},
    {"slug": "checkout-lp", "name": "Checkout Landing Page", "channel_type": "payment_link", "source_label": "Landing Page", "provider_name": "internal", "metric_names": ["count", "value"]},
    # Qualification group
    {"slug": "meeting-booked", "name": "Reuniones Agendadas", "channel_type": "qualification", "source_label": "Scheduling", "provider_name": "internal", "metric_names": ["booked", "completed", "no_show", "rescheduled"]},
],
```

## Bottleneck Threshold Calibration

### Abandoned Cart Rate Thresholds
**Research basis:** Industry average cart abandonment is 70-72% (Baymard Institute 2026). However, Nicolify's context differs from typical ecommerce: the Shopify checkout here is specifically for creators' digital products/services, often with pre-qualified leads (MQLs who already engaged with the funnel). The CONTEXT.md suggestion of 30/50% aligns with a more qualified audience.

**Recommended thresholds (confirmed from CONTEXT.md):**
| Range | Severity | Color | Action |
|-------|----------|-------|--------|
| 0-30% | Normal | None | No badge |
| 31-50% | Warning | Yellow | "Revisa tu proceso de pago y considera email de recuperacion de carrito" |
| >50% | Critical | Red | Same tip, with stronger visual urgency |

**Rationale:** Since these are pre-qualified leads (came through the funnel), a 30% abandonment rate is generous. The industry 70% includes casual browsers -- Nicolify's checkout audience is already interested.

### Meeting No-Show Rate Thresholds
**Research basis:** B2B meeting show rates average 80% (20% no-show). Bottom-of-funnel no-show should not exceed 10%. Top SDR teams achieve 90%+ show rate. For creators selling high-ticket services (coaching, courses), no-show rates tend to be higher than enterprise B2B.

**Recommended thresholds (confirmed from CONTEXT.md):**
| Range | Severity | Color | Action |
|-------|----------|-------|--------|
| 0-20% | Normal | None | No badge |
| 21-40% | Warning | Yellow | "Considera recordatorios automaticos antes de la reunion" |
| >40% | Critical | Red | Same tip, with stronger visual urgency |

**Rationale:** 20% aligns with industry average. Above 40% indicates a systemic issue (wrong audience, no reminders, too long between booking and meeting).

### Abandoned Cart Detection Window
**Recommendation:** Use **1 hour** as specified in CONTEXT.md. This is standard for Shopify stores -- Shopify's own abandoned checkout recovery emails default to 1 hour, 10 hours, or 24 hours. One hour catches genuine abandonments without false positives from slow checkout sessions.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Shopify webhook stub (log only) | Real event parsing + JourneyEvent + scoring | Phase 7 | Enables checkout funnel tracking |
| No scheduling-CRM bridge | EventBus appointment events -> journey_events | Phase 7 | Enables meeting pipeline metrics |
| Hardcoded stage detail panels | Dynamic OpportunityDetail with bottleneck detection | Phase 7 | Proactive friction alerts |

**Deprecated/outdated:**
- AppointmentModel.lead_id references legacy `leads` table -- will need reconciliation with `customer_profiles`

## Open Questions

1. **Scheduling module appointment service location**
   - What we know: AppointmentModel and AppointmentRepository exist. Domain entity and enums exist.
   - What's unclear: Is there an existing application-level AppointmentService that handles status transitions? Or is status updated directly on the model?
   - Recommendation: Check for existing service before creating a new one. The EventBus publishing should happen in whatever service handles appointment status changes.

2. **Lead_id to profile_id mapping**
   - What we know: AppointmentModel uses lead_id FK to leads table. CRM uses customer_profiles.
   - What's unclear: Is there a reliable mapping between leads.id and customer_profiles.id? Do they share email?
   - Recommendation: During implementation, check if lead_id maps to any customer_profile. If no mapping exists, create journey_events with lead_id in properties and add a reconciliation note. This is a known tech debt from the legacy leads table.

3. **Payment link tracking in sales_agent module**
   - What we know: Sales Agent sends payment links via chat. The "link-enviado" channel should track these.
   - What's unclear: Does the sales_agent module currently emit any event when a payment link is sent?
   - Recommendation: For Phase 7, if no existing event exists, the link-enviado channel shows "Proximamente" badge (same as checkout-lp). This can be enabled when the Sales Agent milestone adds payment link tracking.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inside Docker container) |
| Config file | `backend/pytest.ini` or `pyproject.toml` |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/test_opportunity.py -x` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPO-01 | OpportunityDetail panel renders 3 groups | manual | Visual verification | -- Wave 0 |
| OPO-02 | /metrics/opportunity returns SQL pipeline data | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_opportunity_metrics.py -x` | -- Wave 0 |
| OPO-03 | Shopify webhook creates journey_events | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_shopify_webhook.py -x` | -- Wave 0 |
| OPO-04 | Meeting events create journey_events via EventBus | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/scheduling/test_appointment_events.py -x` | -- Wave 0 |
| OPO-05 | Bottleneck detection flags high abandonment | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_bottleneck_detection.py -x` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/analytics/test_opportunity_metrics.py` -- covers OPO-02, OPO-05
- [ ] `tests/modules/connections/test_shopify_webhook.py` -- covers OPO-03
- [ ] `tests/modules/scheduling/test_appointment_events.py` -- covers OPO-04

## Sources

### Primary (HIGH confidence)
- Codebase: `marketing_webhooks.py` -- existing Shopify stub and Mailerlite handler pattern
- Codebase: `webhook_security.py` -- HMAC verification for Shopify
- Codebase: `nurture_dto.py`, `nurture_repository.py` -- Phase 6 pattern to replicate
- Codebase: `channel_registry.py` -- STAGE_CHANNEL_MAP structure
- Codebase: `scoring.py` -- checkout_started=8.0, meeting_requested=10.0 weights
- Codebase: `scheduling/domain/enums.py` -- AppointmentStatus enum (SCHEDULED/COMPLETED/CANCELLED/NO_SHOW)
- Codebase: `events.py` -- DomainEvent + EventBus patterns
- Codebase: `lifecycle_service.py` -- Score recalculation and threshold transitions
- Codebase: `NurtureDetail.tsx` -- Frontend detail panel pattern

### Secondary (MEDIUM confidence)
- [Baymard Institute](https://baymard.com/lists/cart-abandonment-rate) -- Cart abandonment rate 70.22% (2026 data)
- [Operatix/SDR benchmarks](https://tamtotarget.com/sdr-meeting-benchmarks/) -- Meeting show rate 80% average
- [RevenueHero no-show benchmark](https://www.revenuehero.io/reports/no-show-benchmark-december-02-2024) -- B2B no-show rates by industry

### Tertiary (LOW confidence)
- Shopify dev store test order best practices -- general guidance from multiple blog posts, not from official Shopify documentation. Implementation details should be verified with Shopify Dev MCP during development.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries/patterns already exist in codebase
- Architecture: HIGH - directly replicates Phase 5-6 pattern with well-defined new integrations
- Pitfalls: HIGH - identified from codebase analysis (lead_id/profile_id mismatch, tenant resolution, abandonment timing)
- Bottleneck thresholds: MEDIUM - based on industry research, calibrated for Nicolify's qualified-audience context

**Research date:** 2026-03-16
**Valid until:** 2026-04-15 (stable -- internal architecture, no external API changes expected)
