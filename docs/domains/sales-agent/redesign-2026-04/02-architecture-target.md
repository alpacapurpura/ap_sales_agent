# 02 · Arquitectura Target

> **Actualizado 2026-04-28** post-revisión cambios copilot abril 2026: ChatModelSpec native ya implementado, multi-provider per-role activo, observability rebuild Phase 1+2+3 cerrado, pricing aliases Kimi K2.6/K2.5, tool_call_dedup anti-loop.

---

## §1 — Topología destino

```
backend/src/
├── shared/
│   ├── infrastructure/llm/                    ← YA EXISTE — sales_agent solo adopta
│   │   ├── factory.py                         # MultiRoleLLMRouter + get_provider_for_role
│   │   ├── providers/
│   │   │   ├── _kwargs.py                     # SSoT kwarg translation (post-incidente 2026-04-27)
│   │   │   ├── _chat_model_resolver.py        # ChatModelSpec dataclass
│   │   │   ├── openai_compat.py
│   │   │   ├── deepseek.py                    # langchain-deepseek native
│   │   │   ├── kimi.py                        # OpenAI-compat + thinking disabled + temp 0.6
│   │   │   ├── qwen.py                        # OpenAI-compat + DashScope
│   │   │   └── gemini.py
│   │   └── ...
│   └── agent_observability/                   ← S0: NUEVO (extract de copilot/observability)
│       ├── recording/
│       │   ├── base_callback_handler.py       # NEW: abstract template method
│       │   ├── sanitization.py                # MOVED from copilot (PII regex)
│       │   └── turn_envelope.py               # MOVED (parametrize agent_kind, _legacy_compat_keys projection pattern)
│       ├── pricing/
│       │   ├── litellm_sync.py                # MOVED — daily worker
│       │   ├── resolver.py                    # MOVED — point-in-time
│       │   └── aliases.py                     # MOVED — provider+model alias map (Kimi K2.6/K2.5 → LiteLLM)
│       ├── cost/
│       │   ├── calculator.py                  # MOVED — pure function
│       │   └── fx_resolver.py                 # MOVED
│       ├── persistence/
│       │   ├── base_llm_call_repo.py          # NEW: abstract repo
│       │   └── base_trace_event_repo.py       # NEW: abstract repo
│       ├── reporting/
│       │   ├── billing_cycle_service.py       # MOVED (parametrize tables)
│       │   ├── cost_aggregator.py             # MOVED
│       │   └── cycle_window.py                # MOVED
│       ├── channels/                          ← S5: NUEVO (extract de copilot/domain/output_channels)
│       │   ├── format.py                      # ChannelFormat dataclass
│       │   ├── registry.py                    # register_channel + CHANNELS dict
│       │   └── format_for_channel.py          # MOVED — pure post-processor
│       └── workers/
│           ├── pricing_sync_task.py           # MOVED — único cross-agent
│           ├── retention_task.py              # MOVED — parametrized table+days
│           └── aggregate_refresh_task.py      # MOVED
│
├── modules/
│   ├── copilot/                               ← consume shared/, mantiene tablas copilot_*
│   │   ├── observability/                     # POST-S0: thin adapter, repos concretos copilot_*
│   │   ├── application/
│   │   │   └── orchestrator/
│   │   │       └── tool_call_dedup.py         # ANTI-LOOP per-turn (commit 3aab4002)
│   │   └── ...
│   │
│   └── sales_agent/                           ← S00..S10 EVOLUCIONA
│       ├── domain/
│       │   ├── ports.py                       ← BaseAgentProvider (S1, opcional)
│       │   ├── model_tier.py                  ← S4 mapping ROLE→tier (consume shared spec)
│       │   ├── output_channels.py             ← S5 (re-uso shared/channels/)
│       │   └── ... (existentes intactos)
│       │
│       ├── application/
│       │   ├── orchestrator/                  ← chat.py, graph.py existentes
│       │   ├── agents/sales/                  ← StateGraph specialists
│       │   ├── tools/                         ← S8+S9 expansion
│       │   │   ├── registry.py                ← MIRROR de copilot tools/registry.py
│       │   │   ├── scheduling/                ← S8: booking tools
│       │   │   ├── payment/                   ← S9: payment tools
│       │   │   ├── tool_call_dedup.py         ← MIRROR copilot anti-loop, S1
│       │   │   └── ... (existentes)
│       │   ├── prompts/                       ← S3 cache_boundary refactor
│       │   │   └── compose.py                 ← compose_system_prompt fragments (ver §3.3)
│       │   └── ... (existentes intactos)
│       │
│       ├── infrastructure/
│       │   ├── prompts/                       ← Jinja loader + DB override (intacto)
│       │   ├── monitoring/                    ← S1: DELETE @trace_node decorator post-cutover (DEFERRED-S1)
│       │   └── ...
│       │
│       ├── observability/                     ← S1: NUEVO (consume shared)
│       │   ├── callback_handler.py            ← SalesAgentCallbackHandler(BaseAgentCallbackHandler)
│       │   ├── domain_subscribers.py
│       │   └── repositories.py                ← sales_agent_llm_call repo concreto
│       │
│       └── api/                               ← (intacto + S8/S9 webhooks)
│
└── workers/
    └── settings.py                            ← registra workers shared (S0/S1)
```

