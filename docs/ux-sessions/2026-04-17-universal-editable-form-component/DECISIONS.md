# DECISIONS — Session Log

Running log of architectural decisions for the universal editable form component
migration. Every decision has: what was decided, why, and when.

**Status of this document as of 2026-04-17 end-of-session:** All blocking
decisions locked. Ready for execution in a new conversation with clean context.

---

## 2026-04-17 · Session initiated

### D1 · Approach: foundation-first strangler fig
**Decision:** Build `form-runtime/` as shared infrastructure first, then migrate `features/brand/` → `features/brand-studio/` as the first consumer. Do not clean up brand in place.
**Why:** Brand is one of 5 surfaces (brand, offer, buyer_persona, landing config, sales agent config) with the same anti-pattern. Cleaning up brand without the shared primitive leaves the same debt in the other 4. External-consultant view: the right abstraction level is above any single feature.
**Alternatives rejected:**
- Bomba (delete everything, rebuild): high risk, brand broken for days, same end result, shared primitive still needed.
- Quirúrgica in-place: no clean architectural boundary, brand-only fix, shared primitive still needed.
- Strangler fig at brand level with component inside `brand-studio/`: when migrating offer next, the component would have to be extracted again.

### D2 · UI pattern: variant C (list + detail pane)
**Decision:** Adopt variant C (Linear-style row+detail pane) as the default layout of `UniversalEditableSection`.
**Why:** User selected after reviewing 3 HTML mockups. Scales to many fields, minimal navigation change, preview disappears naturally (the row is the preview).
**Alternatives rejected:**
- Variant A (Notion click-to-edit): 1 click extra per edit.
- Variant B (Airtable always-editable + drawer): visual density too high.

### D3 · Folder name: `brand-studio/` (not `brand-v2/`)
**Decision:** New feature folder is `features/brand-studio/`.
**Why:** Matches product language (Brand Studio is the product name of the feature). No "v2" suffix polluting long-term naming. Final state: no rename needed.

### D4 · Focus mode UI: collapse into `copilotSession`
**Decision:** Remove `FocusBar`, `FocusModeButton`, `InterviewModeButton`, `CopilotPreviewPane`, `interview-preview-registry`, `WithCopilot` as distinct components. Collapse `focusEntity` + `focusSnapshot` + `interviewProgress` + `previewData` in the copilot store into a single `session` object + `focusedField`. Progress, undo-all, and "exit session" fuse into a `SessionHeader` chip in the page header.
**Why:** Today's three states (normal / focus / interview) are implementation details the user shouldn't see. With the new architecture, copilot always knows the section and focused field through the form-runtime bridge, so there is no need for a distinct UI state.
**What remains:** copilot chat, copilot input, copilot sidebar, backend persisters, backend interview configs, tools registry, schema introspection. None of those change.

### D5 · Preview pane dies entirely — no "pending changes" UI
**Decision:** Copilot changes apply live to the form. No preview-then-apply flow. Undo is session-level (single button that reverts all field changes since session start).
**Why:** Preview pane exists today only because copilot can't see the form directly (WithCopilot only runs when EditSheet is open). With the new runtime, copilot has continuous access via the bridge, so previews are redundant complexity.

### D6 · Rich action components are ported 1:1 as pluggable actions
**Decision:** ~8–10 components (`VoiceForm`, `CloneUpload`, `BrandVisualsWizard`, `ImageGalleryPicker`, `SingleImagePicker`, `DimensionSliders`, `PresetCatalog`, `SmartFillDialog`, `OnboardingWizard`) are ported to `features/brand-studio/actions/`. They register with the action registry at feature init. Schema entries of type `"custom"` reference them by action key.
**Why:** These encapsulate rich interactions (file upload, multi-step wizards, sliders) that do not fit a generic `EditableField`. They should remain as first-class components, just behind a thin registration layer.

