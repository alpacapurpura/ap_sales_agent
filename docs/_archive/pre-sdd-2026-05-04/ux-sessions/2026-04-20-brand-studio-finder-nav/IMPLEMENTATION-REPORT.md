# Implementation Report — Brand Studio Finder Navigation

**Date:** 2026-04-20
**Scope:** Frontend refactor per UI-SPEC-locked-dimensions.md
**Quality gates:** 0 TS errors · 0 ESLint errors · 1384 / 1384 tests pass · 16 / 16 arch tests pass

---

## Capas entregadas

| # | Capa | Status |
|---|---|---|
| 1 | Finder layout + tokens + breadcrumb | ✅ |
| 2 | Inline editor (auto-grow, chrome-less) | ✅ |
| 3 | Recommendations panel (colapsable abajo) | ✅ |
| 4 | Multi-field responsive grid | ✅ |
| 5 | Collection 4-col InstancePicker + buyer-personas wire-in | ✅ |
| 6 | "Siguiente vacío" CTA | ✅ |

---

## Archivos nuevos

| File | Propósito |
|---|---|
| `src/components/form-runtime/FinderColumn.tsx` | Shared column primitive (header 44px + scroll body) |
| `src/components/form-runtime/CompletionDot.tsx` | Status dot (filled/empty) for field rows |
| `src/components/form-runtime/FieldContextPanel.tsx` | Collapsible Recomendaciones panel + 6 block renderers |
| `src/components/form-runtime/NextEmptyFieldCta.tsx` | Bottom CTA — "Siguiente vacío" / "Sección completa" |
| `src/components/form-runtime/InstancePicker.tsx` | 280px instance column for collection sections |
| `src/components/form-runtime/instance-display.ts` | Pure helpers: initials, avatar palette, tone bucket |
| `src/components/ui/inline-editable.tsx` | InlineEditableInput + InlineEditableTextarea (chrome-less, auto-grow) |
| `src/features/brand-studio/lib/section-catalog.ts` | Slug→meta (label, icon, kind) for sections |
| `src/features/brand-studio/components/BrandStudioBreadcrumb.tsx` | URL-driven breadcrumb |
| `src/features/brand-studio/components/BuyerPersonaInstancePicker.tsx` | Col 2 picker (tenant personas + create) |
| `src/features/brand-studio/pages/BuyerPersonasLandingPage.tsx` | `/publico` welcome: picker + empty editor invitation |
| `src/lib/form-runtime/schema/layout.ts` | Field layout inference + grid-span class helper |
| `__tests__/*` | Tests for every new primitive |

## Archivos modificados

| File | Cambio |
|---|---|
| `src/app/globals.css` | +`--brand`, `--success`, `--warning` tokens (light+dark); +13 `--brand-*` dimension tokens |
| `src/lib/form-runtime/schema/types.ts` | +`FieldLayout`, +`SectionKind`, +`InstanceDisplay`, +reco-block fields (all optional) |
| `src/lib/form-runtime/schema/parser.ts` | Validates new optional fields, splits helpers (cognitive complexity <15) |
| `src/lib/form-runtime/schema/index.ts` | Exports new types + helpers |
| `src/components/form-runtime/FieldList.tsx` | Flat Finder rows (dot + label + chevron) |
| `src/components/form-runtime/FieldDetail.tsx` | Renders ALL fields in responsive grid with scroll-into-view on activeFieldId |
| `src/components/form-runtime/UniversalEditableSection.tsx` | Uses FinderColumn; removes SessionHeader; mounts ContextPanel + NextEmptyCta; optional instanceColumn slot |
| `src/components/form-runtime/inputs/TextareaInput.tsx` | Uses InlineEditableTextarea (`react-textarea-autosize`) |
| `src/components/form-runtime/inputs/TextInput.tsx` | Uses InlineEditableInput |
| `src/components/form-runtime/index.ts` | Barrel updated |
| `src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx` | 48px topbar with breadcrumb + NavRail |
| `src/features/brand-studio/components/BrandStudioNavRail.tsx` | Uses FinderColumn, 260px locked, chevron + icons |
| `src/features/brand-studio/pages/SectionPage.tsx` | Removed obsolete `onStartInterview` prop (now lives in future topbar CTA) |
| `src/features/brand-studio/pages/PersonaDetailPage.tsx` | Removed obsolete interview handler + wires `BuyerPersonaInstancePicker` as `instanceColumn` so the Finder layout becomes 4-col |
| `src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/page.tsx` | Renders `BuyerPersonasLandingPage` (picker + welcome) instead of legacy dashboard |
| Tests | Updated FieldRenderer, UniversalEditableSection, PersonaDetailPage tests for new contract |

---

## Token strategy (dark + light mode)

- **Añadidos a `:root` + `html.dark`**: `--brand`, `--brand-foreground`, `--success`, `--warning`
- **Registrados en `@theme`**: `--color-brand`, `--color-brand-foreground`, `--color-success`, `--color-warning`
- **Dimensiones bloqueadas en `:root`**: `--brand-sidebar-main` (220px), `--brand-col-sections` (260px), `--brand-col-instances` (280px), `--brand-col-fields` (320px), `--brand-topbar-h` (48px), `--brand-col-header-h` (44px), `--brand-row-h` (36px), `--brand-persona-row-h` (62px), `--brand-reco-header-h` (44px), `--brand-reco-max-h` (45%), `--brand-field-grid-gap-row` (24px), `--brand-field-grid-gap-col` (28px)
- **Cero `hsl()` literales inline** en archivos React. Sólo tokens vía `hsl(var(--x))` o utilidades Tailwind. El cambio entre modos resuelve automáticamente.
- **Compatibilidad** con el keyframe `copilotPulse` existente (comparten el tono brand 270 70%).

