# Offer Studio — Refactor Status (2026-04-20)

## COMPLETED — F1 → F3 + F7.1 (brand-parity architecture)

Offer Studio now mirrors the brand-studio architectural pattern at the
foundation, UX, routing, and backend copilot layers. The legacy shell
still co-exists under `components/container/` + `components/navigation/`
+ `components/editor/` + `context/` + `config/` — deletion tracked below
as follow-up work.

### F1 — Foundation alignment (3 commits)

- ✅ **F1.1** — Actions registry homologated with brand pattern
  (`OFFER_STUDIO_ACTION_KEYS` tuple + typed `REGISTRY_ENTRIES` record +
  idempotent `bootstrapOfferStudioActions()` + auto-bootstrap on module
  load). 4 tests.
- ✅ **F1.2** — `useOfferSettings(offerId)` aggregator hook + 14 typed
  per-section updaters + wired `section-pages.tsx` factory so the
  scaffold now saves real data via `saveSection`. 8 tests.
- ✅ **F1.3** — `OfferStudioNavRail` + `OfferStudioBreadcrumb` flat
  components driven purely by `usePathname`, consuming
  `lib/section-catalog.ts` (not the legacy `config/`). 17 tests.

### F2 — Polymorphic VariantRail (2 commits)

- ✅ **F2.1** — `components/variant-rail/` — polymorphic rail that
  dispatches per `variant_structure` (Temporal / Tier / Sku / Regional /
  Modality / Language / + fallback). 72 tests across 8 test files.
- ✅ **F2.2** — `useShouldShowVariantRail` hook + `buildNoVariantRedirect`
  helper for the no-variant single-edition UX (lead-magnet / ebook).
  9 tests.

### F3 — App route migration (1 commit)

- ✅ URL contract moved to brand pattern (`/offer/{id}/editor/{section}`
  replaces `/offer/{id}/edition/{code}/{section}`). 30-day redirect shim
  preserves bookmarks. 11 tests covering matcher + builder.
- ✅ `OfferShellLayout` client shell with conditional VariantRail mount.
- ✅ Collection routes (`testimonials`, `instructors`, `faq`) landing +
  detail pages using brand's InstancePicker pattern. Wired to stub hooks
  until F7 supplies backend APIs.
- ✅ `EditionsManagementClient` + server route renders
  `VariantCollectionLandingPage` with polymorphic card dispatch.
- ✅ `/offer-studio/interview/` route deleted (copilot is sidebar, not
  page — D5).

### F7.1 — Backend copilot section tools (1 commit)

- ✅ `backend/src/modules/copilot/application/tools/offer_section_tools.py`
  — 17 tools decorated with LangChain `@tool`, grouped by section:
  - **Identity/Promise/Strategy** (6): `adapt_from_brand_identity`,
    `adapt_from_brand_narrative`, `rewrite_tones`,
    `validate_preset_coherence`, `reuse_brand_buyer_personas`,
    `inherit_brand_methodology`.
  - **Pricing** (3): `high_ticket_tiering_template`,
    `recurring_billing_setup`, `detect_currency_mismatch`.
  - **Schedule / Location** (2): `import_scheduling_event_type`,
    `detect_hybrid_split`.
  - **Testimonials / Value stack** (4): `import_from_brand_vault`,
    `suggest_missing_objections`, `assemble_from_brand_authority`,
    `reuse_brand_team`.
  - **FAQ** (2): `generate_from_preset_flags`,
    `pull_sales_agent_common_questions`.
- ✅ No cross-module imports — all cross-reads via lazy-imported port
  shims. Pure application layer, no SQLAlchemy/FastAPI at module level.
- ✅ Tenant isolation via `get_tenant_id()` context var on every tool.
- ✅ 51 tests (happy-path + missing-data edge cases + tenant isolation)
  + arch test in `tests/architecture/test_copilot_registry.py`.
- ✅ Per-file ruff exceptions documented in `pyproject.toml`.

**Quality snapshot post-F3+F7.1:**

- Backend: 431 tests pass (380 arch + 51 copilot), ruff + format clean.
- Frontend: 1515 tests pass (+72 F2.1 + 20 F1-F3 tests), tsc clean.
- Zero new arch allowlist entries.

---

## PENDING — Follow-up work (next sprint)

These items are non-blocking for the brand-parity architecture goal.
Each is a well-scoped independent commit.

