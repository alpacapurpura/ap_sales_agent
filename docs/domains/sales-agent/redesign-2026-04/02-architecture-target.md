# 02 · Arquitectura Target

## §1 — Topología destino

```
backend/src/
├── shared/
│   └── agent_observability/         ← S0: NUEVO (extract de copilot)
│       ├── recording/
│       │   ├── base_callback_handler.py    # Abstract LangChain BaseCallbackHandler
│       │   ├── sanitization.py             # PII regex (compartido)
│       │   └── turn_envelope.py            # turn_start/turn_end pattern
│       ├── pricing/
│       │   ├── litellm_sync.py             # Worker único cross-agente
│       │   └── resolver.py                 # Lookup point-in-time
│       ├── cost/
│       │   ├── calculator.py               # Pure function
│       │   └── fx_resolver.py
│       ├── persistence/
│       │   └── base_repos.py               # Abstract: adapter pattern
│       ├── reporting/
│       │   ├── billing_cycle_service.py    # 25-25 anchor
│       │   ├── cost_aggregator.py          # Parametrized agent_kind
│       │   └── cycle_window.py
│       └── workers/
│           ├── pricing_sync_task.py        # Único cross-agent
│           ├── retention_task.py           # Parametrized table+days
│           └── aggregate_refresh_task.py
│
├── modules/
│   ├── copilot/
│   │   └── observability/  ← consume shared/, mantiene tablas copilot_*
│   │
│   └── sales_agent/                 ← S1+ EVOLUCIONA
│       ├── domain/
│       │   ├── ports.py                    ← BaseAgentProvider (S1)
│       │   ├── model_tier.py               ← S4
│       │   ├── output_channels.py          ← S5 (re-uso shared)
│       │   └── ... (existentes intactos)
│       │
│       ├── application/
│       │   ├── orchestrator/               ← chat.py, graph.py existentes
│       │   ├── agents/sales/               ← StateGraph specialists
│       │   ├── tools/                      ← S8+S9 expansion
│       │   │   ├── registry.py             ← MIRROR de copilot tools/registry.py
│       │   │   ├── scheduling/             ← S8: booking tools
│       │   │   ├── payment/                ← S9: payment tools
│       │   │   └── ... (existentes)
│       │   ├── prompts/                    ← S3 cache_boundary refactor
│       │   │   └── compose.py              ← compose_system_prompt fragments
│       │   └── ... (existentes intactos)
│       │
│       ├── infrastructure/
│       │   ├── prompts/                    ← Jinja loader + DB override (intacto)
│       │   ├── monitoring/                 ← S1: DELETE @trace_node decorator post-cutover
│       │   └── ...
│       │
│       ├── observability/           ← S1: NUEVO (consume shared)
│       │   ├── callback_handler.py         ← SalesAgentCallbackHandler
│       │   ├── domain_subscribers.py
│       │   └── repositories.py             ← sales_agent_llm_call repo
│       │
│       └── api/                            ← (intacto + S8/S9 webhooks)
│
└── workers/
    └── settings.py                  ← registra workers shared (S0/S1)
```

---

## §2 — Tablas DB

### S1 — nuevas

| Tabla | Schema mirror de | Diferencias |
|---|---|---|
| `sales_agent_llm_call` | `copilot_llm_call` | + `lead_id` UUID, + `channel_type` text |
| `sales_agent_trace_event` | `copilot_trace_event` | + `lead_id`, + `channel_type` |
| `sales_agent_routing_log` | `copilot_routing_log` | + `lead_id`, + `stage`, + `lead_score` |

### Compartidas (no se duplican)

| Tabla | Razón |
|---|---|
| `model_pricing_snapshot` | Pricing es global (provider+model). Sync único. |
| `tenant_billing_config` | Threshold por tenant aplica cross-agent. |
| `mv_daily_llm_cost_per_tenant` | Materialized view extiende para incluir agent_kind. |

### Cross-agent migration (S2)

```sql
-- Agregar columna agent_kind a MV (S2)
ALTER MATERIALIZED VIEW mv_daily_llm_cost_per_tenant
  ADD COLUMN agent_kind text;
-- Re-create con UNION ALL de copilot_llm_call + sales_agent_llm_call
```

---

## §3 — Contratos clave

### §3.1 — `BaseAgentCallbackHandler` (S0)

```python
# src/shared/agent_observability/recording/base_callback_handler.py
class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):
    """LangChain callback handler. Best-effort writes. PII sanitized."""

    @abstractmethod
    async def _persist_llm_call(self, call: LLMCallEvent) -> None: ...

    @abstractmethod
    async def _persist_trace_event(self, event: TraceEvent) -> None: ...

    # Concrete:
    async def on_chat_model_start(...): self._open_span(...)
    async def on_llm_end(...): self._close_span(...) → calls _persist_llm_call
    async def on_tool_start/end/error(...): → _persist_trace_event
```

