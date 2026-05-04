# UI Spec: Offer Narrative Fields — TextareaInput (newline_array) + Objections Editor

**Status:** Ready to implement
**Contract ref:** `docs/contracts/offer-narrative-fields-CONTRACT.md` §§9–11
**Date:** 2026-04-24
**Implements:** Bug fix — OFFER_LEVEL sections (`identity`, `promise`, `strategy`, `psychology`, `closing`) showing placeholders because FE schema paths pointed to nonexistent fields.

---

## 1. Resumen

Dos componentes frontend desbloquean las secciones OFFER_LEVEL del offer-studio que mostraban placeholders por rutas incorrectas:

1. **`TextareaInput` extendido con `storeAs: "newline_array"`** — convierte entre un textarea de texto libre (una línea = un elemento) y un `string[]` en el store. Elimina la necesidad de parsers ad-hoc desperdigados; el renderer unifica el contrato en un solo lugar. Se usa en 8 campos: `measurable_outcomes`, `target_avatar_match`, `marketing_pain_points`, `marketing_desires`, `anti_avatar_keywords`, `cultural_trust_barriers`, `emotional_triggers`, `status_drivers`, `regret_scenarios`, `urgency_drivers`.

2. **`ObjectionsArrayInput`** — componente custom que reemplaza el campo `objections_raw` (textarea libre sin estructura) por un editor de cards estructuradas (`type` + `trigger_phrases` + `rebuttal`), más un flujo bulk-paste-AI ("Pegar lista y estructurar con IA") que invoca el tool copilot `structure_objections`. La estrategia (`strategy`) se auto-completa en función del `type` seleccionado y queda visible como dropdown compacto en el header del card.

---

## 2. Componente 1: TextareaInput con `storeAs: "newline_array"`

### 2.1 Archivos afectados

| Archivo | Cambio |
|---|---|
| `frontend/src/lib/form-runtime/schema/types.ts` | Agregar `storeAs?: "newline_array"` a `FieldSchema` |
| `frontend/src/components/form-runtime/inputs/TextareaInput.tsx` | Extender para manejar branch `storeAs === "newline_array"` |

### 2.2 Contrato de transformación

```
BE → UI (mount):
  string[] | null | undefined
    → filter(Boolean) → join("\n")
    → "" si vacío (placeholder visible)

UI → BE (onChange):
  string (raw textarea)
    → split("\n")
    → map: replace(/^[\s•·\-\*]+/, "").trim()   ← limpia bullets • - * al inicio
    → filter(line => line.length > 0)
    → string[]

Blur con "" → persiste []  (NO null — columnas JSONB NOT NULL DEFAULT '[]')
Blur con "abc" → persiste ["abc"]
```

### 2.3 Props interface TypeScript

```ts
// Extensión de FieldSchema en types.ts:
storeAs?: "newline_array";
// Solo válido con type === "textarea". Ignorado en otros tipos.

// El componente acepta el tipo union:
BaseInputProps<string | string[] | null>
// - Si storeAs omitido: value es string, onChange(string)
// - Si storeAs === "newline_array": value es string[] | null, onChange(string[])
```

### 2.4 Comportamiento por estado

| Estado | Valor BE | Render UI | Nota |
|---|---|---|---|
| Empty / null | `null` o `[]` | `""` con placeholder visible | `InlineEditableTextarea` ya maneja esto |
| Focused (vacío) | `[]` | cursor visible, placeholder desaparece | comportamiento nativo |
| Focused (con data) | `["a","b","c"]` | `"a\nb\nc"` | join on mount, editable |
| Filled | `["precio","tiempo","confianza"]` | textarea con 3 líneas visibles | auto-height via TextareaAutosize |
| Bullet prefix | `["• precio"]` (pegado) | limpia a `["precio"]` on onChange | regex `/^[\s•·\-\*]+/` |
| Error validación | campo `required: true` y value=`[]` | borde `border-destructive`, ring rojo | heredado de `InlineEditableTextarea` |
| Disabled | — | opacidad 60%, cursor not-allowed | prop `disabled` forwarded |

### 2.5 Tokens visuales

Hereda todos los tokens de `InlineEditableTextarea` (definidos en `frontend/src/components/ui/inline-editable.tsx`):

| Token | Valor actual | Rol |
|---|---|---|
| Padding | `px-[14px] py-3` | espacio interno estándar |
| Border default | `border-transparent` | seamless cuando no activo |
| Border hover | `border-border` | affordance sutil |
| Border focused | `border-ring/50` | ring primario |
| Ring focused | `ring-2 ring-ring/20` | halo de foco |
| Background focused | `bg-background` | eleva el campo del contexto card |
| Font | `text-base leading-relaxed` (tone="default") | legibilidad en mobile |
| Placeholder | `italic text-muted-foreground/70` | voz editorial guía |
| Disabled | `opacity-60 cursor-not-allowed` | feedback de estado |

**No se añaden tokens nuevos.** El diseño es consistente con todos los demás textarea del offer-studio.

### 2.6 ARIA

