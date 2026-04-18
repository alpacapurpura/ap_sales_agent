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

## Patterns every future action port follows

1. **One file per action**; one test file next to it; one story file under `stories/`.
2. **File header comment** explains the non-obvious choice (autosave vs explicit save, multi-field pattern, etc.). Short.
3. **Strip the old console.log / console.error** — replace with a single `console.warn` where the failure must not be silent.
4. **Break inline map() JSX into a sub-component** with useCallback.
5. **Test file mocks**: `@clerk/nextjs`, `next/image`, the specific API module, and `sonner`.
6. **Story file decorator** wraps the component in any needed providers (QueryClient, FormRuntimeProvider).
7. **Placeholder removal is part of the action commit** (same commit deletes the placeholder entry + updates registry.ts).
