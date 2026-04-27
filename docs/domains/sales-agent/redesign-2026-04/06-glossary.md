# 06 · Glossary

Términos clave del redesign sales_agent. Si un término aparece en docs o conversaciones, debe estar acá.

---

## Agente / Agent kinds

- **`agent_kind`**: discriminador `copilot` / `sales_agent` / futuros. Columna en MV cross-agent (S2).
- **Sales agent**: vendedor autónomo del tenant. Ver `00-vision §1`.
- **Copilot**: asistente in-app del operador. Ver `.claude/skills/copilot-expert/SKILL.md`.

## Observabilidad

- **Callback handler**: `BaseCallbackHandler` de LangChain que captura `on_chat_model_start/end`, `on_tool_start/end/error`. Reemplaza `@trace_node` decorator.
- **Trace event**: row en `*_trace_event`. Tipos: `turn_start`, `turn_end`, `llm_call`, `tool_call`, `node_enter`, `node_exit`, `error`, `card_emitted`.
- **LLM call event**: row tipada en `*_llm_call`. SSoT de provider/model/tokens/cost/duration por invocación.
- **Span**: identificador único por LLM call o tool call. Tree via `parent_span_id`.
- **Turn**: ciclo completo desde mensaje del usuario hasta respuesta final. `turn_id` raíz de árbol de spans.
- **Best-effort write**: try/except con structlog warning. Failure NUNCA rompe turn.

## Pricing / Cost

- **`model_pricing_snapshot`**: tabla versionada con (provider, model, valid_from, valid_to, input_cost, output_cost). LiteLLM sync diario. SSoT precios.
- **`tenant_billing_config`**: config por tenant — anchor day (default 25), threshold USD, alert email.
- **Billing cycle 25-25**: ciclo del 25 al 25 del mes siguiente. `compute_cycle_start(tenant_id, date)` SQL function.
- **FX resolver**: convierte USD a moneda del tenant via Frankfurter passthrough. Cached.

## Prompts

- **Cache boundary**: punto en system prompt entre fragments cacheable y volatile. Prefix ≥1024 tokens contiguos = OpenAI prompt cache hit.
- **Lighthouse**: snapshot cacheable per tenant pre-renderizado (ej: `brand_summary`, `brand_voice_summary`). Refresh cuando data fuente cambia (ARQ task).
- **Slot order** (S3 target):
  1. static_identity (cross-tenant)
  2. tools_hint (cross-tenant)
  3. sales_playbook_hint (cross-tenant)
  4. agent_identity_lighthouse (per-tenant cacheable) ← S7
  5. offer_summary (per-tenant cacheable)
  6. channel_format_hint (per-tenant cacheable)
  7. [CACHE_BOUNDARY]
  8. stage_hint (volatile)
  9. lead_signals (volatile)
  10. recent_messages_summary (volatile)
  11. tool_request_format (volatile, suffix)

## State / Conversation

- **AgentState**: TypedDict del LangGraph. Campos clave: `messages`, `current_state` (rapport/discovery/presentation/closing), `lead_score`, `buying_signals`, `objection_history`, `qualification_answers`, `agent_identity`, `turn_count`, `internal_turn`, `_pending_tool`.
- **Checkpoint**: `agent_state_checkpoint` row per (tenant_id, lead_id). Persiste estado entre turns.
- **Lead**: customer del tenant. Identificado por `lead_id` UUID + canal (telegram_id / whatsapp_id / instagram_id / web_session_id).
- **Stage**: rapport / discovery / presentation / closing. Determina specialist activo.
- **Lead score**: 0-100. Threshold para auto-cierre vs hand-off humano.
- **Buying signal**: keyword/intent positivo del lead (ej: "cuándo empieza", "cómo pago"). Acumulados en state.
- **Objection**: resistencia explícita ("muy caro", "no tengo tiempo"). Tracked + abordada por closer.

## Channels

- **`ChannelFormat`**: dataclass frozen — `id`, `label`, `max_chars`, `markdown_allowed`, `emoji_allowed`, `typing_simulation_cpm`. Registrado via `register_channel(...)`.
- **`channel_intent`**: detección de keyword en mensaje del usuario indicando canal preferido (ej: "mándame por WhatsApp"). Inyecta hint en system prompt.
- **`format_for_channel`**: tool determinístico (no LLM call) que aplica reglas del `ChannelFormat` al output.
- **Channel adapter**: webhook handler IN (Telegram/WhatsApp/IG) + sender OUT. Per-channel auth + signature.

## Tools

- **Tool registry**: `tools/registry.py` — `get_tools_for_context(state) → list[BaseTool]`. Stage-scoped + always-available.
- **Stage-scoped**: tool disponible solo en cierto stage (ej: `create_payment_link` solo en `closing`).
- **Always-available**: tool en todos los stages (ej: `escalate_to_human`, `format_for_channel`).
- **Tool spec**: `@tool` decorator + Pydantic args + docstring (description que el LLM lee).

## Brand Voice (S7)

- **Estilo Comunicacional**: campo Brand Studio que define tono, vocabulario, ritmo, emojis, ejemplos do/don't, frases prohibidas.
- **`brand_voice_summary`**: tabla cache (mirror de `brand_summary`). Pre-renderizada para slot 4 del system prompt.
- **Voice ARQ task**: regenera `brand_voice_summary` cuando el tenant edita Brand Studio.

## Scheduler (S8)

- **Booking link**: URL única per lead generada por scheduler integration (Cal.com / Google Calendar / Calendly).
- **Booking tracking**: webhook IN del scheduler → actualiza `agent_state_checkpoint.scheduled_meetings`.
- **Booking verify**: cron periódico que pregunta al scheduler si meetings pendientes se confirmaron / atendieron.
- **Follow-up cadence**: cron que envía recordatorios pre-meeting (24h + 1h antes) y post-meeting (verify atendido + nudge).

## Payment (S9)

- **Payment link**: URL única per lead generada por payment provider (Mercado Pago / Stripe / similar).
- **Payment status**: `pending` / `paid` / `failed` / `refunded`. Webhook IN actualiza.
- **Grant access**: action atómica post-paid: notificar lead + entregar acceso (key/link/código vía connections module) + actualizar lead_state.
- **Idempotency key**: `(tenant_id, lead_id, offer_id, payment_id)` — natural key para evitar double-grant.

## Quality

- **Judge**: LLM rubric multi-dim que evalúa respuestas del agente (fidelidad voz de marca, tono, accion correcta, ausencia de PII leak, etc.).
- **Goldens**: tests con input fijo + expected output verificado por judge. Run weekly via cron.
- **Run mode**: `STUB` default (no LLM call) / `RUN_LLM_JUDGE=1` opt-in para CI / weekly cron real.

## Architectural

- **Ratchet**: allowlist de violaciones legacy (ej: cross-module imports). Solo shrinks. Test falla si crece.
- **Anchor**: marker `[SALES-AGENT-*]` en código que el test fitness cuenta. Cap fijo. Bumpear cap requiere justificación.
- **Fitness test**: test arquitectónico en `tests/architecture/`. Enforza invariantes (folder naming, import boundaries, response_model presence, etc.).

## Workflow

- **Phase / Sprint** (`S{N}`): bloque de trabajo cohesivo del redesign. Una conversación = una fase idealmente.
- **Handoff prompt**: contenido en `prompts/S{N}-start.md` que el usuario pega al iniciar conversación nueva.
- **Learning doc**: `learnings/S{N}-*.md` escrito al cerrar fase. Lo lee S{N+1}.
