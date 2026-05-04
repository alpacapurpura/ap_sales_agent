# Fase 03 — Section catalog dedup

## Objetivo

FE no duplica lista de secciones. Consume del endpoint `/api/v1/offer/archetypes/catalog` extended o nuevo `/section-catalog`. Brand-studio aplica mismo patrón.

## Scope

**Dentro**:
- `section_catalog.py` BE extendido con `kind` (singleton/collection) — hoy solo FE
- Endpoint `/api/v1/offer/section-catalog` versionado con metadata rica
- FE `useSectionCatalog()` React Query hook
- FE `OFFER_SECTIONS` hardcoded array eliminado, reemplazado por consumer del hook
- Mapeo `icon_name` string → componente Lucide via `icon-name-resolver.ts` (ya existe)
- Brand-studio mismo patrón (mirror refactor)
- Arch test: FE no puede hardcodear lista 21 secciones offer ni 14 brand

**Fuera**:
- Cambios per-field (Fase 01-02 ya hechas)
- Drop `OFFER_FIELDS_BY_FE_SECTION` (Fase 04)

## Análisis requerido al abrir fase

- Leer `frontend/src/features/offer-studio/lib/icon-name-resolver.ts` — cómo mapea
- Leer brand-studio `section-catalog.ts` — estructura paralela
- Investigar SSR: section list hardcoded se usa en server components? Si sí, React Query no sirve — fetch server-side + pass as prop
- Verify arch tests existentes `test-studio-structure-parity.test.ts`, `test-studio-sections-lazy-loading.test.ts` no rompen con el cambio

## Duración estimada

0.5 sprint.

## Riesgo

Bajo. Refactor mecánico.

## DoD

Al abrir fase, escribir ACCEPTANCE.md.
