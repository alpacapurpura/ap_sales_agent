# TODO

Próximas acciones + blockers + ideas fuera-de-scope capturadas.

## Próxima acción inmediata

1. **Arrancar Fase 00** siguiendo [protocol/RESUME.md](protocol/RESUME.md) + [phases/00-guardrail/SPEC.md](phases/00-guardrail/SPEC.md).

## Blockers actuales

Ninguno.

## Pendientes por fase

### Fase 00
- Ver [phases/00-guardrail/ACCEPTANCE.md](phases/00-guardrail/ACCEPTANCE.md).

### Fase 01+
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
