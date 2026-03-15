# Phase 4: Stage 0 Attraction Fix & Validate - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire real API data into the existing Attraction panel by implementing all provider adapters, registering them in the ETL pipeline, and proving the infrastructure works end-to-end. Redesign the ChannelRow component to support multiple metrics per channel. Build an automated validation script that compares ETL output against provider dashboards within 5% tolerance. All 13 attraction channels get adapters; missing API clients in the connections module are built as needed.

</domain>

<decisions>
## Implementation Decisions

### Metric Definitions Per Channel Type

**Organic Social (Instagram, YouTube, Facebook, TikTok, LinkedIn):**
- Two primary metrics displayed side by side: **Reach** (big number) + **Engagement** (big total)
- Engagement shows total value with a second line breakdown: likes, comments, shares, saves (smaller text)
- Per-platform API mapping (researcher to normalize nomenclature):
  - Instagram: reach + engagement (likes, comments, shares, saves)
  - YouTube: views + engagement (likes, comments, shares)
  - Facebook: reach + engagement (reactions, comments, shares)
  - TikTok: video_views + engagement (likes, comments, shares)
  - LinkedIn: impressions + engagement (likes, comments, shares) — shows in "available" section until connected

**GA4 Search Channels (google-organic, direct, ai-search):**
- Two primary metrics: **Sessions** + **Users** (unique visitors)
- GA4 runReport() with sessionSource/sessionMedium dimensions to segment traffic
- AI-search identified by referrer domains (perplexity.ai, chatgpt.com, claude.ai, etc.)

**Paid Channels (Meta Ads, Google Ads, TikTok Ads, YouTube Ads):**
- Four primary metrics: **Reach** + **Clicks** + **Conversions** + **Spend**
- Each platform has its own nomenclature but maps to these 4 universal columns
- Researcher to investigate per-platform field mappings and best practices for grouping campaign types
- YouTube Ads separate row from Google Ads (different placement, same Google Ads API credentials)

**Cold Contact (Outbound):**
- Two metrics: **Contacts** (outbound attempts) + **Responses** (replies received)
- Sourced from CRM journey_events where event_type relates to outbound activity
- Response rate derived. Value may be 0 if no outbound activity exists — that's honest
- Cost type: EXPENSE

### ChannelRow Redesign (Multi-Metric Layout)
- Current single-value ChannelRow replaced with multi-metric layout in this phase
- Connected channels: full rich layout with all metrics per channel type
- Available (unconnected) channels: simple row with channel name + "Configurar" badge only
- Other stages (5-10) will inherit this pattern — Phase 11 just polishes
- Group headers match channel metric structure:
  - Organic: Total Reach + Total Engagement
  - Paid: Total Reach + Total Clicks + Total Conversions + Total Spend
  - GA4 Search: Total Sessions + Total Users

### Error UX for Failed Extractions
- Show **last known value** + yellow "desactualizado" stale indicator + timestamp of last successful extraction
- Include a **refresh button** that triggers re-extraction of just that channel/provider block (15-min cooldown per Phase 2 decision)
- All error scenarios (token expired, rate limited, provider down, no data ever extracted) mapped at Claude's discretion
- Priority: keep UX fluid and simple — user should never feel stuck or confused

### "Última actualización" Timestamp
- Single timestamp at top of the Attraction panel header
- Shows the time of the most recent ETL extraction across all providers
- Format: "Última actualización: 14 Mar 2026, 03:15"

### Provider Adapter Scope
- Build ALL provider adapters for Stage 0 channels (not just connected ones):
  - MetaProvider (Instagram organic, Facebook organic, Meta Ads)
  - GoogleAnalyticsProvider (google-organic, direct, ai-search via GA4 runReport)
  - GoogleAdsProvider (Google Ads — search/display campaigns)
  - TikTokProvider (TikTok organic + TikTok Ads)
  - YouTubeProvider (YouTube organic + YouTube Ads via Google Ads API filtering)
  - CRMInternalProvider (Cold Contact — reads journey_events)
- If a provider's API client doesn't exist in the connections module, build it in this phase
- Each adapter implements BaseMetricsProvider ABC and registers in ProviderRegistry
- LinkedIn: no adapter needed — shows in "Canales disponibles" with "Configurar" badge

