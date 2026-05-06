---
module: crm
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/crm/"
  stories_dir: "../stories/crm/"
  domain_doc: "../../domains/module_crm.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# crm — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo |
| Última actualización | 2026-04-30 (PR-10+PR-11+PR-12 shipped — sprint S4 cerrado, MVP 1 Telegram end-to-end) |
| Doc técnico | `docs/domains/module_crm.md` |

## Qué hace por el user
CDP (Customer Data Platform) interno. Almacena contactos, eventos del journey, pipeline ventas. Le permite al user ver TODOS sus leads/clientes/customers cross-canal en un solo lugar. Identidad unificada (multi-canal, deduplicación).

## Capacidades
> Auto-list generated from `docs/product/capabilities/crm/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Buscar contacto (parcial)
- Ver pipeline conversacionalmente (parcial)
- **Gap:** crear/modificar contacto vía copilot
- **Gap:** segmentación dinámica conversacional

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Contactos + identidad | sólido | CDP pattern 3-tabla |
| Journey events | activo | |
| Pipeline | activo | |
| UI dashboard | sólido | |
| Segmentación avanzada | placeholder | |

## Conexiones cross-módulo
- **Lee de:** offer
- **Lo lee:** sales_agent, copilot, scheduling, analytics, offer

## Dolor user / oportunidades detectadas
_Pendiente. Probablemente input para PI-1 campaigns (segmentos)._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| _inicial_ | CDP pattern 3-tabla (contacts + identities + events) | Soporte multi-canal sin duplicar |
