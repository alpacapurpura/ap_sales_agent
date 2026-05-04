---
status: done
opened_at: 2026-04-24
closed_at: 2026-04-24
baseline_green_commit: a495beb2
last_green_commit: bcf6bb49
---

# Fase 03 — Section catalog dedup · Status (closed)

## Resumen

Fase 03 cerrada. FE dejó de hardcodear secciones; ambos studios consumen
BE catalog via React Query. Nuevo arch test FE previene regresión.

## Bloques ejecutados

| Bloque | Commit | Notas |
|---|---|---|
| Open (ACCEPTANCE) | `abeae501` | — |
| A · BE offer +kind en SectionMetadata | `33a35592` | 21 entries populadas, `_CATALOG_VERSION` bump |
| B · FE offer consume hook | `048ed41a` | Delete `lib/section-catalog.ts`. Migrate NavRail/Breadcrumb/ExtractionSummaryCard |
| C · BE brand section catalog + endpoint | `0104047c` | Nuevo módulo `brand/domain/section_catalog.py` + `brand/api/sections.py` + `/api/v1/brand/sections/catalog` |
| D · FE brand consume hook | `c8dd78fd` | Nuevo `features/brand-studio/{api,hooks,lib}/` + delete `lib/section-catalog.ts` |
| E · Arch test anti-drift | `bcf6bb49` | `test-no-hardcoded-section-list.test.ts` |

## Verificación

- BE arch 425 → 432 passed (+6 brand + +1 offer kind).
- FE arch 37 → 38 passed (+1 anti-drift).
- FE TSC 0 errors.
- FE vitest (offer+brand+copilot subset): 81 files · 573 passed.
- Offer `a96403b5...` NavRail renders identical (labels del BE catalog
  preservan neutro LatAm).

## Out of scope (cerrado)

- Cross-module federated paths (Fase 05).
- `OFFER_FIELDS_BY_FE_SECTION` cleanup (Fase 04 — ready).
- Downstream sales-agent/landing consuming contract (Fase 05).

Los 21 paths restantes en `KNOWN_UNRESOLVED_PATHS` son cross-module
federated (assets, testimonials, portfolio, knowledge, scheduling,
gallery, faq) — Fase 05 los cierra. Fase 03 NO los toca.

## Al abrir

1. Re-lectura SPEC.md + `../../PLAN.md` §Fase 03.
2. Knowledge load 10-15 min:
   - `backend/src/modules/offer/domain/section_catalog.py`
     (`SECTION_CATALOG` dict — 21 entries con metadata rica).
   - `frontend/src/features/offer-studio/lib/icon-name-resolver.ts`
     (mapeo Lucide).
   - `frontend/src/features/offer-studio/section-catalog.ts` (hardcoded
     `OFFER_SECTIONS` array a eliminar).
   - `frontend/src/features/brand-studio/section-catalog.ts` (mirror
     para el refactor paralelo).
   - Arch tests `test-studio-sections-lazy-loading`,
     `test-studio-structure-parity` — verificar que no rompen.
3. Escribir ACCEPTANCE.md (criterios no-negociables).
4. Ejecutar PRE_FLIGHT.md.
5. Arrancar SSR check: ¿la lista de secciones se usa en Server
   Components? Si sí, React Query no sirve — fetch server-side y pasar
   como prop.

## Out of scope

- Cross-module federated paths (Fase 05).
- `OFFER_FIELDS_BY_FE_SECTION` dict removal (Fase 04).
- Nuevos FieldContract entries (Fase 02 cerrado).
