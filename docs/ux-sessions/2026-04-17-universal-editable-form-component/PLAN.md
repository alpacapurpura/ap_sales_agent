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

## 3. Sprint 2 — Form-runtime URL-driven + port 7 survivor actions + PersonaDetailView refactor

**Scope pivoted 2026-04-17 afternoon after usage audit.** See `SPRINT-2-PLAN.md` for the complete plan; this section is the top-level summary and delegates detail to that file.

**Key changes vs the earlier draft of this section (git history preserves the diff):**

- Five extraction/wizard actions (SmartFillDialog, OnboardingWizard, VoiceCloneAction, PersonalityClone, BrandVisualsWizard) are NOT ported. They move to Sprint 4 as copilot tools (see §5).
- OnboardingWizard deferred: rebuild later with an industry-standard pattern in its own sprint.
- AvatarAction (sub-entity) is purged; its replacement is the existing `PersonaDetailView` refactor (see Sprint 2.8).
- LegalAction confirmed alive via `FooterSection.onEditLegal` — port it.
- Data-model purge (`BrandTeam`, `team_metadata`, duplicated BrandIdentity visual fields, `positioning.values` → personality) moves to its own Sprint 2.D (full-stack backend + frontend).
- **Route-per-field** is the new form-runtime contract (Sprint 2.0b). UniversalEditableSection becomes URL-driven; FieldList renders `<Link>`s.

**Sprint 2 deliverables (summary):**

1. Sprint 2.0 foundations — Storybook baseline + route-per-field refactor + generic `SectionPage` + 7 placeholder stories.
2. Sprint 2.1–2.7 — port 7 survivor actions (ImageGalleryPicker, SingleImagePicker, ThemeInjector, DimensionSliders, PresetCatalog, LogoKitAction, LegalAction) with Storybook stories + Vitest tests + URL awareness.
3. Sprint 2.8 — port `PersonaDetailView` refactored into form-runtime.
4. Delete redirect pages (`/tono-y-voz`, `/creativos`, `/assets`).

**Sprint 2.D (parallel track, NOT blocking Sprint 2):** Alembic migration + Pydantic DTO update + frontend type purge for the dead model fields. Runs full-stack with backend + frontend agent coordination. Can land before or after Sprint 3 flip; logged as a separate sprint so Sprint 2 keeps frontend-only scope.

**Rollback for Sprint 2:** per-commit independent. `git revert <hash>` isolates any single port, foundation commit, or PersonaDetailView refactor.

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

## 5. Sprint 4 — Copilot Refactor + absorb 5 extraction tools (Claude: 6–10 hrs · User: validate copilot flows)

**Goal:** Collapse focus/interview/preview into `copilotSession`. Remove dead copilot UI. Wire copilot store to `FormRuntimeBridge`. **AND** deliver the five copilot tools that absorb the purged extraction flows from Sprint 2's scope pivot:

| Tool | Replaces (purged in Sprint 2) | Inputs | Output |
|---|---|---|---|
| `extract_brand_from_url` | SmartFillDialog(initial) + Onboarding.StepWebsite + BrandVisualsWizard | url | BrandSettings diff |
| `extract_brand_from_docs` | SmartFillDialog(update) + Onboarding.StepDocuments | files[] | BrandSettings diff |
| `analyze_voice_style` | VoiceCloneAction | text | { voice_tone } |
| `extract_visuals_from_url` | BrandVisualsWizard (visuals-only subflow) | url | BrandVisuals diff |
| `clone_personality_from_chat` | PersonalityClone (clone-upload) | conversation | PersonalityProfile diff |

**Interaction pattern for every tool:**
1. User invokes via natural chat ("extrae desde mi web") or a button in SessionHeader.
2. Copilot requests missing inputs (URL, files, conversation) via structured chat messages.
3. Tool runs on backend; returns a structured diff.
4. Copilot previews the diff in chat as "suggested change" chips, one per field.
5. User approves per chip; copilot calls `bridge.patchField(path, value)` for each approved change.

Backend work lives under `backend/src/modules/copilot/application/tools/`; frontend chat-UI work under `features/copilot/components/`.

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

### 5.4 Tool backends (NEW — absorbs Sprint 2 purges)