### F4 — Retire legacy shell / editor

| File | Action | Blocked by |
|---|---|---|
| `components/container/OfferShell.tsx` | Delete | All consumers migrated to `OfferShellLayout` |
| `components/container/OfferShellHeaderRow1.tsx` | Delete | Same |
| `context/OfferShellContext.tsx` + `context/` dir | Delete | Consumers read React Query direct |
| `components/editor/OfferEditSheetManager.tsx` | Delete | F3 section catch-all replaces it |
| `components/editor/OfferEditorContent.tsx` | Delete | Same |
| `components/editor/OfferSectionWrapper.tsx` | Delete | `UniversalEditableSection` layout handles it |
| `app/.../offer/[id]/edition/[code]/.../page.tsx` | Delete after 2026-05-20 | 30-day redirect shim window |

Migrate consumers at `/assets`, `/ventas`, `/campaigns` to read React Query
directly (no context dependency).

### F5 — Folder flatten (cosmetic, wide imports)

Match brand-studio's flat shape via codemod:

- `components/navigation/OfferNavRail.tsx` → DELETE (replaced by
  `OfferStudioNavRail` in F1.3).
- `components/container/OfferTabBar.tsx` → `components/OfferStudioTabBar.tsx`
- `components/container/EditionsRail.tsx` → DELETE (replaced by
  `variant-rail/VariantRail.tsx` in F2).
- `components/container/EditionsRailCollapsed.tsx` → `components/VariantRailCollapsed.tsx`
- `components/container/AutoSaveIndicator.tsx` → `components/OfferAutoSaveIndicator.tsx`
- `components/wizard/` → `components/legacy-wizard/`
- `components/editor/OfferLivePreview.tsx` → `components/OfferLivePreview.tsx`
- `tests/` top-level → redistribute to `__tests__/` colocated per feature.

Single PR with grep-sed codemod on imports.

### F6 — Delete `config/offer-builder-config.ts`

- Delete file + `config/` dir.
- Last consumers already removed (NavRail reads `lib/section-catalog.ts`
  + `actions/registry.ts` since F1).
- Arch test `test-feature-structure` (ratchet) should pass without
  allowlist change.

### F7.2 — Frontend copilot sidebar

- `components/OfferSectionCopilot.tsx` — suggestion cards + action
  buttons + draft-preview UX per prototype `variant-tier.html` /
  `section-pricing.html` copilot column.
- `hooks/use-offer-copilot.ts` — invokes `POST /copilot/tools/{tool_key}`
  + applies `draft_fields` as pending form patch.
- Wire `copilotSlot={<OfferSectionCopilot …/>}` from each section page
  (already supported by `SectionPage.copilotSlot` in Sprint 15.1).

### F8 — E2E Playwright coverage

- `frontend/e2e/specs/smoke/offer-studio-homologation.smoke.spec.ts`:
  - Journey A (create offer → wizard → editor → save).
  - Journey E (no-variant: verify NO VariantRail, NO Editions tab).
  - Journey F (variant switch via rail → editor auto-filters).
- `frontend/e2e/specs/regression/offer-variants-polymorphic.regression.spec.ts`
  per variant_structure (TIER / SKU / REGIONAL / MODALITY / LANGUAGE /
  TEMPORAL_COHORT).
- `frontend/e2e/specs/regression/offer-copilot-per-section.regression.spec.ts`
  after F7.2 lands.

### F9 — Full-suite `/test-all` + docs snapshot

- Run `/test-all` natively — ratchet arch allowlists green.
- Create `docs/domains/offer-studio/architecture.md` snapshot mirroring
  `docs/domains/brand-studio/`.

---

## Verification commands (native WSL)

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
cd frontend && npx eslint src/ --cache
```

All must pass. Arch allowlists may only SHRINK, never GROW.

## Parallel-safety notes

- Legacy shell (F4 work) still active — `OfferShell` + `OfferShellContext`
  still wired in the current `layout.tsx` until F4 swaps it for
  `OfferShellLayout`.
- Both `EditionsRail` (legacy temporal-only) and `VariantRail`
  (polymorphic, new) exist side-by-side. Consumers migrate in F4/F5.
- `section-pages.tsx` factory still takes `(offerId, editionCode)` props
  — F4 will harmonise the signature once the legacy catch-all is removed.
