# DECISIONS — Brand Studio Finder Navigation

## 2026-04-20 — Session opened

**Trigger:** Chris showed screenshot of Brand Studio current 3-column layout. Columns feel inconsistent. Wants macOS Finder experience.

**Decisions:**

- [x] **Base layout chosen — Opción A (Finder Clásico).** Descartadas B (preview pane separada, redundante), C (rail+tree, demasiado cambio), D (palette, power-user-only).
- [x] **Refinement — A+ (inline editor + context panel).** Chris pidió: (1) aprovechar el ancho del editor con info que ayude a entender el campo, (2) fusionar preview y edit en UN mismo componente para campos largos (historia) que hoy requieren scroll interno.
- [x] **Inline-editable pattern aprobado:** textarea que parece texto cuando no focused, editable al click, altura auto-grow con contenido (`scrollHeight`). Elimina scroll interno en campos largos. Patrón Linear/Notion/Superhuman.
- [x] **Recomendaciones abajo, NO al lado.** Chris pide maximizar ancho del editor. Panel lateral derecho descartado.
- [x] **Colapsable por default:** panel empieza cerrado (solo header visible, ~44px). Click en header → expand con animación. Usuario controla cuándo ver info. Reduce saturación en campos que el usuario ya conoce.
- [x] **Badge "Recomendaciones"** visible siempre (pill color brand) — comunica que es ayuda opcional, no data requerida. Nota secundaria ("6 ayudas disponibles · no obligatorias") refuerza el mensaje.
- [x] **Grid 2 columnas** dentro del panel expandido (colapsa a 1-col <1100px). Aprovecha ancho horizontal.
- [x] **Por-bloque hint tags:** cada bloque lleva micro-tag en header (`Guía`, `IA`, `Swipe file`, `Trazabilidad`, `Contexto`, `Histórico`) para que el usuario distinga la naturaleza del contenido de un vistazo.
- [x] **Editor full-width, left-aligned.** Chris descarta centrado con max-width. El `.editor-main-inner` es `width: 100%` sin margin auto. Aprovecha ancho total.
- [x] **Grid responsive multi-campo.** Cuando una sección tiene N campos, el editor usa grid: 1-col <900px, 2-col ≥900px, 3-col ≥1500px. Cada field declara `layout: full | half | two-thirds`. Default inferido del type (textarea→full, text→half).
- [x] **Dimensiones bloqueadas.** Las medidas del prototipo son contrato. Documentadas en `UI-SPEC-locked-dimensions.md`. Implementación debe respetarlas 1:1. Cambios futuros pasan por nueva decisión explícita.
- [x] **Buyer personas → patrón 4 columnas (colecciones).** Generalizado: cualquier sección de tipo `collection` (buyer_personas, team, testimonials, authority) inserta una columna de instancias entre Secciones y Campos. Singletons (identidad, positioning, etc.) siguen con 3 cols. Prototipo: `option-a-personas.html`.
- [x] **Routes uniformes para colecciones:** `/brand-studio/{section}/instance/{instanceId}/{fieldId}`. Deprecar alias actual `/publico/persona/{id}`.
- [x] **Copilot recibe instance context.** `ModuleDescriptor.collections` expone schema+repo+label por colección. Route-tools binding recibe section + collection + instance_id + field_id + instance_state. Sugerencias IA son contextuales a la instancia (ej: dolor DE ALICIA, no dolor abstracto).
- [x] **Scope:** Brand Studio only for now. Other studios (Offer Studio, Closer Studio) may inherit later if Chris likes.
- [x] **Diagnosis confirmed:** 8 homogeneity issues listed in `FLOW-SPEC.md` §2.
- [x] **Shared CSS tokens:** Mirrored from `globals.css` dark mode. Any change to dark tokens in real code must update `_shared.css` too (prototype stays visually aligned).

## Patterns accepted across all options

- Breadcrumb in topbar replaces `SessionHeader` (`UniversalEditableSection.tsx:98`).
- Depth gradient: each deeper column slightly brighter than previous (dark mode).
- Chevron `›` on rows that have a sub-level.
- Completion dots (filled green / empty red-ish) per field.
- Column header (uppercase label + count) on every column.

## Patterns rejected

- Keeping `rounded-md border` wrapper on `FieldList` ul → confirmed: removes column-feel. Drop.
- Preview pane separada (opción B) → rechazada: duplica componentes, mismo valor se logra con inline-editable.

## Context panel — content decisions

Panel lateral derecho en col3 (ancho ~320px, oculto en <1280px). Contenido por field-type:

| Block | Qué muestra | Disponibilidad |
|---|---|---|
| **Fórmula** | Template declarativo: `Solo nosotros + {X} + {Y}` | Cuando `field.formula` existe en schema |
| **Sugerencia IA** | Copilot analiza el valor actual, sugiere mejora o redacta | Siempre (copilot siempre disponible) |
| **Swipe file** | 2-3 ejemplos de marcas reales en campos similares | Cuando field.examples existe |
| **Se usa en** | Trazabilidad downstream (Landing hero, Email subject, Ad copy, Sales Agent) | Cuando `field.downstream_uses` existe |
| **Relacionado** | Links a otros fields relacionados (insight tensión ↔ observación ↔ implicación) | Cuando `field.related_fields` existe |
| **Metadata** | Última edición, versión, longitud ideal, tono detectado | Siempre |

## Open questions for Chris

1. **Estado inicial del panel:** ¿siempre arrancar colapsado (recomendado — reduce ruido) o recordar preferencia del usuario vía `localStorage`?
2. **Por-campo vs global:** ¿el estado colapsado/expandido aplica a TODO Brand Studio (1 toggle global) o por campo (más granular pero más state)?
3. **Altura del panel expandido:** fijo 45% del viewport, o auto al contenido con `max-height: 60vh`?
4. **Hint tag en bloques** (`Guía` / `IA` / `Swipe file` / `Trazabilidad` / `Contexto` / `Histórico`): ¿quedan en español o los traducimos a íconos puros para reducir ruido visual?
5. ¿Aplicamos el mismo sistema a Offer Studio después? (form-runtime es compartido, sería gratis)
6. ¿Dots de estado 2-estado (filled/empty) o 3-estado (filled/partial/empty)?
7. ¿`react-textarea-autosize` (dep externa, 3kb, production-grade) o implementación propia con `useLayoutEffect` + `ref` (sin dep, ~15 líneas)?
8. ¿Swipe file ejemplos hardcoded en schema (sencillo), o editable desde admin panel (flexible)?
9. ¿Tono detectado en metadata usa LLM (latencia) o regex básico local (instantáneo, 80% accuracy)?
