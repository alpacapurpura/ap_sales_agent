# PLAN — Brand Studio Finder Navigation (bloqueado hasta elegir opción)

> Este plan se concreta una vez Chris elija opción A/B/C/D. Por ahora documenta las fases comunes y el alcance por opción.

## Fase 0 — Decisión (bloquea todo lo demás)

- [ ] Chris revisa http://localhost:8888/ y elige opción + ajustes
- [ ] Actualizar `DECISIONS.md` con la elección
- [ ] Generar `UI-SPEC-{option}.md` con specs detalladas

## Fase 1 — Topbar + Breadcrumb (común a A, B, C, D)

**Archivos:**
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx` (crear si no existe)
- `frontend/src/features/brand-studio/components/BrandStudioBreadcrumb.tsx` (nuevo)

**Acceptance:**
- Topbar 48px height sticky debajo del header global
- Breadcrumb lee `useParams` + `section-catalog.ts` para labels
- `UniversalEditableSection` ya NO renderiza `SessionHeader` (deprecated o removido)

**Verificación:**
```bash
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run src/features/brand-studio/
```

## Fase 2 — Column primitives + tokens (común)

**Archivos:**
- `frontend/src/components/form-runtime/FinderColumn.tsx` (nuevo shared primitive)
- `frontend/src/components/form-runtime/CompletionDot.tsx` (nuevo)
- `frontend/src/app/globals.css` (opcional: tokens `--col-depth-1..4`)

**Acceptance:**
- `FinderColumn` encapsula header + body + scroll
- Row height homogéneo entre usos (NavRail, FieldList)
- Dark + light mode correctos

## Fase 3 — Refactor FieldList + FieldDetail (común a A, B)

**Archivos:**
- `frontend/src/components/form-runtime/FieldList.tsx`
  - Remove `rounded-md border`
  - Replace `FieldRow` preview multi-línea con 1-line + dot + chevrón
  - Use `FinderColumn` wrapper
- `frontend/src/components/form-runtime/FieldDetail.tsx`
  - Add column header (field label + autosave status)
  - Use `FinderColumn` wrapper
- `frontend/src/components/form-runtime/UniversalEditableSection.tsx`
  - Drop `SessionHeader` (migrado a topbar fase 1)
  - Normalize column widths (A: 340px col2; B: 280+380; C: solo col3; D: como A)

**Acceptance:**
- Column widths consistentes por opción
- `FieldList` ya no parece card suelta
- Active row visible por borde izquierdo brand-colored
- Tests pasan: `npx vitest run src/components/form-runtime/`

## Fase 4 (solo opción B) — Preview Pane

**Archivos nuevos:**
- `frontend/src/components/form-runtime/FieldPreview.tsx`

**Cambios:**
- `UniversalEditableSection` acepta `showPreview` prop
- Prop `isEditing` en state (inicialmente false → preview; click "Editar" → true → detail pane)

## Fase 4 (solo opción C) — Tree nav

**Archivos:**
- `frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx` → reescribir como tree
- `frontend/src/components/shared/layout/app-sidebar.tsx` → soporte colapsado (icon rail 64px)
- `frontend/src/features/brand-studio/hooks/use-tree-state.ts` (nuevo, maneja open/close persistido en localStorage)

## Fase 4 (solo opción D) — Command Palette

**Archivos nuevos:**
- `frontend/src/features/brand-studio/components/BrandCommandPalette.tsx`
- `frontend/src/features/brand-studio/hooks/use-command-index.ts`

**Shadcn:**
- `npx shadcn@latest add command` (si no está instalado)

**Keybindings:** `⌘K` / `Ctrl+K` global dentro de Brand Studio.

## Fase 5 — QA + Arch tests

- [ ] `cd frontend && npx tsc --noEmit` → 0 errors
- [ ] `cd frontend && npx eslint src/` → 0 new errors
- [ ] `cd frontend && npx vitest run` → all pass
- [ ] `cd frontend && npx vitest run src/__tests__/architecture/` → all pass
- [ ] Visual check en dark + light mode
- [ ] E2E smoke: navegación Brand Studio sigue funcionando

## Riesgos

| Risk | Mitigation |
|---|---|
| Deep-linking roto al cambiar layout | URLs no cambian — solo visual layer. Tests E2E existentes cubren. |
| `form-runtime` se usa en otros studios | Verificar consumos: `Grep "UniversalEditableSection"`. Si Offer Studio consume, coordinar. |
| Mobile breakpoint rompe con 4 columnas (opción B) | B colapsa a A en <1280px. Documentar en UI-SPEC. |
| Shadcn `command` dep pesada (opción D) | ~15kb gz, aceptable. Lazy-load el palette con dynamic import. |

## Rollback

Todo vive en `features/brand-studio/` + `components/form-runtime/`. Rollback = revert del PR. No migration DB.
