---
phase: 04-stage-0-attraction-fix-validate
plan: 01
subsystem: api
tags: [meta-api, ga4, google-ads, tiktok, youtube, crm, provider-adapter, pydantic, dto]

# Dependency graph
requires:
  - phase: 02-provider-adapter-infrastructure
    provides: BaseMetricsProvider ABC, ProviderRegistry, ETLPipeline, ConnectionPortImpl
provides:
  - 6 concrete provider adapters (meta, google_analytics, google_ads, tiktok, youtube, crm_internal)
  - Multi-metric DTO contracts (MetricValueDTO, updated ChannelMetricDTO)
  - TikTokAdapter and GoogleAdsAdapter connection clients
  - STAGE_CHANNEL_MAP with metric_names per attraction channel
affects: [04-02-PLAN, 04-03-PLAN, metrics-service, frontend-channel-row]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Multi-metric DTO: ChannelMetricDTO.metrics list replaces single value field"
    - "Computed @property value for backward compatibility during DTO migration"
    - "Late-binding _register_all() pattern in registry.py avoids circular imports"
    - "One provider = multiple channel slugs (MetaProvider -> ig-organic, fb-organic, meta-ads)"

key-files:
  created:
    - backend/src/modules/analytics/infrastructure/providers/meta_provider.py
    - backend/src/modules/analytics/infrastructure/providers/google_analytics_provider.py
    - backend/src/modules/analytics/infrastructure/providers/google_ads_provider.py
    - backend/src/modules/analytics/infrastructure/providers/tiktok_provider.py
    - backend/src/modules/analytics/infrastructure/providers/youtube_provider.py
    - backend/src/modules/analytics/infrastructure/providers/crm_internal_provider.py
    - backend/src/modules/connections/infrastructure/channels/tiktok.py
    - backend/src/modules/connections/infrastructure/channels/google_ads.py
    - backend/tests/modules/analytics/test_multi_metric_dto.py
    - backend/tests/modules/analytics/test_meta_provider.py
    - backend/tests/modules/analytics/test_google_analytics_provider.py
    - backend/tests/modules/analytics/test_google_ads_provider.py
    - backend/tests/modules/analytics/test_youtube_provider.py
    - backend/tests/modules/analytics/test_tiktok_provider.py
    - backend/tests/modules/analytics/test_crm_internal_provider.py
  modified:
    - backend/src/modules/analytics/application/dto/attraction_dto.py
    - backend/src/modules/analytics/infrastructure/providers/registry.py
    - backend/src/modules/analytics/application/services/channel_registry.py

key-decisions:
  - "ChannelMetricDTO.value is a computed @property for backward compat (returns first metric or 0.0)"
  - "AttractionDetailDTO groups changed from organic/paid to organic_social/ga4_search/paid/outbound"
  - "TrafficGroupDTO.totals is dict[str, float] keyed by metric name instead of single total_value"
  - "AI_REFERRER_DOMAINS set is configurable for future AI search engine additions"
  - "Instagram shares/saves set to 0 in engagement breakdown (deprecated in Graph API v21+)"
  - "GoogleAdsAdapter uses lazy import of google-ads package for graceful degradation"

patterns-established:
  - "Multi-metric DTO: list[MetricValueDTO] replaces scalar value"
  - "Provider adapter: one class per API, multiple channel_slug values"
  - "Registry late-binding: _register_all() called at module import"

requirements-completed: [ATR-02, ATR-03, ATR-04, ATR-05]

# Metrics
duration: 9min
completed: 2026-03-15
---

# Phase 4 Plan 1: Provider Adapters & Multi-Metric DTO Summary

