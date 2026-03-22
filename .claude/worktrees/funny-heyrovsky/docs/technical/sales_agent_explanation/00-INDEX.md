# Sales Agent — Documentacion Tecnica Completa

## Diagrama de Flujo End-to-End

```
                           CANALES EXTERNOS
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Telegram │  │ WhatsApp │  │Instagram │  │   API    │
    │  Bot API │  │Evolution │  │Meta Graph│  │ Webhook  │
    └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │              │
    ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
    │telegram  │  │whatsapp  │  │  meta    │  │ webhook  │
    │.py:18-39 │  │.py:27-42 │  │.py:42-106│  │.py:37-99 │
    │(webhooks)│  │(webhooks)│  │(webhooks)│  │(sincrono)│
    └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │              │
    ┌────▼─────────────▼─────────────▼──────────────▼─────┐
    │              CHANNEL ADAPTERS (Strategy Pattern)     │
    │   BaseChannel ABC  →  normalize_payload()            │
    │   (base.py:5-31)      send_message()                 │
    │                        set_typing_status()            │
    │                                                       │
    │   ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
    │   │ Telegram   │ │ WhatsApp   │ │ Instagram      │   │
    │   │ Channel    │ │ Channel    │ │ Channel        │   │
    │   │(telegram   │ │(whatsapp/  │ │(instagram.py)  │   │
    │   │ .py:10)    │ │ __init__)  │ │                │   │
    │   └────────────┘ └────────────┘ └────────────────┘   │
    │   ┌────────────────────────────────────────────────┐  │
    │   │ WebhookAdapter (webhook.py:7) — in-memory      │  │
    │   └────────────────────────────────────────────────┘  │
    └──────────────────────┬──────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │    IncomingMessage (messages.py:4)   │
         │    user_id, text, channel_type,      │
         │    metadata                          │
         └──────────────────┬──────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │   ChatOrchestrator         │
              │   (chat.py:35 — Singleton) │
              └─────────────┬──────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  _handle_incoming_webhook       │
           │  (chat.py:80-103)               │
           │                                 │
           │  1. normalize_payload()         │
           │  2. Build composite buffer_key  │
           │     "tenant_id:user_id"         │
           │  3. buffer_service.add_message()│
           │  4. Launch smart_debounce_task  │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  SmartBufferService (Redis)      │
           │  (buffer_service.py:9-101)      │
           │                                  │
           │  Keys:                           │
           │  chat:buffer:{key} → List[str]   │
           │  chat:meta:{key}   → Hash        │
           │  chat:lock:{key}   → Lock (NX)   │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  smart_debounce_task            │
           │  (chat.py:105-201)              │
           │                                  │
           │  1. sleep(0.5s) — initial buffer │
           │  2. Reset check (new msg?)       │
           │  3. set_typing_status()          │
           │  4. Semantic check (LLM):        │
           │     check_is_complete()          │
           │     (semantic.py:8-41)           │
           │  5. Dynamic wait:                │
           │     COMPLETO → 4s more           │
           │     INCOMPLETO → 6s more         │
           │  6. Final reset check + lock     │
           │  7. get_and_clear_buffer()       │
           │  8. → process_chat_flow()        │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  process_chat_flow              │
           │  (chat.py:203-463)              │
           │                                  │
           │  1. Set Tenant Context           │
           │  2. Customer Identity (CRM)      │
           │     → IdentityService            │
           │     → LeadCapturedEvent          │
           │  3. Lead/Session mgmt            │
           │  4. Log user message             │
           │  5. Build Agent Identity (AKS)   │
           │     → TenantKnowledgeBuilder     │
           │  6. Prepare AgentState           │
           │     → create_initial_state()     │
           │  7. Semantic Intent Detection    │
           │     → SemanticRouter             │
           │  8. agent_app.ainvoke(state)     │
           │  9. Extract + Log + Send         │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  LangGraph: Main Workflow        │
           │  (graph.py:1-43)                │
           │                                  │
           │  supervisor → sales_agent → END  │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  LangGraph: Sales Subgraph       │
           │  (sales/graph.py:1-43)          │
           │                                  │
           │        ┌──supervisor──┐           │
           │        │ (routing LLM)│           │
           │        └──┬───┬───┬──┘           │
           │           │   │   │               │
           │     ┌─────▼┐ ┌▼───▼┐ ┌──────┐   │
           │     │Qualif│ │Prod │ │Closer│   │
           │     │ier   │ │Exprt│ │      │   │
           │     └──────┘ └─────┘ └──────┘   │
           │           │   │   │               │
           │           └───┴───┘               │
           │               │                   │
           │              END                  │
           └────────────────┬────────────────┘
                            │
           ┌────────────────▼────────────────┐
           │  OutputManager                   │
           │  (output_manager.py:11-106)     │
           │                                  │
           │  1. Parse response (JSON/text)   │
           │  2. For each chunk:              │
           │     a. Calculate typing time     │
           │        (CPM=320, jitter)         │
           │     b. set_typing_status()       │
           │     c. sleep(typing_time)        │
           │     d. send_message()            │
           │     e. Cognitive pause           │
           └─────────────────────────────────┘
```

## Indice de Archivos