- [ ] `extract_brand_from_url` — backend tool under `backend/src/modules/copilot/application/tools/`. Wraps the existing `brandApi.extractFullBrand` job flow but returns a structured diff (field → new value → confidence).
- [ ] `extract_brand_from_docs` — backend tool. Same wrapping around the docs variant; file upload handled via signed-upload endpoint.
- [ ] `analyze_voice_style` — backend tool wrapping the existing `/api/v1/brand/style/analyze-style` endpoint.
- [ ] `extract_visuals_from_url` — backend tool wrapping the visuals-only extraction + ColorThief palette derivation (port the intent of `BrandVisualsWizard`'s client-side palette generator to the backend so the result is deterministic and auditable).
- [ ] `clone_personality_from_chat` — backend tool (may already exist in `copilot/application/tools/`; verify and extend).
- [ ] All tools register in `copilot/application/tools/registry.py` so the route-based tool selector can expose them on the right pages.
- [ ] Chat-UI components: file dropzone, URL input card, diff preview chips, "apply change" button wired to `bridge.patchField`.
- [ ] Storybook stories for each chat-UI component (`Copilot/Tools/*`).
- [ ] Integration tests (backend pytest + frontend Vitest).
- [ ] Commit: one per tool, `feat(copilot): add <tool> tool (Sprint 4.N)`

### 5.5 Sprint 4 exit gate

- All 5 tools registered and invocable from a chat.
- Chat-UI components tested, Storybook stories exist.
- Copilot store collapsed to `session` + `focusedField`; `WithCopilot`, `FocusBar`, `CopilotPreviewPane`, `interview-preview-registry` deleted.
- User checkpoint: open brand-studio, type "extrae mi marca desde https://...", confirm every field arrives as a diff-chip and applies correctly.

**Rollback for Sprint 4:** per-commit reverts independent. Brand-studio reads via `FormRuntimeBridge`, not directly from copilot store internals, so brand-studio keeps working even if copilot refactor is reverted.

---

## 5bis. Sprint 2.D — Data model purge (parallel track, full-stack)

**Not a sequential sprint.** Can run before or after Sprint 3 flip; logically belongs once the new types are consumed (Sprint 2 porting uses the old shape, Sprint 3 flips, then Sprint 2.D cleans the shape).

**Purges (backend + frontend coordinated):**

| Field / type | Decision | Reason |
|---|---|---|
| `BrandTeam` (legacy interface) | DELETE | Superseded by `KeyFigure[]` |
| `BrandSettings.team_metadata` | DELETE | Last writer unknown; no reader in new code |
| `BrandIdentity.primary_color` / `accent_color` / `font_heading` / `font_body` / `background_color` / `text_primary_color` / `text_on_primary` / `design_style` / `usage_guidelines` | DELETE | Duplicate of BrandVisuals; BrandVisuals is the SSoT. Salvage any tenant value via one-time data migration. |
| `BrandPositioning.values.core_values` / `.personality_traits` / `.archetype` | MOVE to `Personality` | Personality section absorbs these per Sprint 2 decision |

**Work items:**
- [ ] Backend: Alembic idempotent migration — copy salvaged values to BrandVisuals / Personality, then drop the old columns.
- [ ] Backend: Pydantic DTOs + services updated.
- [ ] Backend: pytest regressions + architecture tests.
- [ ] Frontend: types updated in `features/brand-studio/types/` + any consuming component.
- [ ] Frontend: schemas updated (identity.schema removes visuals fields; personality.schema adds values block; positioning.schema removes the values block).
- [ ] Frontend: Storybook stories reflect new shape.
- [ ] Data migration verified on a prod clone before merging.
- [ ] Commit: one commit per concern — `refactor(brand-model): migrate X`.

**Agent split:** backend-expert skill handles migration + DTOs; frontend-expert skill handles types + schemas; auditor skill reviews.

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

Last updated: **2026-04-18 — Sprints 5 + 2.D + 4a + 4b + 4c COMPLETE. Copilot store collapsed to session + focusedField; preview pane retired; FormRuntimeBridge wired. Next: Sprint 4d-h (5 extraction tools) + Sprint 6 (offer-studio editor → form-runtime).**

| Sprint | State | Last commit | Quality gates |
|---|---|---|---|
| Sprint 0 — Specs | ✅ Complete | `e06b7726` | n/a (no code) |
| Sprint 1 — Full scaffold | ✅ Complete + debt-cleaned + pushed | `56b6cfbf` | tsc 0 · eslint 0 / 4587 warn · vitest 1247 tests / 152 files · 10 arch |
| Sprint 2 — URL-driven runtime + 7 survivor ports + PersonaDetail | ✅ Complete + pushed | `bf4bcef8` | tsc 0 · eslint 0 · vitest 1283 tests · 10 arch · build-storybook green |
| Sprint 2.D — Data model purge (backend + frontend) | ✅ Complete + pushed | backend `3e602faa` · frontend `772d3ca9` | ruff 0 · pytest 314 brand tests · arch 86 · tsc 0 · vitest 91 brand-studio tests |
| Sprint 3 — App router flip + route-per-field tree | ✅ Complete + pushed | `3d45858b` | tsc 0 · eslint 0 · vitest 1287 tests · 10 arch · build-storybook green |
| Sprint 4a — Copilot store collapse | ✅ Complete + pushed | `49fa40c0` (combined with 4c) | see 4c |
| Sprint 4b — Wire FormRuntimeBridge | ✅ Complete + pushed | `d5728ebe` + `551043bf` | tsc 0 · eslint 0 / 602 warn · vitest 1176 tests / 149 files · 10 arch |
| Sprint 4c — Delete dead copilot UI | ✅ Complete + pushed | `49fa40c0` | tsc 0 · eslint 0 · vitest 1176 tests · 10 arch · build-storybook green |
| Sprint 4d–h — Five extraction tools | Planned (§5.4) | — | — |
| Sprint 5 — Delete old brand + offer-studio import migration | ✅ Complete + pushed | `8a0729f5` → `87aa7a36` | tsc 0 · eslint 0 / 3595 warn · vitest 1221 tests / 156 files · 10 arch · build-storybook green |
| Sprint 6 — Offer-studio editor → form-runtime (route-per-field) | Planned (new — user directive 2026-04-18: aplicación unificada a nivel de UX URL+campo) | — | — |

**Sprint 4a + 4b + 4c commits (3):**
- `49fa40c0` refactor(copilot): collapse store + retire preview/focus UI (Sprint 4a + 4c). Merges what the PLAN originally split into 3 sub-sprints because the dying UI's consumers made any intermediate state non-compilable. Deletes WithCopilot, FocusBar, CopilotPreviewPane, FocusModeButton, InterviewModeButton, EditionPreviewCard, InterviewDateBlock, interview-preview-registry + all their tests. Collapses focusEntity/focusSnapshot/interviewSessionId/interviewProgress/previewData into `session` + `focusedField` on the store. Drops "expanded" sidebarState. Simplifies CopilotSidebar to chat-only. Strips WithCopilot from the four offer-studio form files that still referenced it.
- `d5728ebe` refactor(copilot): wire FormRuntimeBridge to store, drop window events (Sprint 4b). Adds `activeBridge` + `connectBridge` + `disconnectBridge` to the copilot store. FormRuntimeProvider now registers its bridge on mount. MultiOptionSelector + ProposalCard route Apply through `bridge.patchField(path, value)` instead of dispatching `copilot:field-update` CustomEvents. `useCopilotFieldSync` hook + tests deleted — no remaining consumers.
- `551043bf` chore(offer-studio): delete orphan OfferPreview* files (follow-up to 49fa40c0).

## Sprint 4d–h — Remaining work (planned)

Each tool bundles backend + frontend + tests + storybook. Order is independent; recommended: 4d → 4g → 4e → 4f → 4h (ship the URL-fed extractors first since they're the highest-traffic replacements).

| Tool | Replaces | Backend | Frontend UI | Tests |
|---|---|---|---|---|
| 4d `extract_brand_from_url` | SmartFillDialog(initial) + OnboardingWizard.StepWebsite + BrandVisualsWizard | Wrap `brandApi.extractFullBrand`; register in `copilot/application/tools/registry.py`; return structured diff { field_path → new_value → confidence } | URL input card + per-field diff chips with Apply/Reject per chip → calls `bridge.patchField` | backend pytest integration + frontend vitest + Storybook "Copilot/Tools/ExtractBrandFromURL" |
| 4e `extract_brand_from_docs` | SmartFillDialog(update) + OnboardingWizard.StepDocuments | Same wrapping over docs variant; signed-upload endpoint for file inputs | File dropzone + diff chips | same pattern as 4d |
| 4f `analyze_voice_style` | VoiceCloneAction | Wrap `/api/v1/brand/style/analyze-style` | Text paste + upload + returns `{ voice_tone }` — user Applies → `bridge.patchField("voice_tone", value)` | integration + vitest + storybook |
| 4g `extract_visuals_from_url` | BrandVisualsWizard (visuals-only subflow) | Backend port of ColorThief palette derivation so results are deterministic and auditable; chain with visuals-only extraction | URL input + palette preview + per-field diff chips (primary_color, accent_color, fonts, etc.) | integration + vitest + storybook |
| 4h `clone_personality_from_chat` | PersonalityClone | Verify existing tool at `copilot/application/tools/` — extend if needed; takes a chat transcript and emits `PersonalityProfile` diff | Conversation paste + diff chips for each dimension/value | integration + vitest + storybook |

Shared implementation conventions:
1. Every tool registers in `copilot/application/tools/registry.py` with route-based selection so the tool only appears on brand-studio pages.
2. Every chat-UI component reads `useCopilotStore.getState().activeBridge` to apply. Without a mounted bridge, the UI still renders but Apply is a no-op and shows "conectá una sección primero".
3. Every diff-chip component uses `@storybook/test` `fn()` for handlers in stories. Title: `Copilot/Tools/<Name>`.
4. Backend tool signatures: async functions taking a Pydantic input DTO and returning a structured diff DTO. Inputs passed from chat via copilot's `tool_call` SSE event.

## Sprint 6 — Offer-studio editor → form-runtime (planned, now edition-aware)

User directives (2026-04-18):
1. The offer-studio editor must adopt the same route-per-field form-runtime UX as brand-studio.
2. Editor URL must carry the edition (`/edition/[code]/`) as a required segment, with `code = "evergreen"` as a virtual code for offers without a launch context.
3. Section visibility per archetype is canonical data — backend must be the SSoT (frontend `getSectionsForOffer` is retired).
4. Fields that differ between offer-level and edition-level (pricing overrides, cohort-specific details) must route to the correct aggregate without duplicating schemas.

**Full execution plan:** `SPRINT-6-PLAN.md` in this folder. This section is a
pointer — the authoritative breakdown, phase gates, and checklist live there.

Summary of scope:
- Add `section_catalog.py` domain module + extend `archetype_catalog.py` with `sections: tuple[SectionKey, ...]`.
- Extend `GET /api/v1/offer/archetypes/catalog` to expose per-archetype sections + global SECTION_CATALOG.
- 16 form-runtime schemas under `features/offer-studio/schemas/` (one per SectionKey).
- Server-safe `OFFER_SECTION_PAGE_MAP` + `OfferStudioSectionSlug` pattern (mandatory split per LEARNINGS).
- Catch-all route `/offer-studio/[offerId]/edition/[code]/[section]/[[...fieldId]]/page.tsx` with Server Component importing the `.ts` map.
- `FieldSchema.owner` extension routing saves to `updateOffer` vs `updateEdition` for MIXED scope sections.
- Backwards-compat redirects from legacy `/offer-studio/offer/:offerId/*` shapes (two-phase removal).
- InstructorsSelector refactor + delete `brand-studio/components/legacy-team/` at phase H.
- Copilot route-tool map + `navigation_map.py` updates.

Decisions locked: DECISIONS.md §D19–D27.

**Sprint 5 commits (7):**
- `54d4ab74` feat(brand-studio): port business-types components (S5.1)
- `668c37d2` feat(brand-studio): port legacy TeamManager adapter (S5.2)
- `7c0861eb` refactor(offer-studio): migrate brand imports to brand-studio (S5.3)
- `e9341681` chore(offer-studio): remove useAutoSave shim (S5.4)
- `0fdec609` chore(copilot): remove brand + buyer_persona preview registry entries (S5.5)
- `8848ab20` chore(brand): delete features/brand/ after brand-studio migration (S5.6)
- `8a0729f5` chore(design-system): sync feature registry with brand removal (S5.7)

Sprint 5 took 8 commits (one scope adjustment along the way). 116 files + 17,466 lines removed from frontend/src/features/brand/. Warning baseline dropped from ~4924 → 3595 (-1329). 66 tests retired with the deleted feature; brand-studio + offer-studio + copilot retained all their coverage.

**Sprint 1 commits (11):**
- `6a241f20` form-runtime schema types + parser (S1.1)
- `b9598061` form-runtime action registry (S1.2)
- `fbda97b9` form-runtime copilot bridge (S1.3)
- `fa426159` adopt useAutoSave as shared primitive (S1.4)
- `7d031265` inputs + FieldRenderer (S1.5a)
- `a332efd7` Provider + Context + EditableField + AutosaveBanner (S1.5b)
- `2374a6cd` List/Detail/Header + UniversalEditableSection (S1.5c)
- `55f3c66d` shadcn Slider (S1.6)
- `59018b80` brand-studio api/hooks/types/utils port (S1.7)
- `04796793` brand-studio action placeholders + registry (S1.8)
- `04d8bcce` 15 section schemas + SCHEMA_REGISTRY (S1.9)
- `c2979a0b` brand-studio page stubs wired to schemas (S1.10)
- `b841f062` arch test allowlist for brand-studio (S1.11)

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
