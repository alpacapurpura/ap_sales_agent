# Phase 1B Handoff — Strict Rules

**Date:** 2026-04-13  
**Status:** ~60% complete  
**Paused for:** Manual review before continuing

---

## What Was Done ✅

### 1. Rules Switched to Error Mode (eslint.config.mjs)
- `@typescript-eslint/no-explicit-any`: `"error"`
- `@typescript-eslint/no-floating-promises`: `"error"`
- `@typescript-eslint/no-misused-promises`: `"error"`
- `no-alert`: `"error"`
- `no-empty`: `"error"`
- `prefer-const`: `"error"`

### 2. Violations Fixed

| Category | Count | Files Modified |
|----------|-------|----------------|
| `alert()` calls → `toast.error()` | 3 | audit/context-panel.tsx, audit/chat-timeline.tsx |
| `Promise<any>` → proper types | 22 | lib/api/connections.ts (14), offer-studio/api (4), growth-studio/api (2), app/ routes (2) |
| `as any` assertions | 29 | offer-studio/ (11 files), lib/api/ (6 files), brand/ |
| Catch clauses `any` → `unknown` | ~10 | manychat-view.tsx (3), brand/ (3), google-analytics-view.tsx (1), others |
| Interface properties `any` → `unknown`/typed | 20+ | audit/types/index.ts (4), lib/api/*.ts (16+) |
| Function parameters typed | 8+ | brand/ forms, offer-studio adapters |
| Empty blocks | 2 | Found and documented |

**Total fixed:** ~90+ instances

---

## What Remains ⬜

### 3. TypeScript Errors (BLOCKING — must fix first)
**14 compilation errors** from changing `any` → `unknown` where properties are accessed:

| File | Lines | Error |
|------|-------|-------|
| google-workspace-view.tsx | 578, 580, 582, 583, 585 | `result` is unknown, accessing `.status`, `.data`, `.error` |
| mailerlite-view.tsx | 211, 219 | `.name`, `.email` on type `{}` |
| manychat-view.tsx | 211, 217 | `{}` not assignable to ReactNode |
| whatsapp-view.tsx | 142, 240, 269, 287 | unknown not assignable to string/Blob/ReactNode |
| ChannelDetailSidebar.tsx | 398 | unknown not assignable to ReactNode |

### 4. Remaining `any` Violations (~109 instances)

| Category | Count | Location |
|----------|-------|----------|
| Catch clauses `(error: any)` | 45 | connections/ (40), growth-studio/, sales/, app/ |
| Type annotations `: any` | 53 | growth-studio/ (stage-detail-api), sales/ (event-type-form), offer-studio/ (curriculum-builder) |
| Assertions `as any` | 11 | offer-studio/ (1 in offer-edit-sheet-manager + eslint-disable), connections/, growth-studio/ |

**Hotspot files:**
- `connections/components/google-analytics-view.tsx` — 5 remaining catch clauses
- `connections/components/google-workspace-view.tsx` — 5 catch clauses
- `connections/components/shopify-view.tsx` — 4 catch clauses
- `connections/components/youtube-view.tsx` — 5 catch clauses
- `connections/components/meta-view.tsx` — 4 catch clauses
- `connections/components/gmail-view.tsx` — 3 catch clauses
- `connections/components/google-calendar-view.tsx` — several catch clauses
- `connections/components/telegram-view.tsx` — several catch clauses
- `connections/components/mailerlite-view.tsx` — several catch clauses + TS errors
- `growth-studio/api/stage-detail-api.ts` — ~20 `: any` params in mapper functions
- `growth-studio/components/strategy-canvas/` — ~7 `any` usages
- `sales/components/event-type-form.tsx` — ~4 `any` usages

---

## How to Resume

### Step 1: Fix TypeScript Errors (BLOCKING)
```
Prompt for next agent:
"Fix all 14 TypeScript errors in /home/chris/AISALESHT/frontend/src listed in docs/mejoras-proceso/phase-1b-handoff.md section 3. Read each file, add proper type narrowing or interfaces, then verify with: cd frontend && npx tsc --noEmit"
```

### Step 2: Fix Remaining Catch Clauses (~45)
```
Prompt:
"Fix ALL 'catch (error: any)' in /home/chris/AISALESHT/frontend/src/features/connections/components/. Read each file, change to 'catch (error: unknown)' with 'instanceof Error' check for message access. Files: google-analytics-view, google-workspace-view, shopify-view, youtube-view, meta-view, gmail-view, google-calendar-view, telegram-view, mailerlite-view. Verify no 'catch.*: any)' remains."
```

### Step 3: Fix Remaining Type Annotations (~53)
```
Prompt:
"Fix ALL ': any' type annotations in /home/chris/AISALESHT/frontend/src. Focus on: growth-studio/api/stage-detail-api.ts (mapper params), sales/components/event-type-form.tsx, offer-studio/ form handlers. Use proper interfaces, 'unknown', or 'Record<string, unknown>' as appropriate."
```

### Step 4: Fix Remaining as any (~11)
```
Prompt:
"Fix ALL 'as any' assertions remaining in /home/chris/AISALESHT/frontend/src. Search with grep, read each file, remove or replace with 'as unknown as SpecificType'."
```

### Step 5: Verify
```bash
cd frontend && npx tsc --noEmit           # Must be 0 errors
cd frontend && npx eslint src/ 2>&1 | grep "error" | wc -l  # Count errors
cd frontend && npx vitest run              # Tests must pass
```

---

## Key Files Modified

| File | Changes |
|------|---------|
| `frontend/eslint.config.mjs` | 6 rules switched to error |
| `frontend/src/features/audit/types/index.ts` | 4 any → unknown/Record |
| `frontend/src/features/audit/components/context-panel.tsx` | 2 alert → toast |
| `frontend/src/features/audit/components/chat-timeline.tsx` | 1 alert → toast |
| `frontend/src/lib/api/connections.ts` | 14 Promise<any> → typed, 8 Record<any> → Record<unknown> |
| `frontend/src/features/connections/components/manychat-view.tsx` | 3 catch clauses fixed |
| `frontend/src/features/offer-studio/api/index.ts` | 4 Promise<any> → typed |
| `frontend/src/features/offer-studio/` (11 files) | 29 as any removed |
| `frontend/src/lib/api/` (6 files) | 16 any → proper types |
| `frontend/src/features/brand/` (9 files) | 10 any → proper types, 3 catch clauses, 3 alert → toast |
| `frontend/src/features/growth-studio/api/` (2 files) | 2 Promise<any> → typed |
| `frontend/src/app/` (2 files) | 2 catch clauses fixed |

---

## Lessons Learned

1. **Changing `any` → `unknown` breaks TS** if properties are accessed without narrowing. Always add `instanceof Error` checks or proper interfaces first.
2. **React Hook Form dynamic paths** are the hardest to type — sometimes `eslint-disable` with TODO is pragmatic.
3. **API layer responses** should have proper interfaces defined, not `unknown` or `any`.
4. **Catch clauses are the easiest wins** — mechanical find-and-replace with instanceof pattern.
5. **growth-studio/api/stage-detail-api.ts** has the most complex `any` usage — mapper functions that accept `raw: any` and do dynamic property access. These need proper input types derived from the API schema.

---

## Next Steps After Phase 1B

Once Phase 1B reaches 0 errors:
1. Update `docs/mejoras-proceso/frontend-quality-tracker.md` with Phase 1B results
2. Move to Phase 1C: Lower complexity thresholds
3. Then Phase 2: Prettier integration
4. Then Phase 3: FSD enforcement (194 deep imports)
