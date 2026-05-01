# PI-5 — Decisiones registradas

> Append-only durante PI. Owner: `/pm`. Captura razón, alternativas, fecha.

## D-PI5-001 — Bot global Nicolify único, NO per-tenant copilot

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | `@nicolify_copilot_bot` global (1 token env var). Cero per-tenant tokens copilot |
| Alternativas descartadas | A) per-tenant bot copilot — costo setup + onboarding fricción + escalabilidad 1000+ peor. B) compartir número con sales_agent — auth fragil, voz mezclada, leak risk |
| Razón | Pattern Linear/Notion. Auth limpio via magic link `chat_id`↔tenant. $0 incremental Telegram. Anti-cruce con sales_agent (sales_agent será per-tenant en su PI futuro) |
| Owner | Chris + /pm |

## D-PI5-002 — Sales_agent Telegram queda OUT OF SCOPE este PI

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Sales_agent telegram bot (per-tenant, atiende leads + grupos venta) = PI separado futuro. PI-5 SOLO copilot |
| Razón | Scope cohesivo separado. Diferente identidad bot, diferente capa connection, diferente audiencia. Asegurar arquitectura no-cruce vía 2 webhooks distintos + arch fitness test |
| Owner | Chris + /pm |

## D-PI5-003 — Open + auth in-message

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Bot accesible público. Sin link → response CTA hacia signup. Con link → copilot funcional |
| Alternativas descartadas | Closed (silencio sin link) — peor discovery, no CTA |
| Razón | Pattern industria. Sin leak (bot sin link no expone tenant data). Onboarding fricción menor |
| Owner | Chris confirma 2026-04-30 |

## D-PI5-004 — WhatsApp out of scope PI-5

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | WA queda futuro PI separado. PI-5 = Telegram only |
| Razón | Meta Cloud API limits + auth model distinto + costo número per-tenant. Mejor cohesivo Telegram first, capturar learnings, luego WA con base sólida |
| Owner | Chris confirma 2026-04-30 |

## D-PI5-005 — Switch sales_agent ↔ copilot = separación física por bot identity

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Cero shared state. 2 bots distintos = 2 tokens = 2 webhooks. Telegram routing nativo asegura no cruce |
| Razón | Más simple que routing runtime ("este mensaje para quién"). Auth + voz + observabilidad limpios. Schemas separados (`copilot_channel_link` ≠ `sales_agent_channel_link`) |
| Mitigación edge case | Sales_agent bot detecta phone dueño → responde "andá a `@nicolify_copilot_bot`" con deep link |
| Owner | /pm 2026-04-30 |

## D-PI5-006..D-PI5-025 — Decisiones research-driven (post `2026-04-30-telegram-bot-copilot-patterns.md`)

> Compactadas. Detalle full en research file (sección "Decisiones Recomendadas").

### Memoria conversacional

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-006 | Reutilizar `ContextWindowBuilder` + `RollingSummarizer` con `TELEGRAM_CONTEXT_WINDOW_CONFIG` distinto (3000 raw tokens, 15 max msgs, summary 600 chars, nudge 12000 tokens) | Pattern hybrid ya implementado web. Telegram = sesiones más espaciadas → ventana más larga |
| D-PI5-007 | Reutilizar `CopilotConversationModel` con cols nuevas `channel_type` + `channel_chat_id`. NO tabla separada | Single source of truth. 1 conversation por `(tenant, user, channel_type, channel_chat_id)` |
| D-PI5-008 | NO vector retrieval Qdrant en MVP. Diferir hasta feedback "no me recuerda lo que le dije" | Overkill 1:1 lineal. Costo embed por turno innecesario MVP |
| D-PI5-009 | Añadir fragmento `TELEGRAM_CHANNEL_CONTEXT` a `CACHEABLE_FRAGMENTS` para asegurar prefijo ≥1024 tokens (umbral cache Anthropic) | Sin studio_snapshot/form_data el prefijo Telegram es más corto → riesgo no activar cache |

