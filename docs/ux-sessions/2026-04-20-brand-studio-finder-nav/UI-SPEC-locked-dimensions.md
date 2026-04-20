# UI-SPEC · Dimensiones bloqueadas (Brand Studio Finder layout)

**Status:** locked · no deviation without new decision in `DECISIONS.md`
**Applies to:** opción A+ (finder + inline editor + reco panel) · todos los prototipos en `prototype/`
**Last verified against prototype:** 2026-04-20

Chris pidió explícitamente respetar estas medidas en la implementación. Son el contrato.

---

## 1. Shell (horizontal, de izquierda a derecha)

| Elemento | Width | Notas |
|---|---|---|
| Sidebar principal (studios) | **220px** fixed | `.sidebar-main` — logo + studios + config |
| Divider vertical | 1px `hsl(var(--border))` | entre columnas |
| Col 1 · Secciones | **260px** fixed | `.col-sections` — 12 secciones Brand Studio |
| Col 2 · Instancias (solo colecciones) | **280px** fixed | `.col-instances` — presente solo cuando la sección es colección (buyer personas, team, testimonials, authority). Ver §4. |
| Col 3 · Campos | **320px** fixed | `.col-fields` / `.col-items` — lista de fields de la sección o instancia |
| Col 4 · Editor | **flex: 1, min-width: 0** | absorbe el resto |

**Total mínimo horizontal** (sin col2 de colecciones): `220 + 260 + 320 + 560 (min editor) = 1360px`
**Con columna de colecciones:** `220 + 260 + 280 + 320 + 560 = 1640px`

Responsive: por debajo del mínimo, `.col-editor` se reduce pero NUNCA las otras columnas (son fixed). En móvil <768px se aplica colapso tipo drawer — no es objetivo de esta spec.

---

## 2. Vertical (arriba a abajo)

| Elemento | Height | Notas |
|---|---|---|
| Topbar (breadcrumb) | **48px** fixed | `.topbar` — flex align center, padding 0 20px |
| Demo switcher (solo prototipo) | 39px | NO llevar a producción |
| Column header (`.fcol-header`) | **44px** fixed | padding 12px/16px, h3 12px uppercase |
| Row (field o persona) | **~36px** (content-driven) | padding 9px 14px, font-size 13px |
| Persona row (col2 de colecciones) | **~62px** (content-driven) | avatar 38×38, body con name+role+status bar |
| Reco panel · colapsado | **44px** exact | solo header visible |
| Reco panel · expandido | **max 45%** del `.editor-wrap` | body con `overflow-y: auto` |
| Reco header | **44px** exact | badge + nota + count + toggle |

---

## 3. Paddings & spacing

| Elemento | Padding |
|---|---|
| Sidebar principal | 16px 12px |
| Column header | 12px 16px |
| Row (field/instance) | 9px 14px |
| Persona row | 12px 14px |
| Topbar | 0 20px |
| Editor main | **28px 40px 40px** (top · sides · bottom) |
| Reco header | 0 24px |
| Reco body | 4px 24px 24px |
| Reco block (card) | 16px 18px |
| Field-inline block gap (grid) | **24px 28px** (row · col) |
| Field label → input | 10px |
| Field input → hint | 10px (via `-4px 0 10px 2px` on hint) |
| Inline-editable padding | 12px 14px |

---

## 4. Editor content — full-width, left-aligned, grid responsive

```tsx
// Editor main structure (Chris-approved):
<div className="editor-main">
  <div className="editor-main-inner">  {/* width: 100%; NO max-width; NO margin auto */}
    <div className="field-grid">       {/* grid responsive */}
      <FieldInline width="w-full">...</FieldInline>    {/* spans full row */}
      <FieldInline width="w-half">...</FieldInline>    {/* spans 1 col in grid */}
      <FieldInline width="w-half">...</FieldInline>
    </div>
  </div>
</div>
```

### Grid breakpoints

| Viewport (editor area) | Columns |
|---|---|
| <900px | 1 col |
| 900–1499px | 2 cols |
| ≥1500px | 3 cols |

### Width hints per field (from schema)

| `field.layout` | Behavior | Cuándo usarlo |
|---|---|---|
| `full` (default for textarea/array) | `grid-column: 1 / -1` — always row-full | campos largos, textareas |
| `half` (default for text/url/email/number/enum/boolean) | `grid-column: span 1` | campos cortos, ideal pareados |
| `two-thirds` | `grid-column: span 2` en 3-col, else `full` | casos excepcionales |

Si el schema no declara `layout`, inferir del `type`:

```python
DEFAULT_LAYOUT = {
  "text": "half", "url": "half", "email": "half",
  "number": "half", "boolean": "half", "enum": "half",
  "textarea": "full", "array": "full", "custom": "full",
}
```

Es un hint. Extend `FieldSchema` con `layout?: 'full' | 'half' | 'two-thirds'` (backwards-compat).

---

## 5. Colecciones — cuándo aparece col 2 (instancias)

Una sección es **colección** cuando su valor es `array<Record>` y cada ítem es editable individualmente. Schema flag:

```python
# In SectionSchema:
{
  "slug": "publico",
  "label": "Buyer personas",
  "kind": "collection",          # ← NEW
  "instance_display": {
    "avatar_hint": "initial_or_image",
    "primary": "name",
    "secondary": "role",
    "status_field": "completion_pct",
  },
  "instance_fields": [...]       # same as fields, applied per-instance
}
```

Colecciones identificadas en Brand Studio (hoy):
- `buyer_personas` (publico) — avatar+name+role
- `team` — avatar+name+role
- `testimonials` — avatar+brand+snippet
- `authority_vault` — icon+type+label

