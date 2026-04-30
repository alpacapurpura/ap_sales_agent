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

## Capacidades actuales
- Scraping web → extracción brand info
- Upload de docs (PDF, copy existente) → extraction
- Formularios guiados secciones múltiples
- Identity (logo, colores, paleta)
- Visuals
- Story (StoryBrand framework)
- Positioning (UVP, archetype)
- Narrative
- Personality / voice tone (3-pillar engine + 6 presets + cloning chat)
- Communication style (estilo comunicacional sales agent)
- Buyer Personas (multi-persona)
- Team (instructors, miembros)
- Testimonials
- Authority vault (credenciales, methodology)
- Outbox migration ready behind `USE_OUTBOX_PATTERN_BRAND` flag (OFF default; PI-1 S0 PR-1) — emisores (`brand_repository`, `personality_service`, `workers/tasks brand_summary_regen`) routean vía `EventBusAdapter` y enquean a `domain_event_outbox` cuando ON. After-commit dispatch preserva debounce semántica.

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

## Decisiones producto vinculadas
| Fecha | Decisión | Razón | PI/PR |
|---|---|---|---|
| 2026-04-28 | Voz sales_agent vive 100% en `personality_profiles.system_instruction` | SSoT única, sin mirror tables, sin fine-tune | — |
