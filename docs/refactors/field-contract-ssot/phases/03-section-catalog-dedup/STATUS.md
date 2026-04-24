---
status: in-progress
opened_at: 2026-04-24
closed_at: null
baseline_green_commit: a495beb2
current_sub_step: A (BE offer extend SectionMetadata + kind)
---

# Fase 03 — Section catalog dedup · Status

**Abierta**. Baseline green `a495beb2` (Fase 02 close hash bump). SPEC +
ACCEPTANCE escritos. Sub-steps A → F en ejecución.

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
