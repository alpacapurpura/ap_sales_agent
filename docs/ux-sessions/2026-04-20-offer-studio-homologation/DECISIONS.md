# DECISIONS — Offer Studio Homologation

**Session:** `2026-04-20-offer-studio-homologation`

---

## Accepted

### D1. Homologate offer-studio structure with brand-studio (canonical)
**Rationale:** Brand-studio refactor already landed; two studios with divergent patterns = 2x maintenance + confusion. Any dev opening either studio should see identical shape.
**Scope:** folders, file names, hook names, factory pattern, routing contract, actions registry.
**Excluded from homologation:** editions dimension (exclusive to offer), preset-driven section resolution (backend SSoT), copilot-per-section (net-new pattern).

### D2. Preserve backend preset catalog
**Rationale:** Sprint 12–14 locked 84 presets, 7 questions, 6 flags, 187 arch test cases. Changing backend = rebuild downstream (sales-agent, landing generator, dashboard PresetBadge). Zero value, high risk.
**Scope:** `offer_type_preset_catalog.py`, `resolve_preset_sections`, `preset_id`, `conditional_answers`, all arch tests, downstream consumers — **intocable**.

### D3. URL deep-link pattern from brand-studio applies to offer
**Rationale:** Offer already has `/offer/[id]/edition/[code]/[section]/[[...fieldId]]`. Almost canonical — just drop `edition/[code]` segment.
**Outcome:** New URL = `/offer-studio/offer/[id]/editor/[section]/[[...fieldId]]`. Edition switching via `?edition={code}` query param (React Query).
**Risk:** bookmarks break. Mitigation: 301 redirect middleware for 30 days.

### D4. Extend `UniversalEditableSection` with optional `copilotSlot` (non-breaking)
**Rationale:** Offer-studio needs persistent copilot per section. Brand-studio doesn't need it yet but may adopt later. Alternative (fork form-runtime) = duplication and drift. Alternative (offer wraps form-runtime in custom layout) = leaks layout concern outside runtime.
**Outcome:** Add `copilotSlot?: ReactNode`. Default undefined → existing 2-col grid. Defined → 3-col grid. Brand-studio unchanged.

### D5. Copilot is sidebar, not standalone page
**Rationale:** Current `/offer-studio/interview/page.tsx` standalone copilot interview is dead-end UX. Interview should happen in context (sidebar) so user sees form update in real time.
**Outcome:** Delete `/offer-studio/interview/` route. Copilot lives in `OfferSectionCopilot` rendered via `copilotSlot`.

### D6. Editions are UI state, not URL segment
**Rationale:** Edition switching should not navigate away or force route change. User expects to stay in same section while swapping edition context.
**Outcome:** `EditionsRail` chips update `?edition={code}` query param only. No path segment.

### D7. Flat component folder (+ legitimate sub-domains)
**Rationale:** Brand-studio has flat root components (`BrandStudioNavRail`, `BrandStudioBreadcrumb`) + narrow sub-dirs for domains (`dashboard/`, `legacy-team/`). Offer-studio currently has 12 sub-dirs (over-fragmented).
**Outcome:** Flatten to 6 sub-dirs (`dashboard/`, `editions/`, `assets/`, `knowledge/`, `ventas/`, `campaigns/`, `social-proof/`, `legacy-wizard/`). Top-level shared components (NavRail, Breadcrumb, TabBar, EditionsRail, LivePreview, SectionCopilot).

### D8. Legacy wizard preserved under `legacy-wizard/` prefix
**Rationale:** Sprint 13 wizard preset-first is canonical user flow. Not legacy in "deprecated" sense — but naming it `legacy-wizard/` signals: may evolve; do not wire new features to its internals. Matches brand's `legacy-team/` convention.
**Outcome:** Move `components/wizard/` → `components/legacy-wizard/`. Contents unchanged.

### D9. Delete `config/offer-builder-config.ts`
**Rationale:** Anti-pattern — mixes form component references with icon metadata. Brand-studio decouples this: icons in `lib/section-catalog.ts`, form components in `actions/registry.ts`. Offer should do the same.
**Outcome:** Split config → (a) metadata into new `lib/section-catalog.ts`, (b) form component refs into `actions/registry.ts`.

### D10. Copilot tools grouped by `entity_type="offer-section"` + `section_slug` filter
**Rationale:** Reuses existing copilot module contract. No new entity type proliferation. Registry filters tools by section slug so sidebar only shows relevant suggestions.
**Outcome:** New `backend/src/modules/copilot/tools/offer_section_tools.py`. Each tool decorated with `@copilot_tool(entity_type="offer-section", section_slug="pricing")`.

---

## Rejected

### R1. "Keep legacy shell + modal sheet alongside new split-view"
**Rejected because:** dual code paths = arch test churn + user confusion (two different interactions for same task). Clean cut is cheaper to maintain.
**Mitigation:** Feature flag for 48h rollback window.

### R2. "Move offer-studio under brand-studio as `brand-studio/offers/`"
**Rejected because:** offer is a distinct domain (preset catalog, editions, ladder, assets) with own routing namespace. Nesting would conflate two bounded contexts.

### R3. "Let copilot tools directly mutate backend offer data (write-through)"
**Rejected because:** breaks form-runtime save contract. Users expect to see changes in form, review, then save. Copilot returns `draft_fields` → frontend applies as pending patch → user saves via standard flow.

### R4. "Drop editions dimension; use single offer with scheduled publish windows"
**Rejected because:** editions are a product feature (Sprint 14 shipped it). Scope here is frontend homologation, not product simplification.

### R5. "Preserve `OfferShellContext` for global edit state"
**Rejected because:** context-based global state for shell concerns is an anti-pattern the brand-studio refactor explicitly removed. URL + React Query covers all current use cases.

### R6. "Fork form-runtime into `offer-form-runtime` for copilot integration"
**Rejected because:** fork = drift guaranteed. Optional prop is cheaper and still non-breaking for brand.

---

## Open questions (for user)

### Q1. Copilot suggestions in onboarding — autostart interview or passive?
**Context:** When user lands on newly-created offer (Editor tab, no section selected), should copilot auto-trigger the entrevista or show a passive "Inicia entrevista" CTA?
**Options:**
  - A) Passive (current prototype). User can dismiss and explore sections manually.
  - B) Auto-modal on first landing. Forces guided flow.
**Recommendation:** A (passive). Matches brand-studio "user drives" philosophy.

### Q2. EditionsRail visible on Assets / Knowledge / Campaigns tabs?
**Context:** Editions = pricing + dates + capacity overrides. They affect landing page and sales-agent, not assets.
**Options:**
  - A) Only visible in Editor + Editions tabs (current prototype).
  - B) Always visible.
**Recommendation:** A. Less noise in tabs where edition is irrelevant.

### Q3. Mobile copilot — drawer vs bottom sheet?
**Context:** At < 768px, copilot needs alternative surface.
**Options:**
  - A) Drawer from right (overlay).
  - B) Bottom sheet (thumb-reach).
**Recommendation:** B (bottom sheet). More common mobile pattern for context panels.

### Q4. Should copilot suggestions persist across session?
**Context:** User applies a tool → suggestion disappears. User refreshes → suggestion reappears?
**Options:**
  - A) Server-side dismissal tracking (`POST /copilot/suggestions/{id}/dismiss`).
  - B) Client-side localStorage dismissal (per-offer/per-section).
  - C) No dismissal — always recomputed from current state.
**Recommendation:** C. Simplest. Suggestions are derived from state (preset flags, brand completeness, form values). If state doesn't require tool, tool won't surface.
