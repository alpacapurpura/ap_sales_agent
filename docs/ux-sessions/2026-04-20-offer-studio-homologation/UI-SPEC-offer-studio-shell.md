# UI-SPEC — Offer Studio Shell (3-col split-view + tabs)

**Status:** ready-for-implementation
**Scope:** shell layout, tabs, NavRail, EditionsRail, breadcrumb, topbar
**Feeds agent:** `nicolify-frontend`

---

## 1. Layout grid

### Desktop (≥ 1024px)
```
┌────────────┬──────────────────────────────────────────────────────────┐
│ AppSidebar │ Topbar (breadcrumb + actions)                 h=48       │
│ (Nicolify) ├──────────────────────────────────────────────────────────┤
│  220px     │ OfferStudioTabBar [Editor][Editions][Assets][...]  h=40  │
│            ├──────────────────────────────────────────────────────────┤
│            │ EditionsRail (chips Default / Q2 / VIP)            h=48  │
│            ├──────────┬──────────────────────────────┬────────────────┤
│            │ NavRail  │ Form area                    │ Copilot        │
│            │ (260px)  │ (fluid)                      │ (340px)        │
│            │          │                              │  (collapsible) │
│            │          │                              │                │
└────────────┴──────────┴──────────────────────────────┴────────────────┘
```

### Tablet (768–1023px)
Copilot collapses to 48px rail; click → overlay from right.

### Mobile (< 768px)
- NavRail → drawer triggered by hamburger in topbar.
- Copilot → bottom sheet triggered by floating brand-colored button.
- Tabs row scrolls horizontally.

## 2. Component composition

```tsx
// app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/layout.tsx
<OfferShellLayout offerId={id}>
  <OfferStudioTopbar />
  <OfferStudioTabBar />
  <EditionsRail /* conditionally rendered */ />
  {children}   // editor / editions / assets / knowledge / campaigns / ventas
</OfferShellLayout>
```

## 3. NavRail (`OfferStudioNavRail.tsx`)

**Purpose:** list of resolved sections (from preset), clickable, active state.

**Props:**
```ts
interface OfferStudioNavRailProps {
  offerId: string;
  sections: readonly OfferSectionMeta[];  // from lib/section-catalog.ts + filtered by resolvePresetSections
  activeSlug: string | null;
  completeness?: Record<string, number>;  // 0-100, optional — shows ✓ badge if 100
}
```

