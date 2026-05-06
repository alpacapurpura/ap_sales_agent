---
module: scheduling
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/scheduling/"
  stories_dir: "../stories/scheduling/"
  domain_doc: "../../domains/module_scheduling.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-04
---

# scheduling — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_scheduling.md` |

## Qué hace por el user
Sistema agendamiento integrado Google Calendar. Sales Agent agenda reuniones según disponibilidad user. Landing pública (clon Calendly) donde lead reserva cita.

## Capacidades
> Auto-list generated from `docs/product/capabilities/scheduling/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Crear event type nuevo (parcial)
- Ver agenda próximos días (parcial)
- **Gap:** modificar disponibilidad conversacionalmente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Google Calendar sync | sólido | OAuth + watch channel |
| Booking public page | sólido | Custom domain OK |
| Recordatorios | activo | Email-based |
| Multi-timezone | sólido | TenantLocale-driven |

## Conexiones cross-módulo
- **Lee de:** crm, connections, tenant_domains
- **Lo lee:** sales_agent

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
_Pendiente._
