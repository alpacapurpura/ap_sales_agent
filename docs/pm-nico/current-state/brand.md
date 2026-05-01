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
- Outbox cutover ON (PR-6 Sub-D commit `97780627`, 2026-04-30) — `USE_OUTBOX_PATTERN_BRAND=True` default. Emisores (`brand_repository`, `personality_service`, `workers/tasks brand_summary_regen`) routean vía `EventBusAdapter` y enquean a `domain_event_outbox`. After-commit dispatch preserva debounce semántica. Tests F-7 sin mocks: 4 verde.

**DEUDA RESIDUAL DR-7 (Sub-D-2 / S3 follow-up):** BudgetGuard wiring brand 7 LLM callsites diferido — `style_analyzer/nodes.py` (5) + `voice_fidelity/grader.py` (1) + `services/personality_service.py` (1) usan sync `LLMFactory.get_service().generate_response(...)`. Wrap requiere per-callsite refactor con `BudgetGuardingLLMService`. Allowlist `tests/architecture/test_budget_guard_pre_llm_call.py KNOWN_UNGUARDED` documenta exception con TODO Sub-D-2.

### Cap: BudgetGuard architectural seam (PR-7 Sub-G)
- Introducida: PR-7 Sub-G (PI-1, S3, commit `d7fc7288`, 2026-04-30)
- Estado: seam-ready, runtime wiring DEFERRED a S4
- Helper `get_guarded_llm_service(tenant_id, agent_kind, budget_guard, model_hint)` SSoT en `shared/billing/application/llm_guards.py`. Pattern caller-provided DI: caller pasa `BudgetGuard` instancia → wrappea inner `LLMFactory.get_service()`; caller pasa `None` → retorna plain inner (test path + production while DI not wired).
- Brand 7 callsites + Sub-H quality_eval workers wiring DEFERRED S4 — drift detectado durante build: architect CONTRACT cited `BudgetRepositoryImpl(db)` para construir `BudgetGuard` sync, esa clase NO existe. Sin proper FastAPI provider + ARQ worker startup DI, no hay manera de construir `BudgetGuard` sync inline en helper.
- Ratchet `KNOWN_UNGUARDED` queda en 5 entries (no shrink en PR-7). DR-7 brand BudgetGuard + DR-8 quality_eval stay open architecturally; S4 cierre con FastAPI provider para HTTP brand routes + ARQ `WorkerSettings.on_startup` DI para `weekly_*_quality_eval` + `brand_summary_regen` worker.
- Helper architectural seam SHIPPED — primera siteación que adquiera `BudgetGuard` instancia auto-gates via helper.

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