| Atributo | Valor | Fuente |
|---|---|---|
| `aria-required` | `field.required` | ya presente en TextareaInput actual |
| `aria-describedby` | `{field.id}-hint` si `field.hint` existe | el runtime `FieldLabelWithHelp` ya inyecta este id |
| `aria-multiline` | `"true"` | implícito en `<textarea>` |
| `aria-label` | via `<label>` en `FieldLabelWithHelp` | no duplicar aquí |

### 2.7 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│ Resultados medibles *                               [?] hint icon   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ · Logra [X métrica] en [Y días]                                 │ │  ← placeholder italic muted
│ │ · Aumenta [Z] de [A] a [B]                                      │ │
│ │ · Reduce [tiempo/costo] en [%]                                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  FOCUSED STATE:                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │▌Agenda llena en 30 días                                         │ │  ← valor real, auto-height
│ │ Factura USD 40 por consulta (subió desde USD 15)                │ │
│ │ Primera venta de contenido digital en 6 semanas                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│  ↑ bg-background border-ring/50 ring-2 ring-ring/20               │
│                                                                     │
│  Hint: "Una por línea. Resultados concretos con números cuando     │
│  aplique. El agente los cita para justificar el precio."           │
└─────────────────────────────────────────────────────────────────────┘

ESTADOS:
  empty  → border-transparent bg-transparent  placeholder italic
  hover  → border-border bg-muted/25  cursor-text
  focus  → border-ring/50 bg-background ring-2 ring-ring/20
  error  → border-destructive ring-destructive/20  (+ aria-invalid)
  filled → border-transparent bg-transparent  text normal
  disabled → opacity-60 cursor-not-allowed
```

### 2.8 Responsive

El componente no tiene layout propio — es un input en línea dentro de la grilla del `UniversalEditableSection`. La grilla ya maneja breakpoints. `TextareaAutosize` crece verticalmente en todos los viewports sin overflow horizontal.

---

## 3. Componente 2: Objections Editor (cards + bulk-paste-AI)

### 3.1 Decisión de arquitectura: componente custom vs extensión del form-runtime

**Decisión:** Componente custom `ObjectionsArrayInput` registrado como `type: "custom"` en `psychology.schema.ts` mediante el action registry del form-runtime (`field.action = "objections-editor"`).

**Justificación:** El flujo bulk-paste-AI (`bulkPasteHelper`) no existe en el contrato genérico de `ArrayCardsEditor`. Introducirlo en el runtime genérico agregaría una prop no-genérica a un componente que debe ser agnóstico del dominio. El componente custom mantiene el bulk-paste como concern del offer-studio mientras hereda `ArrayCardsEditor` para el rendering de items.

**Alternativa descartada:** Extender `FieldSchema` con `bulkPasteHelper` config genérica. Viable a futuro si más de 2 arrays necesitan el patrón. Por ahora: un componente custom limpio > una abstracción prematura.

### 3.2 Archivos

| Archivo | Cambio |
|---|---|
| `frontend/src/features/offer-studio/components/psychology/ObjectionsArrayInput.tsx` | Nuevo — componente custom principal |
| `frontend/src/features/offer-studio/components/psychology/BulkPasteSheet.tsx` | Nuevo — Sheet lateral para bulk-paste flow |
| `frontend/src/features/offer-studio/actions/registry.ts` | Registrar `"objections-editor"` → `ObjectionsArrayInput` |
| `frontend/src/features/offer-studio/schemas/psychology.schema.ts` | Cambiar field `objections` de `type: "textarea"` a `type: "custom", action: "objections-editor"` |

### 3.3 Schema entry en `psychology.schema.ts`

```ts
{
  id: "objections",
  label: "Objeciones típicas del lead",
  type: "custom",
  path: "objections",
  action: "objections-editor",
  hint: "Las frases reales que escuchan tus prospectos antes de no cerrar. El agente las detecta en el chat y responde con el argumento correspondiente.",
}
```

### 3.4 Sub-fields visibles del card (conformidad con `form-runtime-array.md`)

La regla exige ≤3 sub-fields para cards mode. Los 4 campos del domain `ObjectionItem` se distribuyen así:

| Campo | Visible en card | Tipo render | Nota |
|---|---|---|---|
| `type` | Sí — header del card | `Select` (Shadcn) | Opciones mapeadas a labels (ver §3.8) |
| `strategy` | Sí — header del card (compacto) | `Select` pequeño, `ghost` variant | Auto-completa al cambiar `type`; editable |
| `trigger_phrases` | Sí — body del card | `TextareaInput storeAs:"newline_array"` | 2 rows mínimo |
| `rebuttal` | Sí — body del card | `InlineEditableTextarea` | 3 rows mínimo |

**Conteo de sub-fields visibles en el body: 2** (`trigger_phrases` + `rebuttal`). `type` y `strategy` aparecen en el header del card, no en el body expandido. El `ArrayCardsEditor` base mapea los fields del itemSchema al body. Para el header custom, `ObjectionsArrayInput` renderiza su propio header row con `type` y `strategy`.

Esto cumple el espíritu de la regla: el body expandido tiene ≤3 campos, sin abrumar el viewport.

### 3.5 ASCII Wireframe — estado con items

```
┌────────────────────────────────────────────────────────────────────┐
│  Objeciones típicas del lead                          ╔══════════╗ │
│  Las frases reales que escuchas de prospectos         ║  3 ítems ║ │
│                                           [↑] [↓ todo] ╚══════════╝ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ ≡  ›  01  [Precio ▾]  [ROI Reframing ▾]   [⧉] [✕]          │ │  ← expandido
│  │ ────────────────────────────────────────────────────────────  │ │  border-primary/50
│  │                                                               │ │
│  │  Frases que la disparan (una por línea)                      │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │ es mucho dinero para mí                               │   │ │
│  │  │ no sé si puedo pagarlo                                │   │ │
│  │  │ no tengo el presupuesto ahorita                       │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  Respuesta del agente                                        │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │ Entiendo perfectamente — es una inversión, no un      │   │ │
│  │  │ gasto. En 30 días vas a recuperar [X]…                │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ ≡  ›  02  [Tiempo ▾]  [Time Reallocation ▾]  [⧉] [✕]       │ │  ← colapsado
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ ≡  ›  03  [Confianza ▾]  [Risk Reversal ▾]   [⧉] [✕]       │ │  ← colapsado
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  [+ Agregar manual]        [⚡ Pegar lista y estructurar con IA]  │
└────────────────────────────────────────────────────────────────────┘