### HITL sales_agent ↔ copilot

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-010 | Tabla nueva `hitl_requests` (tenant_id, lead_id, sales_agent_thread_id, question, context, status, response, timeout_at) | Persistencia state machine handoff. Schema en research §2 |
| D-PI5-011 | Sales_agent `node_escalation` migra de fire-and-forget → `interrupt()` LangGraph + `Command(resume=...)` | Pattern canonical LangGraph HITL. Lead recibe holding msg, dueño decide, graph resume con respuesta |
| D-PI5-012 | Timeout default 15 min. Post-timeout sales_agent procede con `decision_fallback` configurable per tenant en `personality_profiles` | Balance UX (lead no espera más de 15 min) + safety (tenant define qué hacer si dueño no contesta) |
| D-PI5-013 | Worker ARQ cada 5 min resuelve expirados (`status='timed_out'`, resume con `TIMEOUT_FALLBACK`) | Async cleanup, no bloquea graph |
| D-PI5-014 | Reutilizar `AgentStateCheckpointModel` existente sales_agent como checkpointer. NO migrar a `PostgresCheckpointer` LangGraph en este PI | Reutiliza infra, no introduce nueva dependencia |

### Multi-user roles arquitectura prep

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-015 | Tabla `copilot_channel_links` (tenant_id, user_id, channel_type, **channel_user_id (= `from_user.id` Telegram, identity inmutable**), channel_username (mutable, display only), role, linked_at, revoked_at) | Identity key = numérico inmutable. `username` cambia. Schema preparado multi-rol desde día 1 |
| D-PI5-016 | UNIQUE constraint `(tenant_id, channel_type, channel_user_id)` — 1 chat_id = 1 rol por tenant | Mismo dueño en 2 tenants Nicolify → 2 chat_ids distintos (acepta edge case raro) |
| D-PI5-017 | MVP solo `role='owner'`. Schema soporta `assistant`, `finance_admin`, `marketing_lead`. Implementación filtros tools por rol = futuro PI | Costo-cero ahora, evita migración futura |
| D-PI5-018 | `ToolRegistry.get_tools_for_context()` recibe `user_role` futuro, MVP siempre owner | Hook listo, sin lógica MVP |

### Onboarding + magic link

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-019 | Magic link `t.me/nicolify_copilot_bot?start=TOKEN`. Token = HMAC-SHA256(secrets.token_urlsafe(32)). TTL 15 min. Single-use. Hash en DB | Industry standard auth flow |
| D-PI5-020 | Tabla `copilot_link_tokens` (token_hash, tenant_id, user_id, expires_at, used_at) | Persistencia tokens. Hash no plaintext (anti-leak DB) |
| D-PI5-021 | FE polling cada 3s por 60s `/api/v1/copilot/telegram-link-status?token_id=X` para confirmar linked. WebSocket = futuro optim | Simple MVP, evita socket infra ahora |
| D-PI5-022 | Bot sin link → response template friendly con URL directa onboarding. NO auth in-chat (anti-pattern + ToS Telegram) | UX claro + seguridad |

### Tools + canal subset

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-023 | Metadata `available_channels: frozenset[str]` en `ToolGroupMeta` (nuevo dataclass). Default = `{"web","telegram","whatsapp"}`. Restricción = subset explícito | Single source of truth canal por tool group |
| D-PI5-024 | Tools web-only MVP: `navigation`, `guided` (wizard), `landing` mutations, `offer_section` mutations. Telegram-allowed: `awareness`, `analytics`, `crm`, `sales_agent`, `extraction`, `knowledge_search`, `data_query`, `document`, `channel_format`, `pin_to_memory`, `mutation` (parcial), `offer_ladder` (consulta) | Clasificación research §5. Subset MVP amplio (~12 tool groups operables Telegram) |
| D-PI5-025 | Tool no disponible → response template "Ese ajuste requiere el editor web. ¿Te mando link directo `app.nicolify.com/[tenant]/...`?" + LLM system prompt instruccion explícita | UX friendly, evita error técnico |

### Escalabilidad + seguridad

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-026 | Webhook handler **NON-BLOCKING**. Encola en ARQ/Redis, devuelve 200 < 200ms. Worker procesa LLM async | Telegram retry timeout 5s. Inline LLM = mensajes duplicados |
| D-PI5-027 | Rate limiting en worker: `asyncio.Semaphore(30)` global + `dict[chat_id, asyncio.Lock]` per-chat | Telegram limits: 30 msg/sec global, 1 msg/sec per chat |
| D-PI5-028 | Validar `X-Telegram-Bot-Api-Secret-Token` header en webhook (configurar via `setWebhook` con secret_token) | Endpoint público — anti fake updates |
| D-PI5-029 | Filtrar `update.message.chat.type == "private"` — IGNORAR grupos, supergrupos, canales | Bot solo DMs. Sales_agent territory grupos en futuro PI suyo |
| D-PI5-030 | Sanitizar payload con `sanitize_payload()` existente antes persistir. Solo guardar `chat_id`, `text`, `message_id`. NO `username`/`first_name`/`phone` en logs | PII LGPD/GDPR. `username` solo en `copilot_channel_links` (mutable, display) |
| D-PI5-031 | Files >20MB → reject con redirect web. ≤20MB → `getFile` API → mismo `document_processor` que web | Telegram bot limit. Reuso pipeline existente |

