# Arquitectura destino

> Estado al cierre de F10. Cada fase aporta una rebanada de esta topología.

---

## §1 Topología final

```
backend/src/modules/copilot/                      ← NÚCLEO AGNÓSTICO
│
├── domain/
│   ├── ports.py                                  ← CopilotProvider + 4 sub-ports
│   ├── workflow.py                               ← Workflow + WorkflowState
│   ├── output_channels.py                        ← ChannelFormat registry
│   ├── state.py                                  ← CopilotState + scratchpad refs
│   ├── model_tier.py                             ← (existente, refinado en F8)
│   ├── routing_policy.py                         ← (existente)
│   ├── navigation_map.py                         ← (existente, intacto)
│   └── schema_introspection.py                   ← (existente, intacto)
│
├── application/
│   ├── orchestrator/
│   │   └── deep_agent.py                         ← langchain-deepagents harness
│   ├── subagents/
│   │   ├── url_analyzer.py                       ← F4
│   │   ├── data_query.py                         ← F5
│   │   └── audit_inspector.py                    ← F2 (pattern)
│   ├── nodes/
│   │   ├── intent_router.py                      ← F5 sub-step
│   │   ├── synthesize_for_channel.py             ← F7
│   │   └── (otros nodes específicos)
│   ├── discovery.py                              ← F1, auto-load providers
│   ├── context_builder.py                        ← F3, ensambla system prompt
│   ├── memory/
│   │   ├── context_window_builder.py             ← (existente, refinado F8)
│   │   └── rolling_summarizer.py                 ← (existente, refinado F8)
│   ├── observability/
│   │   └── trace_recorder.py                     ← (existente, extendido F9)
│   └── router/
│       ├── model_router.py                       ← (existente, refinado F8)
│       └── classifiers/
│           ├── rule_classifier.py                ← (existente)
│           └── llm_classifier.py                 ← F8 nuevo
│
├── tools/                                        ← SOLO TOOLS TRANSVERSALES
│   ├── fetch_url.py                              ← F4
│   ├── ask_tenant_data.py                        ← F5 (entry point)
│   ├── knowledge_search.py                       ← F10
│   ├── format_for_channel.py                     ← F7
│   ├── propose_field_updates.py                  ← (existente, intacto)
│   ├── clarify.py                                ← (existente, refinado F6)
│   ├── navigation.py                             ← (existente, intacto)
│   ├── document_read.py                          ← (existente, intacto)
│   ├── web_research.py                           ← (existente, intacto - Tavily)
│   └── deepagents_builtins/
│       ├── write_todos.py                        ← F2 (planning)
│       ├── scratchpad.py                         ← F2 (read/write/edit_file)
│       └── pin_to_memory.py                      ← F2 (StoreBackend opt-in)
│
└── infrastructure/
    ├── qdrant/
    │   └── nicolify_marketing_kb.py              ← F10 collection
    ├── persisters/...                            ← (existente, intacto)
    ├── repositories/
    │   ├── pinned_memory_repository.py           ← F2 nuevo (StoreBackend)
    │   └── (existentes)
    ├── prompts/                                  ← (existente, refinado)
    └── web/
        ├── trafilatura_client.py                 ← F4 nuevo
        └── tavily_search.py                      ← (existente, intacto)


backend/src/modules/{module}/copilot_provider/    ← PLUGIN POR MÓDULO
│
├── __init__.py                                   ← exporta CopilotProvider impl
├── tools.py                                      ← tools del dominio
├── workflows.py                                  ← Workflow declarations
├── summary.py                                    ← genera resumen vivo (si aplica)
└── context_inject.py                             ← qué inyectar en system prompt


backend/src/shared/
├── events/
│   └── brand_section_updated.py                  ← F3 nuevo
└── workers/
    └── brand_summary_regen.py                    ← F3 nuevo (ARQ task)
```

---

## §2 Ports (interfaces) — `copilot/domain/ports.py`

```python
from typing import Protocol, runtime_checkable
from uuid import UUID

@runtime_checkable
class ToolProvider(Protocol):
    """Cada módulo expone tools de su dominio."""
    def tools(self) -> list[BaseTool]: ...

@runtime_checkable
class WorkflowProvider(Protocol):
    """Cada módulo declara workflows multi-step."""
    def workflows(self) -> list[Workflow]: ...

@runtime_checkable
class SummaryProvider(Protocol):
    """Cada módulo (que aplique) genera y persiste resumen vivo."""
    async def summary(self, tenant_id: UUID) -> str | None: ...

@runtime_checkable
class ContextInjector(Protocol):
    """Cada módulo decide qué meter en system prompt según route target."""
    async def inject_for(self, target_route: str, tenant_id: UUID) -> str | None: ...

@runtime_checkable
class CopilotProvider(Protocol):
    """Root interface — un módulo lo implementa para enchufarse al copilot."""
    @property
    def module_id(self) -> str: ...
    def tool_provider(self) -> ToolProvider | None: ...
    def workflow_provider(self) -> WorkflowProvider | None: ...
    def summary_provider(self) -> SummaryProvider | None: ...
    def context_injector(self) -> ContextInjector | None: ...
```

Discovery via Python entry points en `pyproject.toml`:

```toml
[project.entry-points."nicolify.copilot_providers"]
brand = "src.modules.brand.copilot_provider:provider"
offer = "src.modules.offer.copilot_provider:provider"
landing = "src.modules.landing.copilot_provider:provider"
analytics = "src.modules.analytics.copilot_provider:provider"
crm = "src.modules.crm.copilot_provider:provider"
connections = "src.modules.connections.copilot_provider:provider"
```