LEYENDA HEADER ROW:
  ≡  = drag handle (ArrayDragHandle)
  ›  = chevron collapse/expand (rotate 90° cuando expandido)
  01 = número monospace
  [Precio ▾] = Select tipo (width fijo ~110px)
  [ROI Reframing ▾] = Select estrategia (ghost variant, width fijo ~160px)
  [⧉] = Duplicar (Tooltip "Duplicar")
  [✕] = Eliminar (Tooltip "Eliminar", destructive icon)
```

### 3.6 ASCII Wireframe — estado vacío

```
┌────────────────────────────────────────────────────────────────────┐
│  Objeciones típicas del lead                           0 ítems     │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                                                              │ │
│  │   Sin objeciones todavía.                                    │ │
│  │   Agrega manualmente o pega tu lista para estructurar.       │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  [+ Agregar manual]        [⚡ Pegar lista y estructurar con IA]  │
└────────────────────────────────────────────────────────────────────┘
```

### 3.7 Bulk-paste Sheet — flujo completo

El componente usa `Sheet` (no `Dialog`) porque:
- En mobile ocupa el 90% de la pantalla desde abajo sin interrumpir el scroll del formulario.
- En desktop abre como panel lateral (side="right") sin bloquear el contenido principal.
- El patrón `Sheet` ya existe en `frontend/src/components/ui/sheet.tsx`.

#### ASCII Wireframe — Sheet abierto

```
  ←──────────── SHEET (side="right", w-[400px] lg:w-[480px]) ───────────→

  ┌──────────────────────────────────────────────────────────────────────┐
  │ Pegar lista y estructurar con IA                              [  ✕ ] │
  │ ─────────────────────────────────────────────────────────────────── │
  │                                                                      │
  │ Pega objeciones, una por línea. Pueden ser frases de prospectos      │
  │ reales, notas de llamadas, mensajes de WhatsApp.                     │
  │                                                                      │
  │ ┌──────────────────────────────────────────────────────────────────┐ │
  │ │ No tengo presupuesto para esto ahora                             │ │
  │ │ Tengo que consultarlo con mi marido primero                      │ │
  │ │ Ya probé algo similar y no me funcionó                           │ │
  │ │ ¿Y si no me resulta? ¿hay devolución?                           │ │
  │ │ Es mucho dinero para mí en este momento                         │ │
  │ │ Prefiero esperar al próximo año                                  │ │
  │ │                                                                  │ │
  │ └──────────────────────────────────────────────────────────────────┘ │
  │  6 líneas detectadas                                                 │
  │                                                                      │
  │   [Cancelar]                    [⚡ Estructurar con IA   →  ]       │
  │                                                                      │
  └──────────────────────────────────────────────────────────────────────┘

  ESTADO CARGANDO (reemplaza footer):
  │   ████████████████████████████░░░░░░░░   Estructurando con IA...   │
  │   (Progress indeterminado + spinner en el botón, texto "Procesando")│

  ESTADO ERROR (reemplaza footer):
  │   [!] No pudimos estructurar. Revisa que sean frases claras,        │
  │       una por línea.                  [Reintentar]                  │
