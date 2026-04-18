# PLAN — Brand Studio Migration Execution

**Session:** `docs/ux-sessions/2026-04-17-universal-editable-form-component/`
**Authoritative document.** Every commit in this refactor must tick a box below in the same commit. Status section at the bottom is the single source of truth for "where are we".

**Pace note:** timings are Claude-active hours, not elapsed days. Each sprint closes with a user checkpoint; user turnaround drives the elapsed calendar, not Claude throughput.

**E2E Playwright:** excluded from this migration's gating. Existing E2E tests may break temporarily and will be addressed in a separate task after migration.

---

## 0. Pre-Flight Protocol (EVERY new Claude session reading this plan)

Before ANY tool call in a new session, Claude must:

1. `git status --short` — confirm working tree state.
2. `git log --oneline -10` — confirm last commits match "Status" section below.
3. Read this file top-to-bottom.
4. State to user: *"Estamos en Sprint N, tarea X. Último commit: [hash] [title]. Tests: [pasar/fallar]. Próximo paso: [Y]. ¿Avanzo?"*
5. Wait for user confirmation before acting.

No step skipped. No assumption carried from memory.

---

## 1. Sprint 0 — Specs & Review (Claude: 30–60 min · User: review)

**Goal:** User approves architectural direction + concrete schema shape before any production code.

**Deliverables:**

- [x] `FLOW-SPEC.md` written
- [x] `PLAN.md` written (this file)
- [x] `schemas/identity.schema.example.ts` written (concrete example)
- [x] `DECISIONS.md` written (session decision log)
- [ ] User reviews spec + plan + schema example
- [ ] User answers the 5 open questions in FLOW-SPEC §9
- [ ] User approves: "adelante con Sprint 1"

**Exit criteria:** user approval recorded in `DECISIONS.md`.

**Rollback:** n/a — no code change yet.

---

## 2. Sprint 1 — Foundation + Identity Pilot (Claude: 2–4 hrs · User: validate UI)

**Goal:** Prove the pattern works end-to-end on ONE section. If this fails, we learn cheaply.

### 2.1 Foundation — `lib/form-runtime/` + `components/form-runtime/`

- [ ] Create `lib/form-runtime/schema/types.ts` — FieldSchema + SectionSchema types
- [ ] Create `lib/form-runtime/schema/parser.ts` — runtime validation
- [ ] Create `lib/form-runtime/schema/__tests__/parser.test.ts` — 100% parser coverage (TDD)
- [ ] Create `lib/form-runtime/actions/registry.ts` + test
- [ ] Create `lib/form-runtime/copilot/bridge.ts` + test
- [ ] Create `components/form-runtime/FormRuntimeProvider.tsx` + test (mock schema render)
- [ ] Create `components/form-runtime/EditableField.tsx` + test (focus, change, AI update subscription)
- [ ] Create `components/form-runtime/FieldRenderer.tsx` + test
- [ ] Create `components/form-runtime/inputs/TextInput.tsx` + test
- [ ] Create `components/form-runtime/inputs/TextareaInput.tsx` + test
- [ ] Create `components/form-runtime/inputs/EnumInput.tsx` + test
- [ ] Create `components/form-runtime/inputs/ArrayInput.tsx` + test (list + detail pane variant)
- [ ] Create `components/form-runtime/inputs/CustomInput.tsx` + test (renders from action registry)
- [ ] Create `components/form-runtime/SessionHeader.tsx` + test (progress chip, actions)
- [ ] Create `components/form-runtime/UniversalEditableSection.tsx` + test (integration)
- [ ] `npx tsc --noEmit` green
- [ ] `npx eslint src/` green (0 new errors)
- [ ] `npx vitest run` green
- [ ] Commit: `feat(form-runtime): schema types, EditableField, UniversalEditableSection, action registry`

**Commit is ship-able:** nothing consumes this yet, brand stays intact.

### 2.2 Brand-Studio scaffolding

- [ ] Create `features/brand-studio/` empty structure: `api/`, `hooks/`, `types/`, `schemas/`, `actions/`, `pages/`
- [ ] Port `features/brand/api/` → `features/brand-studio/api/` (no logic change, only folder move + import updates)
- [ ] Port `features/brand/hooks/` → `features/brand-studio/hooks/`
- [ ] Port `features/brand/types/` (except `edit-mode.ts`) → `features/brand-studio/types/`
- [ ] Update arch test allowlist in `src/__tests__/architecture/test-feature-structure.ts` to include `brand-studio`
- [ ] `npx tsc --noEmit` green
- [ ] `npx vitest run` green
- [ ] Commit: `feat(brand-studio): scaffold + port api/hooks/types from brand/`

**Commit is ship-able:** old brand/ still works, new brand-studio/ exists unused.

### 2.3 Identity section — end-to-end migration

