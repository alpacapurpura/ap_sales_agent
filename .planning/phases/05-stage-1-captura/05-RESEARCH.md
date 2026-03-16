# Phase 5: Stage 1 Captura - Research

**Researched:** 2026-03-15
**Domain:** CRM lead aggregation, cost tracking, EventBus integration, Mailerlite webhooks
**Confidence:** HIGH

## Summary

Phase 5 builds the Capture detail panel for the Growth Studio metrics dashboard. The backend needs a new `/metrics/capture` endpoint that queries `customer_profiles` by `lead_source` to count net-new leads per channel, grouped into Web Infrastructure (landing-form, mailerlite) and AI Agent Conversational (ig-dm, fb-messenger, tiktok-dm, whatsapp-inbound). A cost configuration system must be built from scratch (no existing cost model exists) for manual channel costs, with LLM token costs auto-calculated. The ChatOrchestrator in `sales_agent` must emit `LeadCapturedEvent` via the shared `EventBus` when the agent extracts email/phone during conversation. The frontend replicates the AttractionDetail pattern with new components: CaptureDetail, MiniFunnel, and CostLink.

The codebase has strong patterns to follow: MetricsService + ChannelRegistry + cache for backend, AttractionDetail + ChannelGroup + ChannelRow for frontend. The capture channel definitions already exist in `STAGE_CHANNEL_MAP["capture"]` with 6 channels. The critical new work is: (1) CRM-based lead counting repository, (2) LeadCapturedEvent emission from ChatOrchestrator, (3) cost configuration model + settings API, (4) Mailerlite webhook/ETL for subscriber sync, and (5) CAL calculation.

**Primary recommendation:** Follow the proven attraction metrics pattern exactly (MetricsService method, DTO, API endpoint, frontend hook + detail panel), adding a CRM-internal provider for lead counts and a new `channel_cost_settings` table for cost configuration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- A "captured lead" from AI Agent = email or phone successfully extracted during conversation (not just first message)
- Data sources: customer_profiles (primary count -- net-new profiles by lead_source) + journey_events (extraction detail)
- Web infrastructure leads: landing page form submission creates profile directly + periodic Mailerlite sync pulls new subscribers
- Sales Agent emits LeadCapturedEvent via EventBus when it extracts email/phone. CRM listens, calls CustomerService.identify(), creates profile with lead_source = channel_slug
- Attribution: first-touch -- the channel where person was first identified gets the lead credit
- Count scope: net-new profiles only (created in period)
- Two groups: Web Infrastructure (landing-form, mailerlite) and AI Agent Conversational (ig-dm, fb-messenger, tiktok-dm, whatsapp-inbound)
- Group header metrics: 3 values -- Total Leads + Cost per Lead + Conversion Rate from Stage 0
- Per-channel row metrics: Leads + Cost + Conversion Rate
- AI Agent channels additionally show conversation volume: "X leads" + "de Y conversaciones"
- Mini arrow funnel at panel top: "Visitors (45,000) -> Leads (8,500) = 18.9%"
- Panel header KPIs: Total Leads | Conversion Rate | CAL
- Full cost system built in this phase -- manual config for platform costs, API-sourced ad spend, agency/third-party costs with proration
- LLM token costs: auto-calculated from token usage per conversation x configurable cost-per-token rate
- Unconfigured cost: show "---" with "Configurar costo" link
- CAP-05 CAL displayed at both overall and per-group levels