```

#### Flow step-by-step

1. Usuario hace click en "Pegar lista y estructurar con IA" → `setSheetOpen(true)`.
2. Sheet abre. Textarea grande vacío con placeholder de ejemplo.
3. Usuario pega texto. Contador de líneas actualiza en tiempo real (`lines.filter(l => l.trim()).length`).
4. Botón "Estructurar con IA" habilitado cuando ≥2 líneas no vacías.
5. Click → `isPending = true` → `fetchClient.post('/api/v1/copilot/tools/structure_objections', { raw_text })`.
6. Loading: botón disabled + spinner + Progress indeterminado en el footer.
7. **Success:** la respuesta llega como `{ draft_fields: { objections: [...] } }` (card proposal del copilot vía `_ok_response`).
   - El componente aplica `onChange([...existingItems, ...proposedItems])` — merge, no reemplazo, para preservar items manuales ya ingresados.
   - Sheet cierra. Toast: "Objeciones estructuradas. Revisa y ajusta según tu conocimiento."
8. **Error:** muestra inline error en el footer del Sheet. Sheet no cierra. Usuario puede reintentar.

**Nota de integración:** CONTRACT §11.1 define que `structure_objections` devuelve el patrón `_ok_response` del copilot con `draft_fields.objections`. En v1, el componente aplica directamente el resultado sin pasar por el flujo `propose_field_updates` del copilot (que requiere navegación al panel copilot). Justificación: el usuario abre explícitamente el Sheet y presiona "Estructurar" — hay consentimiento explícito y el contexto es claro. El flujo `propose_field_updates` es para sugerencias iniciadas por el copilot sin acción del usuario.

### 3.8 type → strategy default mapping

Este mapeo es determinístico client-side. El componente lo aplica en `useEffect([type])`:

| `type` value | Label display | `strategy` default | Label strategy display |
|---|---|---|---|
| `"price"` | Precio | `"ROI Reframing"` | ROI Reframing |
| `"time"` | Tiempo | `"Time Reallocation"` | Reorganización de tiempo |
| `"trust"` | Confianza | `"Risk Reversal + Guarantee"` | Reversal de riesgo |
| `"partner"` | Tengo que consultarlo | `"Decision Facilitator"` | Facilitación de decisión |
| `"custom"` | Otra | `""` | — (editable por el usuario) |

**Regla de aplicación del auto-complete:**
- Solo se aplica si `item.strategy === ""` o `item.strategy === undefined` en el momento del cambio de `type`.
- Si el usuario ya editó manualmente la estrategia, NO se sobreescribe (respeta la intención del usuario).
- El select `strategy` siempre es editable manualmente, independientemente del auto-complete.

**Labels de estrategia (display solo):** los valores de `strategy` son strings libres (no un enum cerrado). El select muestra las 5 opciones comunes como sugerencias; el usuario puede escribir una estrategia custom si elige `type: "custom"` o si quiere nombrar su propia técnica. En v1, las opciones del Select de strategy se limitan a los 4 defaults + vacío + "Otra (escribir)".

### 3.9 Estados del componente

| Estado | Qué muestra |
|---|---|
| `value = []` o `value = null` | Empty state: texto "Sin objeciones todavía. Agrega manualmente o pega tu lista para estructurar." + 2 CTAs |
| `value.length > 0` | Cards apilados, 1 expandido a la vez (hereda `ArrayCardsEditor`) |
| Sheet cerrado | Solo CTAs al pie del contenedor |
| Sheet abierto + vacío | Textarea placeholder, botón disabled |
| Sheet abierto + ≥2 líneas | Botón "Estructurar" habilitado, contador de líneas |
| Sheet cargando | Progress indeterminado, botón disabled "Procesando..." |
| Sheet error | Alert destructive inline, botón "Reintentar" |
| Item sin `type` | Badge `FALTA tipo` (ArrayItemBadge status "required-type") |
| Item sin `rebuttal` | Badge `FALTA respuesta` |
| Item completo | Badge `OK` (check verde) |

### 3.10 Shadcn Components Used

| Componente | Import path | Uso |
|---|---|---|
| `Card` | `@/components/ui/card` | Contenedor general del array editor |
| `Button` | `@/components/ui/button` | CTAs: "Agregar manual", "Pegar lista y estructurar con IA", "Estructurar", "Cancelar", "Reintentar" |
| `Select`, `SelectTrigger`, `SelectContent`, `SelectItem`, `SelectValue` | `@/components/ui/select` | Tipo de objeción + estrategia |
| `Sheet`, `SheetContent`, `SheetHeader`, `SheetTitle`, `SheetDescription`, `SheetFooter`, `SheetClose` | `@/components/ui/sheet` | Bulk-paste panel |
| `Textarea` | `@/components/ui/textarea` | Textarea grande en BulkPasteSheet |
| `Progress` | `@/components/ui/progress` | Loading indeterminado en Sheet |
| `Badge` | `@/components/ui/badge` | Contador "N ítems" en ArrayFieldHeader |
| `Tooltip`, `TooltipContent`, `TooltipTrigger`, `TooltipProvider` | `@/components/ui/tooltip` | Botones icon-only: duplicar, eliminar |
| `Separator` | `@/components/ui/separator` | Línea entre header y body del card expandido |
| `Alert`, `AlertDescription` | `@/components/ui/alert` | Error state en Sheet footer |

**Componentes del array runtime reutilizados (no son Shadcn, son del proyecto):**

| Componente | Path | Uso |
|---|---|---|
| `ArrayDragHandle` | `./array/array-drag-handle` | Handle de arrastre por item |
| `ArrayItemActions` | `./array/array-item-actions` | Duplicar + eliminar por item |
| `ArrayItemBadge` | `./array/array-item-badge` | Badge OK / FALTA X |
| `ArrayFieldHeader` | `./array/array-field-header` | Header con contador y colapsar/expandir todo |
| `ArrayAddButton` | `./array/array-add-button` | Botón "+ Agregar manual" |
| `InlineEditableTextarea` | `@/components/ui/inline-editable` | Campos trigger_phrases y rebuttal |

---

## 4. type → strategy Mapping Table (copy-paste literal para implementación)

```ts
// frontend/src/features/offer-studio/components/psychology/ObjectionsArrayInput.tsx

