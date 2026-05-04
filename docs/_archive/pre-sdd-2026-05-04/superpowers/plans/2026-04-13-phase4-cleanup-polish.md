# Phase 4: Cleanup + Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all dead code from the unified copilot refactoring (Phases 0–3), deprecate replaced backend endpoints, and fix remaining ESLint issues.

**Architecture:** Phase 4 is pure cleanup — no new features. We delete ~20 legacy files, migrate 2 components from store aliases to canonical fields, convert 1 remaining interview page to the sidebar redirect pattern, remove SmartFill dialogs replaced by Focus Mode, and deprecate 2 backend endpoints.

**Tech Stack:** Next.js (App Router), React, Zustand, FastAPI, Python

**Parallelization:** Tasks 1, 4, 5, 6, 8 are independent. Tasks 2→3→7 are sequential (each depends on the previous). Task 9 is the final verification.

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Fix | `frontend/src/features/copilot/components/copilot-preview-pane.tsx` | Move `lazy()` outside component, fix useMemo deps |
| Redirect | `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/buyer-persona/page.tsx` | Convert to sidebar redirect |
| Migrate | `frontend/src/features/brand/components/interview/brand-preview-sections.tsx` | Replace `interviewPreviewData` → `previewData` |
| Migrate | `frontend/src/features/brand/components/interview/brand-preview-summary.tsx` | Replace `interviewPreviewData` → `previewData` |
| Delete | `frontend/src/features/copilot/components/interview/interview-split-view.tsx` | Legacy split view |
| Delete | `frontend/src/features/copilot/components/interview/interview-chat-panel.tsx` | Legacy chat panel |
| Delete | `frontend/src/features/copilot/components/interview/interview-input.tsx` | Legacy input |
| Delete | `frontend/src/features/copilot/components/interview/interview-header.tsx` | Legacy header |
| Delete | `frontend/src/features/copilot/components/interview/interview-message.tsx` | Legacy message |
| Delete | `frontend/src/features/copilot/components/interview/session-restore-modal.tsx` | Legacy modal |
| Delete | `frontend/src/features/copilot/components/interview/__tests__/interview-split-view.test.tsx` | Test for deleted file |
| Delete | `frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx` | Test for deleted file |
| Delete | `frontend/src/features/copilot/hooks/useInterviewChat.ts` | Deprecated hook |
| Delete | `frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts` | Test for deleted hook |
| Delete | `frontend/src/features/brand/components/interview/interview-split-view.tsx` | Brand wrapper of copilot split view |
| Delete | `frontend/src/features/brand/components/interview/session-restore-modal.tsx` | Brand wrapper |
| Delete | `frontend/src/features/brand/components/interview/interview-header.tsx` | Brand wrapper |
| Delete | `frontend/src/features/brand/components/interview/register-brand-preview.ts` | No-op side-effect (registry is static) |
| Delete | `frontend/src/features/offer-studio/components/interview/register-offer-preview.tsx` | No-op side-effect (registry is static) |
| Delete | `frontend/src/features/copilot/components/CopilotPanel.tsx` | Replaced by CopilotSidebar |
| Delete | `frontend/src/components/shared/interview-banner.tsx` | Replaced by CopilotStatusBar |
| Migrate | `frontend/src/features/offer-studio/components/container/offer-shell-header-row2.tsx` | Replace AutocompletarIAButton → FocusModeButton |
| Migrate | `frontend/src/features/offer-studio/components/editor/offer-editor-content.tsx` | Remove OfferSmartFillDialog |
| Delete | `frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx` | Replaced by FocusModeButton |
| Delete | `frontend/src/features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx` | Replaced by Focus Mode |
| Clean | `frontend/src/features/copilot/store/copilot-store.ts` | Remove 4 backward-compat aliases |
| Clean | `frontend/src/features/copilot/__tests__/copilot-store.test.ts` | Remove 3 alias tests |
| Clean | `frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx` | Remove alias fields from mock state |
| Clean | `frontend/src/lib/design-system/registry.ts` | Update CopilotPanel text reference |
| Deprecate | `backend/src/modules/copilot/api/actions.py` | Remove extract-full + psychology endpoints |
| Clean | `frontend/src/features/copilot/config/interview-preview-registry.ts` | Remove dead `getPreview()`, `registerPreview()`, `clearPreviewRegistry()`, `PreviewConfig` |

