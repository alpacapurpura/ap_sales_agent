# FLOW-SPEC — Universal Editable Form Runtime + Brand Studio Migration

**Session:** `docs/ux-sessions/2026-04-17-universal-editable-form-component/`
**Date:** 2026-04-17
**Scope:** Build a shared `form-runtime/` primitive. Migrate `features/brand/` → `features/brand-studio/` as first consumer. Collapse copilot focus/interview/preview into a single `copilotSession` concept.
**Approach:** Foundation-first strangler fig.
**Status:** Spec under review (no production code yet).

---

## 1. Motivation & Target Architecture

### 1.1 Problem

Today Nicolify reinvents the same "edit domain entity" pattern per feature. Each section ships three coupled components (`{X}Manager`, `{X}Form`, `{X}Preview`) plus a modal sheet. Copilot is bolted on via `WithCopilot` wrappers inside forms, meaning the copilot only "sees" a field while the modal is open. The preview pane in the copilot sidebar exists specifically to compensate for the disconnect.

Counts in `features/brand/` alone:
- `sections/` = 15 sections × 3 files = ~45 files
- `EditSheetManager.tsx` + `EDIT_MODE_META` config registry
- `views/{X}View.tsx` = 4 wrapper views
- `interview-preview-registry.ts` + `BrandPreviewSections.tsx` + `BrandPreviewSummary.tsx` (preview pane renderers for copilot)

The same pattern repeats (with local variations) in `features/offer-studio/` and `features/brand/components/interview/previews/`. Migrating only brand does not eliminate the architectural debt — the next feature inherits it.

### 1.2 Target

One shared primitive that:

1. Renders a section's fields from a declarative JSON schema.
2. Edits those fields in place (no preview/form duplication).
3. Exposes view and focused-field state to copilot through a single context.
4. Accepts rich custom actions (file upload, wizards, pickers) via a plugin registry.
5. Is backend-independent (consumer provides data hook + mutation).

Consumers:

- `features/brand-studio/` — first consumer (this spec).
- `features/offer-studio/` — second consumer (later, same approach, trivial cost).
- `features/buyer-persona-studio/` — third consumer (later).
- Future WhatsApp copilot integration — same schemas, headless usage.

### 1.3 Folder Layout After Migration

```
frontend/src/
├── lib/
│   └── form-runtime/                 ← NEW. Non-React logic.
│       ├── schema/
│       │   ├── types.ts              ← FieldSchema, SectionSchema, ResolverRegistry
│       │   ├── parser.ts             ← runtime validation of schemas
│       │   └── zod-bridge.ts         ← optional Zod derivation from schemas
│       ├── actions/
│       │   └── registry.ts           ← global action registry (name → Component)
│       └── copilot/
│           └── bridge.ts             ← imperative API for copilot store
│
├── components/
│   └── form-runtime/                 ← NEW. React components.
│       ├── UniversalEditableSection.tsx  ← top-level: list + detail pane layout
│       ├── EditableField.tsx             ← single-field wrapper (replaces WithCopilot)
│       ├── FieldRenderer.tsx             ← resolves type → input component
│       ├── FormRuntimeProvider.tsx       ← React Context with section state
│       ├── inputs/                       ← per-type input components
│       │   ├── TextInput.tsx
│       │   ├── TextareaInput.tsx
│       │   ├── EnumInput.tsx
│       │   ├── ArrayInput.tsx            ← list of items + row/detail layout
│       │   └── CustomInput.tsx           ← renders from action registry
│       └── SessionHeader.tsx             ← progress chip + "run interview" + undo
│
├── features/
│   ├── brand-studio/                 ← NEW. Replaces features/brand/.
│   │   ├── schemas/
│   │   │   ├── identity.schema.ts
│   │   │   ├── team.schema.ts
│   │   │   ├── voice.schema.ts
│   │   │   ├── ... (one per section)
│   │   │   └── index.ts              ← registry { sectionKey → schema }
│   │   ├── actions/
│   │   │   ├── VoiceCloneAction.tsx   ← ported from brand/sections/voice
│   │   │   ├── PersonalityClone.tsx
│   │   │   ├── BrandVisualsWizard.tsx
│   │   │   ├── ImageGalleryPicker.tsx
│   │   │   ├── DimensionSliders.tsx
│   │   │   ├── PresetCatalog.tsx
│   │   │   ├── SmartFillDialog.tsx
│   │   │   └── OnboardingWizard.tsx
│   │   ├── api/                      ← PORTED from brand/api/
│   │   ├── hooks/                    ← PORTED from brand/hooks/
│   │   ├── types/                    ← PORTED from brand/types/
│   │   └── pages/
│   │       ├── EsenciaPage.tsx       ← thin: loads schema + hook, passes to runtime
│   │       ├── EstrategiaPage.tsx
│   │       └── ... (one per route)
│   │
│   ├── brand/                        ← DELETED at end of migration
│   │
│   └── copilot/                      ← refactored in phase 4
│       └── (CopilotPreviewPane, interview-preview-registry, FocusBar → collapsed)
│
└── app/(main)/[tenantId]/(dashboard)/brand-studio/
    └── **/page.tsx                   ← each page imports from brand-studio/
```

