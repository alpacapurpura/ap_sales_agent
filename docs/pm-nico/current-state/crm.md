# crm — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Sales |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_crm.md` |

## Qué hace por el user
CDP (Customer Data Platform) interno. Almacena contactos, eventos del journey, pipeline ventas. Le permite al user ver TODOS sus leads/clientes/customers cross-canal en un solo lugar. Identidad unificada (multi-canal, deduplicación).

## Capacidades actuales
- Tabla contactos con identidad multi-canal (email, phone, IG handle, etc)
- IdentityType enum (3-tabla pattern)
- Journey events (touch points lifecycle)
- Pipeline ventas (etapas)
- Lifecycle scoring
- Soft delete (`deleted_at`)
- Tenant aislado UUID
- Listado / filtrado / búsqueda

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
