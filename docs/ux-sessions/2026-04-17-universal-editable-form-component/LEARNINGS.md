# LEARNINGS — Brand Studio refactor

Compact notes per sprint, for future developers picking up the work. No verbosity; only the non-obvious decisions and patterns that paid off.

---

## Sprint 1 (foundation + scaffold)

- **Separate schema types from React.** `lib/form-runtime/schema/` stays framework-free; React components live at `components/form-runtime/`. Consumers cast at the boundary (`values as unknown as T`).
- **Inject recursion, don't import it.** `ArrayInput` takes `renderField` as a prop; this breaks the `FieldRenderer ↔ ArrayInput` cycle.
- **Registry rendering → `createElement`.** `<Component {...} />` flags `react/no-nested-component-definitions`. `createElement(component, props)` is lint-clean and clearer intent.
- **Fake timers:** `vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] })` + `flushMicrotasks()` after `advanceTimersByTime`. Synchronous React state updates require `act()` wrapping.
- **Testing-library events:** `fireEvent.change()`, never `input.dispatchEvent(new Event("change"))`. The raw DOM event doesn't go through React's synthetic-event system.
- **`<textarea rows>`** reads as a string in happy-dom. Assert via `.getAttribute("rows")` not `.rows`.
- **Autosave is shared.** `useAutoSave` lives in `lib/form-runtime/hooks` — don't rewrite per feature.

## Sprint 2.0 (Storybook + URL-driven runtime)

- **Storybook 10 `fn()` lives in `storybook/test`** (not `@storybook/test`). The new path.
- **Storybook stories need `export default meta`** — CSF contract. Exempted from the project's `test-no-default-exports.test.ts` arch gate for `.stories.tsx` files.
- **URL = single source of truth for active field.** `UniversalEditableSection` accepts `activeFieldId` + `getFieldHref` props instead of holding state. The page (or a hook, e.g. `useBrandStudioFieldRouting`) reads the URL and passes the props down. Rows become `<Link>`s; deep-linking is free; mobile back is a URL transition, not a state toggle.
- **Generic `SectionPage` + factory.** 11 brand-studio sections share the same mount code. `createPage({ slug, schema, select, save })` produces page components in one line each. Special cases (personality, voice, logos, avatars) are documented in the module's top comment and live outside the factory.
- **Per-file colocation for stories.** New stories next to source in a sibling `stories/` dir (matching `__tests__/`). Existing segregated stories in `src/stories/*/` are untouched — SSoT in `src/stories/README.md`.

## Sprint 2.1–2.7 (port 7 actions)

- **The ActionComponent contract `(value, onChange, props)` is single-field by convention.** When an action needs multi-field writes (Legal: 6 fields on BrandIdentity), the action reads the full slice via `useFormRuntime()` and dispatches per-field with `setFieldValue(path, val)`. Autosave debounce absorbs the writes into one composed PATCH. Documented in LegalAction's header comment.
- **Variance forces one cast.** `ActionComponent<NarrowType>` is not assignable to `ActionComponent<unknown>` in the registry map. The cast `as unknown as ActionComponent` is the canonical escape hatch. Keep it isolated to one line per entry in `registry.ts`.
- **Split big actions into small components with stable refs.** SingleImagePicker = Action + Wrapper + Dialog + GalleryTile + UploadPreview. ImageGallery same pattern. Every map() row has its own component so inline callbacks become `useCallback` at the row level — no react-perf warnings.
- **Explicit save, not autosave, for auth-mutating actions.** DimensionSliders + PresetCatalog invalidate their own React Query caches; the save button fires the mutation, then bubbles the new value via `onChange`. Wiring it through form-runtime's autosave would double-post.
- **Shadcn `<Slider>` over raw `<input type=range>`.** Radix slider ships a11y (role, keyboard arrows, aria-valuenow) for free.
- **`useMemo` for derived defaults.** `logos = value ?? EMPTY_LOGOS` inline triggers `react-hooks/exhaustive-deps` on the useCallback that depends on it. `useMemo(() => value ?? EMPTY_LOGOS, [value])` is stable and lint-clean.
- **Never import `NextImage` in tests.** `vi.mock("next/image", …)` with a data-testid span short-circuits the SSR image optimizer — tests don't need real rendering, just presence checks.
- **`QueryClientProvider` wrapper for every action that uses React Query hooks in tests AND stories.** A shared one-line decorator per story file keeps it readable.

## Sprint 2.8 (PersonaDetailView → form-runtime)

- **Dotted paths render fine for nested objects.** `demographics.age_range` in schema → the form-runtime writes each leaf via `setFieldValue(path, val)` and composes on save. No special nested-object handling needed in the runtime — the feature's save function is the one that understands the nested shape (PATCH on buyer-persona accepts `demographics: {age_range: ...}`).
- **A page can derive its own URL routing** instead of reusing the generic `useBrandStudioFieldRouting`. PersonaDetailPage routes under `/publico/persona/{personaId}/{fieldId?}` — a different URL shape — so the hrefs are computed locally.
- **`toEditable(persona)` at the page boundary.** Strip server-only fields (completeness_score, created_at, offer_id, etc.) before feeding to the runtime. Keeps the types clean: the runtime sees the PATCH shape; the hook deals with the full entity.

