---
phase: quick-260319-hdo
plan: 01
subsystem: database, api, ui
tags: [alembic, migration, assets, error-handling, gallery]

requires:
  - phase: none
    provides: none
provides:
  - "Nullable file_path column in assets table (fixes gallery upload 500)"
  - "Descriptive error messages in frontend asset API"
affects: [assets, gallery]

tech-stack:
  added: []
  patterns: [throwWithDetail helper for API error propagation]

key-files:
  created:
    - backend/alembic/versions/012_make_assets_file_path_nullable.py
  modified:
    - frontend/src/lib/api/assets.ts

key-decisions:
  - "Migration numbered 012 (not 011) due to existing 011_create_sales migration"
  - "Backfill NULL file_path from storage_path for data consistency"
  - "Set file_path DEFAULT '' as safety net for any remaining legacy code"

patterns-established:
  - "throwWithDetail: reusable async error extractor for fetch responses"

requirements-completed: []

duration: 3min
completed: 2026-03-19
---

# Quick Task 260319-hdo: Fix Image Gallery Upload Error Summary

**Alembic migration dropping NOT NULL on assets.file_path plus frontend throwWithDetail error propagation helper**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-19T17:37:07Z
- **Completed:** 2026-03-19T17:39:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Gallery image uploads no longer fail with NOT NULL violation on file_path
- Frontend upload/list/delete errors now surface actual server-provided detail instead of generic messages
- Existing NULL file_path rows backfilled from storage_path

## Task Commits

Each task was committed atomically:

1. **Task 1: Create idempotent migration to make file_path nullable** - `462b8d8` (fix)
2. **Task 2: Improve frontend upload error messages** - `1a120d9` (fix)

## Files Created/Modified
- `backend/alembic/versions/012_make_assets_file_path_nullable.py` - Alembic migration: DROP NOT NULL on file_path, backfill from storage_path, set default ''
- `frontend/src/lib/api/assets.ts` - Added throwWithDetail helper; upload/list/delete use it for descriptive errors

## Decisions Made
- Migration numbered 012 instead of plan's 011 because 011_create_sales already existed with down_revision 010_referral_nps
- Backfill strategy: copy storage_path to file_path for existing NULL rows (data consistency)
- Set column default to empty string as safety net for any legacy code paths

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Migration revision conflict with existing 011_create_sales**
- **Found during:** Task 1
- **Issue:** Plan specified revision 011 and down_revision 010_referral_nps, but 011_create_sales already used that down_revision, creating multiple Alembic heads
- **Fix:** Changed revision to 012_file_path_nullable with down_revision 011_create_sales; renamed file to 012_make_assets_file_path_nullable.py
- **Files modified:** backend/alembic/versions/012_make_assets_file_path_nullable.py
- **Verification:** `alembic upgrade head` succeeded, `alembic current` shows 012_file_path_nullable
- **Committed in:** 462b8d8

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix to maintain linear Alembic revision chain. No scope creep.

## Issues Encountered
None beyond the migration revision conflict addressed above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Gallery uploads should work immediately after deployment
- Frontend error messages will be visible on next client build

## Self-Check: PASSED

All files and commits verified.
