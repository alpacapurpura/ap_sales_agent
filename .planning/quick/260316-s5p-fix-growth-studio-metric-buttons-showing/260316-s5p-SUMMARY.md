---
phase: quick-fix
plan: s5p
subsystem: ui
tags: [react-query, clerk, multi-tenant, cache-isolation]

requires:
  - phase: 04-attraction-detail
    provides: Growth Studio detail hooks pattern
provides:
  - Tenant-scoped React Query keys for all 8 Growth Studio detail hooks
affects: [marketing-studio, multi-tenant]

tech-stack:
  added: []
  patterns:
    - "orgId from useAuth() in all React Query keys for tenant cache isolation"

key-files:
  created: []
  modified:
    - frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts
    - frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts
    - frontend/src/features/marketing-studio/hooks/useNurtureDetail.ts
    - frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts
    - frontend/src/features/marketing-studio/hooks/useSalesDetail.ts
    - frontend/src/features/marketing-studio/hooks/useAdoptionDetail.ts
    - frontend/src/features/marketing-studio/hooks/useExpansionDetail.ts
    - frontend/src/features/marketing-studio/hooks/useEvangelizationDetail.ts

key-decisions:
  - "Used orgId from useAuth() (Clerk) rather than tenantId from URL params -- consistent with existing hook pattern"

patterns-established:
  - "All Growth Studio detail hooks include orgId in queryKey for tenant isolation"

requirements-completed: [TENANT-ISOLATION]

duration: 2min
completed: 2026-03-17
---

# Quick Fix S5P: Growth Studio Metric Detail Hook Cache Isolation

**Added orgId to all 8 Growth Studio detail hook query keys to prevent stale cross-tenant data on org switch**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-17T01:18:40Z
- **Completed:** 2026-03-17T01:20:24Z
- **Tasks:** 1
- **Files modified:** 8

## Accomplishments
- All 8 Growth Studio detail hooks now include orgId from useAuth() in their React Query keys
- Switching Clerk organizations triggers automatic refetch for all metric detail panels
- No stale cross-tenant cached data possible

## Task Commits

Each task was committed atomically:

1. **Task 1: Add orgId to all 8 Growth Studio detail hook query keys** - `d263f57` (fix)

## Files Modified
- `frontend/src/features/marketing-studio/hooks/useAttractionDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useNurtureDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useOpportunityDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useSalesDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useAdoptionDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useExpansionDetail.ts` - Added orgId to queryKey
- `frontend/src/features/marketing-studio/hooks/useEvangelizationDetail.ts` - Added orgId to queryKey

## Decisions Made
- Used orgId from useAuth() (Clerk) rather than tenantId from URL params -- plan specified useAuth() pattern and it is consistent with how these hooks already obtain getToken

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
- TypeScript full-project compilation OOMs in container with default heap -- resolved by increasing NODE_OPTIONS max-old-space-size to 4096MB
- 2 pre-existing type errors in PlaceholderDetail.tsx (unrelated to this fix) -- not in scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Growth Studio hooks are now tenant-isolated
- No blockers

---
*Quick Fix: 260316-s5p*
*Completed: 2026-03-17*