---

## §2 — Tablas DB

### Existentes copilot (post observability rebuild — NO duplicar)

| Tabla | Schema |
|---|---|
| `copilot_llm_call` | event-sourced LLM calls — provider, model, tokens (input/output/cached_read/reasoning), cost_usd, fx, duration_ms |
| `copilot_trace_event` | turn timeline — turn_start/end/llm_call/tool_call/node_enter/exit/error/card_emitted |
| `copilot_routing_log` | tier + classifier + tools_available |
| `copilot_mutation_journal` | mutaciones via propose_field_updates |
| `copilot_events` | accepted/rejected/nudge_* |
| `model_pricing_snapshot` | versionado (provider, model, valid_from, valid_to, input_cost, output_cost, cached_read_cost) — **GLOBAL cross-agent** |
| `tenant_billing_config` | anchor_day=25, currency, fx_source — **GLOBAL cross-agent** |
| `mv_daily_llm_cost_per_tenant` | MV refresh hourly |

### S1 — nuevas para sales_agent (mirror schema)

| Tabla | Schema mirror de | Diferencias |
|---|---|---|
| `sales_agent_llm_call` | `copilot_llm_call` | + `lead_id` UUID, + `channel_type` text |
| `sales_agent_trace_event` | `copilot_trace_event` | + `lead_id`, + `channel_type` |
| `sales_agent_routing_log` | `copilot_routing_log` | + `lead_id`, + `stage`, + `lead_score` |

### S2 — MV cross-agent

```sql
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant_v2 AS
SELECT 'copilot' AS agent_kind, tenant_id, occurred_on,
       SUM(cost_usd) AS cost_usd, COUNT(*) AS calls, COUNT(DISTINCT turn_id) AS turns
FROM copilot_llm_call GROUP BY tenant_id, occurred_on
UNION ALL
SELECT 'sales_agent', tenant_id, occurred_on,
       SUM(cost_usd), COUNT(*), COUNT(DISTINCT turn_id)
FROM sales_agent_llm_call GROUP BY tenant_id, occurred_on;

CREATE UNIQUE INDEX ix_mv_daily_v2 ON mv_daily_llm_cost_per_tenant_v2(agent_kind, tenant_id, occurred_on);
```

### Legacy a eliminar post-cutover (DEFERRED-S1+S6)

| Tabla legacy | Reemplazo | Cuándo drop |
|---|---|---|
| `agent_trace_model` (decorator-based) | `sales_agent_trace_event` | Post S1 dual-write cutover (~4 sem) |
| `agent_log_model` | `sales_agent_llm_call` | Idem |

---

## §3 — Contratos clave

### §3.1 — `BaseAgentCallbackHandler` (S0)

Mirror de `ObservabilityCallbackHandler` de copilot, abstracted.

```python
# src/shared/agent_observability/recording/base_callback_handler.py
class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):
    """LangChain callback handler. Best-effort writes. PII sanitized.
    Captures: on_chat_model_start, on_llm_end (cost computed), on_tool_*."""

    @abstractmethod
    async def _persist_llm_call(self, call: LLMCallEvent) -> None: ...

    @abstractmethod
    async def _persist_trace_event(self, event: TraceEvent) -> None: ...

    # Concrete:
    async def on_chat_model_start(self, ...): self._open_span(...)
    async def on_llm_end(self, ...):
        call = self._build_llm_call_event(response, run_id)
        call = self._apply_sanitization(call)
        call = self._resolve_pricing(call)  # uses pricing/aliases.py + resolver.py
        try:
            await self._persist_llm_call(call)
        except Exception as exc:
            logger.warning("obs_write_failed", error=str(exc))
            await self._db_session.rollback()
```

### §3.2 — `ChatModelSpec` (YA EXISTE — adoptar en S4)

`backend/src/shared/infrastructure/llm/providers/_chat_model_resolver.py`:

```python
@dataclass(frozen=True, slots=True)
class ChatModelSpec:
    chat_class: type[BaseChatModel]
    builder: Callable[[ChatBuildContext], BaseChatModel]
    kwargs_normalizer: Callable[..., dict] = normalize_openai_protocol_kwargs
    library_name: str = "langchain_openai"
    is_reasoning_model: bool = False
    reasoning_token_reserve: int = 0  # DeepSeek-V4 = 4000
    reasoning_effort_param: str | None = None
```

