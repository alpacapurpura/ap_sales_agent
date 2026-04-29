---
globs: "{frontend/src/lib/form-runtime/**,frontend/src/features/{brand,offer}-studio/schemas/**}"
description: Stub — invoca brand-expert / offer-expert
---

# Form-runtime Array Field

Default automático por `itemSchema.fields.length`:
- ≤3 sub-fields → `cards` (Enhanced Cards, expand/collapse inline)
- ≥4 sub-fields → `split` (Master-Detail, lista izquierda + editor derecha)

Autosave on-change preservado en ambos modos. Override `renderAs: "accordion"` solo justificado (lista ≥15 items con búsqueda/import batch).

Detalle (invariantes comunes, tabla cobertura por array, agregar nuevo, mockup ref) en `brand-expert` / `offer-expert` skills → `references/form-runtime-array.md`.

**Prohibido:** items sin contenedor visual, inputs sin borde, botón "Guardar" (rompe autosave), modal edición de item, textarea multi-línea como array simulado, hardcodear `renderAs` sin chequear fields count.
