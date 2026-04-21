# Offer Studio — Refactor Status (2026-04-20)

## COMPLETED — F1 → F9 (full brand-parity)

Offer Studio homologation with brand-studio architecture, UX, routing and
backend copilot layers. 7 phases landed in `development`; snapshot lives
in `docs/domains/offer-studio/architecture.md`.

### F1 — Foundation alignment (3 commits)

- ✅ **F1.1** — Actions registry homologated (`OFFER_STUDIO_ACTION_KEYS`
  tuple + `REGISTRY_ENTRIES` + idempotent `bootstrapOfferStudioActions()`
  + auto-bootstrap). 4 tests.
- ✅ **F1.2** — `useOfferSettings(offerId)` aggregator + 14 typed
  per-section updaters + wired `section-pages.tsx` factory. 8 tests.
- ✅ **F1.3** — `OfferStudioNavRail` + `OfferStudioBreadcrumb` flat
  components driven by `usePathname` + `lib/section-catalog.ts`. 17 tests.

### F2 — Polymorphic VariantRail (2 commits)

- ✅ **F2.1** — `components/variant-rail/` polymorphic dispatch per
  `variant_structure` (Temporal / Tier / Sku / Regional / Modality /
  Language / fallback). 72 tests across 8 files.
- ✅ **F2.2** — `useShouldShowVariantRail` + `buildNoVariantRedirect`
  for no-variant single-edition UX (lead-magnet / ebook). 9 tests.

### F3 — App route migration (1 commit)

- ✅ URL contract moved to brand pattern (`/offer/{id}/editor/{section}`
  replaces `/offer/{id}/edition/{code}/{section}`). 30-day redirect shim.
- ✅ `OfferShellLayout` client shell with conditional VariantRail mount.
- ✅ Collection routes (testimonials, instructors, faq) using brand's
  InstancePicker pattern.
- ✅ `EditionsManagementClient` + server route renders
  `VariantCollectionLandingPage` with polymorphic card dispatch.
- ✅ `/offer-studio/interview/` deleted (copilot is sidebar — D5).

### F4 — Retire legacy shell (commit `0018493b`)

- ✅ Deleted `OfferShell`, `OfferShellHeaderRow1`, `OfferShellContext` +
  `OfferAutoSaveContext` (no consumers need global shell state — FSD
  per-route state via URL + React Query).
- ✅ Deleted `editor/OfferEditSheetManager`, `OfferEditorContent`,
  `OfferSectionWrapper`, `OfferLivePreview`, `offer-section/OfferSection`.
- ✅ New flat `components/OfferShellHeader.tsx` (prop-based, no context).
- ✅ `layout.tsx` switched `OfferShell` → `OfferShellLayout`.
- ✅ Consumers in `/assets`, `/ventas`, `/campaigns`, `/editions/*`
  migrated to direct React Query + `use(params)` — no context dependency.
- ✅ `/editions/[editionId]/page.tsx` replaced with 307 redirect to
  `/editor`.

### F5 — Folder flatten + codemod (commit `3da7cd85`)

- ✅ Flatten `components/container/` → flat `components/` + symbol renames
  (`AutoSaveIndicator` → `OfferAutoSaveIndicator`, `OfferTabBar` →
  `OfferStudioTabBar`).
- ✅ Deleted `components/navigation/OfferNavRail.tsx` (replaced by F1.3),
  `components/container/EditionsRail.tsx` +
  `components/container/EditionsRailCollapsed.tsx` (replaced by F2,
  no live consumers).
