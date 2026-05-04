# UI-SPEC — Offer Studio Shell (rail + tab bar + landing button + banner + clone modal)

> **Scope:** El "chrome" del Offer Studio detail view. Todo lo que rodea el contenido de cada tab.
>
> **Reference:** `prototype/offer-studio/offer-info.html`, `offer-info-edition2.html`, `offer-no-editions.html`, `offer-landing-editor.html`.
>
> **Status:** Ready for implementation.

---

## 1. Overall layout

```
┌───────────────────────────────────────────────────────────────────────┐
│ App sidebar │ Editions rail │ Main content (tabs + body)              │
│    w-60     │    w-60       │   flex-1                                │
│  (AppSide-  │  (EditionsRail│  ┌────────────────────────────────────┐ │
│   bar.tsx)  │   .tsx)       │  │ OfferShellHeaderRow1               │ │
│             │               │  ├────────────────────────────────────┤ │
│             │               │  │ OfferShellHeaderRow2 (optional)    │ │
│             │               │  ├────────────────────────────────────┤ │
│             │               │  │ OfferTabBar + LandingSplitButton   │ │
│             │               │  ├────────────────────────────────────┤ │
│             │               │  │ WaitlistBanner (if applicable)     │ │
│             │               │  ├────────────────────────────────────┤ │
│             │               │  │ Tab content                        │ │
│             │               │  └────────────────────────────────────┘ │
│             │  (collapsed   │                                          │
│             │   variant     │                                          │
│             │   w-14)       │                                          │
└───────────────────────────────────────────────────────────────────────┘
```

**Tailwind layout root:**
```tsx
<div className="flex min-h-screen">
  <AppSidebar />              {/* always visible */}
  {offer.has_editions && <EditionsRail />}   {/* only if supports editions */}
  <main className="flex-1 overflow-auto">
    <OfferShellHeaderRow1 />
    <OfferShellHeaderRow2 />   {/* optional, see § 4 */}
    <OfferTabBar />            {/* includes LandingSplitButton on right */}
    {waitlistCount > 0 && <WaitlistBanner />}
    <Outlet />                 {/* tab content via Next.js or conditional */}
  </main>
</div>
```

**Responsive:**
- Desktop ≥ `xl` (1280px): app sidebar + rail + main.
- Tablet `md`–`xl`: app sidebar collapsed + rail visible + main.
- Mobile `<md`: todo mobile-sheet triggered, rail becomes bottom drawer.

---

## 2. EditionsRail component

### 2.1 File location
`frontend/src/features/offer-studio/components/container/EditionsRail.tsx`

### 2.2 Props
```ts
interface EditionsRailProps {
  offerId: string;
  offerName: string;
  offerIconName: string;  // lucide icon from archetype_catalog
  currentEditionId: string | null;  // current ?edition= query param
  editions: LaunchEdition[];        // all editions, unsorted
  waitlistCount: number;            // offer-level waitlist
  onSwitch: (editionId: string) => void;
  onCollapse: () => void;
  onCreateNew: () => void;          // opens EditionCloneModal
}
```

### 2.3 Visual structure

```
┌─────────────────────────┐
│  [🗺️] MasterClass Copy  │ ← header con icono archetype + name (truncate) + collapse
│                    ‹‹   │
├─────────────────────────┤
│ ⭐ PRÓXIMA              │ ← group label, text-[10px] uppercase
│ ┌─────────────────────┐ │
│ │ Edición #3  [Prox.] │ │ ← active: bg-blue-50 border-blue-200 ring-1 ring-blue-200/50
│ │ Lun 15 jul · 6 sem  │ │
│ │ 🌐 Pública · 12/50  │ │
│ └─────────────────────┘ │
│                         │
│ ✏ BORRADORES           │
│ ┌─────────────────────┐ │
│ │ Edición #4 [Borr.]  │ │ ← border-dashed border-amber-300
│ │ Sin fecha           │ │
│ │ ⚠ 3 en waitlist     │ │ (si waitlist > 0)
│ └─────────────────────┘ │
│                         │
│ ✓ PASADAS              │
│ Edición #2     abr '26  │ ← rows simples, text-slate-600
│ 25/25 · Completada      │
│                         │
│ Edición #1     ene '26  │
│ 18/30 · Completada      │
│                         │
├─────────────────────────┤
│ [+ Nueva edición]       │ ← footer CTA, bg-purple-600
│ Clonar recomendado      │
└─────────────────────────┘
```