### Claude's Discretion
- Mailerlite webhook vs ETL decision based on API requirements research
- Agency cost proration algorithm
- Exact Growth Studio settings panel layout for cost configuration
- Mini funnel arrow component design details
- Token tracking implementation in sales_agent module
- Channel-matched conversion rate algorithm (UTM parsing, source matching logic)
- Error state mapping for capture-specific scenarios

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CAP-01 | Detail panel showing two groups: Web Infrastructure leads and AI Agent conversational leads | ChannelRegistry already has `STAGE_CHANNEL_MAP["capture"]` with 6 channels in correct grouping. Frontend follows AttractionDetail pattern with CaptureDetail + ChannelGroup components. UI-SPEC defines layout. |
| CAP-02 | Backend endpoint `/metrics/capture` aggregating new customer_profiles by source channel with lead count and conversion rate | CustomerProfileModel has `lead_source` (indexed) and `first_seen_at` fields. New repository method needed: `count_by_lead_source(tenant_id, period)` grouping by `lead_source`. MetricsService pattern proven. |
| CAP-03 | AI Agent leads tracked by extraction events where agent obtained email/phone from messaging channels | ChatOrchestrator.process_chat_flow() creates customer profiles at line 256 via IdentityService but does NOT set `lead_source`. Must add `lead_source` assignment + emit LeadCapturedEvent via shared EventBus. JourneyEvent tracking for extraction detail. |
| CAP-04 | Cost tracking per capture channel -- Manychat licensing, LLM token consumption, WhatsApp API costs, Mailerlite subscription | No cost configuration model exists. Must create `channel_cost_settings` table + API. LLM token tracking needs integration point in sales_agent. |
| CAP-05 | Cost of Acquisition per Lead = Total Stage 0 investment / Total Stage 1 leads | Stage 0 spend available from `metric_aggregations` table (paid channel spend). Stage 1 leads from new CRM query. CAL calculated at service layer. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | API endpoint `/metrics/capture` | Project stack |
| SQLAlchemy 2.0 | existing | CRM queries, new cost settings model | Project stack, `select()` syntax |
| Pydantic v2 | existing | DTOs for capture metrics | Project stack |
| React/Next.js 14 | existing | CaptureDetail panel | Project stack |
| TanStack Query | existing | `useCaptureDetail` hook | Proven pattern from `useAttractionDetail` |
| Alembic | existing | Migration for `channel_cost_settings` table | Project stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Redis (via MetricsCache) | existing | Cache capture metrics (300s TTL) | All dashboard reads |
| ARQ | existing | Periodic Mailerlite ETL sync | Mailerlite subscriber sync cron |
| Shared EventBus | existing | LeadCapturedEvent dispatch | AI Agent lead capture |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct CRM query for leads | ETL pipeline + official_metrics | CRM query is simpler for real-time lead counts; ETL better for historical. Use CRM query directly -- capture data changes frequently (300s cache). |
| New table for costs | JSONB in tenant config | Separate table is cleaner, queryable, and auditable. Tenant config would be a mess. |

## Architecture Patterns

### Recommended Project Structure
```
backend/src/modules/
  analytics/
    api/metrics.py                    # Add /metrics/capture endpoint
    application/
      dto/capture_dto.py              # CaptureDetailDTO, CaptureGroupDTO
      services/metrics_service.py     # Add get_capture_metrics() method
      services/capture_cost_service.py # Cost calculation logic
    infrastructure/
      models/channel_cost_model.py    # New: ChannelCostSettingModel
      repositories/capture_repository.py # New: CRM-based lead counts
    domain/
      events.py                       # Add LeadCapturedEvent (or in crm/domain/events.py)
  crm/
    domain/events.py                  # Add LeadCapturedEvent
    application/services/
      customer_service.py             # Ensure lead_source is set on identify()
  sales_agent/
    application/orchestrator/chat.py  # Emit LeadCapturedEvent after contact extraction

frontend/src/features/marketing-studio/
  components/metrics-dashboard/
    detail-panels/CaptureDetail.tsx    # New detail panel
    channel-widgets/MiniFunnel.tsx     # New mini funnel component
    channel-widgets/CostLink.tsx       # New cost config link
  hooks/useCaptureDetail.ts            # New data hook
  api/metrics-api.ts                   # Add getCaptureDetail()
  types/metrics.ts                     # Add CaptureDetail, CaptureGroupType types
```

### Pattern 1: CRM-Based Lead Count Query
**What:** Query `customer_profiles` grouped by `lead_source` with date filter on `first_seen_at`
**When to use:** For net-new lead counts per channel in a period
**Example:**
```python
# Source: Existing CustomerProfileModel schema + SQLAlchemy 2.0 patterns
from sqlalchemy import select, func
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel

stmt = (
    select(
        CustomerProfileModel.lead_source,
        func.count(CustomerProfileModel.id).label("lead_count"),
    )
    .where(
        CustomerProfileModel.tenant_id == tenant_id,
        CustomerProfileModel.first_seen_at >= start_date,
        CustomerProfileModel.first_seen_at <= end_date,
        CustomerProfileModel.lead_source.isnot(None),
    )
    .group_by(CustomerProfileModel.lead_source)
)
```

