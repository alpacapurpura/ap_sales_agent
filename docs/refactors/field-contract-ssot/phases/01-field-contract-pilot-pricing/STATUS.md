---
status: ready-to-start
opened_at: 2026-04-24 15:30
closed_at: null
---

# Fase 01 — Status

Lista para arrancar. Fase 00 cerrada (`701f6f2d` + closing commit).
`KNOWN_UNRESOLVED_PATHS` guarda 3 entradas pricing LATAM que esta fase
debe eliminar:

- `tax_included`
- `installments_available`
- `accepted_payment_providers`

## Al abrir

1. Re-lectura `SPEC.md` + `../../PLAN.md` §Fase 01.
2. Knowledge load 10-15 min:
   - `backend/src/modules/offer/domain/offer.py` (Offer + OfferPricingUpdate)
   - `backend/src/modules/offer/domain/enums.py` (PaymentProvider si existe)
   - `backend/src/modules/offer/application/services/offer_extraction_service.py`
     — dónde se invoca prompt closing
   - `frontend/src/features/offer-studio/schemas/pricing.schema.ts`
   - ETL Contract si el nuevo flujo toca analytics.
3. Refinar `SPEC.md` con sub-steps concretos (migration + domain + DTO +
   prompt + codegen + schema unlock + sales-agent block + landing
   consume + golden roundtrip).
4. Escribir `ACCEPTANCE.md`.
5. Arrancar `protocol/PRE_FLIGHT.md`.

## Resultado final esperado

- 3 fields nuevos persistidos (tax_included bool, installments_available
  text, accepted_payment_providers jsonb[]).
- Extraction prompt closing extendido.
- `offer_field_paths.json` regenerado con 126 paths (actualmente 123).
- Allowlist shrink: `KNOWN_UNRESOLVED_PATHS.size === 56`. Cap del ratchet
  baja a 56.
- Golden fixture round-trip valida los 3 fields nuevos.