### 2.4 Grouping logic
```ts
const grouped = useMemo(() => {
  const active = editions.filter(e => e.status === 'active');
  const upcoming = editions.filter(e => e.status === 'upcoming');
  const drafts = editions.filter(e => e.status === 'draft');
  const past = editions
    .filter(e => e.status === 'completed' || e.status === 'cancelled')
    .sort((a, b) => (b.start_date ?? '').localeCompare(a.start_date ?? ''));  // recent first
  return { active, upcoming, drafts, past };
}, [editions]);
```

**Order of sections shown:**
1. `🔴 EN CURSO` (active) — only if exists
2. `⭐ PRÓXIMA` (upcoming) — expected 0 or 1
3. `✏ BORRADORES` (drafts)
4. `✓ PASADAS` (completed/cancelled)

### 2.5 Styling per entry

**Próxima (active):**
```tsx
<a className="block p-3 rounded-lg bg-blue-50 border border-blue-200 hover:bg-blue-100 ring-1 ring-blue-200/50">
  <div className="flex items-center justify-between mb-1">
    <span className="font-semibold text-sm text-blue-900">Edición #{n}</span>
    <StatusBadge status="upcoming" size="xs" />
  </div>
  <p className="text-xs text-blue-700">{formatDate(start_date)} · {duration}</p>
  <p className="text-xs text-blue-700 mt-1">
    {visibility === 'public' ? '🌐 Pública' : '🔒 Privada'} · {enrollment_count}/{capacity}
  </p>
</a>
```

**Borrador:**
```tsx
<a className="block p-3 rounded-lg border border-dashed border-amber-300 hover:bg-amber-50">
  <div className="flex items-center justify-between mb-1">
    <span className="font-semibold text-sm text-amber-800">Edición #{n}</span>
    <StatusBadge status="draft" size="xs" />
  </div>
  <p className="text-xs text-amber-700">{start_date ? formatDate(start_date) : 'Sin fecha'}</p>
  {waitlistCount > 0 && (
    <p className="text-xs text-purple-700 mt-1">⚠ {waitlistCount} en waitlist</p>
  )}
</a>
```

**Pasada:**
```tsx
<a className="block p-2.5 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200">
  <div className="flex items-center justify-between">
    <span className="text-sm text-slate-600">Edición #{n}</span>
    <span className="text-xs text-slate-400">{formatMonth(start_date)}</span>
  </div>
  <p className="text-xs text-slate-400">{enrollment_count}/{capacity} · Completada</p>
</a>
```

**Pasada selected (when user clicks):** bg-slate-100, border-slate-300, ring-1 ring-slate-200, add revenue/NPS detalle bajo el nombre.

### 2.6 Footer CTA

```tsx
<div className="p-2 border-t border-slate-200">
  <button
    onClick={onCreateNew}
    className="w-full px-3 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700"
  >
    + Nueva edición
  </button>
  <p className="text-[10px] text-slate-400 text-center mt-1.5">Clonar recomendado</p>
</div>
```

### 2.7 Empty state
Si `editions` está vacío (no debería pasar post Phase 2 porque siempre hay placeholder):
```
┌─────────────────────────┐
│ MasterClass Copy        │
├─────────────────────────┤
│      (empty icon)       │
│  Sin ediciones todavía  │
│                         │
│  [+ Crear primera]      │
└─────────────────────────┘
```

---

## 3. EditionsRailCollapsed component

### 3.1 File location
Mismo archivo que `EditionsRail.tsx` o `EditionsRailCollapsed.tsx` colocated.

### 3.2 Visual

```
┌──────┐
│ ››   │ ← expand button
│      │
│  3   │ ← current upcoming, ring-2 ring-blue-200, bg-blue-600 text-white
│      │
│ (4)  │ ← draft, border-dashed border-amber-400, bg-amber-50, text-amber-700
│ ──── │ ← separator (draft/past)
│  2   │ ← past, bg-slate-100, text-slate-500
│  1   │
│      │
│  +   │ ← new edition button, border-dashed border-purple-300, text-purple-600
└──────┘
```

### 3.3 Styling

**Badge próxima:**
```tsx
<a
  className="w-10 h-10 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center ring-2 ring-blue-200"
  title={`Edición #${n} · Próxima`}
>
  {n}
