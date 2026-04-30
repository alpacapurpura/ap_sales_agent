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
| 2026-04-29 | Suggestion engine heuristico (no LLM ranking) | Latencia <10ms, costo cero. LLM ranking = backlog SI motor heuristico no alcanza (PI-2 S2+) |
| 2026-04-29 | Persistencia suggestions via copilot_trace_event (no tabla nueva) | Zero migracion. ML feedback loop = backlog PI-2 S2+, migrar si volumen lo justifica |
| 2026-04-29 | provider_priority: int per provider (tiebreak explicito) | Orden opaco fragil cuando lleguen brand/copilot/SA providers; peso explicito = A/B-testable |

## Capacidades actuales

- **Suggestion engine + provider registry** (BE motor): ranking heuristico, route-scoped providers, observability via `copilot_trace_event(event_type=suggestion_shown|suggestion_accepted)`. Inicial: `OfferSuggestionProvider` (preset-flag-driven). Surface FE smart-chips = PR siguiente (FE swap del stub `useSuggestions`).
  - Introducida: PR-2 (PI-2, S1, 2026-04-29)
  - Estado: BE motor live, FE consumiendo stub aun
  - Operable copilot: indirecto (alimenta smart chips bajo input chat)
  - Providers registrados: `offer` (route `offer-studio`, priority 0)
  - Providers pendientes: brand, sales_agent, copilot (PRs siguientes)
  - Heuristic rules: 6 reglas (no offers -> create chip; high_ticket -> pricing; recurring_billing -> billing; is_lead_magnet -> link core; incomplete promise.headline -> variants; lead_magnet sin core -> link)

### Cap: Backfill content→blocks (data migration v1→v2)
- Introducida: PR-3 (PI-2, S1, 2026-04-29)
- Estado: script + audit table live, migration marker shipped. Backfill ejecuta manual per-tenant via `python scripts/backfill_copilot_content_to_blocks.py`
- Operable copilot: no (mantenimiento interno transparente al user)
- CLI flags: `--dry-run` (default), `--apply`, `--batch-size N` (default 100), `--tenant-id X`, `--confirm-prod` (regex `prod\.` interceptor), `--max-failure-rate 0.05`
- Audit: tabla `copilot_backfill_runs` (run_id, tenant_id, stats, status, mode)
- Codec v1 warning: sampled 1/100 reads logean `copilot_message_legacy_v1_read` (threshold ops día 30+ con 0 warnings → safe drop codec v1 path)
- Idempotente: re-run = 0 rows updated. Optimistic lock `WHERE messages = :original` evita conflict mid-flight
- Out of scope: DROP `content` column (safety wait, PR futuro tras N días sin warnings v1)

### Cap: BudgetGuard.check — gating cross-cutting LLM budget (Others bucket)
- Introducida: PR-2 (PI-1, S0, commit `dbc367f2`, 2026-04-29) — **primitiva expuesta; wiring al orchestrator diferido S2**
- Estado: primitiva disponible en `shared/billing/application/budget_guard.py`
- Operable copilot: no directamente (infra pre-LLM-call)
- Bucket: copilot consume del pool **Others** (`plan_config.llm_budget_total_usd * (1 - sales_agent_reserved_pct)`)
- Invariante: Others exhausto NO bloquea `sales_agent` (pools independientes, arch test property-based enforce)
- Stale MV soft cap: si `mv_refresh_log` > 1h, admite 5% overrun (cap 105%) para no bloquear en datos stale
- Firma: `await budget_guard.check(tenant_id, agent_kind="copilot", estimated_cost_usd=Decimal("..."))`
- Wiring S2: `copilot/application/orchestrator/chat.py` — antes del `llm.ainvoke()`. No modifica §3-protected surfaces.
