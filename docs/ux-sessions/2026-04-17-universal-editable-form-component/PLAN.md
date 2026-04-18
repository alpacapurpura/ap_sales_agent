# PLAN — Brand Studio Refactor · Execution (scaffold-first)

**Session:** `docs/ux-sessions/2026-04-17-universal-editable-form-component/`
**Status:** Sprint 0 complete. All decisions locked (see DECISIONS.md §D11–D18). Ready for Sprint 1 in a fresh conversation.
**Authoritative document.** Every commit must tick a box below in the same commit. The "Status" section near the bottom is the single source of truth for "where are we".

**Pace note:** timings are Claude-active hours, not elapsed days. Each sprint closes with a user checkpoint; user turnaround drives calendar time, not Claude throughput.

**E2E Playwright:** excluded from this migration's gating (D9). May break temporarily and will be addressed in a separate task after migration.

**Execution model (D16):** scaffold-first. Sprint 1 builds the entire new architecture in-tree without flipping any route. Sprints 2–4 add behavior, flip routes, refactor copilot. Sprint 5 deletes old code. Old `features/brand/` keeps serving the app until Sprint 3.

---

## 0. Pre-Flight Protocol (EVERY new Claude session reading this plan)

Before ANY tool call in a new session, Claude must:

1. `git status --short` — confirm working tree state.
2. `git log --oneline -10` — confirm last commits match "Status" section below.
3. Read this file top-to-bottom.
4. Read `FLOW-SPEC.md` + `DECISIONS.md`.
5. State to user: *"Estamos en Sprint N, tarea X. Último commit: [hash] [title]. Tests: [pasar/fallar]. Próximo paso: [Y]. ¿Avanzo?"*
6. Wait for user confirmation before acting.

No step skipped. No assumption carried from memory.

---

## 1. Sprint 0 — Specs & Lock ✅ COMPLETE

Completed 2026-04-17.

- [x] `FLOW-SPEC.md` written and locked (no open questions left)
- [x] `PLAN.md` written (this file)
- [x] `DECISIONS.md` written — all 18 decisions closed
- [x] `schemas/identity.schema.example.ts` written
- [x] 5 open questions resolved by architect-role decisions (D11–D15)
- [x] Execution model updated to scaffold-first (D16)

---

## 2. Sprint 1 — Full Scaffold (Claude: 3–5 hrs · User: architectural review, no UI validation yet)

**Goal:** Build the entire new architecture IN-TREE as a scaffold. At end of Sprint 1, the new code is present but unused (App Router still points to old `brand/`). No behavior change for end users. Old brand keeps working untouched.

### 2.1 `lib/form-runtime/` — primitive logic

- [ ] Create `frontend/src/lib/form-runtime/schema/types.ts` — FieldSchema, SectionSchema, FieldType union. Matches FLOW-SPEC §2.1.
- [ ] Create `frontend/src/lib/form-runtime/schema/parser.ts` — runtime validator that a schema is well-formed.
- [ ] Create `frontend/src/lib/form-runtime/schema/__tests__/parser.test.ts` (TDD — write first).
- [ ] Create `frontend/src/lib/form-runtime/actions/registry.ts` — `registerAction`, `getAction` API.
- [ ] Create `frontend/src/lib/form-runtime/actions/__tests__/registry.test.ts`.
- [ ] Create `frontend/src/lib/form-runtime/copilot/bridge.ts` — `FormRuntimeBridge` interface and default implementation. Matches FLOW-SPEC §3.4.
- [ ] Create `frontend/src/lib/form-runtime/copilot/__tests__/bridge.test.ts`.
- [ ] Create `frontend/src/lib/form-runtime/index.ts` — public barrel (types + bridge + registry only; no components).
- [ ] `npx tsc --noEmit` green
- [ ] `npx vitest run src/lib/form-runtime/` green
- [ ] Commit: `feat(form-runtime): schema types, action registry, copilot bridge (logic)`

### 2.2 `components/form-runtime/` — React runtime