### Pattern 2: LeadCapturedEvent via Shared EventBus
**What:** ChatOrchestrator emits event when AI agent extracts contact info
**When to use:** After successful identity resolution in `process_chat_flow()`
**Example:**
```python
# Source: Existing SaleCompletedEvent + EventBus patterns
from src.shared.domain.events import DomainEvent, EventBus

@dataclass
class LeadCapturedEvent(DomainEvent):
    @classmethod
    def create(cls, tenant_id, profile_id, channel_slug, extracted_field):
        return cls(
            event_name="lead_captured",
            tenant_id=tenant_id,
            payload={
                "profile_id": str(profile_id),
                "channel_slug": channel_slug,
                "extracted_field": extracted_field,  # "email" or "phone"
            },
        )

# In ChatOrchestrator.process_chat_flow() after CustomerService.identify():
EventBus.publish(
    LeadCapturedEvent.create(tenant_uuid, customer.id, channel_slug, "email"),
    session=db,
)
```

### Pattern 3: Cost Configuration Model
**What:** Per-tenant, per-channel cost settings stored in dedicated table
**When to use:** Manual cost input by business owner for CAL calculation
**Example:**
```python
# New model following project conventions
class ChannelCostSettingModel(Base):
    __tablename__ = "channel_cost_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_slug = Column(String, nullable=False)  # "mailerlite", "whatsapp-inbound", etc.
    cost_type = Column(String, nullable=False)  # "platform", "agency", "tool"
    monthly_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    description = Column(String, nullable=True)  # e.g., "Manychat Pro plan"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Anti-Patterns to Avoid
- **Direct CRM model import in analytics service:** Use a repository pattern. Analytics should not import CRM models directly -- create a CaptureMetricsRepository in analytics that wraps the CRM query.
- **Hardcoded channel-to-group mapping in frontend:** Use backend response grouping. The API should return pre-grouped data (web_infrastructure, ai_agent) just like attraction returns (organic_social, ga4_search, paid, outbound).
- **Synchronous EventBus handlers blocking ChatOrchestrator:** EventBus.publish with session defers until after-commit. Handler exceptions are isolated (already handled in EventBus._dispatch).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Channel connected/available split | Custom connection checker | `ChannelRegistry.get_available_channels(tenant_id, "capture")` | Already works for 6 capture channels |
| Event dispatch | Custom pub/sub | `EventBus.publish(event, session=db)` | Proven, after-commit dispatch, exception isolation |
| Identity resolution | Custom dedup logic | `CustomerService.identify()` | Handles email/phone/user_id priority, deduplication |
| Metrics caching | Custom Redis wrapper | `MetricsCache.get/set()` with stage="capture" | Per-stage TTL, tenant-scoped keys |
| Frontend data fetching | Custom fetch + state | TanStack Query via `useCaptureDetail` hook | 5-min staleTime, loading/error states |
| API response mapping | Manual camelCase conversion | `mapChannel()`, `mapGroup()` patterns from metrics-api.ts | snake_case -> camelCase already handled |

## Common Pitfalls

### Pitfall 1: lead_source Not Set on Profile Creation
**What goes wrong:** ChatOrchestrator creates customer profiles via IdentityService but never sets `lead_source`. All leads would have `null` lead_source, making aggregation impossible.
**Why it happens:** Current `create_with_identity()` in CustomerRepository doesn't accept a `lead_source` parameter.
**How to avoid:** Modify `CustomerService.identify()` and `CustomerRepository.create_with_identity()` to accept optional `lead_source` and `lead_source_detail` parameters. Set these in ChatOrchestrator based on `channel_type`.
**Warning signs:** All lead counts return 0 despite having customer profiles.

### Pitfall 2: Channel Slug Mismatch Between Sales Agent and Channel Registry
**What goes wrong:** ChatOrchestrator uses `channel_type` values like "telegram", "instagram", "whatsapp" but `STAGE_CHANNEL_MAP["capture"]` uses slugs like "ig-dm", "fb-messenger", "whatsapp-inbound".
**Why it happens:** Different naming conventions between connections module (ChannelType enum) and analytics module (channel slugs).
**How to avoid:** Create an explicit mapping: `{"instagram": "ig-dm", "facebook": "fb-messenger", "tiktok": "tiktok-dm", "whatsapp": "whatsapp-inbound", "telegram": "telegram-dm"}`. Apply this mapping when setting `lead_source` on the profile.
**Warning signs:** Leads exist in CRM but don't show up in capture metrics.

### Pitfall 3: Double-Counting Leads from Returning Visitors
**What goes wrong:** `CustomerService.identify()` finds existing profile and returns it. If the code emits LeadCapturedEvent on every identify() call, returning visitors are counted as new leads.
**Why it happens:** identify() merges traits for existing profiles (returns existing, not new).
**How to avoid:** Only emit LeadCapturedEvent when identify() creates a NEW profile (not when it finds an existing one). Check return value or add a `was_created` flag.
**Warning signs:** Lead counts much higher than unique profile counts.

### Pitfall 4: Mailerlite Deduplication
**What goes wrong:** Mailerlite subscriber.created webhook fires for subscribers already in CRM (e.g., captured via AI Agent first, then subscribed to newsletter).
**Why it happens:** Mailerlite doesn't know about our CRM. Same person, different channels.
**How to avoid:** `CustomerService.identify()` already handles deduplication via email lookup. The Mailerlite handler should call identify() with the subscriber email -- if profile exists, it just updates traits without creating a duplicate. Only new profiles get lead_source = "mailerlite".
**Warning signs:** Duplicate profiles or inflated lead counts.

### Pitfall 5: Conversation Count for AI Agent Channels
**What goes wrong:** Missing conversation volume metric for the "de X conversaciones" display.
**Why it happens:** No existing mechanism counts total conversations per channel.
**How to avoid:** Query `journey_events` or `audit_messages` for unique conversation sessions per channel in the period. Or count distinct `user_id` interactions from the sales_agent audit log.
**Warning signs:** Secondary line shows "de 0 conversaciones" despite active AI Agent channels.

### Pitfall 6: Cost Calculation with Missing Costs
**What goes wrong:** CAL (Cost of Acquisition per Lead) becomes NaN or 0 when some channels have no cost configured.
**Why it happens:** Division by zero or null arithmetic.
**How to avoid:** When cost is null/unconfigured, display "---" with "Configurar costo" link per CONTEXT.md. CAL at panel level should only sum configured costs. Make this clear in the DTO: `cost_per_lead: Optional[float] = None`.
**Warning signs:** Incorrect cost metrics or frontend crashes.

## Code Examples

### Backend: CaptureDetailDTO Structure
```python
# Source: AttractionDetailDTO pattern from attraction_dto.py
from pydantic import BaseModel
from typing import Optional