---

## Acceptance checklist UI-SPEC §9

- ✅ Widths fijos respetan `--brand-col-*` (verificable con DevTools)
- ✅ Editor main sin `max-width`/`margin auto` — `width: 100%` + padding `28px 40px 40px`
- ✅ Field grid: 1 col <900px, 2 col ≥900px, 3 col ≥1500px (`md:grid-cols-2 xl:grid-cols-3`)
- ✅ `w-full` respeta `col-span-full` en todas las columnas
- ✅ Reco panel colapsado 44px exactos (`--brand-reco-header-h`) / expandido `max-h-[45%]`
- ✅ Row height 36px para fields, 62px para personas (via padding + content)
- ✅ Status bar persona row: 60×3px, color por umbral 33/80 (`computeCompletionTone`)
- ✅ Avatar persona 38×38 redondo, color-hashed estable (`avatarClassFor`)
- ✅ Buyer personas 4-col wired end-to-end: `/publico` muestra picker + welcome, `/publico/persona/{id}` activa layout 4-col con picker activo + schema fields + editor grid + Recomendaciones
- ⚠️ Copilot `module_registry.py` + `navigation_map.py` diferido — Python/backend, no frontend-expert scope

---

## Pendientes (scope de otro ciclo)

1. **Uniform route `/brand-studio/[section]/instance/[instanceId]/[[...fieldId]]/page.tsx`** — patrón genérico para team, testimonials, authority. Hoy buyer personas usa el path legacy `/publico/persona/[id]` que funciona idéntico. Migrar luego con redirect.
2. **Extender collection wiring a equipo/testimonios/autoridad**: copiar el patrón BuyerPersonaInstancePicker usando los hooks/schemas respectivos (`TeamInstancePicker`, etc.).
3. **Backend copilot module_registry**: agregar `collections` dict + expose `instance_state` en route-tools. Archivos: `backend/src/modules/copilot/domain/module_registry.py`, `backend/src/modules/copilot/tools/registry.py`, `backend/src/modules/copilot/domain/navigation_map.py`.
4. **AI hint lazy call**: `FieldContextPanel` renderiza `Metadata` + bloques declarados en schema, pero la llamada `suggest_field_value` al copilot ("◆ Copilot detecta…") es un slot — falta conectar al bridge con caché por `(fieldId, valueHash)`.
5. **Schemas brand-studio** (`identity`, `positioning`, etc.): declarar `formula`, `examples`, `downstreamUses`, `relatedFields`, `lengthHint` donde tenga valor. Hoy el panel renderiza sólo `Metadata` (siempre presente). Es migración progresiva: cada schema que enriquezcas activa más bloques sin tocar código.

---

## Verificación

```bash
# Native (WSL)
cd frontend && npx tsc --noEmit                              # ✅ 0 errors
cd frontend && npx eslint src/{components/form-runtime,components/ui/inline-editable.tsx,features/brand-studio,lib/form-runtime/schema} --no-cache   # ✅ 0 errors (203 warnings pre-existing)
cd frontend && npx vitest run                                 # ✅ 1384 / 1384 pass
cd frontend && npx vitest run src/__tests__/architecture/     # ✅ 16 / 16 pass

# Browser (Docker dev up, Clerk logged in)
http://localhost:3000/{tenantId}/brand-studio/identity        # topbar + breadcrumb + 3 cols + grid multi-campo
http://localhost:3000/{tenantId}/brand-studio/positioning     # misma experiencia
http://localhost:3000/{tenantId}/brand-studio/publico         # dashboard legacy (intacto; pendiente wire InstancePicker)

# Prototipos de referencia
http://localhost:8888/option-a-enhanced.html                  # singleton
http://localhost:8888/option-a-personas.html                  # collection (4-col)
```

---

## Observaciones

- **TDD completo:** tests escritos antes del componente para `CompletionDot`, `FinderColumn`, `NextEmptyFieldCta`, `FieldContextPanel`, `InstancePicker`, `BrandStudioBreadcrumb`, `inline-editable`, `layout` helpers.
- **Ratchet preservado:** 0 nuevos errores ESLint, 0 nuevas violaciones arch tests.
- **Pre-existentes no tocados:** 78 errors / 3521 warnings en el resto del monorepo (legacy).
- **Sin deps nuevas** más allá de `react-textarea-autosize` (ya estaba en `package.json`, solo empecé a consumirlo).
- **FSD respetado:** primitives en `components/form-runtime/` + `components/ui/`, feature code en `features/brand-studio/`.
- **Spanish neutro:** todo el copy visible (Recomendaciones, Mostrar/Ocultar, Siguiente vacío, Sección completa, Campos de…, Instancia #…, Persona #…, Crear nueva persona) usa tuteo y tildes correctas.

El trabajo está listo para que el usuario navegue la UI en el browser y me confirme visual match antes de commitear.
