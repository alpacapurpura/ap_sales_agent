---
status: in-progress
opened_at: 2026-04-24
closed_at: null
baseline_green_commit: b826928b
current_sub_step: A (Authority block)
---

# Fase 02 — Status

**Abierta**. Baseline green `b826928b`. SPEC + ACCEPTANCE escritos.
Bloques A→I en ejecución — ver `SPEC.md`.

`KNOWN_UNRESOLVED_PATHS` guarda 56 entradas. Distribución esperada de
shrink en Fase 02 (leer arch test FE para breakdown exacto):

- Authority block (2): `authority_positioning_for_sales`, `authority_notes`
- Value-stack anchor (2): `total_perceived_value_anchor`, `stack_positioning_statement`
- Program narratives (2): `specific_details.weekly_time_commitment_hours`,
  `specific_details.prerequisites_text`
- SubscriptionDetails renames + nuevos (7)
- ServiceDetails nuevos (3)
- ProductDetails nuevos (5)
- Platform archetype (14 — requiere `PlatformDetails` + 6ta entry en
  `ARCHETYPE_TO_DETAILS_MAPPING`)

Total Fase 02 esperado: **35 paths** (allowlist baja 56 → 21).

Los 21 restantes quedan para Fase 05 (cross-module federated).

## Al abrir

1. Re-lectura `SPEC.md` (a crear) + `../../PLAN.md` §Fase 02.
2. Knowledge load 10-15 min:
   - `backend/src/modules/offer/domain/details.py` (SubscriptionDetails,
     ServiceDetails, ProductDetails, ProgramDetails).
   - `backend/src/modules/offer/domain/archetype_catalog.py`
     (ARCHETYPE_TO_DETAILS_MAPPING).
   - `backend/src/modules/offer/domain/field_contract.py` — extender
     registry fase por sección.
   - FE schemas relevantes (`authority.schema.ts`, `value-stack.schema.ts`,
     `program-details.schema.ts`, etc.)
   - Revisar `docs/refactors/field-contract-ssot/DECISIONS.md` ADR-009
     para evaluar si Fase 02 puede mover `PaymentProvider` a
     `shared/domain/payment.py`.
3. Refinar `SPEC.md` (separar bloques semánticos, un commit por bloque).
4. Escribir `ACCEPTANCE.md`.
5. Arrancar `protocol/PRE_FLIGHT.md`.

## Out of scope

- Cross-module federated paths (Fase 05).
- `OFFER_FIELDS_BY_FE_SECTION` cleanup (Fase 04).
- FE consumir section catalog (Fase 03).
