---
module: scheduling
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/scheduling/"
  stories_dir: "../stories/scheduling/"
  domain_doc: "../../domains/module_scheduling.md"
  legacy_pm_nico: "../../pm-nico/current-state/scheduling.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
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

## Capacidades actuales
- Sync Google Calendar (OAuth)
- Event types (tipos de cita configurables)
- Disponibilidad por timezone tenant
- Booking link público (slug)
- Custom domain integration
- Confirmación + recordatorios (vía email)
- Cancelación / reagendar

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