**Render rules:**
- Each row = `<Link href={getSectionHref(slug)}>` — uses `useOfferStudioFieldRouting`.
- Active row: `border-left: 2px solid var(--brand)` + `bg-brand/10`.
- Icon comes from `meta.icon` (Lucide component).
- Completeness badge (optional): `✓` in success color when 100%.
- No health-dots (anti-pattern — brand doesn't use them).

**Column header:**
```
┌──────────────────────────────┐
│ SECCIONES          11/11 ✓   │  ← label + completeness counter
├──────────────────────────────┤
│ ◉ Identidad              ›   │
│ ★ Promesa                ›   │  (active — brand accent bar)
│ ♛ Público objetivo       ›   │
│ ⚙ Metodología            ›   │
│ $ Pricing                ›   │
│ 📅 Calendario            ›   │
│ 📍 Ubicación             ›   │
│ ♫ Testimonios            ›   │
│ ❓ FAQ                   ›   │
│ 🎁 Value stack           ›   │
│ 👥 Instructores          ›   │
└──────────────────────────────┘
```

## 4. TabBar (`OfferStudioTabBar.tsx`)

**Tabs (fixed order):**
1. Editor (default)
2. Editions `[count]`
3. Assets `[count]`
4. Knowledge
5. Campaigns
6. Ventas

**Active underline:** 2px bottom border in brand color.
**Inactive color:** `var(--muted-foreground)`.
**Hover:** `var(--foreground)` — no background fill.

## 5. EditionsRail (`EditionsRail.tsx`)

**Rendered only in tabs:** `Editor`, `Editions`.

**Layout:** horizontal scroll chips + sticky label "Edition:" prefix.

**States:**
- Default chip always first, always labeled "(activa)" if Default is published.
- Draft chips = pill with warning dot.
- Active published chip = pill with success dot.
- Selected chip = inverse colors (`bg-foreground text-primary-foreground`).
- `+ Nueva edition` button trailing.

**Behavior:**
- Selecting a chip updates query param `?edition={code}`.
- Query param read via React Query `useEditionResolver` (existing hook `use-offer-edition-resolver.ts`).
- Does NOT change URL path — just search param.

## 6. Topbar / Breadcrumb

**Format:**
`Offer Studio › {OfferName} › {TabLabel} › {SectionLabel?} › {FieldLabel?}`

**Right actions:**
- Offer status badge (draft/active)
- "Vista previa" button (when Editor tab)
- "Publicar" button (primary, when draft)

## 7. Color tokens (align with brand-studio)

| Element | Token |
|---|---|
| NavRail active border | `var(--brand)` (hsl 270 70% 55%) |
| NavRail active bg | `hsl(270 30% 95%)` |
| Form area bg | `var(--background)` |
| Copilot bg | `hsl(270 30% 98%)` |
| Copilot header bg | `hsl(270 40% 96%)` |
| Border | `var(--border)` |
| Muted | `var(--muted)` |

**No custom emerald / amber / blue decoration** — kill health-dot styling from current OfferNavRail.

## 8. Typography

- Section title: `22px / 600 / letter-spacing: -0.01em`
- Field label: `13px / 600`
- Field hint: `12.5px / var(--muted-foreground)`
- Tab label: `13px / 500` (inactive) / `13px / 600` (active)
- Breadcrumb: `13px / var(--muted-foreground)` + current in `foreground`

## 9. Interaction details

| Event | Behavior |
|---|---|
| NavRail row click | `router.push(getFieldHref(null))` |
| Field card click | `router.push(getFieldHref(fieldId))` |
| Tab click | `router.push(/offer-studio/offer/{id}/{tab})` |
| Edition chip click | Update search param via `router.replace({query: {edition}})` |
| Copilot collapse toggle | Update local React state + `localStorage['offer-studio:copilot-collapsed']` |
| Save field | Optimistic update → React Query mutation → toast on success |
| Unsaved changes + navigate | `useBeforeUnload` prompt |

## 10. Example file snippets

### `layout.tsx`
```tsx
export default async function OfferLayout({ children, params }) {
  const { id, tenantId } = await params;
  return (
    <div className="flex h-screen flex-col">
      <OfferStudioTopbar offerId={id} />
      <OfferStudioTabBar offerId={id} tenantId={tenantId} />
      <EditionsRail offerId={id} />
      <div className="flex-1 min-h-0">{children}</div>
    </div>
  );
}
```

### `app/.../editor/[section]/[[...fieldId]]/page.tsx`
```tsx
import { SECTION_PAGE_MAP } from "@/features/offer-studio/pages/section-page-map";

export default async function SectionRoute({ params }) {
  const { section } = await params;
  const Page = SECTION_PAGE_MAP[section];
  if (!Page) notFound();
  return <Page />;
}
```

### `pages/section-pages.tsx` (factory)
```tsx
function createPage<TSlice extends object>(cfg: {
  slug: string;
  schema: SectionSchema;
  select: (settings: OfferSettings) => TSlice | null;
  save: (h: OfferSettingsHooks) => (next: TSlice) => Promise<void>;
}) {
  return function Page() {
    const h = useOfferSettings();
    const values = cfg.select(h.settings);
    return (
      <SectionPage
        sectionSlug={cfg.slug}
        schema={cfg.schema}
        values={values}
        onSave={cfg.save(h)}
        isLoading={h.isLoading}
        copilotSlot={<OfferSectionCopilot sectionSlug={cfg.slug} offerId={h.offerId} />}
      />
    );
  };
}

export const PromisePage = createPage<OfferPromise>({
  slug: "promise",
  schema: promiseSchema,
  select: (s) => s.promise,
  save: (h) => h.updatePromise,
});
// ... 10 more
```

## 11. Accessibility

- NavRail rows: `role="link"`, `aria-current="page"` when active.
- Tabs: `role="tab"` + `aria-selected`, wrapped in `role="tablist"`.
- Copilot collapse button: `aria-expanded` + `aria-controls`.
- Field cards: `role="button"` + `aria-label={`Edit ${fieldLabel}`}`.
- Keyboard: `Tab` cycles through NavRail rows → tab bar → edition chips → form fields.