---

## Task 1: Fix ESLint errors in copilot-preview-pane.tsx

**Files:**
- Modify: `frontend/src/features/copilot/components/copilot-preview-pane.tsx`

**Problems:**
1. `lazy()` called inside component body (lines 31-32) — creates new component identity each render
2. `useMemo` deps use `focusEntity?.domain` (optional chain in deps array)

- [ ] **Step 1: Fix the component**

Replace the entire file content. The fix: move `lazy()` into a memoized object via a helper, and fix the useMemo deps.

```tsx
"use client";

import { Suspense, lazy, useMemo } from "react";
import { Loader2 } from "lucide-react";
import { useCopilotStore } from "../store/copilot-store";
import { getPreviewEntry } from "../config/interview-preview-registry";
import type { PreviewRegistryEntry } from "../config/interview-preview-registry";
import type { ComponentType } from "react";
import type { PreviewSummaryProps, PreviewSectionsProps } from "../config/interview-preview-registry";

// ── Lazy component cache (stable references across renders) ───────────────
const lazyCache = new Map<string, {
  Summary: ComponentType<PreviewSummaryProps>;
  Sections: ComponentType<PreviewSectionsProps>;
}>();

function getLazyComponents(domain: string, entry: PreviewRegistryEntry) {
  const cached = lazyCache.get(domain);
  if (cached) return cached;

  const pair = {
    Summary: lazy(entry.summaryComponent),
    Sections: lazy(entry.sectionsComponent),
  };
  lazyCache.set(domain, pair);
  return pair;
}

function PreviewLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
    </div>
  );
}

export function CopilotPreviewPane() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const previewData = useCopilotStore((s) => s.previewData);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);

  const domain = focusEntity?.domain ?? null;

  const entry = useMemo(
    () => (domain ? getPreviewEntry(domain) : null),
    [domain],
  );

  if (!focusEntity || !entry || !domain) return null;

  const { Summary, Sections } = getLazyComponents(domain, entry);
  const data = previewData ?? focusSnapshot ?? {};
  const hasData = Object.keys(data).length > 0;

  return (
    <div className="flex h-full flex-col bg-slate-50 dark:bg-slate-800/50">
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          Vista previa
        </h3>
        <p className="mt-0.5 text-xs text-slate-500">{focusEntity.label}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {hasData ? (
          <Suspense fallback={<PreviewLoader />}>
            <Summary data={data} completenessScore={0} />
            <Sections data={data} currentBlock="" blocksCompleted={[]} />
          </Suspense>
        ) : (
          <div className="flex h-full items-center justify-center text-center">
            <p className="text-sm text-slate-400">{entry.emptyStateMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify ESLint passes**

Run: `cd frontend && npx eslint src/features/copilot/components/copilot-preview-pane.tsx`
Expected: No errors

- [ ] **Step 3: Verify TypeScript passes**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "copilot-preview-pane" || echo "No errors"`
Expected: No type errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/copilot/components/copilot-preview-pane.tsx
git commit -m "fix(copilot): move lazy() outside component body, fix useMemo deps in preview pane"
```

---

## Task 2: Migrate buyer-persona interview to sidebar redirect

**Files:**
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/buyer-persona/page.tsx`

**Context:** The brand-studio and offer-studio interview pages already redirect to their parent studio with `?interview=SESSION` query param. The buyer-persona page is the last one still rendering `InterviewSplitView` directly.

- [ ] **Step 1: Convert page to redirect**

Replace the entire content of `buyer-persona/page.tsx`:

```tsx
import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ personaId?: string; session?: string }>;
}

export default async function BuyerPersonaInterviewPage({
  params,
  searchParams,
}: PageProps) {
  const { tenantId } = await params;
  const { session, personaId } = await searchParams;

  // Redirect to brand-studio with interview query param for sidebar activation
  const query = new URLSearchParams();
  if (session) query.set("interview", session);
  if (personaId) query.set("personaId", personaId);
  query.set("domain", "buyer_persona");

  const qs = query.toString();
  const target = `/${tenantId}/brand-studio${qs ? `?${qs}` : ""}`;

  redirect(target);
}
```

