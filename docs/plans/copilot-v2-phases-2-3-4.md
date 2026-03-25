# Copilot v2: Fases 2, 3 y 4 — Plan de Implementación

> **Contexto:** La Fase 1 (Schema-Driven Foundation) está completa. El copilot ya descubre módulos, campos y secciones dinámicamente via `MODULE_REGISTRY` + `schema_introspection.py`, tiene 13 tools con selección por ruta, y un system prompt enriquecido con snapshot de completitud.
>
> **Estado verificado:** 309 tests PASS, ruff clean, tsc clean.

---

## Arquitectura Actual (Post-Fase 1)

### Backend: `backend/src/modules/copilot/`

```
copilot/
├── domain/
│   ├── module_registry.py          # MODULE_REGISTRY: 7 módulos (brand, offer, connections, crm, analytics, sales_agent, landing)
│   ├── schema_introspection.py     # get_model_sections(), check_section_completion(), format_completion_markdown()
│   └── navigation_map.py           # AppPage/AppSection (sin AppField hardcodeados — campos se descubren via Pydantic)
├── infrastructure/
│   ├── models/
│   │   └── conversation_model.py   # CopilotConversationModel (tabla copilot_conversations)
│   ├── repositories/
│   │   └── conversation_repository.py
│   └── prompts/
│       ├── base.py                 # PromptLoader (Jinja2/DB, cache 60s)
│       └── templates/
│           └── copilot_system.j2   # Template con {{ completion_snapshot }}, {{ modules }}, {{ available_tools }}
├── application/
│   ├── orchestrator/
│   │   ├── state.py                # CopilotState (TypedDict) — incluye active_tool_names
│   │   ├── graph.py                # LangGraph StateGraph: agent_node (dynamic tool binding), tool_executor_node, should_continue
│   │   └── chat.py                 # CopilotOrchestrator.stream_chat() — SSE streaming, Redis cache, DB persistence
│   ├── tools/
│   │   ├── registry.py             # ROUTE_TOOL_MAP + get_tools_for_route() + get_all_tools()
│   │   ├── navigation.py           # navigate_to_page, scroll_to_field, open_form, list_app_pages
│   │   ├── awareness.py            # get_module_completion_status (dynamic via schema_introspection)
│   │   ├── mutations.py            # propose_field_updates
│   │   ├── module_tools.py         # get_module_data(module, section?) — genérico para brand/offer/connections/landing
│   │   ├── analytics_tools.py      # get_funnel_metrics(period?)
│   │   ├── crm_tools.py            # get_lead_summary(temp?, limit?), get_pipeline_overview()
│   │   ├── sales_agent_tools.py    # get_sales_agent_status()
│   │   ├── connections_tools.py    # get_connections_detail()
│   │   ├── landing_tools.py        # get_landing_pages(status?)
│   │   ├── brand_tools.py          # DEPRECADO — reemplazado por module_tools.py (aún existe, no se importa)
│   │   ├── offer_tools.py          # DEPRECADO — reemplazado por module_tools.py (aún existe, no se importa)
│   │   └── research.py             # Stub (mock)
│   ├── agents/                     # Sub-agentes: web_extractor, style_analyzer, etc.
│   └── services/                   # brand_ai_actions_service, web_extractor_adapter, offer_psychology_service
└── api/
    ├── dto.py                      # CopilotChatRequest, ClientContextDTO, SSEEvent, SSEEventType
    ├── chat.py                     # POST /api/v1/copilot/chat (SSE streaming)
    └── actions.py                  # Endpoints de acciones de Brand AI
```

### Frontend: `frontend/src/features/copilot/`

