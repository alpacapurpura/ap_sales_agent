---
gsd_state_version: 1.0
milestone: v19.0
milestone_name: milestone
status: executing
stopped_at: Completed 11-02-PLAN.md (Detail panel polish, channel icons, sidebar wiring)
last_updated: "2026-03-16T22:40:30.699Z"
last_activity: "2026-03-16 -- Completed plan 09-01 (Adoption backend + frontend: health tracking per offer, CSS health bar, TTV, bottleneck detection)"
progress:
  total_phases: 11
  completed_phases: 11
  total_plans: 31
  completed_plans: 31
  percent: 97
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15)

**Core value:** Business owner sees their entire customer lifecycle at a glance and understands where the funnel is healthy, leaking, or needs action.
**Current focus:** Phase 8 — Stage 4 Ventas

## Current Position

Phase: 9 of 11 (Stages 5-6 Adoption & Expansion)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-03-17 - Completed quick task 260317-h91: Fix frontend ESLint errors blocking GitHub Actions CI

Progress: [█████████▊] 97%

## Performance Metrics

**Velocity:**
- Total plans completed: 9
- Average duration: 4 min
- Total execution time: 0.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-critical-bug-fixes | 1 | 2 min | 2 min |
| 02-provider-adapter-infrastructure | 5 | 25 min | 5 min |
| 03-crm-lifecycle-automation | 2 | 11 min | 5.5 min |

**Recent Trend:**
- Last 5 plans: 02-03 (7 min), 02-04 (3 min), 02-05 (2 min), 03-01 (5 min), 03-02 (6 min)
- Trend: Stable