</a>
```

**Badge borrador:**
```tsx
<a
  className="w-10 h-10 rounded-full bg-amber-50 text-amber-700 border-2 border-dashed border-amber-400 font-semibold flex items-center justify-center"
  title={`Edición #${n} · Borrador`}
>
  {n}
</a>
```

**Badge pasada:**
```tsx
<a className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 font-semibold flex items-center justify-center">
  {n}
</a>
```

**Nueva:**
```tsx
<button className="w-10 h-10 rounded-full border-2 border-dashed border-purple-300 text-purple-600 hover:bg-purple-50">
  +
</button>
```

### 3.4 Persistence
State `railCollapsed: boolean` persisted en localStorage `nicolify.offer-studio.rail-collapsed`. Default `false`.

---

## 4. Offer header rows

### 4.1 OfferShellHeaderRow1 (identity + lifecycle)

**Current implementation:** exists, needs update.

**New visual:**
```
┌──────────────────────────────────────────────────────────────────────┐
│ ← MasterClass de Copywriting · Edición #3 · Julio 2026    [Próxima] │
│    Programa · DWY · ● Guardado hace 2s                    [Pública] │
│                                                            [⋮]      │
└──────────────────────────────────────────────────────────────────────┘
```

**Markup:**
```tsx
<header className="bg-white border-b border-slate-200 px-8 py-3 flex items-center justify-between">
  <div className="flex items-center gap-3">
    <BackButton href={`/${tenantId}/offer-studio`} />
    <div>
      <h1 className="text-lg font-bold flex items-center gap-2 flex-wrap">
        <span>{offer.public_name}</span>
        {currentEdition && (
          <>
            <span className="text-slate-300 font-normal">·</span>
            <span className="text-blue-700">Edición #{currentEdition.edition_number} · {formatEditionMonth(currentEdition.start_date)}</span>
          </>
        )}
      </h1>
      <p className="text-xs text-slate-500">
        {archetypeLabel} · {deliveryModel} · <AutoSaveIndicator />
      </p>
    </div>
  </div>
  <div className="flex items-center gap-2">
    {currentEdition && (
      <>
        <StatusBadge status={currentEdition.status} />
        <VisibilityBadge visibility={currentEdition.visibility} />
      </>
    )}
    <OfferOptionsMenu />  {/* ⋮ menu: duplicar, archivar, etc. */}
  </div>
</header>
```

**Offer without editions:** solo muestra nombre de oferta y status/visibility de la oferta (no de edición).

### 4.2 OfferShellHeaderRow2 (progress + AI)

**Current implementation:** exists with "Landing Page" button — remove that button (moved to split-button).

**New visual:**
```
┌──────────────────────────────────────────────────────────────────────┐
│ 78% ████████░░ 8/10 · siguiente: Testimonios           [✨ IA]       │
└──────────────────────────────────────────────────────────────────────┘
```

**Markup:**
```tsx
<div className="bg-slate-50 border-b border-slate-200 px-8 py-2 flex items-center justify-between text-xs">
  <div className="flex items-center gap-3 flex-1 max-w-xl">
    <span className="font-bold text-blue-600 tabular-nums">{completionPct}%</span>
    <Progress value={completionPct} className="h-1.5" />
    <span className="text-slate-500">
      {completedSections}/{totalSections} · siguiente: <strong className="text-slate-800">{nextSection}</strong>
    </span>
  </div>
  <Button onClick={onAutoCompleteAI} className="px-3 py-1.5 bg-purple-600 text-white rounded-lg">
    ✨ Autocompletar IA
  </Button>
</div>
```

---

## 5. OfferTabBar + LandingSplitButton

### 5.1 File location
- `frontend/src/features/offer-studio/components/container/OfferTabBar.tsx`
- `frontend/src/features/offer-studio/components/container/LandingSplitButton.tsx`

### 5.2 Visual

```
┌─ border-b ─────────────────────────────────────────────────────────┐
│ [📋 Info] [💰 Ventas (12)] [🎨 Assets (12)] [📢 Campañas (3)]  [🌐 Editar landing ▾]
└────────────────────────────────────────────────────────────────────┘
```

**Tabs active:** underline style (border-b-2 accent color).
**Tabs inactive:** border-b-2 transparent, hover color change.

### 5.3 Tab markup

```tsx
<nav className="bg-white border-b border-slate-200 px-8 flex items-center justify-between">
  <div className="flex gap-1 text-sm">
    {TABS.map(tab => (
      <Link
        key={tab.id}
        href={`?tab=${tab.id}${currentEditionId ? `&edition=${currentEditionId}` : ''}`}
        className={cn(
          "px-4 py-3 border-b-2 transition-colors",
          activeTab === tab.id
            ? "border-blue-600 text-blue-700 font-semibold"
            : "border-transparent text-slate-500 hover:text-slate-800"
        )}
      >
        {tab.icon} {tab.label}
        {tab.count != null && <span className="ml-1 text-xs text-slate-400">({tab.count})</span>}
      </Link>
    ))}
  </div>
  <LandingSplitButton {...landingProps} />