---

## 2. Component Contracts

### 2.1 `SectionSchema` (the declarative core)

```ts
// lib/form-runtime/schema/types.ts

export type FieldType =
  | "text"
  | "textarea"
  | "enum"
  | "number"
  | "boolean"
  | "url"
  | "email"
  | "array"        // list of items (team members, testimonials)
  | "custom";      // delegates to action registry

export interface FieldSchema {
  /** Unique within section. Becomes `fieldId` in copilot store. */
  id: string;
  /** Human label shown in UI + copilot focus bar. */
  label: string;
  /** Field type — drives which input renders. */
  type: FieldType;
  /** Dot-path into the section data object. */
  path: string;
  /** Optional short help text. */
  hint?: string;
  /** Placeholder text. */
  placeholder?: string;
  /** Required for completeness calculation. */
  required?: boolean;
  /** For `enum` type. */
  options?: Array<{ value: string; label: string }>;
  /** For `textarea` type. */
  rows?: number;
  /** For `array` type: sub-schema for each item. */
  itemSchema?: Omit<SectionSchema, "key" | "title">;
  /** For `custom` type: key into action registry. */
  action?: string;
  /** Arbitrary props passed to custom action. */
  actionProps?: Record<string, unknown>;
}

export interface SectionSchema {
  /** Stable key, e.g. "brand.identity". Used by copilot and URL query. */
  key: string;
  /** Section title shown in page header. */
  title: string;
  /** Short description under title. */
  description?: string;
  /** Ordered list of fields. */
  fields: FieldSchema[];
}
```

### 2.2 `UniversalEditableSection` (the runtime entry point)

```tsx
// components/form-runtime/UniversalEditableSection.tsx

interface Props<TValues> {
  schema: SectionSchema;
  values: TValues;
  /** Called when a field is saved. Runtime handles dirty tracking. */
  onSave: (patch: Partial<TValues>) => Promise<void>;
  /** Optional loading state from consumer. */
  isLoading?: boolean;
  /** Optional save mode. Default: "explicit" (button). */
  saveMode?: "explicit" | "autosave" | "autosave-with-banner";
}

export function UniversalEditableSection<T>(props: Props<T>): JSX.Element;
```

Internal responsibilities:
- Renders variant C layout (list left + detail pane right) — locked in from the prototype review.
- Tracks dirty state per field.
- Provides `FormRuntimeContext` to children.
- Registers section metadata in copilot store on mount; clears on unmount.

### 2.3 `EditableField` (replaces `WithCopilot`)

```tsx
interface Props {
  field: FieldSchema;
  value: unknown;
  onChange: (newValue: unknown) => void;
  onFocus?: () => void;
  onBlur?: () => void;
}

export function EditableField(props: Props): JSX.Element;
```

- Reads from `FormRuntimeContext`.
- Registers the field in context on mount (replaces per-element DOM data attributes).
- Dispatches focus state to copilot via context → store.
- Receives AI-driven updates via context → store subscription (not window events).