class CaptureHeaderKpisDTO(BaseModel):
    total_leads: int
    conversion_rate: float  # percentage 0-100
    cost_per_lead: Optional[float] = None

class MiniFunnelDTO(BaseModel):
    source_label: str  # "Visitantes"
    source_value: int
    target_label: str  # "Leads"
    target_value: int
    conversion_rate: float

class CaptureDetailDTO(BaseModel):
    header_kpis: CaptureHeaderKpisDTO
    mini_funnel: MiniFunnelDTO
    web_infrastructure: TrafficGroupDTO  # reuse from attraction_dto
    ai_agent: TrafficGroupDTO
    available: Optional[AvailableChannelsDTO] = None
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### Backend: Channel Slug Mapping for Sales Agent
```python
# Source: ChatOrchestrator channel_type -> capture channel slug
CHANNEL_TYPE_TO_CAPTURE_SLUG = {
    "instagram": "ig-dm",
    "facebook": "fb-messenger",
    "tiktok": "tiktok-dm",
    "whatsapp": "whatsapp-inbound",
    "telegram": "telegram-dm",  # Not in current capture stage but future-proof
}
```

### Frontend: CaptureDetail Component Pattern
```typescript
// Source: AttractionDetail.tsx pattern
'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useCaptureDetail } from '../../../hooks/useCaptureDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';

export function CaptureDetail() {
  const { data, isLoading, error } = useCaptureDetail();

  if (isLoading) { /* skeleton pattern */ }
  if (error || !data) { /* error pattern */ }

  return (
    <div className="space-y-2">
      {/* Panel Header KPIs */}
      {/* MiniFunnel */}
      <MiniFunnel data={data.miniFunnel} />
      <ChannelGroup
        title="Infraestructura Web"
        totals={data.webInfrastructure.totals}
        channels={data.webInfrastructure.channels}
        groupType="web_infrastructure"
        defaultOpen
      />
      <ChannelGroup
        title="Agente AI Conversacional"
        totals={data.aiAgent.totals}
        channels={data.aiAgent.channels}
        groupType="ai_agent"
        defaultOpen
      />
    </div>
  );
}
```