</nav>
```

### 5.4 Tab config

```ts
const TABS: TabConfig[] = [
  { id: 'info', icon: '📋', label: 'Info', count: null },
  { id: 'ventas', icon: '💰', label: 'Ventas', count: enrollmentsCount },
  { id: 'assets', icon: '🎨', label: 'Assets', count: assetsCount },
  { id: 'campanas', icon: '📢', label: 'Campañas', count: campaignsCount },
];
```

Note: contador de `ventas/assets/campanas` scoped a la edición actual, se calcula del `counts` endpoint (agregado).

### 5.5 LandingSplitButton

```tsx
interface LandingSplitButtonProps {
  editionId: string | null;
  landingStatus: 'none' | 'draft' | 'publishing' | 'dirty' | 'published';
  publicUrl: string | null;
  onMainClick: () => void;    // opens editor in new window
  onRegenerate: () => void;
  onCloneFrom: () => void;    // opens source picker
  onUnpublish: () => void;
  onCopyUrl: () => void;
  onOpenPublic: () => void;   // abre URL en nueva pestaña
}
```

**Main button label based on status:**
```ts
const MAIN_LABEL: Record<LandingStatus, { label: string; icon: string; bg: string }> = {
  none:       { label: 'Generar landing con IA', icon: '✨', bg: 'bg-purple-600 hover:bg-purple-700' },
  draft:      { label: 'Publicar landing',       icon: '🚀', bg: 'bg-amber-600 hover:bg-amber-700' },
  publishing: { label: 'Publicando…',            icon: '⏳', bg: 'bg-slate-400' },
  dirty:      { label: 'Publicar cambios',       icon: '🌐', bg: 'bg-emerald-600 hover:bg-emerald-700' },
  published:  { label: 'Editar landing',         icon: '🌐', bg: 'bg-emerald-600 hover:bg-emerald-700' },
};
```

**Markup:**
```tsx
<div className="relative flex items-center py-2">
  <button
    onClick={onMainClick}
    className={cn("flex items-center gap-2 px-3 py-1.5 text-white text-sm rounded-l-lg border-r font-medium", mainBg, mainBorderR)}
  >
    <span className={cn(landingStatus === 'published' ? 'w-1.5 h-1.5 bg-white rounded-full' : '')} />
    <span>{mainIcon} {mainLabel}</span>
  </button>
  <button
    onClick={toggleMenu}
    className={cn("px-2 py-1.5 text-white text-sm rounded-r-lg", mainBg)}
    aria-label="Opciones"
  >
    ▾
  </button>
  {menuOpen && (
    <div className="absolute right-0 top-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg w-64 py-1 z-30">
      {landingStatus !== 'none' && <MenuItem icon="👁" label="Abrir URL pública" onClick={onOpenPublic} />}
      {landingStatus !== 'none' && <MenuItem icon="📋" label="Copiar URL" onClick={onCopyUrl} />}
      <MenuItem icon="🔄" label="Regenerar con IA" onClick={onRegenerate} />
      <MenuItem icon="📥" label="Clonar de otra edición" onClick={onCloneFrom} />
      {landingStatus === 'published' && (
        <>
          <MenuSeparator />
          <MenuItem icon="⏸" label="Despublicar" onClick={onUnpublish} variant="warning" />
        </>
      )}
    </div>
  )}
