---
phase: 06-stage-2-nutricion
plan: 01
subsystem: api
tags: [fastapi, analytics, crm, mailerlite, webhook, arq, retargeting, mql]

# Dependency graph
requires:
  - phase: 03-crm-lifecycle-automation
    provides: LifecycleTransitionModel, LifecycleService.recalculate_score, scoring thresholds
  - phase: 05-stage-1-captura
    provides: CaptureMetricsRepository pattern, CaptureCostService pattern, MiniFunnelDTO
provides:
  - NurtureDetailDTO with retargeting and automation channel groups
  - NurtureMetricsRepository for MQL transition counting from lifecycle_transitions
  - StageCostService with per-group cost/MQL breakdown (retargeting vs automation)
  - GET /metrics/nurturing endpoint
  - POST /webhooks/mailerlite/{tenant_id} for real-time email scoring
  - run_mailerlite_etl_sync ARQ task (6h backup sync)
  - Provider stage filtering for retargeting campaigns (Meta, Google, TikTok)
  - STAGE_CHANNEL_MAP["nurture"] with 5 channels
affects: [06-stage-2-nutricion, frontend-nurture-panel]

# Tech tracking
tech-stack:
  added: []
  patterns: [per-group cost/MQL in TrafficGroupDTO totals, stage parameter on providers, webhook-to-scoring pipeline]

key-files:
  created:
    - backend/src/modules/analytics/application/dto/nurture_dto.py
    - backend/src/modules/analytics/infrastructure/repositories/nurture_repository.py
    - backend/src/modules/analytics/application/services/stage_cost_service.py
    - backend/tests/modules/analytics/test_nurture_metrics.py
    - backend/tests/modules/analytics/test_retargeting_filter.py
    - backend/tests/modules/analytics/test_mailerlite_webhook.py
    - backend/tests/modules/analytics/test_stage_cost_service.py
  modified:
    - backend/src/modules/analytics/application/services/metrics_service.py
    - backend/src/modules/analytics/application/services/channel_registry.py
    - backend/src/modules/analytics/api/metrics.py
    - backend/src/modules/analytics/infrastructure/providers/meta_provider.py
    - backend/src/modules/analytics/infrastructure/providers/google_ads_provider.py
    - backend/src/modules/analytics/infrastructure/providers/tiktok_provider.py
    - backend/src/modules/connections/api/marketing_webhooks.py
    - backend/src/modules/analytics/workers/tasks.py
    - backend/src/modules/analytics/workers/settings.py

key-decisions:
  - "StageCostService is generic (not nurture-specific) -- reusable for future stages"
  - "Per-group cost/MQL injected into TrafficGroupDTO.totals dict for frontend consumption"
  - "Mailerlite webhook looks up profile by primary_email (no find_by_email method existed)"
  - "Provider retargeting detection: Meta uses custom_audiences on adsets, Google/TikTok use campaign name heuristic as best-effort"
  - "Legacy /webhooks/mailerlite endpoint preserved for backward compatibility"
  - "ManyChat removed from nurture channel registry (infrastructure, not visible per CONTEXT.md)"

patterns-established:
  - "Stage parameter on providers: extract_metrics(stage='nurturing') filters to retargeting campaigns"
  - "Webhook-to-scoring pipeline: webhook creates journey_event, calls recalculate_score, commits"
  - "ETL backup sync: ARQ cron with idempotent dedup via campaign_id in properties JSONB"

requirements-completed: [NUT-02, NUT-03, NUT-04, NUT-05]

# Metrics
duration: 9min
completed: 2026-03-16
---

# Phase 06 Plan 01: Nurture Backend Summary

**MQL counting from lifecycle_transitions, Mailerlite webhook-to-scoring pipeline, retargeting provider filtering, StageCostService with per-group cost/MQL breakdown, and GET /metrics/nurturing endpoint**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-16T06:34:25Z
- **Completed:** 2026-03-16T06:43:27Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments
- NurtureDetailDTO, NurtureMetricsRepository, and StageCostService implement the full nurture metrics backend
- Mailerlite webhook creates journey_events and triggers lead score recalculation for MQL transitions
- Provider stage filtering enables retargeting campaign extraction via Meta custom_audiences, Google remarketing, TikTok custom audiences
- ETL backup sync (6h ARQ cron) ensures missed webhook events are recovered