---

## Sprint 3 (App Router flip + route tree restructure)

- **Catch-all `[[...fieldId]]` over 11 per-section folders.** Next.js 16 App Router resolves `/brand-studio/[section]/[[...fieldId]]/page.tsx` for both `/brand-studio/identity` and `/brand-studio/identity/tagline`. One dispatcher + `SECTION_PAGE_MAP`; unknown slugs → `notFound()`. Per-section folders = 11 near-identical `page.tsx` files — not worth it.
- **Layout is minimal.** Drop every state container, sheet manager, dialog, wizard, provider. The form-runtime scaffold inside each page owns autosave, copilot bridge, session state. Layout contributes only: nav rail + `children`. Bigger = state leaking into layout that belongs per-page.
- **URL-driven navigation uses `<Link>`, not `router.push`.** `BrandStudioNavRail` renders `next/link` entries; browser back/forward works out of the box, SSR renders correct href in HTML, keyboard nav works.
- **`as const satisfies Readonly<Record<string, () => React.JSX.Element>>`** preserves literal types (so `keyof typeof MAP` becomes a union of section slugs) while still type-checking shape. Global `JSX` namespace is gone in React 19 — use `React.JSX.Element`.
- **Delete redirect pages when the destination route tree changes shape.** Old `tono-y-voz`/`creativos`/`assets` redirects pointed at URLs that no longer exist. Deleting them is cleaner than redirect chains that traverse dead nodes.
- **Keep external-linked routes alive with stub content.** `/avatars/[id]/edit` is linked from offer-studio — deleting would 404 their flow. Swap the import to a brand-studio stub; fix the real UX in the next persona iteration. Zero-break migration.
- **`next build` has a pre-existing standalone+Pages-Router-404 conflict.** Gate Sprint 3 on tsc + eslint + vitest + build-storybook; skip `next build` until that bug resolves (tracked in memory `project_nextjs_build_bug`).

## Sprint 5 (delete features/brand/ + offer-studio import migration)

- **Dynamic imports don't block tsc until you reference the module.** `interview-preview-registry.ts` has `import("@/features/brand/...")` strings. Until they resolve at runtime, the TS checker doesn't fail — but the lazy loader does. Fix path: shrink the registry (drop brand + buyer_persona entries) BEFORE deleting brand/, so the static `PREVIEW_REGISTRY` map no longer references missing modules. Order matters: registry shrink first, then `rm -rf features/brand/`.
- **Ported "legacy" components should use PascalCase filenames even when the source used kebab-case.** brand-studio's component layer enforces PascalCase for `.tsx` component files (check-file plugin). Ports must rename as they move — `team-manager.tsx` → `TeamManager.tsx`.
- **Strip WithCopilot on port if the component will stop being a copilot focus surface.** Legacy TeamMemberForm lost its two WithCopilot wrappers because it's embedded in a dialog inside offer-studio (no section context to feed copilot). This also gets WithCopilot to zero consumers earlier, unblocking Sprint 4c.
- **Deprecation comments in code > docs-only notes.** Every file in `brand-studio/components/legacy-team/` starts with a "delete when Sprint 6 refactors offer-studio" header comment. Future engineers see the expiration date without having to find a separate doc.
- **Registry-as-metadata still needs to stay in sync.** `lib/design-system/registry-features.ts` catalogs components for the design-system tooling. Dead entries surface in audits and mislead future consumers — purge them in the same sprint as the file deletion, not later.
- **The "expand delete" trap.** Sprint 5's stated scope was "delete brand/". The correct execution actually required: (1) porting 3 business-types components + 4 legacy-team components to brand-studio first; (2) rewiring 7 offer-studio imports; (3) removing the useAutoSave shim. Skipping (1-3) would have left tsc broken immediately after `rm -rf`. Plan for the ripple, not just the delete.
- **`tsc --noEmit` is the fastest smoke test.** After the 17,466-line deletion it took 3 seconds to confirm the world still type-checked. Run it after every batch of changes, not just at the end.
- **Keep `placeholders.tsx` in brand-studio/actions/ alive.** Per PLAN Sprint 2 exit it was supposed to die by now, but Sprint 4d-h (copilot tools) will substitute those 6 remaining placeholder actions. Deleting the file prematurely would force re-inventing the registry during Sprint 4.
- **Tests for ported components: add a single smoke test rather than a full port.** The original brand/ business-types/ had zero tests. Adding the minimum smoke test on the brand-studio port (3 cases: loading / populated / onChange) is low-cost regression insurance without writing the tests the legacy never had.