```
copilot/
├── api/
│   └── copilot-api.ts              # streamCopilotChat() — native fetch + SSE parser
├── store/
│   └── copilot-store.ts            # Zustand: messages, status, selectedFields, pendingUIActions, currentRoute
├── hooks/
│   ├── useCopilotChat.ts           # sendMessage(), stopStreaming()
│   ├── useRouteTracker.ts          # Syncs pathname → store.currentRoute
│   ├── useCopilotNavigator.ts      # Executes UIActions (navigate, scroll, open_form)
│   └── useCopilotFieldSync.ts      # Field sync
└── components/
    ├── CopilotPanel.tsx            # Panel container
    ├── CopilotChat.tsx             # Chat UI (messages list, input, SuggestedActions, ContextChips)
    ├── CopilotRail.tsx             # Collapsed button rail (Sparkles + MessageCircle)
    ├── WithCopilot.tsx             # Field wrapper ("+a Copilot" pill, copilot:collect-values, copilot:field-update)
    ├── SuggestedActions.tsx         # Route-aware quick actions (brand, offer, marketing, sales, connections)
    ├── ContextChips.tsx            # Selected fields chips
    └── messages/
        ├── UserMessage.tsx
        ├── AssistantMessage.tsx     # Renders content + UIAction cards (ProposalCard o NavigationCard)
        ├── NavigationCard.tsx       # Clickable navigation card con MapPin
        └── ProposalCard.tsx         # Apply/Reject proposal card (dispatches copilot:field-update)
```

### Tipos Clave (Frontend)

```typescript
// copilot-store.ts
interface UIAction {
  type: "navigate" | "scroll_to_field" | "open_form" | "proposal";
  route?: string;
  page_label?: string;
  section_id?: string;
  field_id?: string;
  form_id?: string;
  prefill_data?: Record<string, unknown>;
  updates?: ProposalUpdate[];
}

interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  toolCalls?: Array<{ tool: string; args?: Record<string, unknown>; result?: string }>;
  uiActions?: UIAction[];
}

type CopilotStatus = "idle" | "thinking" | "streaming" | "done";
```

### SSE Protocol (Backend → Frontend)

```
event: text_chunk     → data: { content: string }
event: tool_start     → data: { tool: string, args: object }
event: tool_result    → data: { tool: string, result: string }  // capped 500 chars
event: ui_action      → data: UIAction object
event: status         → data: { state: "thinking" | "streaming" | "done" }
event: done           → data: { conversation_id: string }
event: error          → data: { message: string }
```

### Patrones de Acceso a Datos

- **BrandSettings**: Stored in `TenantModel.config_json['brand_settings']` — Pydantic model, introspectable
- **Offers (products)**: SQLAlchemy `ProductModel` table — `OfferRepository.get_all_by_tenant(tenant_id)`
- **Connections**: SQLAlchemy `ChannelConnectionModel` — `ChannelConnectionRepository.get_all_by_tenant(tenant_id)`
- **Leads**: SQLAlchemy `LeadModel` — `LeadRepository.get_by_id()`, `.get_high_intent_leads()`
- **Sales**: SQLAlchemy `SaleModel` — `SaleRepository.get_sales_by_date_range()`
- **Messages**: SQLAlchemy `MessageModel` — `MessageRepository.get_history(lead_id, limit)`
- **Landing Pages**: SQLAlchemy `LandingPageModel` — `LandingRepository.list_by_tenant(tenant_id)`
- **Analytics**: `SalesMetricsRepository.get_sales_summary()`, `.get_total_conversion_customers()`, `.get_total_sql_count()`
- **Tenant ID**: Siempre vía `get_tenant_id()` (context var) + `SessionLocal()` para DB sync

### Convenciones Copilot

- Tools usan `@tool` decorator de LangChain, docstrings en español
- DB access: `SessionLocal()` + `try/finally: db.close()`
- Tenant isolation: SIEMPRE filtrar por `tenant_id`
- Tool output: markdown formateado para consumo del LLM
- UIActions: retornar `{"ui_action": {...}}` — chat.py lo emite como SSE `ui_action` event
- Nuevos tools: registrar en `tools/registry.py` TOOL_GROUPS y ROUTE_TOOL_MAP

---

## Phase 2: Procedimientos Guiados + Inteligencia Proactiva

**Meta:** Workflows multi-paso + nudges proactivos que no requieren hardcodear pasos específicos.

### 2.1 Motor de Procedimientos Schema-Driven

Los procedimientos se definen declarativamente pero **descubren sus pasos del MODULE_REGISTRY**.

#### Crear `backend/src/modules/copilot/application/procedures/__init__.py`
Archivo vacío.

#### Crear `backend/src/modules/copilot/application/procedures/base.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    check_section_completion,
    get_model_sections,
)