## Task Commits

Each task was committed atomically:

1. **Task 0: Test stubs** - `d028b9c` (test)
2. **Task 1: Domain contracts, repository, cost service, channel registry** - `b52e2af` (feat)
3. **Task 2: MetricsService, API endpoint, providers, webhook, ETL sync** - `33d43fd` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/application/dto/nurture_dto.py` - NurtureDetailDTO, NurtureHeaderKpisDTO, CampaignMetricDTO
- `backend/src/modules/analytics/infrastructure/repositories/nurture_repository.py` - MQL counting, email event aggregation from CRM
- `backend/src/modules/analytics/application/services/stage_cost_service.py` - Generic stage cost service with per-group cost/MQL
- `backend/src/modules/analytics/application/services/metrics_service.py` - Added get_nurturing_metrics() with _NURTURE_GROUP_MAP
- `backend/src/modules/analytics/application/services/channel_registry.py` - Expanded nurture to 5 channels, removed manychat
- `backend/src/modules/analytics/api/metrics.py` - Added GET /metrics/nurturing endpoint
- `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` - Stage param + _extract_meta_retargeting (custom_audiences filter)
- `backend/src/modules/analytics/infrastructure/providers/google_ads_provider.py` - Stage param + _aggregate_retargeting (name heuristic)
- `backend/src/modules/analytics/infrastructure/providers/tiktok_provider.py` - Stage param + _extract_retargeting (name heuristic)
- `backend/src/modules/connections/api/marketing_webhooks.py` - New tenant-aware Mailerlite webhook + legacy endpoint
- `backend/src/modules/analytics/workers/tasks.py` - run_mailerlite_etl_sync with idempotent dedup
- `backend/src/modules/analytics/workers/settings.py` - Added ETL sync to functions and cron_jobs

## Decisions Made
- StageCostService is generic (not nurture-specific), reusable for future stage cost calculations
- Per-group cost/MQL injected into TrafficGroupDTO.totals dict (retargeting_totals["cost_per_mql"]) for frontend consumption
- No find_by_email method existed on CustomerRepository; webhook queries CustomerProfileModel.primary_email directly via SQLAlchemy select
- Provider retargeting detection is best-effort for Google/TikTok (campaign name heuristic); Meta uses proper custom_audiences adset filtering
- Legacy /webhooks/mailerlite endpoint preserved (no tenant_id) for backward compatibility with existing integrations
- ManyChat removed from nurture channels per CONTEXT.md (it's infrastructure, not a visible channel)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unused import lint warnings in meta_provider.py**
- **Found during:** Task 2
- **Issue:** Dict and Optional imports became unused after refactoring
- **Fix:** Removed unused imports
- **Files modified:** backend/src/modules/analytics/infrastructure/providers/meta_provider.py
- **Committed in:** 33d43fd (Task 2 commit)

**2. [Rule 2 - Missing Critical] Added legacy Mailerlite webhook endpoint**
- **Found during:** Task 2
- **Issue:** Existing /mailerlite endpoint would break if replaced entirely with tenant-aware version
- **Fix:** Kept legacy endpoint as /mailerlite (no tenant_id), added new /mailerlite/{tenant_id}
- **Files modified:** backend/src/modules/connections/api/marketing_webhooks.py
- **Committed in:** 33d43fd (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both auto-fixes necessary for correctness and backward compatibility. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Nurture backend complete, ready for frontend panel implementation (06-02)
- Provider retargeting methods ready for ETL extraction when stage parameter is passed
- Mailerlite webhook ready for testing once Mailerlite connection is configured

## Self-Check: PASSED

All 7 created files verified. All 3 task commits verified (d028b9c, b52e2af, 33d43fd).

---
*Phase: 06-stage-2-nutricion*
*Completed: 2026-03-16*
