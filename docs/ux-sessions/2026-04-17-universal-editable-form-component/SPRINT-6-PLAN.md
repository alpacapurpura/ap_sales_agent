# SPRINT-6-PLAN — Offer Studio Editor → Form-Runtime (Edition-Aware)

**Status:** LOCKED for execution. All decisions finalized 2026-04-18. Extends
PLAN.md §Sprint 6 with the edition-aware URL shape, backend section-catalog
SSoT, and offer/edition scope split that PLAN.md's original paragraph did not
cover.

**Authoritative documents read before starting:**
1. `PLAN.md` — Sprint 6 stub + status table.
2. `FLOW-SPEC.md` — form-runtime contract.
3. `DECISIONS.md` §D19–D27 — this plan's ratified decisions.
4. `LEARNINGS.md` — canonical patterns (server-safe split, named volumes, route audit).
5. `.claude/rules/offer-catalogs.md` — SSoT rule for offer-studio catalogs.

**Pre-flight (§0 of PLAN.md) applies to every session.**

---

## 0 · Objective

Bring offer-studio's per-offer editor to the same architectural maturity as
brand-studio:

- **Form-runtime** as the only editor primitive (no `SectionFormWrapper`,
  `FormField`, `*Form.tsx`, or `*Preview.tsx`).
- **Section catalog** living in the backend as the single source of truth
  for "which sections exist and which archetypes surface them".
- **Route-per-field** URL shape, **edition-aware**: every editor URL carries
  a virtual or real edition code.
- **Offer/edition scope split** exposed in schemas so each field knows which
  aggregate (`Offer` vs `LaunchEdition`) it persists to.

Offer-ladder overview (`/offer-studio` dashboard) and non-editor tabs
(`ventas`, `assets`, `campaigns`, `landing`) stay out of scope.

---

## 1 · The model (picture first)

```
                       offer-studio route tree
                       ─────────────────────────
/offer-studio                                   ← ladder (unchanged)
└── [offerId]
    ├── /                                       ← redirect to default edition
    └── /edition/[code]                         ← editor mount point
         ├── /                                  ← redirect to first section
         ├── /ventas | /assets | /campaigns | /landing   (existing tabs — unchanged)
         └── /[section]/[[...fieldId]]          ← catch-all (form-runtime)
```

- `[code]` resolves via `useOfferEditionResolver(offerId, code)`:
  - `code === "evergreen"` → `null` edition + offer-level schemas only.
  - `code === "<N>"` where `N` is a positive integer → `LaunchEdition` with
    `edition_number === N`. 404 if none.
- Every offer has offer-level content regardless of archetype. Archetypes
  that don't support launches (`PRODUCTO`, `MEMBRESIA`) always resolve
  against `evergreen`. Archetypes that do (`PROGRAMA`, `SERVICIO`,
  `EXPERIENCIA`) can use `evergreen` (to edit offer-wide fields) or a
  specific edition number (to edit edition fields + see offer baseline).
- No DB row for the virtual `evergreen`. The resolver is a pure function
  of URL + existing data.

### 1.1 Section scope (the key invariant)

Each section declares its scope:

| Scope | What it touches | Shown on `/evergreen/` | Shown on `/<N>/` |
|---|---|---|---|
| `OFFER_LEVEL` | `Offer` row only | ✅ editable | ✅ editable |
| `EDITION_LEVEL` | `LaunchEdition` row only | ❌ hidden (needs edition) | ✅ editable |
| `MIXED` | both (per-field `owner`) | Subset (offer fields only) | ✅ full |

This is the semantic foundation for everything downstream — schemas,
navigation rail filtering, copilot tool routing, and arch tests.

### 1.2 Example — section inventory

Derived from the existing `SECTION_REGISTRY`. Final owner assignments locked
in D22:

| Section key | Scope | Archetypes (from ARCHETYPE_BUILDER_CONFIG) |
|---|---|---|
| `identity` | OFFER_LEVEL | all |
| `strategy` | OFFER_LEVEL | all |
| `psychology` | OFFER_LEVEL | all |
| `promise` | OFFER_LEVEL | all |
| `value_stack` | OFFER_LEVEL | all |
| `instructors` | OFFER_LEVEL | PROGRAMA, SERVICIO, EXPERIENCIA |
| `knowledge` | OFFER_LEVEL | all |
| `closing` | OFFER_LEVEL | all |
| `program_details` | MIXED | PROGRAMA |
| `product_details` | OFFER_LEVEL | PRODUCTO |
| `service_details` | MIXED | SERVICIO |
| `event_details` | EDITION_LEVEL | EXPERIENCIA |
| `subscription_details` | OFFER_LEVEL | MEMBRESIA |
| `resources` | MIXED | all |
| `gallery` | OFFER_LEVEL | (deleted from registry per LEARNINGS — verify before assuming) |
| `pricing` | MIXED | all |

Scope assignments derived from current `LaunchEdition` and `Offer` field
ownership:

- `pricing`: base `pricing_options` on `Offer`; per-edition override
  `pricing_tiers` on `LaunchEdition`. Schema exposes base as
  `owner: "offer"`, overrides as `owner: "edition"`.
- `event_details`: single-date archetype; dates + location + capacity are
  edition-owned.
- `program_details`: program structure is offer-wide; cohort-specific
  overrides (session schedule) are edition-owned.
- `service_details`: category/mode are offer-wide; convocatoria dates are
  edition-owned.
- `resources`: base resources on offer; per-edition additions on edition
  (future — phase in later).

Any ambiguity resolved when porting the corresponding schema in Phase C.

---

## 2 · Phase execution

### Phase A — Backend section catalog + archetype extension (SSoT foundation) ✅ COMPLETE

**Goal:** make "the backend knows which sections exist, which belong to each
archetype, and which scope each has" a fact enforced by tests, not a
convention.

Completed 2026-04-18 in three commits (`0ede2913`, `05e7c487`, `030ddfc8`)
pushed to `origin/development`. Backend now owns section metadata and the
per-archetype section lists; HTTP catalog carries it all. Ready for Phase B
frontend consumption without further backend work.

- [x] **A.1** `backend/src/modules/offer/domain/section_catalog.py`:
  - `class SectionKey(StrEnum)` — keys matching the frontend `SECTION_REGISTRY`.
  - `class SectionScope(StrEnum)` — `OFFER_LEVEL | EDITION_LEVEL | MIXED`.
  - `@dataclass(frozen=True, slots=True) class SectionMetadata` —
    `key: SectionKey`, `label_es: str`, `subtitle_es: str`,
    `icon_name: str`, `scope: SectionScope`.
  - `SECTION_CATALOG: dict[SectionKey, SectionMetadata]` populated from
    current frontend labels + icons + scope assignments (§1.2).
  - `get_section(key)` lookup with KeyError + arch test guard.
- [x] **A.2** `tests/architecture/test_section_catalog.py`:
  - Every `SectionKey` enum member has a `SECTION_CATALOG` entry.
  - Every `SectionMetadata` uses a valid `SectionScope`.
  - No duplicate icons across keys (allowed to duplicate, test documents intent).
- [x] **A.3** Extend `archetype_catalog.ArchetypeCapabilities`:
  - New field `sections: tuple[SectionKey, ...]` — ordered.
  - Populate each archetype's entry from the current
    `ARCHETYPE_BUILDER_CONFIG` in the frontend. Frozen dataclass → new
    field added with explicit defaults in each record.
  - Bump `_CATALOG_VERSION` in `api/archetypes.py`.
- [x] **A.4** `tests/architecture/test_archetype_catalog.py` — extend:
  - Every archetype's `sections` references only valid `SectionKey`s.
  - Scope constraint: an archetype that `supports_editions = False` must
    not list any `EDITION_LEVEL` section (otherwise the UI would show a
    hidden section forever).
  - An archetype with `supports_editions = True` must list at least one
    section whose scope ≠ `OFFER_LEVEL` (otherwise editions are dead
    weight in the UI).
- [x] **A.5** `api/archetypes.py` DTO extension:
  - New `SectionMetadataDTO`.
  - `ArchetypeCapabilitiesDTO` adds `sections: list[SectionMetadataDTO]`
    — resolved server-side by expanding keys to full metadata.
  - Response envelope exposes global `SECTION_CATALOG` too (so clients
    can render label for an arbitrary key without per-archetype lookup).
  - Increment catalog version to force client cache eviction.
