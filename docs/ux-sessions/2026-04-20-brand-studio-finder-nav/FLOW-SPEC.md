# FLOW-SPEC — Brand Studio Finder-style Navigation

- **Date:** 2026-04-20
- **Scope:** Studio-scoped (Brand Studio)
- **Mode:** UX navigation redesign — homogenize the 3-column hierarchical layout to feel like macOS Finder.
- **Owner:** Chris
- **Prototype:** http://localhost:8888/

---

## 1. Audit Summary (quantitative)

| Metric | Value |
|---|---|
| Sections in Brand Studio | 12 (11 `SECTIONS` + `publico`/Buyer personas) |
| Route pattern | `/{tenantId}/brand-studio/{section}/[[...fieldId]]/page.tsx` |
| Layout owner | `UniversalEditableSection.tsx` (`components/form-runtime/`) |
| Sidebar owner | `BrandStudioNavRail.tsx` (`features/brand-studio/components/`) |
| Field list owner | `FieldList.tsx` (`components/form-runtime/`) |
| Detail owner | `FieldDetail.tsx` (`components/form-runtime/`) |
| Columns today | 3 (sidebar 240px / list 320px / detail flex) |
| Mobile breakpoint | 768px (collapses to list OR detail, not both) |

---

## 2. Current Navigation Map (Brand Studio only)

```
Sidebar (BrandStudioNavRail · 240px)
├── ✨ Buyer personas      → /brand-studio/publico
├── ─────── divider ───────
├── 🔒 Identidad           → /brand-studio/identity
├── 🎯 Posicionamiento     → /brand-studio/positioning            ← active in screenshot
├── 📜 Narrativa           → /brand-studio/narrative
├── 🚩 Metodología         → /brand-studio/methodology
├── 📄 Historia            → /brand-studio/story
├── 👥 Equipo              → /brand-studio/team
├── 🏛️ Autoridad           → /brand-studio/authority
├── 🎧 Testimonios         → /brand-studio/testimonials
├── 🎨 Visuales            → /brand-studio/visuals
├── 📚 Assets              → /brand-studio/communication-assets
└── 📣 Contacto            → /brand-studio/contact

Dentro de cada sección (UniversalEditableSection)
├── SessionHeader (full width, top)
└── Split
    ├── FieldList (w-80 desktop, rounded-md border)  ← "Propuesta de valor única" / "Discriminador" / …
    └── FieldDetail (flex-1, p-4, AutosaveBanner + EditableField)
```

### Observed homogeneity issues

1. **Column widths dispares** (240 / 320 / flex) no comunican jerarquía — un Finder tiene columnas de igual ratio y todas scrollean.
2. **`FieldList` envuelta en `rounded-md border`** (`FieldList.tsx:27`) — parece tarjeta suelta dentro de una columna, no columna hermana.
3. **`SessionHeader` ocupa todo el top** arriba del split (`UniversalEditableSection.tsx:98`) — fragmenta la jerarquía visual; Finder usa breadcrumb en topbar.
4. **Preview multi-línea** (label + 80 chars truncados, `FieldList.tsx:62`) compite con el título principal.
5. **Sin chevrón `›`** indicando que el item tiene sub-nivel.
6. **Sin gradiente de profundidad** entre columnas — todo `bg-muted/10` o plano.
7. **Col3 (detail) sin header propio** — aparece sin etiqueta, sin indicador de qué campo está editando (el label está dentro del form, no como column header).
8. **Dot de estado (filled/empty)** ausente — el usuario no ve a golpe de vista cuáles campos están completos.

---

## 3. Chosen Option — A+ (Finder Clásico + Inline Editor + Context Panel)

**Decisión 2026-04-20:** Chris elige base A (Finder Clásico) refinada con inline-editable en col3 + context panel lateral.

Prototipo: `prototype/option-a-enhanced.html`. Otros (A base, B, C, D) quedan como referencia histórica en el mismo folder.

