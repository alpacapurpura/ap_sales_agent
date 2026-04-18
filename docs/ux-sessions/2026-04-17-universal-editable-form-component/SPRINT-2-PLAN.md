# Sprint 2 — Port 13 Rich Actions · Execution Plan

**Session folder:** `docs/ux-sessions/2026-04-17-universal-editable-form-component/`
**Depends on:** Sprint 1 COMPLETE (commit `56b6cfbf` pushed to origin/development).
**Goal:** Replace every Sprint-1 placeholder in `features/brand-studio/actions/registry.ts` with the real ported component. At end of Sprint 2, no placeholder entry remains; schemas render real rich actions.

Old `features/brand/` stays in the tree. App Router still serves old pages (Sprint 3 flips). Every action commit is ship-able and revert-able independently.

---

## 1. Learnings from Sprint 1 — MUST apply in every Sprint 2 commit

These are structural lessons that avoided or surfaced tech debt during Sprint 1. Internalize them before writing any new code.

### 1.1 Architecture & design

| # | Lesson | Applied in Sprint 2 |
|---|---|---|
| L1 | **`Record<string, unknown>` is too strict for typed domain values.** Use `object` + explicit cast at the runtime boundary. | Action components receive `value: TValue` where `TValue` extends `object` (or `unknown` when the value is primitive). Never force feature types into `Record<string, unknown>`. |
| L2 | **Import cycles on recursive components need prop injection, not direct imports.** `FieldRenderer ↔ ArrayInput` cycle was fixed by injecting `renderField`. | If an action needs to render nested form-runtime primitives, inject a renderer prop; do not import `FieldRenderer` directly. |
| L3 | **Custom components from registries → use `createElement`.** `<Component {...props} />` triggers `@eslint-react/no-nested-component-definitions`. `createElement(component, props)` is clearer intent and lint-clean. | CustomInput already does this. Any new registry-style lookup follows the same pattern. |
| L4 | **React ref access during render is flagged.** Bridge readers (`valuesRef.current` inside closures invoked by copilot) need a localized `eslint-disable react-hooks/refs` with a justification comment. | Reuse the existing bridge. Do NOT introduce new refs-in-render patterns. If an action needs latest state, use a state setter or lift the state. |
| L5 | **`set-state-in-effect` cascades.** When a component needs "fire an effect only when X becomes true", encapsulate the state in an inner component whose mount is keyed on that condition. | See `AutosaveBanner.SavedBanner`. Actions with timed UI (dialogs, toasts, transitions) use the same pattern. |
| L6 | **Don't `import "@/features/brand-studio/actions/registry"` from N places.** Centralize bootstrap in the module every consumer already imports (`schemas/index.ts`). | Never add a side-effect import to an action file or a page. |

### 1.2 Testing discipline

| # | Lesson | Applied in Sprint 2 |
|---|---|---|
| L7 | **`fireEvent.change(el, { target: { value } })`, not `el.dispatchEvent(new Event("change"))`.** Synthetic events don't propagate via the raw DOM event. | Every action test that simulates typing uses `fireEvent` or `userEvent`. |
| L8 | **Happy-dom does not map `textarea.rows` to a number.** Assert via `.getAttribute("rows")` which is a string. | Tests that check numeric-origin DOM attributes assert against the string form. |
| L9 | **Fake timers require `vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] })`, and `await flushMicrotasks()` after `advanceTimersByTime`.** | Reuse the helper in `FormRuntimeProvider.test.tsx`. Any action with debounce replicates this setup. |
| L10 | **Mock the registry in action tests with `clearRegistry()` in `beforeEach`.** Prevents cross-test leakage — the registry is global. | Copy the pattern from `inputs.test.tsx#CustomInput`. |

### 1.3 Lint & quality-gate hygiene