</div>
```

### 5.6 Main click behavior
- Si `editionId` presente: `window.open('/${tenantId}/offer-studio/offer/${offerId}/editions/${editionId}/landing', '_blank')`.
- Si no (offer sin ediciones): `window.open('/${tenantId}/offer-studio/offer/${offerId}/landing', '_blank')`.

---

## 6. WaitlistBanner

### 6.1 File location
`frontend/src/features/offer-studio/components/container/WaitlistBanner.tsx`

### 6.2 Visibility condition
```ts
const shouldShowBanner = (
  currentEdition?.visibility === 'public' &&
  waitlistCount > 0
);
```

### 6.3 Visual
```
┌─────────────────────────────────────────────────────────────────────┐
│ [📋] Tienes 12 leads en lista de espera para esta oferta           │
│      Podés notificarles que la Edición #3 ya está abierta           │
│                                       [Ver lista] [Notificar todos] │
└─────────────────────────────────────────────────────────────────────┘
```

**Background:** gradiente `from-purple-50 to-blue-50` con `border border-purple-200/50`.

### 6.4 Markup
```tsx
<div className="mx-8 mt-4 rounded-xl p-4 flex items-center justify-between"
     style={{background: 'linear-gradient(90deg, hsl(var(--purple-soft)), hsl(var(--accent-soft)))', border: '1px solid hsl(var(--purple) / 0.3)'}}>
  <div className="flex items-center gap-3">
    <span className="w-10 h-10 rounded-full bg-purple-200 text-purple-700 flex items-center justify-center">📋</span>
    <div>
      <p className="font-semibold text-sm">Tienes {waitlistCount} leads en lista de espera para esta oferta</p>
      <p className="text-xs text-slate-600">Podés notificarles que la Edición #{editionNumber} ya está abierta</p>
    </div>
  </div>
  <div className="flex gap-2">
    <Button variant="outline" size="sm" onClick={onViewList}>Ver lista</Button>
    <Button variant="primary" size="sm" onClick={onNotifyAll}>Notificar a todos</Button>
  </div>
</div>
```

### 6.5 Notify action
Llama `/api/v1/sales-agent/enrollments/promote-waitlist` con `{enrollment_ids: [...], target_edition_id: currentEdition.id}`. Retorna lista de resultados. Muestra toast con resumen.

---

## 7. EditionCloneModal

### 7.1 File location
`frontend/src/features/offer-studio/components/container/EditionCloneModal.tsx`

### 7.2 Trigger
- Botón `+ Nueva edición` en `EditionsRail`.
- Botón `Clonar → Edición #N+1` en header cuando usuario está viendo edición pasada.
- Menú `⋮` de la edición en rail → `Clonar esta`.

### 7.3 Visual structure

```
┌──────────────────────────────────────────────────┐
│ Crear edición nueva                         [✕]  │
│ Clonar desde una edición anterior                │
├──────────────────────────────────────────────────┤
│ Fuente: [▼ Edición #2 · Abril 2026 (completa) ] │
│                                                   │
│ Estrategia:                                       │
│ ○ Literal — copia exacta                         │
│ ● Cambiar fechas — copia + sustituye fechas      │
│ ○ Regenerar con IA — copia + pide cambios        │
│                                                   │
│ ─── (si "cambiar fechas"): ───────                │
│ Nueva fecha inicio: [15 oct 2026]                │
│ Nueva fecha fin:    [30 nov 2026]                │
│                                                   │
│ ─── (si "regenerar IA"): ─────────                │
│ ¿Qué cambia?                                      │
│ [textarea: "Cambiamos el formato..."]            │
│ Adjuntos: [upload 📎]                            │
│                                                   │
├──────────────────────────────────────────────────┤
│ [Cancelar]           [Clonar y abrir Edición #3] │
└──────────────────────────────────────────────────┘
```