| # | Documento | Contenido |
|---|-----------|-----------|
| [01](01-ENTRY-POINTS.md) | Entry Points | Webhooks, endpoints, verificacion de seguridad |
| [02](02-CHANNEL-ADAPTERS.md) | Channel Adapters | Patron Strategy, BaseChannel, adaptadores concretos |
| [03](03-SMART-BUFFER.md) | Smart Buffer | Debounce inteligente, Redis, check semantico |
| [04](04-CHAT-ORCHESTRATOR.md) | Chat Orchestrator | Flujo completo de process_chat_flow() |
| [05](05-AGENT-IDENTITY-SYSTEM.md) | Agent Identity System | TenantKnowledgeBuilder, agent_identity.j2, AKS |
| [06](06-LANGGRAPH-ARCHITECTURE.md) | LangGraph Architecture | Grafo principal, subgrafo sales, nodos, routing |
| [07](07-PROMPT-SYSTEM.md) | Prompt System | PromptLoader hibrido, todos los templates j2 |
| [08](08-SEMANTIC-ROUTER.md) | Semantic Router | Intent detection, rutas sistema/tenant, fastembed |
| [09](09-OUTPUT-AND-RESPONSE.md) | Output & Response | OutputManager, chunking, typing simulation |
| [10](10-DATA-MODELS.md) | Data Models | Modelos SQLAlchemy, DTOs, repositorios |
| [11](11-OBSERVABILITY.md) | Observability | Tracing, LLM logs, audit trail |
| [12](12-CRM-INTEGRATION.md) | CRM Integration | IdentityService, leads, eventos de dominio |

## Tabla de Archivos Clave

| Archivo | Lineas | Proposito |
|---------|--------|-----------|
| `backend/src/modules/connections/api/telegram.py` | 116 | Webhooks Telegram (legacy + multitenant) |
| `backend/src/modules/connections/api/whatsapp.py` | 231 | Webhooks WhatsApp (global + per-tenant) |
| `backend/src/modules/connections/api/meta.py` | 470 | Webhook Meta con signature verification |
| `backend/src/modules/connections/api/webhook.py` | 100 | Endpoint sincrono generico (API) |
| `backend/src/modules/connections/api/dependencies/webhook_security.py` | 73 | HMAC verification (Shopify + Meta) |
| `backend/src/shared/infrastructure/channels/base.py` | 32 | BaseChannel ABC |
| `backend/src/shared/domain/messages.py` | 15 | IncomingMessage / OutgoingMessage |
| `backend/src/modules/connections/infrastructure/channels/telegram.py` | 122 | TelegramChannel adapter |
| `backend/src/modules/connections/infrastructure/channels/whatsapp/__init__.py` | 45 | WhatsAppChannel facade |
| `backend/src/modules/connections/infrastructure/channels/instagram.py` | 124 | InstagramChannel adapter |
| `backend/src/modules/connections/infrastructure/channels/webhook.py` | 34 | WebhookAdapter in-memory |
| `backend/src/modules/sales_agent/infrastructure/external/buffer_service.py` | 101 | SmartBufferService (Redis) |
| `backend/src/modules/sales_agent/application/orchestrator/chat.py` | 463 | ChatOrchestrator (core) |
| `backend/src/modules/sales_agent/infrastructure/prompts/semantic.py` | 42 | check_is_complete (LLM) |
| `backend/src/modules/sales_agent/application/services/knowledge_builder.py` | 115 | TenantKnowledgeBuilder |
| `backend/src/modules/sales_agent/application/orchestrator/graph.py` | 44 | Main LangGraph workflow |
| `backend/src/modules/sales_agent/application/agents/sales/graph.py` | 44 | Sales subgraph |
| `backend/src/modules/sales_agent/application/agents/sales/nodes.py` | 95 | Specialist nodes |
| `backend/src/modules/sales_agent/application/orchestrator/state.py` | 97 | AgentState + factory |
| `backend/src/modules/sales_agent/infrastructure/prompts/base.py` | 175 | PromptLoader hibrido |
| `backend/src/modules/sales_agent/application/services/semantic_router.py` | 249 | SemanticRouter |
| `backend/src/modules/sales_agent/infrastructure/external/output_manager.py` | 106 | OutputManager |
| `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py` | 150 | trace_node decorator |
| `backend/src/modules/sales_agent/infrastructure/memory/audit_repository.py` | 175 | AuditRepository |

## Tabla de Prompts

| Template | Archivo | Usado En | Proposito |
|----------|---------|----------|-----------|
| `agent_identity.j2` | `templates/agent_identity.j2` | `knowledge_builder.py:78` | Identidad completa del agente (Brand + Offer) |
| `supervisor_routing.j2` | `templates/supervisor_routing.j2` | `nodes.py:25` | Routing del supervisor a especialistas |
| `specialist_qualifier.j2` | `templates/specialist_qualifier.j2` | `nodes.py:54` | Prompt del nodo Qualifier |
| `specialist_product_expert.j2` | `templates/specialist_product_expert.j2` | `nodes.py:68` | Prompt del nodo Product Expert |
| `specialist_closer.j2` | `templates/specialist_closer.j2` | `nodes.py:85` | Prompt del nodo Closer |
| `message_completeness.j2` | `templates/message_completeness.j2` | `semantic.py:24` | Clasificador binario COMPLETO/INCOMPLETO |
| `safety_context_check.j2` | `templates/safety_context_check.j2` | (safety layer) | Evaluacion de contenido censurado |
| `summary_generator.j2` | `templates/summary_generator.j2` | (session summary) | Generador de resumenes de sesion |
| `offer_psychology_generator.j2` | `templates/offer_psychology_generator.j2` | (offer AI tools) | Generador de pains/desires para ofertas |