| # | Lesson | Applied in Sprint 2 |
|---|---|---|
| L11 | **Run `eslint --fix` after each file batch, BEFORE writing tests.** Prettier auto-fixes save a commit cycle; new files should land clean. | Every action port runs eslint --fix once before its tests are written. |
| L12 | **Cognitive complexity ≤ 15.** Split per-type branch dispatch into dedicated helper functions when `if / switch` chains grow. | Pre-factor. See `FieldList.preview` split (isEmpty → previewArrayCount → preview). |
| L13 | **0 ESLint errors before commit.** Warnings are tolerated only if they match the existing baseline; new files target 0 warnings as aspirational, 0 errors as gate. | Every commit runs `./node_modules/.bin/eslint src/features/brand-studio/actions/ --cache` and must show 0 errors. |
| L14 | **Arch fitness tests — any new folder under `features/brand-studio/` that is non-canonical must already be in the `KNOWN_NONSTANDARD` allowlist.** | No new non-canonical folders are introduced in Sprint 2; actions live in the already-allowlisted `actions/` directory. |

### 1.4 Data-contract preservation (NO DATA LOSS)

| # | Lesson | Applied in Sprint 2 |
|---|---|---|
| L15 | **When porting a component, port imports 1:1 first; only then refactor.** Sprint 1 porting `use-buyer-persona` was clean BECAUSE we preserved the contract first and fixed autosave later as an explicit debt entry. | Step 1 of every action port: copy file, rewire imports, tests green. Step 2: refactor to runtime contract. Both steps in the same commit. |
| L16 | **React Query keys are immutable across the migration.** If an action triggers a mutation, it invalidates the same key the old code used. Changing keys = invisibly invalidating every other consumer's cache. | Each action's mutation copy-pastes the key from the original brand/ file. |
| L17 | **`useAutoSave` (lib/form-runtime/hooks) is the canonical autosave.** Never write per-component debounce state. | Actions with "save on change" use `useAutoSave`. |

### 1.5 SSR & Next.js

| # | Lesson | Applied in Sprint 2 |
|---|---|---|
| L18 | **Window access must be guarded for SSR.** `UniversalEditableSection`'s mobile detection uses `useEffect` (client-only). `"use client"` directive alone does NOT prevent the module body from running at build time. | Any action that touches `window`, `localStorage`, `navigator`, `document` lives inside a `useEffect` or uses a `useIsClient`-style guard. |

---

## 2. Pre-flight per-action checklist (blocking)

**Before writing any code for an action, paste this checklist into the commit branch task and tick every box before closing the commit. If you cannot tick a box, the action is NOT done.**

