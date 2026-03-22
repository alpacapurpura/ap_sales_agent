# Phase 5: Stage 1 Captura - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Capture detail panel showing how many leads each channel captures and what each lead costs. Two channel groups: Web Infrastructure leads (landing-form, Mailerlite) and AI Agent conversational leads (IG DM, FB Messenger, TikTok DM, WhatsApp). Backend `/metrics/capture` endpoint aggregating CRM data. Full cost tracking system including platform costs, agency/third-party costs with intelligent proration. Cost of Acquisition per Lead (CAL) calculated at panel, group, and channel levels.

</domain>

<decisions>
## Implementation Decisions

### Lead Counting Logic
- A "captured lead" from AI Agent = email or phone successfully extracted during conversation (not just first message)
- Data sources: customer_profiles (primary count — net-new profiles by lead_source) + journey_events (extraction detail — which field captured, conversation context)
- Web infrastructure leads: landing page form submission creates profile directly + periodic Mailerlite sync pulls new subscribers from external Mailerlite forms (with deduplication via identity resolution)
- Mailerlite sync: if webhook only requires existing token, use both webhook (real-time) + ETL (backup). If requires complex user config, ETL periodic only. Claude/researcher to investigate and decide.
- Sales Agent emits LeadCapturedEvent via EventBus when it extracts email/phone. CRM listens, calls CustomerService.identify(), creates profile with lead_source = channel_slug
- Attribution: first-touch — the channel where person was first identified gets the lead credit. Subsequent channels add to profile but don't create new lead
- Count scope: net-new profiles only (created in period). Returning visitors don't count as new captures

### Channel Grouping & Metrics
- Two groups per CAP-01: **Web Infrastructure** (landing-form, mailerlite) and **AI Agent Conversational** (ig-dm, fb-messenger, tiktok-dm, whatsapp-inbound)
- Group header metrics: 3 values — Total Leads + Cost per Lead + Conversion Rate from Stage 0
- Per-channel row metrics: Leads + Cost + Conversion Rate (full detail per channel)
- AI Agent channels additionally show conversation volume: primary "X leads" + secondary line "de Y conversaciones"
- Web channels: landing-form and mailerlite as separate rows (not merged)
- Cross-stage conversion: channel-matched where possible (e.g., UTM on landing forms traces to Stage 0 source). Falls back to stage-level ratio for messaging channels where cross-stage attribution isn't possible
- Mini arrow funnel at panel top: "Visitors (45,000) → Leads (8,500) = 18.9%" — new visual pattern for Stage 1+
- Panel header KPIs: 3 values — Total Leads | Conversion Rate | CAL (Cost per Lead)
- CAP-05 CAL displayed at both levels: overall in panel header + per-group in group headers

### Cost Tracking Model
- **Full cost system built in this phase** — needed for accurate CAL and will serve all future stages (CAC in Stage 4, etc.)
- Per-channel platform costs: manual config by business owner in Growth Studio settings panel ("Costos de canales")
- Stage 0 paid channel costs: sourced from ad platform APIs (spend from Meta/Google/TikTok Ads — already built in Phase 4)
- **Agency/third-party costs**: user inputs monthly amounts. System prorate across channels intelligently. Researcher must investigate LATAM small-business agency models (fixed + variable fees, specialists by area like video/organic/paid) and propose clean proration UX
- LLM token costs: auto-calculated from token usage per conversation in sales_agent module × configurable cost-per-token rate
- Unconfigured cost: show "—" with small "Configurar costo" link to Growth Studio settings. Non-blocking — leads still display
- **Key principle**: total real investment = platform spend (API) + agency fees (manual) + tool subscriptions (manual) + LLM costs (auto). Complexity managed by system, user inputs simple monthly values

### Panel Layout & Display
- AI Agent channel rows: two-line metric — primary "45 leads" + secondary "de 140 conversaciones" (reuses Attraction engagement breakdown pattern)
- Zero-lead channels: show row with "0 leads" + subtle hint "Sin actividad en los últimos 30 días". Connected channels always visible
- Available (unconnected) channels: show with "Configurar" badge at bottom, same pattern as Attraction
- "Última actualización" timestamp at panel header (same pattern as Attraction)
- Error/stale UX: reuse Phase 4 pattern — last known value + yellow "desactualizado" badge + refresh button

