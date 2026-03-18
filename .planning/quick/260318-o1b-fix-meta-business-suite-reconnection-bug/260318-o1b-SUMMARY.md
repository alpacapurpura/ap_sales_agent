---
phase: quick
plan: 260318-o1b
subsystem: connections
tags: [meta, oauth, reconnection, bug-fix]
dependency_graph:
  requires: []
  provides: [meta-disconnect-cleanup, meta-reconnect-state]
  affects: [connections-meta]
tech_stack:
  added: []
  patterns: [child-asset-deactivation, state-preservation]
key_files:
  created: []
  modified:
    - backend/src/modules/connections/api/meta.py
    - frontend/src/features/connections/components/meta-view.tsx
decisions:
  - Disconnect deactivates all child assets before master (prevents orphaned rows)
  - OAuth callback response includes is_connected for frontend verification
  - useSearchParams triggers loadAll re-fetch on OAuth redirect
metrics:
  duration: 2min
  completed: "2026-03-18T22:24:43Z"
---

# Quick Task 260318-o1b: Fix Meta Business Suite Reconnection Bug Summary

Disconnect endpoint now cleans up child asset connections and frontend preserves is_configured state, fixing the reconnection flow.

## What Changed

### Task 1: Backend disconnect cleanup + reconnect logging
- **Disconnect endpoint** now deactivates all child asset connections (facebook_page, instagram_account, meta_ads_account, meta_pixel, whatsapp_business_account) before deactivating the master META connection
- **OAuth callback** logs master re-activation after upsert for debugging
- **Callback response** includes `is_connected: true` field for frontend verification
- **Commit:** c29f579

### Task 2: Frontend state preservation + force-refresh on redirect
- **handleDisconnect** preserves `is_configured` in status state using functional update `setStatus((prev) => ...)` instead of overwriting entire state
- **useSearchParams** added to detect `?tab=meta` query parameter from OAuth callback redirect
- **loadAll useEffect** includes `tabParam` as dependency to force re-fetch when arriving from callback
- **Commit:** bbe100b

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

1. Backend syntax check: PASSED
2. Frontend lint: PASSED (0 warnings, 0 errors)
3. Disconnect endpoint includes `get_all_by_tenant_and_types` call: CONFIRMED (line 453)
4. Frontend preserves `is_configured` on disconnect: CONFIRMED (line 377)
5. MetaView re-fetches on `tabParam` change: CONFIRMED

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | c29f579 | fix(quick-260318-o1b): disconnect deactivates child assets + add reconnect logging |
| 2 | bbe100b | fix(quick-260318-o1b): preserve is_configured on disconnect + force-refresh on redirect |

## Self-Check: PASSED
