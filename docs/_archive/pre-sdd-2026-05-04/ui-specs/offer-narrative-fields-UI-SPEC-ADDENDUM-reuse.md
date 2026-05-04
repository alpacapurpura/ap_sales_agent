# UI-SPEC Addendum — Reuse Strategy (Brand ↔ Offer unified)

**Date:** 2026-04-24
**Supersedes sections:** D3, D5, D7 of `offer-narrative-fields-UI-SPEC.md`
**Status:** BLOCKING for Fase 5-6

## Propósito

El usuario pidió: *"reusa todo lo posible en cuanto a componentes UI, reusa todo lo que está ya en el brand para que la experiencia sea unificada"*.

Tras investigación (Explore agent, 2026-04-24), brand-studio y offer-studio **YA comparten** el runtime `form-runtime` completo. No hay componentes duplicados. La unificación se logra por **schemas declarativos** + **reuse del form-runtime**, NO por componentes custom adicionales.

## Qué reusar directo (sin crear nada)

Ubicaciones canónicas:

| Recurso | Path | Usado por |
|---|---|---|
| Runtime entry | `frontend/src/components/form-runtime/UniversalEditableSection.tsx` | brand + offer |
| Field dispatcher | `frontend/src/components/form-runtime/FieldRenderer.tsx` | brand + offer |
| Textarea input | `frontend/src/components/form-runtime/inputs/TextareaInput.tsx` | brand + offer |
| Array dispatcher | `frontend/src/components/form-runtime/ArrayInput.tsx` | brand + offer |
| Array cards editor | `frontend/src/components/form-runtime/ArrayCardsEditor.tsx` | brand (reasons_to_believe) + offer (faq) |
| Array split editor | `frontend/src/components/form-runtime/ArraySplitEditor.tsx` | brand + offer |
| Schema types | `frontend/src/lib/form-runtime/schema/types.ts` | brand + offer |
| Autosave hooks | `frontend/src/lib/form-runtime/hooks/` | brand + offer |
| Copilot bridge | `frontend/src/lib/form-runtime/copilot/bridge.ts` | brand + offer |
| Actions registry | `frontend/src/lib/form-runtime/actions/registry.ts` | brand + offer |

## Patrón ya existente en brand — `reasons_to_believe`

`frontend/src/features/brand-studio/schemas/positioning.schema.ts:99-146` declara array estructurado con `itemSchema`, SIN `renderAs` explícito (auto-dispatch a cards por itemSchema.fields.length ≤ 3). Autosave on-change gratis.

**Objections offer-studio DEBE seguir este patrón literal**, no inventar componente nuevo. Diff cosmético: objections tiene 4 sub-fields → forzar `renderAs: "cards"` con comentario justificativo (`form-runtime-array.md` permite override documentado — strategy auto-sugerido desde type lo vuelve perceptualmente 3).

## Qué SÍ agregar al form-runtime (genérico, no offer-only)

Estas dos extensiones viven en `frontend/src/lib/form-runtime/` + `frontend/src/components/form-runtime/` porque brand-studio también se beneficiará. No duplicar bajo `features/offer-studio/`.

### 1. `FieldSchema.storeAs: "newline_array"` (renderer extension)

Motivo: DB columns ya están migradas como `JSONB default='[]'` (measurable_outcomes, urgency_drivers, cultural_trust_barriers, emotional_triggers, status_drivers, regret_scenarios, marketing_pain_points, marketing_desires, anti_avatar_keywords). El renderer transforma `string[] ↔ string` solo en UI, preservando shape estructurado en DB para sales-agent queries.

Alternativa descartada: path TEXT plano tipo brand `_text`. Rota contract sales-agent (`trigger_phrases` estructurado no queryable). Mejor migrar brand a este patrón en futuro sprint.

**Contrato** (agregar a `frontend/src/lib/form-runtime/schema/types.ts`):

```ts
export interface FieldSchema {
  // ...existente
  /** For type: "textarea". When set, value is transformed split/join by newline. */
  storeAs?: "newline_array";
}
```