### Claude's Discretion
- Mailerlite webhook vs ETL decision based on API requirements research
- Agency cost proration algorithm (after researcher investigates LATAM agency models)
- Exact Growth Studio settings panel layout for cost configuration
- Mini funnel arrow component design details
- Token tracking implementation in sales_agent module
- Channel-matched conversion rate algorithm (UTM parsing, source matching logic)
- Error state mapping for capture-specific scenarios

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CRM & Lead Management
- `backend/src/modules/crm/infrastructure/models/customer_model.py` — CustomerProfileModel with lead_source, lead_source_detail, first_seen_at fields
- `backend/src/modules/crm/application/services/customer_service.py` — CustomerService.identify() for identity resolution and profile creation
- `backend/src/modules/crm/infrastructure/repositories/customer_repository.py` — find_by_identity(), create_with_identity() methods

### Analytics Pattern (Phase 4 reference)
- `backend/src/modules/analytics/api/metrics.py` — /metrics/attraction endpoint pattern to follow
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/attraction_dto.py` — AttractionDetailDTO structure (groups, channels, metrics)
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP["capture"] with 6 channels already defined

### Sales Agent & EventBus
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` — ChatOrchestrator message handling flow (where LeadCapturedEvent should be emitted)
- `backend/src/modules/crm/application/services/lifecycle_service.py` — EventBus subscription pattern from Phase 3

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AttractionDetail.tsx` — Detail panel pattern to replicate
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add CAPTURA case)
- `frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts` — Hook pattern for data fetching
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId, StageSummary types

### Connections & Messaging Channels
- `backend/src/modules/connections/infrastructure/channels/instagram.py` — Instagram webhook normalization
- `backend/src/modules/connections/infrastructure/channels/whatsapp/interface.py` — WhatsApp provider pattern
- `backend/src/modules/connections/infrastructure/channels/telegram.py` — Telegram webhook normalization

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseMetricsProvider` ABC + `ProviderRegistry`: CRM-internal provider needed for lead counts (similar to CRMInternalProvider for Cold Contact)
- `ChannelRegistry.get_available_channels("capture")`: Already returns connected/available split for 6 capture channels
- `MetricsCache` with per-stage TTL: capture stage will use 300s default (CRM data changes faster than ad APIs)
- `AttractionDetail.tsx` + `ChannelGroup` + `ChannelRow`: Frontend component pattern ready for replication
- `EventBus` (Phase 3): Class-level handler registry for LeadCapturedEvent → CRM listener
- `CustomerService.identify()`: Full identity resolution with deduplication — exactly what lead capture needs

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- Multi-metric ChannelRow with engagement breakdown line (Phase 4) — reuse for "de X conversaciones"
- ConnectionPort for DDD-safe credential access
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks

### Integration Points
- `MetricsDashboard.tsx`: Add `activeStage === 'CAPTURA' ? <CaptureDetail /> : ...` routing
- `StageSummary` mock data: Set `hasDetail: true` for CAPTURA stage
- `metrics.py` router: Register new `/metrics/capture` endpoint
- `ChatOrchestrator`: Emit LeadCapturedEvent after successful contact info extraction
- `main.py`: Register EventBus handler for LeadCapturedEvent → CRM

</code_context>

<specifics>
## Specific Ideas

- "Ambos, tanto la suscripción desde la landing page como la sincronización de un nuevo contacto en mailerlite" — both direct form capture AND Mailerlite sync. External Mailerlite forms capture leads outside our system that we must pull in
- "de 140 conversaciones" pattern — AI Agent channels show conversation volume as context for lead extraction rate
- Mini arrow funnel: "Visitors (45,000) → Leads (8,500) = 18.9%" — new visual pattern for capture panel header
- Agency costs: "El usuario puede estar terciarizando el manejo de sus redes... cobran un fijo mensual + un variable". System must capture real total investment including agency fees, tool subscriptions, and platform spend. Research LATAM small-business agency models (video specialists, organic managers, paid campaign managers). User inputs simple monthly values, system handles proration complexity
- "La complejidad la debemos manejar nosotros" — user should never deal with allocation math. Simple inputs, intelligent system-side distribution
- "—" with "Configurar costo" link for unconfigured channels — non-blocking, leads still display

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-stage-1-captura*
*Context gathered: 2026-03-15*