### Decisiones implementación PR-2 (S2 cierre, 2026-05-01)

| ID | Decisión | Razón |
|---|---|---|
| D-PI5-IMPL-007 | `for_channel(channel)` classmethod canonical en `ContextWindowBuilder` + `RollingSummarizer`. Legacy `__init__(config)` / `__init__(llm, max_chars)` preservado para tests | Backward compat 0% breaking. Tests pre-existentes pasan sin cambios. Q6 PM-resolved |
| D-PI5-IMPL-008 | Cache prefix threshold ≥2048 tokens (Sonnet floor + Kimi K2.6 ≥1024 cubierto). Provider AGENT actual = Kimi K2.6 via LiteLLM (`AI_PROVIDER_AGENT=kimi`) | Cubre con margin Sonnet (2048) y Kimi (1024). Si swap a Anthropic Opus 4.x en futuro PR → extender `_TELEGRAM_CHANNEL_CONTEXT_ES` a ≥4096 (follow-up). Q3 PM-Opus resolved |
| D-PI5-IMPL-009 | Orchestrator entrypoint accepta `channel` por DOS paths: `ClientContextDTO.channel: str \| None = None` field + `invoke_text(channel: str = "web")` kwarg. Dispatch `context.channel or kwarg or "web"` | Ergonomía worker (kwarg directo) + futuro callers (DTO). Single source of truth en dispatch. Q4 PM-Opus resolved |
| D-PI5-IMPL-010 | Conversation lookup `get_or_create_by_channel` optimistic SELECT-then-INSERT, NO SELECT FOR UPDATE. UNIQUE constraint `(tenant_id, user_id, channel_type, channel_chat_id)` deferred a S5 PR-5 | Race window microsegundos MVP volume (≤docenas tenants telegram-active). Index ya cubre lookup performance. Nueva migration excluida scope PR-2. Q5 PM-Opus resolved |
| D-PI5-IMPL-011 | `format_for_channel_impl` shared en `shared/agent_observability/channels/format_for_channel.py:83` reuso directo. NO new function | Verified existe pre-PR-2. Worker llama `format_for_channel_impl(content, channel_id='telegram')`. Q2 architect-resolved |
| D-PI5-IMPL-012 | `_TELEGRAM_CHANNEL_CONTEXT_ES` constant string puro Python (NO interpolación, NO timestamps, NO tenant_name interpolado, NO conversation_id mid-block) | Preserva cache hit rate Anthropic/Kimi — bytes byte-idénticos entre invocaciones. Builder fn devuelve `""` cuando channel != telegram → web prefix preservado |
| D-PI5-IMPL-013 | `CopilotOrchestrator.invoke_text` sibling de `stream_chat`, NO nueva clase, NO nuevo grafo. Comparte `_prepare_conversation` + `_run_graph_stream` | Worker no puede consumir SSE → invoke_text agrega chunks del stream a buffer + retorna `CopilotInvokeResult` Pydantic value object. Cero duplicación. Cero deuda gratuita |
| D-PI5-IMPL-014 | PR-2 owns FIRST-TIME wiring de `ContextWindowBuilder` + `RollingSummarizer` dentro `_prepare_conversation` (greps confirmaron ZERO call sites pre-existentes) | Memory primitivos provisionados pero no cableados. ~15 LOC delta interno = trivial. NO scope creep. Q1 PM-Opus resolved |
| D-PI5-IMPL-015 | Anchor cap bumped 37→39 (registrá `COPILOT-INVOKE-RESULT-PR2-PI5` + `COPILOT-TELEGRAM-CHANNEL-CONTEXT`). Slot order ratchet extended `TELEGRAM_CHANNEL_CONTEXT` idx 3 entre `MARKETING_KB_HINT` y `LIGHTHOUSE` | Arch fitness ratchet correctly captures new PR-2 surfaces. Iter-2 fix |
| D-PI5-IMPL-016 | Worker resilience: 30s `asyncio.wait_for` orchestrator timeout + per-dependency try/except (lookup/orchestrator/format/bot send). Best-effort NO rompe turn | Tessl graceful-degradation pattern aplicado. Fallback CTA template friendly si orchestrator falla |