### Layout final

Recomendaciones ABAJO (no al lado), colapsables — maximiza ancho del editor y evita saturación:

```
┌────────┬──────────┬──────────────────────────────────────────────┐
│        │          │ Topbar: Brand Studio › Pos › UVP         ✨ │
│        │          ├──────────────────────────────────────────────┤
│        │          │ Col3 editor                                  │
│ Studio │ Secciones│ ┌──────────────────────────────────────────┐ │
│ rail   │ 260px    │ │ Editor main (full ancho, max-w 860)     │ │
│        │          │ │ inline-editable textarea auto-grow      │ │
│        │          │ │ (ocupa 55%+ del alto)                   │ │
│        │          │ ├──────────────────────────────────────────┤ │
│        │          │ │ ✨ Recomendaciones · 6 · no obligatorias │ │ ← header 44px
│        │          │ │                               Mostrar ▾ │ │    siempre visible
│        │          │ ├──────────────────────────────────────────┤ │
│        │          │ │ Grid 2-col (expandido)                  │ │ ← max 45% alto
│        │          │ │ ┌──────────┐ ┌──────────┐               │ │    scrolleable
│        │          │ │ │ Fórmula  │ │ IA hint  │               │ │
│        │          │ │ └──────────┘ └──────────┘               │ │
│        │          │ │ ┌──────────┐ ┌──────────┐               │ │
│        │          │ │ │ Swipe    │ │ Trace    │               │ │
│        │          │ │ └──────────┘ └──────────┘               │ │
│        │          │ └──────────────────────────────────────────┘ │
└────────┴──────────┴──────────────────────────────────────────────┘
```

Estado colapsado por default: solo el header de 44px es visible, el editor absorbe el espacio.

### Inline-editable pattern (el corazón del refinamiento)

**Problema actual:** `TextareaInput.tsx` usa `rows={field.rows ?? 3}` — altura fija, scroll interno en campos largos (Historia, Origen de marca). Usuario no puede leer todo sin entrar al cursor.

**Solución:** textarea sin chrome cuando no focused, seamless transition a edit mode:

```tsx
// Minimal implementation, no external dep:
<textarea
  ref={taRef}
  value={value}
  onChange={(e) => { onChange(e.target.value); autoResize(taRef.current); }}
  className="inline-editable"
  style={{ overflow: 'hidden' }}  // critical: no internal scroll
/>
```

```css
.inline-editable {
  background: transparent;
  border: 1px solid transparent;
  resize: none;
  overflow: hidden;  /* auto-grow handles height */
}
.inline-editable:hover:not(:focus) {
  background: hsl(var(--muted) / 0.25);
  border-color: hsl(var(--border));
  cursor: text;
}
.inline-editable:focus {
  background: hsl(var(--background));
  border-color: hsl(var(--ring) / 0.5);
  box-shadow: 0 0 0 3px hsl(var(--ring) / 0.12);
}
```