```
Action: <name>
Source (old): features/brand/<path>/<file>.tsx
Target (new): features/brand-studio/actions/<Name>Action.tsx
Registry key: <kebab-key>

Contract compliance
- [ ] Signature matches ActionComponent<TValue>: { value, onChange, props? }
- [ ] TValue is the correct domain type (not unknown)
- [ ] onChange writes back values the surrounding schema field expects at `field.path`
- [ ] For sub-entity actions (avatar), onChange is a no-op; component drives its own API

Imports rewired
- [ ] @/features/brand/api        → @/features/brand-studio/api
- [ ] @/features/brand/hooks      → @/features/brand-studio/hooks
- [ ] @/features/brand/types      → @/features/brand-studio/types
- [ ] @/features/copilot/WithCopilot → REMOVED (uses EditableField context now)
- [ ] @/features/copilot/FocusModeButton → REMOVED
- [ ] @/features/copilot/InterviewModeButton → REMOVED
- [ ] No circular imports introduced (run `npx madge --circular src/components/form-runtime/ src/features/brand-studio/`)

React quality
- [ ] No inline JSX callback props in a map() — hoist with useCallback
- [ ] No setState inside useEffect body unless guarded by a condition that cannot be re-entered
- [ ] No ref reads in render; refs invoked only from handlers/effects
- [ ] Component returns stable references (useMemo/useCallback for large prop objects)

Tests
- [ ] Colocated test file: actions/__tests__/<Name>Action.test.tsx
- [ ] beforeEach(clearRegistry) when the test registers actions
- [ ] fireEvent/userEvent — no raw dispatchEvent
- [ ] Debounce assertions use vi.useFakeTimers + flushMicrotasks helper
- [ ] Action-specific edge cases covered (upload failure, empty input, invalid URL, etc.)

Bootstrap
- [ ] placeholders.tsx: entry REMOVED (not just deprecated)
- [ ] registry.ts: PLACEHOLDERS map entry points at real component
- [ ] BRAND_STUDIO_ACTION_KEYS unchanged (key string constant)

Quality gates
- [ ] cd frontend && npx tsc --noEmit  → 0 errors
- [ ] cd frontend && ./node_modules/.bin/eslint <new-file> --cache  → 0 errors
- [ ] cd frontend && npx vitest run <new-test>  → all green
- [ ] cd frontend && npx vitest run src/__tests__/architecture/  → 10/10 green
- [ ] Full suite still passes: cd frontend && npx vitest run  → 1247 + new tests, 0 failures

Commit
- [ ] Conventional Commits: `feat(brand-studio): port <ActionName> as action (Sprint 2.N)`
- [ ] Body lists which placeholder is replaced and what tests cover
- [ ] Tests in same commit as the code (TDD — red then green in one commit)
- [ ] User checkpoint triggered for CP-marked actions

Debt log
- [ ] If anything non-obvious had to be disabled or worked around, it lives in this commit's message OR an inline `// eslint-disable` with a justification. NEVER silently absorbed.
- [ ] Scope creep → SPRINT-2-PLAN.md §7 log ONLY, never the diff.
```

---

## 3. Action order (cheapest → heaviest, with user checkpoints)

The order concentrates the simple work up front so pattern mistakes are caught early, before the hard ones.

| # | Action | Key | Source file(s) | TValue type | Est. Claude-active | Checkpoint? |
|---|---|---|---|---|---|---|
| 2.1 | **SmartFillDialog** | `smart-fill` | `brand/components/smart-fill/SmartFillDialog.tsx` | `unknown` (imperative) | 20–30 min | no |
| 2.2 | **ImageGalleryPicker** | `image-gallery` | `brand/sections/team/image-gallery-picker.tsx` | `string` (url) | 20–30 min | no |
| 2.3 | **SingleImagePicker** | `single-image` | `brand/sections/visuals/single-image-picker.tsx` | `string` (url) | 20–30 min | no |
| 2.4 | **ThemeInjector** | `theme-injector` | `brand/sections/visuals/theme-injector.tsx` | `unknown` (imperative) | 15–25 min | no |
| 2.5 | **DimensionSliders** | `personality-dimensions` | `brand/sections/personality/dimension-sliders.tsx` | `PersonalityDimensions` | 25–40 min | no |
| 2.6 | **PresetCatalog** | `personality-presets` | `brand/sections/personality/preset-catalog.tsx` | `string` (preset key) | 20–30 min | no |
| 2.7 | **VoiceCloneAction** | `voice-clone` | `brand/sections/voice/voice-form.tsx` | `string` (voice_tone) | 30–45 min | ✅ CP-2A |
| 2.8 | **PersonalityClone** | `personality-clone` | `brand/sections/personality/clone-upload.tsx` | `PersonalityProfile` | 30–45 min | ✅ CP-2B |
| 2.9 | **BrandVisualsWizard** | `brand-visuals-wizard` | `brand/sections/visuals/brand-visuals-wizard.tsx` + step files | `BrandVisuals` | 45–75 min | ✅ CP-2C |
| 2.10 | **LogoKitAction** | `logo-kit` | `brand/sections/logos/logo-kit.tsx` | `BrandLogos` | 30–45 min | ✅ CP-2D |
| 2.11 | **AvatarAction** | `avatar` | `brand/sections/avatars/avatar-form.tsx` | `unknown` (sub-entity API) | 45–60 min | ✅ CP-2E |
| 2.12 | **LegalAction** | `legal` | `brand/components/legal/LegalManager.tsx` + `LegalForm.tsx` | `{ legal_name, tax_id, ... }` | 30–45 min | no |
| 2.13 | **OnboardingWizard** | `onboarding-wizard` | `brand/components/onboarding/OnboardingWizard.tsx` + 6 step files | `unknown` (multi-step) | 45–90 min | ✅ CP-2F |

**Checkpoints (CP-2A … CP-2F):** after the commit, user validates in a dev harness page (see §5) before Sprint 2 continues. The cheap actions (2.1–2.6, 2.12) batch without checkpoints.

---

## 4. Commit template (Conventional Commits)

```
feat(brand-studio): port <ActionName> as action (Sprint 2.N)

Replaces the <action-key> placeholder in features/brand-studio/actions/registry.ts
with the real ported component. The <ActionName> ships with:

- <key behaviour 1>
- <key behaviour 2>
- Ported tests: <test 1>, <test 2>, …

