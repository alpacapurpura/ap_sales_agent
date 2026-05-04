---
module: advertising
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/advertising/"
  stories_dir: "../stories/advertising/"
  domain_doc: "../../domains/module_advertising.md"
  legacy_pm_nico: "../../pm-nico/current-state/advertising.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# advertising — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Growth |
| Estado | placeholder |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_advertising.md` |

## Qué hace por el user
**Placeholder.** No implementado como módulo. Data ads vive en `analytics` ETL (Meta Ads, Google Ads). Acción sobre ads ocurre vía `analytics` action triggers.

## Capacidades actuales
- (Sólo lectura, vía analytics) ROAS, CPL, CPM, CPC, gasto, conversiones

## Capacidades operables desde copilot
- **Gap general:** crear/modificar/pausar campañas ads conversacionalmente. Hoy es solo lectura.

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Lectura métricas | sólido (vía analytics) | |
| Creación campaña | placeholder | |
| Mod campaña | placeholder | |

## Conexiones cross-módulo
- **Lee de:** (vía analytics)
- **Lo lee:** —

## Dolor user / oportunidades detectadas
_Probable PI futuro: módulo advertising real (creación/mod ads desde Nicolify). PI-1 campaigns puede absorber parte._

## PIs históricos
_Ninguno — placeholder desde inicio._

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| _inicial_ | Diferir módulo dedicado | Analytics ETL cubre lectura. Acción se prioriza vía action triggers cuando user pide. |

## Capabilities

> **Drift documentación detectado 2026-05-04**: el module doc llama "placeholder" pero el módulo está implementado (3 services, 11 archivos test, 11 endpoints REST `/api/v1/advertising/`). Status real = `live` para asociaciones + métricas + suggestions.

| ID | Name | Status | Stories live/total |
|---|---|---|---|
| ad-offer-association | Asociación ad ↔ oferta | live | 2/2 |
| metrics-by-offer-aggregation | Métricas agregadas por oferta | live | 1/1 |
| campaign-template-suggestions | Sugerencias de templates de campaña ads | live | 1/1 |