```ts
// Auto-resize hook (15 líneas sin dep, o drop-in react-textarea-autosize):
function autoResize(el: HTMLTextAreaElement | null) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${el.scrollHeight}px`;
}
useLayoutEffect(() => autoResize(taRef.current), [value]);
```

**Alternativa recomendada:** `react-textarea-autosize` (Jed Watson, ~3kb gz, usado por Jira, Linear, Vercel). Dep battle-tested, SSR-safe, maneja edge cases (mobile virtual keyboard resize, Safari bugs). 1 línea de import. Preferir esta salvo que Chris prefiera evitar la dep.

### Recommendations panel (col3 bottom, collapsible)

Vive debajo del editor. Header sticky de 44px siempre visible + body colapsable. Responsive: 2-col grid ≥1100px, 1-col <1100px.

**Header (siempre visible):**
- Badge pill `✨ Recomendaciones` — color brand, comunica "ayuda opcional"
- Nota secundaria `N ayudas disponibles · no obligatorias` — refuerza que es opt-in
- Chip con count total
- Toggle `Mostrar ▾ / Ocultar ▴` a la derecha

**Estado por default:** colapsado. El usuario controla cuándo ver ayuda — reduce saturación.

**Body (cuando expandido):**
Grid de hasta 6 bloques opcionales driven por schema:

| Block | Field schema key | Siempre? | Hint tag |
|---|---|---|---|
| Fórmula | `field.formula` | No | Guía |
| Sugerencia IA | (lazy call al copilot) | Sí | IA |
| Ejemplos de referencia | `field.examples[]` | No | Swipe file |
| Dónde se usa | `field.downstream_uses[]` | No | Trazabilidad |
| Campos relacionados | `field.related_fields[]` | No | Contexto |
| Metadata | (auto: char count, last edit, length hint, tone) | Sí | Histórico |

Cada bloque lleva micro-tag de categoría en el header — usuario distingue naturaleza del contenido de un vistazo.

Renderizar solo bloques con data → panel nunca vacío ni saturado. Schema extensiones son backwards-compatible (todos los keys opcionales).

### State management

- **Collapse state:** recomendado global a Brand Studio via `localStorage["brand-studio.reco-expanded"] = boolean`. Persistente entre sesiones. Chris decide (pregunta abierta #2): per-field vs global.
- **Lazy IA hint:** solo llama al copilot cuando panel se expande la primera vez por field. Evita calls innecesarios. Cache por (fieldId + value hash).
- **Scroll behavior:** body del panel `overflow-y: auto`, `max-height: 45vh`. El editor arriba tiene su propio scroll independiente.

### Patrones comunes a las 4 opciones

- **Breadcrumb en topbar:** `Brand Studio › Posicionamiento › Propuesta de valor única` (reemplaza `SessionHeader`).
- **Gradiente de profundidad:** col más profunda = `bg-card` (ligeramente más claro en dark / más oscuro en light).
- **Dots de estado:** verde=filled, rojo atenuado=empty.
- **Chevrón `›` al final de row** cuando el ítem tiene sub-nivel.
- **Column header uniforme** (`fcol-header`): título uppercase + count.
- **Row height consistente** (~36px) entre col1 y col2.
- **`Autosave banner` inline con el input**, no flotante arriba.

---

## 4. Gap Analysis

| # | Finding | Category | Impact | Effort | Priority |
|---|---|---|---|---|---|
| 1 | `FieldList` parece card flotante, no columna | Architecture | H | L | P1 |
| 2 | Sin breadcrumb → usuario pierde rastro al entrar a detalle | Broken journey | M | L | P1 |
| 3 | Sin dots de estado → no se ve completitud sin leer cada ítem | Missing connection | M | L | P1 |
| 4 | Anchos dispares de columnas | Architecture | M | L | P2 |
| 5 | Falta gradiente de profundidad | Polish | L | L | P2 |
| 6 | Chevrón `›` ausente | Missing connection | L | L | P2 |
| 7 | Column headers inconsistentes | Architecture | L | L | P3 |
| 8 | Preview multi-línea compite con título | Polish | L | L | P3 |

---

## 5. File Changes Required (una vez elegida opción A/B/C/D)

### Archivos afectados (A+ · chosen)

**Capa 1 — Layout Finder (común a A y A+):**

| File | Change |
|---|---|
| `frontend/src/components/form-runtime/UniversalEditableSection.tsx` | Remove `SessionHeader` from top (breadcrumb va al topbar de layout.tsx). Normalize column widths (260/320/flex). |
| `frontend/src/components/form-runtime/FieldList.tsx` | Remove `rounded-md border` from `<ul>`. Flatten row: label + status dot + chevron. Remove multi-line preview. |
| `frontend/src/components/form-runtime/FieldDetail.tsx` | Add column header (field label + autosave status inline). |
| `frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx` | Width 260px. Add section-level completion indicator (`3/9`). Add chevron. |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx` (nuevo) | Topbar with breadcrumb (section + fieldId from params). |
| `frontend/src/features/brand-studio/components/BrandStudioBreadcrumb.tsx` (nuevo) | Lee params, resuelve labels desde section-catalog + schema. |

