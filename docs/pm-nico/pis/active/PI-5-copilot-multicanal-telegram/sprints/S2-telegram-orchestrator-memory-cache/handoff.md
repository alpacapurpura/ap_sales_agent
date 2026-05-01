# S2 → S3 Handoff

> Owner: `/pm`. Cierre 2026-05-01.

## Surface live disponible (post-S2)

### Orchestrator multi-channel (live)

- `CopilotOrchestrator.invoke_text(channel: str = "web", ..., context: ClientContextDTO | None) -> CopilotInvokeResult` en `application/orchestrator/chat.py`
- Sibling de `stream_chat`. Comparte `_prepare_conversation` + `_run_graph_stream`.
- Worker non-streaming consume invoke_text. SSE callers consumen stream_chat.
- Dispatch canal: `context.channel or kwarg or "web"`.

### Memory inyección por canal (live)

- `ContextWindowBuilder.for_channel(channel)` + `RollingSummarizer.for_channel(channel)` classmethods.
- Telegram: `TELEGRAM_CONTEXT_WINDOW_CONFIG` (3000/15/600/12000).
- Web: `DEFAULT_CONTEXT_WINDOW_CONFIG` baseline.
- Default 'web' fallback canal desconocido.
- First-time wired en `_prepare_conversation` (PR-2 owns).

### Cache fragment per-channel (live)

- `PromptFragment.TELEGRAM_CHANNEL_CONTEXT` enum + `CACHEABLE_FRAGMENTS` slot idx 3 (entre `MARKETING_KB_HINT` y `LIGHTHOUSE`).
- Builder `_build_telegram_channel_context_fragment(state)` devuelve `_TELEGRAM_CHANNEL_CONTEXT_ES` (~2200 tokens stable bytes Spanish prose) cuando `state.channel == "telegram"`, `""` cuando otro canal.
- Threshold ≥2048 tokens enforced via `test_telegram_cache_prefix_meets_anthropic_threshold` arch fitness.

### Tool registry runtime filter (live)

- `deep_agent.py` pasa `channel=ctx.get("channel") or "web"` a `get_tools_for_context()`.
- `ToolGroupMeta.available_channels` SSoT respetado.
- Telegram excluye: `navigation`, `guided`, `landing.mutations`, `offer_section.mutations`. Incluye 12+ groups telegram-allowed.
- Pattern reusable para futuros canales (whatsapp, voice, etc).

### Conversation lookup multi-channel (live)

- `ConversationRepository.get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` tenant-scoped optimistic SELECT-then-INSERT.
- Soft-delete aware (`deleted_at IS NULL`).
- UNIQUE constraint deferred S5 PR-5.

### Worker resilience (live)

- `process_copilot_telegram_turn` con 30s `asyncio.wait_for` timeout + per-dependency try/except + structured success log con cache metrics + fallback CTA template friendly.
- Pattern transferible a worker WhatsApp futuro.

## Decisiones consolidadas para S3 (HITL escalation)

### Crítico para S3 PR-3

- **`CopilotInvokeResult` Pydantic value object disponible** — sales_agent escalation puede hooked en orchestrator results. `error_kind` field permite señalar HITL pending vs completed.
- **`channel` propagation pattern establecido** — sales_agent recibe info canal para construct holding message en idioma+formato correcto cuando dueño no responde 15 min.
- **`AgentStateCheckpointModel` reusable** — D-PI5-014 ya decidió reusar en lugar de PostgresCheckpointer LangGraph. S3 implementa interrupt() + Command(resume=...) sobre este checkpointer.
- **Tabla `hitl_requests`** — schema en research §2 (D-PI5-010). S3 PR-3 crea migration + repo + service.
- **Worker ARQ resolver expirados** — D-PI5-013 cada 5 min cleanup `status='timed_out'`. Pattern transferible desde `telegram_worker` async resilience.

### Pattern HITL recomendado (research §2 + D-PI5-010..014)

```
sales_agent.node_escalation
  → HITL service: insert hitl_requests row + interrupt()
  → ARQ worker: encola notif a copilot (telegram channel + texto pregunta)
  → copilot.invoke_text(channel='telegram', message=question_with_context)
  → dueño responde Telegram (text)
  → telegram_worker recibe response → HITL service: resume() with response_text
  → sales_agent graph resume con Command(resume=response_text)
  → sales_agent procesa decision + responde lead
```

### Skills/agentes recomendados S3 PR-3

- `nicolify-context-builder` (Haiku) pre-flight obligatorio (PR ≥M, cross-module sales_agent + copilot)
- `nicolify-architect` (Opus) — CONTRACT cross-module HITL state machine + interrupt() + repo + worker
- `nicolify-agentic` (Opus) — single builder cross-surface (sales_agent + copilot + shared HITL service en `shared/`?)
- `nicolify-agentic-auditor` (Opus) — audit interrupt patterns + tabla state + timeout cleanup
- Skills domain: `copilot-expert` + `sales-agent-expert` + `tessl__langgraph` (interrupt/resume patterns canonical)

## Riesgos abiertos para S3

| Riesgo | Mitigación |
|---|---|
| Sales_agent owner identification (qué dueño Telegram responder?) | Reuso `copilot_channel_links` PR-1 — query `(tenant_id, role='owner')` retorna chat_id. UNIQUE garantiza 1 dueño por tenant |
| Multi-tenant ambigüedad chat_id (1 dueño 2 tenants) | D-PI5-016 confirmed: 1 chat_id = 1 rol por tenant. Edge case multi → 2 cuentas Telegram |
| Timeout fallback per-tenant config | D-PI5-012: `personality_profiles.timeout_fallback` configurable. S3 implementa lookup |
| Orchestrator timeout 30s vs HITL timeout 15 min | Diferentes layers — orchestrator in-turn vs HITL cross-turn. NO conflict |
| Cache prefix HITL turn-of-context cuando channel='telegram' + message=hitl-context | Builder fn TELEGRAM_CHANNEL_CONTEXT preserved. NO interpolación necesaria |

## Deuda técnica que S3 puede absorber (opcional)

- DTO cache token fields hardcoded 0 en `invoke_text` — wire-up callback handler real. Aprox 30 LOC.
- `invoke_text` outer except `set_turn_error` defensive coverage — aprox 5 LOC.

## Acción Chris pendiente (NO bloquea S3)

- Smoke test live PR-2 (Paso 6 del autonomous-start flow): abrir Telegram, escribir `@nicolify_dev_bot`, verificar CTA template + URL real. Si flow linked: generar magic link + `/start TOKEN` + mensaje + verificar respuesta orchestrator real.
- Decision: ¿arrancar S3 inmediato (HITL), o pausa para feedback live PR-2 first?

## Estado sprint S2

- **Status:** done
- **Cierre:** 2026-05-01
- **PRs:** 1/1 shipped (PR-2)
- **Verdict final:** PASS auditor agentic iter-2
- **Acción siguiente Chris:** smoke test live (Paso 6 autonomous flow) + decisión arrancar S3 HITL o pausa feedback
