---
phase: quick
plan: 260319-udq
subsystem: auth, connections
tags: [meta, oauth, clerk, fetchClient, callback]

requires:
  - phase: quick-260317-tng
    provides: "Meta OAuth backend flow and asset sync"
provides:
  - "Resilient Meta OAuth callback with Clerk auth retry loop"
  - "Backend diagnostic logging for Meta OAuth troubleshooting"
  - "Error UI on callback page instead of silent redirect"
affects: [connections, meta]

tech-stack:
  added: []
  patterns:
    - "Auth retry loop: poll getToken() up to 10 times (500ms intervals) after full-page OAuth redirect"
    - "Bypass fetchClient for OAuth callbacks to avoid silent 401 redirect interceptor"
    - "sessionStorage for OAuth state preservation across redirects"

key-files:
  created: []
  modified:
    - frontend/src/app/connections/meta/callback/page.tsx
    - backend/src/modules/connections/api/meta.py

key-decisions:
  - "Use native fetch instead of fetchClient for OAuth callback POST to avoid silent 401/403 redirects"
  - "Poll getToken() with 500ms intervals (max 10 attempts) to handle Clerk session hydration delay after OAuth redirect"
  - "Add debug query param to /status endpoint for diagnostic info (guarded by auth)"

patterns-established:
  - "OAuth callback retry pattern: poll auth token after full-page redirect before making API calls"

requirements-completed: [fix-meta-oauth-callback]

duration: 8min
completed: 2026-03-19
---

# Quick Task 260319-udq: Fix Meta OAuth Callback Summary

**Fixed Clerk auth race condition and fetchClient silent redirect causing Meta OAuth callback to lose connection state after Facebook permission grant**

## Performance

- **Duration:** ~8 min
- **Tasks:** 3 (2 auto + 1 human verification)
- **Files modified:** 2

## Accomplishments
- Fixed auth race condition where Clerk session was not hydrated when getToken() was called after Facebook OAuth redirect
- Replaced fetchClient with native fetch on callback page to prevent silent 401 interceptor from redirecting away before error handling
- Added error state UI with retry button instead of silently redirecting to sign-in on failure
- Added backend diagnostic logging at each OAuth step (code exchange, profile fetch, upsert, verification read-back)
- Added debug mode to /status endpoint for connection troubleshooting
- User confirmed working: "ya funciono" (it worked)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix Meta OAuth callback -- auth race condition and silent failure handling** - `16d3411` (fix)
2. **Task 2: Add backend diagnostic logging and debug mode to Meta OAuth callback** - `adb1044` (feat)
3. **Task 3: Human verification** - Approved by user

## Files Created/Modified
- `frontend/src/app/connections/meta/callback/page.tsx` - Auth retry loop, native fetch, error UI, sessionStorage code persistence, diagnostic console logs
- `backend/src/modules/connections/api/meta.py` - Request logging, post-upsert verification, debug mode on status endpoint

## Decisions Made
- Used native fetch instead of fetchClient for the OAuth callback POST to maintain full error handling control
- 500ms polling interval with max 10 attempts (5s total) for Clerk token hydration -- balances UX speed with reliability
- Added debug query param to existing /status endpoint rather than creating a separate /debug-status endpoint

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both tasks completed cleanly, user verified the fix works end-to-end.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Meta OAuth flow fully functional
- Diagnostic logging in place for future troubleshooting

---
*Plan: quick-260319-udq*
*Completed: 2026-03-19*

## Self-Check: PASSED
- frontend/src/app/connections/meta/callback/page.tsx: FOUND
- backend/src/modules/connections/api/meta.py: FOUND
- Commit 16d3411: FOUND
- Commit adb1044: FOUND