Imports rewired from @/features/brand/* to @/features/brand-studio/*.
Contract adapted to ActionComponent<TValue>: (value, onChange, props?).
<Any non-obvious decision>: <justification>.

Quality gates: tsc 0 errors · eslint 0 errors · <N> new tests pass · full
suite 1247+N green.

Sprint 2 / action N of 13.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## 5. Dev harness for checkpoints

Because App Router still serves old brand/ until Sprint 3, validating a new action visually requires a temporary harness. Decision:

- Add `features/brand-studio/actions/__tests__/harness.tsx` (not a page — a test-only fixture).
- **OR** for the six checkpointed actions, Claude runs the dev server and navigates to a schema whose rendered field embeds the new action — confirming the UI works via screenshot / description. No new route is added.

**Pick one before CP-2A fires.** Default: harness file, because it is deterministic and cheap.

---

## 6. Sprint 2 exit criteria

All of the following must be true to close Sprint 2:

- [ ] `features/brand-studio/actions/placeholders.tsx` has zero exports remaining (file deleted or reduced to an empty module with a deletion TODO logged to Sprint 5).
- [ ] `features/brand-studio/actions/registry.ts#PLACEHOLDERS` map references real components for all 13 keys.
- [ ] Every action has at least 3 tests covering: happy path, edge case, failure.
- [ ] `tsc --noEmit` → 0 errors.
- [ ] `eslint src/` → 0 errors (warnings ≤ baseline from Sprint 1).
- [ ] `vitest run` → baseline + ~40 new tests all green.
- [ ] Arch fitness → 10/10 green.
- [ ] PLAN.md Status table updated.
- [ ] All commits pushed to origin/development.
- [ ] User checkpoints signed off: CP-2A, CP-2B, CP-2C, CP-2D, CP-2E, CP-2F.
- [ ] No entries in §7 Scope Creep log.

---

## 7. Scope Creep log (MUST STAY EMPTY)

If during Sprint 2 anything arises that is not a direct port of a listed action (e.g., a new schema field, a new copilot capability, a new hook), it goes HERE with status `deferred` and is added to `docs/mejoras-proceso/to-do.md`. Never absorbed silently.

_(empty — good)_

---

## 8. Rollback

Every action port is its own commit touching:
- one new file in `features/brand-studio/actions/`
- one or two modifications in `actions/registry.ts`, `actions/placeholders.tsx`
- one new test file in `actions/__tests__/`
- optionally one new hook adapter in `features/brand-studio/hooks/`

A single `git revert <hash>` restores the placeholder for that one action only. The rest of Sprint 2 keeps working.

---

## 9. What dies on Sprint 2 close (previewing Sprint 5 deletions)

Not deleted in Sprint 2, but flagged as ready-for-deletion-in-Sprint-5 as their replacements land:

- `features/brand/sections/voice/voice-form.tsx` ← replaced by `VoiceCloneAction`
- `features/brand/sections/personality/{clone-upload,dimension-sliders,preset-catalog}.tsx`
- `features/brand/sections/visuals/{brand-visuals-wizard,theme-injector,single-image-picker}.tsx`
- `features/brand/sections/logos/logo-kit.tsx`
- `features/brand/sections/team/image-gallery-picker.tsx`
- `features/brand/sections/avatars/avatar-form.tsx`
- `features/brand/components/smart-fill/SmartFillDialog.tsx`
- `features/brand/components/onboarding/**`
- `features/brand/components/legal/{LegalForm,LegalManager}.tsx`

Sprint 3 flips the App Router to use brand-studio pages; Sprint 4 refactors copilot; Sprint 5 deletes everything above.

---

## 10. Resume primer (for fresh conversations mid-Sprint 2)

> Sigo el refactor brand studio, Sprint 2. Lee:
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/PLAN.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/SPRINT-2-PLAN.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/FLOW-SPEC.md`
> - `docs/ux-sessions/2026-04-17-universal-editable-form-component/DECISIONS.md`
> - memoria `project_brand_studio_refactor.md`
> Ejecuta pre-flight §0 del PLAN, dime qué acción fue la última en ser porteada (ver git log + registry.ts) y cuál sigue en §3, y esperá mi OK antes de tocar nada.