- [ ] Create `frontend/src/components/form-runtime/FormRuntimeProvider.tsx` — React Context provider exposing bridge methods.
- [ ] Create `frontend/src/components/form-runtime/FormRuntimeProvider.test.tsx`.
- [ ] Create `frontend/src/components/form-runtime/inputs/TextInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/TextareaInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/EnumInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/NumberInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/BooleanInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/UrlInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/EmailInput.tsx` + test.
- [ ] Create `frontend/src/components/form-runtime/inputs/ArrayInput.tsx` + test (list with per-item sub-schema + detail pane variant).
- [ ] Create `frontend/src/components/form-runtime/inputs/CustomInput.tsx` + test (renders from action registry; shows placeholder when action is not yet registered).
- [ ] Create `frontend/src/components/form-runtime/FieldRenderer.tsx` + test (type → input dispatcher).
- [ ] Create `frontend/src/components/form-runtime/EditableField.tsx` + test (focus, change, AI-update subscription via bridge).
- [ ] Create `frontend/src/components/form-runtime/FieldList.tsx` + test (left pane: compact rows).
- [ ] Create `frontend/src/components/form-runtime/FieldDetail.tsx` + test (right pane: active field edit).
- [ ] Create `frontend/src/components/form-runtime/SessionHeader.tsx` + test (progress chip, "run interview", undo-session).
- [ ] Create `frontend/src/components/form-runtime/AutosaveBanner.tsx` + test (saving / saved / error states, D12).
- [ ] Create `frontend/src/components/form-runtime/UniversalEditableSection.tsx` + integration test with a mock schema + values.
- [ ] Create `frontend/src/components/form-runtime/index.ts` — public barrel.
- [ ] Handle mobile <768px: `FieldDetail` becomes full-screen with back button (D13). Test with happy-dom mocking viewport.
- [ ] `npx tsc --noEmit` green
- [ ] `npx vitest run src/components/form-runtime/` green
- [ ] Commit: `feat(form-runtime): React components (UniversalEditableSection, EditableField, inputs)`

### 2.3 `features/brand-studio/` — scaffold + ported logic

- [ ] Create `frontend/src/features/brand-studio/` with folders: `api/`, `hooks/`, `types/`, `schemas/`, `actions/`, `components/`, `pages/`.
- [ ] Port `features/brand/api/*` → `features/brand-studio/api/`. Update internal imports.
- [ ] Port `features/brand/hooks/*` → `features/brand-studio/hooks/`. Update internal imports.
- [ ] Port `features/brand/types/*` (excluding `edit-mode.ts`) → `features/brand-studio/types/`.
- [ ] Port `features/brand/store/*` if any → `features/brand-studio/store/`.
- [ ] Port `features/brand/components/empty-state/BrandEmptyState.tsx` → `features/brand-studio/components/BrandEmptyState.tsx` (D15).
- [ ] Add `features/brand-studio/actions/registry.ts` — registers all brand-studio actions on module load (even if the action components are stubs in Sprint 1).
- [ ] Add `features/brand-studio/actions/placeholders.tsx` — temporary stub components for each action the schemas reference. Each stub renders `<div>Action "{name}" pendiente de portar en Sprint 2</div>`. Register them in `registry.ts`. This lets Sprint 1 schemas reference actions without Sprint 2 being done.
- [ ] Port tests along with ported files; update import paths.
- [ ] `npx tsc --noEmit` green
- [ ] `npx vitest run src/features/brand-studio/` green
- [ ] Commit: `feat(brand-studio): scaffold + port api/hooks/types + action placeholders`

### 2.4 All 15 schemas written

Writing all schemas in one sprint concentrates the simple work. Each schema is a pure JSON-like TS file, ~30–80 lines.

- [ ] `features/brand-studio/schemas/identity.schema.ts` (mirror of the example file).
- [ ] `features/brand-studio/schemas/voice.schema.ts`.
- [ ] `features/brand-studio/schemas/team.schema.ts` (ArrayInput with sub-schema for each member).
- [ ] `features/brand-studio/schemas/authority.schema.ts` (ArrayInput).
- [ ] `features/brand-studio/schemas/testimonials.schema.ts` (ArrayInput).
- [ ] `features/brand-studio/schemas/visuals.schema.ts` (several custom actions).
- [ ] `features/brand-studio/schemas/logos.schema.ts` (custom action).
- [ ] `features/brand-studio/schemas/methodology.schema.ts`.
- [ ] `features/brand-studio/schemas/story.schema.ts`.
- [ ] `features/brand-studio/schemas/narrative.schema.ts`.
- [ ] `features/brand-studio/schemas/positioning.schema.ts` (includes values-essence nested fields).
- [ ] `features/brand-studio/schemas/communication-assets.schema.ts` (ArrayInput).
- [ ] `features/brand-studio/schemas/personality.schema.ts` (several custom actions).
- [ ] `features/brand-studio/schemas/contact.schema.ts`.
- [ ] `features/brand-studio/schemas/avatars.schema.ts` (ArrayInput; custom action for avatar creation).
- [ ] `features/brand-studio/schemas/__tests__/*.test.ts` — one test per schema asserting shape and that it parses.
- [ ] `features/brand-studio/schemas/index.ts` — `SCHEMA_REGISTRY: Record<sectionKey, SectionSchema>`.
- [ ] `npx tsc --noEmit` green
- [ ] `npx vitest run src/features/brand-studio/schemas/` green
- [ ] Commit: `feat(brand-studio): add 15 section schemas`