export const OBJECTION_TYPE_TO_DEFAULT_STRATEGY: Record<string, string> = {
  price: "ROI Reframing",
  time: "Time Reallocation",
  trust: "Risk Reversal + Guarantee",
  partner: "Decision Facilitator",
  custom: "",
};

export const OBJECTION_TYPE_LABELS: Record<string, string> = {
  price: "Precio",
  time: "Tiempo",
  trust: "Confianza",
  partner: "Tengo que consultarlo",
  custom: "Otra",
};

export const OBJECTION_STRATEGY_LABELS: Record<string, string> = {
  "ROI Reframing": "ROI Reframing",
  "Time Reallocation": "Reorganización de tiempo",
  "Risk Reversal + Guarantee": "Reversal de riesgo",
  "Decision Facilitator": "Facilitación de decisión",
};

// Opciones del Select de tipo (en orden de frecuencia)
export const OBJECTION_TYPE_OPTIONS = [
  { value: "price", label: "Precio" },
  { value: "time", label: "Tiempo" },
  { value: "trust", label: "Confianza" },
  { value: "partner", label: "Tengo que consultarlo" },
  { value: "custom", label: "Otra" },
] as const;

// Opciones del Select de estrategia (sugerencias comunes + vacío)
export const OBJECTION_STRATEGY_OPTIONS = [
  { value: "ROI Reframing", label: "ROI Reframing" },
  { value: "Time Reallocation", label: "Reorganización de tiempo" },
  { value: "Risk Reversal + Guarantee", label: "Reversal de riesgo" },
  { value: "Decision Facilitator", label: "Facilitación de decisión" },
  { value: "custom_strategy", label: "Estrategia personalizada" },
] as const;
```

---

## 5. Data Flow E2E

```
psychology.schema.ts
  └── field: {
        id: "objections",
        type: "custom",
        path: "objections",
        action: "objections-editor"
      }
                │
                ▼
  form-runtime renderer:
    type === "custom" → look up action registry
    action === "objections-editor" → ObjectionsArrayInput
                │
                ▼
  ObjectionsArrayInput ("use client")
    ├── state: expandedIndex (card seleccionado)
    ├── state: sheetOpen (bulk-paste Sheet)
    │
    ├── FLUJO MANUAL:
    │   User edita campo en card
    │     → updateItem(index, patch)
    │     → onChange(nextItems)           ← propaga al form-runtime
    │     → useAutoSave debounce 800ms    ← vive en el runtime, no aquí
    │     → PATCH /api/v1/offer/{id}      ← con { objections: [...] }
    │     → Autosave indicator actualiza
    │
    └── FLUJO BULK-PASTE:
        User click "Pegar lista y estructurar"
          → setSheetOpen(true)
          BulkPasteSheet abre
          User pega texto → setRawText(text)
          User click "Estructurar con IA"
            → fetchClient.post('/api/v1/copilot/tools/structure_objections',
                               { raw_text: text })
            → isPending = true (progress + disable)
            → Respuesta: { draft_fields: { objections: ObjectionItem[] } }
            → merge: onChange([...currentItems, ...proposedItems])
            → setSheetOpen(false)
            → toast.success("Objeciones estructuradas. Revisa y ajusta.")
          En error:
            → setError(message)
            → Sheet permanece abierto
            → Botón "Reintentar" visible

AUTOSAVE invariant:
  ObjectionsArrayInput nunca llama save directamente.
  Solo llama `onChange(nextItems)` que el runtime recibe y
  pasa por useAutoSave (debounce 800ms → PATCH).
  No hay botón "Guardar" en ningún lugar del componente.