@dataclass
class ProcedureStep:
    step_id: str
    module_id: str              # "brand", "offer" → lookup en MODULE_REGISTRY
    section_id: Optional[str]   # Sección del modelo Pydantic (auto-descubierta)
    instruction: str            # Qué decirle al usuario
    validation: str             # "has_any_data" | "has_required_fields" | "custom"
    tips: List[str] = field(default_factory=list)
    route_hint: Optional[str] = None  # Ruta sugerida para navegar


@dataclass
class Procedure:
    procedure_id: str
    name: str
    description: str
    steps: List[ProcedureStep]

    def get_current_step_index(self, tenant_id: UUID) -> int:
        """Encuentra el primer paso no completado. Usa MODULE_REGISTRY + schema_introspection."""
        db = SessionLocal()
        try:
            registry = get_module_registry()
            for i, step in enumerate(self.steps):
                if not self._is_step_complete(step, tenant_id, db, registry):
                    return i
            return len(self.steps)  # All complete
        finally:
            db.close()

    def get_completion_summary(self, tenant_id: UUID) -> dict:
        """Retorna {step_id: bool} indicando completitud de cada paso."""
        db = SessionLocal()
        try:
            registry = get_module_registry()
            return {
                step.step_id: self._is_step_complete(step, tenant_id, db, registry)
                for step in self.steps
            }
        finally:
            db.close()

    @staticmethod
    def _is_step_complete(step: ProcedureStep, tenant_id: UUID, db, registry) -> bool:
        descriptor = registry.get(step.module_id)
        if not descriptor or not descriptor.repo_factory:
            return False

        try:
            repo = descriptor.repo_factory(db)
            data = descriptor.read_fn(repo, tenant_id)
        except Exception:
            return False

        if not data:
            return False

        # Para módulos sin model_class (offer, connections), "has_any_data" = tiene datos
        if step.validation == "has_any_data":
            if isinstance(data, list):
                return len(data) > 0
            return True

        # Para módulos con model_class, verificar sección específica
        if step.section_id and descriptor.model_class:
            raw = data.model_dump(mode="json") if hasattr(data, "model_dump") else {}
            sections = get_model_sections(descriptor.model_class)
            completion = check_section_completion(raw, sections)
            section_status = completion.get(step.section_id)
            return section_status.is_configured if section_status else False

        return True
```

#### Crear `backend/src/modules/copilot/application/procedures/brand_setup.py`

Define el procedimiento `brand_setup` con pasos que referencian `module_id="brand"` + `section_id` por cada sección de BrandSettings. Los `section_id` corresponden a las keys de `BrandSettings.model_fields` (identity, story, positioning, narrative, visuals, etc.). La validación se descubre automáticamente via `get_model_sections()`.

**Pasos sugeridos:**
1. `identity` — "Completa la identidad básica de tu marca"
2. `story` — "Cuenta la historia de tu marca"
3. `positioning` — "Define el posicionamiento (Brand Love Key)"
4. `narrative` — "Construye la narrativa (StoryBrand)"
5. `visuals` — "Configura la identidad visual"
6. `communication_assets` — "Crea tus assets de comunicación"

#### Crear `backend/src/modules/copilot/application/procedures/offer_creation.py`

Procedimiento para crear una oferta. Pasos:
1. `module_id="offer"`, validation="has_any_data" — "Crea al menos una oferta"
2. Pasos adicionales por sección de oferta (general, avatar, objeciones, knowledge)

Nota: Como Offer es un SQLAlchemy model sin Pydantic root, la validación usa `has_any_data` y queries SQL específicas.

#### Crear `backend/src/modules/copilot/application/procedures/first_setup.py`

Meta-procedimiento que encadena: brand identity → primera oferta → primera conexión.

**Pasos:**
1. `module_id="brand"`, section_id="identity" — "Lo primero: ¿quién eres?"
2. `module_id="brand"`, section_id="positioning" — "Define tu propuesta de valor"
3. `module_id="offer"`, validation="has_any_data" — "Crea tu primera oferta"
4. `module_id="connections"`, validation="has_any_data" — "Conecta tu primer canal"

### 2.2 Procedure Tools

#### Crear `backend/src/modules/copilot/application/tools/procedure_tools.py`

Tres tools:

```python
@tool
def start_procedure(procedure_id: str) -> str:
    """Inicia un procedimiento guiado. Opciones: "brand_setup", "offer_creation", "first_setup"."""
    # Lookup en PROCEDURE_REGISTRY
    # Calcula current_step via get_current_step_index()
    # Retorna instrucciones del paso actual + tips

