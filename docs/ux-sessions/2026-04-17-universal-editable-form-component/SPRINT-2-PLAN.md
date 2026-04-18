# Sprint 2 — Form-runtime URL-driven + port 7 survivor actions + PersonaDetailView refactor

**Session folder:** `docs/ux-sessions/2026-04-17-universal-editable-form-component/`
**Depends on:** Sprint 1 COMPLETE (commit `56b6cfbf` pushed to origin/development).
**Scope change (2026-04-17 afternoon):** purged from 13 → 8 ports after usage audit. Five extraction/wizard flows move to copilot Sprint 4. Onboarding deferred to a later sprint. Data-model purge moved to its own Sprint 2.D.

---

## 1. Final scope

### 1.1 What Sprint 2 DELIVERS

1. **Storybook baseline** (`Form Runtime/Actions/*`) as the visual-verification surface.
2. **Route-per-field refactor** of the form-runtime (UniversalEditableSection becomes URL-driven). Every field of every section is deep-linkable at `/{tenantId}/brand-studio/{section}/{fieldId}`.
3. **Port 7 survivor actions** with Storybook stories + Vitest tests + URL awareness:
   - ImageGalleryPicker (team photos)
   - SingleImagePicker (logo/favicon)
   - ThemeInjector (apply visuals live)
   - DimensionSliders (personality tuning)
   - PresetCatalog (personality presets)
   - LogoKitAction (logo kit editor)
   - LegalAction (still used by Esencia's FooterSection)
4. **PersonaDetailView refactor** — the only "new UI" in brand/ that survives. Ported into form-runtime, WithCopilot stripped, bridge-driven.
5. **Purge of dead paths** — redirect pages (`/tono-y-voz`, `/creativos`, `/assets`) die with the route restructure.

### 1.2 What Sprint 2 DOES NOT TOUCH

- **AI extraction flows** (SmartFillDialog, OnboardingWizard, VoiceCloneAction, PersonalityClone, BrandVisualsWizard) → Sprint 4 absorbs them as copilot tools. See §6.
- **Data model purge** (`BrandTeam`, `team_metadata`, duplicated visual fields, `positioning.values` → personality) → Sprint 2.D (full-stack backend + frontend coordinated).
- **Onboarding rebuild** → deferred to a later dedicated sprint with an industry-standard pattern.
- **App Router flip** → Sprint 3 unchanged.

### 1.3 Learnings from Sprint 1 (must apply to every Sprint 2 commit)

Eighteen lessons that prevented and surfaced debt during Sprint 1. They remain non-negotiable (details unchanged from the previous revision of this plan — see git history at `da341e2d`). Short form:

- **Typing:** generic `object` beats `Record<string, unknown>`; domain types flow to runtime via cast at the boundary.
- **Recursion:** inject renderers, do not import them circularly.
- **Registry rendering:** use `createElement`, not `<Component />`, to side-step the "nested component definitions" rule.
- **React rules:** no ref reads in render; no setState in effect without a condition-keyed inner component.
- **Side-effect imports:** centralize in schemas/index.ts.
- **Testing:** `fireEvent.change()`, not raw `dispatchEvent`; `toFake: ["setTimeout", "clearTimeout"]` + `flushMicrotasks`; `clearRegistry` in beforeEach; `.getAttribute("rows")` for DOM attrs.
- **Lint hygiene:** `eslint --fix` after every file batch, before writing tests; cognitive complexity ≤15; 0 errors gate.
- **Data contracts:** port 1:1 first, refactor later in the same commit; React Query keys are immutable during migration; `useAutoSave` is the only autosave.
- **SSR:** window/localStorage behind `useEffect`.

---

## 2. Sprint 2.0 — Foundations (blocking pre-work, 4 commits)

### 2.0a — Storybook baseline

Storybook 10 (`@storybook/nextjs-vite`) is already installed; existing `src/stories/molecules/` stories prove the setup is stable. No config changes required.

- [ ] Document title hierarchy in `src/stories/README.md`:
  - `Molecules/<Component>` — existing (unchanged)
  - `Form Runtime/Inputs/<Name>` — opt-in, Sprint 3+
  - `Form Runtime/Actions/<Name>` — this sprint
  - `Brand Studio/Pages/<Name>` — Sprint 3+
- [ ] Declare colocation convention for new stories (`features/brand-studio/actions/stories/`), matching `.test.tsx` placement.
- [ ] Verify `npm run storybook` + `npm run build-storybook` succeed.
- [ ] Commit: `docs(storybook): colocation convention + title hierarchy`

### 2.0b — Route-per-field refactor of form-runtime

**Architectural decision D1(a):** URL is the single source of truth for which field is active. The runtime no longer owns `activeFieldId` state; it reads it from the URL.

Design contract:
- Route pattern: `/{tenantId}/brand-studio/{section}/{fieldId}` (field-level) and `/{tenantId}/brand-studio/{section}` (section-level; defaults to first field).
- `UniversalEditableSection` receives `activeFieldId` as a prop from the page; no internal `useState` for it. The FieldList renders Next.js `<Link>`s, not onClick handlers.
- Mobile detail pane still full-screen below 768 px — the URL already distinguishes list-view vs field-view (no field in path ⇒ list view; field in path ⇒ detail view).

Tasks:
- [ ] Modify `UniversalEditableSection` to accept `activeFieldId: string | null` as a prop. Remove its internal `useState`. Remove the `mobileDetailOpen` state; derive presence from `activeFieldId`.
- [ ] Add optional `navigateFieldPath: (fieldId: string | null) => string` prop so pages plug their routing strategy. Default = append `/{fieldId}` to current pathname.
- [ ] `FieldList` renders `next/link` wrappers instead of buttons (keyboard + screen-reader friendly).
- [ ] `FieldDetail` "Atrás" button on mobile routes to the section-level URL via `router.push`, not an onBack callback.
- [ ] Existing tests ported (Vitest mocks `next/navigation` via `vi.mock`).
- [ ] `UniversalEditableSection` tests updated to pass `activeFieldId` via prop; add a test for navigation link hrefs.
- [ ] `npx tsc --noEmit` + `vitest run src/components/form-runtime/` green.
- [ ] Commit: `refactor(form-runtime): URL-driven active field (route-per-field support)`

### 2.0c — App Router scaffold for `/brand-studio/{section}/{fieldId}`

Pages created but **not yet wired to App Router** (Sprint 3 flips). Sprint 2.0c writes the page components inside `features/brand-studio/pages/` and leaves App Router untouched.

- [ ] Replace existing 6 page stubs with 1 generic `SectionPage.tsx` that accepts `schema` + `fieldId?` props and wires `useBrandSettings` / matching update-fn + `UniversalEditableSection`.
- [ ] Rewrite `pages/index.ts` to export the generic + a per-section factory (EsenciaPage = SectionPage(identitySchema, …), etc.) — 15 thin factories vs 15 fat pages.
- [ ] Add Storybook stories for `SectionPage` with fixture schemas (1 story per layout state: loading / populated / empty / error).
- [ ] Commit: `feat(brand-studio): generic SectionPage + 15 factories`

### 2.0d — Baseline Storybook stories for 7 survivor actions

Before porting any real action, land 7 placeholder stories under `Form Runtime/Actions/*` so the Storybook sidebar shows the full survivor catalog.

- [ ] One `.stories.tsx` per survivor (7 files, each exports a single `Default` story rendering the current placeholder component).
- [ ] `args` pass `value` + `onChange` so Controls + Actions panels are exercised.
- [ ] `npm run build-storybook` succeeds.
- [ ] Commit: `docs(storybook): baseline placeholder stories for 7 survivor actions`

### 2.0 Exit gate

All of:
- `tsc --noEmit` → 0 errors
- `eslint src/components/form-runtime/ src/features/brand-studio/` → 0 errors
- `vitest run src/components/form-runtime/` → all green
- `npm run build-storybook` succeeds
- Arch fitness → 10/10
- User checkpoint **Sprint-2.0**: user opens Storybook locally, confirms 7 placeholder cards render under `Form Runtime/Actions`; user navigates the in-dev app to a field URL (`/{t}/brand-studio/esencia/brand_name`) and confirms it shows the detail pane for that one field.

---

## 3. Sprint 2.1–2.7 — Port 7 survivor actions

Order (cheapest → heaviest), each one its own commit, each a complete unit (code + tests + story + registry update). Per-action blocking checklist in §4.

| # | Action | Key | Source | TValue | Est. | Checkpoint |
|---|---|---|---|---|---|---|
| 2.1 | ImageGalleryPicker | `image-gallery` | `sections/team/image-gallery-picker.tsx` | `string` url | 20–30 min | no |
| 2.2 | SingleImagePicker | `single-image` | `sections/visuals/single-image-picker.tsx` | `string` url | 20–30 min | no |
| 2.3 | ThemeInjector | `theme-injector` | `sections/visuals/theme-injector.tsx` | `unknown` | 15–25 min | no |
| 2.4 | DimensionSliders | `personality-dimensions` | `sections/personality/dimension-sliders.tsx` | `PersonalityDimensions` | 30–45 min | ✅ CP-2A |
| 2.5 | PresetCatalog | `personality-presets` | `sections/personality/preset-catalog.tsx` | `string` preset key | 25–40 min | ✅ CP-2B |
| 2.6 | LogoKitAction | `logo-kit` | `sections/logos/logo-kit.tsx` | `BrandLogos` | 30–45 min | ✅ CP-2C |
| 2.7 | LegalAction | `legal` | `components/legal/{LegalManager,LegalForm}.tsx` | `{ legal_name, tax_id, terms_url, privacy_url, … }` | 30–45 min | ✅ CP-2D |

Checkpoint protocol: user opens `npm run storybook`, reviews the 4 required stories (`Default`, `Populated`, `Loading` if applicable, `Error` if applicable), signs off before the next port starts.

---

## 4. Per-action preflight checklist (blocking)

Tick every box before closing a commit. Silent workarounds are scope creep — log to §7 or fail the commit.

```
Action: <name>
Source (old): features/brand/<path>/<file>.tsx
Target (new): features/brand-studio/actions/<Name>Action.tsx
Registry key: <kebab-key>
Story file: features/brand-studio/actions/stories/<Name>Action.stories.tsx

Contract
- [ ] ActionComponent<TValue>: (value, onChange, props?)
- [ ] TValue is the correct domain type (not unknown unless truly opaque)
- [ ] onChange writes back values matching the schema field's `path`
- [ ] URL-driven: action renders inside the Field URL; navigating away terminates pending work

Imports rewired
- [ ] @/features/brand/api → @/features/brand-studio/api
- [ ] @/features/brand/hooks → @/features/brand-studio/hooks
- [ ] @/features/brand/types → @/features/brand-studio/types
- [ ] WithCopilot / FocusModeButton / InterviewModeButton → REMOVED (EditableField owns focus now)
- [ ] No circular imports introduced (`npx madge --circular` passes)

React quality
- [ ] No inline JSX callback props inside map() — hoist with useCallback
- [ ] No setState in useEffect without a keyed inner component
- [ ] No ref reads in render; refs invoked only from handlers/effects
- [ ] useMemo / useCallback stabilize large props
- [ ] Consumer code uses the new useAutoSave if it needs debounced save

Tests (Vitest)
- [ ] actions/__tests__/<Name>Action.test.tsx
- [ ] ≥3 tests: happy path, edge case, failure
- [ ] beforeEach(clearRegistry) when the test registers actions
- [ ] fireEvent / userEvent — no raw dispatchEvent
- [ ] Debounce assertions use vi.useFakeTimers + flushMicrotasks

Storybook
- [ ] Colocated: actions/stories/<Name>Action.stories.tsx
- [ ] `title: "Form Runtime/Actions/<Name>"`
- [ ] Default + Populated minimum; Loading + Error when applicable
- [ ] `tags: ["autodocs"]`
- [ ] `args.onChange = fn()` from @storybook/test — Actions panel wired
- [ ] a11y addon clean (0 violations) or documented exception
- [ ] `npm run build-storybook` succeeds with the new story

Bootstrap
- [ ] placeholders.tsx entry REMOVED (not just deprecated)
- [ ] registry.ts#PLACEHOLDERS entry points at real component
- [ ] BRAND_STUDIO_ACTION_KEYS const unchanged
- [ ] Old features/brand/<path> still present (Sprint 5 deletes)

Quality gates
- [ ] cd frontend && npx tsc --noEmit → 0 errors
- [ ] cd frontend && ./node_modules/.bin/eslint <new-files> → 0 errors
- [ ] cd frontend && npx vitest run → baseline + new tests all green
- [ ] cd frontend && npx vitest run src/__tests__/architecture/ → 10/10 green
- [ ] cd frontend && npm run build-storybook → succeeds

Commit
- [ ] Conventional Commits: `feat(brand-studio): port <ActionName> as action (Sprint 2.N)`
- [ ] Body lists placeholder replaced, tests covered, stories exported
- [ ] Screenshot of Storybook attached to checkpoint commits (CP-2A..CP-2D)
- [ ] Pushed to origin/development at end of day
```

---

## 5. Sprint 2.8 — PersonaDetailView refactor & port

The only "new UI" in `features/brand/` that survives. Currently uses `WithCopilot`, section-based progress bar, inline edit. Port it to form-runtime semantics.

- [ ] Define a `PersonaDetailSchema` (form-runtime SectionSchema) covering BuyerPersona fields: demographics, pain_desire, psychographics, purchase_behavior, etc. One schema per logical block; or a single schema with grouped fields.
- [ ] Migrate PersonaDetailView to `features/brand-studio/pages/PersonaDetailPage.tsx` using the generic SectionPage + persona schema. WithCopilot is stripped — the copilot sees the persona via the bridge.
- [ ] `/brand-studio/publico/persona/{personaId}/{fieldId?}` becomes URL-driven like all other sections.
- [ ] `useBuyerPersona` (already refactored to use `useAutoSave` in the Sprint 1 debt-cleanup commit `56b6cfbf`) wires the save function.
- [ ] Stories: `Brand Studio/Pages/PersonaDetail` with fixtures (empty persona / populated / with errors).
- [ ] Per-block Vitest integration tests.
- [ ] User checkpoint **CP-2E**: full persona flow — create, edit a field, copilot "sees" the field via the bridge, undo-session reverts.
- [ ] Commit: `feat(brand-studio): port PersonaDetailView refactored to form-runtime (Sprint 2.8)`

---

## 6. What Sprint 4 (copilot refactor) absorbs — documented here for continuity

Sprint 4's scope grows: original plan was "collapse copilot state + delete dead UI". With the pivot, Sprint 4 ALSO delivers five copilot tools that replace what used to be standalone actions in brand/. These are NEW code designed from the intent of the purged flows, not ports.

Copilot tool contracts (backend side under `backend/src/modules/copilot/application/tools/` + frontend chat UI under `features/copilot/components/`):

| Tool | Replaces | Inputs | Output | Absorbed flows |
|---|---|---|---|---|
| `extract_brand_from_url` | SmartFillDialog (mode=initial) + OnboardingWizard.StepWebsite + BrandVisualsWizard | url: string | BrandSettings diff | "URL as source" |
| `extract_brand_from_docs` | SmartFillDialog (mode=update) + OnboardingWizard.StepDocuments | files: File[] | BrandSettings diff | "docs as source" |
| `analyze_voice_style` | VoiceCloneAction | text: string | { voice_tone: string } | "infer voice from sample" |
| `extract_visuals_from_url` | BrandVisualsWizard | url: string | BrandVisuals diff | "extract colors/fonts only" |
| `clone_personality_from_chat` | PersonalityClone | conversation: Msg[] | PersonalityProfile diff | "infer personality from real chats" |

Each tool:
1. The user invokes via natural chat or a button in SessionHeader (eg "Extrae mi marca desde mi web").
2. The copilot prompts for missing inputs (URL, docs, conversation).
3. Tool runs on backend; result arrives as a structured diff.
4. Copilot previews the diff in chat (each field as a "suggested change" chip).
5. User confirms per-chip; copilot calls `bridge.patchField(path, value)` for each approved change.

**NOT in Sprint 2.** Kept here so the team remembers where these flows went.

---

## 7. Scope Creep log (MUST STAY EMPTY)

Anything that arises mid-sprint and is not explicitly in §1.1 goes HERE with status `deferred`, also appended to `docs/mejoras-proceso/to-do.md`. Never absorbed silently.

_(empty — good)_

---

## 8. Exit criteria for Sprint 2

- [ ] Sprint 2.0 all four commits landed, user-approved.
- [ ] Sprint 2.1–2.7 all 7 action ports landed; each with story + tests.
- [ ] Sprint 2.8 PersonaDetailView refactor landed.
- [ ] `features/brand-studio/actions/placeholders.tsx` — DELETED.
- [ ] `registry.ts#PLACEHOLDERS` map has 7 real entries + notes for the 5 copilot-absorbed keys (or key removed if no schema references it after purge).
- [ ] Redirect pages deleted (`tono-y-voz`, `creativos`, `assets`).
- [ ] `tsc --noEmit` → 0 errors.
- [ ] `eslint src/` → 0 errors; warnings ≤ baseline.
- [ ] `vitest run` → 1247 + ~40 new tests green.
- [ ] `npx next build` succeeds.
- [ ] `npm run build-storybook` succeeds.
- [ ] Arch fitness → 10/10.
- [ ] User checkpoints signed off: Sprint-2.0 + CP-2A..CP-2E.
- [ ] Zero §7 entries.
- [ ] All commits pushed to origin/development.
- [ ] PLAN.md Status table updated.

---

## 9. Rollback

Every sub-commit is independent. `git revert <hash>` isolates any one action port, any one foundation commit, or the PersonaDetailView refactor without affecting the others.

---

## 10. Resume primer

> Sigo el refactor brand studio, Sprint 2. Lee:
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/PLAN.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/SPRINT-2-PLAN.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/FLOW-SPEC.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/DECISIONS.md`
> - memoria `project_brand_studio_refactor.md`
> Ejecuta pre-flight §0 del PLAN, dime qué etapa (2.0a/b/c/d, 2.1..2.8) fue la última en commit, y esperá mi OK antes de tocar nada.
