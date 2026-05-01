# UI-SPEC — PR-11-fe-primitives-and-contactos-page

> Owner: PM main session (Opus 4.7) — UX session ya hecha en `docs/ux-sessions/2026-04-29-crm-module-proposal/` (FLOW-SPEC + DECISIONS + prototype). Este UI-SPEC adapta a S4 lite scope. Frontend builder consume esto + CONTRACT.md.

## § 0 Source of truth

- `docs/ux-sessions/2026-04-29-crm-module-proposal/FLOW-SPEC.md` § 5.1 "Personas (Contact Database)" — capacidades full vision
- `docs/ux-sessions/2026-04-29-crm-module-proposal/DECISIONS.md` D1-D5 aceptadas
- **S4 lite scope** = "Personas básico" del FLOW-SPEC § 9 Fase 1 (2-3 sem)
- PI-3 expansion = full vision

## § 1 Layout — `/sales/contactos` (xl ≥1280px desktop)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ◀ Sidebar app (existing)                                                │
├─────────────────────────────────────────────────────────────────────────┤
│ Contactos                                                               │
│ Tu base completa. Filtra, busca y selecciona para crear segmentos…      │
├──────────────┬──────────────────────────────────────┬──────────────────┤
│              │ ┌──────────────────────────────────┐ │                  │
│  FILTROS     │ │ 🔍 Buscar nombre, email...       │ │  DRAWER DETAIL   │
│  (280px      │ └──────────────────────────────────┘ │  (Sheet 480px)   │
│   sticky)    │                                      │                  │
│              │ ┌──────────────────────────────────┐ │  Visible solo    │
│ Etapa        │ │ ☐ Nombre  Email     Tel.  Etapa  │ │  cuando user     │
│ ☐ Suscriptor │ ├──────────────────────────────────┤ │  click row.      │
│ ☐ Lead       │ │ ☐ Juan…   juan@x… +54 9 ✦Lead    │ │                  │
│ ☐ MQL        │ │ ☐ Ana…    -        +52 1 ✦MQL    │ │  ContactDetail   │
│ ☐ SQL        │ │ ☐ Pedro…  ped@y… -    ✦Customer  │ │  Content render  │
│ ☐ Cliente    │ │ ...                              │ │  inside Sheet    │
│ ...          │ └──────────────────────────────────┘ │                  │
│              │                                      │                  │
│ Score        │ ◀ 1 2 3 ... 10 ▶                     │                  │
│ ━━━●━━━●━━━  │ Mostrando 50 de 247                  │                  │
│ 40 — 80      │                                      │                  │
│              │                                      │                  │
│ Canales      │                                      │                  │
│ ☐ Telegram   │                                      │                  │
│ ☐ Email      │                                      │                  │
│ ☐ Phone      │                                      │                  │
│              │                                      │                  │
│ Otros        │                                      │                  │
│ ☐ Inactivos  │                                      │                  │
│ ☐ Recibió    │                                      │                  │
│   campaña    │                                      │                  │
│              │                                      │                  │
│ País         │                                      │                  │
│ ☐ AR ☐ MX    │                                      │                  │
│ ☐ CO ☐ PE    │                                      │                  │
│              │                                      │                  │
│ [Limpiar]    │                                      │                  │
├──────────────┴──────────────────────────────────────┴──────────────────┤
│ ✓ 3 contactos seleccionados        [Limpiar]          (no actions PR-11)│
└─────────────────────────────────────────────────────────────────────────┘
```

Bar bottom = `SelectedContactsBar` con `actions: []` PR-11. PR-12 inyecta "Crear segmento" como primera action.

## § 2 Responsive breakpoints

| Breakpoint | Layout |
|---|---|
| xl (≥1280px) | Sidebar 280px + Table flex + Drawer overlay 480px |
| lg (≥1024px) | Sidebar 240px + Table flex; Drawer overlay 90% width Sheet |
| md (≥768px) | Tabs Filtros/Tabla; Drawer = full-screen Sheet |
| sm (<768px) | Tabs Filtros/Tabla mobile; Drawer = full-screen Sheet, sticky bar bottom |

## § 3 Drawer detail (Sheet) — `ContactDetailContent` host-agnostic

```
┌──────────────────── DRAWER (Sheet right 480px) ──────┐
│ ❌ ✕                                                 │
│                                                      │
│ Juan García                                          │
│ ✦ Lead — Score 67  🔥 Hot                           │
│                                                      │
│ ─── Identidades ────────────────────────────────────│
│ ✉  juan@example.com  ★  verificado                  │
│ 📞 +54 9 11 1234-5678                               │
│ 💬 Telegram @juan_arg                               │
│                                                      │
│ ─── Scoring ───────────────────────────────────────│
│ Lead score:    67/100  ━━━━━━●━━━━                  │
│ Fit score:     72/100  ━━━━━━━●━━━                  │
│ Intent score:  60/100  ━━━━━●━━━━━                  │
│ Lifetime val.: $0                                   │
│                                                      │
│ ─── Actividad ─────────────────────────────────────│
│ Última: hace 2 días                                 │
│ Primera conversión: -                               │
│ Origen: instagram_dm                                │
│                                                      │
│ ─── Detalle ───────────────────────────────────────│
│ País: 🇦🇷 AR                                        │
│ Temperatura: HOT                                    │
│ Conversación: "Preguntó precio…"                    │
│                                                      │
│ ─── Traits ────────────────────────────────────────│
│ {expanded JSON key-value list}                      │
└──────────────────────────────────────────────────────┘
```

`ContactDetailContent` recibe solo `detail: ContactDetail | null` + `isLoading`. NO conoce su host.

## § 4 Filter panel detalle

Shadcn primitives map:
- Etapa multi-select → `<Popover>` con `<Command>` + `<CommandInput>` + `<CommandGroup>` + `<CommandItem>` (multi-check pattern)
- Score range → `<Slider>` dual con value labels
- Boolean checkboxes → `<Checkbox>` + `<Label>` inline
- País multi → `<Popover>` + `<Command>` con flag emoji + ISO code
- Reset button → `<Button variant="ghost">`
- Layout: `<ScrollArea>` para overflow

State pattern:
```typescript
const [filters, setFilters] = useState<ContactFilterParams>(initialFilters);