Presets, identity, positioning, narrative, etc. → `kind: "singleton"` (3 cols, sin col instancias).

---

## 6. Persona row anatomy (col 2 de colecciones)

```
┌──────────────────────────────────────┐
│ [38px avatar] [name (13px bold)]    │  ← row 62px
│                [role (11px muted)]  │
│                [ ━━━━━━──── 18/22 ] │  ← status bar 60×3px
└──────────────────────────────────────┘
```

- Avatar: 38×38, border-radius 50%, tinted bg por color-hash del ID
- Status bar: 60px wide, 3px tall, fill color verde/amarillo/rojo según completitud (0–33% rojo, 34–79% amarillo, 80+% verde)
- CTA "Crear nueva persona" en top de la lista, border-dashed brand

---

## 7. Route & copilot contract

### Routes

```
/brand-studio/{section}                              → singleton, col2 = fields
/brand-studio/{section}/{fieldId}                    → singleton + field selected
/brand-studio/{section}/instance/{instanceId}        → collection, col2 = instances, col3 empty
/brand-studio/{section}/instance/{instanceId}/{fieldId}  → collection + field selected
```

Migración: las rutas actuales `/brand-studio/publico/persona/{personaId}/[[...fieldId]]/page.tsx` pasan a usar el patrón uniforme `/instance/{id}/{field}`. El segmento `persona` queda como alias por compatibilidad temporal — deprecar en siguiente sprint.

### Copilot contract (module_registry)

`ModuleDescriptor` for Brand Studio exponer:

```python
collections = {
  "buyer_personas": {
    "schema": buyer_persona_schema,
    "repository": BuyerPersonaRepository,
    "instance_label": lambda p: f"Buyer persona '{p.name}'",
  },
  "team": { ... },
  "testimonials": { ... },
  "authority_vault": { ... },
}
```

Route-based tool binding (navigation_map.py):

```python
ROUTE_TOOL_MAP["/brand-studio/{section}/instance/{instanceId}/{fieldId}"] = [
  "update_instance_field",          # generic: (section, instance_id, field_path, value)
  "create_instance",                # generic: (section, initial_values)
  "delete_instance",                # with soft-delete
  "suggest_field_value",            # IA, scoped to (section + instance_context + field)
  "clone_instance",
]
```

El copilot recibe contexto completo por URL params:
- `section = "publico"` (Brand Studio section)
- `collection = "buyer_personas"` (resolved from section schema)
- `instance_id = "alicia-uuid"`
- `field_id = "pain_primary"`
- Plus: **entire instance state** (para que la sugerencia IA sea contextual a Alicia, no genérica)

Este último punto es lo que hace la UX de 4 columnas valiosa: **el copilot no pierde contexto** al entrar a un campo. Sabe que está editando el dolor DE ALICIA, no un dolor abstracto — puede cross-referenciar sus otros fields (deseo, objeciones, día típico) para mejor sugerencia.

---

## 8. Tokens (exportar a Tailwind config + globals.css)

```ts
// Propuesta — agregar a tailwind.config o globals.css
const BRAND_STUDIO_TOKENS = {
  sidebarMainWidth: '220px',
  colSectionsWidth: '260px',
  colInstancesWidth: '280px',
  colFieldsWidth: '320px',
  topbarHeight: '48px',
  colHeaderHeight: '44px',
  rowHeight: '36px',
  personaRowHeight: '62px',
  recoHeaderHeight: '44px',
  recoMaxHeight: '45%',
  editorPadding: '28px 40px 40px',
  fieldGridGap: '24px 28px',
  fieldGridBreakpoint2: '900px',
  fieldGridBreakpoint3: '1500px',
};
```

Plasmar como CSS vars en `globals.css` bajo `:root`:

```css
:root {
  --brand-sidebar-main: 220px;
  --brand-col-sections: 260px;
  --brand-col-instances: 280px;
  --brand-col-fields: 320px;
  --brand-topbar-h: 48px;
  --brand-col-header-h: 44px;
  --brand-row-h: 36px;
  --brand-persona-row-h: 62px;
  --brand-reco-header-h: 44px;
  --brand-reco-max-h: 45%;
  --brand-editor-pad: 28px 40px 40px;
  --brand-field-grid-gap-row: 24px;
  --brand-field-grid-gap-col: 28px;
}
```

Implementación debe referenciar siempre estos tokens, nunca números inline. Cualquier cambio pasa por este UI-SPEC.

---

## 9. Acceptance checklist (para implementation phase)

- [ ] Todos los widths fixed matchean valores arriba (medir con DevTools)
- [ ] Editor main sin `max-width`, `margin: 0 auto`, ni `center` — siempre full-width left-aligned
- [ ] Field grid colapsa/expande en 900px y 1500px exactos
- [ ] `.w-full` respeta grid-column: 1 / -1 en todas las columnas
- [ ] Buyer personas renderiza 4 columnas con col instances de 280px
- [ ] Reco panel colapsado exactamente 44px, expandido max 45% del `.editor-wrap`
- [ ] Row height 36px para fields, 62px para personas
- [ ] Status bar en persona row: 60×3px, colores por umbral 33/80
- [ ] Avatar persona: 38×38, border-radius 50%, tinted bg
- [ ] Copilot recibe instance context en URL params + en ModuleDescriptor
- [ ] Routes migran al patrón `/instance/{id}/{field}` uniforme para todas las colecciones

---

## 10. Prototipos de referencia

- `prototype/option-a-enhanced.html` — singleton (3 cols, grid multi-campo en demo "Identidad")
- `prototype/option-a-personas.html` — collection (4 cols, demo buyer personas con Alicia/Bruno/Carla)