### D7 · Schemas live in feature, runtime lives in shared infra
**Decision:**
- `lib/form-runtime/` — non-React: schema types, parser, action registry, copilot bridge.
- `components/form-runtime/` — React: UniversalEditableSection, EditableField, inputs.
- `features/brand-studio/schemas/` — domain schemas (brand-specific).
- `features/brand-studio/actions/` — domain-specific rich actions.
**Why:** Schemas are feature territory (they describe domain fields). The runtime is infrastructure (reusable by every feature). Separation keeps FSD boundaries intact.

### D8 · TDD enforced + commits ship-able
**Decision:** Every code change commits with its test (Red → Green → commit). Every commit leaves brand studio functional. Scope creep goes to a log, not into the diff.
**Why:** User expressed fear of Claude dropping work mid-refactor. Structural safeguards (artifacts over memory, tests as gate, checkpoints) reduce the risk to: one section per failure, not the whole migration.

### D9 · E2E Playwright excluded from migration gating
**Decision:** E2E tests are not required to pass during this migration. Existing E2E tests may break and will be addressed as a separate task after migration.
**Why:** User explicitly scoped them out. Reason: E2E infrastructure has unresolved stability issues (see existing memory `project_e2e_playwright_fixes.md`). Including them would add noise to an already sizable refactor.

### D10 · Pace is measured in Claude-active hours, not weeks
**Decision:** PLAN.md time estimates use Claude-active hours. Calendar time is driven by user checkpoint turnaround, not by Claude throughput.
**Why:** User asked to correct the earlier "weeks" framing. An LLM works at different cadence than a human team; the bottleneck is human validation, not code production.

---

## 2026-04-17 · Architect-role decisions (locked for execution)

User asked Claude to take an "architect consultant" role, use expert criteria to
resolve all remaining open questions, and leave the spec ready for a fresh
conversation to execute.

### D11 · Form-runtime location (resolves Q1)
**Decision:** Split across two folders.
- `lib/form-runtime/` — non-React: `schema/`, `actions/`, `copilot/`.
- `components/form-runtime/` — React: `UniversalEditableSection`, `EditableField`, `inputs/`, `SessionHeader`.
**Why:** Respects FSD boundaries as-is. No new element types needed in the arch test. `lib/` already has mixed utilities and logic; `components/` is the natural home for JSX. Alternative (`features/_form-runtime/` meta-feature) would require an FSD exception comparable to copilot's, adding rule complexity for no real benefit.

### D12 · Default save mode (resolves Q2)
**Decision:** `autosave-with-banner` as the runtime default. Per-field debounce 800ms. Banner at top of the detail pane shows three states: "Guardando…", "Guardado ✓" (fades after 2s), "Error al guardar — reintentar". Session-level undo available via the `SessionHeader` button (reverts all field changes in the current session).
**Why:** Unifies user-driven and copilot-driven flows. Copilot (especially via WhatsApp in the future) has no human to click "Save" — autosave is mandatory for headless operation. Banner preserves the safety signal that explicit save provides. Session-level undo replaces the defensive preview pane.
**Per-field override:** Individual fields may opt out with `saveMode: "explicit"` in the schema if the field is heavy (file upload, long text) and autosave would thrash the API.
**API compatibility:** existing `updateIdentity(fullSectionObject)` hooks continue to work — the runtime composes the full patch internally before calling the consumer's `onSave`.

### D13 · Mobile behavior (resolves Q3)
**Decision:** Below 768px, the detail pane becomes a full-screen view with a back button in the top-left returning to the field list. List view occupies 100% width below 768px. The FieldList component collapses any parent navigation chrome.
**Why:** Native-app feel. Works naturally for nested items (team member sub-schema, testimonial sub-schema) where detail content can be long. Accordion alternative breaks down with `ArrayInput` rendering.

### D14 · Bridge naming (resolves Q4)
**Decision:** `FormRuntimeBridge`.
**Why:** Explicit and descriptive. `FormContext` conflicts with React's Context terminology (readers would assume it's just a Context object). `SessionBridge` is ambiguous (copilot session vs auth session).