### 2.4 `ActionRegistry` (plug-in point for rich components)

```ts
// lib/form-runtime/actions/registry.ts

type ActionComponent = React.ComponentType<{
  value: unknown;
  onChange: (v: unknown) => void;
  props?: Record<string, unknown>;
}>;

export const actionRegistry = new Map<string, ActionComponent>();

export function registerAction(key: string, component: ActionComponent): void;
export function getAction(key: string): ActionComponent | undefined;
```

Consumer registers its actions once in its `index.ts`:

```ts
// features/brand-studio/actions/index.ts
registerAction("voice-clone", VoiceCloneAction);
registerAction("personality-clone", PersonalityClone);
// ...
```

Schema entry uses it:

```ts
{ id: "voice_tone_clone", type: "custom", action: "voice-clone", label: "Clonación de estilo", path: "identity.voice_tone" }
```

---

## 3. Copilot Integration — The Single Bridge

### 3.1 What dies

- `copilot:field-update` window events (replaced by direct context ops).
- `copilot:collect-values` window events (context exposes snapshot via hook).
- `CopilotPreviewPane.tsx` (no preview state — edits apply live).
- `interview-preview-registry.ts` (no preview renderers per domain).
- `BrandPreviewSections.tsx`, `BrandPreviewSummary.tsx`, `PersonaPreviewSections.tsx`, `PersonaPreviewSummary.tsx`, `OfferPreviewSections.tsx`, `OfferPreviewSummary.tsx` (all preview renderers).
- `WithCopilot.tsx` (replaced by `EditableField`).
- `FocusBar.tsx` as a separate component (merges into `SessionHeader`).
- Distinction in copilot store between `focusEntity`, `interviewProgress`, `previewData` (collapsed — see 3.3).

### 3.2 What stays (unchanged)

- `CopilotChat.tsx`, `CopilotInput.tsx`, `CopilotSidebar.tsx` (the chat UI itself).
- Backend: `copilot/infrastructure/persisters/*` (brand, buyer_persona, offer).
- Backend: `copilot/domain/interview_configs/*` (brand_config, buyer_persona_config, offer_config).
- Backend: `copilot/application/tools/registry.py` (tool registry per route).
- Copilot's schema introspection (`copilot/domain/schema_introspection.py`).

### 3.3 What collapses — the `copilotSession` state

Before:
```ts
interface CopilotStore {
  focusEntity: { domain, entityId, label } | null;
  focusSnapshot: object | null;          // initial values for undo
  interviewProgress: { totalBlocks, blocksCompleted, currentBlock } | null;
  previewData: Record<string, unknown> | null;  // pending changes from copilot
  selectedFields: Array<{ fieldId, fieldLabel, fieldValue }>;
  // ...
}
```

After:
```ts
interface CopilotStore {
  /** Active "run" — either user-driven free edit or copilot-guided procedure. */
  session: {
    sectionKey: string;                  // e.g. "brand.identity"
    entityId: string | null;
    procedure: "free" | "interview";
    progress?: { total: number; completed: string[]; current?: string };
    startedAt: Date;
    snapshot: Record<string, unknown>;   // for session-level undo
  } | null;
  /** Currently focused field in the active section. */
  focusedField: { id: string; label: string; path: string } | null;
  /** Selected for multi-field context. Stays. */
  selectedFields: Array<{ id: string; label: string; value: unknown }>;
}
```

Transitions:
- User opens `/brand-studio/esencia` → `session` = `{ sectionKey: "brand.identity", procedure: "free", ... }` auto-starts.
- User clicks "Entrevista guiada" in `SessionHeader` → `session.procedure` flips to `"interview"`, copilot tool picks first empty required field, drives conversation.
- Field click in UI → `focusedField` updates.
- Copilot patches field via context bridge → EditableField re-renders with highlight.
- User navigates away → `session = null` + snapshot cleared.

### 3.4 Single bridge API (how copilot mutates the form)