useEffect(() => {
  // debounce 300ms → router.replace con searchParams
  const t = setTimeout(() => syncToURL(filters), 300);
  return () => clearTimeout(t);
}, [filters]);
```

## § 5 SelectedContactsBar visual

```
┌────────────────────────────────────────────────────────────────────────┐
│ ✓ 3 contactos seleccionados   [actions slot ←PR-12 inyecta]  [Limpiar] │
└────────────────────────────────────────────────────────────────────────┘
```

- Sticky bottom 0
- Background: `bg-card` border-top
- Slide-up animation cuando `selectedIds.length` transiciona 0 → ≥1
- z-index `z-40` (drawer = z-50)

## § 6 Empty states

| Caso | Mensaje |
|---|---|
| Tabla vacía sin filtros | "Aún no tienes contactos. Conecta canales o importa una lista." |
| Tabla vacía con filtros | "Ningún contacto coincide. Ajusta filtros o limpia búsqueda." (con botón "Limpiar filtros") |
| Drawer cargando | Skeleton `<Skeleton>` Shadcn |
| Error API | Toast Sonner "No pudimos cargar contactos. Reintenta." |

## § 7 Accesibilidad (a11y)

- DataTable: `role="table"`, `<th scope="col">`, sortable headers `aria-sort`
- Checkboxes filas: `aria-label="Seleccionar {nombre}"`
- Drawer: `role="dialog" aria-labelledby="contact-detail-title"`
- Search input: `aria-label="Buscar contactos"`
- Bar: `role="region" aria-label="Acciones para contactos seleccionados"`
- Keyboard nav: `Tab` cycle filters → search → table → bar; `Esc` cierra drawer
- Focus trap dentro drawer cuando open

## § 8 Column tabla lite (S4 vs PI-3)

| Columna lite (S4) | PI-3 expansion |
|---|---|
| ☐ checkbox | mismo |
| Nombre (full_name) | mismo + avatar generado |
| Email (primary_email) | mismo |
| Teléfono (primary_phone) | mismo |
| Etapa (LifecycleStageChip) | mismo |
| Score (ScoreBadge) | + trend arrow ↑↓ |
| Última actividad (relative time) | mismo |
| Canales (icons row: 💬📞✉) | + count messages enviados |
| (no más) | + lifetime value, source, country, RFM segment |

PR-11 = 8 columnas. PI-3 puede ocultar/mostrar dinámicamente vía column-toggle UI.

## § 9 Skeleton loading

- Tabla: 10 rows skeleton mientras `isLoading`
- Drawer: 5 sections skeleton

## § 10 Toast feedback

- Errores carga API → Sonner toast destructive "No pudimos cargar contactos"
- Filtros aplicados (>10 results) → no toast (silent)
- Filtros vacíos resultado → no toast (empty state inline)

## § 11 Tailwind tokens (NO hardcoded colors)

Usar:
- `bg-background`, `bg-card`, `bg-muted`, `bg-accent`
- `text-foreground`, `text-muted-foreground`, `text-destructive`
- `border-border`, `border-input`
- Radix `data-[state=...]` patterns para Shadcn variants
- Lifecycle chip variants: usar `Badge` variant prop + Tailwind utility classes

NO hex hardcoded. NO `bg-[#xxx]`.

## § 12 Spanish neutro LATAM (final)

Strings clave:
- "Contactos" (no "Contacts")
- "Buscar nombre, email o teléfono…"
- "Mostrando {n} de {total}"
- "{n} contactos seleccionados"
- "Limpiar selección"
- "Limpiar filtros"
- "Etapa", "Score", "Canales", "País", "Otros"
- "Recibió campaña últimos 90d"
- "Inactivos"
- "Última actividad"
- "Sin actividad reciente"
- "Cargando contactos…"
- LifecycleStageChip labels: "Suscriptor / Lead / MQL / SQL / Oportunidad / Cliente / Evangelista / Churn"

## § 13 Out of scope UI (PI-3 expansion)

- Page completa `/sales/contactos/{id}` (S4 = drawer only)
- Timeline rich (BE 501 stub)
- Bulk actions avanzadas (export CSV, bulk update tags, etc.)
- Column resizing / reordering
- Saved filter views
- Search highlights inline
- Notes manuales
- Tags personalizados
- Stage manual override button
- Avatar generation
- Filter builder visual drag-drop
- Pulso (attention queue widget)
- Cards copilot integration

PI-3 expandirá UI **agregando** componentes. PR-11 forward-compat invariantes garantizan cero refactor.

---

<!-- @pm: UI-SPEC.md ready. Frontend builder puede consumir esto + CONTRACT.md TS contract directamente. Próximo paso: spawn nicolify-frontend cuando PR-10 BE merge. -->