**Implementación** — extender `TextareaInput.tsx`:

```tsx
export function TextareaInput({ field, value, onChange, ... }: BaseInputProps<string | string[]>) {
  const isArrayMode = field.storeAs === "newline_array";
  const displayValue = isArrayMode
    ? (Array.isArray(value) ? value.join("\n") : "")
    : (value ?? "");

  const handleChange = (next: string) => {
    if (isArrayMode) {
      const arr = next.split("\n").map(l => l.trim()).filter(Boolean);
      onChange(arr as unknown as string); // upstream type narrows by storeAs
    } else {
      onChange(next);
    }
  };

  return <InlineEditableTextarea value={displayValue} onChange={handleChange} ... />;
}
```

Brand puede migrar sus `_text` paths a `storeAs: "newline_array"` + paths canónicos cuando quiera — queda opcional. No rompe nada hoy.

### 2. Bulk-paste-AI helper (deferred, NOT en esta fase)

Regla "Rule of three": el bulk-paste-AI hoy solo lo necesita `objections`. Hasta que 2 features más lo pidan, mantenerlo **local** a offer-studio (`features/offer-studio/components/psychology/ObjectionsBulkPasteSheet.tsx`), no en form-runtime.

Uso patrón que ya existe en brand: `useClonePersonality()` en `features/brand-studio/api/personality.ts:183-226` invoca backend LangGraph con textarea raw. Objections-bulk-paste sigue mismo patrón:

1. Sheet lateral (reusar `@/components/ui/sheet` de Shadcn).
2. Textarea grande con placeholder lista bullets.
3. Botón "Estructurar con IA" → fetchClient POST al tool copilot `/api/v1/copilot/tools/structure_objections`.
4. Respuesta = **proposal card** via flujo estándar `propose_field_updates` (ver corrección D7 abajo).

Cuando 2+ features más pidan patrón similar → refactor a `form-runtime/helpers/BulkPasteAIAction.tsx` shared.

## Corrección D7 (UX designer se desvió del CONTRACT)

UX-SPEC §D7 propuso aplicar resultado directo sin `propose_field_updates`. **Revertir**.

**Motivos**:
1. Brand usa proposal card flow estándar. Aplicar directo en offer = inconsistencia UX entre studios. User pidió "experiencia unificada".
2. CONTRACT §10 explícito: "emite card tipo `proposal` con updates para `objections` field".
3. El flujo `propose_field_updates` ya trae undo gratis + trace en `copilot_mutation_journal`. Bypass = data loss risk sin audit trail.
4. "El user ya dio consentimiento al click Estructurar" es falacia — el user dio consent para **extraer**, no para **sobreescribir** sus objections manuales previas. Proposal card le muestra diff y confirma.

**Comportamiento correcto**:

1. User click "Estructurar con IA" en Sheet.
2. POST al tool copilot con raw_text.
3. Tool emite proposal card (visible en chat copilot lateral).
4. User review diff en card + Accept/Reject.
5. Accept → PATCH via `propose_field_updates` flow existente.

Latencia extra: 1 click. Beneficio: consistencia + undo + trace. Vale.

## Corrección D3 + D5

**D3 (ObjectionsArrayInput custom vs runtime extension)**: OK mantener como indica UX-SPEC — `type: "custom"` + action registry. Alternativa: `type: "array"` con `renderAs: "cards"` + campo `customHeader` en schema que permita botón "Estructurar con IA". Ambas válidas.

**Decisión final**: **Opción B — `type: "array"` estándar**. Razones:
- Reusa `ArrayCardsEditor` existente (brand ya lo usa en reasons_to_believe). Cero código nuevo en el runtime.
- El botón "Estructurar con IA" vive en el **header del array** (nivel section, no nivel item). No requiere custom action, sino un slot opcional `headerActions?: ReactNode[]` en `ArrayCardsEditor` — extension minimal.
- Si brand mañana quiere "Estructurar personality con IA", hereda gratis.