- [x] **A.6** Integration test `tests/modules/offer/test_archetypes_api.py`
  covers: response shape, sections-per-archetype count, scope values.
- [x] **A.7** Run `cd backend && .venv/bin/pytest tests/architecture/ -x -q`
  + `tests/modules/offer/` + `ruff check`. All green.

**Commit discipline:** one commit per file group, `feat(offer): add section
catalog SSoT (Sprint 6.A.N)`. Each commit independently revertible.

**Exit gate A:** backend exposes catalog over HTTP, tests green, no frontend
changes yet.

### Phase B — Frontend catalog consumption

- [ ] **B.1** `features/offer-studio/api/section-catalog-api.ts` — React
  Query hook `useSectionCatalog()` fetching `/api/v1/offer/archetypes/catalog`
  (already exists — extend types).
- [ ] **B.2** Derived hooks:
  - `useSectionsForArchetype(archetype)` → ordered `SectionMetadata[]`.
  - `useVisibleSections(archetype, editionCode)` → filters by scope:
    - `code === "evergreen"` ⇒ drop `EDITION_LEVEL` sections.
    - `code === "<N>"` ⇒ keep all.
- [ ] **B.3** TS types generated from catalog response (`SectionKey` TS enum
  mirroring backend). Fixture file + drift test.
- [ ] **B.4** Frontend anti-drift test
  `src/__tests__/architecture/test-no-section-catalog-duplicates.test.ts`:
  - Fails if `SECTION_METADATA`, `SECTION_SCOPE`, `SECTION_LABELS`, or any
    new `*_METADATA` map appears in offer-studio outside the generated
    types file.
  - Fails if `ARCHETYPE_BUILDER_CONFIG` (the old ordered section list) is
    still hardcoded in the frontend. Backend catalog becomes the only
    ordering source.
- [ ] **B.5** Delete `offer-builder-config.ts` `ARCHETYPE_BUILDER_CONFIG` +
  `getSectionsForOffer` export. Update consumers to use
  `useSectionsForArchetype(archetype)`. `SECTION_REGISTRY` stays
  temporarily as a lookup-by-key map; it's purged in Phase H.
- [ ] **B.6** `tsc --noEmit`, `eslint`, `vitest` green; build-storybook green.

**Exit gate B:** frontend reads section list from backend. No hardcoded
section ordering anywhere in features/.

### Phase C — Offer-studio schemas (TDD, one section per commit)

**Pattern** matches brand-studio exactly (see `LEARNINGS.md` §Sprint 1).

- [ ] **C.0** Scaffold `features/offer-studio/schemas/` + `__tests__/` dir.
  Add index registry mirroring `brand-studio/schemas/index.ts`.
- [ ] **C.1–C.16** One commit per section. Each commit:
  1. `{section}.schema.ts` with field list. Fields declare:
     - `id`, `label`, `type`, `path`, `hint`, `required?`, etc. (as in
       form-runtime types).
     - `owner: "offer" | "edition"` (extended form-runtime `FieldSchema`)
       for `MIXED` scope sections. For `OFFER_LEVEL` or `EDITION_LEVEL`
       sections, the section's scope implies owner uniformly.
  2. `{section}.schema.test.ts` asserts shape + parses via form-runtime
     parser.
  3. Schema entry in `schemas/index.ts` (typed registry).
  4. Commit: `feat(offer-studio): <section> schema (Sprint 6.C.N)`.

Order: identity, strategy, psychology, promise, value_stack, closing,
instructors, knowledge, product_details, subscription_details, pricing,
service_details, program_details, event_details, resources.

Reason for order: pure `OFFER_LEVEL` plain-field sections first (fastest +
least risk), MIXED next (drives the form-runtime `owner` field design),
EDITION_LEVEL last (needs edition resolver working end-to-end).

- [ ] **C.17** Form-runtime extension `FieldSchema.owner?: "offer" | "edition"`.
  Runtime default: inherit from section scope. Patch dispatcher routes save
  to the correct mutation.
- [ ] **C.18** Arch fitness: one schema per `SectionKey` in backend
  `SECTION_CATALOG`, modulo intentionally unavailable sections (documented
  in a `KNOWN_SECTIONS_WITHOUT_SCHEMA` set — empty at end of phase C).