`copilot/application/discovery.py` itera con `importlib.metadata.entry_points(group="nicolify.copilot_providers")` y arma el registry runtime.

---

## §3 Workflow declarativo unificado

Reemplaza `guided` + `procedure` + `extraction_card_flow`.

```python
# copilot/domain/workflow.py
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class WorkflowTrigger(Enum):
    URL_PASTED = "url_pasted"
    DOC_UPLOADED = "doc_uploaded"
    USER_INTENT = "user_intent"        # detected by classifier
    WIZARD_BUTTON = "wizard_button"

@dataclass(frozen=True)
class WorkflowNode:
    id: str
    handler: Callable                  # async callable
    next: str | Callable[[State], str] # static or conditional
    timeout_s: int = 30

@dataclass(frozen=True)
class Workflow:
    id: str                            # "design_offer_from_url"
    domain: str                        # "offer"
    description_es: str
    trigger: WorkflowTrigger
    nodes: list[WorkflowNode]
    state_schema: type                 # Pydantic model
    ui_progress_kind: str              # "block_progress" | "plan_card"
    max_clarify_questions: int = 5
```

Estado en `copilot_conversations.workflow_state` JSONB (rename de `procedure_state`).

---

## §4 Brand Summary — Tabla + flujo

### Schema

```sql
CREATE TABLE IF NOT EXISTS brand_summary (
    tenant_id UUID PRIMARY KEY,
    summary TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    model_used TEXT NOT NULL,                -- "gpt-5.4-nano"
    chars_count INT NOT NULL,                -- ≤800 enforced
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_section_changed TEXT NULL
);
```

### Flow

```
brand.save_section() ──► emit BrandSectionUpdated event
                              │
                              ▼
                    handler en brand/application/services/
                              │
                              ▼
                  ARQ task: regen_brand_summary(tenant_id)
                              │
                              ├─► fetch fields críticos (identity, positioning, voice, narrative)
                              ├─► render template `prompts/brand_summary_caveman.j2`
                              ├─► LLM NANO con structured output
                              ├─► validate ≤800 chars
                              └─► UPSERT brand_summary
                              
copilot system_prompt build ──► via brand provider context_injector ──► get_brand_summary(tenant_id)
                                                                              │
                                                                              ▼
                                                                       inserta como prefix estable
                                                                       (cacheable)
```

---

## §5 Scratchpad híbrido

| Backend | Scope | Persistencia | Path típico |
|---|---|---|---|
| `StateBackend` (Deep Agents default) | per-conversation | ephemeral (vive en `CopilotState`) | `/notes.txt`, `/inspirations/*.md`, `/plan.md` |
| `StoreBackend` (Postgres custom) | per-user opt-in | persistente cross-thread | `/memories/*.md` |

Tabla:

```sql
CREATE TABLE IF NOT EXISTS copilot_pinned_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    path TEXT NOT NULL,                     -- "/memories/competitor-mujerescoraje.md"
    content TEXT NOT NULL,
    pinned_from_conversation_id UUID NULL,  -- audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id, path)
);
```

Tool `pin_to_memory(path)` promueve archivo del scratchpad ephemeral al persistente.

---

## §6 `ask_tenant_data` subgraph

```
user msg → tool ask_tenant_data(question, output_channel="chat")
              │
              ▼
   spawn_subagent("data_query", question)
              │
   ┌──────────┴────────────────────────────────────┐
   │ subgraph aislado (Deep Agents subagent)       │
   │                                               │
   │  intent_classifier (NANO)                     │
   │     ↓ {"kind": "offer_lookup", "name": "..."} │
   │  entity_resolver (pg_trgm fuzzy match)        │
   │     ↓ resolved_entities                       │
   │  query_builder (MINI)                         │
   │     ↓ structured query plan                   │
   │  executor (repo.search via provider)          │
   │     ↓ raw results                             │
   │  state_check (active? archived?)              │
   │     ↓ flagged results                         │
   │  synthesizer (MINI, channel-aware)            │
   │     ↓ formatted answer                        │
   └──────────────────┬────────────────────────────┘
                      ▼
              return to main agent
```

Cada provider expone repos enriquecidos:

- `OfferRepository.search(name_like, status, since, limit)`
- `CrmContactRepository.count_inbound(since, until, channel)`
- `ConversationRepository.search(period, channel, status)`

---

## §7 Channel Formatter Registry

```python
# copilot/domain/output_channels.py
@dataclass(frozen=True)
class ChannelFormat:
    id: str                            # "whatsapp"
    label_es: str
    max_chars: int
    emoji_allowed: bool
    line_break_style: str              # "\n\n", "<br>", " — "
    markdown_allowed: bool
    structure_hint: str                # prompt hint to LLM

CHANNEL_FORMATS = {
    "chat": ChannelFormat(...),
    "whatsapp": ChannelFormat(
        id="whatsapp",
        label_es="WhatsApp",
        max_chars=1024,
        emoji_allowed=True,
        line_break_style="\n\n",
        markdown_allowed=False,  # WA no soporta markdown nativo
        structure_hint="hook · 3 bullets cortas · CTA breve · link al final",
    ),
    "email": ChannelFormat(...),
    "sms": ChannelFormat(...),
    "voice": ChannelFormat(...),
    "instagram_dm": ChannelFormat(...),
}
```

Providers pueden agregar canales propios via `register_channel(format)`.

---

## §8 Cierre

Esta topología emerge **incrementalmente** a través de F0-F10. Ningún cambio big-bang. Cada fase deja la app funcionando.

Para detalle de cada slice, ver `phases/F#-*.md`.