### 2.5 Page stubs in `features/brand-studio/pages/`

One page per App Router route under `/brand-studio/`. Each page file is 5–15 lines — just wires hook + schema to `UniversalEditableSection`.

- [ ] Identify the route tree under `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/`. Write page files covering each.
- [ ] `EsenciaPage.tsx`, `EstrategiaPage.tsx`, `IdentidadCreativaPage.tsx`, `PublicoPage.tsx`, etc. Exact list to be verified against the route tree.
- [ ] Each page uses the ported hook (e.g., `useBrandSettings`) and the matching schema.
- [ ] `npx tsc --noEmit` green
- [ ] Commit: `feat(brand-studio): page components for all routes (not yet wired to app router)`

### 2.6 Arch test update

- [ ] Update `frontend/src/__tests__/architecture/test-feature-structure.ts` allowlist to include `brand-studio`. Commit message must reference D17.
- [ ] Confirm allowlist contains BOTH `brand` and `brand-studio` (temporary during migration, shrinks in Sprint 5).
- [ ] `npx vitest run src/__tests__/architecture/` green
- [ ] Commit: `chore(arch): accept brand-studio as canonical feature (temporary with brand during migration; see DECISIONS.md D17)`

### 2.7 Sprint 1 close

- [ ] All quality gates green: tsc, eslint, vitest, arch fitness.
- [ ] **USER CHECKPOINT 1 — architectural review.** User reads the tree under `lib/form-runtime/`, `components/form-runtime/`, `features/brand-studio/` and confirms the shape matches FLOW-SPEC. No UI validation yet (app still serves old brand).
- [ ] Update "Status" section below.
- [ ] Push to origin/development.

**Rollback for Sprint 1:** Every commit is independent and touches only new files (plus arch test allowlist). `git revert` of any commit removes that layer without affecting old brand. Full rollback: `git revert` Sprint 1 commits in reverse order; tree returns to post-Sprint-0 state.

---

## 3. Sprint 2 — Port Rich Actions (Claude: 3–6 hrs · User: validate each action in isolation)

**Goal:** Replace the Sprint-1 placeholder actions with real ported components. Schemas already reference them by key.

Process per action (repeat ~10 times). Each action gets its own commit.

**Action checklist (port from `features/brand/` to `features/brand-studio/actions/`):**

- [ ] `VoiceCloneAction.tsx` (from `brand/sections/voice/voice-form.tsx`)
- [ ] `PersonalityClone.tsx` (from `brand/sections/personality/clone-upload.tsx`)
- [ ] `DimensionSliders.tsx` (from `brand/sections/personality/dimension-sliders.tsx`)
- [ ] `PresetCatalog.tsx` (from `brand/sections/personality/preset-catalog.tsx`)
- [ ] `BrandVisualsWizard.tsx` (from `brand/sections/visuals/brand-visuals-wizard.tsx`)
- [ ] `SingleImagePicker.tsx` (from `brand/sections/visuals/single-image-picker.tsx`)
- [ ] `ThemeInjector.tsx` (from `brand/sections/visuals/theme-injector.tsx`)
- [ ] `LogoKitAction.tsx` (from `brand/sections/logos/logo-kit.tsx`)
- [ ] `ImageGalleryPicker.tsx` (from `brand/sections/team/image-gallery-picker.tsx`)
- [ ] `AvatarAction.tsx` (from `brand/sections/avatars/avatar-form.tsx` — note: creates a sub-entity via separate API, not a field)
- [ ] `SmartFillDialog.tsx` (from `brand/components/smart-fill/SmartFillDialog.tsx`)
- [ ] `OnboardingWizard.tsx` (from `brand/components/onboarding/OnboardingWizard.tsx` and related step files)
- [ ] `LegalAction.tsx` (from `brand/components/legal/LegalManager.tsx` + `LegalForm.tsx`) — D15

For each action:
- [ ] Copy file(s) to `features/brand-studio/actions/`.
- [ ] Rewire imports to use brand-studio's api/hooks/types (not brand/).
- [ ] Adapt props signature to `(value, onChange, props)` contract expected by the action registry.
- [ ] Port associated tests (rename imports).
- [ ] Replace the placeholder entry in `features/brand-studio/actions/registry.ts` with the real component.
- [ ] Quality gates green.
- [ ] Commit: `feat(brand-studio): port {actionName} as action`
- [ ] After VoiceCloneAction, BrandVisualsWizard, PersonalityClone, LogoKitAction, AvatarAction and OnboardingWizard (the complex ones): **USER CHECKPOINT** per action, rendered in a dev harness page if needed.