```ts
// lib/form-runtime/copilot/bridge.ts
export interface FormRuntimeBridge {
  /** Read the active section snapshot. */
  getSnapshot(): { sectionKey: string; values: Record<string, unknown>; schema: SectionSchema } | null;
  /** Patch a field. Returns updated value after normalization. */
  patchField(fieldPath: string, newValue: unknown): Promise<void>;
  /** Set focus on a field (programmatic). */
  focusField(fieldId: string): void;
  /** Subscribe to changes. */
  subscribe(listener: (snapshot: ReturnType<typeof getSnapshot>) => void): () => void;
}
```

One instance per mounted section. Copilot tools call this bridge instead of dispatching events. Cleaner, testable, no event-timing bugs.

---

## 4. Data Flow Per Section

```
┌────────────────────────────────────────────────────────────────┐
│ Page: /brand-studio/esencia                                    │
│                                                                │
│ const { settings, updateIdentity } = useBrandSettings();       │
│                                                                │
│ <UniversalEditableSection                                      │
│    schema={identitySchema}                                     │
│    values={settings?.identity}                                 │
│    onSave={updateIdentity} />                                  │
└────────────────────────────────────────────────────────────────┘
           │ provides schema + values + onSave
           ▼
┌────────────────────────────────────────────────────────────────┐
│ FormRuntimeProvider                                            │
│  ├── registers section in copilot store                        │
│  ├── renders <SessionHeader/> (chip + progress + actions)      │
│  ├── renders <FieldList/> (left pane, compact rows)            │
│  └── renders <FieldDetail/> (right pane, active field edit)    │
└────────────────────────────────────────────────────────────────┘
           │ each field rendered via
           ▼
┌────────────────────────────────────────────────────────────────┐
│ <EditableField field={schema.fields[i]} value onChange />      │
│  ├── FieldRenderer picks input by field.type                   │
│  ├── onFocus → context.setFocusedField → copilot store         │
│  └── onChange → context.patchField → provider.onSave           │
└────────────────────────────────────────────────────────────────┘
           │ copilot side (read-only from copilot's POV):
           ▼
┌────────────────────────────────────────────────────────────────┐
│ Copilot subscribes to FormRuntimeBridge                        │
│  ├── knows sectionKey (e.g. "brand.identity")                  │
│  ├── knows focusedField (for chat framing)                     │
│  ├── knows values (for tool reasoning)                         │
│  └── mutates via bridge.patchField(path, newValue)             │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Migration Inventory — `features/brand/`

### 5.1 Files to DELETE (no port)

All files in the following folders are disposable scaffolding — the schema + runtime replaces them:

```
features/brand/sections/
├── authority/
│   ├── authority-preview.tsx          DELETE
│   ├── authority-list.tsx             DELETE (replaced by ArrayInput)
│   ├── authority-item-form.tsx        DELETE (replaced by sub-schema detail pane)
│   └── authority-manager.tsx          DELETE
├── avatars/
│   ├── avatars-preview.tsx            DELETE
│   └── avatar-form.tsx                PORT as action (complex: creates sub-entity via API)
├── communication-assets/
│   ├── assets-preview.tsx             DELETE
│   ├── concept-form.tsx               DELETE
│   ├── asset-item-form.tsx            DELETE
│   └── assets-manager.tsx             DELETE
├── contact/ (all 3)                   DELETE
├── differentiation/
│   └── differentiation-preview.tsx    DELETE
├── gallery/
│   └── gallery-manager.tsx            PORT as action (image gallery picker)
├── identity/ (all 3)                  DELETE
├── logos/
│   ├── logo-kit.tsx                   PORT as action (complex logo editor)
│   ├── logo-kit-manager.tsx           DELETE
│   └── logo-kit-preview.tsx           DELETE
├── market/
│   └── market-preview.tsx             DELETE
├── methodology/ (all 3)               DELETE
├── narrative/ (all 3)                 DELETE
├── personality/
│   ├── dimension-sliders.tsx          PORT as action
│   ├── clone-upload.tsx               PORT as action
│   ├── preset-catalog.tsx             PORT as action
│   ├── personality-section.tsx        DELETE
│   ├── personality-manager.tsx        DELETE
│   └── personality-preview.tsx        DELETE
├── positioning/ (manager, form, preview, rtb-item-form, values-essence-*)  DELETE all preview/manager; values-essence RTB list via schema array
├── story/ (all 3)                     DELETE
├── strategy/ (all 2)                  DELETE
├── team/
│   ├── team-manager.tsx               DELETE
│   ├── team-list.tsx                  DELETE (replaced by ArrayInput)
│   ├── team-preview.tsx               DELETE
│   ├── team-member-form.tsx           DELETE (replaced by sub-schema detail pane)
│   └── image-gallery-picker.tsx       PORT as action
├── testimonials/ (all 4)              DELETE (same array pattern)
├── visuals/
│   ├── brand-visuals-wizard.tsx       PORT as action
│   ├── theme-injector.tsx             PORT as action
│   ├── single-image-picker.tsx        PORT as action
│   ├── visuals-preview.tsx            DELETE
│   ├── visuals-form.tsx               DELETE
│   └── visuals-manager.tsx            DELETE
└── voice/
    ├── voice-form.tsx                 PORT as action (VoiceCloneAction)
    ├── voice-manager.tsx              DELETE
    └── voice-preview.tsx              DELETE

