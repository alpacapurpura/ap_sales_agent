---
module: copilot
last_audit: 2026-05-04
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/copilot/"
  stories_dir: "../stories/copilot/"
  domain_doc: "../../domains/module_copilot.md"
  legacy_pm_nico: "../../pm-nico/current-state/copilot.md"
active_projects: []                              # auto-populated by /pm cuando hay PIs activos tocando este módulo
---

# copilot — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Supporting (transversal) |
| Estado | activo (en mejora — PI-2) |
| Última actualización | 2026-05-01 (PR-2 PI-5 telegram orchestrator hookup live) |
| Doc técnico | `docs/domains/module_copilot.md` |

## Qué hace por el user
Asistente in-app conversacional. Interfaz primaria de Nicolify. User configura, opera y consulta cualquier módulo conversando con el copilot. Auto-completa formularios, sugiere acciones, explica métricas, ejecuta tools.

## Capacidades actuales
- Chat UI in-app
- **Canal Telegram (live)** — DMs linkeados magic link + orchestrator real respondiendo + memory cost-aware (`TELEGRAM_CONTEXT_WINDOW_CONFIG` 3000/15/600/12000) + cache prefix ≥2048 tokens activo per-channel + tool subset filter runtime + format adapter MarkdownV2. PI-5 S2 PR-2 shipped 2026-05-01
- LangGraph orchestrator + sub-agents (deepagents)
- Tools transversales (extract_document_to_fields, propose_field_updates, format_for_channel)
- Tool registry SSoT `ToolGroupMeta.available_channels` (PI-5 PR-1) — channel-aware filtering web|telegram|whatsapp
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

### Cap: Canal Telegram — DMs linkeados magic link
- Introducida: PR-1 (PI-5, S1, commit `c1fa2909`, 2026-04-30)
- Última modificación: PR-2 (PI-5, S2, commit `d09799b9`, 2026-05-01) — orchestrator real reemplaza placeholder
- Estado: **live (orchestrator real + memory cost-aware + cache fragment ≥2048 tokens activo)**
- Operable copilot: sí (orchestrator real responde; tools telegram-allowed 12+ groups; cache prefix ahorro tokens activo)
- Surface API: `/api/v1/copilot/telegram/{webhook,link-tokens,link-status,link}`
- Surface FE: `/{tenantId}/settings/copilot/telegram` page + `<TelegramLinkingClient />`
- Tablas: `copilot_channel_links` + `copilot_link_tokens` + `copilot_conversations` (cols `channel_type`, `channel_chat_id`)
- Webhook: NON-BLOCKING enqueue ARQ <200ms, valida `X-Telegram-Bot-Api-Secret-Token`, filtra `chat.type='private'`
- Bot adapter: global Nicolify (1 token env var `COPILOT_TELEGRAM_BOT_TOKEN`), rate-limited 30 msg/sec global + per-chat lock
- Magic link: HMAC-SHA256, TTL 15 min, single-use, hash en DB (no plaintext)
- Tool subset SSoT: `ToolGroupMeta.available_channels` (web-only: `navigation`, `guided`, `landing.mutations`, `offer_section.mutations`) — runtime filter validado PR-2
- Separación física vs sales_agent: 2 bots, 2 tokens, 2 webhooks, 2 schemas. Cero shared state. Arch fitness tests enforce
- Webhook dev live: `https://dev-api.nicolify.com/api/v1/copilot/telegram/webhook` → `@nicolify_dev_bot`. setWebhook configurado con secret_token
- Operación pendiente Chris: BotFather setWebhook prod `@nicolify_bot` post-deploy