**Sprint 2 exit criteria:** all 13 actions live, no `actions/placeholders.tsx` entries remain, all their tests green.

**Rollback for Sprint 2:** per-action commits independent. `git revert` a single action commit restores the placeholder for that one action only.

---

## 4. Sprint 3 — App Router Flip (Claude: 30–60 min · User: full UI regression)

**Goal:** Replace old brand imports in App Router pages with brand-studio page imports. Single atomic commit. After this commit, the app uses the new code.

- [ ] Identify each `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/**/page.tsx` file.
- [ ] Each page.tsx changes from `import { <OldView> } from "@/features/brand/..."` to `import { <NewPage> } from "@/features/brand-studio/pages/..."`.
- [ ] Similarly update any non-brand-studio route that imported from brand/ (grep `from "@/features/brand/"`).
- [ ] Verify no remaining imports from `features/brand/` outside the `brand/` folder itself (old brand becomes self-contained before deletion in Sprint 5).
- [ ] Quality gates green: tsc, eslint, vitest, arch fitness.
- [ ] **USER CHECKPOINT 2 — full brand studio UI walkthrough.** User opens each route under `/brand-studio/`, validates: fields render, edit works, autosave banner shows, copilot focus bar updates, custom actions fire, mobile layout, revert/undo. Any broken section → fix in a follow-up commit before proceeding to Sprint 4.
- [ ] Commit: `feat(brand-studio): flip app router to use brand-studio pages`

**Rollback for Sprint 3:** a single `git revert` returns all routes to old brand. Nothing else changes.

---

## 5. Sprint 4 — Copilot Refactor (Claude: 2–4 hrs · User: validate copilot flows)

**Goal:** Collapse focus/interview/preview into `copilotSession`. Remove dead copilot UI. Wire copilot store to `FormRuntimeBridge`.

### 5.1 Copilot store reshape

- [ ] Refactor `features/copilot/store/copilot-store.ts`:
  - Remove `focusEntity`, `focusSnapshot`, `interviewProgress`, `previewData`.
  - Add `session: { sectionKey, entityId, procedure, progress?, startedAt, snapshot }` and `focusedField: { id, label, path }`.
  - Keep `selectedFields`, chat state, UI state.
- [ ] Update all copilot store consumers: `use-copilot-chat.ts`, `use-copilot-ui-action.ts`, any component reading removed fields.
- [ ] Update copilot types in `features/copilot/types/`.
- [ ] Update copilot store tests.
- [ ] Quality gates green.
- [ ] Commit: `refactor(copilot): collapse focus+interview+preview into session`

### 5.2 Wire bridge

- [ ] `FormRuntimeProvider` (Sprint 1) calls `copilotStore.connectBridge(bridge)` on mount; disconnects on unmount.
- [ ] Copilot tools that previously dispatched `copilot:field-update` window events now call `bridge.patchField(path, value)` directly via store.
- [ ] Remove the `window.addEventListener("copilot:field-update")` registrations in `EditableField` / `WithCopilot` (the latter is deleted).
- [ ] Update copilot chat component to read `session.sectionKey` + `focusedField` for framing.
- [ ] Quality gates green.
- [ ] Commit: `refactor(copilot): wire bridge to form-runtime, drop window events`

### 5.3 Delete dead copilot components

- [ ] Delete `features/copilot/components/CopilotPreviewPane.tsx` + its test.
- [ ] Delete `features/copilot/components/FocusBar.tsx` + its test (replaced by SessionHeader inside form-runtime).
- [ ] Delete `features/copilot/components/FocusModeButton.tsx` + its test.
- [ ] Delete `features/copilot/components/shared/InterviewModeButton.tsx` + its test.
- [ ] Delete `features/copilot/components/WithCopilot.tsx` + its test (replaced by EditableField).
- [ ] Delete `features/copilot/config/interview-preview-registry.ts` + its test.
- [ ] Delete `features/copilot/components/interview/EditionPreviewCard.tsx`.
- [ ] Delete `features/copilot/components/interview/InterviewDateBlock.tsx`.
- [ ] Handle offer-studio and brand preview files that reference the registry — if they only exist to feed the registry (PersonaPreviewSections, OfferPreviewSections, etc.), delete them too; otherwise leave as explicit TODOs tied to future offer-studio migration.
- [ ] Update Sidebar / CopilotRail / CopilotHeader if any reference the deleted components.
- [ ] Quality gates green.
- [ ] **USER CHECKPOINT 3 — copilot walkthrough.** User: open brand-studio, click copilot icon, run a free chat, then "Entrevista guiada", verify focus-bar chip in SessionHeader, verify undo-session.
- [ ] Commit: `chore(copilot): delete dead preview/focus components`