## Mailerlite Integration Decision

**Recommendation: Webhook (primary) + ETL periodic (backup)**

**Evidence (HIGH confidence):**
- Mailerlite API supports `subscriber.created` webhook via REST API (`POST /api/webhooks`)
- Webhook payload includes `source` field indicating subscriber origin
- Webhook setup requires only an API token (already available via ConnectionPort for tenants with Mailerlite connected)
- No complex user configuration needed -- webhook URL is system-managed, not user-configured

**Implementation approach:**
1. On Mailerlite connection setup: register webhook via `POST https://connect.mailerlite.com/api/webhooks` with events: `["subscriber.created"]` and our callback URL
2. Webhook handler: receive payload, extract email + source, call `CustomerService.identify()` with `lead_source="mailerlite"`
3. ETL backup: periodic sync (daily via ARQ cron) lists recent subscribers and reconciles with CRM

**Why both:** Webhooks provide real-time counts but can fail silently (server downtime, Mailerlite outage). ETL catches anything missed. This matches the user's preference from CONTEXT.md.

## Agency Cost Proration Research

**LATAM small-business agency model (MEDIUM confidence):**

Typical agency arrangements for LATAM small businesses:
1. **Social media manager** -- fixed monthly fee (e.g., $500-2000/mo) covering organic content creation and posting
2. **Paid campaign manager** -- fixed monthly fee + percentage of ad spend (e.g., $300 base + 15% of spend)
3. **Video specialist** -- fixed monthly or per-deliverable fee
4. **Full-service agency** -- bundled fee covering multiple services

**Recommended proration algorithm:**
- User inputs: monthly amount + category (organic_management, paid_management, video, full_service)
- System distributes:
  - `organic_management`: evenly across connected organic social channels
  - `paid_management`: proportional to ad spend per paid channel (from Stage 0 API data)
  - `video`: evenly across video-capable channels (IG, TikTok, YouTube)
  - `full_service`: evenly across all connected channels
- UI: simple form with 3-4 rows: service name, monthly cost, category dropdown

**Key principle (from user):** "La complejidad la debemos manejar nosotros" -- user enters simple monthly values, system handles proration.

## LLM Token Cost Tracking

