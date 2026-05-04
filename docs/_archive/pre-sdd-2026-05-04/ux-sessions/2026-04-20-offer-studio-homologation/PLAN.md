# PLAN — Offer Studio Homologation Execution Plan

**Session:** `2026-04-20-offer-studio-homologation`
**Target estimate:** 3 sprints (2 weeks each). Phases can overlap; F (copilot) requires A–D done.

---

## Phase A — Foundation scaffolding (1–2 días)

**Goal:** Create brand-studio-parity primitives. Zero deletion yet. Ship alongside legacy.

### Files to create
- `features/offer-studio/lib/section-catalog.ts`
- `features/offer-studio/hooks/use-field-routing.ts`
- `features/offer-studio/hooks/use-offer-settings.ts`
- `features/offer-studio/pages/SectionPage.tsx`
- `features/offer-studio/pages/section-pages.tsx`
- `features/offer-studio/actions/placeholders.tsx`
- `features/offer-studio/actions/registry.ts` (with `bootstrapOfferStudioActions`)

### Acceptance criteria
- `cd frontend && npx tsc --noEmit` passes.
- New files have colocated tests in `__tests__/` covering: catalog completeness, hook routing contract, factory output.
- Legacy components still work (no routes changed).

### Verification commands
```bash
cd frontend && npx vitest run src/features/offer-studio/__tests__/ src/features/offer-studio/lib/__tests__/ src/features/offer-studio/hooks/__tests__/
cd frontend && npx tsc --noEmit
```

### Feeds UI-SPEC
- `UI-SPEC-offer-studio-shell.md` §1–2 (section catalog + routing contract)

---

## Phase B — Schema/action registry migration (3–5 días)

**Goal:** All 11 sections render through `UniversalEditableSection` + actions registry. Delete legacy `*Form.tsx`.

### Files to create
- `actions/SocialProofPickerAction.tsx` (port from `components/social-proof/OfferSocialProofPicker.tsx`)
- `actions/InstructorsPickerAction.tsx`
- `actions/PaymentProviderPickerAction.tsx`
- `actions/SchedulingEventTypePickerAction.tsx`
- `actions/ValueStackBuilderAction.tsx`
- `actions/FAQBuilderAction.tsx`
- `actions/EditionPricingOverrideAction.tsx`
- `actions/GalleryPickerAction.tsx`

### Files to update
- `schemas/index.ts` — add side-effect import `import "../actions/registry"`
- `actions/registry.ts` — populate `REGISTRY_ENTRIES` with real actions

### Files to delete
- `components/editor/sections/*.tsx` (if present — hand-rolled forms)

### Acceptance criteria
- Every `action_key` declared in any `schemas/*.schema.ts` has a matching entry in registry.
- Arch test `test-no-missing-actions` (new, port from brand-studio) passes.
- `/test-frontend` passes (all 1063+ tests).

### Verification commands
```bash
cd frontend && npx vitest run src/features/offer-studio/actions/__tests__/ src/features/offer-studio/schemas/__tests__/
cd frontend && npx eslint src/features/offer-studio/ --cache --cache-location .eslintcache
```

### Feeds UI-SPEC
- `UI-SPEC-actions-registry.md` (deltа)

---

## Phase C — Shell + route restructure (5–7 días)

**Goal:** Swap legacy shell for brand-parity 3-col split-view. Update app routes. Delete modal sheet pattern.

### Files to create
- `features/offer-studio/components/OfferStudioNavRail.tsx` (flat)
- `features/offer-studio/components/OfferStudioBreadcrumb.tsx` (flat)
- `features/offer-studio/components/OfferStudioTabBar.tsx` (flat)
- `features/offer-studio/pages/CollectionLandingPage.tsx`
- `features/offer-studio/pages/CollectionDetailPage.tsx`
- `features/offer-studio/pages/EditionDetailPage.tsx`

### App routes to rewrite
```
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/layout.tsx       ← new OfferShellLayout
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/page.tsx          ← redirect → editor
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/page.tsx   ← new landing (onboarding or first section)
app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/[section]/[[...fieldId]]/page.tsx  ← generic
app/.../offer/[id]/editor/testimonials/page.tsx + /[testimonialId]/[[...fieldId]]/page.tsx
app/.../offer/[id]/editor/instructors/page.tsx + /[instructorId]/[[...fieldId]]/page.tsx
app/.../offer/[id]/editor/faq/page.tsx + /[faqId]/[[...fieldId]]/page.tsx
app/.../offer/[id]/editions/page.tsx
app/.../offer/[id]/editions/[editionId]/page.tsx
```

### Files to delete
- `features/offer-studio/components/container/OfferShell.tsx`
- `features/offer-studio/components/container/OfferShellHeaderRow1.tsx`
- `features/offer-studio/components/editor/OfferEditSheetManager.tsx`
- `features/offer-studio/components/editor/OfferEditorContent.tsx`
- `features/offer-studio/components/editor/OfferSectionWrapper.tsx`
- `features/offer-studio/context/OfferShellContext.tsx` + dir
- `features/offer-studio/config/` + dir
- `features/offer-studio/components/navigation/` (after move)
- `app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/edition/[code]/[section]/[[...fieldId]]/page.tsx`
- `app/.../offer-studio/offer/[id]/editions/[editionId]/{assets,ventas,landing,campaigns}/page.tsx`
- `app/.../offer-studio/interview/`