- [ ] **Step 2: Verify TypeScript passes**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "buyer-persona" || echo "No errors"`
Expected: No type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/interview/buyer-persona/page.tsx
git commit -m "refactor(copilot): buyer-persona interview page redirects to brand-studio sidebar"
```

---

## Task 3: Delete legacy interview files + clean preview components

**Files:**
- Delete: 16 files (see list below)
- Modify: `brand-preview-sections.tsx` (replace `interviewPreviewData` → `previewData`)
- Modify: `brand-preview-summary.tsx` (replace `interviewPreviewData` → `previewData`)
- Clean: `interview-preview-registry.ts` (remove dead backward-compat functions)

**IMPORTANT:** `brand-preview-sections.tsx` and `brand-preview-summary.tsx` are used by the static preview registry (`interview-preview-registry.ts`) for `CopilotPreviewPane`. They CANNOT be deleted — only migrated from the store alias to the canonical field.

### Step-by-step

- [ ] **Step 1: Migrate brand-preview-sections.tsx from alias to canonical field**

In `frontend/src/features/brand/components/interview/brand-preview-sections.tsx`:

Replace line 55:
```tsx
  const { interviewPreviewData } = useCopilotStore();
```
with:
```tsx
  const previewData = useCopilotStore((s) => s.previewData);
```

Replace lines 73 and 88 — every occurrence of `interviewPreviewData` → `previewData`:
```tsx
  // Line 73:
    if (!previewData) return settings;
  // Line 77:
        Object.entries(previewData).map(([k, v]) => [
  // Line 88:
  }, [settings, previewData]);
```

- [ ] **Step 2: Migrate brand-preview-summary.tsx from alias to canonical field**

In `frontend/src/features/brand/components/interview/brand-preview-summary.tsx`:

Replace line 18:
```tsx
  const { interviewPreviewData } = useCopilotStore();
```
with:
```tsx
  const previewData = useCopilotStore((s) => s.previewData);
```

Replace all occurrences of `interviewPreviewData` → `previewData` in the file (lines 23 and 37).

- [ ] **Step 3: Clean interview-preview-registry.ts — remove dead compat code**

In `frontend/src/features/copilot/config/interview-preview-registry.ts`:

Delete the `PreviewConfig` interface (lines 22-28), the `getPreview()` function (lines 98-111), the `registerPreview()` function (lines 117-122), and the `clearPreviewRegistry()` function (lines 128-130). These are all no-ops or dead compat shims.

Keep: `PreviewRegistryEntry`, `PreviewSummaryProps`, `PreviewSectionsProps`, `PreviewTabsProps`, `PREVIEW_REGISTRY`, `getPreviewEntry()`, `getSupportedDomains()`.

- [ ] **Step 4: Verify migrated files compile**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors

- [ ] **Step 5: Delete copilot legacy interview files**

```bash
rm frontend/src/features/copilot/components/interview/interview-split-view.tsx
rm frontend/src/features/copilot/components/interview/interview-chat-panel.tsx
rm frontend/src/features/copilot/components/interview/interview-input.tsx
rm frontend/src/features/copilot/components/interview/interview-header.tsx
rm frontend/src/features/copilot/components/interview/interview-message.tsx
rm frontend/src/features/copilot/components/interview/session-restore-modal.tsx
rm -rf frontend/src/features/copilot/components/interview/__tests__/
rm frontend/src/features/copilot/hooks/useInterviewChat.ts
rm frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
```

- [ ] **Step 6: Delete brand legacy interview wrappers**

```bash
rm frontend/src/features/brand/components/interview/interview-split-view.tsx
rm frontend/src/features/brand/components/interview/session-restore-modal.tsx
rm frontend/src/features/brand/components/interview/interview-header.tsx
rm frontend/src/features/brand/components/interview/register-brand-preview.ts
```

- [ ] **Step 7: Delete offer legacy interview register**

```bash
rm frontend/src/features/offer-studio/components/interview/register-offer-preview.tsx
```