@tool
def get_procedure_status(procedure_id: str) -> str:
    """Consulta el progreso de un procedimiento activo."""
    # Retorna summary de pasos completados vs pendientes

@tool
def advance_procedure(procedure_id: str) -> str:
    """Revisa si el paso actual está completo y avanza al siguiente."""
    # Recalcula completitud, avanza si corresponde
    # Retorna instrucciones del nuevo paso o "¡Procedimiento completado!"
```

**Registrar** en `tools/registry.py`:
- Añadir `"procedure": PROCEDURE_TOOLS` a `TOOL_GROUPS`
- Añadir `"procedure"` a TODOS los routes en `ROUTE_TOOL_MAP` (los procedimientos aplican en cualquier ruta)

#### Modificar `state.py`

Añadir a `CopilotState`:
```python
active_procedure: Optional[Dict[str, Any]]  # {procedure_id, current_step_index}
```

Y en `create_initial_copilot_state`:
```python
"active_procedure": None,
```

#### Modificar `graph.py`

En `build_system_prompt()`: si `state["active_procedure"]` existe, inyectar contexto del procedimiento en el system prompt (paso actual, progreso, instrucciones).

#### Modificar `copilot_system.j2`

Añadir bloque condicional:
```jinja2
{% if active_procedure %}
## Procedimiento Activo: {{ active_procedure.name }}
Paso actual ({{ active_procedure.current_step }}/{{ active_procedure.total_steps }}): {{ active_procedure.instruction }}
{% if active_procedure.tips %}
Tips: {{ active_procedure.tips | join(', ') }}
{% endif %}
{% endif %}
```

### 2.3 Sistema de Nudges Proactivos

#### Crear `backend/src/modules/copilot/api/nudge.py`

Endpoint: `GET /api/v1/copilot/nudge-context?route={route}`

**Lógica:**
- Usa `MODULE_REGISTRY` + `schema_introspection` para detectar gaps dinámicamente
- Reglas de nudge declarativas:
  - `EmptyModuleNudge`: Si el módulo relevante a la ruta está vacío → sugerir configuración
  - `CrossModuleGapNudge`: Si Brand tiene datos pero Offer no → sugerir crear oferta
  - `IncompleteModuleNudge`: Si módulo tiene <30% completitud → sugerir continuar
- Cache Redis 5min por tenant+route (key: `copilot:nudge:{tenant_id}:{route_hash}`)
- Response: `{ nudges: [{ type, title, message, prompt, dismissible }] }`

**Registrar** el router en `src/main.py` bajo `/api/v1/copilot`.

#### Crear `frontend/src/features/copilot/hooks/useProactiveNudges.ts`

```typescript
// Se ejecuta en cambio de ruta
// Fetch GET /api/v1/copilot/nudge-context?route={currentRoute}
// Filtra nudges ya dismissed (localStorage: copilot:dismissed-nudges)
// Expone nudges para NudgeBanner
```

#### Crear `frontend/src/features/copilot/components/NudgeBanner.tsx`

- Banner sutil arriba del chat o inline en la página
- Click → envía `prompt` al copilot via `sendMessage()`
- Botón dismiss → guarda en localStorage, no reaparece
- Estilo: border-left purple, icono Lightbulb, texto conciso

### 2.4 UI de Procedimiento

#### Crear `frontend/src/features/copilot/components/ProcedureProgress.tsx`

Mini stepper que se muestra en CopilotChat entre el header y los mensajes cuando hay un procedimiento activo.

```typescript
// Props: { steps: Array<{label, completed, active}>, onStepClick: (stepIndex) => void }
// Visual: horizontal dots con labels, step activo highlighted en purple
// Click en paso → navega a la ruta correspondiente
```

**Datos del procedimiento:** Se pueden transmitir como un nuevo tipo de SSE event o como parte del `ui_action` con `type: "procedure_progress"`.

#### Modificar `copilot-store.ts`

Añadir a la store:
```typescript
activeProcedure: {
  procedureId: string;
  name: string;
  steps: Array<{ stepId: string; label: string; completed: boolean; active: boolean; routeHint?: string }>;
} | null;
setActiveProcedure: (proc: ...) => void;
clearActiveProcedure: () => void;
```

Extender `UIAction.type` para incluir `"procedure_progress"`.

#### Modificar `CopilotChat.tsx`

Montar `<ProcedureProgress />` condicionalmente cuando `activeProcedure` existe.

#### Modificar `CopilotRail.tsx`

Añadir indicador visual (pulse dot) cuando hay un nudge activo pendiente.

### Archivos Phase 2

| Acción | Archivo |
|--------|---------|
| **Crear** | `backend/src/modules/copilot/application/procedures/__init__.py` |
| **Crear** | `backend/src/modules/copilot/application/procedures/base.py` |
| **Crear** | `backend/src/modules/copilot/application/procedures/brand_setup.py` |
| **Crear** | `backend/src/modules/copilot/application/procedures/offer_creation.py` |
| **Crear** | `backend/src/modules/copilot/application/procedures/first_setup.py` |
| **Crear** | `backend/src/modules/copilot/application/tools/procedure_tools.py` |
| **Crear** | `backend/src/modules/copilot/api/nudge.py` |
| **Crear** | `frontend/src/features/copilot/hooks/useProactiveNudges.ts` |
| **Crear** | `frontend/src/features/copilot/components/ProcedureProgress.tsx` |
| **Crear** | `frontend/src/features/copilot/components/NudgeBanner.tsx` |
| **Modificar** | `backend/src/modules/copilot/application/orchestrator/state.py` — `active_procedure` |
| **Modificar** | `backend/src/modules/copilot/application/orchestrator/graph.py` — procedure context in prompt |
| **Modificar** | `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_system.j2` — procedure block |
| **Modificar** | `backend/src/modules/copilot/application/tools/registry.py` — añadir procedure tools |
| **Modificar** | `frontend/src/features/copilot/store/copilot-store.ts` — activeProcedure state |
| **Modificar** | `frontend/src/features/copilot/components/CopilotChat.tsx` — mount ProcedureProgress |
| **Modificar** | `frontend/src/features/copilot/components/CopilotRail.tsx` — nudge pulse indicator |
| **Registrar** | Router de nudge en `src/main.py` |

### Verificación Phase 2

1. "Guíame para configurar mi marca" → inicia procedimiento, muestra stepper
2. Navegar a Brand Studio vacío → aparece nudge proactivo
3. Completar paso (llenar identity) → stepper avanza automáticamente con `advance_procedure`
4. Nudge dismissed → no reaparece (localStorage)
5. `get_procedure_status("first_setup")` retorna progreso correcto
6. Procedure context aparece en system prompt

---

## Phase 3: UI Generativa Expandida + RAG Knowledge Base

**Meta:** Respuestas ricas con componentes interactivos + base de conocimiento vectorial.

### 3.1 Nuevos Componentes de UI Generativa

Estos componentes se renderizan dentro de `AssistantMessage.tsx` basados en `ui_action.type`.

#### Crear `frontend/src/features/copilot/components/messages/MetricSummaryCard.tsx`

- `ui_action.type: "metric_summary"`
- Data: `{ metrics: [{ label: string, value: string, trend?: "up"|"down"|"flat", delta?: string }] }`
- Visual: Grid de mini-cards con valor grande, label pequeño, flecha de trend con color (verde/rojo)

#### Crear `frontend/src/features/copilot/components/messages/ComparisonTable.tsx`

- `ui_action.type: "comparison"`
- Data: `{ columns: string[], rows: Array<Record<string, string>>, recommended?: string }`
- Visual: Tabla responsive, fila recomendada highlighted
- Uso: Comparar ofertas, opciones de UVP, canales

#### Crear `frontend/src/features/copilot/components/messages/ProgressChecklist.tsx`

- `ui_action.type: "checklist"`
- Data: `{ items: [{ label: string, done: boolean, route?: string }] }`
- Visual: Lista con checkmarks, items clickeables navegan a la ruta
- Uso: Setup progress, checklist de configuración

#### Crear `frontend/src/features/copilot/components/messages/MultiOptionSelector.tsx`

- `ui_action.type: "multi_option"`
- Data: `{ options: [{ id: string, title: string, content: string }], field_id: string }`
- Visual: Cards seleccionables, click selecciona y aplica via `copilot:field-update`
- Uso: Elegir entre opciones de UVP, taglines, headlines

#### Modificar `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`

Añadir switch cases para los nuevos tipos de `ui_action`:
```tsx
// Dentro del map de uiActions:
action.type === "metric_summary" ? <MetricSummaryCard data={action} /> :
action.type === "comparison" ? <ComparisonTable data={action} /> :
action.type === "checklist" ? <ProgressChecklist data={action} /> :
action.type === "multi_option" ? <MultiOptionSelector data={action} /> :
action.type === "proposal" ? <ProposalCard ... /> :
<NavigationCard ... />
```

#### Modificar `frontend/src/features/copilot/store/copilot-store.ts`

Extender `UIAction.type`:
```typescript
type: "navigate" | "scroll_to_field" | "open_form" | "proposal"
     | "metric_summary" | "comparison" | "checklist" | "multi_option"
     | "procedure_progress";
