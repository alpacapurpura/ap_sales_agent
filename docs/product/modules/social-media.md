---
module: social-media
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/social-media/"
  stories_dir: "../stories/social-media/"
  domain_doc: "../../domains/module_social-media.md"
  legacy_pm_nico: "../../pm-nico/current-state/social-media.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# social_media — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Growth |
| Estado | placeholder |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_social_media.md` |

## Qué hace por el user
**Placeholder.** No implementado como módulo. Lectura social orgánico vive en `connections` (channels via Manychat / IG / FB / TikTok). Generación contenido vive en `assets` + skill `content-hunter`.

## Capacidades actuales
- (Vía assets) Generar copies / ideas videos / flyers
- (Vía analytics) Métricas orgánico (reach, engagement)
- (Vía connections) Programación posteo (limitada — depende canal)

## Capacidades operables desde copilot
- Generar copy para post (parcial — vía assets/content-hunter)
- **Gap:** programar posteo conversacionalmente
- **Gap:** moderar comentarios automáticamente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Content gen | activo (vía assets) | |
| Programación posts | placeholder | |
| Moderación auto | placeholder | |

## Conexiones cross-módulo
- **Lee de:** (vía analytics, connections)
- **Lo lee:** —

## Dolor user / oportunidades detectadas
_Probable: módulo dedicado social media (programación + moderación + content calendar) es PI futuro grande._

## PIs históricos
_Ninguno._

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| _inicial_ | Diferir módulo | Skill `content-hunter` + assets cubre generación. Programación nativa requiere expansión Meta API |

## Capabilities

> **Nota**: módulo BE `social_media` está vacío (solo `__init__.py`). Las capabilities listadas son cross-module (analytics + connections + assets + content-hunter skill). Todo placeholder se mantiene a nivel BE.

| ID | Name | Status | Stories live/total |
|---|---|---|---|
| organic-metrics-via-analytics | Métricas orgánicas vía analytics (read-only) | live | 1/1 |
| content-generation-via-assets | Generación contenido social vía assets + content-hunter | live | 1/1 |