**Implementation approach (Claude's Discretion):**

The ChatOrchestrator invokes `agent_app.ainvoke(initial_state)` which returns a result dict. The LLM provider (OpenAI/Anthropic) returns token usage in the response.

1. After `agent_app.ainvoke()`, extract `usage` from result metadata
2. Write a `journey_event` with `event_name="llm_token_usage"` and properties: `{input_tokens, output_tokens, model, channel_slug, cost_estimate}`
3. Cost estimate = `(input_tokens * input_rate + output_tokens * output_rate)` where rates are from `channel_cost_settings` with `cost_type="llm"`
4. Aggregate via SQL query on journey_events for the capture metrics endpoint

**Fallback:** If token extraction is complex due to LangGraph internals, start with a configurable per-conversation flat rate stored in cost settings.

## Conversion Rate Calculation

**Cross-stage conversion (Stage 0 -> Stage 1):**

- **Channel-matched (where possible):** For landing-form, match UTM parameters from Stage 0 (e.g., google-ads UTM -> landing-form capture). Requires UTM data in CRM profile traits.
- **Stage-level ratio (fallback):** Total Stage 1 leads / Total Stage 0 visitors = overall conversion rate. Apply this to messaging channels where cross-stage attribution isn't possible.
- Per CONTEXT.md: "Falls back to stage-level ratio for messaging channels where cross-stage attribution isn't possible"

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| customer_profiles without lead_source | lead_source field exists but not populated | Phase 3 added field | Must populate on profile creation |
| Sankey-only metrics | Stage detail panels with ChannelGroup pattern | Phase 4 | Reuse proven architecture |
| No cost tracking | Manual cost settings + API ad spend | Phase 5 (new) | Full investment tracking |

## Open Questions

1. **Token usage extraction from LangGraph**
   - What we know: `agent_app.ainvoke()` returns a state dict. OpenAI/Anthropic APIs include token usage in responses.
   - What's unclear: How LangGraph aggregates token usage across multi-step agent runs. May need to use LangSmith callbacks.
   - Recommendation: Start with per-conversation flat rate; add actual token tracking as enhancement.

2. **Existing profiles without lead_source**
   - What we know: Current profiles created by ChatOrchestrator have `lead_source = None`.
   - What's unclear: Whether to backfill existing profiles or only track new ones.
   - Recommendation: Only count going forward (net-new). Don't backfill -- it's unreliable and the feature is new.

3. **Telegram channel in capture**
   - What we know: ChatOrchestrator handles Telegram but `STAGE_CHANNEL_MAP["capture"]` doesn't include a Telegram channel.
   - What's unclear: Whether Telegram should be added to capture channels.
   - Recommendation: Not in scope for this phase. Can be added to channel registry later.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `backend/tests/conftest.py` |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAP-01 | Capture detail panel renders two groups | unit (frontend) | Manual verification | No - Wave 0 |
| CAP-02 | `/metrics/capture` returns lead counts by source channel | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_capture_metrics.py -x` | No - Wave 0 |
| CAP-03 | LeadCapturedEvent emitted on contact extraction | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_lead_captured_event.py -x` | No - Wave 0 |
| CAP-04 | Cost settings CRUD and cost calculation | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_capture_cost.py -x` | No - Wave 0 |
| CAP-05 | CAL calculation: Stage 0 investment / Stage 1 leads | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_cal_calculation.py -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/analytics/test_capture_metrics.py` -- covers CAP-02 (lead count aggregation)
- [ ] `tests/modules/analytics/test_lead_captured_event.py` -- covers CAP-03 (event emission + CRM handling)
- [ ] `tests/modules/analytics/test_capture_cost.py` -- covers CAP-04 (cost settings CRUD + calculation)
- [ ] `tests/modules/analytics/test_cal_calculation.py` -- covers CAP-05 (CAL formula)
- [ ] Alembic migration for `channel_cost_settings` table

## Sources

### Primary (HIGH confidence)
- `backend/src/modules/analytics/application/services/metrics_service.py` -- MetricsService pattern, get_attraction_metrics() as template
- `backend/src/modules/analytics/application/services/channel_registry.py` -- STAGE_CHANNEL_MAP["capture"] with 6 channels already defined
- `backend/src/modules/analytics/application/dto/attraction_dto.py` -- DTO patterns (ChannelMetricDTO, TrafficGroupDTO, etc.)
- `backend/src/modules/crm/infrastructure/models/customer_model.py` -- CustomerProfileModel with lead_source, first_seen_at fields
- `backend/src/modules/crm/application/services/customer_service.py` -- CustomerService.identify() for identity resolution
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` -- ChatOrchestrator.process_chat_flow() where LeadCapturedEvent should be emitted
- `backend/src/shared/domain/events.py` -- EventBus with after-commit dispatch pattern
- `backend/src/modules/crm/domain/events.py` -- SaleCompletedEvent/ChurnEvent as event templates
- `frontend/src/features/marketing-studio/` -- AttractionDetail, ChannelGroup, ChannelRow, useAttractionDetail, metrics-api patterns
- `.planning/phases/05-stage-1-captura/05-UI-SPEC.md` -- Complete UI design contract

### Secondary (MEDIUM confidence)
- [Mailerlite Webhooks API](https://developers.mailerlite.com/docs/webhooks) -- subscriber.created webhook with source field, API-managed webhook registration

### Tertiary (LOW confidence)
- LLM token tracking via LangGraph -- needs validation during implementation
- Agency cost proration categories -- based on general LATAM market knowledge, needs user validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, patterns proven in Phase 4
- Architecture: HIGH -- directly follows AttractionDetail pattern with CRM data source
- Pitfalls: HIGH -- identified from actual code analysis (lead_source not set, slug mismatches, dedup)
- Cost tracking: MEDIUM -- new subsystem, no existing pattern to follow; model design is straightforward
- Mailerlite integration: HIGH -- API docs confirm webhook support with minimal setup

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable -- all internal patterns, Mailerlite API stable)