### Files to rename
- `components/navigation/OfferNavRail.tsx` → `components/OfferStudioNavRail.tsx`
- `components/container/OfferTabBar.tsx` → `components/OfferStudioTabBar.tsx`
- `components/container/EditionsRail*.tsx` → `components/EditionsRail*.tsx`
- `components/container/AutoSaveIndicator.tsx` → `components/OfferAutoSaveIndicator.tsx`
- `components/container/LandingActionButton.tsx`, `LandingKebabMenu.tsx`, `GenerateLandingConfirmDialog.tsx`, `OfferStatusSwitcher.tsx`, `OfferStatusChangeModal.tsx` → flat
- `components/wizard/` → `components/legacy-wizard/`

### Acceptance criteria
- All sections editable via deep-link URL.
- EditionsRail visible in Editor + Editions tabs only.
- Tabs navigate correctly between Editor / Editions / Assets / Knowledge / Campaigns / Ventas.
- `/test-frontend` passes.
- E2E smoke: open existing offer → click section in NavRail → click field → save → success.

### Verification commands
```bash
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke --grep "offer"
```

### Feeds UI-SPEC
- `UI-SPEC-offer-studio-shell.md` §3–5 (layout, tabs, editions rail, navigation)

---

## Phase D — Cleanup + arch tests (1–2 días)

**Goal:** Remove dead code, move tests, update arch test allowlists.

### Actions
- Move `features/offer-studio/tests/` content to colocated `__tests__/` directories.
- Verify arch tests pass without allowlist additions.
- Update `frontend/src/__tests__/architecture/*` allowlists to remove deleted files.
- Remove any dead imports.

### Acceptance criteria
- `grep -rn "OfferShell\|OfferEditSheetManager\|OfferEditorContent\|offer-builder-config" frontend/src/` → no hits.
- Frontend arch fitness tests all pass.
- `cd frontend && npx madge --circular src/ --extensions ts,tsx` — no new cycles.
- `npx knip` — no new dead code.

### Verification commands
```bash
cd frontend && npx vitest run src/__tests__/architecture/
cd frontend && npx madge --circular src/ --extensions ts,tsx
cd frontend && npx knip
```

---

## Phase E — Copilot form-runtime extension (2–3 días)

**Goal:** Add non-breaking `copilotSlot?: ReactNode` to `UniversalEditableSection`. Create `OfferSectionCopilot` component.

### Files to update
- `frontend/src/components/form-runtime/UniversalEditableSection.tsx` — add `copilotSlot?` prop, render in split-view layout.
- `frontend/src/features/offer-studio/pages/SectionPage.tsx` — pass `copilotSlot` prop.

### Files to create
- `frontend/src/features/offer-studio/components/OfferSectionCopilot.tsx`
- `frontend/src/features/offer-studio/hooks/use-offer-copilot.ts`

### Acceptance criteria
- Brand-studio pages still compile and render without `copilotSlot` (non-breaking).
- Offer-studio section pages render copilot column on right at ≥1024px.
- Collapse toggle persists to `localStorage`.
- `/test-frontend` passes. Copilot column keyboard-accessible.

### Verification commands
```bash
cd frontend && npx vitest run src/components/form-runtime/__tests__/
cd frontend && npx vitest run src/features/offer-studio/components/__tests__/OfferSectionCopilot
cd frontend && npx vitest run src/features/brand-studio/pages/__tests__/  # regression check
```

### Feeds UI-SPEC
- `UI-SPEC-copilot-sidebar.md`

---

## Phase F — Section-scoped copilot tools (backend) (3–5 días)

**Goal:** Wire 11 copilot tools (one per section) so sidebar suggestions become functional.

### Files to create
- `backend/src/modules/copilot/tools/offer_section_tools.py`
- `backend/tests/modules/copilot/test_offer_section_tools.py`

### Files to update
- `backend/src/modules/copilot/tools/registry.py` — register new tools under `entity_type="offer-section"`
- `frontend/src/features/offer-studio/hooks/use-offer-copilot.ts` — consume new tool endpoints

### Acceptance criteria
- Each section has at least 1 copilot tool (see FLOW-SPEC §10).
- HIGH_TICKET preset → pricing section surfaces tier template tool.
- RECURRING_BILLING → pricing section surfaces subscription setup tool.
- Copilot tool responses update form-runtime fields via `copilotSlot` bridge.
- Backend arch tests pass.

### Verification commands
```bash
cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q
cd backend && .venv/bin/pytest tests/architecture/ -x -q
```

### Feeds UI-SPEC
- `UI-SPEC-copilot-sidebar.md` §4 (tool integration points)

---

## Risk / rollback notes

| Risk | Mitigation |
|---|---|
| Legacy users have offers in flight when shell swaps | Feature flag `offer-studio-v2` for initial 48h. Rollback = flip flag. |
| `UniversalEditableSection` prop change breaks brand-studio | `copilotSlot` is optional with default undefined. Type test in brand-studio arch tests. |
| Deep-link URL change (`edition/[code]` removed) breaks bookmarks | 301 redirect from old pattern to new in `middleware.ts` for 30 days. |
| Copilot tools not ready by Phase E | Copilot sidebar ships with placeholders (same pattern as brand-studio placeholders). |
| Arch test allowlist churn | Each phase includes arch test step. Never merge phase if allowlist grows. |

## Phase dependencies

```
A (foundation) ──┐
                 ├──→ C (shell + routes) ──→ D (cleanup) ──→ E (copilot ext.) ──→ F (backend tools)
B (actions)   ──┘
```

A and B are parallel. C depends on both. D depends on C. E depends on D. F depends on E (or parallel with placeholders).

## Post-refactor validation

```bash
cd /home/chris/AISALESHT && /test-all
```

Must pass: lint + 1063 frontend tests + arch fitness + E2E smoke for offer flow.