```

---

## 6. Accessibility Checklist

### Componente 1: TextareaInput newline_array

- [x] `aria-required={field.required}` — ya presente, se preserva
- [x] `aria-describedby="{field.id}-hint"` — el runtime inyecta el id en `FieldLabelWithHelp`; el renderer no necesita declararlo
- [x] Foco visible: `focus:ring-2 ring-ring/20` en `InlineEditableTextarea`
- [x] Texto de placeholder informativo (no solo "Escribe aquí") — especificado en schemas
- [x] `aria-multiline="true"` implícito en `<textarea>`
- [x] Resize: `resize-none` + auto-height via `TextareaAutosize` — sin scrollbar interno

### Componente 2: ObjectionsArrayInput

- [x] Cada card: `role="group"` + `aria-label="Objeción {N}: {typeLabel}"` — en el div contenedor del card
- [x] Drag handle: `aria-label="Mover objeción {N}"` + `tabIndex={0}` + soporte teclado Space/Enter para activar, arrow keys para mover (hereda `ArrayDragHandle`)
- [x] Botón collapse/expand: `aria-expanded={isExpanded}` + `aria-controls="{id}-body"`
- [x] Botón "Duplicar": `aria-label="Duplicar objeción {N}"` (Tooltip + aria-label, visible solo en hover/focus)
- [x] Botón "Eliminar": `aria-label="Eliminar objeción {N}"` + `aria-describedby` hacia el texto del ítem
- [x] Select tipo: `<label>` asociado vía `htmlFor` + `aria-label="Tipo de objeción"` en `SelectTrigger`
- [x] Select estrategia: `aria-label="Estrategia de respuesta"` en `SelectTrigger`
- [x] CTA "Pegar lista": `aria-describedby="{field.id}-hint"` para describir el propósito
- [x] Sheet: `SheetTitle` visible + `SheetDescription` como subtítulo
- [x] Textarea en Sheet: `aria-label="Lista de objeciones para estructurar"` + `aria-describedby` hacia las instrucciones
- [x] Botón "Estructurar": `aria-disabled={lines < 2}` + Tooltip explicativo cuando disabled
- [x] Progress loading: `role="status"` + `aria-live="polite"` + texto "Estructurando con IA…"
- [x] Error en Sheet: `role="alert"` vía `Alert` component (Shadcn maneja esto)
- [x] Toast success: `aria-live="polite"` vía `sonner` (Shadcn)

---

## 7. Latam Neutro — Verify (Español Neutro sin Voseo)

Lista completa de strings user-facing. Todos verificados contra `.claude/rules/spanish-text.md`.

### Labels de campo

| Texto | Corrección aplicada |
|---|---|
| "Objeciones típicas del lead" | OK |
| "Tipo" | OK |
| "Estrategia" | OK |
| "Frases que la disparan (una por línea)" | OK (no "Frases que la disparan") |
| "Respuesta del agente" | OK |

### Placeholders

| Campo | Placeholder | Verificación |
|---|---|---|
| `trigger_phrases` | "• Está muy caro\n• No tengo el presupuesto ahora" | OK — "ahora" no "ahorita" (regional MX); ambos OK; preferir neutro |
| `rebuttal` | "Entiendo perfectamente. Si en 30 días no ves [resultado]…" | OK — "ves" no "ves vos" |
| BulkPasteSheet textarea | "No tengo presupuesto para esto\nTengo que consultarlo primero\nYa probé algo similar y no me funcionó\n¿Hay devolución si no me resulta?" | OK — tuteo neutro |

### Botones y CTAs

| Texto actual | Estado |
|---|---|
| "Agregar manual" | OK (no "Agregá") |
| "Pegar lista y estructurar con IA" | OK (no "Pegá") |
| "Estructurar con IA" | OK |
| "Cancelar" | OK |
| "Reintentar" | OK |
| "Aceptar" | OK (si aplica en contexto de propuesta) |

### Mensajes de estado

| Texto | Estado |
|---|---|
| "Sin objeciones todavía. Agrega manualmente o pega tu lista para estructurar." | OK (no "Agregá", no "pegá") |
| "Estructurando con IA..." | OK |
| "No pudimos estructurar. Revisa que sean frases claras, una por línea." | OK (no "Revisá", no "fijate") |
| "Objeciones estructuradas. Revisa y ajusta según tu conocimiento." | OK |
| "Nuevo {singularLabel} — agrega {campo}" | OK (no "agregá") |
| "6 líneas detectadas" | OK |
| "Procesando..." | OK |

### Hints de campo (en schemas)

| Hint | Verificación |
|---|---|
| "Las frases reales que escuchas de prospectos que no cierran. Usa sus palabras exactas…" | OK — tuteo ("escuchas", "usa") |
| "Una por línea. Tus palabras, no teoría de marketing." | OK |
| "Uno por línea. Resultados concretos con números cuando aplique." | OK |

### Títulos de Section en Sheet

| Texto | Estado |
|---|---|
| "Pegar lista y estructurar con IA" | OK |
| "Pega objeciones, una por línea. Pueden ser frases de prospectos reales, notas de llamadas, mensajes de WhatsApp." | OK |

---

## 8. Anti-patterns (Documentados Explícito)

| Anti-pattern | Por qué está prohibido | Alternativa correcta |
|---|---|---|
| Modal centrado (`Dialog`) para edición de item de objeción | Bloquea scroll de la página, crea desorientación en mobile, rompe el flujo de edición inline | Cards con expand/collapse inline (`ArrayCardsEditor` pattern) |
| Botón "Guardar" en el componente o en el Sheet | Rompe autosave on-change (regla `feedback_form_runtime_autosave.md`) | `onChange` propaga al form-runtime → `useAutoSave` debounce 800ms → PATCH automático |
| Inputs sin borde dentro del array | "Filas fantasma" — sin affordance visual, usuario no sabe qué es editable | `InlineEditableTextarea` con `border-transparent → hover:border-border → focus:border-ring/50` |
| `type`/`strategy` enum raw en UI (`"price"`, `"time"`, `"trust"`) | Ininteligible para el usuario que no habla inglés técnico | Mapear a labels Latam neutro: "Precio", "Tiempo", "Confianza" (ver §4) |
| Guardar `strategy` como valor derivado de `type` sin permitir edición | El usuario puede tener mejor nombre para su estrategia | `strategy` se auto-completa pero siempre es editable vía Select |
| Argentinismos en UI copy | Excluye mercados MX/CO/PE/CL (regla `spanish-text.md`) | "fijate" → "revisa"; "mirá" → "mira"; "dale" → — ; "poné" → "pon"; "pegá" → "pega" |
| `bulkPasteHelper` config genérica en `FieldSchema` | Abstracción prematura — solo un caso de uso en v1 | Componente custom `ObjectionsArrayInput` con `type: "custom"` + action registry |
| Hardcodear labels/opciones de `type` en FE sin mapa central | Duplicación que diverge — si BE agrega `ObjectionType.doubt`, FE no lo muestra | Mapa central `OBJECTION_TYPE_OPTIONS` + `OBJECTION_TYPE_LABELS` en el componente, consumido desde un solo lugar |
| Aplicar `draft_fields` del copilot vía `propose_field_updates` (flujo copilot proactivo) | El usuario abrió el Sheet explícitamente y dio consentimiento — no necesita el paso intermedio de "propuesta en el panel copilot" | `onChange` directo al recibir la respuesta del tool (merge con items existentes) |

---

## 9. FSD File Structure

```
frontend/src/
├── lib/form-runtime/schema/
│   └── types.ts                          ← Agregar storeAs?: "newline_array" a FieldSchema
│
├── components/form-runtime/inputs/
│   ├── TextareaInput.tsx                 ← Extender con branch storeAs === "newline_array"
│   └── __tests__/
│       └── inputs.test.tsx               ← Agregar suite "TextareaInput storeAs newline_array"
│
└── features/offer-studio/
    ├── components/
    │   └── psychology/
    │       ├── ObjectionsArrayInput.tsx  ← Nuevo (Client Component)
    │       └── BulkPasteSheet.tsx        ← Nuevo (Client Component)
    │
    ├── actions/
    │   └── registry.ts                   ← Registrar "objections-editor" action
    │
    └── schemas/
        ├── psychology.schema.ts          ← Cambiar field objections a type:"custom"
        └── __tests__/
            └── path-contract.test.ts     ← Nuevo (CONTRACT §13.4)