Sales_agent S4: `LLMFactory.get_service(role)` → resuelve spec via `settings.get_provider_for_role(role)`.

### §3.3 — Multi-provider per-role (YA EXISTE — adoptar)

Env vars:
```bash
AI_PROVIDER=openai                    # global fallback
AI_PROVIDER_NANO=openai               # routing decisions
AI_PROVIDER_FAST=openai               # quick gen
AI_PROVIDER_REASONING=deepseek        # complex reasoning (deepseek-reasoner)
AI_PROVIDER_AGENT=kimi                # agent loops (kimi-k2.6)
AI_PROVIDER_VISION=openai
AI_PROVIDER_EMBEDDING=openai
```

Sales_agent specialists adoptan:
- supervisor → `ModelRole.NANO` (decisión rápida)
- buffer completeness → `ModelRole.NANO`
- qualifier/product_expert → `ModelRole.FAST` o `AGENT` según costo
- closer → `ModelRole.AGENT` (Kimi económico, manejo objeciones largas)

### §3.4 — `compose_system_prompt` (S3)

Slot order:
```
[1 cacheable cross-tenant] static_identity
[2 cacheable cross-tenant] tools_hint
[3 cacheable cross-tenant] sales_playbook_hint
[4 cacheable per-tenant]   agent_identity_lighthouse  ← S7 brand voice
[5 cacheable per-tenant]   offer_summary
[6 cacheable per-tenant]   channel_format_hint
[CACHE_BOUNDARY_MARKER]
[7 volatile per-turn] stage_hint
[8 volatile per-turn] lead_signals
[9 volatile per-turn] recent_messages_summary
[10 volatile per-turn] tool_request_format (suffix)
```

Target: prefix cacheable ≥1024 tokens. Hit rate ≥60%. Pattern espejo F8 copilot.

### §3.5 — Channel registry (S5)

`shared/agent_observability/channels/`:
```python
@dataclass(frozen=True)
class ChannelFormat:
    id: str
    label: str
    max_chars: int
    chunk_size: int
    markdown_allowed: bool
    emoji_allowed: bool
    typing_simulation_cpm: int  # sales-specific extension
    structure_hint: str
    parse_mode: str | None      # Telegram MarkdownV2

CHANNELS: dict[str, ChannelFormat] = {}
def register_channel(fmt: ChannelFormat) -> None: ...
def get_channel(channel_id: str) -> ChannelFormat: ...
```

`OutputManager.process_response` consume registry, no hardcoded.

### §3.6 — Brand voice lighthouse (S7)

Tabla `brand_voice_summary` (mirror `brand_summary` copilot F3):
- Cacheable per tenant
- ARQ regen al cambiar campo `Estilo Comunicacional` Brand Studio
- Inyectada slot 4 system prompt

### §3.7 — Scheduler tool (S8)

`@tool` `create_booking_link(lead_id, duration_minutes, channel)` → strategy pattern providers (Cal.com, Google Calendar, Calendly).

### §3.8 — Payment lifecycle (S9)

`@tool` `create_payment_link` / `verify_payment_status` / `grant_access`. Strategy pattern (Mercado Pago, Stripe). Idempotency natural key `(tenant_id, lead_id, offer_id, payment_id)`.

### §3.9 — Tool call dedup (S1)

Espejo de `copilot/application/orchestrator/tool_call_dedup.py` (commit 3aab4002):
```python
class ToolCallDedupTracker:
    """Per-turn. Detect repeated tool calls.
    Threshold=3 → anti-loop directive. Hard limit=5 → ToolCallLoopError."""
```

---

## §4 — Anti-objetivos arquitectónicos

| Tentación | Por qué NO |
|---|---|
| Mover specialists a deepagents subagents | StateGraph lineal correcto para playbook cierre |
| Unificar `agent_state_checkpoint` con `copilot_conversations` | Shapes diferentes; sales tiene lead_score/buying_signals |
| Compartir `OutputManager` con copilot | Copilot in-app no usa typing simulation |
| Borrar `PromptVersionModel` (DB-backed Jinja override) | Sales necesita override per tenant |
| Compartir `tools/registry.py` físico | Tools de cada agente distintos; semantic registry sí, archivo no |
| Subagents deepagents para "calificación profunda" | Specialists actuales hacen el trabajo |
| Re-implementar ChatModelSpec o providers Chinese | YA EXISTEN (commits c60197fa, 7dcc5db4) — adoptar |
| Re-implementar pricing aliases | YA EXISTE (`copilot/observability/pricing/aliases.py`, commit a3f65d04) — mover a shared |
| Re-implementar callback handler observability | YA EXISTE (`ObservabilityCallbackHandler` copilot post-Phase 2) — abstract a shared en S0 |
