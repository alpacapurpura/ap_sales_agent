---
module: assets
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/assets/"
  stories_dir: "../stories/assets/"
  domain_doc: "../../domains/module_assets.md"
  legacy_pm_nico: "../../pm-nico/current-state/assets.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# assets — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Assets |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_assets.md` |

## Qué hace por el user
Genera material promocional automático. Copies para redes/ads/videos, flyers, imágenes, brochures. Acceso desde Offer individual y Brand Studio.

## Capacidades actuales
- AI generation copies (redes, ads, video ideas)
- Flyers / images / brochures
- Storage R2 (Cloudflare)
- MIME handling
- Templates dinámicas

## Capacidades operables desde copilot
- Generar copy para X canal (parcial)
- **Gap:** loop conversacional iterativo (ajustar tono, generar variantes)

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Copy gen | activo | LLM-driven |
| Flyer gen | parcial | Templates limitadas |
| Image gen | parcial | Pipeline básico |
| Video ideas | activo | Solo ideas, no producción |
| Brochures | placeholder | |

## Conexiones cross-módulo
- **Lee de:** —
- **Lo lee:** —

## Dolor user / oportunidades detectadas
_Probable: gap entre "ideas video" y "video producido". Oportunidad expansión._

## PIs históricos
_Sin tracked aún._

## Decisiones producto vinculadas
_Pendiente._