### D15 · Port list (resolves Q5)
**Decision:** Port list in FLOW-SPEC §5.1 stands as-is, with two additions and one explicit exclusion:

**Added to port list:**
- `LegalManager` + `LegalForm` → `features/brand-studio/actions/LegalAction.tsx` (port as action; schema-ify in a later iteration if fields turn out to be simple).
- `components/empty-state/BrandEmptyState.tsx` → `features/brand-studio/components/BrandEmptyState.tsx` (runtime renders it when a section has no data yet).

**Explicit exclusion (scope-locked):**
- `features/brand/components/business-types/` (BusinessTypesSection, BusinessTypeOnboardingDialog, BusinessTypeSelector) stays as-is. It is a separate onboarding flow, not a form-runtime target. Out of scope §7.

### D16 · Scaffold-first execution (new organizing principle)
**Decision:** Sprint 1 builds the complete new architecture as a scaffold in-tree BEFORE any route is flipped. Concretely, Sprint 1 delivers:
- `lib/form-runtime/` complete (with tests).
- `components/form-runtime/` complete (with tests).
- `features/brand-studio/` with: api/hooks/types ported, **all 15 schemas written** (plain fields only — custom-action slots reference actions not yet ported but registered as "placeholder"), page files in place, **all pages still unused by the App Router** (old brand/ keeps serving the app).
- Arch tests updated to acknowledge `brand-studio` feature.

Sprints 2-5 then:
- Sprint 2 ports the 8-10 rich actions and wires them into their schema slots.
- Sprint 3 flips App Router pages in one commit to use brand-studio pages.
- Sprint 4 refactors copilot store + deletes copilot-pane dead components.
- Sprint 5 deletes `features/brand/` entirely.

**Why:** User's instinct — build the whole clean solution, then port atoms. Benefits over section-by-section:
1. Architectural review is complete after one sprint (user sees the final shape in the tree, not working app yet).
2. Schemas are quick to write (1-2 min each) and are the simple atoms. Getting all 15 done in Sprint 1 concentrates the easy work and exposes edge cases early.
3. Rich actions are the real risk; they get dedicated sprint with individual per-action checkpoints.
4. Route flip is one atomic commit — brand-studio either serves all pages or none.
5. Old `features/brand/` is deleted only after everything is live on new, minimizing partial-migration states.

### D17 · Arch test allowlist strategy
**Decision:** Add `brand-studio` to the canonical feature name allowlist in `frontend/src/__tests__/architecture/` **in Sprint 1, same commit as the scaffold**. Temporarily both `brand` and `brand-studio` exist; the ratchet pattern (allowlist can only shrink) is satisfied because we add then shrink (remove `brand` in Sprint 5).
**Why:** Avoids arch tests blocking the migration. Allowlist change is acknowledged in the commit message with a comment pointing to this decisions file.

### D18 · Memory updates after session close
**Decision:** After this session, update:
- `project_brand_studio_refactor.md` — reflects locked status, Sprint 0 complete.
- `MEMORY.md` entry already points to the refactor file.
Next session's pre-flight reads memory + PLAN.md + FLOW-SPEC.md + DECISIONS.md and needs nothing from chat history to start Sprint 1.

---

## Status: LOCKED FOR EXECUTION

All 18 decisions are final. Spec is self-contained. A new Claude conversation
armed with:

1. `docs/ux-sessions/2026-04-17-universal-editable-form-component/FLOW-SPEC.md`
2. `docs/ux-sessions/2026-04-17-universal-editable-form-component/PLAN.md`
3. `docs/ux-sessions/2026-04-17-universal-editable-form-component/DECISIONS.md`
4. `docs/ux-sessions/2026-04-17-universal-editable-form-component/schemas/identity.schema.example.ts`

…can execute Sprint 1 without referring to any chat history.
