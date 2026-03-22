# Phase 6: Stage 2 Nutricion - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Nurturing detail panel showing which nurturing activities are converting leads into marketing-qualified prospects (MQLs). Two channel groups: Retargeting Omnichannel (Meta/Google/TikTok retargeting campaigns filtered to MOFU) and Automation (Mailerlite newsletters + AI SDR follow-up). Backend `/metrics/nurturing` endpoint tracking MQL conversion via lead_score threshold crossing. Mailerlite webhook integration for real-time email engagement scoring. Campaign-level drill-down for both retargeting and email channels. Cost of nurturing per MQL calculated at panel and group levels.

Stage 2 focuses exclusively on **direct actions toward known leads** — retargeting via custom audiences and personalized automation. Organic content (IG/FB/TikTok/YouTube posts) is NOT included here — it's already measured in Stage 0 (Attraction) and cannot be attributed to specific leads via platform APIs.

</domain>

<decisions>
## Implementation Decisions

### Retargeting Campaign Classification (Combined Strategy)
- **Audience-first, objective-second** approach to classify campaigns as TOFU vs MOFU:
  1. If adset uses **Custom Audience** (website visitors, email list, engagement audience) → **Retargeting (Stage 2)** regardless of campaign objective
  2. If no Custom Audience, classify by objective: Awareness/Reach → Stage 0, Traffic/Engagement/Leads → Stage 0 (cold), Sales/Conversions → Stage 3
  3. **Manual override** available in settings — user can reclassify campaigns between stages if auto-mapping fails
- Applies uniformly to Meta, Google Ads, and TikTok
- Meta API: read `custom_audiences` from adset targeting; objectives use ODAX enum (OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT, OUTCOME_LEADS, OUTCOME_SALES)
- Google Ads: remarketing lists and Customer Match = retargeting; Display with remarketing = MOFU
- TikTok: Custom Audiences for retargeting; campaign objective as fallback