Implementación concreta Fase 5-6:
- Extender `ArrayCardsEditor.tsx` con prop opcional `headerSlot?: React.ReactNode`.
- Extender `FieldSchema` con `bulkPasteAction?: { toolName: string; label: string; placeholder: string }`.
- Cuando `bulkPasteAction` está seteado, `ArrayCardsEditor` renderiza un botón secundario en el header que abre Sheet + llama `toolName`.
- **Offer-studio NO crea custom component**. Solo declara `bulkPasteAction` en su schema.

Esto cumple "reusar brand al máximo" — la extension vive en form-runtime (shared), no en offer-studio (aislado).

**D5 (Sheet vs Dialog)**: OK mantener Sheet. Ambos studios pueden reusar el patrón.

## Addendum a schemas finales (psychology objections)

```ts
// frontend/src/features/offer-studio/schemas/psychology.schema.ts
{
  id: "objections",
  label: "Objeciones típicas",
  type: "array",
  path: "objections",
  renderAs: "cards",  // override justified: strategy auto-derivable from type, 3 visible inline
  itemSchema: {
    fields: [
      { id: "type", label: "Tipo", type: "enum", path: "type",
        options: [
          { value: "price", label: "Precio" },
          { value: "time", label: "Tiempo" },
          { value: "trust", label: "Confianza" },
          { value: "partner", label: "Pareja / consulta" },
          { value: "fit", label: "No es para mí" },
          { value: "custom", label: "Otro" },
        ]
      },
      { id: "trigger_phrases", label: "Frases que la disparan", type: "textarea",
        path: "trigger_phrases", storeAs: "newline_array", rows: 3,
        hint: "Una por línea. El sales-agent las detecta en el chat." },
      { id: "rebuttal", label: "Respuesta del agente", type: "textarea",
        path: "rebuttal", rows: 4 },
      { id: "strategy", label: "Estrategia", type: "text",
        path: "strategy", hint: "Auto-sugerido desde tipo. Editable." },
    ]
  },
  bulkPasteAction: {
    toolName: "structure_objections",
    label: "Pegar lista y estructurar con IA",
    placeholder: "Pega una lista de objeciones, una por línea...",
  },
}
```

## Checklist frontend-expert (Fase 5-6)

- [ ] Agregar `storeAs?: "newline_array"` a `FieldSchema` en `lib/form-runtime/schema/types.ts`.
- [ ] Extender `TextareaInput.tsx` con transform split/join cuando `storeAs === "newline_array"`.
- [ ] Agregar `bulkPasteAction?: BulkPasteActionConfig` a `FieldSchema` (nueva type).
- [ ] Extender `ArrayCardsEditor.tsx` con slot header opcional — renderiza botón "Pegar y estructurar" cuando `bulkPasteAction` existe.
- [ ] Crear `ObjectionsBulkPasteSheet.tsx` en `features/offer-studio/components/psychology/` — Sheet + textarea + POST `/api/v1/copilot/tools/structure_objections`.
- [ ] Fix paths en 5 schemas (identity, promise, strategy, psychology, closing) per CONTRACT §8.
- [ ] Agregar `storeAs: "newline_array"` a todos los textareas que apunten a columnas JSONB string[] (9 fields).
- [ ] Ningún componente nuevo fuera de `ObjectionsBulkPasteSheet.tsx`. Todo vive en form-runtime extendido.
- [ ] TypeScript strict + Vitest + arch tests verdes.
- [ ] No romper brand-studio — correr tests brand explicit: `npx vitest run src/features/brand-studio/`.

## Verificación final

Al terminar Fase 5-6, correr:

```bash
cd frontend && npx vitest run src/features/brand-studio/ src/features/offer-studio/ src/components/form-runtime/
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run src/__tests__/architecture/
```

Si **algún** test de brand-studio falla → rollback extension y fixear — la unificación no puede romper el otro lado.