- [ ] Create `features/brand-studio/schemas/identity.schema.ts`
- [ ] Create `features/brand-studio/schemas/__tests__/identity.test.ts`
- [ ] Create `features/brand-studio/pages/EsenciaPage.tsx` — thin wrapper around UniversalEditableSection
- [ ] Update `app/(main)/[tenantId]/(dashboard)/brand-studio/esencia/page.tsx` — import EsenciaPage from brand-studio
- [ ] Run `npx tsc --noEmit` + `npx vitest run` — green
- [ ] **USER CHECKPOINT 1**: user opens `/brand-studio/esencia`, validates edit flow works + copilot focuses fields correctly
- [ ] Delete `features/brand/sections/identity/` (3 files)
- [ ] Delete `features/brand/sections/identity/__tests__/` if exists
- [ ] Remove `"identity"` key from `features/brand/components/forms/EditSheetManager.tsx` registry
- [ ] Remove `identity` from `features/brand/config/sections.ts` EDIT_MODE_META
- [ ] Run full quality gates (tsc, eslint, vitest, arch fitness)
- [ ] Commit: `feat(brand-studio): migrate identity section + remove old`

**Commit is ship-able:** identity uses new runtime; other 14 sections still use old brand/; app fully functional.

### 2.4 Sprint 1 close

- [ ] **USER CHECKPOINT 2**: user validates entire brand studio still works (old sections untouched, identity uses new pattern)
- [ ] Update "Status" section below
- [ ] Push to origin/development

**Exit criteria:** user confirms identity section works in UI and OK to proceed with the rest.

**Rollback plan for Sprint 1:**
- `git revert` the identity migration commit → page.tsx falls back to old brand
- form-runtime/ and brand-studio/ scaffolding stay in the tree (harmless, unused)
- Or full rollback: `git revert` all 3 commits → pre-Sprint-1 state

---

## 3. Sprint 2 — Remaining Brand Sections (Claude: 4–8 hrs · User: batch validate)

**Goal:** Migrate all remaining sections using the pattern proven in Sprint 1.

**Process per section (repeat 14 times):**

For each of: `voice`, `team`, `authority`, `testimonials`, `visuals`, `logos`, `methodology`, `story`, `narrative`, `positioning`, `communication-assets`, `personality`, `contact`, `avatars`.

- [ ] Write schema `features/brand-studio/schemas/{section}.schema.ts`
- [ ] Write schema test `features/brand-studio/schemas/__tests__/{section}.test.ts`
- [ ] Port required rich actions to `features/brand-studio/actions/` (if section uses them)
- [ ] Port their tests + rename imports
- [ ] Create/update page in `features/brand-studio/pages/`
- [ ] Update `app/.../{section-route}/page.tsx` to import from brand-studio
- [ ] Quality gates green
- [ ] Delete old `features/brand/sections/{section}/*` files
- [ ] Delete old `features/brand/sections/{section}/__tests__/*` files
- [ ] Remove entry from `EditSheetManager.tsx` registry
- [ ] Remove entry from `EDIT_MODE_META`
- [ ] Quality gates green (again, post-delete)
- [ ] Commit: `feat(brand-studio): migrate {section} + remove old`

Checklist of section commits:

- [ ] voice (+ port VoiceCloneAction)
- [ ] team (array with detail pane; port image-gallery-picker)
- [ ] authority (array)
- [ ] testimonials (array)
- [ ] visuals (+ port BrandVisualsWizard, SingleImagePicker, theme-injector)
- [ ] logos (+ port LogoKit action)
- [ ] methodology
- [ ] story
- [ ] narrative
- [ ] positioning (+ values-essence as nested section?)
- [ ] communication-assets
- [ ] personality (+ port DimensionSliders, CloneUpload, PresetCatalog)
- [ ] contact
- [ ] avatars (+ port AvatarForm as complex action)

**User checkpoint strategy in Sprint 2:**

To avoid 14 individual checkpoints (exhausting), group into 3 batches:

- Batch A (low complexity — no rich actions): methodology, story, narrative, positioning, contact, communication-assets → 1 checkpoint after batch
- Batch B (array patterns): team, authority, testimonials → 1 checkpoint after batch
- Batch C (rich actions): voice, personality, visuals, logos, avatars → 1 checkpoint per section (these are the risky ones)

- [ ] **USER CHECKPOINT 3** after Batch A
- [ ] **USER CHECKPOINT 4** after Batch B
- [ ] **USER CHECKPOINT 5** after voice
- [ ] **USER CHECKPOINT 6** after personality
- [ ] **USER CHECKPOINT 7** after visuals
- [ ] **USER CHECKPOINT 8** after logos
- [ ] **USER CHECKPOINT 9** after avatars

**Rollback plan for Sprint 2:**
Per-section commits are independent. `git revert` any single section commit restores that section to the old pattern without affecting others.

---

## 4. Sprint 3 — Copilot Refactor (Claude: 2–4 hrs · User: validate copilot flows)

**Goal:** Collapse focus/interview/preview into `copilotSession`. Remove dead copilot code.

