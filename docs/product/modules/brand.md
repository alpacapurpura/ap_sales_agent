---
module: brand
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/brand/"
  stories_dir: "../stories/brand/"
  domain_doc: "../../domains/module_brand.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# brand — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Brand Studio |
| Estado | activo |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_brand.md` |

## Qué hace por el user
Captura identidad de marca del user. Vía 2 caminos: scraping web (si tiene website) + carga manual + auto-fill copilot. Genera arquitectura marca completa (identity, voice, story, positioning, narrative, communication-style, team, testimonials, authority).

## Capacidades
> Auto-list generated from `docs/product/capabilities/brand/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot
- Auto-fill formularios desde docs/scraping (sólido)
- Update fields conversacionalmente (parcial)
- Cloning estilo comunicacional desde chat real (sólido)
- **Gap:** revisar/auditar marca completa conversacionalmente

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Web scraping | sólido | Múltiples fuentes |
| Doc extraction | sólido | LLM-powered |
| Formularios | sólido | Form-runtime homologado |
| Personality engine | sólido | 3-pillar (dims/patterns/exchanges) — SSoT del estilo agent |
| Buyer Personas | activo | Multi-persona, upload docs OK |
| Authority vault | activo | Refactor field-contract-platform 2026-04 |
| Brand data adapter ORM→DTO | live | PR-1 PI-7 (commit `1bdcfdc9`, 2026-05-01) — `PersonalityProfileDTO.model_validate(orm).model_dump()` canonical Pydantic v2 path. Pattern aplicable a otros adapters brand/offer si encuentran type-mismatch ORM vs Pydantic |

## Conexiones cross-módulo
- **Lee de:** copilot
- **Lo lee:** sales_agent, copilot

## Dolor user / oportunidades detectadas
| Fecha | Señal | Origen | Opportunity? |
|---|---|---|---|

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| _migración: brand → brand-studio_ | foundation-first strangler fig | 2026-04 (refactor) |
| PI-7-app-stability-restore S1 PR-1 | Bug #7 fix — `brand_data_adapter` convierte ORM PersonalityProfileModel via `PersonalityProfileDTO.model_validate()` antes serialize. Restaura sales_agent functional | 2026-05-01 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón | PI/PR |
|---|---|---|---|
| 2026-04-28 | Voz sales_agent vive 100% en `personality_profiles.system_instruction` | SSoT única, sin mirror tables, sin fine-tune | — |

## Capabilities (auto-mapped 2026-05-04)

- [brand-identity-visuals](../capabilities/brand/brand-identity-visuals.yaml) — live, 2 stories
- [brand-personality-voice](../capabilities/brand/brand-personality-voice.yaml) — live, 2 stories
- [brand-buyer-personas](../capabilities/brand/brand-buyer-personas.yaml) — live, 1 story
- [brand-extraction](../capabilities/brand/brand-extraction.yaml) — live, 1 story
- [brand-credentials](../capabilities/brand/brand-credentials.yaml) — live, 1 story (2 pending YAML)
