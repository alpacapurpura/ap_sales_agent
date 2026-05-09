# Story 4 — CRM + Analytics + Landing + Connections lift

> **Outcome:** luana-platform-migration · **Sequence:** 4/14

## What

Lift 4 módulos densos a packages:

| Module | Destino | Notas |
|---|---|---|
| `crm` | `luana-core-crm` | CDP genérico, custom_fields data-driven |
| `analytics` | `luana-core-analytics-engine` | ETL framework + 12 providers + metric_catalog + extraction_contract + scheduler + workers |
| `landing` | `luana-core-landing` | Page generator engine, templates registry |
| `connections` (engine) | `luana-core-connections` | OAuth + adapter pattern + channel base classes |

## Critical: ETL extraction-contract regen

Analytics tiene workflow `make extraction-contract` SSoT-critical. Story 4 debe verificar que regen funciona post-split (contract.py + metric_catalog.py source of truth).

## Brand-extension reservado

Channel adapters brand-specific (Lupulo POS, Vitalia payment gateway) NO migran a core en esta story. Quedan en respective `vertical-{niche}/connections/` packages (Stories 11-13).

## Acceptance

- 4 packages publicados v0.0.4-alpha
- ETL contract regen smoke test PASS
- Connections engine permite registro de adapter externo (smoke con stub adapter)

## Effort: 16-22 tickets, ~5 días
