# DECISIONS — Session Log

Running log of architectural decisions for the universal editable form component
migration. Every decision has: what was decided, why, and when.

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

## Open — Awaiting User Decision

These questions block Sprint 1 start. User should confirm in next message.

### Q1 · `lib/form-runtime/` + `components/form-runtime/` vs `features/_form-runtime/`
Default proposal: split (lib for logic, components for React). Alternative: a single meta-feature under `features/_form-runtime/` with underscore prefix. Minor operational difference; splitting makes FSD boundaries cleaner.

### Q2 · Default save mode
Proposal: `"explicit"` (save button per field or section). Alternatives: autosave per field, autosave with pending-changes banner. Per-field override via schema remains possible regardless.

### Q3 · Variant C mobile behavior
Proposal: below 768px, detail pane becomes full-screen modal with a back button returning to the list. Alternative: below 768px, list transforms to accordion (variant A-like). Either works; need a call.

### Q4 · Naming of the copilot bridge
Proposal: `FormRuntimeBridge`. Alternatives: `FormContext`, `SessionBridge`. No consequence beyond mental model.

### Q5 · Actions to port — confirm the list
Proposed list in FLOW-SPEC §5.1. User should confirm no additions / removals needed.