### 7.4 Markup skeleton
```tsx
<Dialog open={open} onOpenChange={onClose}>
  <DialogContent className="max-w-xl">
    <DialogHeader>
      <DialogTitle>Crear edición nueva</DialogTitle>
      <DialogDescription>Clonar desde una edición anterior acelera la configuración</DialogDescription>
    </DialogHeader>

    <div className="space-y-4">
      <FormField label="Edición fuente">
        <Select value={sourceId} onValueChange={setSourceId}>
          {sourceEditions.map(e => (
            <SelectItem key={e.id} value={e.id}>
              Edición #{e.edition_number} · {formatMonth(e.start_date)} ({e.status})
            </SelectItem>
          ))}
        </Select>
      </FormField>

      <FormField label="Estrategia">
        <RadioGroup value={strategy} onValueChange={setStrategy}>
          <RadioOption value="literal" label="Literal" description="Copia exacta de todos los campos" />
          <RadioOption value="date_replace" label="Cambiar fechas" description="Copia + sustituye tokens {start_date}, {end_date}, {capacity}" />
          <RadioOption value="ai_regen" label="Regenerar con IA" description="Copia como base + pide cambios conversacionales" />
        </RadioGroup>
      </FormField>

      {strategy === 'date_replace' && (
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Nueva fecha de inicio"><DatePicker value={newStart} onChange={setNewStart} /></FormField>
          <FormField label="Nueva fecha de fin"><DatePicker value={newEnd} onChange={setNewEnd} /></FormField>
        </div>
      )}

      {strategy === 'ai_regen' && (
        <>
          <FormField label="¿Qué cambia?">
            <Textarea value={brief} onChange={setBrief} placeholder="Ej: Cambiamos el formato a 8 semanas y agregamos un módulo de VSL..." />
          </FormField>
          <FormField label="Adjuntos (opcional)">
            <FileUpload multiple accept=".pdf,.png,.jpg,.mp4" onFilesChange={setAttachments} />
          </FormField>
        </>
      )}
    </div>

    <DialogFooter>
      <Button variant="outline" onClick={onClose}>Cancelar</Button>
      <Button onClick={handleConfirm} disabled={!sourceId || submitting}>
        {submitting ? <Loader /> : `Clonar y abrir Edición #${nextNumber}`}
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 7.5 API call
```ts
await editionsApi.clone(offerId, sourceId, {
  strategy,
  new_start_date: strategy === 'date_replace' ? newStart : undefined,
  new_end_date: strategy === 'date_replace' ? newEnd : undefined,
  changes_brief: strategy === 'ai_regen' ? brief : undefined,
  attachments: strategy === 'ai_regen' ? attachments : undefined,
}, token);
```

Backend endpoint: `POST /api/v1/offer/products/{offer_id}/editions/{source_id}/clone` (ya existe desde Phase 3, agregar payload fields).

### 7.6 On success
- Invalida `queryKey: ["editions", offerId]`.
- `router.push('/offer-studio/offer/{offerId}?edition={newEditionId}')`.
- Toast: "Edición #{n} creada. ¡Editá lo que necesites cambiar!"

---

## 8. Variant: offer without editions (PRODUCTO / MEMBRESIA)

**Prototype:** `offer-studio/offer-no-editions.html`.

### 8.1 Trigger
```ts
const showsRail = offer.has_editions !== false;  // has_editions === false siempre oculta rail
// has_editions === null/undefined durante loading → oculta rail (skeleton)
```

### 8.2 Behavior
- Rail hidden. Main ocupa todo el ancho disponible.
- Tabs idénticos (`Info · Ventas · Assets · Campañas`).
- Info tab: sin sección "Fechas y Logística", sin sección "Pricing Tiers Timeline". En su lugar: "Acceso y Entrega" + precio único.
- WaitlistBanner no se muestra (no hay concepto de waitlist para offers evergreen).
- Landing split-button sin cambios (edita la única landing del offer).
- EditionCloneModal no se abre (no hay botón que lo invoque).

### 8.3 Info banner
Mostrar en la parte superior del contenido de Info:
```
💡 Este producto es evergreen — no hay ediciones/cohortes. El rail lateral de ediciones está oculto automáticamente para archetypes PRODUCTO y MEMBRESIA.
```

---

## 9. Interaction details

### 9.1 Switching editions via rail

Cuando usuario hace click en una edición del rail:
1. Update URL: `router.replace('?tab={currentTab}&edition={newEditionId}')` (reemplaza, no push, para no llenar history).
2. React Query automáticamente re-fetchea datos scoped a nueva edición.
3. Tab content renderea nueva data (sin re-mount del shell).
4. Rail highlight cambia instantáneamente.
5. Scroll posición del tab se preserva.

### 9.2 Read-only mode for past/cancelled editions

Cuando `currentEdition.status ∈ {COMPLETED, CANCELLED}`:
- Banner arriba del tab content: "📦 Viendo Edición #2 · Abril 2026 (completada). Solo lectura." (ver prototipo `offer-info-edition2.html`).
- Botón "Clonar → Edición #5" prominente.
- Todos los inputs de Info tab son `readonly` o `disabled`.
- Landing split-button: main button label cambia a "Ver landing" (no "Editar"). Dropdown solo muestra "Copiar URL", "Abrir URL pública". No ofrece "Regenerar" ni "Despublicar".
- WaitlistBanner no se muestra.