### Channel Grouping (2 Groups)
- **Retargeting Omnichannel**: meta-retargeting, google-retargeting, tiktok-retargeting
- **Automatizacion**: mailerlite, ai-sdr
- NO organic content group — organic is Stage 0 only (cannot attribute to specific leads, APIs don't filter by "leads only")
- Available (unconnected) channels shown at bottom with "Configurar" badge — only channels relevant to nurturing that the connections module supports or plans to support

### Retargeting Metrics Per Channel
- Three metrics per channel: **Reach + Clicks + Spend** (no Conversions — those belong in Stage 3)
- Secondary line: "{N} campanas activas" (campaign count)
- Group header totals: Total Reach | Total Clicks | Total Spend
- Collapsable drill-down: click channel row to expand and see individual MOFU campaigns with their metrics

### Provider Architecture for Retargeting
- **Reuse existing providers** (MetaProvider, GoogleAdsProvider, TikTokProvider) with a `stage` filter parameter
- `provider.extract(tenant_id, stage="nurturing")` applies the combined classification logic internally
- `provider.extract(tenant_id, stage="attraction")` returns TOFU campaigns (existing behavior)
- No new provider classes needed — DRY approach

### Mailerlite Engagement
- Metrics: **Emails Sent + Open Rate + Click Rate** (3 classic email marketing metrics)
- Collapsable drill-down: by default shows aggregate metrics. Click to expand and see **each campaign individually** with its own sent/open/click metrics
- Secondary line on collapsed view: "Ultima: [campaign name]"
- Aggregate calculation: total emails = sum(sent), open rate = weighted avg(open_rate), click rate = weighted avg(click_rate)

### Mailerlite → Lead Scoring Flow
- **Webhook real-time + ETL backup** dual strategy
- Real-time: Mailerlite webhook → `/webhooks/mailerlite` → create journey_event (email_opened/email_clicked) → EventBus.publish(EngagementEvent) → LifecycleService.recalculate_score() → if score >= 40: stage = MQL
- Backup ETL (every 6h): Mailerlite API → campaign stats → sync missing events → recalculate affected scores
- Existing scoring weights apply: email_opened = 2.0 pts, email_clicked = 3.0 pts

### AI SDR as Nurturing Channel
- Role: **Follow-up automatico post-captura** — after capturing a lead, the SDR follows up via the same channel (IG DM, WhatsApp) to maintain interest, send relevant content, answer questions
- Metrics: **Follow-ups enviados + Response Rate** (primary: count, secondary: "X respuestas (Y%)")
- Source: journey_events where event_name = 'sdr_followup_sent' / 'sdr_followup_replied'
- Scoring impact: message_sent = 4.0 pts (existing weight in scoring.py)
- **Current state**: AI SDR does not implement follow-up yet (in construction). Build the panel structure with proper metrics, show real data from message_sent events if available, "Proximamente" badge otherwise. When follow-up is implemented, events will flow naturally

### ManyChat Role
- **ManyChat = infrastructure, not a visible channel** — it's the platform that powers messaging channels (IG DM, FB Messenger, WhatsApp)
- Does NOT appear as a row in the panel
- If automated sequences exist, extract metrics (Sent, Delivered, Read, Clicked per flow) from ManyChat API and aggregate into the corresponding messaging channels
- ManyChat API provides: Sent, Delivered, Read, Clicked per sequence/flow

### Mini Funnel
- Same pattern as Stage 1: **Leads (8,500) → MQLs (2,100) = 24.7%**
- MQL = customer_profiles where lifecycle_stage >= MQL AND transitioned in period
- Panel header KPIs: **Total MQLs | Conversion Rate | Cost per MQL** (3 KPIs, consistent with Stage 1)

### Cost Tracking
- **Extend CaptureCostService** → generic StageCostService pattern
- Cost per MQL = Total nurturing spend / Total new MQLs
- **Per-group cost breakdown**: Retargeting cost/MQL (ad spend only) and Automation cost/MQL (email + SDR costs) shown in group headers
- **Combined cost/MQL** shown in panel header KPI
- Cost sources:
  1. Retargeting spend: **AUTO** from ad platform APIs (Meta/Google/TikTok retargeting campaign spend)
  2. Mailerlite subscription: **MANUAL** config by user (same ChannelCostSettingModel pattern)
  3. AI SDR token cost: **AUTO** from token usage per conversation
  4. ManyChat licensing: **MANUAL** config, shared with Stage 1
- **Split by activity** for shared costs: ManyChat and AI SDR costs split between Stage 1 (capture) and Stage 2 (nurturing) based on event_type in journey_events. Capture conversations → Stage 1, follow-up conversations → Stage 2

### Claude's Discretion
- Exact Custom Audience detection logic per platform (API field mapping for audience types)
- Campaign objective → stage mapping edge cases
- Mailerlite webhook endpoint implementation and event validation
- ManyChat API integration for sequence metrics extraction
- ETL backup sync implementation details
- Collapsable component design (animation, state management)
- Available channels list (which non-connected nurturing platforms to show)
- Error/stale UX casuistry for nurturing-specific scenarios
- ChannelCostSettingModel extension for stage-aware cost assignment

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Analytics Pattern (Phase 4-5 reference)
- `backend/src/modules/analytics/api/metrics.py` — /metrics/attraction and /metrics/capture endpoint patterns to follow
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/capture_dto.py` — CaptureDetailDTO structure (groups, channels, header KPIs, mini funnel)
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP["nurture"] (currently only mailerlite + manychat, needs retargeting channels added)
- `backend/src/modules/analytics/infrastructure/repositories/capture_repository.py` — Repository pattern for stage-specific queries

### Cost Service
- `backend/src/modules/analytics/application/services/capture_cost_service.py` — CaptureCostService with manual costs, prorated agency costs, and CAL calculation. Extend for Stage 2

### CRM & Lead Scoring
- `backend/src/modules/crm/application/services/lifecycle_service.py` — LifecycleService.recalculate_score(), threshold transitions (MQL >= 40)
- `backend/src/modules/crm/domain/scoring.py` — Scoring weights: email_opened=2.0, email_clicked=3.0, message_sent=4.0
- `backend/src/modules/crm/domain/enums.py` — LifecycleStage enum (SUBSCRIBER, LEAD, MQL, SQL, etc.)
- `backend/src/modules/crm/infrastructure/models/customer_model.py` — CustomerProfileModel with lead_score, lifecycle_stage

### Provider Infrastructure
- `backend/src/modules/analytics/infrastructure/providers/base.py` — BaseMetricsProvider ABC (add stage filter parameter)
- `backend/src/modules/analytics/infrastructure/providers/registry.py` — ProviderRegistry for adapter registration

### Mailerlite Integration
- `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py` — Current MailerLite connector (API key verification, connection CRUD). Needs webhook endpoint + campaign data retrieval
- `backend/src/modules/connections/api/mailerlite.py` — MailerLite connection API endpoints

### Sales Agent (AI SDR)
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` — ChatOrchestrator (where follow-up events would be emitted)
- `backend/src/modules/crm/application/services/lifecycle_service.py` — EventBus subscription pattern

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx` — Detail panel pattern to replicate (header KPIs, mini funnel, channel groups, collapsable)
- `frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts` — Hook pattern for data fetching
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId, StageSummary, CaptureDetail types
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add NUTRICION case)

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseMetricsProvider` ABC + `ProviderRegistry`: Existing providers (MetaProvider, GoogleAdsProvider, TikTokProvider) can be extended with stage filter parameter
- `ChannelRegistry.get_available_channels("nurture")`: Returns connected/available split. STAGE_CHANNEL_MAP["nurture"] needs expansion (add retargeting channels)
- `MetricsCache` with per-stage TTL: nurture stage can use 300s default (like capture)
- `CaptureDetail.tsx` + `ChannelGroup` + `ChannelRow`: Frontend component pattern ready for replication with collapsable campaign drill-down
- `EventBus` (Phase 3): Class-level handler registry for engagement events → scoring
- `LifecycleService.recalculate_score()`: Full scoring engine with threshold-based MQL transitions
- `CaptureCostService`: Manual + automatic + prorated cost calculation. Extend for stage-aware splitting

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- Multi-metric ChannelRow with secondary line (Phase 4-5) — reuse for "N campanas activas" and "X respuestas (Y%)"
- Collapsable component pattern: new for Phase 6 (Mailerlite campaigns + retargeting campaigns)
- ConnectionPort for DDD-safe credential access
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks
- "Ultima actualizacion" timestamp at panel header

### Integration Points
- `MetricsDashboard.tsx`: Add `activeStage === 'NUTRICION' ? <NurtureDetail /> : ...` routing
- `StageSummary` mock data: Set `hasDetail: true` for NUTRICION stage
- `metrics.py` router: Register new `/metrics/nurturing` endpoint
- `STAGE_CHANNEL_MAP["nurture"]`: Add meta-retargeting, google-retargeting, tiktok-retargeting channels
- Existing ad platform providers: Add `stage` parameter for MOFU filtering
- `ChannelCostSettingModel`: Extend for stage-aware cost assignment
- `/webhooks/mailerlite`: New webhook endpoint for email engagement events

</code_context>

<specifics>
## Specific Ideas

- "Audience-first, objective-second" — retargeting classification uses Custom Audience as primary signal, campaign objective as secondary. Based on Meta/Google/TikTok best practices research
- "N campanas activas" secondary line on retargeting channels — gives context of retargeting effort per platform
- Collapsable campaign drill-down for BOTH Mailerlite and retargeting channels — click to expand and see individual campaigns with metrics
- "Cada plataforma tiene su propia nomenclatura pero a las finales siempre es lo mismo" — normalize platform-specific targeting fields to unified Custom Audience detection
- Organic content explicitly excluded from Stage 2 — it's measured in Stage 0 and cannot be attributed to specific leads. Stage 2 = direct actions on known leads only
- ManyChat = infrastructure not channel — powers messaging but doesn't appear as a row. Extract sequence metrics (Sent/Delivered/Read/Clicked) and aggregate to corresponding channels
- AI SDR follow-up not yet implemented — build structure, show real message_sent events if available, "Proximamente" badge otherwise. Future-proof design
- Per-group cost breakdown in group headers, combined cost/MQL in panel header — user wants granularity to see which nurturing type (retargeting vs automation) is more cost-effective

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-stage-2-nutricion*
*Context gathered: 2026-03-16*