```

Añadir fields opcionales para los nuevos tipos:
```typescript
metrics?: Array<{ label: string; value: string; trend?: string; delta?: string }>;
columns?: string[];
rows?: Array<Record<string, string>>;
recommended?: string;
items?: Array<{ label: string; done: boolean; route?: string }>;
options?: Array<{ id: string; title: string; content: string }>;
```

### 3.2 RAG con Qdrant

#### Reusar `QdrantVectorStore`

Existe en `backend/src/modules/sales_agent/infrastructure/memory/vector_store.py`:
- Hybrid search (dense + sparse)
- Tenant-scoped collections
- FlashRank reranking

#### Crear `backend/src/modules/copilot/application/tools/knowledge_tools.py`

```python
@tool
def search_knowledge_base(query: str, scope: Optional[str] = None) -> str:
    """Busca en la base de conocimiento del copilot.

    Args:
        query: Texto de búsqueda.
        scope: Alcance. Opciones: "help" (docs del producto), "business" (docs del usuario), "all".
    """
    # Colección: copilot_knowledge_{tenant_id}
    # Usa QdrantVectorStore.hybrid_search()
    # Formatea resultados como contexto para el LLM
```

**Registrar** en `tools/registry.py`:
- Añadir `"knowledge": KNOWLEDGE_TOOLS` a `TOOL_GROUPS`
- Añadir `"knowledge"` al route `"*"` en `ROUTE_TOOL_MAP`

#### Crear `backend/src/modules/copilot/application/services/knowledge_ingestion.py`

Servicio para ingestar documentos:
1. **Docs del producto** — Markdown seeded desde `docs/` (help, FAQ)
2. **Docs del usuario** — Uploads a oferta/marca (PDFs, docs)
3. **Auto-resúmenes** — Resúmenes periódicos de configuración del tenant

Método: `ingest_document(tenant_id, content, metadata, scope)` → chunking → embedding → upsert a Qdrant.

#### Crear `backend/src/modules/copilot/api/knowledge.py`

Endpoints:
- `POST /api/v1/copilot/knowledge/ingest` — Ingest document
- `GET /api/v1/copilot/knowledge/search?query=&scope=` — Search (for testing/admin)

### 3.3 Memoria de Conversación Mejorada

#### Modificar `backend/src/modules/copilot/application/orchestrator/chat.py`

- Serializar `tool_calls` en conversation history (actualmente se pierden — solo se guardan role+content)
- En `_cache_history` y `append_messages`: incluir `tool_calls` array en cada message dict
- En `_deserialize_messages`: reconstruir `AIMessage(tool_calls=...)` si existen

### Archivos Phase 3

| Acción | Archivo |
|--------|---------|
| **Crear** | `frontend/src/features/copilot/components/messages/MetricSummaryCard.tsx` |
| **Crear** | `frontend/src/features/copilot/components/messages/ComparisonTable.tsx` |
| **Crear** | `frontend/src/features/copilot/components/messages/ProgressChecklist.tsx` |
| **Crear** | `frontend/src/features/copilot/components/messages/MultiOptionSelector.tsx` |
| **Crear** | `backend/src/modules/copilot/application/tools/knowledge_tools.py` |
| **Crear** | `backend/src/modules/copilot/application/services/knowledge_ingestion.py` |
| **Crear** | `backend/src/modules/copilot/api/knowledge.py` |
| **Modificar** | `frontend/src/features/copilot/components/messages/AssistantMessage.tsx` — switch nuevos tipos |
| **Modificar** | `frontend/src/features/copilot/store/copilot-store.ts` — nuevos UIAction types + fields |
| **Modificar** | `backend/src/modules/copilot/application/orchestrator/chat.py` — tool_calls serialization |
| **Modificar** | `backend/src/modules/copilot/application/tools/registry.py` — knowledge tools |

### Verificación Phase 3

1. "Dame 3 opciones de UVP" → LLM retorna `ui_action.type="multi_option"` → renderiza `MultiOptionSelector`, click aplica
2. "Compara mis ofertas" → LLM retorna `ui_action.type="comparison"` → renderiza `ComparisonTable`
3. "¿Cómo van mis métricas?" → LLM retorna `ui_action.type="metric_summary"` → renderiza `MetricSummaryCard`
4. "¿Qué me falta?" → LLM retorna `ui_action.type="checklist"` → renderiza `ProgressChecklist`, items clickeables navegan
5. "¿Cómo funciona el funnel bowtie?" → LLM llama `search_knowledge_base("funnel bowtie", scope="help")` → responde con contexto
6. Tool calls se persisten y reconstruyen al cargar conversación

---

## Phase 4: Observabilidad + Feedback Loop

**Meta:** Medir efectividad y personalizar respuestas basado en comportamiento.

### 4.1 Modelo de Eventos

#### Crear migración Alembic

**IMPORTANTE:** Seguir convención de migraciones idempotentes (raw SQL + IF NOT EXISTS).

```sql
CREATE TABLE IF NOT EXISTS copilot_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    conversation_id UUID,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_copilot_events_tenant ON copilot_events(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_copilot_events_type ON copilot_events(tenant_id, event_type);
```

Event types: `proposal_accepted`, `proposal_rejected`, `nudge_clicked`, `nudge_dismissed`, `procedure_started`, `procedure_completed`, `procedure_abandoned`, `option_selected`, `navigation_clicked`.

#### Crear `backend/src/modules/copilot/infrastructure/models/event_model.py`

SQLAlchemy model para `copilot_events`.

#### Crear `backend/src/modules/copilot/infrastructure/repositories/event_repository.py`

```python
class CopilotEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(self, tenant_id, user_id, event_type, event_data=None, conversation_id=None):
        """Guarda un evento."""

    def get_user_behavior_summary(self, tenant_id, user_id, days=30) -> dict:
        """Agrega eventos por tipo para un usuario en los últimos N días.
        Retorna: { proposal_accepted: 12, proposal_rejected: 3, ... }"""

    def get_tenant_summary(self, tenant_id, days=30) -> dict:
        """Agrega eventos para todo el tenant."""
```

### 4.2 Tracking Pipeline

#### Crear `backend/src/modules/copilot/api/events.py`

```python
# POST /api/v1/copilot/events
# Body: { event_type: str, event_data: dict, conversation_id?: str }
# Autenticado: requiere get_current_user + get_tenant_context
```

**Registrar** el router en `src/main.py`.

#### Modificar `frontend/src/features/copilot/api/copilot-api.ts`

Añadir función:
```typescript
export async function reportCopilotEvent(
  eventType: string,
  eventData: Record<string, unknown>,
  token: string,
  conversationId?: string,
): Promise<void> {
  // POST /api/v1/copilot/events
}
```

#### Modificar componentes que reportan eventos

- **`ProposalCard.tsx`**: En `handleApply()` → `reportCopilotEvent("proposal_accepted", { updates })`. En `handleReject()` → `reportCopilotEvent("proposal_rejected", { updates })`.
- **`NavigationCard.tsx`**: En click → `reportCopilotEvent("navigation_clicked", { route, section_id })`.
- **`NudgeBanner.tsx`** (de Phase 2): En click → `reportCopilotEvent("nudge_clicked", { nudge_type })`. En dismiss → `reportCopilotEvent("nudge_dismissed", { nudge_type })`.
- **`MultiOptionSelector.tsx`** (de Phase 3): En selección → `reportCopilotEvent("option_selected", { option_id, field_id })`.

### 4.3 Feedback-Informed Prompting

#### Modificar `backend/src/modules/copilot/application/orchestrator/graph.py`

En `build_system_prompt()`:
1. Llamar `CopilotEventRepository.get_user_behavior_summary(tenant_id, user_id, days=30)`
2. Inyectar resumen en template como `{{ behavior_summary }}`

#### Modificar `copilot_system.j2`

```jinja2
{% if behavior_summary %}
## Historial de Interacción
{{ behavior_summary }}
{% endif %}
```

Ejemplo de output:
```
## Historial de Interacción
- Acepta 80% de propuestas (12 aceptadas, 3 rechazadas)
- Completó Brand Setup, abandonó Offer Creation 2 veces
- Prefiere navegación directa sobre explicaciones largas
```

### Archivos Phase 4

| Acción | Archivo |
|--------|---------|
| **Crear** | Migración Alembic para `copilot_events` |
| **Crear** | `backend/src/modules/copilot/infrastructure/models/event_model.py` |
| **Crear** | `backend/src/modules/copilot/infrastructure/repositories/event_repository.py` |
| **Crear** | `backend/src/modules/copilot/api/events.py` |
| **Modificar** | `frontend/src/features/copilot/api/copilot-api.ts` — `reportCopilotEvent()` |
| **Modificar** | `frontend/src/features/copilot/components/messages/ProposalCard.tsx` — report events |
| **Modificar** | `frontend/src/features/copilot/components/messages/NavigationCard.tsx` — report events |
| **Modificar** | `backend/src/modules/copilot/application/orchestrator/graph.py` — behavior summary in prompt |
| **Modificar** | `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_system.j2` — behavior block |
| **Registrar** | Router de events en `src/main.py` |

### Verificación Phase 4

1. Click "Aplicar" en ProposalCard → evento `proposal_accepted` en `copilot_events`
2. Click "Rechazar" → evento `proposal_rejected`
3. Click nudge → evento `nudge_clicked`
4. Dismiss nudge → evento `nudge_dismissed`
5. Tras varios eventos: system prompt incluye resumen de comportamiento
6. `GET /api/v1/copilot/events/summary` (admin) retorna agregados correctos

---

## Secuenciación

```
Phase 2 → Guided Experience (depende de Phase 1 ✅)
  ├── 2.1 Procedure engine (base.py, 3 procedimientos)
  ├── 2.2 Procedure tools + registry + state + prompt
  ├── 2.3 Nudge system (backend endpoint + frontend hook + component)
  └── 2.4 ProcedureProgress UI + CopilotChat/Rail updates

Phase 3 → Rich Intelligence (depende de Phase 1 ✅, independiente de Phase 2)
  ├── 3.1 4 generative UI components + AssistantMessage switch + store types
  ├── 3.2 RAG: knowledge_tools + knowledge_ingestion + knowledge API
  └── 3.3 Conversation memory: tool_calls serialization in chat.py

Phase 4 → Learning (depende de Phase 2 para nudge events, Phase 3 para option events)
  ├── 4.1 copilot_events migration + model + repository
  ├── 4.2 Events API + frontend reportCopilotEvent + component integrations
  └── 4.3 Feedback-informed prompting in graph.py + template
```

> **Nota:** Phase 2 y Phase 3 son mayormente independientes entre sí y podrían ejecutarse en paralelo. Phase 4 depende de que los componentes de Phase 2 y 3 existan para poder trackear sus eventos.

---

## Principios de Resiliencia (aplicar en todas las fases)

| Cambio en el sistema | Qué hacer en copilot |
|---------------------|---------------------|
| Añadir campo a BrandIdentity | **Nada** — se descubre automáticamente |
| Añadir sección a BrandSettings | **Nada** — `model_fields` lo detecta |
| Añadir módulo nuevo | Añadir `ModuleDescriptor` al `MODULE_REGISTRY` (5 líneas) |
| Cambiar ruta de página | Actualizar `navigation_map.py` + `ROUTE_TOOL_MAP` |
| Eliminar campo | **Nada** — `model_dump(exclude_none=True)` lo ignora |
| Añadir procedimiento nuevo | Crear archivo en `procedures/` referenciando `module_id` + `section_id` |
| Añadir componente de UI generativa | Crear componente + añadir case en `AssistantMessage.tsx` + type en store |