### Cap: Canal Telegram — orchestrator real + memory cost-aware + prefijo cacheable Anthropic
- Introducida: PR-2 (PI-5, S2, commits `d09799b9` + `8b180584` + `a6c6ad3d`, 2026-05-01)
- Estado: live
- Operable copilot: sí (orchestrator real, memory windowed cost-aware, cache prefix ≥2048 tokens activo per-channel)
- Surface code: `modules/copilot/application/memory/` + `modules/copilot/application/orchestrator/{chat,graph,deep_agent,system_prompt_layout,invoke_result}.py` + `modules/copilot/infrastructure/workers/telegram_worker.py` + `modules/copilot/infrastructure/repositories/conversation_repository.py`
- Memory: `TELEGRAM_CONTEXT_WINDOW_CONFIG` (RAW_WINDOW_TOKENS=3000, RAW_WINDOW_MAX_MESSAGES=15, RAW_WINDOW_MIN_MESSAGES=4, SUMMARY_MAX_CHARS=600, SUMMARY_TARGET_TOKENS=200, NUDGE_AFTER_TOTAL_TOKENS=12000, NUDGE_HARD_LIMIT_TOKENS=20000, NUDGE_AFTER_MESSAGE_COUNT=20). Inyección via `for_channel(channel)` classmethod
- Cache: `TELEGRAM_CHANNEL_CONTEXT` fragment ~2200 tokens stable bytes Spanish prose. Sonnet floor + Kimi K2.6 ≥1024 cubierto. Web bytes byte-idénticos preservados (builder devuelve `""` cuando channel != telegram). Arch fitness `test_telegram_cache_prefix_meets_anthropic_threshold` ≥2048
- Tool subset runtime filter: deep_agent passa `channel=ctx.channel or "web"` a `get_tools_for_context()`. Web-only excluded para channel=telegram
- Format: MarkdownV2 escape via `format_for_channel_impl(channel_id='telegram')` shared reuso (NO new function)
- Conversation lookup: `ConversationRepository.get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` tenant-scoped optimistic SELECT-then-INSERT. UNIQUE constraint deferred S5 PR-5
- Orchestrator entrypoint: `CopilotOrchestrator.invoke_text(channel='web', ..., context: ClientContextDTO | None)` sibling de `stream_chat`. Comparte `_prepare_conversation` + `_run_graph_stream`. Dispatch canal: `context.channel or kwarg or "web"`
- Resilience: 30s `asyncio.wait_for` orchestrator timeout + per-dependency try/except (lookup/orchestrator/format/bot send) + structured success log con cache metrics + fallback CTA template friendly
- Deuda técnica explícita: DTO cache token fields hardcoded 0 (S5 wire-up); `invoke_text` outer except defensive `set_turn_error` (S5); UNIQUE constraint conversations multi-channel (S5 PR-5)

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
| Observability lifecycle base | live | PR-2 (PI-1.1, S2, commit `d80d15f5`, 2026-05-01) — refactored `ObservabilityContext` to subclass `CopilotObservabilityContext(BaseObservabilityContext)` shared. Capability unchanged user-facing, 4260 traces preserved, back-compat alias |
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

### Cap: LLM stack DeepSeek V4-Flash infra ready (wiring PR-4 pendiente)
- Introducida: PR-3 (PI-2, S2, commit `8b8f538d`, 2026-04-30)
- Estado: PARTIAL — infra live, wiring upstream LLMClassifier+RollingSummarizer factory PENDIENTE PR-4
- Operable copilot: no directamente (infra LLM layer, transparente al user)
- Components live: model_config env override layer, DeepSeekLLMProvider adapter (OpenAI-compatible API + retry/timeout), provider_factory get_llm_provider_for_tier + _FallbackLLMProvider chain DeepSeek→OpenAI single retry, eval gate framework (golden_dataset + runner CLI + scorers classifier/summarizer ROUGE+cosine)
- Goldens dataset: 100 ejemplos versionados (50 classifier + 50 summarizer, 5 cat × 8 + 10 adversarial each)
- Migration: alembic 114 idempotente — pricing snapshot deepseek-v4-flash ($0.14 in / $0.28 out per 1M)
- Env flags ready: `COPILOT_TIER_<NANO|MINI>_{MODEL_NAME, PROVIDER, PRICE_INPUT_PER_1M, PRICE_OUTPUT_PER_1M}` + `DEEPSEEK_API_KEY`
- Cost reduction projection post wiring: NANO -30% in/-78% out, MINI -81% in/-94% out vs gpt-5.4 actual
- Wiring upstream PENDIENTE PR-4: LLMClassifier factory + RollingSummarizer + TitleGenerator (~50 LOC + 24 tests + .env update)

### Cap: 4 suggestion providers — multi-route smart-chips
- Introducida: PR-2 (PI-2, S2, commit `64374b55`, 2026-04-30)
- Estado: live
- Operable copilot: indirecto (chips habilitan exploración rápida cualquier route)
- Providers registrados: offer (route `offer-studio`, priority=0), brand (route `brand-studio`, priority=10), sales_agent (route `sales`, priority=10), copilot (transversal, priority=5)
- Heurísticas tabuladas per provider (CONTRACT D-3/D-4/D-5)
- Cap engine total <11ms p99 con 4 providers (per CONTRACT D-15)