**6 provider adapters (Meta, GA4, Google Ads, TikTok, YouTube, CRM) with multi-metric DTO contracts and AI-search referrer segmentation**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-15T20:23:57Z
- **Completed:** 2026-03-15T20:32:53Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Multi-metric DTO contracts: MetricValueDTO, updated ChannelMetricDTO with backward-compat @property, restructured AttractionDetailDTO with 4 groups
- 6 provider adapters registered in PROVIDER_REGISTRY, each implementing BaseMetricsProvider ABC
- MetaProvider handles 3 channel slugs (ig-organic, fb-organic, meta-ads) via Graph API v24.0
- GoogleAnalyticsProvider segments GA4 traffic into google-organic, direct, ai-search-organic using AI_REFERRER_DOMAINS
- GoogleAdsProvider separates YouTube Ads (VIDEO campaigns) from Google Ads with cost_micros / 1_000_000 conversion
- TikTokAdapter and GoogleAdsAdapter connection clients created as async stubs
- 50 unit tests passing across 7 test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Multi-metric DTO contracts and connection client stubs**
   - `cf03d96` (test: failing DTO tests)
   - `a5b8da1` (feat: DTO implementation + connection stubs + channel registry)
2. **Task 2: Implement all 6 provider adapters and register in ProviderRegistry**
   - `697cddf` (test: failing provider tests)
   - `ff47dfe` (feat: 6 provider implementations + registry registration)

## Files Created/Modified
- `backend/src/modules/analytics/application/dto/attraction_dto.py` - Multi-metric DTO with MetricValueDTO list
- `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` - Instagram, Facebook, Meta Ads extraction
- `backend/src/modules/analytics/infrastructure/providers/google_analytics_provider.py` - GA4 source/medium segmentation
- `backend/src/modules/analytics/infrastructure/providers/google_ads_provider.py` - Google Ads + YouTube Ads separation
- `backend/src/modules/analytics/infrastructure/providers/tiktok_provider.py` - TikTok organic + ads
- `backend/src/modules/analytics/infrastructure/providers/youtube_provider.py` - YouTube organic views + engagement
- `backend/src/modules/analytics/infrastructure/providers/crm_internal_provider.py` - Cold contact from journey_events
- `backend/src/modules/analytics/infrastructure/providers/registry.py` - Late-binding registration of all 6 providers
- `backend/src/modules/connections/infrastructure/channels/tiktok.py` - TikTok Business API adapter stub
- `backend/src/modules/connections/infrastructure/channels/google_ads.py` - Google Ads GAQL adapter stub
- `backend/src/modules/analytics/application/services/channel_registry.py` - metric_names per attraction channel

## Decisions Made
- ChannelMetricDTO.value is a Pydantic computed_field @property for backward compatibility during migration
- AttractionDetailDTO groups changed from organic/paid to organic_social/ga4_search/paid/outbound matching CONTEXT.md
- TrafficGroupDTO uses totals dict keyed by metric name (e.g., {"reach": 5000, "engagement": 1200})
- AI_REFERRER_DOMAINS configurable set: perplexity.ai, chatgpt.com, claude.ai, copilot.microsoft.com, gemini.google.com, you.com, phind.com
- Instagram shares/saves set to 0 in engagement breakdown (deprecated in Graph API v21+, Jan 2025)
- GoogleAdsAdapter uses lazy import of google-ads package to avoid import errors when not installed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed YouTube provider test mock pattern**
- **Found during:** Task 2 (YouTube provider tests)
- **Issue:** asyncio.to_thread mock using `new_callable=lambda: AsyncMock` with `spec=` caused InvalidSpecError
- **Fix:** Changed to `new=AsyncMock(return_value=mock_overview)` pattern
- **Files modified:** backend/tests/modules/analytics/test_youtube_provider.py
- **Verification:** All 5 YouTube provider tests pass
- **Committed in:** ff47dfe (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test mock pattern fix, no scope change.

## Issues Encountered
None beyond the test mock pattern fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 6 provider adapters ready for ETL pipeline integration (Plan 02)
- Multi-metric DTO ready for MetricsService aggregation and frontend consumption
- STAGE_CHANNEL_MAP has metric_names for frontend rendering logic

## Self-Check: PASSED

- 16/16 files verified present
- 4/4 commits verified in git log

---
*Phase: 04-stage-0-attraction-fix-validate*
*Completed: 2026-03-15*