Concreto en sales_agent:
```python
class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    async def _persist_llm_call(self, call):
        # writes to sales_agent_llm_call con lead_id+channel_type
```

### §3.2 — `ChatModelSpec` (S4)

Cada provider declara:
```python
class DeepseekChatSpec:
    provider = "deepseek"
    model = "deepseek-chat"
    max_input_tokens = 64000
    max_output_tokens = 4096
    supports_caching = True
    kwargs_normalizer = "openai_protocol"
```

`LLMFactory.get_service(role)` resuelve spec por role; cualquier kwarg pasa por `normalize_openai_protocol_kwargs` (SSoT). Hereda anti-incidente del 2026-04-27.

### §3.3 — `compose_system_prompt` (S3)

```python
# src/modules/sales_agent/application/prompts/compose.py
def compose_system_prompt(state: AgentState) -> list[SystemMessage]:
    fragments_cacheable = [
        _static_identity(),                    # Slot 1, cross-tenant
        _tools_hint(state.active_tools),       # Slot 2, cross-tenant
        _sales_playbook_hint(),                # Slot 3, cross-tenant
        _agent_identity_lighthouse(state),     # Slot 4, per-tenant cacheable (S7)
        _offer_summary(state),                 # Slot 5, per-tenant cacheable
        _channel_format_hint(state),           # Slot 6, per-tenant cacheable
    ]
    fragments_volatile = [
        _stage_hint(state),                    # Slot 7, per-turn
        _lead_signals(state),                  # Slot 8, per-turn
        _recent_messages_summary(state),       # Slot 9, per-turn
        _tool_request_format(state),           # Slot 10, per-turn (suffix)
    ]
    return [
        SystemMessage(content="\n\n".join(fragments_cacheable)),
        SystemMessage(content="\n\n".join(fragments_volatile)),
    ]
```

Target: prefix cacheable ≥1024 tokens contiguos → cache hit ≥60%.

### §3.4 — Channel registry (S5)

Re-uso de copilot `output_channels.py` movido a `shared/agent_observability/channels/`:
```python
@dataclass(frozen=True)
class ChannelFormat:
    id: str
    label: str
    max_chars: int
    markdown_allowed: bool
    emoji_allowed: bool
    typing_simulation_cpm: int  # ← sales_agent specific extension

CHANNELS: dict[str, ChannelFormat] = {}

def register_channel(fmt: ChannelFormat) -> None:
    if fmt.id in CHANNELS: raise ValueError(...)
    CHANNELS[fmt.id] = fmt
```

`OutputManager.process_response` consume registry, no hardcoded.

### §3.5 — Brand voice lighthouse (S7)

Tabla `brand_voice_summary` (mirror de `brand_summary` de copilot F3):
- Cacheable per tenant
- Regenerada por ARQ task cuando Brand Studio actualiza `Estilo Comunicacional`
- Inyectada en slot 4 del system prompt

### §3.6 — Scheduler tool (S8)

```python
@tool
async def create_booking_link(
    lead_id: UUID,
    duration_minutes: int = 30,
    channel: str | None = None,
) -> dict:
    """Crea link único de reserva para este lead. Devuelve URL + tracking_id."""
```

Verificación passive (webhook del scheduler) + active (cron `verify_pending_bookings`).

### §3.7 — Payment lifecycle (S9)

```python
@tool
async def create_payment_link(lead_id: UUID, offer_id: UUID, ...) -> dict: ...

@tool
async def verify_payment_status(lead_id: UUID, payment_id: UUID) -> dict: ...

@tool
async def grant_access(lead_id: UUID, offer_id: UUID, payment_id: UUID) -> dict:
    """Gates: payment must be PAID. Otorga access vía connections module."""
```

---

## §4 — Anti-objetivos arquitectónicos

| Tentación | Por qué NO |
|---|---|
| Mover specialists a deepagents subagents | StateGraph lineal es correcto para playbook de cierre |
| Unificar `agent_state_checkpoint` con `copilot_conversations` | Shapes diferentes; sales tiene lead_score/buying_signals que copilot no |
| Compartir `OutputManager` con copilot | Copilot in-app no usa typing simulation; chunking distinto |
| Borrar `PromptVersionModel` (DB-backed Jinja override) | Sales necesita override per tenant. Copilot usa lighthouse. Ambos válidos |
| Compartir `tools/registry.py` físico | Tools de cada agente son distintos; semantic registry pattern sí, archivo no |
| Subagents deepagents para "calificación profunda" | Specialists actuales hacen el trabajo. Subagents añaden complejidad sin valor |
