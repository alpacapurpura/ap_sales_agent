---
module: tenant-domains
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/tenant-domains/"
  stories_dir: "../stories/tenant-domains/"
  domain_doc: "../../domains/module_tenant-domains.md"
  legacy_pm_nico: "../../pm-nico/current-state/tenant-domains.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# tenant_domains — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Supporting |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_tenant_domains.md` |

## Qué hace por el user
Permite al user usar su dominio propio para landings, booking pages, etc. Vía Cloudflare Custom Hostnames.

## Capacidades actuales
- Add custom domain
- DNS verification
- SSL automático (Cloudflare)
- Status monitoring
- Remove domain

## Capacidades operables desde copilot
- **Gap:** flow OAuth + verificación DNS conversacional

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Cloudflare CHM | sólido | |
| Verificación DNS | activo | |
| SSL | sólido | Auto |

## Conexiones cross-módulo
- **Lee de:** —
- **Lo lee:** scheduling

## Dolor user / oportunidades detectadas
_Pendiente. Probablemente fricción setup DNS para no-técnicos._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
_Pendiente._