```

**FSD boundaries respetadas:**
- `ObjectionsArrayInput` y `BulkPasteSheet` viven bajo `features/offer-studio/` — son dominio específico del offer-studio.
- `TextareaInput` vive bajo `components/form-runtime/inputs/` — es infraestructura compartida del runtime.
- `fetchClient` es llamado solo desde un hook o directamente en el componente client (no en Server Components).
- No hay imports entre features (`copilot` es infra-like y está allowlisteado — el componente llama al endpoint HTTP del copilot, no importa código de la feature copilot).

---

## 10. Responsive Behavior

### TextareaInput newline_array

| Breakpoint | Comportamiento |
|---|---|
| Mobile (<768px) | Auto-height crece verticalmente. `minRows` de la grilla (2 por defecto). Sin scroll interno. Padding estándar `px-[14px] py-3`. |
| Tablet / Desktop (≥768px) | Mismo comportamiento. El ancho es dictado por el `FieldLayout: "full"` del schema (ocupa las 2 columnas de la grilla). |

### ObjectionsArrayInput

| Breakpoint | Comportamiento |
|---|---|
| Mobile (<640px) | Cards stack vertical. Header row: drag handle + número + chevron + acciones (⧉ ✕). Los selects `type` y `strategy` se mueven al body del card expandido (no en el header — demasiado estrecho). CTA "Pegar lista" ocupa ancho completo. Sheet side="bottom" (90vh). |
| Tablet (640–1023px) | Header row muestra type select. Strategy se mantiene en header si el viewport lo permite (>540px de card). Sheet side="right" (w-[400px]). |
| Desktop (≥1024px) | Layout completo como el wireframe: header row con type + strategy. Sheet side="right" (w-[480px]). |

---

## 11. Loading, Error y Empty States

### TextareaInput newline_array

| Estado | Comportamiento visual |
|---|---|
| Loading (initial) | Skeleton `h-[72px] w-full rounded-md animate-pulse` (gestionado por el section page, no por el renderer) |
| Empty (value=[] o null) | Placeholder italic visible `muted-foreground/70` |
| Error validación (required+vacío) | `border-destructive ring-destructive/20` — heredado del wrapper del form-runtime |
| Saving (autosave en curso) | Indicador global `OfferAutoSaveIndicator` — el renderer no muestra feedback propio |

### ObjectionsArrayInput

| Estado | Componente afectado | Comportamiento |
|---|---|---|
| `value = []` o `null` | Contenedor principal | Empty state text + 2 CTAs (ver wireframe §3.6) |
| Item sin `type` (required) | `ArrayItemBadge` | Badge rojo "FALTA tipo" |
| Item sin `rebuttal` | `ArrayItemBadge` | Badge amarillo "FALTA respuesta" |
| Item completo | `ArrayItemBadge` | Badge verde "OK" con check |
| Sheet textarea vacío o 1 línea | Botón "Estructurar" | `disabled` + Tooltip "Escribe al menos 2 objeciones para estructurar" |
| Sheet cargando | Footer del Sheet | `Progress` indeterminado + botón "Procesando..." disabled |
| Sheet error API | Footer del Sheet | `Alert` variant="destructive" + "No pudimos estructurar. Revisa que sean frases claras, una por línea." + botón "Reintentar" |
| Sheet success | Sheet + toast | Sheet cierra + `toast.success(...)` vía sonner |

---

## 12. API Integration

| Componente | Acción | Endpoint | Trigger |
|---|---|---|---|
| `ObjectionsArrayInput` (edit manual) | `onChange → useAutoSave` | `PATCH /api/v1/offer/{id}` (via form-runtime) | Cada cambio de campo, debounce 800ms |
| `BulkPasteSheet` | `fetchClient.post` | `POST /api/v1/copilot/tools/structure_objections` | Click "Estructurar con IA" |

El componente **no tiene hooks de React Query propios**. Delega la persistencia al form-runtime (`onChange` + `useAutoSave`). Solo hace una llamada directa via `fetchClient` para el tool del copilot.

**Request body para `structure_objections`:**
```ts
{ raw_text: string }  // el texto pegado por el usuario
```

**Response esperada (CONTRACT §11.1):**
```ts
{
  status: "ok",
  section: "psychology",
  draft_fields: {
    objections: Array<{
      type: string,
      rebuttal: string,
      strategy: string,
      trigger_phrases: string[]
    }>
  },
  confidence: 0.8,
  suggestions: string[],
  sources: string[]
}
```

---

## 13. Decisiones de Diseño

### D1 — `storeAs: "newline_array"` en vez de un nuevo tipo `"textarea-array"`

Introducir un nuevo `FieldType` requeriría cambiar el switch del dispatcher del form-runtime, actualizar los arch tests de naming, y registrar un nuevo renderer. Agregar `storeAs` a `FieldSchema` es backwards-compatible: un renderer existente (`TextareaInput`) solo agrega un branch. Menos fricción, mismo resultado, sin romper la arquitectura de tipos.

### D2 — Limpiar bullets `• - *` en el split de líneas

Los usuarios de Latam frecuentemente pegan desde documentos Word, WhatsApp o Google Docs donde las listas tienen bullets. Si el renderer no los limpia, la persistencia guarda `["• precio", "• tiempo"]` en vez de `["precio", "tiempo"]`. El sales-agent vería "• precio" como frase en el chat, lo cual rompe el matching semántico del `SemanticRouter`. El cleanup con `/^[\s•·\-\*]+/` es defensivo y no destructivo.

### D3 — `ObjectionsArrayInput` como custom component vs extensión de `ArrayCardsEditor`

`ArrayCardsEditor` es un renderer genérico del form-runtime. Inyectarle el bulk-paste CTA requeriría props condicionales o configuración que solo tiene sentido para objeciones. El principio de responsabilidad única justifica un componente custom que usa `ArrayCardsEditor` internamente (o copia su estructura) y agrega el CTA al pie. En una iteración futura, si 3+ arrays necesitan bulk-paste, se puede extraer `BulkPasteCTA` como primitivo genérico del runtime.

### D4 — `strategy` en header del card (no en el body expandido)

Poner `strategy` en el body expandido junto a `trigger_phrases` y `rebuttal` daría 3 campos en el body, lo cual es aceptable para cards mode. Sin embargo, `strategy` es un metadato del card — etiqueta cómo el card se clasifica — similar a `type`. Ponerlos juntos en el header permite leer de un vistazo el tipo y estrategia de cada objeción sin expandirla. Reduce la necesidad de expandir para entender el contenido. El costo es un header row más denso, mitigado con anchos fijos para los selects.

### D5 — Sheet (no Dialog) para bulk-paste

`Dialog` bloquea el scroll de la página y centra el modal, lo que en mobile hace que el teclado empuje el modal hacia arriba y crea problemas de viewport. `Sheet` desde abajo (mobile) o desde la derecha (desktop) respeta el scroll del formulario subyacente y sigue el patrón existente en el proyecto (`OfferStatusChangeModal` usa Dialog, pero ese es para confirmaciones, no para entrada de texto largo). La entrada de texto largo requiere espacio vertical — Sheet es la herramienta correcta.

### D6 — Merge (no reemplazo) al aplicar resultado del bulk-paste

Si el usuario ya tiene 2 objeciones manuales y pega una lista que produce 4 nuevas, el resultado debería ser 6 objeciones (2 + 4), no 4. El reemplazo destruiría trabajo previo. El merge permite flujo iterativo: el usuario puede usar bulk-paste varias veces y limpiar duplicados después. Los duplicados son menos perjudiciales que la pérdida de datos.

### D7 — Aplicación directa del resultado del copilot (sin `propose_field_updates`)

El flujo `propose_field_updates` del copilot muestra una card en el panel lateral del copilot que el usuario debe aceptar o rechazar en otro contexto visual. Para el bulk-paste iniciado por el usuario dentro del Sheet, ese flujo es innecesariamente indirecto: el usuario ya tomó la acción de abrir el Sheet, pegar texto y presionar "Estructurar". La intención es clara. Aplicar directamente y mostrar el resultado en las cards es más directo. Si el usuario no le gusta el resultado, puede eliminar los cards propuestos o hacer CTRL+Z (el autosave tiene un buffer de 800ms antes de PATCH).