- ✅ Renamed `components/wizard/` → `components/legacy-wizard/` (D8 —
  matches brand's `legacy-team/`).
- ✅ Redistributed `tests/` top-level to colocated `__tests__/` per
  domain (api, utils, hooks, components/dashboard, components/editions)
  + fixtures moved to `__tests__/fixtures/` feature root.
- ✅ Arch test allowlist shrunk (removed stale `OfferLivePreview` entry
  + re-pointed `tests/` paths to `__tests__/`).

### F6 — Delete config + dead editor subtree (commit `207adb32`)

- ✅ Deleted `config/offer-builder-config.ts` + `config/` dir (D9
  anti-pattern — replaced by `lib/section-catalog.ts` +
  `actions/registry.ts`).
- ✅ Deleted entire `components/editor/` tree (`sections/`, `ui/`,
  `components/` — all dead after config removal). 40+ files, ~7000 LOC.
- ✅ Cleaned stale entries in `design-system/registry-features.ts`.

### F7 — Copilot section tools

- ✅ **F7.1** (commit `5c4a6e44`) — backend
  `offer_section_tools.py` with 17 `@tool` functions grouped by section.
  No cross-module imports (lazy via `shared/links/ports/`). 51 tests +
  `test_copilot_registry.py` arch gate.
- ✅ **F7.2** (commit `ab5724a7`) — REST endpoint
  `POST /api/v1/copilot/offer-section-tools/{tool_key}` +
  frontend `useOfferCopilot` hook + `OfferSectionCopilot` sidebar
  component wired as `copilotSlot` in `section-pages.tsx` factory.
  `onApplyDraft` handler sets form values with `shouldDirty: true` —
  NO write-through (R3). 18 new frontend tests + 9 new backend tests.

### F8 — E2E Playwright suite (commit `e4f10568`)

- ✅ `fixtures/offer-studio.fixture.ts` — per-`variant_structure` mock
  factories (TIER, SKU, REGIONAL, MODALITY, LANGUAGE, TEMPORAL_COHORT,
  lead-magnet no-variant) + mocked copilot endpoint.
- ✅ `pages/offer-studio.page.ts` — POM extended (getVariantRail,
  getEditionsTab, getCopilotCards, applyCopilotSuggestion, ...).
- ✅ `specs/smoke/offer-studio-homologation.smoke.spec.ts` — Journeys
  A / E / F (7 tests).
- ✅ `specs/regression/offer-variants-polymorphic.regression.spec.ts` —
  one test per variant_structure (6 tests).
- ✅ `specs/regression/offer-copilot-per-section.regression.spec.ts` —
  suggestion cards, empty state, apply flow, error toast (7 tests).

### F9 — Final validation + docs (this commit)

- ✅ Full suite green: backend ruff + format + 948 tests (arch + copilot);
  frontend TSC + 1512 tests + 17 arch gates.
- ✅ `docs/domains/offer-studio/architecture.md` snapshot written —
  canonical post-refactor reference for folder layout, URL contract,
  SSoT catalog, shell composition, copilot integration, variant
  dispatch, test layout, arch fitness.
- ✅ PENDING-REFACTOR.md updated (this file).

---

## Quality snapshot post-F9

- **Backend:** 948 tests (arch + full copilot module) pass. Ruff + format
  clean. Zero new arch allowlist entries across all 7 phases.
- **Frontend:** 1512 vitest tests + 20 Playwright tests (pending
  container-based execution in CI). TSC clean. Zero new eslint errors
  introduced by F4-F9 (pre-existing errors in VariantCard / variant-
  structure-catalog / SectionCardLayout untouched).
- **Lines:** F4+F5+F6 removed ~9500 lines net; F7.2+F8 added ~1500 lines.

## Legacy scheduled for removal

- `app/.../offer/[id]/edition/{code}/[section]/[[...fieldId]]/page.tsx`
  — 30-day 301 redirect shim. Retires **2026-05-20**.

## Known follow-ups (non-blocking)

- Legacy wizard (`components/legacy-wizard/`) may evolve when
  Sprint 13 wizard gets retired.
- `/editions/[editionId]/*` subtree currently redirects to `/editor` —
  per-edition tab views (`/assets`, `/campaigns`, `/ventas`) are
  scheduled for deletion when EditionsManagementClient links swap to
  `?edition={code}` query params (FLOW-SPEC §4).
- Deep collection routes (`testimonials/`, `instructors/`, `faq/`)
  currently wire against stub APIs; real backend list endpoints pending.

---

## Verification commands (native WSL)

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest tests/architecture/ tests/modules/copilot/ -x -q

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache

# E2E (requires dev containers up: docker compose up -d)
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke --grep @smoke
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=regression --grep @regression
```

Architecture snapshot: `docs/domains/offer-studio/architecture.md`.
Session spec + decisions: `docs/ux-sessions/2026-04-20-offer-studio-homologation/`.
