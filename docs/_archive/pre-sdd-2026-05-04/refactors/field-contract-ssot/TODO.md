# TODO

Próximas acciones + blockers + ideas fuera-de-scope capturadas.

## Próxima acción inmediata

1. **Arrancar Fase 02** siguiendo [protocol/RESUME.md](protocol/RESUME.md) + crear `phases/02-migrate-sections/SPEC.md` (usar plantilla de Fase 01 como referencia).

## Blockers actuales

Ninguno.

## Pendientes por fase

### Fase 00 — DONE
- Cerrada 2026-04-24. Commits `b7398ed0`, `2822b525`, `701f6f2d` + closing.
- Allowlist ratchet fija en 59 (ADR-007). Fase 01 baja a 56.

### Fase 01 — Pricing LATAM — DONE
- Cerrada 2026-04-24. Commits `fbe4bb08`, `88383918`, `907e1dcc`, `1033d922`, `564b696c`, `a5b5f3e8`, `4abb34ba`, `28efe0e9`, `92523a6e` + closing.
- `KNOWN_UNRESOLVED_PATHS` ahora 56 (baja de 59). Cap arch test ratchet ahora 56.
- ADR-008 + ADR-009 ratificados.

### Fase 02 — Migrar 8 secciones restantes
- Crear `phases/02-migrate-sections/SPEC.md` + `ACCEPTANCE.md`.
- Secciones previstas: authority, value-stack anchor, program narrativas, subscription renames + nuevos, service new, product new, platform archetype, resto offer sections.
- 53 paths por remover de `KNOWN_UNRESOLVED_PATHS` (56 − 3 Fase 05 cross-module federados = 53 fase 02).

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

### Fase 01 descubierto

- [ ] `PaymentProvider` enum vive en `sales_agent.domain.enrollment`. Offer lo necesita sin violar DDD. Plan: en Fase 02 evaluar mover a `shared/domain/payment.py` + refactor import sites (offer + sales_agent). ADR-009 la documenta. Ya duplicado en `docs/mejoras-proceso/to-do.md` entry.
- [ ] Landing builders consumen `pricing` JSONB legacy (`pricing.pay_in_full`) no top-level fields. Alineación a FieldContract queda para Fase 05 (downstream unify).