- [ ] **C.19** Storybook stories for each schema (render in
  UniversalEditableSection with mock values). Title `OfferStudio/Schemas/<Section>`.
- [ ] Run `tsc + eslint + vitest + build-storybook` green after each commit.

**Exit gate C:** 16 schemas live, registry typed end-to-end, each has
tests + a story. Old `*Form.tsx` still mounted by the app; schemas unused
at the app-router level yet.

### Phase D — Pages + URL migration

- [ ] **D.1** Edition resolver hook
  `features/offer-studio/hooks/use-offer-edition-resolver.ts`:
  - Input: `offerId`, `code`.
  - Output: `{ offer, edition | null, scopeMode: "evergreen" | "edition" }`.
  - Signals `notFound()` when `code` is a number that doesn't resolve.
  - Uses existing `use-editions` + `use-offer-with-edition`.
- [ ] **D.2** `features/offer-studio/pages/section-pages.tsx` — `"use client"`.
  One React component per `SectionKey`. Each loads its schema + data and
  mounts `UniversalEditableSection` with the correct owner routing.
- [ ] **D.3** `features/offer-studio/pages/section-page-map.ts` — server-safe
  (no `"use client"`). Exports `OFFER_SECTION_PAGE_MAP` +
  `OfferStudioSectionSlug` type. **Mandatory split per LEARNINGS** — a
  Server Component importing `.tsx` with client references would fail silently.
- [ ] **D.4** App Router catch-all:
  `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/[offerId]/edition/[code]/[section]/[[...fieldId]]/page.tsx`
  — Server Component:
  - Reads `[section]` → looks up `OFFER_SECTION_PAGE_MAP`; 404 on miss.
  - Reads `[code]` → passes to client component as prop; resolution happens
    client-side in the hook.
  - Renders `<Suspense>` + the chosen section page component.
- [ ] **D.5** Default route redirect
  `.../offer-studio/[offerId]/page.tsx`:
  - If offer has ≥1 LAUNCH edition ⇒ redirect to
    `/edition/<first-active-edition-number>/identity`.
  - Else redirect to `/edition/evergreen/identity`.
- [ ] **D.6** Edition default redirect
  `.../offer-studio/[offerId]/edition/[code]/page.tsx`:
  - Redirect to `/edition/[code]/identity`.
