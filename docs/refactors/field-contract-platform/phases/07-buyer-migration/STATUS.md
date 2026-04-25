---
status: ready-to-start
opened_at: null
closed_at: null
baseline_green_commit: ed8a3a4f
---

# Fase 07 — Buyer-persona migration · Status

**Ready-to-start**. Fase 06 cerrada (`ed8a3a4f`). 471 arch tests +
4261 BE tests verde.

Al abrir:
1. Re-leer SPEC.md + PRE_INVESTIGATION.md.
2. Knowledge load: `BuyerPersona` Pydantic (dict-typed JSONB campos:
   demographics, psychographics, buyer_journey, pain_points, etc.) +
   `BUYER_PERSONA_EDITABLE_FIELDS` actual (12 entries hand-authored) +
   `_build_buyer_persona_paths` validator (top-level + dot-notation
   sub-keys conocidos).
3. Decisión clave: walker handling de dict sub-keys.
   - Patrón A (hand-author): mantener catalog hand-authored, crear
     FieldContract registry con paths explícitos para sub-keys conocidos.
   - Patrón B (extender walker): agregar arg `dict_subkeys` al walker
     para declarar sub-keys de dict-typed columns.
   Recomendación pre-investigación: B (más sostenible, aplicable a
   futuros módulos con JSONB).
4. Capturar baseline golden buyer-persona.
5. Ejecutar PRE_FLIGHT.md.
6. Escribir ACCEPTANCE.md.

Coordinación: brand-studio refactor sigue con Sprint 6.E offer-studio
editor (FE-side, no buyer-persona). Cero overlap.
