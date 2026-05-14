# T-fe-5 Impl Log — Dashboard Components (alone wave)

**Ticket:** T-fe-5  
**Story:** luana-vitalia-bootstrap  
**Session:** 4 (2026-05-14)  
**Builder:** frontend-developer (Sonnet)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, component structure | Named exports only; `"use client"` only on interactive components; hooks consumed via barrel |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup | Applied on every component: `role="alert"` for errors, `aria-busy` on loading, `aria-live="polite"` for async state changes, `role="status"` for loading skeletons, stable keys via entity `id` |
| `tessl__tailwind` | Utility classes + `cn()` — no inline `style={{}}` | All conditional classes via `cn()` |
| `tessl__nextjs-app-router-modularization` | All 8 components are interactive (state/effects/event handlers) | `"use client"` on all 8; no Server Component needed since these are client-side dashboards |

## TDD Workflow

### RED phase (prior context, session 4 start)
- `tests/unit/features/vitalia/components/treatment-followup-dashboard-client.test.tsx` — 10 tests
- `tests/unit/features/vitalia/components/compliance-page-client.test.tsx` — 14 tests (includes ComplianceEventRow + getSeverityBadgeVariant)
- `tests/unit/features/vitalia/components/compliance-stats-cards.test.ts` — pre-existing 10 tests
- `tests/unit/features/vitalia/components/treatment-timeline.test.ts` — pre-existing 6 tests

### GREEN phase (this session)
Implemented 8 new components:

1. `compliance-event-row.tsx` — exports `getSeverityBadgeVariant(severity) → "danger"|"warning"|"neutral"` as named utility; renders table row with severity badge, event type label from microcopy SSoT, masked patient ID, actor type
2. `compliance-page-client.tsx` — exports `generateCsvBlob(events): Blob` as named utility; reuses `ComplianceStatsCards`; filter bar (Tipo + Severidad selects); scrollable event table using `ComplianceEventRow`; CSV export CTA with `"idle"|"preparing"|"ready"` state cycle
3. `treatment-followup-dashboard-client.tsx` — uses `useTreatment` + `useTreatmentSnapshot` (polls 30s); reuses `TreatmentTimeline`; derives `milestones` from `current_step`; derives `dashboardStatus` from `paused_reason`; status banners (paused_safety_escalation = red, paused_awaiting_clinic = yellow, completed = green); `NextActionCard` with next scheduled date + adherence; CTA bar: "Tomar conversación" + "Enviar consentimiento" + "Ver audit log paciente"
4. `treatment-list-table.tsx` — paginated (PAGE_SIZE=10); `useTreatments` hook; adherence badge color-coded; keyboard-accessible row click
5. `patient-list-table.tsx` — PII displayed as-is (masked at BE); `usePatients` hook; clinic_type badge; page-by-page navigation
6. `patient-detail-panel.tsx` — `usePatient(id)` hook; medical_history_summary prose block; date formatted via `toLocaleDateString("es", ...)`
7. `patient-medical-pdf-upload.tsx` — `"idle"|"reading"|"uploading"|"success"|"error"` state machine; file-to-base64 via FileReader; drag-and-drop + click-to-open; 10 MB guard; PDF type guard; `usePatientUploadPdf` mutation; hidden native `<input type="file" accept="application/pdf" />`
8. `appointments-calendar-client.tsx` — `useBookings` hook; groups bookings by date (ISO slice 0:10); renders per-day sections with `role="list"`; status badge with Spanish labels

## Key Design Decisions

- `generateCsvBlob` exported from `compliance-page-client.tsx` for testability — no React render needed in tests
- `getSeverityBadgeVariant` exported from `compliance-event-row.tsx` for testability
- `toLocaleDateString("es", {...})` used only for display inside Client Components — BE dates are ISO 8601; `formatTenantDate*()` N/A in this brand vertical (no `useTenantLocale` hook exists in vitalia frontend)
- `@luana/core/scheduling` package not yet available in monorepo — `AppointmentsCalendarClient` uses `useBookings` directly per prior session decision
- All 8 components: named exports only, no defaults (architecture fitness gate)
- `style={{width: ...%}}` in `ComplianceStatsCards` (existing T-fe-3 component, pre-existing inline style for progress bar) — not touched

## Barrel updates

Added 16 new exports to `src/features/vitalia/index.ts` (8 components + 8 type exports + 2 utility function exports).

## Validators

V-F-11: `npx vitest run --coverage` — 199/199 PASS, coverage 99.31% stmts / 100% branches / 42.1% funcs — above 20% threshold.

A1 (treatment followup dashboard): 10/10 PASS  
A2 (compliance dashboard): 14/14 PASS  
TSC: 0 errors
