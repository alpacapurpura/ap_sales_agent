# IMPL-LOG-fe — PR-1-pi1-bugs-hotfix (FE surface)

Builder: `nicolify-frontend` (Sonnet)
Date: 2026-04-30
Iteration: 1

## Bugs Fixed

### Bug #1 — Trailing slash missing in contacts API URL

**Root cause:** `use-contacts-query.ts:26` was calling `/api/v1/contacts?` without trailing slash. BE registers `@router.get("/")` → effective path `/api/v1/contacts/`. With `redirect_slashes=False` (mandatory rule), 404 was returned.

**Fix:** Changed `/api/v1/contacts?` → `/api/v1/contacts/?` in `use-contacts-query.ts:26`.

**Grep audit:** Checked all `${API_URL}/api/v1/[a-z-]+\?` patterns in frontend source. The `contacts` endpoint was the only one with this inconsistency — `use-contact-detail-query.ts` and `use-filter-schema-query.ts` both have path segments after the base path so they don't have the issue.

### Bug #4 — Next.js 16 campañas folder rename + sidebar entry

**Root cause 1:** Next.js 16 dev mode does not compile routes with non-ASCII characters (`ñ`) in folder names. The `campañas/` folder was never compiled.

**Root cause 2:** Sidebar `AppSidebar.tsx` had no link to the campañas/campanas route — it was orphaned.

**Fix 1:** `git mv frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campanas`

**Fix 2:** Added sidebar entry in `AppSidebar.tsx` "Closer Studio" group children:
```
{ title: "Campañas", href: `/${tenantId}/sales/campanas/nuevo`, icon: Megaphone }
```
(Megaphone already imported — used for Growth Studio parent, reused here for campaigns semantics)

**Fix 3:** Updated all URL references to use `campanas` (ASCII) instead of `campañas` or `campa%C3%B1as`:
- `CampaignNewClient.tsx`: comment + `router.push` URL
- `LaunchCampaignChoiceDialog.tsx`: comment + `router.push` URL
- `CampaignTag.tsx` (closer-studio): comment + Link href

## Files Modified (primary surface)

| File | Change |
|---|---|
| `frontend/src/features/crm-hub/api/use-contacts-query.ts` | Line 26: add `/` before `?` |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/` | Renamed to `campanas/` (git mv) |
| `frontend/src/components/shared/layout/AppSidebar.tsx` | Added "Campañas" child entry to Closer Studio nav group |
| `frontend/src/features/campaigns-lite/components/CampaignNewClient.tsx` | Comment + router.push URL: `campañas` → `campanas` |
| `frontend/src/features/crm-hub/components/LaunchCampaignChoiceDialog.tsx` | Comment + router.push URL: `campa%C3%B1as` → `campanas` |
| `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` | Comment + Link href: `campañas` → `campanas` |

## Files Modified (tests)

| File | Change |
|---|---|
| `frontend/src/features/crm-hub/api/__tests__/use-contacts-query.test.ts` | Added test asserting URL includes `/api/v1/contacts/?` (Bug #1 RED→GREEN) |
| `frontend/src/features/crm-hub/components/__tests__/LaunchCampaignChoiceDialog.test.tsx` | Updated existing test to assert `campanas` (not `campa%C3%B1as`) in URL |
| `frontend/e2e/specs/smoke/sales-campaigns-route.spec.ts` | New E2E smoke: `/sales/campanas/nuevo` renders, sidebar contains "Campañas" link |

## Quality Gates Output

### TypeScript (`tsc --noEmit`)
```
PASS — 0 errors
```

### ESLint
```
PASS — 0 errors (pre-existing warnings in AppSidebar.tsx and campaigns-lite are unchanged)
```

### Vitest (crm-hub + campaigns-lite)
```
Test Files  12 passed (12)
Tests  64 passed (64)
```

### Architecture fitness (20 tests)
```
Test Files  24 passed (24)
Tests  50 passed (50)
```

## Decisions

- Sidebar entry links directly to `/sales/campanas/nuevo` (wizard entry point) — not to a list page (`/sales/campanas`) since no list `page.tsx` exists at the root. Consistent with decision B in PR.md.
- `Megaphone` icon reused (already imported in AppSidebar for Growth Studio parent). Semantically appropriate for campaigns.
- `CampaignTag.tsx` href change: from `/campañas/{id}` to `/campanas/{id}` — both still lack `tenantId` prefix (pre-existing issue, not in scope of this PR).
