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

## Capacidades actuales
- Auto-gen landing desde Offer (templates dinámicas)
- Preview antes publicar
- Slug editable
- Publish / unpublish
- Sections múltiples (hero, beneficios, testimonios, FAQ, CTA)
- Custom domain integration (vía tenant_domains)

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