- [ ] **Step 8: Verify TypeScript + ESLint after deletions**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Run: `cd frontend && npx eslint src/features/copilot/ src/features/brand/components/interview/ --no-cache 2>&1 | head -20`
Expected: No errors from deleted files. If any file still imports a deleted module, fix the import.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/brand/components/interview/brand-preview-sections.tsx \
       frontend/src/features/brand/components/interview/brand-preview-summary.tsx \
       frontend/src/features/copilot/config/interview-preview-registry.ts
git rm frontend/src/features/copilot/components/interview/interview-split-view.tsx \
      frontend/src/features/copilot/components/interview/interview-chat-panel.tsx \
      frontend/src/features/copilot/components/interview/interview-input.tsx \
      frontend/src/features/copilot/components/interview/interview-header.tsx \
      frontend/src/features/copilot/components/interview/interview-message.tsx \
      frontend/src/features/copilot/components/interview/session-restore-modal.tsx \
      frontend/src/features/copilot/components/interview/__tests__/interview-split-view.test.tsx \
      frontend/src/features/copilot/components/interview/__tests__/interview-input.test.tsx \
      frontend/src/features/copilot/hooks/useInterviewChat.ts \
      frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts \
      frontend/src/features/brand/components/interview/interview-split-view.tsx \
      frontend/src/features/brand/components/interview/session-restore-modal.tsx \
      frontend/src/features/brand/components/interview/interview-header.tsx \
      frontend/src/features/brand/components/interview/register-brand-preview.ts \
      frontend/src/features/offer-studio/components/interview/register-offer-preview.tsx
git commit -m "refactor(copilot): delete legacy interview chain (16 files), migrate preview to canonical store fields"
```

---

## Task 4: Replace SmartFill with FocusModeButton in offer-studio

**Files:**
- Modify: `frontend/src/features/offer-studio/components/container/offer-shell-header-row2.tsx`
- Modify: `frontend/src/features/offer-studio/components/editor/offer-editor-content.tsx`
- Delete: `frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx`
- Delete: `frontend/src/features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx`

**Context:** The `AutocompletarIAButton` opens a SmartFill dialog. Focus Mode replaces this — `FocusModeButton` activates the copilot sidebar in focus mode for the offer entity.

- [ ] **Step 1: Replace AutocompletarIAButton in offer-shell-header-row2.tsx**

In `frontend/src/features/offer-studio/components/container/offer-shell-header-row2.tsx`:

Replace the import (line 7):
```tsx
import { AutocompletarIAButton } from "./autocompletar-ia-button";
```
with:
```tsx
import { FocusModeButton } from "@/features/copilot/components/focus-mode-button";
```

Replace the usage (line 38):
```tsx
        <AutocompletarIAButton offerId={offer.id} />
```
with:
```tsx
        <FocusModeButton
          domain="offer"
          entityId={offer.id}
          label={offer.public_name ?? "Oferta"}
          entityData={offer as unknown as Record<string, unknown>}
        />
```

- [ ] **Step 2: Remove OfferSmartFillDialog from offer-editor-content.tsx**

In `frontend/src/features/offer-studio/components/editor/offer-editor-content.tsx`:

Delete the import (line 17):
```tsx
import { OfferSmartFillDialog } from "./components/smart-fill/offer-smart-fill-dialog";
```

Delete the state variable (line 40):
```tsx
  const [isSmartFillOpen, setIsSmartFillOpen] = useState(false);
```

Delete the JSX (lines 135-142):
```tsx
        <OfferSmartFillDialog
          open={isSmartFillOpen}
          onOpenChange={setIsSmartFillOpen}
          offerId={offerId}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["offer", offerId] });
          }}
        />
```

Also remove `useQueryClient` import if it's no longer used (check if other code in the file uses it — the `useOffer` hook calls are internal so it may still be needed).

- [ ] **Step 3: Verify TypeScript passes**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Delete SmartFill files**

```bash
rm frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx
rm frontend/src/features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx
```

- [ ] **Step 5: Verify no remaining imports to deleted files**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/offer-studio/components/container/offer-shell-header-row2.tsx \
       frontend/src/features/offer-studio/components/editor/offer-editor-content.tsx
git rm frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx \
      frontend/src/features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx
git commit -m "refactor(offer-studio): replace SmartFill dialog with FocusModeButton"
```

---