### Cap: SalesAgentObservabilityPort cross-module read-only
- Introducida: PR-2 (PI-2, S2, commit `64374b55`, 2026-04-30)
- Estado: live
- Operable copilot: indirecto (alimenta SalesAgentSuggestionProvider chips)
- Path: `backend/src/shared/links/ports/sales_agent.py` (port + DTO PII-stripped + factory)
- Adapter: `backend/src/modules/sales_agent/application/services/observability_adapter.py`
- §3 protected: solo lectura `enrollments` + `messages`. NO toca Closer Studio API/WS, BufferService, OutputManager, FollowUp, PromptVersionModel, agent_state_checkpoint
- Preserva ratchet F1 `copilot→sales_agent` 0 entries (port-mediated cross-module)

### Cap: offer_section_tools pure expansion (cero deuda S1 PR-2)
- Introducida: PR-2 (PI-2, S2, commit `64374b55`, 2026-04-30)
- Estado: live
- Cierra deuda S1 PR-2 D-9 (Q1 expansion vs additive trade-off pragmático)
- Verificación: `grep -n '"suggestions": \[hint\]' offer_section_tools.py` = 0 hits hardcoded
- Engine-driven: tools llaman `_engine_suggestions_for_context()` → engine.get_suggestions(ctx) → providers ranked

### Cap: BrandDataPort extension additive
- Introducida: PR-2 (PI-2, S2, commit `64374b55`, 2026-04-30)
- Estado: live
- 2 nuevos métodos abstract: `get_buyer_persona_count(tenant_id) -> int`, `get_active_personality_profile_present(tenant_id) -> bool`
- Adapter `BrandDataAdapter` impl con repo soft-delete handling

### Cap: Smart-chips dinámicas FE consume engine + producer event
- Introducida: PR-1 (PI-2, S2, commits `e53b7ef6` + `824c946a`, 2026-04-30)
- Estado: live
- Operable copilot: indirecto (chips habilitan exploración rápida bajo input chat)
- Consumer FE: `useSuggestions()` React Query hook (queryKey [route, conversationId], staleTime 5min)
- Producer: `useSuggestionAccept()` mutation fire-and-forget → endpoint `POST /copilot/suggestions/accept` → event `SuggestionAccepted` → subscriber S1 escribe `copilot_trace_event`
- Endpoint motor: `POST /copilot/suggestions` retorna `{suggestions, breakdown, latency_ms}` best-effort 200
- Métricas adopción habilitadas: `SELECT COUNT(*) FILTER (WHERE event_type='suggestion_accepted') / COUNT(*) FILTER (WHERE event_type='suggestion_shown') ratio`

### Cap: Voice transcription endpoint estable (legacy retired live)
- Introducida: PR-1 (PI-2, S2, commit `e53b7ef6`, 2026-04-30)
- Estado: live
- Operable copilot: sí (voice button composer)
- FE migration: `voice-api.ts` llama `/voice/upload-and-transcribe` con D-9 shape adapter (firma pública `TranscriptionResponse` intacta — consumers sin cambios)
- Cierre deuda S1 PR-1 D-5: legacy `/voice/transcribe` 410 Gone ya NO recibe llamadas FE (verificable `grep -rn "voice/transcribe" frontend/src/` = 0 hits activos)

### Cap: BudgetGuard.check — gating cross-cutting LLM budget (Others bucket)
- Introducida: PR-2 (PI-1, S0, commit `dbc367f2`, 2026-04-29) — **primitiva expuesta; wiring al orchestrator diferido S2**
- Estado: primitiva disponible en `shared/billing/application/budget_guard.py`
- Operable copilot: no directamente (infra pre-LLM-call)
- Bucket: copilot consume del pool **Others** (`plan_config.llm_budget_total_usd * (1 - sales_agent_reserved_pct)`)
- Invariante: Others exhausto NO bloquea `sales_agent` (pools independientes, arch test property-based enforce)
- Stale MV soft cap: si `mv_refresh_log` > 1h, admite 5% overrun (cap 105%) para no bloquear en datos stale
- Firma: `await budget_guard.check(tenant_id, agent_kind="copilot", estimated_cost_usd=Decimal("..."))`
- Wiring S2: `copilot/application/orchestrator/chat.py` — antes del `llm.ainvoke()`. No modifica §3-protected surfaces.