features/brand/components/
├── forms/EditSheetManager.tsx         DELETE
├── interview/BrandPreviewSections.tsx DELETE
├── interview/BrandPreviewSummary.tsx  DELETE
├── interview/previews/*               DELETE (all preview renderers)
├── layout/BrandSectionShell.tsx       KEEP as reference; runtime may or may not reuse NavRail
├── layout/SectionHeader.tsx           KEEP as reference
├── navigation/SectionNavRail.tsx      KEEP — useful as brand-studio layout
├── views/EsenciaView.tsx              DELETE (page uses runtime directly)
├── views/EstrategiaView.tsx           DELETE
├── views/IdentidadCreativaView.tsx    DELETE
├── views/PublicoView.tsx              DELETE
├── views/PersonaDetailView.tsx        DELETE
├── views/AvatarEditView.tsx           DELETE
├── onboarding/*                       PORT as action (OnboardingWizard)
├── smart-fill/SmartFillDialog.tsx     PORT as action
├── legal/*                            PORT if still in use
├── empty-state/BrandEmptyState.tsx    PORT as runtime empty state
├── tabs/BrandStudioTabs.tsx           KEEP (tab navigation, not section UI)
├── business-types/*                   KEEP — separate flow, not form-runtime territory

features/brand/config/sections.ts (EDIT_MODE_META)  DELETE
features/brand/types/edit-mode.ts                   DELETE
```

### 5.2 Files to PORT (copy + adapt)

```
features/brand/api/                  → features/brand-studio/api/         (rename imports)
features/brand/hooks/                → features/brand-studio/hooks/       (rename imports)
features/brand/types/ (minus edit-mode) → features/brand-studio/types/
features/brand/store/ (if any)       → features/brand-studio/store/
```

8–10 rich action components ported to `features/brand-studio/actions/` (see 5.1 PORT lines).

### 5.3 Files NEW

- 15 schemas in `features/brand-studio/schemas/`
- 1 schema index (`schemas/index.ts`)
- ~7 page files in `features/brand-studio/pages/` (matching the current routes)
- Updated `app/(main)/[tenantId]/(dashboard)/brand-studio/**/page.tsx` (1-line imports)

---

## 6. Tests Policy

(E2E Playwright removed from this migration per user decision. Smoke tests during feature development only — not gating migration steps.)

### 6.1 Frontend tests

| Layer | Tool | Coverage requirement |
|---|---|---|
| Schema parsing + validation | Vitest | 100% for parser + type guards |
| `EditableField` render + focus + change | Vitest + @testing-library | Each input type covered |
| `UniversalEditableSection` with mock schema + values | Vitest + @testing-library | Render, dirty tracking, save flow |
| `FormRuntimeBridge` contract | Vitest | All methods + subscription |
| Per-section schemas (brand-studio) | Vitest | One test per schema asserting shape |
| Custom actions ported | Vitest | Existing tests carry over with renamed imports |

Existing tests for components being deleted → deleted in the same commit as the component.

### 6.2 Architecture fitness tests (must keep passing)

- `test_component_naming` — new components PascalCase ✓
- `test_file_naming` — non-components kebab-case ✓
- `test_folder_naming` — folders kebab-case ✓
- `test_hook_location` — hooks only in `hooks/` or `api/` ✓
- `test_no_default_exports` — no default exports in features ✓
- `test_feature_structure` — `brand-studio/` must be added to canonical names allowlist
- `test_api_location` — `fetchClient` only in `api/` dirs ✓
- `test_no_duplicate_names` — may temporarily allow brand + brand-studio overlap via allowlist; shrinks as migration progresses

### 6.3 Backend tests

No backend changes in this refactor. Existing backend architecture tests must keep passing.

### 6.4 Quality gates (every commit must pass)

```bash
# frontend
cd frontend && npx tsc --noEmit
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/