### Validation
- **Automated comparison script**: on-demand, not CI (requires real credentials)
- Run: `docker exec ... python scripts/validate_attraction.py`
- Calls provider APIs directly AND reads ETL tables, compares values
- **5% tolerance** threshold — values within 5% of provider dashboard are valid
- Tests ALL connected providers for Visionarias tenant (skip disconnected)
- Outputs a structured report: per-channel pass/fail with actual vs expected values
- Check which providers Visionarias actually has connected before running

### Claude's Discretion
- Per-platform API field mapping to unified metrics (Reach, Engagement, Clicks, Conversions, Spend)
- Campaign type grouping logic for paid channels (TOFU vs MOFU vs BOFU campaign classification)
- Error UX casuistry — map all possible failure scenarios and design appropriate user-facing states
- ChannelRow component design details (spacing, typography, responsive behavior)
- GA4 dimension/filter values for AI-search referrer detection
- Validation script implementation details and report format
- Which connections module API clients need to be built vs already exist

</decisions>

<specifics>
## Specific Ideas

- "Reach(views) + Engagement (likes, comments, shares, saves)" — user wants both metrics visible side by side per channel, with engagement showing total big + breakdown small
- "Reach + clicks + conversión + gasto" — for paid, the user explicitly wants to see the full funnel per channel: views → clicks → conversion → cost
- "Cada plataforma tiene su propia nomenclatura pero a las finales siempre es lo mismo" — researcher should normalize platform-specific terms to the 4 universal paid metrics
- "La experiencia de usuario debe ser fluida y sencilla" — error states should never leave the user confused. Last known value + stale badge + refresh button. Simple.
- "Toda la casuística la dejo a tu criterio pero ten mapeado todos los posibles escenarios" — Claude must enumerate all error/edge cases but keep the UX simple

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseMetricsProvider` ABC (analytics/infrastructure/providers/base.py): Ready for concrete adapters
- `ProviderRegistry` (analytics/infrastructure/providers/registry.py): Empty — needs adapter registration
- `ETLPipeline` (analytics/infrastructure/etl/pipeline.py): Full atomic pipeline — extract → stage → transform → official → aggregate → cache invalidate
- `ConnectionPortImpl` (connections/application/services/connection_port_impl.py): Credential retrieval with token refresh, ConnectionRevokedException on failure
- `GoogleAnalyticsAdapter.run_report()` (connections/infrastructure/channels/google_analytics.py): GA4 runReport() wrapper, accepts arbitrary dimensions/metrics, async
- `MetaAdapter` (connections/infrastructure/channels/meta.py): Per-instance API v24.0, Graph API calls
- `ChannelRegistry` (analytics/application/services/channel_registry.py): STAGE_CHANNEL_MAP with 13 attraction channels, splits connected/available
- `MetricsCache` (analytics/infrastructure/cache/metrics_cache.py): Redis with per-stage TTL (attraction=3600s)
- `OfficialMetricsRepository` (analytics/infrastructure/repositories/official_metrics_repository.py): Upsert + get_channel_summary for dashboard
- `AttractionDetail.tsx` (frontend): Renders ChannelGroup sections from backend data
- `ChannelRow` component: Current single-value layout — will be redesigned for multi-metric

### Established Patterns
- ETL batch model: extract daily, dashboard reads PostgreSQL (Phase 2)
- asyncio.to_thread() for sync Google SDK calls (Phase 1)
- Per-request adapter instantiation (Meta) — safe multi-tenant pattern
- ConnectionPort bridges analytics ↔ connections without DDD violations
- Cost type mapping: (channel_slug, stage_slug) → CostType enum

### Integration Points
- `ProviderRegistry`: Register all new concrete adapters here
- `STAGE_CHANNEL_MAP["attraction"]`: Already defines 13 channels — may need metric_names update
- `MetricsService.get_attraction_metrics()`: Currently returns single value per channel — needs to return multiple metrics
- `AttractionDetailDTO` (backend): Needs to carry multiple metrics per channel
- `ChannelMetric` type (frontend): Needs to support multiple metric values
- `ChannelRow.tsx` (frontend): Redesign for multi-metric display
- `connections/infrastructure/channels/`: May need new API clients for TikTok, YouTube Analytics

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-stage-0-attraction-fix-validate*
*Context gathered: 2026-03-15*
