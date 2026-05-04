# 02-design-ui.md — Template (UX/UI)

> Owner: `/ux-ui`. Diseño UI completo para ui-story (o componente UI de mixed-story).
> Consume `01-spec.md` + skills (`brand-expert`, `frontend-expert`, `tessl__shadcn-ui`, `tessl__tailwind`).
> Si descubre edge cases nuevos durante diseño → propone `delta-spec.md` y /po ratifica antes de seguir.

---
story_id: STORY_ID
type: ui-story
designer: /ux-ui
ux_version: 1
last_modified: 2026-05-04T15:00Z
ratified_by_chris: false
links:
  spec: "01-spec.md"
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  brand_studio: "../../../../../product/modules/brand.md"          # si toca tokens marca
  design_tokens: "frontend/src/lib/tokens.ts"
---

## Resumen UX

[1 párrafo: qué experiencia se entrega, dónde vive en la app, cómo se accede.]

## Información architecture

### Ubicación en la app
- **Ruta:** `/[module]/[section]/[action]`
- **Sidebar entry:** [sí/no, dónde]
- **Breadcrumb:** [Home > Module > Section > Action]
- **Modal | Page | Drawer | Inline edit:** [decisión + razón]

### Entry points
- [Cómo llega el user a esta pantalla]
- [Triggers de copilot que abren esta vista]
- [Deep links si aplica]

## Layout + wireframe (ASCII o referencia HTML mockup)

```
┌─────────────────────────────────────────┐
│ Header / breadcrumb                     │
├─────────────────────────────────────────┤
│ ┌─────────┐  ┌────────────────────────┐ │
│ │ Side    │  │  Main content area     │ │
│ │ nav     │  │  - Form / list / cards │ │
│ │         │  │                        │ │
│ └─────────┘  └────────────────────────┘ │
└─────────────────────────────────────────┘
```

> O link a HTML mockup: `progress/mockup-{story-id}.html`

## Componentes (Shadcn UI + custom)

| Componente | Reutilizado o nuevo | Path | Notas |
|---|---|---|---|
| `<NoteForm>` | nuevo | `frontend/src/features/{module}/components/NoteForm.tsx` | RHF + Zod |
| `<DataTable>` | reutilizado | `frontend/src/components/shared/data-table.tsx` | filtros + ordenable |

## Estados de UI (state machine)

```
idle → loading → success
       loading → error → retry → loading
       loading → empty
```

| Estado | Componente | Comportamiento |
|---|---|---|
| `idle` | Form vacío | Botón submit deshabilitado |
| `loading` | Skeleton + spinner | Inputs disabled, "Guardando..." |
| `success` | Toast + redirect | Toast 3s, redirect a list |
| `error` | Inline + toast | Mostrar field errors + global toast retryable |
| `empty` | EmptyState component | CTA primario claro |

## Data flow

```
User input
  → React Hook Form (Zod schema)
  → useMutation (React Query)
  → fetchClient.post('/api/v1/...')
  → backend
  ← response
  → invalidate queries
  → toast + redirect
```

- **Hooks:** `use{Module}{Action}Mutation` en `frontend/src/features/{module}/api/use-{action}.ts`
- **Schema Zod:** `frontend/src/features/{module}/schemas/{action}-schema.ts`

## Responsive behavior

| Breakpoint | Layout | Notas |
|---|---|---|
| `< 768px` (mobile) | Single column, modal full-screen | |
| `768-1024px` (tablet) | 2-column | |
| `>= 1024px` (desktop) | 3-column con sidebar | |

## Accessibility

- Roles ARIA: `<form role="form">`, `<button aria-label="...">`
- Keyboard nav: Tab order definido, Esc cierra modal
- Focus management: trap en modal, return on close
- Color contrast: AA minimum (verificar tokens)
- Screen reader: labels asociadas, error announcement

## Microcopy (Spanish neutro)

| Elemento | Copy |
|---|---|
| Botón principal | "Guardar cambios" |
| Botón secundario | "Cancelar" |
| Empty state title | "Aún no tienes [recursos]" |
| Empty state CTA | "Crear primer [recurso]" |
| Success toast | "Cambios guardados" |
| Error generic | "Hubo un problema. Reintenta" |
| Validation required | "Este campo es obligatorio" |

## Telemetría / analytics

- Event: `{module}_{action}_submitted` con props `{tenant_id, success, duration_ms}`
- Event: `{module}_{action}_error` con props `{error_code, error_message}`
- Heatmap si aplica

## Brand voice

- Tone: [profesional / casual / cálido / directo según brand de tenant]
- Términos a usar: [glosario corto]
- Términos a evitar: [...]

## Spec deltas (si UX descubrió cambios al spec)

> Si vacío, /po no necesita re-ratificar.
> Si no vacío, /po revisa y mergea a `01-spec.md` antes de continuar.

- [ ] [Delta 1: scenario nuevo a agregar]
- [ ] [Delta 2: criterio refinado]

## Próximo paso

`→ /architect lee 01+02 → spawn /architect-{be,fe} paralelo (architect-agentic si mixed) → produce 03-arch-* y 04-tickets.yaml`
