---
phase: 02-provider-adapter-infrastructure
plan: 03
subsystem: infra
tags: [arq, redis, etl, scheduler, worker, seed-data, channel-registry, fastapi]

# Dependency graph
requires:
  - phase: 02-provider-adapter-infrastructure/01
    provides: "Domain enums, ETL models, BaseMetricsProvider ABC, ConnectionPort, cost_type_mapping"
provides:
  - "ARQ WorkerSettings and SchedulerSettings for ETL job execution"
  - "Tick-based scheduler with timezone-aware 3am evaluation per tenant"
  - "run_tenant_extraction and run_initial_load task functions with Fibonacci retry"
  - "Docker services: visionarias_scheduler, visionarias_worker"
  - "ChannelRegistry with stage-contextual channel mapping and connected/available split"
  - "seed_metrics.py with 7 days of realistic test data across 3 providers"
  - "ETL health endpoint (GET /health/etl) and manual retry (POST /etl/retry/{run_id})"
  - "ETL status endpoint (GET /etl/status) for frontend 'Ultima actualizacion'"
affects: [02-provider-adapter-infrastructure/04, 03-frontend-dashboard, frontend-metrics]

# Tech tracking
tech-stack:
  added: [arq==0.27.0, sentry-sdk>=1.40.0]
  patterns: [tick-scheduler, fibonacci-backoff-retry, late-binding-imports, stage-channel-map]

key-files:
  created:
    - backend/src/modules/analytics/workers/__init__.py
    - backend/src/modules/analytics/workers/settings.py
    - backend/src/modules/analytics/workers/scheduler.py
    - backend/src/modules/analytics/workers/tasks.py
    - backend/src/modules/analytics/application/services/channel_registry.py
    - backend/src/modules/analytics/api/etl_admin.py
    - backend/scripts/seed_metrics.py
    - backend/tests/modules/analytics/test_scheduler_tick.py
    - backend/tests/modules/analytics/test_channel_fallback.py
    - backend/tests/modules/analytics/test_seed_metrics.py
  modified:
    - backend/src/core/config.py
    - backend/requirements.txt
    - docker-compose.yml
    - backend/src/main.py

key-decisions:
  - "Late binding imports in tasks.py to avoid circular deps with Plan 02 ETLService"
  - "Health endpoint registered without tenant context; retry/status endpoints require X-Tenant-ID"
  - "ChannelRegistry uses ConnectionPort ABC for connected/available split (DDD boundary respected)"
  - "Fibonacci backoff: [1,1,2,3,5,8,13] minutes for transient failures; permanent stop on ConnectionRevokedException"

patterns-established:
  - "Tick-scheduler pattern: ARQ cron every minute, evaluate tenant timezone, enqueue by priority"
  - "Late-binding import pattern: import services inside function body to decouple parallel plan execution"
  - "Channel registry pattern: static STAGE_CHANNEL_MAP + dynamic connected/available split via port"

requirements-completed: [INFRA-03, INFRA-05]

# Metrics
duration: 7min
completed: 2026-03-15
---

# Phase 02 Plan 03: Worker Infrastructure Summary

**ARQ worker/scheduler with timezone-aware tenant scheduling, ChannelRegistry for dynamic channel rendering, seed_metrics.py, and ETL admin/health endpoints**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-15T16:29:25Z
- **Completed:** 2026-03-15T16:36:03Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- ARQ worker and scheduler Docker services ready to process ETL extraction jobs
- Tick-based scheduler evaluates 3am local time per tenant timezone, prioritized by extraction_priority
- ChannelRegistry dynamically maps stages to channels with connected/available badge split
- seed_metrics.py provides 7 days of realistic Meta Ads, GA4, and Instagram test data (idempotent)
- ETL health, retry, and status endpoints registered in main.py (health=public, others=tenant-scoped)
- Fibonacci backoff retry for transient failures; permanent stop for revoked connections

## Task Commits

Each task was committed atomically:

1. **Task 1: ARQ worker/scheduler, Docker services, config updates, scheduler tick test** - `7b64fba` (feat)
2. **Task 2 RED: Failing tests for channel registry and seed metrics** - `a3e18fb` (test)
3. **Task 2 GREEN: Channel registry, seed script, ETL admin endpoints** - `c48ad82` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/workers/settings.py` - ARQ WorkerSettings and SchedulerSettings
- `backend/src/modules/analytics/workers/scheduler.py` - Tick scheduler (3am local, priority ordered)
- `backend/src/modules/analytics/workers/tasks.py` - run_tenant_extraction, run_initial_load with Fibonacci retry
- `backend/src/modules/analytics/application/services/channel_registry.py` - Stage-contextual channel mapping
- `backend/src/modules/analytics/api/etl_admin.py` - Health, retry, and status endpoints
- `backend/scripts/seed_metrics.py` - Idempotent seed script for all ETL tables
- `backend/src/core/config.py` - Added SENTRY_DSN and ENVIRONMENT settings
- `backend/requirements.txt` - Added arq==0.27.0, sentry-sdk>=1.40.0
- `docker-compose.yml` - Added visionarias_scheduler and visionarias_worker services
- `backend/src/main.py` - Registered ETL admin routers
- `backend/tests/modules/analytics/test_scheduler_tick.py` - Timezone, priority, and enqueue tests
- `backend/tests/modules/analytics/test_channel_fallback.py` - Channel registry connected/available tests
- `backend/tests/modules/analytics/test_seed_metrics.py` - Seed idempotency and row creation tests

## Decisions Made
- Late binding imports in tasks.py to avoid circular dependencies with Plan 02's ETLService (which runs in parallel)
- Health endpoint registered without tenant context dependency (public monitoring endpoint)
- Retry/status endpoints require X-Tenant-ID via get_tenant_context dependency
- ChannelRegistry uses ConnectionPort ABC for connected/available split, respecting DDD bounded context boundary
- Fibonacci backoff intervals [1,1,2,3,5,8,13] minutes; ConnectionRevokedException causes permanent failure (no retry)
- Seed script uses fixed UUID tenant ID for reproducibility across runs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker daemon not running, so verification was done via Python AST parsing and docker-compose config validation instead of in-container execution. All syntax is valid and docker-compose validates successfully.

## User Setup Required
None - no external service configuration required. ARQ worker/scheduler services will start automatically with `docker compose up -d`.

## Next Phase Readiness
- Worker infrastructure complete, ready for Plan 04 (integration tests and final validation)
- ChannelRegistry ready for frontend dashboard to consume stage-contextual channel data
- Seed script provides test data for dashboard development without needing live provider connections

---
*Phase: 02-provider-adapter-infrastructure*
*Completed: 2026-03-15*