- [ ] **D.7** Backwards-compat redirects (Phase 1 of 2 — soft redirects):
  - `next.config.mjs` adds redirects from legacy shapes:
    - `/<tenant>/offer-studio/offer/:offerId` → new default.
    - `/<tenant>/offer-studio/offer/:offerId/editions/:editionId` → new
      shape (need edition-id-to-number translation; fall through to a
      client-side redirect page if SSR can't resolve).
  - Legacy `/offer/:offerId/:tab` deep-links preserved for ventas/assets/
    campaigns/landing (not form-runtime targets).
- [ ] **D.8** `OfferNavRail` rewrites to use `useVisibleSections(archetype, code)`.
  Each row is a `<Link>` to the new URL. Same URL-driven pattern as
  `BrandStudioNavRail`.
- [ ] **D.9** `EditionsRail` updated to read `code` from URL + emit new
  switch hrefs via `buildEditionSwitchHref(…)` extended for new shape.
- [ ] **D.10** Copilot `navigation_map.py` + `routes` registry updated with
  new paths. Per LEARNINGS: audit frontend redirects + AppSidebar +
  TenantSwitcher + Clerk + copilot `navigation_map` + `procedures/*.py`
  route_hints + e2e specs.
- [ ] **D.11** Smoke walk: open each archetype's offer, click through each
  section under evergreen + under a LAUNCH edition, validate save, copilot
  focus bar, field deep-link.

**Exit gate D:** new routes serve the editor. Old `*Form.tsx` still mounted
per section (schemas mount empty shells with "pendiente" placeholders
actions for anything not yet schemaed). Backwards-compat redirects live.

### Phase E — Editor migration (section-by-section)

Each section in this phase already has a schema (Phase C). Phase E replaces
its `*Form.tsx` + `*Preview.tsx` with form-runtime mounts.

- [ ] **E.1–E.16** One commit per section. Each commit:
  1. Delete `sections/<section>/{Form,Preview,Manager}.tsx`.
  2. Update `SECTION_REGISTRY` in `offer-builder-config.ts` to point to a
     minimal `SectionPage(...)` wrapper that mounts
     `UniversalEditableSection` with the schema. (The registry retires
     entirely in Phase H.)
  3. If the section has rich actions (pricing tiers editor, gallery picker,
     program session builder), port them to
     `features/offer-studio/actions/` as `ActionComponent` entries. Reuse
     brand-studio patterns (stable refs per-row, `useMemo` for derived
     defaults, etc.).
  4. Remove dead imports from consumers.
  5. Commit `refactor(offer-studio): migrate <section> to form-runtime (Sprint 6.E.N)`.
- [ ] **E.17** `OfferEditSheetManager`, `OfferEditorContent`, `OfferLivePreview`,
  `OfferSectionWrapper` retire. Last commit of phase E.
- [ ] After each commit: `tsc + eslint + vitest + build-storybook + backend
  pytest/ruff + arch fitness` all green.

**Exit gate E:** `features/offer-studio/components/editor/` no longer has
`SectionFormWrapper`, `FormField`, or any `*Form.tsx` / `*Preview.tsx`
files. All sections render via form-runtime.

### Phase F — Copilot integration + route-tool map

- [ ] **F.1** Update `copilot/application/tools/registry.py` `ROUTE_TOOL_MAP`
  to include new offer-studio section paths. Route-based tool selection
  picks the right tools per section.
- [ ] **F.2** `copilot/domain/navigation_map.py` extended: per-section
  descriptors with label, quick hints, archetype, scope.
- [ ] **F.3** Audit copilot `procedures/*.py` `route_hints` — they must point
  at the new URL shape.
- [ ] **F.4** Arch allowlist updates:
  - `test-feature-structure` — add `offer-studio/schemas` and
    `offer-studio/pages` as canonical folders.
  - `test-no-duplicate-names` — no duplicate with brand-studio after
    Phase E.
- [ ] **F.5** Smoke: open offer-studio section page, invoke copilot chat,
  confirm the chat's apply-chip patches the field through
  `bridge.patchField`.

**Exit gate F:** copilot works on the new offer-studio URL tree exactly
like on brand-studio.

### Phase G — Sprint 4d–h (copilot extraction tools, one sub-session per tool)

Execute independently. These can run in any order; recommended: 4d → 4g →
4e → 4f → 4h.

| Sub-session | Tool | Specs |
|---|---|---|
| 4d | `extract_brand_from_url` | PLAN.md §5.4 table |
| 4e | `extract_brand_from_docs` | idem |
| 4f | `analyze_voice_style` | idem |
| 4g | `extract_visuals_from_url` | idem |
| 4h | `clone_personality_from_chat` | idem |

Each sub-session delivers: backend tool + registry entry + chat-UI component
+ storybook story + pytest + vitest.

**Exit gate G:** 5 tools registered, each with story + tests + integration
coverage.

### Phase H — Cleanup

- [ ] **H.1** Delete `frontend/src/features/brand-studio/components/legacy-team/`
  once InstructorsSelector either:
  - Links out to `/brand-studio/team/[fieldId?]`, OR
  - Wraps `SectionPage(teamSchema)` inline with a brand-studio bridge.
- [ ] **H.2** Delete `offer-builder-config.ts` `SECTION_REGISTRY` once all
  sections are form-runtime mounts.
- [ ] **H.3** Delete stale `*Preview.tsx` + `*Form.tsx` paired files that
  survived Phase E for offline reference.
- [ ] **H.4** Shrink arch allowlists:
  - `test-feature-structure`: no more `brand-studio/components/legacy-team`.
  - `test-no-default-exports`: offer-studio entries removed per-file as
    they retire.
- [ ] **H.5** Backwards-compat redirects (Phase 2 — hard removal): delete
  `next.config.mjs` redirect entries after 1 sprint of production coexistence.
  Track date in a `docs/migrations/` note so the hard cut is scheduled.
- [ ] **H.6** Final grep verification:
  - `grep -r "SectionFormWrapper" frontend/src/` → 0 hits
  - `grep -r "ARCHETYPE_BUILDER_CONFIG" frontend/src/` → 0 hits
  - `grep -r "from.*offer-builder-config" frontend/src/` → 0 hits
  - `grep -r "FormField" frontend/src/features/offer-studio/` → 0 hits

**Exit gate H (= Sprint 6 done):**

- Offer-studio editor serves from form-runtime.
- Backend owns the section catalog.
- URL shape is edition-aware with an evergreen virtual code.
- All 10 frontend arch fitness tests + backend arch tests green.
- Redirect table documented for legacy URL removal.

---

## 3 · Quality bar per commit

(Non-negotiable — mirrors PLAN.md §6.)

- `tsc --noEmit`: 0 errors.
- `eslint`: 0 errors. New warnings tolerated **only in unchanged files**.
- `vitest`: green baseline, no regressions.
- Backend `ruff check`: 0 errors.
- Backend `pytest -x -q`: green.
- `build-storybook`: green (when UI changes).
- 10 frontend arch tests + backend arch tests green.
- TDD: RED → GREEN → commit.
- Conventional Commits + Co-Authored-By.
- Commit ship-able: app still serves.

## 4 · Rollback

Per-commit `git revert`. The phase gates (A/B/C/D/E/F/G/H) are independent:
- Revert all of E → old `*Form.tsx` returns (if files still referenced by
  registry).
- Revert D → old routes return, new tree becomes dead.
- Revert A → no backend or frontend impact (catalog is additive until
  Phase B consumes).

## 5 · Risks + mitigations

| Risk | Mitigation |
|---|---|
| URL redirects leak `editions/{editionId}` UUIDs into bookmarks that can't be translated server-side | Client-side redirect page with lookup; 24-hour browser cache for the translation. Phase H.5 removes after grace window. |
| `LaunchEdition` entities proliferate (user creates editions in old UI that the new UI can't show) | No. The old UI is deleted in Phase E; only the new form-runtime mount exists post-Phase E. |
| Section schema drift vs backend catalog | Arch tests on both ends. Fails CI on any mismatch. |
| Copilot tools reference old paths and break post-flip | Phase F.3 audits `route_hints`; arch test adds to `navigation_map.py` ensures parity. |
| Storybook stories run forever due to new schema fixtures | Per-story fixtures colocated; no global fixtures introduced. |
| Docker named-volumes cache invalidates form-runtime updates | Standard nuclear sequence documented in LEARNINGS §Sprint 1 applies. |

## 6 · Parallel vs serial

Sprint 6 (A→H) is **serial** end-to-end because later phases depend on
earlier phases' contracts (B depends on A's API, C depends on A's enum, D
depends on C's schemas, E depends on D's URL tree, F depends on E's mount
points). Sprint 4d–h (Phase G) is **independent** and can run in parallel
once E is done (bridges are in place for both brand-studio and offer-studio).

## 7 · Session checkpoints

Recommended cuts so fresh sessions can resume cleanly:

- **Session α** — Phase A (backend catalog). Push, hand off at commit
  boundary.
- **Session β** — Phase B + C.1–C.8 (simple OFFER_LEVEL schemas). One session.
- **Session γ** — Phase C.9–C.16 + C.17 form-runtime `owner` extension.
- **Session δ** — Phase D (pages + routes + nav).
- **Session ε** — Phase E (editor migration, section-by-section).
- **Session ζ** — Phase F (copilot integration) + kickoff of Sprint 4d.
- **Sessions 4d/4e/4f/4g/4h** — one tool per session.
- **Session η** — Phase H cleanup + final status + memory update.

Each session closes with:
- Push to `origin/development`.
- Update PLAN.md Status table + this file's phase checklist.
- Write a short LEARNINGS entry for any non-obvious pattern discovered.
- Message user with last commit hash + next step.

## 8 · Out of scope (scope creep log — must stay empty)

- Offer-ladder overview UI changes.
- Sales agent, analytics, connections, growth changes.
- Backend offer domain refactors beyond the section catalog addition.
- Slug-based edition URLs (deferred — `edition_number` for now).
- Non-editor tabs (`ventas`, `assets`, `campaigns`, `landing`) reconfigured
  under the new URL shape. Existing routes keep working; their internals
  stay.

_(empty — good)_
