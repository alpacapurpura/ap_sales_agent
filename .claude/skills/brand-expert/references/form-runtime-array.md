# Form-runtime Array Field — Design Rule

**Non-negotiable.** Todo campo `type: "array"` en schemas del form-runtime usa uno de 2 modos. Elección depende de `itemSchema.fields.length`.

## Regla

| Sub-campos por item | Modo | Variante |
|---|---|---|
| **1–3** | `"cards"` | **A · Enhanced Cards** — items como cards apilados con expand/collapse inline |
| **4+** | `"split"` | **C · Split Master-Detail** — lista izquierda + editor derecha |

Default automático via `itemSchema.fields.length`. Schema no necesita declarar nada.

Mockup referencia: `docs/mockups/array-field-unified.html`.

## Por qué

- **≤3 campos inline** (cards): el expand no domina viewport, mantiene visible el array completo, flujo lineal rápido.
- **≥4 campos editor dedicado** (split): formularios largos respiran, eliminan empuje vertical, navegación rápida entre items sin perder contexto.
- **Autosave on-change se mantiene en ambos** (ver `feedback_form_runtime_autosave.md`). No botones "Guardar".

## Override explícito

Solo 2 casos permitidos:
1. **Accordion denso** (`renderAs: "accordion"`): listas ≥15 items con 2–4 campos donde búsqueda/import batch es crítico (FAQ 30+ preguntas, resources catalog). Justificar en PR.
2. **Cards forzado** en arrays con 4+ campos cuando semántica requiere visibilidad simultánea (raro; argumentar).

Cualquier otro override = rechazar en review.

## Invariantes comunes (A y C)

- Drag handle para reorder (persistir `sort_order`).
- Contador `N ítems` / `N de M recomendados`.
- Duplicar + eliminar por item.
- Badge validación por item: `OK` / `FALTA X` / `REQUIERE Y`.
- Autosave on-change con debounce del form-runtime.
- Label número de item (`01`, `02`…) monospace.
- Bordes visibles en contenedor + en cada input (nunca inputs "desnudos").

## Prohibido

- ❌ Items sin contenedor visual (bordes/background) — "filas fantasma".
- ❌ Inputs sin borde dentro del array.
- ❌ Botón "Guardar" — rompe autosave.
- ❌ Modal para edición de item (a menos que sea el split drawer en mobile fallback).
- ❌ Textarea multi-línea como array simulado (`deliverables_list`, `scope_excluded`, `photos_urls`, `hours_of_operation`). Migrar a array real.
- ❌ Hardcodear `renderAs` sin chequear fields count — dejar default automático salvo override documentado.

## Implementación

`ArrayInput` (form-runtime) elige modo automáticamente:

```ts
const renderMode =
  field.renderAs ??
  (field.itemSchema.fields.length <= 3 ? "cards" : "split");
```

Schema puede override explícito:
```ts
{ type: "array", renderAs: "accordion", itemSchema: {...} }
```

## Cobertura actual → modo

| Array | Campos | Modo |
|---|---|---|
| `methodology_pillars` | 2 | cards |
| `plan` | 3 | cards |
| `reasons_to_believe` | 3 | cards |
| `pain_points`, `desires` | 2 | cards |
| `objections` | 2 | cards |
| `preferred_channels` | 2 | cards |
| `creative_concepts` | 3 | cards |
| `curriculum` | 3 | cards |
| `schedule` | 4 | split |
| `deliverables` (value_stack) | 5 | split |
| `faq.questions` | 5 | split (u `accordion` override si >15 preguntas) |
| `resources.*` | 4–5 | split (u `accordion` override) |
| `integrations` | 4 | split |
| `core_features` | 4 | split |
| `client_logos` | 2 | cards |
| `testimonials` | 12 | split |
| `portfolio.cases` | 15 | split |
| `portfolio.cases[].results_metrics` | 3 | cards |
| `venues` | 11 | split |
| `communication-assets.assets` | 8 | split |
| `before_after_pairs` | 3 | cards |

## Agregar nuevo array

1. Definir `itemSchema.fields` — contar.
2. ≤3 campos → listo, default cards aplica.
3. ≥4 campos → listo, default split aplica.
4. Caso especial justificar `renderAs` override en schema con comentario.
5. No hay paso 5 — autosave, drag, badges, duplicar vienen gratis del componente.

## Test arch (propuesto, no bloqueante aún)

Ratchet test FE que falla si schema hardcodea `renderAs` diferente al default sin comentario justificativo adyacente. Agregar cuando >2 overrides legítimos aparezcan.
