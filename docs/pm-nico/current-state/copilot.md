# copilot — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Supporting (transversal) |
| Estado | activo (en mejora — PI-2) |
| Última actualización | 2026-04-29 (bootstrap) |
| Doc técnico | `docs/domains/module_copilot.md` |

## Qué hace por el user
Asistente in-app conversacional. Interfaz primaria de Nicolify. User configura, opera y consulta cualquier módulo conversando con el copilot. Auto-completa formularios, sugiere acciones, explica métricas, ejecuta tools.

## Capacidades actuales
- Chat UI in-app
- LangGraph orchestrator + sub-agents (deepagents)
- Tools transversales (extract_document_to_fields, propose_field_updates, format_for_channel)
- Module Registry → introspección Pydantic schemas
- Route-based tool selection (solo tools relevantes a la ruta actual)
- Cards (UI cards emitidas por tools)
- Trace observability completa (turn_envelope, llm_call, mutation_journal)
- Per-tenant prompt caching (cache hit rate >50% target)
- Tier routing (classifier → modelo correcto)
- Cost tracking (cycle billing 25-25, MV daily aggregation)
- Domain event bus para subscribers cross-cutting
- Subagent isolation (stream provenance classifier)
- Outbox migration ready behind `USE_OUTBOX_PATTERN_COPILOT` flag (OFF default; PI-1 S0 PR-1) — emisores (`extraction_card_flow`, `domain_subscribers`, `chat orchestrator`, `extract_from_doc tool`) routean vía `EventBusAdapter` y enquean a `domain_event_outbox` cuando ON
- `extraction_card_flow` usa `@idempotent` decorator (PI-1 S0 PR-1 Sub-D) reemplazando ad-hoc Redis SETEX → at-least-once dedup centralizado, soft-fail Redis, mismo TTL 86400s

### Cap: Rate limit voice + per-tenant media/voice limits
- Introducida: PR-1 (PI-2, S1, commits `2d0b9e0e` + `caacdffa`, 2026-04-29)
- Estado: live
- Operable copilot: no (infra BE — protege Whisper budget + cuota tenant)
- Surface admin: Streamlit `/admin/copilot-limits` (CRUD overrides per-tenant)
- Defaults: voice 6 RPM, media 25 MiB, /media/upload 30 RPM
- Cap upper override media: 100 MiB (CHECK editable post planes per-tenant)
- Tablas: `copilot_tenant_limits` (overrides) + `copilot_tenant_limits_audit` (append-only)
- Legacy `/voice/transcribe`: 410 Gone con `X-Deprecation-Notice` header (FE migration → PR follow-up cross-stack)

## Capacidades operables desde copilot (meta — qué hace user CON copilot)
- Auto-fill formularios (sólido — el #1 caso uso)
- Subir doc/PDF → extracción a campos (sólido)
- Preguntas sobre métricas (parcial)
- Ejecutar tools (crear, modificar, listar)
- Procedimientos guiados step-by-step (parcial)
- **Gap general:** consistencia entre módulos. Algunos tienen tools ricos, otros poco.

## Estado calidad funcional
| Capacidad | Estado | Notas |
|---|---|---|
| Auto-fill | sólido | Caso uso #1, mature |
| Doc extraction | sólido | |
| Tools registry | sólido | Route-based |
| Observabilidad | sólido | Rebuild 2026-04 (`copilot_llm_call`, MV, retention) |
| Subagent isolation | sólido | Stream provenance fix |
| Cost tracking | sólido | Cycle 25-25 implementado |
| Mutaciones que persisten | sólido | mutation_journal |
| Conversación largas (Lost-in-the-Middle) | parcial | Mitigation con per-turn anchor |
| RAG style anchors per tenant | placeholder | Slot 5 en compiled prompt — pendiente >=50 mensajes reales aprobados |

## Conexiones cross-módulo
- **Lee de:** brand, offer, connections, crm, analytics, landing, commercial_calendar, sales_agent
- **Lo lee:** brand, offer

## Dolor user / oportunidades detectadas
_Pendiente captura entrevistas users actuales._

## PIs históricos
| PI | Cambio | Fecha cierre |
|---|---|---|
| Observabilidad rebuild | typed event-sourced LLM-call log + cycle billing | 2026-04 |
| Subagent isolation | Stream provenance classifier | 2026-04 |
| Extraction feedback | (ux-session 2026-04-22) | 2026-04 |

## Decisiones producto vinculadas
| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04 | Schema introspection, no hardcode fields | Resiliencia a cambios brand/offer schemas |
| 2026-04 | Route-based tool selection | Reducir surface attack + foco contextual |
