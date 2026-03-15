---
phase: 02-provider-adapter-infrastructure
plan: 01
subsystem: database, api, infra
tags: [sqlalchemy, pydantic, abc, etl, alembic, domain-enums, provider-adapter]

# Dependency graph
requires:
  - phase: 01-critical-bug-fixes
    provides: "Stable Meta API v24.0 and tenant-isolated SDK pattern"
provides:
  - "CostType, MetricUnit, ExtractionStatus domain enums"
  - "ConnectionPort ABC and ConnectionCredentials value object"
  - "BaseMetricsProvider ABC and ExtractedMetric model"
  - "4 ETL SQLAlchemy table models (staging, official, extraction_runs, aggregations)"
  - "COST_TYPE_MAP with 16 initial channel/stage mappings"
  - "Extended ChannelMetricDTO with cost_type, unit, currency, last_updated"
  - "TenantModel.extraction_priority for scheduler ordering"
  - "Alembic migration for all ETL tables + tenant priority"
affects: [02-02, 02-03, 02-04, 03-etl-pipeline, 04-dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns: [provider-adapter-abc, domain-port-abc, encrypted-monetary-columns, composite-indexes-for-etl]

key-files:
  created:
    - backend/src/modules/analytics/domain/enums.py
    - backend/src/modules/analytics/domain/ports.py
    - backend/src/modules/analytics/domain/exceptions.py
    - backend/src/modules/analytics/domain/models.py
    - backend/src/modules/analytics/infrastructure/providers/base.py
    - backend/src/modules/analytics/infrastructure/models/staging_metrics_model.py
    - backend/src/modules/analytics/infrastructure/models/official_metrics_model.py
    - backend/src/modules/analytics/infrastructure/models/extraction_run_model.py
    - backend/src/modules/analytics/infrastructure/models/metric_aggregation_model.py
    - backend/src/modules/analytics/application/cost_type_mapping.py
    - backend/alembic/versions/a1b2c3d4e5f6_add_etl_infrastructure_tables_and_tenant_priority.py
    - backend/tests/modules/analytics/conftest.py
    - backend/tests/modules/analytics/test_cost_type.py
    - backend/tests/modules/analytics/test_provider_adapter.py
    - backend/tests/modules/analytics/test_connection_port.py
  modified:
    - backend/src/modules/analytics/application/dto/attraction_dto.py
    - backend/src/modules/iam/infrastructure/models/tenant_model.py
    - backend/alembic/env.py

key-decisions:
  - "ChannelMetricDTO value/cost changed from int to float for ETL precision (backward compatible)"
  - "EncryptedJSON used for spend/revenue columns in staging and official tables"
  - "Composite indexes designed for ETL query patterns (tenant+provider+date) and dashboard patterns (tenant+channel+date)"
  - "Manual Alembic migration written since Docker was unavailable for autogenerate"

patterns-established:
  - "Provider ABC pattern: new providers implement BaseMetricsProvider without modifying service/API layers"
  - "ConnectionPort ABC: analytics domain accesses credentials via port interface, not direct import"
  - "Domain enums as str Enum: serializable, JSON-friendly, used as column values"

requirements-completed: [INFRA-01, INFRA-02, INFRA-04]

# Metrics
duration: 6min
completed: 2026-03-15
---

# Phase 2 Plan 01: Domain Contracts and ETL Infrastructure Summary

**Domain enums, ABC interfaces (ConnectionPort + BaseMetricsProvider), 4 ETL table models, cost type mapping, and ChannelMetricDTO extension for provider-adapter infrastructure**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-15T16:19:55Z
- **Completed:** 2026-03-15T16:26:31Z
- **Tasks:** 2
- **Files modified:** 21

## Accomplishments
- Complete domain type system: CostType (4 values), MetricUnit (4), ExtractionStatus (5) as str enums
- Provider adapter pattern: BaseMetricsProvider ABC with extract_metrics/provider_name/rate_limit_config -- new providers implement one class
- ConnectionPort ABC bridges analytics and connections bounded contexts without coupling
- 4 ETL tables with composite indexes optimized for both extraction and dashboard query patterns
- 16-entry cost type mapping for financial classification of channel metrics
- 24 passing tests covering all contracts via TDD

## Task Commits

Each task was committed atomically:

1. **Task 1: Domain contracts -- enums, ports, exceptions, provider ABC** - `6ae6f3f` (feat, TDD)
2. **Task 2: ETL database models, tenant priority, DTO extension, cost mapping, migration** - `39c4c8b` (feat)

## Files Created/Modified
- `backend/src/modules/analytics/domain/enums.py` - CostType, MetricUnit, ExtractionStatus str enums
- `backend/src/modules/analytics/domain/ports.py` - ConnectionPort ABC + ConnectionCredentials model
- `backend/src/modules/analytics/domain/exceptions.py` - ConnectionRevokedException, TokenRefreshFailed
- `backend/src/modules/analytics/domain/models.py` - Domain value objects placeholder
- `backend/src/modules/analytics/infrastructure/providers/base.py` - BaseMetricsProvider ABC + ExtractedMetric
- `backend/src/modules/analytics/infrastructure/models/staging_metrics_model.py` - Raw ETL landing zone
- `backend/src/modules/analytics/infrastructure/models/official_metrics_model.py` - Validated dashboard data
- `backend/src/modules/analytics/infrastructure/models/extraction_run_model.py` - ETL run tracking
- `backend/src/modules/analytics/infrastructure/models/metric_aggregation_model.py` - Pre-computed rollups
- `backend/src/modules/analytics/application/cost_type_mapping.py` - COST_TYPE_MAP + get_cost_type()
- `backend/src/modules/analytics/application/dto/attraction_dto.py` - Extended with cost_type, unit, currency, last_updated
- `backend/src/modules/iam/infrastructure/models/tenant_model.py` - Added extraction_priority field
- `backend/alembic/env.py` - Registered analytics ETL models for autogenerate
- `backend/alembic/versions/a1b2c3d4e5f6_*.py` - Migration for 4 ETL tables + tenant priority

## Decisions Made
- ChannelMetricDTO value/cost changed from int to float -- Pydantic float accepts int, so all existing code passing int values (e.g., `value=0`) remains valid
- EncryptedJSON used for spend/revenue columns to encrypt monetary data at rest, matching existing pattern from ChannelConnectionModel.credentials
- Composite indexes designed per query access pattern: (tenant_id, provider, metric_date) for ETL writes, (tenant_id, channel_slug, metric_date) for dashboard reads
- Manual Alembic migration written because Docker daemon was not accessible in this session

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker daemon not accessible from WSL2 environment (no sudo access to start service). Alembic migration was written manually instead of using autogenerate. Migration must be applied when Docker is available: `docker exec -t visionarias_brain_dev alembic upgrade head`
- Local Python environment lacks project dependencies (passlib, etc.), so ETL model import verification was done via AST parsing and syntax checks rather than full import

## User Setup Required

None - no external service configuration required. However, the Alembic migration needs to be applied in Docker:
```bash
docker exec -t visionarias_brain_dev alembic upgrade head
```

## Next Phase Readiness
- All domain contracts stable -- Plans 02 and 03 can implement against these interfaces
- Plan 02 (Meta/Google provider adapters) can subclass BaseMetricsProvider
- Plan 03 (scheduler/orchestrator) can use ExtractionRunModel and TenantModel.extraction_priority
- Plan 04 (API endpoints) can use extended ChannelMetricDTO with cost_type fields

---
*Phase: 02-provider-adapter-infrastructure*
*Completed: 2026-03-15*