*Updated after each plan completion*
| Phase 03 P03 | 5 min | 2 tasks | 9 files |
| Phase 04 P01 | 9 min | 2 tasks | 18 files |
| Phase 04 P02 | 4min | 2 tasks | 8 files |
| Phase 04 P03 | 6min | 2 tasks | 1 files |
| Phase 05 P01 | 7min | 3 tasks | 18 files |
| Phase 05 P02 | 8min | 3 tasks | 10 files |
| Phase 06 P01 | 9min | 3 tasks | 16 files |
| Phase 06 P02 | 5min | 2 tasks | 10 files |
| Phase 06 P03 | 1min | 1 tasks | 1 files |
| Phase 07 P01 | 11min | 3 tasks | 12 files |
| Phase 07 P02 | 4min | 2 tasks | 9 files |
| Phase 08 P01 | 6min | 2 tasks | 11 files |
| Phase 08 P00 | 2min | 1 tasks | 6 files |
| Phase 08 P02 | 4min | 2 tasks | 9 files |
| Phase 09 P01 | 9min | 2 tasks | 13 files |
| Phase 09 P02 | 8min | 2 tasks | 14 files |
| Phase 10 P01 | 6min | 3 tasks | 13 files |
| Phase 10 P02 | 3min | 2 tasks | 5 files |
| Phase 10 P03 | 4min | 2 tasks | 10 files |
| Phase 11 P01 | 6 | 6 tasks | 8 files |
| Phase 11 P00 | 8 | 4 tasks | 7 files |
| Phase 11 P02 | 10 | 6 tasks | 15 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Provider adapter pattern chosen as architecture for source-agnostic design
- Roadmap: CRM is authoritative source of truth for conversion counts (never sum ad-platform conversions)
- Roadmap: Shopify uses test data behind feature flag until connection is repaired
- Roadmap: Stages 5-6 combined into one phase (both CRM-heavy retention lifecycle)
- 01-01: Meta API v24.0 chosen as target (latest stable, well within support window)
- 01-01: Per-instance FacebookAdsApi via FacebookSession replaces singleton init()
- 01-01: facebook-business pinned to >=22.0,<26.0
- [Phase 01]: asyncio.to_thread() used for all sync Google SDK calls in GA4 adapter and API routes
- 02-01: ChannelMetricDTO value/cost changed from int to float for ETL precision (backward compatible)
- 02-01: EncryptedJSON used for spend/revenue columns in ETL tables
- 02-01: Provider ABC pattern: new providers implement BaseMetricsProvider without modifying service/API layers
- 02-01: ConnectionPort ABC bridges analytics and connections bounded contexts
- 02-02: ConnectionPortImpl lives in connections module (not analytics) to keep repository access within bounded context
- 02-02: 5-minute proactive token refresh buffer prevents mid-extraction token expiry
- 02-02: Redis cache uses synchronous redis-py wrapped in async for interface consistency
- 02-02: ETLPipeline two-phase error handling: rollback on failure, then commit FAILED status
- 02-02: Official metrics upsert on (tenant_id, provider, channel_slug, metric_name, metric_date)
- 02-03: Late binding imports in ARQ tasks to decouple parallel plan execution
- 02-03: Health endpoint public (no tenant context); retry/status require X-Tenant-ID
- 02-03: ChannelRegistry uses ConnectionPort for connected/available split (DDD boundary)
- 02-03: Fibonacci backoff [1,1,2,3,5,8,13] min; permanent stop on ConnectionRevokedException
- 02-04: MetricsService constructor backward-compatible: cache and connection_port optional for sankey
- 02-04: AvailableChannelsDTO wraps unconnected channels as separate section in API response
- 02-04: Frontend ChannelSlug changed from union to string for fully dynamic channel rendering
- 02-04: Cache-first read pattern: MetricsCache checked before OfficialMetricsRepository
- 02-05: PROVIDER_TO_CHANNEL_TYPES uses plain strings to preserve DDD boundary (no connections import)
- 02-05: Internal/manual providers always classified as connected without ConnectionPort check
- 02-05: Attraction stage gets 3600s cache TTL; all other stages default to 300s
- 03-01: EventBus uses class-level _handlers dict (singleton pattern) -- no DI container needed
- 03-01: triggered_by uses String not PG Enum to avoid ALTER TYPE migration issues
- 03-01: LifecycleStage enum reused in lifecycle_transitions via create_type=False
- 03-02: Service-layer orchestration for scoring: CustomerService.track_event calls repo + LifecycleService
- 03-02: Fit score applied once via computed_traits flag (prevents re-adding on recalculation)
- 03-02: LifecycleTransitionModel.metadata renamed to transition_metadata (SQLAlchemy reserved attr)
- 03-02: SaleService decoupled from CRM -- imports only shared EventBus + domain events
- [Phase 03]: Score decay clamps to 0.0 when below 0.01 (exponential decay asymptote)
- [Phase 03]: Churn handler uses churn_detected event_name (matching ChurnEvent.create factory)
- [Phase 03]: Pipeline manual override and audit trail endpoints added to existing pipeline.py router
- 04-01: ChannelMetricDTO.value is computed @property for backward compat (returns first metric or 0.0)
- 04-01: AttractionDetailDTO groups: organic_social/ga4_search/paid/outbound (matching CONTEXT.md)
- 04-01: AI_REFERRER_DOMAINS configurable set for GA4 AI-search segmentation
- 04-01: Instagram shares/saves set to 0 in engagement breakdown (deprecated in Graph API v21+)
- 04-01: GoogleAdsAdapter lazy-imports google-ads package for graceful degradation
- [Phase 04]: Channel grouping via _GROUP_MAP: social->organic_social, search/direct->ga4_search, paid->paid, outbound->outbound
- [Phase 04]: Stale detection reads ExtractionRunRepository.get_latest() per provider with result caching
- [Phase 04]: Error messages mapped from extraction error keywords to Spanish user-facing strings
- [Phase 04]: UI visual polish deferred to Phase 11 based on user feedback
- 05-01: IdentityService.get_or_create_customer changed to return (profile, was_created) tuple for conditional event emission
- 05-01: CaptureMetricsRepository uses distinct profile_id as conversation approximation (JourneyEventModel lacks session_id)
- 05-01: Alembic migration created manually due to pre-existing duplicate revision ID issue
- 05-01: Agency cost proration distributes by category: organic_management, paid_management, video, full_service
- 05-02: Reused TrafficGroup type for both web_infrastructure and ai_agent capture groups
- 05-02: CostLink defaults to /growth/settings/costs route for cost configuration
- 05-02: ChannelRow conversations secondary line uses 10px muted text below leads metric
- 06-01: StageCostService is generic (not nurture-specific) -- reusable for future stages
- 06-01: Per-group cost/MQL injected into TrafficGroupDTO.totals dict for frontend consumption
- 06-01: Mailerlite webhook queries CustomerProfileModel.primary_email directly (no find_by_email method)
- 06-01: Provider retargeting detection: Meta uses custom_audiences on adsets, Google/TikTok use campaign name heuristic
- 06-01: Legacy /webhooks/mailerlite endpoint preserved for backward compatibility
- 06-01: ManyChat removed from nurture channels (infrastructure, not visible per CONTEXT.md)
- 06-02: CampaignDrillDown wraps ChannelRow with empty campaigns -- activates when backend provides campaign data
- 06-02: AI SDR shows Proximamente badge when metrics array empty or all zeroes
- 06-02: Per-group cost/MQL displayed in ChannelGroup summary when cost_per_mql in totals
- [Phase 06]: Added MailerLiteConnector alias to fix CamelCase import mismatch in tasks.py without modifying consumer code
- [Phase 07]: jsonb_extract_path_text used for JSONB property queries instead of getitem operator (SQLAlchemy JSONB operator compatibility)
- [Phase 07]: Appointment event handlers create own SessionLocal (follows existing sale_completed handler pattern)
- [Phase 07]: PATCH /agenda/{id}/status added for appointment status updates (no existing status-change endpoint)
- [Phase 07]: Abandoned cart detection deferred to background task (1h detection window requires periodic check, not synchronous webhook)
- [Phase 07]: OpportunityDetail panel matches NurtureDetail layout exactly (flex gap-6 KPIs, space-y-2 panel rhythm)
- [Phase 07]: Inline bottleneck badges computed from metric values in ChannelRow (no prop drilling)
- [Phase 07]: Proximamente badge extended to checkout-lp and link-enviado with sourceLabel context
- [Phase 08]: OfferReadPort follows ConnectionPort ABC pattern exactly: defined in analytics.domain.ports, implemented in offer module
- [Phase 08]: SaleStatus.COMPLETED and SaleStage enum members used directly for PG enum column filtering
- [Phase 08]: LifecycleTransitionModel.profile_id used for SQL count (not customer_id)
- [Phase 08]: VALUE_LEVEL_TO_TIER maps 7 OfferValueLevel values to 4 display tiers (backend only)
- [Phase 08]: Lazy imports inside test functions for RED-state stubs that fail individually per-test
- [Phase 08]: SalesBottleneck separate type from BottleneckData (different shape: message/tip vs metricLabel/currentRate/threshold)
- [Phase 08]: useSalesDetail follows useAuth+metricsApi pattern (matches existing hooks, not tenantId prop pattern)
- [Phase 08]: Dual currency formatting via Intl.NumberFormat with es-MX for MXN and en-US for USD
- [Phase 09]: HealthBar uses CSS proportional widths (no chart library) with min 1% visual width for non-zero segments
- [Phase 09]: BottleneckBanner reused from OpportunityDetail via BottleneckData type casting for adoption bottlenecks
- [Phase 09]: Header KPI customer counts use distinct total query to avoid double-counting across offers
- [Phase 09]: Renewal classification via jsonb_extract_path_text(metadata_info, event_name) = subscription_cycle
- [Phase 09]: Churn lost revenue estimated from last EXPANSION sale per churned customer via SQL window function
- [Phase 09]: KpiTooltip as reusable standalone component with shadcn Tooltip for plain-Spanish KPI hints
- [Phase 10]: Public NPS survey endpoints use token-based access without auth
- [Phase 10]: promote_to_evangelist uses lazy import of ReferralService to avoid circular dependency
- [Phase 10]: ReferralService uses secrets.token_urlsafe(6) with REF- prefix and 3-retry collision handling
- [Phase 10]: EvangelizationRepository uses sync DB queries called from async service (matching adoption/expansion pattern)
- [Phase 10]: K-Factor bottleneck: < 0.5 critical, < 1.0 warning; NPS response rate: < 15% critical, < 30% warning
- [Phase 10]: NPS proportional bar uses same CSS technique as HealthBar (min 1% visual width for non-zero segments)
- [Phase 10]: All 8 bowtie funnel stages now have dedicated detail panels (PlaceholderDetail only for future stages)
- [Phase 11]: mergeStageData() maps heterogeneous per-stage API shapes to unified StageSummary via switch/case per StageId
- [Phase 11]: StageSummary.mainKpi.value widened to number|string for dual-currency pre-formatted strings
- [Phase 11]: Stub components created instead of vi.mock: Vite resolves static imports before mock hoisting, stubs are more reliable
- [Phase 11]: @testing-library/user-event not installed in frontend container — Plan 11-01 must add it before click interaction tests can run
- [Phase 11]: channelIcons.ts uses lucide-react fallbacks for all channels; TikTok uses Radio, Meta Ads uses Zap
- [Phase 11]: SidebarContent renders stage-specific context banners via polymorphic switch(stageId)
- [Phase 11]: MetricSidebar accepts children ReactNode — SidebarContent injected from MetricsDashboard, static fallback preserved

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Meta API v19.0 is completely broken in production (HTTP 400).~~ FIXED in 01-01: updated to v24.0
- ~~Meta SDK singleton causes cross-tenant data leaks.~~ FIXED in 01-01: per-instance API pattern
- ~~CRM move_stage() is a pass placeholder.~~ FIXED in 03-02: PipelineService.move_stage delegates to LifecycleService.force_stage
- ~~CRM scoring thresholds (e.g., lead_score > 70 = MQL) need product input before Phase 3 implementation.~~ RESOLVED in 03-01: thresholds set at 10/40/70 per research recommendations
- TikTok token 24h expiry needs refresh job that differs from Google/Meta patterns.
- Stage 7 K-Factor depends on whether referral codes exist in CRM schema — verify before Phase 10.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260316-s5p | Fix Growth Studio metric buttons showing same values across tenants - add tenantId to React Query keys | 2026-03-17 | 10099cd | [260316-s5p-fix-growth-studio-metric-buttons-showing](./quick/260316-s5p-fix-growth-studio-metric-buttons-showing/) |
| 260317-h91 | Fix frontend ESLint errors blocking GitHub Actions CI (Link, Image, a11y) | 2026-03-17 | 2c53bb1 | [260317-h91-fix-frontend-eslint-errors-blocking-gith](./quick/260317-h91-fix-frontend-eslint-errors-blocking-gith/) |

## Session Continuity

Last session: 2026-03-17T17:29:52Z
Stopped at: Completed quick task 260317-h91 (Fix frontend ESLint errors blocking GitHub Actions)
Resume file: None
