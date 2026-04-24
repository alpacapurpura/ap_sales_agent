---
status: ready-to-start
opened_at: null
closed_at: null
baseline_green_commit: bcf6bb49
---

# Fase 04 — Drop `OFFER_FIELDS_BY_FE_SECTION` · Status

**Lista para arrancar**. Fase 03 cerrada (section catalog dedup completed;
FE ambos studios consumen BE catalog via React Query). Baseline green en
`bcf6bb49` (último commit Fase 03 Block E).

## Al abrir

1. Re-lectura SPEC.md + `../../PLAN.md` §Fase 04.
2. Knowledge load 10-15 min:
   - `backend/src/modules/offer/domain/field_contract.py` — extender con
     util `fields_by_section(section_key) -> tuple[str, ...]` puro
     derivado del registry.
   - `backend/src/modules/offer/workers/tasks.py` — consumer actual del
     dict `OFFER_FIELDS_BY_FE_SECTION`.
   - `backend/src/modules/offer/domain/extraction_section_map.py` —
     segundo consumer.
   - Paridad check: asegurar que cada field listado hoy en
     `OFFER_FIELDS_BY_FE_SECTION` también vive en el registry del
     `FieldContract` (Fase 02 cerró la extensión — validar hoy).
3. Escribir ACCEPTANCE.md.
4. Ejecutar PRE_FLIGHT.md.

## Out of scope

- Downstream sales-agent/landing consume contract directamente (Fase 05).
- Cross-module federated paths (Fase 05).
