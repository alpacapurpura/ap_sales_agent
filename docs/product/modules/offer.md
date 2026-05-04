---
module: offer
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/offer/"
  stories_dir: "../stories/offer/"
  domain_doc: "../../domains/module_offer.md"
  legacy_pm_nico: "../../pm-nico/current-state/offer.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# offer — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Offer Studio |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_offer.md` |

## Qué hace por el user
Construye Offer Ladder (gratis → low → high ticket). Para cada oferta individual, blueprint de producto con info completa (qué incluye, precio, posicionamiento, value level, archetype, variantes).

## Capacidades actuales
- Offer Ladder visual por tipo de negocio
- 21 secciones offer (homologadas, post pre-venta)
- 7 catálogos SSoT (ExpertBusinessType, ValueLevel, Section, VariantStructure, Archetype, Format, LadderHints, OfferTypePreset)
- 76 presets por tipo de negocio
- Conditional questions por preset
- Variantes (TIER, BUNDLE, etc)
- Lead magnet flow
- Upsell/downsell relationships
- Pricing con multi-currency (TenantLocale)
- Sections referencias módulos externos: LOCATION → scheduling, PRICING → connections, INSTRUCTORS → brand team

## Capacidades operables desde copilot
- Auto-fill desde docs/scraping (sólido)
- Crear oferta nueva conversacionalmente (parcial)
- Modificar fields existentes (sólido)
- Sugerir oferta faltante en ladder (parcial)

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Offer Ladder | sólido | UI homologada 2026-04 |
| Presets catalog | sólido | 76 presets, conditional questions |
| Form-runtime | sólido | Cards/Split mode automático |
| Sections homologadas | sólido | 21 secciones (de 23, eliminadas duplicadas con brand) |
| Multi-currency | sólido | TenantLocale-driven |

## Conexiones cross-módulo
- **Lee de:** crm, copilot, landing, analytics (ports)
- **Lo lee:** sales_agent, copilot, landing, crm, analytics

## Dolor user / oportunidades detectadas
_Pendiente captura._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| Offer Studio homologation | UI + sections refactor | 2026-04 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04 | Eliminadas METHODOLOGY + CREDENTIALS sections | Duplicaban brand-studio |
| 2026-04 | OfferTypePreset 7th catalog axis | Modelar presets por tipo negocio + archetype |