**Capa 2 — Inline editor (solo A+):**

| File | Change |
|---|---|
| `frontend/src/components/form-runtime/inputs/TextareaInput.tsx` | Swap `<Textarea>` → `<TextareaAutosize>`. Remove `rows` fixed. Add `inline-editable` class variant. |
| `frontend/src/components/form-runtime/inputs/TextInput.tsx` | Apply same `inline-editable` class variant (sin auto-grow, solo chrome). |
| `frontend/src/components/ui/inline-editable.tsx` (nuevo) | Shadcn-style wrapper, dark+light tokens. |
| `frontend/src/app/globals.css` | Add `.inline-editable` base styles (hover/focus transitions). |
| `package.json` | Add `react-textarea-autosize` (opcional — decisión pendiente). |

**Capa 3 — Context panel (solo A+):**

| File | Change |
|---|---|
| `frontend/src/components/form-runtime/FieldDetail.tsx` | Add right-side context panel (320px, hidden <1280px). |
| `frontend/src/components/form-runtime/FieldContextPanel.tsx` (nuevo) | Renderiza los 6 bloques opcionales desde schema. |
| `frontend/src/components/form-runtime/context-blocks/Formula.tsx` | Template renderer con slots. |
| `frontend/src/components/form-runtime/context-blocks/SwipeFile.tsx` | Lista de ejemplos de marcas. |
| `frontend/src/components/form-runtime/context-blocks/DownstreamUses.tsx` | Trazabilidad con links clickables. |
| `frontend/src/components/form-runtime/context-blocks/RelatedFields.tsx` | Cross-field navigation. |
| `frontend/src/components/form-runtime/context-blocks/Metadata.tsx` | Char count, last edit, length hint. |
| `frontend/src/components/form-runtime/context-blocks/AiHint.tsx` | Lazy copilot call via existing bridge. |
| `frontend/src/lib/form-runtime/schema.ts` | Extend `FieldSchema` with optional: `formula`, `examples`, `downstream_uses`, `related_fields`, `length_hint`. All backwards-compat. |

### Archivos NO afectados (opciones B/C/D descartadas)

- `app-sidebar.tsx` — sin cambios (no rail colapsado)
- `BrandCommandPalette.tsx` — no se crea
- `FieldPreview.tsx` separado — NO se crea (inline-editable cubre el caso)

---

## 6. New Components (si aplica)

- **`FinderColumn`** (shared primitive · opcional): encapsula `fcol-header` + `fcol-body` + scroll behavior. Evita duplicación entre NavRail, FieldList, FieldPreview.
- **`Breadcrumb`** (compartido): ya existe en Shadcn, usar.
- **`CompletionDot`**: tiny ui component — `filled | empty | pending`.

---

## 7. Prototype Reference

- URL: http://localhost:8888/ (Python `http.server` corriendo desde `prototype/`)
- Archivos:
  - `index.html` — landing con las 4 opciones + diagnóstico
  - `option-a-classic.html` — Finder clásico
  - `option-b-preview.html` — Preview pane
  - `option-c-rail-tree.html` — Icon rail + tree
  - `option-d-palette.html` — Command palette
  - `_shared.css` — tokens de diseño

Todos los prototipos incluyen switcher abajo para comparar sin perder contexto.

---

## 8. Next Steps

1. Chris elige una opción (o pide mezcla / variante adicional).
2. Actualizar `DECISIONS.md` con la elección.
3. Generar `UI-SPEC-{option}.md` específico.
4. Generar `PLAN.md` con fases.
5. Invocar `nicolify-frontend` o `nicolify-feature` con la carpeta de sesión.
