---
module: landing
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/landing/"
  stories_dir: "../stories/landing/"
  domain_doc: "../../domains/module_landing.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# landing — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Assets |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_landing.md` |

## Qué hace por el user
Genera landing page automática para cada oferta. Toma data brand + offer y produce página publicable con dominio del tenant.

## Capacidades
> Auto-list generated from `docs/product/capabilities/landing/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Crear landing desde oferta (parcial)
- Editar copy de sección conversacionalmente (parcial)
- **Gap:** preview en chat antes publicar

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Auto-gen | activo | Templates dinámicas |
| Preview | activo | UI dedicada |
| Publish | activo | Cloudflare custom hostname |
| Custom layouts | parcial | Limitado a templates predefinidos |

## Conexiones cross-módulo
- **Lee de:** offer
- **Lo lee:** copilot, offer

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
_Ninguno aún tracked en pm-nico._

## Decisiones producto vinculadas
_Pendiente._

## Capabilities (auto-mapped 2026-05-04)

- [landing-auto-generation](../capabilities/landing/landing-auto-generation.yaml) — live, 2 stories
- [landing-publishing](../capabilities/landing/landing-publishing.yaml) — live, 2 stories
- [landing-public-render](../capabilities/landing/landing-public-render.yaml) — live, 1 story