### 9.3 Tab counts update

Los counts en cada tab (`(12)`, `(3)`) provienen de un endpoint agregado:
```
GET /api/v1/offer/products/{offer_id}/counts?edition={editionId}
→ { ventas: 12, assets: 12, campanas: 3, knowledge: 5 }
```

React Query invalidate tras mutations relevantes.

---

## 10. Accessibility

- Rail es `<aside>` con `aria-label="Ediciones de la oferta"`.
- Colapsado rail mantiene `tabindex` + keyboard nav (flechas arriba/abajo).
- Landing split-button dropdown: `role="menu"`, items `role="menuitem"`, focus trap cuando abre.
- Status badges tienen `aria-label` explícito (ej. `aria-label="Estado: Próxima"`).
- Waitlist banner uses `role="status"` con `aria-live="polite"` para anunciar count changes.

---

## 11. States visual summary

| Estado | Rail entry | Status badge | Border card |
|---|---|---|---|
| DRAFT (placeholder) | bg-transparent border-dashed amber | amber soft | amber dashed |
| DRAFT (user fill) | bg-amber-50 border-amber-200 | amber soft | amber solid |
| UPCOMING + PRIVATE | bg-slate-100 border-slate-200 | blue soft | slate solid |
| UPCOMING + PUBLIC | **bg-blue-50 border-blue-200 ring** ← "la próxima" | blue soft | blue solid |
| ACTIVE + PUBLIC | bg-emerald-50 border-emerald-200 ring | emerald soft | emerald solid |
| COMPLETED | bg-slate-50 border-transparent hover:bg-slate-100 | slate 100 | hidden |
| CANCELLED | opacity-40 bg-red-50 | red soft | red soft |

---

## 12. Test scenarios (E2E smoke)

1. **Rail render:** abrir oferta con 3 ediciones → verificar rail muestra Próxima destacada + Borradores + Pasadas.
2. **Switch edición:** click en Edición #2 pasada → content re-fetchea, URL cambia con `?edition=`.
3. **Collapse rail:** click ‹‹ → rail se reduce a badges, tab bar se mantiene.
4. **Offer sin ediciones:** abrir oferta PRODUCTO → rail no visible, tabs sí.
5. **Landing split-button:** botón main label cambia según `landing_status`. Dropdown abre/cierra.
6. **Waitlist banner:** abrir oferta con waitlist > 0 y edición public → banner aparece. Click "Notificar" → loading → toast success.
7. **Clone modal:** botón `+ Nueva edición` → modal abre → selección + strategy + confirmar → crea + navega.
8. **Read-only edición pasada:** inputs bloqueados, banner read-only visible, CTA "Clonar" visible.

---

## 13. Implementation checklist

- [ ] `EditionsRail.tsx` — expanded variant con grouping + empty states
- [ ] `EditionsRailCollapsed.tsx` — badges con coloring semántico
- [ ] `LandingSplitButton.tsx` — 5 estados + dropdown menu
- [ ] `WaitlistBanner.tsx` — gradient + actions + show/hide logic
- [ ] `EditionCloneModal.tsx` — 3 strategies + conditional UI
- [ ] `OfferShell.tsx` — compose all children, rail visibility logic
- [ ] `OfferTabBar.tsx` — 4 tabs + landing button
- [ ] `OfferShellHeaderRow1.tsx` — title con edition suffix
- [ ] `OfferShellHeaderRow2.tsx` — remove landing button
- [ ] `use-offer-with-edition.ts` — resolve current edition hook
- [ ] `use-edition-waitlist.ts` — waitlist count hook
- [ ] Update `app/.../offer/[id]/page.tsx` — search params parsing
- [ ] Delete `/assets/page.tsx`, `/campaigns/page.tsx`, `/knowledge/page.tsx`
- [ ] Vitest tests for each component
- [ ] E2E smoke + regression tests

## 14. References

- Prototype HTML canónico: `docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/prototype/offer-studio/offer-info.html`
- Status/visibility color tokens: `prototype/styles.css`
- Architecture catalog: `backend/src/modules/offer/domain/archetype_catalog.py`
- LaunchEdition entity: `backend/src/modules/offer/domain/launch_edition.py`