## Task 5: Delete CopilotPanel.tsx

**Files:**
- Delete: `frontend/src/features/copilot/components/CopilotPanel.tsx`
- Modify: `frontend/src/lib/design-system/registry.ts` (line 289 — update text reference)

- [ ] **Step 1: Update design-system registry text**

In `frontend/src/lib/design-system/registry.ts`, line 289 mentions `CopilotPanel`. Change the description to reference `CopilotSidebar`:

Replace:
```
'Copilot-aware slide-out detail panel. Positions itself to the left of the CopilotPanel (respects open/rail width). Use instead of Sheet when the panel must coexist with the copilot.',
```
with:
```
'Copilot-aware slide-out detail panel. Positions itself to the left of the CopilotSidebar (respects open/rail width). Use instead of Sheet when the panel must coexist with the copilot.',
```

- [ ] **Step 2: Delete CopilotPanel.tsx**

```bash
rm frontend/src/features/copilot/components/CopilotPanel.tsx
```

- [ ] **Step 3: Verify TypeScript passes**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "CopilotPanel" || echo "No errors"`
Expected: No errors (playground page only has comments, not imports)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/design-system/registry.ts
git rm frontend/src/features/copilot/components/CopilotPanel.tsx
git commit -m "refactor(copilot): delete dead CopilotPanel.tsx, update registry reference"
```

---

## Task 6: Delete InterviewBanner

**Files:**
- Delete: `frontend/src/components/shared/interview-banner.tsx`

- [ ] **Step 1: Verify no active imports**

Run: `cd frontend && grep -rn "interview-banner" src/ --include="*.tsx" --include="*.ts" | grep -v "node_modules"`
Expected: Only the file itself (no imports)

- [ ] **Step 2: Delete file**

```bash
rm frontend/src/components/shared/interview-banner.tsx
```

- [ ] **Step 3: Verify TypeScript passes**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "interview-banner" || echo "No errors"`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git rm frontend/src/components/shared/interview-banner.tsx
git commit -m "refactor(copilot): delete dead InterviewBanner (replaced by CopilotStatusBar)"
```

---

## Task 7: Remove backward-compat aliases from copilot store

**Files:**
- Modify: `frontend/src/features/copilot/store/copilot-store.ts`
- Modify: `frontend/src/features/copilot/__tests__/copilot-store.test.ts`
- Modify: `frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx`

**Depends on:** Task 3 (all files that used these aliases are deleted or migrated)

### Aliases to remove:
- `interviewMode: boolean` (line 165)
- `setInterviewMode(active, sessionId)` (line 166, impl lines 321-333)
- `interviewPreviewData` (line 174, impl lines 337, 342, 351)
- `updateInterviewPreview(delta)` (line 175, impl lines 348-352)

- [ ] **Step 1: Remove aliases from CopilotState interface**

In `frontend/src/features/copilot/store/copilot-store.ts`:

Delete lines 164-166 (the interviewMode alias block):
```typescript
  // Backward-compat: interviewMode derived from interviewSessionId
  interviewMode: boolean;
  setInterviewMode: (active: boolean, sessionId?: string) => void;
```

Delete lines 173-175 (the interviewPreviewData alias block):
```typescript
  // Backward-compat: interviewPreviewData aliases previewData
  interviewPreviewData: Record<string, unknown> | null;
  updateInterviewPreview: (delta: Record<string, unknown>) => void;
```

- [ ] **Step 2: Remove alias implementations from store create**

Delete the `interviewMode: false` initial value (line 304).

In `setInterviewSession` (line 306-307), remove `, interviewMode: true`:
```typescript
  setInterviewSession: (id) =>
    set({ interviewSessionId: id }),
```

In `clearInterview` (lines 311-318), remove `interviewMode: false` and `interviewPreviewData: null`:
```typescript
  clearInterview: () =>
    set({
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
    }),
```

Delete the entire `setInterviewMode` implementation (lines 320-333).

Delete `interviewPreviewData: null` initial value (line 337).

In `updatePreviewData` (lines 339-343), remove `, interviewPreviewData: merged`:
```typescript
  updatePreviewData: (delta) =>
    set((state) => {
      const merged = { ...(state.previewData ?? {}), ...delta };
      return { previewData: merged };
    }),
```