# backend (even though unchanged, run after pulls)
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest -x -q --tb=short
```

---

## 7. Scope Locks — What This Refactor Does NOT Touch

Explicit exclusions so no scope creep slips in mid-migration:

1. **Backend**: no endpoint changes, no DTO changes, no persister changes, no Pydantic schema changes. Anything that requires backend edits is out of scope and goes into `docs/mejoras-proceso/to-do.md`.
2. **Sales agent, analytics, connections, growth, offer, buyer_persona features**: untouched. They continue working.
3. **Copilot backend (tools, interview configs, persisters)**: unchanged. Only frontend copilot store + sidebar components change.
4. **E2E Playwright tests**: dropped from gating. Existing ones stay in place but are not required to pass during migration. After migration is complete, a separate task updates them.
5. **App Router routes**: stay exactly as they are. `/brand-studio/esencia`, `/brand-studio/estrategia`, etc. Only the page content changes.
6. **Clerk auth, tenant isolation, multitenancy**: unchanged.
7. **Business-types flow** (`features/brand/components/business-types/`): separate flow, not form-runtime territory. Left alone.
8. **Legal tab** (`features/brand/components/legal/`): ported as a simple custom action if still in use, else deferred.
9. **Focus mode UI styling**: the collapse into a `SessionHeader` chip is the only UI change in the copilot panel for this refactor. Further visual polish is a separate task.

---

## 8. Success Criteria

Declared done when all of the following are true:

- [ ] `lib/form-runtime/` and `components/form-runtime/` exist, tests green.
- [ ] `features/brand-studio/` exists, all 15 sections migrated, tests green.
- [ ] `features/brand/` folder no longer exists (fully deleted).
- [ ] `CopilotPreviewPane.tsx`, `interview-preview-registry.ts`, `FocusBar.tsx` (old), `WithCopilot.tsx`, `EditSheetManager.tsx` no longer exist.
- [ ] Copilot store uses single `session` + `focusedField` concept.
- [ ] `/brand-studio/*` routes render correctly — user manually validates.
- [ ] All frontend arch fitness tests pass.
- [ ] No new ESLint errors.
- [ ] Vitest suite green.
- [ ] Backend tests unchanged and green.
- [ ] `docs/ux-sessions/2026-04-17-universal-editable-form-component/PLAN.md` — all checkboxes ticked.

---

## 9. Open Questions for User Review

Confirm the following before Sprint 1:

1. **Folder location** — agree with `lib/form-runtime/` (non-React logic) + `components/form-runtime/` (React components)? Alternative: everything under `features/form-runtime/` as a "meta-feature" with underscore prefix to mark it as infra.
2. **Save strategy default** — `"explicit"` save per card (current) vs `"autosave"` per field (Airtable) vs `"autosave-with-banner"` (pending-changes indicator)? Per-field variance allowed via schema, but the default matters.
3. **Variant C confirmed** — list left + detail pane right, as in the prototype. Mobile behavior: detail pane becomes full-screen modal on <768px, back button returns to list.
4. **Copilot bridge name** — `FormRuntimeBridge` vs `FormContext` vs `SessionBridge`. Minor but affects mental model.
5. **Acciones ricas** — agree with the list in section 5.1 (8-10 components ported)? Anything missing? Anything on the "port" list that should actually die?