### Cap: Outbox cutover ON + BudgetGuard wiring single point deep_agent (PR-6 PI-1 S2)
- Introducida: PR-6 Sub-C (PI-1, S2, commit `8d2aed36`, 2026-04-30)
- Estado: live
- `USE_OUTBOX_PATTERN_COPILOT=True` default — emisores routean a `domain_event_outbox` table via `EventBusAdapter`
- `BudgetGuardingChatModel` wired single point en `build_deep_agent_graph(budget_guard, tenant_id)` DI optional. Cuando provided wraps LLM antes de `create_deep_agent`, gating todo el graph (subagentes incluido) transparentemente
- Drift resolved: CONTRACT mencionaba `provider_factory.build_chat_model` que no existe; wiring real en `build_deep_agent_graph` (LLMFactory.get_service().get_client retorna BaseChatModel LangChain)
- Tests F-7 sin mocks: 12 verde (outbox cutover + budget_guard_wiring + Others pool isolation + soft-warn + proxy attrs + build_deep_agent_graph wraps llm)
- Operable copilot: no PR-6 (infra cutover)

### Cap: LLM stack ModelRole único SSoT + DeepSeek V4-Flash NANO+FAST activo (S3 PR-1 PI-2)
- Introducida: S3 PR-1 (PI-2, S3-copilot-llm-stack-convergence, commits `d079f13b`+`773604ab`, 2026-04-30)
- Estado: shipped — cero deuda LLM routing residual
- Allowlist `KNOWN_LEGACY_LLM_FILES` shrunk **19 → 0 entries** (target ratchet alcanzado)
- ModelTier domain enum eliminado. ModelRole único SSoT (`src.core.enums.ModelRole`) con mapping cementado: NANO→NANO, MINI→FAST, REASONING→REASONING, HEAVY→AGENT.
- Capa duplicada PR-3 (`copilot/infrastructure/llm/`) DELETED total.
- RollingSummarizer + TitleGenerator refactor a `BaseChatModel` directo via `LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)` — pattern judge/intent_classifier/synthesizer dominante.
- Migration alembic 115 idempotente: column rename `tier_selected` → `role_selected` + UPDATE values mini→fast, heavy→agent en `copilot_routing_log` + `copilot_conversation`.
- `.env.example`: AI_MODEL_NANO + AI_MODEL_FAST = deepseek-v4-flash + AI_PROVIDER_*=deepseek (cost reduction esperado 4-15x). Eval gate S5 = guardrail forward.
- SSoT doc: `docs/domains/llm-routing.md`. Arch fitness: `tests/architecture/test_llm_routing_ssot.py` 3/3 verde + allowlist 0.

### Cap: LiteLLM Proxy motor multi-provider centralizado (S3 PR-2 PI-2)
- Introducida: S3 PR-2 (PI-2, S3-copilot-llm-stack-convergence, commit `06065f6c`, 2026-04-30)
- Estado: shipped — Docker svc `visionarias_litellm` v1.83.10-stable + healthcheck `GET /health/readiness`
- Operable copilot: indirecto — todos los consumers `LLMFactory.get_service()` ahora dispatch via LiteLLM Proxy endpoint OpenAI-compat (`http://visionarias_litellm:4000/v1`)
- Surface: `shared/infrastructure/llm/providers/litellm.py` (197 LOC) + `router.py` refactor toggle-based + `litellm_config.yaml` SSoT 6 modelos + `docker-compose.yml` svc append
- Architecture: 18 D-decisions ejecutadas. Dispatch único `LiteLLMService` cuando `LITELLM_PROXY_ENABLED=True` (default). Toggle `False` → rollback emergency a per-provider legacy adapters (lazy imports, eliminación física S4 PR-1).
- Fallback chain transparente: `deepseek-v4-flash → openai/gpt-4o-mini`, `deepseek-reasoner → gpt-4o`, `kimi-k2.6 → gpt-4o`. `drop_params:True` auto-filter unsupported kwargs. `request_timeout 30s`.
- DB separada `visionarias_litellm_db` (Prisma vs Alembic isolation, migration 116 idempotente). Cost tracking SSoT inmutable `model_pricing_snapshot` preservado, LiteLLM `LiteLLM_SpendLogs` DISABLED (PII guard).
- Recorder `copilot_llm_call.model` strip prefix `<provider>/<model>` → `<model>` (preserve queries Streamlit `/costo-copilot` + `/marketing-kb`).
- Admin Streamlit `/admin/llm-virtual-keys` read-only (CRUD UI completo S4 PR-1).
- Habilita: S4 PR-1 (DB registry + admin UI hot-swap <60s sin deploy), S4 PR-2 (GrowthBook per-tenant override + A/B), S5 (eval gate pre-promote).
- Tests: 24 nuevos verde (5 service + 3 router + 4 recorder + 5 migration + 7 admin smoke). Arch fitness D-18 nuevo (AST scan module-level imports). 791 PASS total.