In `clearPreviewData` (line 345), remove `, interviewPreviewData: null`:
```typescript
  clearPreviewData: () => set({ previewData: null }),
```

Delete the entire `updateInterviewPreview` implementation (lines 347-352).

- [ ] **Step 3: Remove alias tests from copilot-store.test.ts**

In `frontend/src/features/copilot/__tests__/copilot-store.test.ts`:

Delete the three test cases (lines 392-408):
```typescript
  it('interviewMode should derive from interviewSessionId', () => { ... });
  it('updateInterviewPreview should alias updatePreviewData', () => { ... });
  it('interviewPreviewData should alias previewData', () => { ... });
```

- [ ] **Step 4: Remove alias fields from copilot-sidebar.test.tsx mock state**

In `frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx`:

Remove from the `beforeEach` setState call (lines 55 and 60):
```typescript
      interviewPreviewData: null,   // DELETE this line
      interviewMode: false,          // DELETE this line
```

- [ ] **Step 5: Verify TypeScript + tests pass**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Run: `cd frontend && npx vitest run src/features/copilot/ 2>&1 | tail -20`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/store/copilot-store.ts \
       frontend/src/features/copilot/__tests__/copilot-store.test.ts \
       frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx
git commit -m "refactor(copilot): remove 4 backward-compat store aliases (interviewMode, setInterviewMode, interviewPreviewData, updateInterviewPreview)"
```

---

## Task 8: Deprecate backend endpoints

**Files:**
- Modify: `backend/src/modules/copilot/api/actions.py`

**Context:** Two endpoints are replaced:
- `POST /copilot/actions/brand/extract-full` → replaced by focus mode + `extract_from_document` tool
- `POST /copilot/actions/offer/psychology` → replaced by interview

The `research.py` tool is still actively used by the `style_analyzer` agent — do NOT delete it.

Note: `POST /copilot/actions/brand/extract` (the non-full version) is still used — keep it.

- [ ] **Step 1: Remove deprecated endpoints**

In `backend/src/modules/copilot/api/actions.py`:

Delete the `extract_full_brand_data` function (lines 64-104) and the `generate_offer_psychology` function (lines 107-126).

Also remove now-unused imports. After deletion, check which imports are still needed:
- Keep: `Annotated`, `UUID`, `APIRouter`, `Depends`, `HTTPException`, `Session`, `get_db`, `ExtractRequest`, `BrandVisuals`, `BrandExtractResponse`, `CopilotBrandAIActionsService`, `get_current_user`, `get_tenant_context`, `User`
- Remove: `Literal`, `File`, `Form`, `UploadFile`, `BrandSettings`, `CopilotOfferPsychologyService`, `PsychologyGenerationRequest`, `PsychologyGenerationResponse`, `FileParsingService`

- [ ] **Step 2: Verify backend lint passes**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/api/actions.py --no-cache`
Expected: No errors

- [ ] **Step 3: Run backend tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
Expected: All pass (no tests targeted the deprecated endpoints directly)

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/copilot/api/actions.py
git commit -m "refactor(copilot): remove deprecated extract-full and psychology endpoints (replaced by focus mode + interview)"
```

---

## Task 9: Full verification

**Files:** None (verification only)

- [ ] **Step 1: Backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: No new errors

- [ ] **Step 2: Backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: All pass

- [ ] **Step 3: Architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 4: Frontend TypeScript**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Frontend ESLint**

Run: `cd frontend && npx eslint src/`
Expected: No new errors from our changes

- [ ] **Step 6: Frontend tests**

Run: `cd frontend && npx vitest run`
Expected: All pass

- [ ] **Step 7: Report final state**

Report: number of files deleted, any remaining issues, final test counts.

---

## Parallelization Guide for Subagent-Driven Development

```
Wave 1 (parallel): Tasks 1, 2
Wave 2 (sequential, depends on T2): Task 3
Wave 3 (parallel, T3 done): Tasks 4, 5, 6, 7, 8
Wave 4 (all done): Task 9
```

Tasks 4, 5, 6, 8 touch completely independent files. Task 7 depends on Task 3 (aliases can only be removed after their consumers are deleted/migrated).
