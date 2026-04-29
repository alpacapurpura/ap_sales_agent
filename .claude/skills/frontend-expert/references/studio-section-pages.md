# Studio Section Pages — FE FSD pattern

Patrón homologado con lazy-loading real per-section via `next/dynamic`. Aplica brand-studio, offer-studio, futuros studios con form-runtime.

```
features/{studio}-studio/pages/
  section-slugs.ts            ← server-safe: SLUGS[] + is{Studio}StudioSection(slug)
  SectionDispatcher.tsx       ← "use client", mapa next/dynamic per slug
  sections/
    {slug}-page.tsx           ← named export, importa SOLO su schema
```

## Contrato

- **Server route** (`app/.../[section]/page.tsx`): importa solo `section-slugs.ts` (server-safe gate). Valida slug, delega al `SectionDispatcher` client con props. Nunca importa schemas ni componentes `"use client"`.
- **SectionDispatcher.tsx**: `"use client"`. Bootstrap side-effect del action registry. Cada entry: `dynamic(() => import("./sections/X-page").then(m => ({ default: m.XPage })))`.
- **sections/*-page.tsx**: named export (respeta `test-no-default-exports`). Importa schema individual desde `schemas/{slug}.schema.ts`, NO barrel `schemas/index.ts`.
- **Factory opcional** (offer-studio usa `create-offer-section-page.tsx` por guard edition-scope + save handler memoizado).
- **Shared primitives** en `src/lib/studio-section-page/`: `SectionPage` (wrapper), `SectionPageLoading` (fallback `next/dynamic`).

## Prohibido

- `section-pages.tsx` monolítico o `section-page-map.ts` con imports estáticos.
- Side-effect `import "@/features/{studio}/actions/registry"` en barrel schemas — debe vivir en `SectionDispatcher.tsx`.
- Importar otra sección dentro `*-page.tsx` (rompe chunk isolation Turbopack).

## Arch tests
- `test-studio-sections-lazy-loading.test.ts`
- `test-studio-structure-parity.test.ts`
