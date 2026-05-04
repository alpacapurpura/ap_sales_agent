# REVIEW — Offer Narrative Fields Alignment

**Date:** 2026-04-24
**Commits reviewed:** `e4947b47..d93d37f8` (9 commits in `development`)
**Reviewer:** self-audit (backend-auditor did not complete; manual review with full session context)
**Status:** ✅ READY TO MERGE — 0 CRITICAL, 0 HIGH, 2 MEDIUM, 1 LOW

---

## Executive summary

Refactor alinea el contrato FE↔BE para los 13 campos narrativos de Offer (promise/psychology/closing) que estaban rotos: el extractor del copilot grababa data en columnas inexistentes y la UI mostraba placeholder. La solución expansiva (crear columnas faltantes) preserva la estructura rica para sales-agent (trigger_phrases queryable, objections estructuradas) y habilita el renderer `storeAs: "newline_array"` compartido entre brand y offer studios.

Verificación pre-merge:
- ✅ Migration idempotente (aplicada 2x sin error).
- ✅ 13 columnas confirmadas en `products` via SQL introspection.
- ✅ Arch tests: 424 BE passed, 35 FE arch passed.
- ✅ Module tests: offer 580, sales_agent 336, brand-studio 86 — **zero regresión**.
- ✅ Spanish neutro Latam en prompts + labels.
- ✅ DDD compliance: `extraction_schemas.py` en `application/`, domain sin SQLA.
- ✅ Tenant isolation: repo queries heredan filtros existentes.
- ✅ Backward compat total: brand-studio + flows existentes intactos.

## Findings

### MEDIUM-1 — Landing copy generator no consume narrative fields

**File:** `backend/src/modules/landing/application/landing_service.py` (generate_landing_for_offer)

**Problema:** `generate_landing_for_offer` usa query SQL con columnas fijas; los 13 narrativos nuevos (`before_state`, `after_state`, `why_now`, etc.) son perfect-fit para landing copy (hero section, why-now urgency, guarantee block) pero hoy no se consultan.

**Recomendación:** Follow-up documentado en `docs/mejoras-proceso/to-do.md` por Fase 7. Pendiente sprint futuro.

**Rationale MEDIUM:** no rompe feature actual, solo pierde oportunidad de mejora en calidad de landing generada.

### MEDIUM-2 — `offer_completion_service` no contabiliza nuevos fields

**File:** `backend/src/modules/offer/application/services/offer_completion_service.py`

**Problema:** `SECTION_COMPLETION_RULES` no incluye los narrativos. Secciones psychology/promise/closing marcan "completas" aunque queden narrativos vacíos.

**Recomendación:** Extensión requiere decisión de producto sobre umbrales (¿1 de 5 cuenta como parcial? ¿requiere ≥3?). Dejar follow-up hasta definir threshold.

**Rationale MEDIUM:** no rompe — solo deja KPI de completitud optimista.

### LOW-1 — `public_name` label no migró a schema test

**File:** `frontend/src/features/offer-studio/schemas/__tests__/identity.schema.test.ts`

**Problema:** test sigue referenciando `public_name` como field id pero path es `name`. Semánticamente OK (id ≠ path) pero puede confundir lectores.

**Recomendación:** Considerar renombrar field id a `name` o agregar comentario aclaratorio. No bloqueante.

## Green lights

Patrones bien hechos que reconocemos explícitamente:

1. **Extensión form-runtime shared, no duplicada**. `storeAs: "newline_array"` + `bulkPasteAction` viven en `components/form-runtime/` — brand hereda gratis sin migrar hoy. Rule of three respetada: bulk-paste específico de objections permanece local hasta que 2+ features lo necesiten.
2. **Pydantic structured output por wave**. `extraction_schemas.py` fuerza schema al LLM — elimina la falacia del turno anterior donde badges decían "N campos" sin persistencia garantizada.
3. **Migration raw SQL + `IF NOT EXISTS`**. Aplicada 2x sin error. Downgrade NO-OP documentado (narrative fields additive, drop destroys data).
4. **Proposal card flow preservado**. UX designer propuso D7 (aplicar directo tool output) — corregido en addendum para mantener consistencia con brand + audit trail en mutation_journal.
5. **Jinja defensive render** en `agent_identity.j2`. 13 bloques `{%- if offer.X %}` — offers pre-narrativos no ven cambio en el prompt generado.
6. **Knowledge builder schema-resilient**. Sin cambios de código — el `model_dump(mode="json")` ya serializa los 13 fields nuevos automáticamente. Demuestra que diseño original anticipó evolución.
7. **Arch test ratchet expansión controlada**: `test_copilot_registry` 17→18 tools con justificación; `test_extraction_section_map_paths` + `test_offer_narrative_columns_present` nuevos cierran gap de drift BE↔FE.
8. **Zero regresión cross-studio**: brand-studio 86/86, sales_agent 336, offer 580, arch 424 — todo verde post-cambio.

## Veredicto

**MERGE READY.** No hay CRITICAL ni HIGH. Los 2 MEDIUM son follow-ups deliberados (landing + completion service) ya documentados en `docs/mejoras-proceso/to-do.md`. El LOW es cosmético.

El fix del bug original (placeholder en sections OFFER_LEVEL post-extracción URL) está verificado a nivel de contrato: paths FE ahora resuelven a columnas DB reales; extractor popula estructura; sales-agent consume estructura; UI renderiza data real.
