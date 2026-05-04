---
module: commercial-calendar
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/commercial-calendar/"
  stories_dir: "../stories/commercial-calendar/"
  domain_doc: "../../domains/module_commercial-calendar.md"
  legacy_pm_nico: "../../pm-nico/current-state/commercial-calendar.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# commercial_calendar — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Supporting |
| Estado | activo (mínimo) |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_commercial_calendar.md` |

## Qué hace por el user
Calendario eventos comerciales — feriados sistema-wide + promociones del tenant. Útil para timing de campañas (Black Friday, Día de Madres LATAM, etc).

## Capacidades actuales
- Sistema-wide holidays (multi-país LATAM)
- Tenant-specific promotional events
- Country code filtering

## Capacidades operables desde copilot
- Consultar próximos eventos (parcial)
- **Gap:** sugerir campaña basado en evento próximo

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Holidays catalog | activo | |
| Tenant events | activo | |
| FE | placeholder | No hay UI dedicada hoy |

## Conexiones cross-módulo
- **Lee de:** —
- **Lo lee:** copilot

## Dolor user / oportunidades detectadas
_Probable: oportunidad gigante para timing de campaigns (PI-1 lo aprovechará)._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
_Pendiente._
