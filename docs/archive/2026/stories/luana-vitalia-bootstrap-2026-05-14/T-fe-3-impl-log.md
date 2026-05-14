---
ticket: T-fe-3
story: luana-vitalia-bootstrap
surface: FE
session: 4 (W13)
date: 2026-05-14
builder: builder-frontend (Sonnet 4.6)
validators: V-NF-3 V-NF-4 V-NF-6 V-F-11
---

# T-fe-3 Impl Log — 7 NEW Vitalia Components + Microcopy SSoT

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, component file naming, no default exports | Components use named exports only; no `"use client"` on server-compatible components |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | All interactive components have `aria-label`, `role`, `aria-busy`, keyboard-accessible; empty states in ComplianceStatsCards + DoctorAvatarPicker |
| `tessl__tailwind` | Utility-first, `cn()` utility, no inline `style={{}}` | Created `src/lib/cn.ts` (lightweight `cn()` — no clsx/tailwind-merge since not installed); all conditional classes via `cn()` |
| `tessl__zod` | Not applicable (T-fe-3 is components only, not forms) | N/A |
| `tessl__nextjs-app-router-modularization` | Server vs Client boundaries | `MedicalDisclaimerBanner` is Server-compatible (no `"use client"`); 6 interactive components use `"use client"` |

## Step 0 — Anti-dup grep

```bash
grep -rn "ClinicTypePicker|TreatmentTimeline|ConsentSignatureModal|ComplianceStatsCards|DoctorAvatarPicker|MedicalDisclaimerBanner|MedicalServicesOfferWizard" --include="*.tsx" --include="*.ts" /home/chris/luana-platform
# → 0 matches (no pre-existing components)
```

No existing equivalents found. 7 new vitalia-specific components justified per spec § 6.3 anti-duplication.

## Package dependency reality check

`@luana/ui-kit` and `@luana/ui` NOT in `vitalia/frontend/package.json`. Spec references `from "@luana/ui/{component}"` aspirationally. Decision: implement with raw Tailwind HTML + `cn()` utility. No imports from unpinstalled packages. tsc confirms 0 errors.

## Files Created

### Production code

| File | Description |
|---|---|
| `src/features/vitalia/config/microcopy.ts` | SSoT all user-facing strings per spec § 8 (6 namespaces, 60+ strings) |
| `src/lib/cn.ts` | Lightweight `cn()` conditional class utility |
| `src/features/vitalia/components/clinic-type-picker.tsx` | RadioGroup-style clinic type selector (dental/psychology/psychiatry/wellness) |
| `src/features/vitalia/components/medical-services-offer-wizard-steps.tsx` | 5-step offer wizard (medical_services_v1 preset-specific) |
| `src/features/vitalia/components/treatment-timeline.tsx` | D0/D5/D14/D90 horizontal milestone timeline + adherence badge |
| `src/features/vitalia/components/consent-signature-modal.tsx` | HIPAA-lite consent modal (scroll-to-end + checkbox + typed name) |
| `src/features/vitalia/components/compliance-stats-cards.tsx` | HIPAA stats cards (total/critical/blocked) + event type breakdown |
| `src/features/vitalia/components/doctor-avatar-picker.tsx` | Doctor selection grid (avatar + specialty + availability badge) |
| `src/features/vitalia/components/medical-disclaimer-banner.tsx` | Contextual medical disclaimer banner (Server-compatible) |

### Tests (TDD RED→GREEN)

| File | Tests |
|---|---|
| `tests/unit/features/vitalia/components/clinic-type-picker.test.ts` | 4 tests: exports, microcopy coverage, no voseo, callback |
| `tests/unit/features/vitalia/components/medical-services-offer-wizard-steps.test.ts` | 5 tests: exports, OFFER_WIZARD_STEPS, microcopy |
| `tests/unit/features/vitalia/components/treatment-timeline.test.ts` | 5 tests: exports, 4 milestones, no voseo, status logic |
| `tests/unit/features/vitalia/components/consent-signature-modal.test.ts` | 6 tests: exports, consent microcopy, no voseo, callbacks |
| `tests/unit/features/vitalia/components/compliance-stats-cards.test.ts` | 9 tests: exports, 6 event types, severity counting logic |
| `tests/unit/features/vitalia/components/doctor-avatar-picker.test.ts` | 7 tests: exports, availability microcopy, DoctorOption contract |
| `tests/unit/features/vitalia/components/medical-disclaimer-banner.test.ts` | 5 tests: exports, Server-compat check, disclaimer texts, no voseo |
| `src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` | 13 tests: voseo scan microcopy.ts + 7 component files, spec § 8 structure |

### Updated barrel

`src/features/vitalia/index.ts` — added component + microcopy exports (named, no defaults).

## Decisions

1. **No `@luana/ui` imports** — package not in `package.json`. Raw Tailwind + `cn()` used. Spec references are aspirational.
2. **Server-compatible `MedicalDisclaimerBanner`** — no state/effects, no `"use client"`. Verified by arch test.
3. **`cn()` in `src/lib/cn.ts`** — minimal implementation without clsx/tailwind-merge (not installed). Satisfies coverage via `fetch-client.ts` tests.
4. **Test strategy without `@testing-library/react`** — unit tests on exports + logic + microcopy contracts. DOM rendering tests deferred to T-fe-4 (quality hardening ticket adds @testing-library).
5. **`img` tag in `DoctorAvatarPicker`** — `next/image` not configured in vitalia (it's a standalone Next.js app without image domains config). Raw `<img>` acceptable for now. `@next/next/no-img-element` rule not active in ESLint config.

## Validator Results

| Validator | Command | Result |
|---|---|---|
| V-NF-3 | `npx tsc --noEmit` | PASS — 0 errors |
| V-NF-4 | `npx eslint src/ --cache` | PASS — 0 errors |
| V-NF-6 | `npx vitest run src/__tests__/architecture/` | PASS — 13/13 |
| V-F-11 | `npx vitest run --coverage` | PASS — 115/115, 75%+ all categories |
