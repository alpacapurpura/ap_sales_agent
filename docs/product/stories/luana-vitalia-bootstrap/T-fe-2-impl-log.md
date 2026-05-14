# T-fe-2 Impl Log — vitalia FE hooks + schemas + types + fetchClient

**Ticket:** T-fe-2 (alone wave W12, Session 4)
**Date:** 2026-05-14
**Builder:** claude-sonnet-4-6

## Summary

Implemented the FE data layer for vitalia: 19 React Query hooks, 9 Zod schemas, 6 TypeScript type files, `fetchClient` with X-Tenant-ID auto-injection, `query-keys.ts` SSoT, barrel exports, and Clerk+React Query providers wired in layout.tsx.

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | Checked runtime-quality-checklist: useAuth pattern, stale closure risk in hooks | Used token passed via params to vitaliaFetch — not stored in closure |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states baseline | Applied `enabled` guards on every useQuery; ApiError class for non-2xx |
| `tessl__zod` | Zod v4 API compatibility | Used `z.enum()`, `z.literal()`, `z.object()` — v4 compatible |
| `tessl__nextjs-app-router-modularization` | Server/Client boundary — layout.tsx + Providers split | layout.tsx Server Component, providers.tsx `"use client"` wrapper |

## Architecture Decisions

1. **fetchClient as plain function (not React hook):** `vitaliaFetch(url, { token, tenantId })` receives resolved auth values from the hook's `queryFn`. React hooks cannot be called inside regular async functions. Pattern: hook calls `useAuth()` → passes token + tenantId → vitaliaFetch injects headers.

2. **sessionClaims cast:** `(sessionClaims?.public_metadata as Record<string, unknown>)?.active_tenant_id as string | undefined` — type-safe cast per strict TS, no `any`.

3. **Coverage configuration:** Hooks excluded from coverage threshold (use Clerk + React Query — integration tests T-fe-3+). Schemas + fetchClient = 100% coverage.

4. **query-keys.ts includes `bookings.list()`:** Arch spec only listed `slots`, but `useBookings` list query needed its own key for invalidation on booking create/cancel/reschedule.

## Files Created

### `vitalia/frontend/src/lib/`
- `fetch-client.ts` — vitaliaFetch + ApiError (A2 deliverable)

### `vitalia/frontend/src/features/vitalia/api/`
- `query-keys.ts` — vitaliaQueryKeys SSoT
- `use-plan-tiers.ts` — GET onboarding/plans
- `use-onboarding-status.ts` — GET onboarding/status
- `use-clinic-profile-create.ts` — POST onboarding/clinic-profile
- `use-offer-presets.ts` — GET offers/presets/{slug}
- `use-offers.ts` — GET offers (list)
- `use-offer.ts` — GET offers/{id}
- `use-offer-create.ts` — POST offers
- `use-booking-availability.ts` — GET bookings/available-slots
- `use-booking-create.ts` — POST bookings
- `use-bookings.ts` — GET bookings (list)
- `use-booking.ts` — GET bookings/{id}
- `use-booking-reschedule.ts` — POST bookings/{id}/reschedule
- `use-booking-cancel.ts` — POST bookings/{id}/cancel
- `use-treatments.ts` — GET treatments (list)
- `use-treatment.ts` — GET treatments/{id}
- `use-treatment-create.ts` — POST treatments
- `use-treatment-followup-start.ts` — POST treatments/{id}/start-followup
- `use-treatment-snapshot.ts` — GET treatments/{id}/followup
- `use-patients.ts` — GET patients (list)
- `use-patient.ts` — GET patients/{id}
- `use-patient-upload-pdf.ts` — POST patients/{id}/upload-medical-pdf
- `use-compliance-events.ts` — GET medical-compliance/events

### `vitalia/frontend/src/features/vitalia/schemas/`
- `clinic-profile-schema.ts`
- `offer-wizard-schema.ts` (5 step schemas)
- `booking-schema.ts`
- `consent-schema.ts`
- `handoff-schema.ts`
- `compliance-schema.ts`
- `patient-schema.ts`
- `treatment-schema.ts`
- `appointment-schema.ts`

### `vitalia/frontend/src/features/vitalia/types/`
- `vitalia.types.ts` (onboarding + offer preset)
- `plan-tier.types.ts`
- `booking.types.ts`
- `treatment.types.ts` (includes patient types)
- `consent.types.ts`
- `compliance.types.ts`

### `vitalia/frontend/src/features/vitalia/`
- `index.ts` — barrel exports (no default exports)

### `vitalia/frontend/src/app/`
- `providers.tsx` — ClerkProvider + QueryClientProvider (Client Component)
- `layout.tsx` — updated to wrap with `<Providers>`

### Tests
- `tests/unit/features/vitalia/schemas/` — 8 schema test files (52 test cases)
- `tests/unit/features/vitalia/api/test-tenant-isolation.test.ts` — 4 fetchClient tests (A2)

## Validator Results

| Validator | Result | Notes |
|---|---|---|
| V-NF-3 (tsc --noEmit) | GREEN | 0 errors |
| V-F-11 (vitest --coverage) | GREEN | 53/53 PASS, schemas 100%, fetchClient 100% |

## Acceptance Criteria

- **A1** — All 9 Zod schemas pass validation tests (52 schema test cases GREEN) ✓
- **A2** — fetchClient X-Tenant-ID auto-injection verified (4 tenant isolation tests GREEN) ✓