**Rollback for Sprint 4:** per-commit reverts independent. Brand-studio reads via `FormRuntimeBridge`, not directly from copilot store internals, so brand-studio keeps working even if copilot refactor is reverted.

---

## 6. Sprint 5 — Delete Old Brand (Claude: 30–60 min · User: final regression)

**Goal:** Zero dead code. `features/brand/` folder no longer exists.

- [ ] Confirm `features/brand/sections/` contents are all obsolete (they are — every section got a schema + actions ported in Sprints 1–2).
- [ ] Delete `features/brand/components/forms/EditSheetManager.tsx` + test.
- [ ] Delete `features/brand/components/interview/*` + tests.
- [ ] Delete `features/brand/components/views/*` (all view files).
- [ ] Delete `features/brand/config/sections.ts` (or trim it if anything else uses it — unlikely).
- [ ] Delete `features/brand/types/edit-mode.ts`.
- [ ] Delete any remaining files in `features/brand/`, check each — they should all be dead.
- [ ] Delete `features/brand/` folder entirely.
- [ ] Shrink arch test allowlist: remove `brand` from canonical names. D17 allows this.
- [ ] Global grep verification:
  - [ ] `grep -r "from.*features/brand/" frontend/src/` → 0 hits
  - [ ] `grep -r "EditSheetManager" frontend/src/` → 0 hits
  - [ ] `grep -r "WithCopilot" frontend/src/` → 0 hits
  - [ ] `grep -r "FocusBar" frontend/src/` → 0 hits (or renamed references only)
  - [ ] `grep -r "CopilotPreviewPane" frontend/src/` → 0 hits
- [ ] Quality gates green.
- [ ] **USER CHECKPOINT 4 — final validation.** Full brand-studio + copilot walkthrough. Nothing missing, nothing broken.
- [ ] Commit: `chore(brand): remove deprecated features/brand after brand-studio migration`
- [ ] Push to origin/development.

**Rollback for Sprint 5:** `git revert` restores the deletion. Nothing else moves.

---

## 7. Status (UPDATE WITH EVERY COMMIT)

Last updated: **2026-04-17 end of session — Sprint 0 COMPLETE, all decisions locked, ready for fresh-conversation Sprint 1.**

| Sprint | State | Last commit | Quality gates |
|---|---|---|---|
| Sprint 0 — Specs | ✅ Complete | `01eb07a2` (+ decisions lock commit pending push) | n/a (no code) |
| Sprint 1 — Full scaffold | Not started | — | — |
| Sprint 2 — Port rich actions | Not started | — | — |
| Sprint 3 — App router flip | Not started | — | — |
| Sprint 4 — Copilot refactor | Not started | — | — |
| Sprint 5 — Delete old brand | Not started | — | — |

---

## 8. Scope Creep Log (MUST STAY EMPTY)

If during migration anything arises that is not explicitly in scope (FLOW-SPEC §7), it MUST be logged here with status `deferred` and added to `docs/mejoras-proceso/to-do.md`. Claude MUST NOT silently absorb out-of-scope work.

_(empty — good)_

---

## 9. Guarantees Recap

1. Every commit is ship-able. No commit breaks brand studio.
2. Every code change has a test in the same commit (TDD).
3. Every deletion has a corresponding line in this plan.
4. Every new Claude session runs §0 pre-flight.
5. User checkpoints are NOT optional — Claude blocks on them.
6. Scope creep goes to §8 log, not into the diff.
7. Rollback per sprint is one `git revert` on a specific hash.
8. All architectural decisions locked in DECISIONS.md §D1–D18 — no re-litigation in execution sessions.

---

## 10. How to Resume in a New Conversation

Open a fresh Claude Code conversation. Paste this primer:

```
Sigo el refactor brand studio. Lee PLAN.md, FLOW-SPEC.md y DECISIONS.md en
docs/ux-sessions/2026-04-17-universal-editable-form-component/ y la memoria
project_brand_studio_refactor.md. Ejecuta pre-flight §0 del PLAN, dime dónde
estamos y cuál es el próximo paso, y espera mi confirmación antes de avanzar.
```

That is the whole startup cost. No context from the planning conversation is needed.
