---
phase: quick
plan: 260317-tng
subsystem: api
tags: [meta, oauth, connections, assets, facebook, instagram]

requires:
  - phase: none
    provides: n/a
provides:
  - create_asset() repository method for multi-row asset storage
  - Auto-sync of Meta business assets after OAuth callback
  - Frontend belt-and-suspenders sync call after OAuth redirect
affects: [connections, meta, webhooks]

tech-stack:
  added: []
  patterns: [create_asset for multi-row insert vs upsert for singleton rows, _sync_assets_for_tenant helper shared between oauth_callback and sync_assets endpoint]

key-files:
  created: []
  modified:
    - backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py
    - backend/src/modules/connections/api/meta.py
    - frontend/src/app/connections/meta/callback/page.tsx

key-decisions:
  - "create_asset() always inserts new row (never upserts) for asset channel types with multiple rows per tenant"
  - "Extracted _sync_assets_for_tenant() helper to DRY sync logic between oauth_callback and sync_assets endpoint"
  - "Auto-sync failure in oauth_callback is non-blocking (logged warning, OAuth still succeeds)"
  - "Frontend sync call is belt-and-suspenders: backend auto-syncs first, frontend retries if needed"

patterns-established:
  - "create_asset for multi-row channel types vs upsert for singleton channel types"

requirements-completed: [quick-260317-tng]

duration: 2min
completed: 2026-03-18
---

# Quick Task 260317-tng: Fix Meta Asset Sync Summary

**Fixed multi-asset storage bug (upsert overwriting 2nd+ assets) and added auto-sync after OAuth callback**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T02:24:43Z
- **Completed:** 2026-03-18T02:26:41Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Fixed repository bug where upsert() overwrote assets when tenant has multiple assets of the same channel type (e.g. 2 Facebook Pages)
- Added create_asset() method that always inserts new rows for asset channel types
- Auto-sync business assets immediately after OAuth callback (backend + frontend fallback)
- Extracted shared _sync_assets_for_tenant() helper to eliminate code duplication

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix repository asset creation and backend auto-sync** - `cdce0bd` (fix)
2. **Task 2: Frontend auto-sync after OAuth callback redirect** - `f4285dd` (feat)

## Files Created/Modified
- `backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py` - Added create_asset() method for multi-row asset storage
- `backend/src/modules/connections/api/meta.py` - Extracted _sync_assets_for_tenant() helper, auto-sync in oauth_callback, replaced upsert with create_asset for new assets
- `frontend/src/app/connections/meta/callback/page.tsx` - Added POST /assets/sync call after OAuth, updated toast message

## Decisions Made
- create_asset() always inserts (never upserts) for asset channel types where multiple rows per tenant per type are expected
- Auto-sync wrapped in try/except so OAuth connection succeeds even if asset sync fails
- Frontend sync is non-blocking fallback (catch swallows errors)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing langgraph import error in dev container prevents full module import test, but syntax check and create_asset attribute check both pass

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Meta OAuth flow now auto-syncs assets on connection
- Manual "Sincronizar activos" button still works as fallback
- Multiple assets of same type correctly stored as separate rows

---
*Phase: quick*
*Completed: 2026-03-18*
