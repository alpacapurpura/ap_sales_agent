---
module: connections
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/connections/"
  stories_dir: "../stories/connections/"
  domain_doc: "../../domains/module_connections.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-04
---

# connections — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Config |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_connections.md` |

## Qué hace por el user
Conexiones a sistemas externos. User conecta sus redes/sistemas/pasarelas y Nicolify orquesta. Sin connections, ni sales_agent ni analytics ni assets funcionan.

## Capacidades
> Auto-list generated from `docs/product/capabilities/connections/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Status conexión (sólido)
- Reconectar plataforma (parcial)
- **Gap:** OAuth conversacional (entender contexto + iniciar flow)

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Meta OAuth | sólido | |
| Manychat integration | sólido | Webhooks + tags + custom fields |
| Shopify | sólido | |
| Google services | sólido | |
| MailerLite | activo | |
| Connection status UI | sólido | Coverage 90%+ |
| Instagram Direct Login | placeholder | OAuth credentials configured, flow pendiente |

## Conexiones cross-módulo
- **Lee de:** sales_agent, analytics
- **Lo lee:** sales_agent, copilot, scheduling, analytics

## Dolor user / oportunidades detectadas
| Fecha | Señal | Origen | Opportunity? |
|---|---|---|---|
| pendiente | IG Direct Login OAuth | implementación pausada | pendiente |

## PIs históricos
_Sin tracked aún en pm-nico._

## Decisiones producto vinculadas
_Pendiente._
