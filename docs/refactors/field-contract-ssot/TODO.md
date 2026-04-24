# TODO

Próximas acciones + blockers + ideas fuera-de-scope capturadas.

## Próxima acción inmediata

1. **Arrancar Fase 01** siguiendo [protocol/RESUME.md](protocol/RESUME.md) + [phases/01-field-contract-pilot-pricing/SPEC.md](phases/01-field-contract-pilot-pricing/SPEC.md).

## Blockers actuales

Ninguno.

## Pendientes por fase

### Fase 00 — DONE
- Cerrada 2026-04-24. Commits `b7398ed0`, `2822b525`, `701f6f2d` + closing.
- Allowlist ratchet fija en 59 (ADR-007). Fase 01 baja a 56.

### Fase 01 — Pricing LATAM
- Reducir `KNOWN_UNRESOLVED_PATHS` en −3 (tax_included, installments_available, accepted_payment_providers).
- Ver [phases/01-field-contract-pilot-pricing/SPEC.md](phases/01-field-contract-pilot-pricing/SPEC.md).

### Fase 02+
- Se actualizan al cerrar fase anterior.

## Fuera de scope — candidatos futuros

Ideas que aparezcan durante el refactor. NO tocar en este refactor. Post-Fase 05 revisar.

- [ ] Migrar brand-studio al mismo patrón FieldContract (después de offer-studio probado)
- [ ] Cambiar `BaseEntity.model_config` a `extra="forbid"` — requiere migration data previa
- [ ] Refactor `PricingStructure` VO para concentrar concepto pricing disperso (4 lugares hoy)
- [ ] Extraction time_increment=1 assertion para más providers Meta (ver `.claude/rules/etl-extraction-contract.md`)
- [ ] Feature flag dinámico por preset (enums condicionales) — design separado
- [ ] Buyer-persona studio adoptar form-runtime (tercer studio)

## Deuda técnica global (cross-refactor)

Agregar entries a [docs/mejoras-proceso/to-do.md](../../mejoras-proceso/to-do.md) según aparezcan.

Espejo aquí para contexto rápido:

- [ ] _pending — se popula al descubrir_

## Tech debt dentro del refactor

Capturada en [LEARNINGS.md](LEARNINGS.md) per fase bajo "Deuda técnica encontrada". Si es arreglable en la fase, se arregla. Si tangencial, entry aquí + en `docs/mejoras-proceso/to-do.md`.
