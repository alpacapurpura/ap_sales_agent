---
phase: 10-stage-7-evangelizacion
plan: 01
subsystem: database, api
tags: [crm, nps, referral, evangelization, sqlalchemy, fastapi, alembic]

# Dependency graph
requires:
  - phase: 03-crm-lifecycle-automation
    provides: LifecycleService, CustomerProfileModel, LifecycleStage enum
provides:
  - ReferralCodeModel SQLAlchemy table (referral_codes)
  - NpsSurveyModel + NpsResponseModel SQLAlchemy tables
  - ReferralService (code generation, Shopify extraction)
  - NpsService (survey lifecycle, NPS scoring, candidate detection)
  - LifecycleService.promote_to_evangelist (atomic promotion + code gen)
  - CRM API endpoints for referrals and NPS at /api/v1/crm/referrals/* and /api/v1/crm/nps/*
  - 4 pytest stub files for downstream behavioral testing
affects: [10-02, analytics, evangelization-metrics]

# Tech tracking
tech-stack:
  added: []
  patterns: [token-based public endpoints, atomic service composition]

key-files:
  created:
    - backend/src/modules/crm/infrastructure/models/referral_code_model.py
    - backend/src/modules/crm/infrastructure/models/nps_models.py
    - backend/alembic/versions/010_referral_nps_tables.py
    - backend/src/modules/crm/application/services/referral_service.py
    - backend/src/modules/crm/application/services/nps_service.py
    - backend/src/modules/crm/api/referral.py
    - backend/src/modules/crm/api/nps.py
    - backend/tests/modules/analytics/test_evangelization_metrics.py
    - backend/tests/modules/analytics/test_k_factor.py
    - backend/tests/modules/crm/test_nps_service.py
    - backend/tests/modules/crm/test_referral_service.py
  modified:
    - backend/src/modules/crm/application/services/lifecycle_service.py
    - backend/src/main.py

key-decisions:
  - "Public NPS survey endpoints use token-based access without auth (GET/POST /survey/{token})"
  - "ReferralService uses secrets.token_urlsafe(6) with REF- prefix and 3 retry collision handling"
  - "promote_to_evangelist uses lazy import of ReferralService to avoid circular dependency"
  - "Alembic migration created manually (not auto-gen) to avoid revision ID conflicts per Phase 5 decision"

patterns-established:
  - "Token-based public endpoints: no get_current_user dependency for respondent-facing URLs"
  - "Atomic promotion: LifecycleService composes ReferralService for multi-step business operations"

requirements-completed: [EVA-02, EVA-03, EVA-04]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 10 Plan 01: CRM Evangelization Foundation Summary

**Referral code model + NPS survey/response tables with services for code generation, scoring, evangelist candidate detection, and atomic promotion via CRM API endpoints**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-16T20:09:47Z
- **Completed:** 2026-03-16T20:16:12Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- 3 new database tables (referral_codes, nps_surveys, nps_responses) with tenant isolation indexes
- ReferralService generates REF-XXXXXX codes with collision retry and supports Shopify discount code extraction
- NpsService manages full survey lifecycle: create, respond, score calculation (0-10 avg + standard NPS -100 to +100), evangelist candidate detection
- LifecycleService.promote_to_evangelist atomically transitions lifecycle stage and generates referral code
- 8 API endpoints: 3 for referrals (list, promote, generate) and 5 for NPS (create survey, get survey, respond, summary, candidates)
- 20 pytest stub tests across 4 files for downstream implementation

## Task Commits

Each task was committed atomically:

1. **Task 0: Create test stub files (Wave 0)** - `a1a4503` (test)
2. **Task 1: CRM models, migration, and services** - `72e0324` (feat)
3. **Task 2: CRM API endpoints for referrals and NPS** - `1f60385` (feat)

## Files Created/Modified
- `backend/src/modules/crm/infrastructure/models/referral_code_model.py` - ReferralCodeModel with tenant_id, customer_id FK, unique code, source tracking
- `backend/src/modules/crm/infrastructure/models/nps_models.py` - NpsSurveyModel (token-based) + NpsResponseModel (score, feedback, testimonial)
- `backend/alembic/versions/010_referral_nps_tables.py` - Creates 3 tables with indexes, downgrades cleanly
- `backend/src/modules/crm/application/services/referral_service.py` - Code generation, tenant listing, deactivation, Shopify extraction
- `backend/src/modules/crm/application/services/nps_service.py` - Survey CRUD, response handling, NPS scoring, candidate detection
- `backend/src/modules/crm/application/services/lifecycle_service.py` - Added promote_to_evangelist method
- `backend/src/modules/crm/api/referral.py` - GET /referrals, POST /promote, POST /generate
- `backend/src/modules/crm/api/nps.py` - POST /surveys, GET /survey/{token}, POST /survey/{token}/respond, GET /summary, GET /candidates
- `backend/src/main.py` - Registered referral and NPS routers under /api/v1/crm
- `backend/tests/modules/analytics/test_evangelization_metrics.py` - 5 stub tests
- `backend/tests/modules/analytics/test_k_factor.py` - 4 stub tests
- `backend/tests/modules/crm/test_nps_service.py` - 6 stub tests
- `backend/tests/modules/crm/test_referral_service.py` - 5 stub tests

## Decisions Made
- Public NPS survey endpoints (GET/POST /survey/{token}) use token-based access without authentication, matching the plan's requirement for respondent-facing URLs
- ReferralService uses secrets.token_urlsafe(6) with alphanumeric filtering and REF- prefix, with 3-retry collision handling on IntegrityError
- promote_to_evangelist uses lazy import of ReferralService inside method body to avoid circular import between lifecycle and referral services
- Alembic migration created manually with explicit revision ID per Phase 5 decision to avoid auto-gen conflicts

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker container missing API_URL env var prevents `alembic upgrade head` and direct Python import verification; verified migration file parses correctly via importlib and models via PYTHONPATH-based pytest execution instead

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All CRM models and services ready for Plan 10-02 (analytics evangelization endpoint)
- Referral codes, NPS responses, and evangelist lifecycle data available for metrics aggregation
- Test stubs ready to be filled in during Plan 10-02 implementation

---
*Phase: 10-stage-7-evangelizacion*
*Completed: 2026-03-16*
