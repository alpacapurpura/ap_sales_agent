---
gsd_state_version: 1.0
milestone: v19.0
milestone_name: milestone
status: in-progress
stopped_at: Completed 03-01-PLAN.md
last_updated: "2026-03-15T18:55:10.000Z"
last_activity: "2026-03-15 — Completed plan 03-01 (EventBus, scoring config, lifecycle schema)"
progress:
  total_phases: 11
  completed_phases: 2
  total_plans: 10
  completed_plans: 8
  percent: 80
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15)

**Core value:** Business owner sees their entire customer lifecycle at a glance and understands where the funnel is healthy, leaking, or needs action.
**Current focus:** Phase 3 — CRM Lifecycle Automation

## Current Position

Phase: 3 of 11 (CRM Lifecycle Automation)
Plan: 1 of 3 in current phase (03-01 complete)
Status: In progress
Last activity: 2026-03-15 — Completed plan 03-01 (EventBus, scoring config, lifecycle schema)

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 4 min
- Total execution time: 0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-critical-bug-fixes | 1 | 2 min | 2 min |
| 02-provider-adapter-infrastructure | 5 | 25 min | 5 min |
| 03-crm-lifecycle-automation | 1 | 5 min | 5 min |

**Recent Trend:**
- Last 5 plans: 02-02 (7 min), 02-03 (7 min), 02-04 (3 min), 02-05 (2 min), 03-01 (5 min)
- Trend: Stable

*Updated after each plan completion*

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

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Meta API v19.0 is completely broken in production (HTTP 400).~~ FIXED in 01-01: updated to v24.0
- ~~Meta SDK singleton causes cross-tenant data leaks.~~ FIXED in 01-01: per-instance API pattern
- CRM move_stage() is a pass placeholder. All stages 1-7 will return zero until Phase 3 completes.
- ~~CRM scoring thresholds (e.g., lead_score > 70 = MQL) need product input before Phase 3 implementation.~~ RESOLVED in 03-01: thresholds set at 10/40/70 per research recommendations
- TikTok token 24h expiry needs refresh job that differs from Google/Meta patterns.
- Stage 7 K-Factor depends on whether referral codes exist in CRM schema — verify before Phase 10.

## Session Continuity

Last session: 2026-03-15T18:55:10.000Z
Stopped at: Completed 03-01-PLAN.md
Resume file: .planning/phases/03-crm-lifecycle-automation/03-01-SUMMARY.md