- [ ] Refactor `features/copilot/store/copilot-store.ts`:
  - Remove `focusEntity`, `focusSnapshot`, `interviewProgress`, `previewData`
  - Add `session`, `focusedField`
  - Keep `selectedFields`, chat state, UI state
- [ ] Update copilot types in `features/copilot/types/`
- [ ] Update `features/copilot/hooks/use-copilot-chat.ts` to read new session shape
- [ ] Update `features/copilot/hooks/use-copilot-ui-action.ts`
- [ ] Create new `features/copilot/components/SessionHeader.tsx` (replaces FocusBar)
- [ ] Wire `FormRuntimeBridge` into copilot store (subscription on section mount)
- [ ] Delete `features/copilot/components/CopilotPreviewPane.tsx`
- [ ] Delete `features/copilot/components/FocusBar.tsx`
- [ ] Delete `features/copilot/components/FocusModeButton.tsx`
- [ ] Delete `features/copilot/components/InterviewModeButton.tsx`
- [ ] Delete `features/copilot/components/WithCopilot.tsx`
- [ ] Delete `features/copilot/config/interview-preview-registry.ts`
- [ ] Delete `features/copilot/components/interview/EditionPreviewCard.tsx`
- [ ] Delete `features/copilot/components/interview/InterviewDateBlock.tsx`
- [ ] Delete all related tests
- [ ] Update remaining copilot tests to new store shape
- [ ] Quality gates green
- [ ] **USER CHECKPOINT 10**: validate copilot chat + interview + field-update flow in brand-studio
- [ ] Commit: `refactor(copilot): collapse focus/interview/preview into session, bridge to form-runtime`

**Also in Sprint 3:**

- [ ] Update other preview renderers (offer, persona): if they are still imported somewhere, deprecate with clear TODOs pointing to future offer-studio migration. If unused, delete.
- [ ] Update copilot backend integration if any client-side contract changed (should not — backend stays intact).

**Rollback plan for Sprint 3:**
`git revert` the copilot commit restores the old store + components. Brand-studio keeps working (it reads via bridge, not via store shape directly).

---

## 5. Sprint 4 — Final Cleanup (Claude: 30–60 min · User: final validation)

**Goal:** Zero dead code. `features/brand/` gone.

- [ ] Verify `features/brand/sections/` is empty (all sections deleted in Sprint 2)
- [ ] Delete `features/brand/components/forms/EditSheetManager.tsx`
- [ ] Delete `features/brand/components/interview/BrandPreviewSections.tsx`
- [ ] Delete `features/brand/components/interview/BrandPreviewSummary.tsx`
- [ ] Delete `features/brand/components/interview/previews/` (entire folder)
- [ ] Delete `features/brand/components/views/` (all 6 views)
- [ ] Delete `features/brand/config/sections.ts` (if only contains EDIT_MODE_META)
- [ ] Delete `features/brand/types/edit-mode.ts`
- [ ] Check any remaining files in `features/brand/` — port to brand-studio or delete with justification
- [ ] Delete `features/brand/` entirely
- [ ] Global search: `from ".*brand/"` — verify 0 hits (all consumers now use brand-studio)
- [ ] Global search: `import.*EditSheetManager` — verify 0 hits
- [ ] Global search: `import.*WithCopilot` — verify 0 hits
- [ ] Remove any remaining legacy entries from arch test allowlists
- [ ] Quality gates green
- [ ] **USER CHECKPOINT 11**: full regression walkthrough
- [ ] Commit: `chore(brand): remove deprecated brand/ folder after brand-studio migration`
- [ ] Push to origin/development

---

## 6. Status (UPDATE WITH EVERY COMMIT)

Last updated: **2026-04-17 — Sprint 0, specs under review**

| Sprint | State | Last commit | Tests |
|---|---|---|---|
| Sprint 0 — Specs | **🟡 In progress** (awaiting user review) | — | — |
| Sprint 1 — Foundation + identity | Not started | — | — |
| Sprint 2 — Remaining sections | Not started | — | — |
| Sprint 3 — Copilot refactor | Not started | — | — |
| Sprint 4 — Final cleanup | Not started | — | — |

---

## 7. Scope Creep Log (MUST STAY EMPTY)

If during migration anything arises that is not explicitly in scope (FLOW-SPEC §7), it MUST be logged here with status `deferred` and added to `docs/mejoras-proceso/to-do.md`. Claude MUST NOT silently absorb out-of-scope work.

_(empty — good)_

---

## 8. Guarantees Recap

1. Every commit is ship-able. No commit breaks brand studio.
2. Every code change has a test in the same commit (TDD).
3. Every deletion has a corresponding line in this plan.
4. Every new Claude session runs §0 pre-flight.
5. User checkpoints are NOT optional — Claude blocks on them.
6. Scope creep goes to log, not into the diff.
7. Rollback per sprint is one `git revert` on a specific hash.