## Sprint 2.D (data-model purge, backend + frontend)

- **Verify the "duplicate" actually exists before writing the migration.** PLAN §5bis listed 9 visual fields on `BrandIdentity` as duplicates of `BrandVisuals`. Backend reality: those fields lived only in `BrandVisuals`; the frontend `BrandIdentity` interface had them as a loose legacy surface for the wizard extraction flow. No SQL migration was needed — the whole purge was Pydantic `extra="ignore"` + frontend type deletions.
- **JSONB blobs don't need Alembic migrations for field removal.** `brand_settings` is stored as JSONB inside `TenantModel.config_json`. Dropping fields at the Pydantic layer with `extra="ignore"` silently drops old keys on read. No DDL, no prod-clone test needed.
- **`positioning.values.*` → `BrandPersonality` is a value-object move, not a column rename.** In the frontend we introduced `BrandPersonality` (core_values, personality_traits, archetype) and exposed it on `BrandSettings.brand_personality`. The pattern: new VO at the same aggregate root, schema entry `path` uses the top-level VO name, legacy read-paths die with `extra="ignore"`.
- **Schema fields for `string[]` via textarea is a pragmatic compromise.** The form-runtime's `array` type needs `itemSchema` (objects), which is wrong for string lists. Until the runtime grows a native string-list input, use `type: "textarea"` with a "Uno por línea" hint and split/join at the consumer page boundary.

## Sprint 4a + 4c (store collapse + delete dead UI, combined)

- **Intermediate stores break compilation.** PLAN split 4a (collapse state) from 4c (delete UI) as two sprints. Reality: every dying component (WithCopilot, FocusBar, CopilotPreviewPane, FocusModeButton, etc.) references dying state slices, and every live consumer (use-copilot-chat, CopilotHeader, InterviewCompleteCard, use-interview-notifications) references the same slices. Splitting the sprint forces either a half-working store with both old+new slices, or sequential commits where tsc is red between them. Combined commit = single cohesive refactor.
- **`eslint --fix` after large refactors is dangerous.** The auto-fix rewrote 425 files — mostly adding empty JSDoc placeholders, some removing load-bearing casts. Use targeted `git restore -- <paths>` to keep only the files you intentionally touched. Leave `--fix` for one-file scope, not a whole refactor commit.
- **Some casts that look redundant aren't.** `\`${fromStatus}_${toStatus}\` as TransitionKey` gives a precise literal type; eslint's prefer-nothing rule removed it and tsc then complained about indexing a `Partial<Record<...>>`. When a cast narrows a string to a literal union, keep it.
- **Sidebar "expanded" state dies with the preview.** The copilot sidebar had three states — collapsed/open/expanded — where "expanded" existed solely to house the preview pane column. With preview gone, the state simplifies to `collapsed | open`. Don't keep zombie states "in case we want them back"; delete them and restore if a real UX need emerges.
- **Zustand store owning a framework-neutral slot.** `activeBridge: FormRuntimeBridge | null` in the copilot store is fine because the type lives in `lib/form-runtime/copilot/` — FSD-neutral. The copilot store can consume it; the feature store can't reference the other feature store. If the bridge type ever needs to live inside copilot/, that'd be a real boundary violation.

## Sprint 4b (bridge wiring)

- **Identity-preserving disconnect.** `disconnectBridge(bridge)` only nulls the slot if the passed bridge is still active. Two mounts racing (a page navigation mid-transition) leave the newer mount's bridge intact rather than clobbering it. The symmetric check also prevents a legitimate late-unmount from blanking the store after a replacement.
- **Fail-safe Apply on disconnected bridge.** `MultiOptionSelector` + `ProposalCard` mark themselves "Aplicado" even when no bridge is active. This is correct UX: the user sees feedback, and when no form is mounted there's nothing to patch. The alternative (grey out Apply when no session) leaks copilot-session concepts into chat UI that should stay agnostic.
- **Field id → field path via schema lookup.** The backend emits `field_id: "tagline"` because it doesn't know the consumer's path structure. The bridge's `getSnapshot()` exposes the schema; chat UI resolves `field_id` to `path` at Apply time. Keeps the protocol flat and leaves routing concerns in the frontend.

## Patterns every future action port follows

1. **One file per action**; one test file next to it; one story file under `stories/`.
2. **File header comment** explains the non-obvious choice (autosave vs explicit save, multi-field pattern, etc.). Short.
3. **Strip the old console.log / console.error** — replace with a single `console.warn` where the failure must not be silent.
4. **Break inline map() JSX into a sub-component** with useCallback.
5. **Test file mocks**: `@clerk/nextjs`, `next/image`, the specific API module, and `sonner`.
6. **Story file decorator** wraps the component in any needed providers (QueryClient, FormRuntimeProvider).
7. **Placeholder removal is part of the action commit** (same commit deletes the placeholder entry + updates registry.ts).
