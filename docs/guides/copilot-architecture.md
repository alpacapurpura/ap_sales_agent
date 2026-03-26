# Copilot Agentico - Arquitectura y Funcionamiento

## Resumen

El Copilot es un asistente de IA integrado en Nicolify que vive en un panel lateral permanente. Puede navegar la app, leer datos del negocio del usuario, y proponer cambios a formularios — todo mediante una arquitectura agentica (ReAct loop) con streaming SSE.

***

## Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                  │
│                                                          │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐   │
│  │ Zustand   │  │ CopilotPanel│  │ WithCopilot       │   │
│  │ Store     │◄─┤ CopilotChat │  │ (field wrapper)   │   │
│  │           │  │ ContextChips│  │                   │   │
│  └─────┬────┘  └──────┬─────┘  └────────┬──────────┘   │
│        │              │                  │               │
│        │    SSE Stream│         CustomEvent               │
│        │              │     copilot:field-update          │
│        │              ▼                  │               │
│  ┌─────┴──────────────────┐    ┌────────┴──────────┐    │
│  │ useCopilotChat         │    │ useCopilotFieldSync│    │
│  │ useCopilotNavigator    │    │ (React Hook Form)  │    │
│  └────────────┬───────────┘    └───────────────────┘    │
└───────────────┼─────────────────────────────────────────┘
                │ POST /api/v1/copilot/chat
                ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              CopilotOrchestrator                  │   │
│  │  - Gestiona estado de conversacion               │   │
│  │  - Persiste historial (Redis + PostgreSQL)        │   │
│  │  - Emite eventos SSE al frontend                  │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │            LangGraph ReAct Agent                  │   │
│  │                                                   │   │
│  │  ┌─────────┐    ┌──────────┐                     │   │
│  │  │  agent   │───▶│ tools    │──┐                  │   │
│  │  │  (LLM)  │◀───│ executor │◀─┘                  │   │
│  │  └─────────┘    └──────────┘                     │   │
│  │       │                                           │   │
│  │       ▼ (sin tool calls = END)                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Tools disponibles:                                      │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐  │
│  │ Navigation │ │ Awareness │ │ Mutation │ │ Read   │  │
│  │ (4 tools)  │ │ (1 tool)  │ │ (1 tool) │ │(2 tools│  │
│  └────────────┘ └───────────┘ └──────────┘ └────────┘  │
└─────────────────────────────────────────────────────────┘
```

***

## Componentes Frontend

### Zustand Store (`features/copilot/store/copilot-store.ts`)

Estado central del copilot, persiste entre navegaciones.

| Estado             | Tipo                                            | Proposito                          |
| ------------------ | ----------------------------------------------- | ---------------------------------- |
| `isOpen`           | `boolean`                                       | Panel expandido/colapsado          |
| `messages`         | `CopilotMessage[]`                              | Historial del chat                 |
| `status`           | `"idle" \| "thinking" \| "streaming" \| "done"` | Estado de la peticion              |
| `conversationId`   | `string \| null`                                | ID de conversacion activa          |
| `currentRoute`     | `string \| null`                                | Ruta actual del usuario            |
| `pendingUIActions` | `UIAction[]`                                    | Cola de acciones UI pendientes     |
| `selectedFields`   | `SelectedField[]`                               | Campos seleccionados como contexto |

Tipos clave:

```typescript
interface UIAction {
  type: "navigate" | "scroll_to_field" | "open_form" | "proposal";
  route?: string;
  page_label?: string;
  section_id?: string;
  field_id?: string;
  form_id?: string;
  prefill_data?: Record<string, unknown>;
  updates?: ProposalUpdate[];  // Solo para type: "proposal"
}

interface ProposalUpdate {
  field_id: string;
  new_value: string;
  reason?: string;
}

interface SelectedField {
  fieldId: string;
  fieldLabel: string;
  fieldValue: string;
}
```

### CopilotPanel (`components/CopilotPanel.tsx`)

Componente raiz del copilot. Montado en el dashboard layout.

- **Expandido:** Panel de 380px con header + CopilotChat
- **Colapsado:** Rail de 60px con iconos (CopilotRail)
- Activa `useRouteTracker` (sincroniza ruta al store) y `useCopilotNavigator` (procesa cola de acciones)

### CopilotChat (`components/CopilotChat.tsx`)

Chat principal con:

- Area de mensajes (UserMessage + AssistantMessage)
- SuggestedActions (acciones rapidas contextuales por ruta)
- ContextChips (campos seleccionados)
- Input con auto-resize + boton enviar/detener

### AssistantMessage (`components/messages/AssistantMessage.tsx`)

Renderiza mensajes del asistente con:

- Texto con streaming (cursor pulsante)
- **NavigationCard** — boton para navegar a una pagina/seccion
- **ProposalCard** — propuesta de cambios con Aplicar/Rechazar

### NavigationCard (`components/messages/NavigationCard.tsx`)

Boton que ejecuta una accion de navegacion al hacer clic. Muestra el label de la pagina destino con un icono de MapPin.

### ProposalCard (`components/messages/ProposalCard.tsx`)

Tarjeta de propuesta de cambios del copilot:

```
┌─────────────────────────────────────┐
│ ✏️ Propuesta de cambios             │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ uvp                             │ │
│ │ "Nueva propuesta de valor..."   │ │
│ │ Razon: Mas enfocada al dolor    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Aplicar]  [Rechazar]               │
└─────────────────────────────────────┘
```

Estados: `pending` (purple) → `applied` (green) / `rejected` (grey)

Al hacer clic en "Aplicar", despacha un `CustomEvent("copilot:field-update")` por cada campo, que los formularios escuchan via `useCopilotFieldSync`.

### SuggestedActions (`components/SuggestedActions.tsx`)

Acciones rapidas contextuales que aparecen cuando el chat esta vacio. Se adaptan segun la ruta actual:

| Ruta               | Sugerencias                                                     |
| ------------------ | --------------------------------------------------------------- |
| `brand-settings`   | "Que me falta de mi marca?", "Mejora mi UVP", "Extrae mi marca" |
| `offer-studio`     | "Crea una oferta", "Revisa mi escalera"                         |
| `growth-studio` | "Explica mi funnel", "Como mejoro conversion?"                  |
| `sales`            | "Como va mi agente?"                                            |
| `connections`      | "Que debo conectar?"                                            |
| Default            | "Que me falta configurar?", "Guiame paso a paso"                |

### ContextChips (`components/ContextChips.tsx`)

Muestra los campos seleccionados como contexto sobre el input del chat. Cada chip tiene un "x" para quitar. Boton "Limpiar" cuando hay 2+ campos.

```
┌─────────────────────────────────────┐
│ CONTEXTO  [UVP ×] [Tagline ×] Limpiar│
└─────────────────────────────────────┘
```

### WithCopilot (`components/WithCopilot.tsx`)

Wrapper para cualquier campo de formulario. Hace el campo "copilot-aware":

```tsx
<WithCopilot fieldId="uvp" fieldLabel="Propuesta de Valor" getValue={() => form.getValues("uvp")}>
  <Input {...form.register("uvp")} />
</WithCopilot>
```

Comportamiento:

1. **Hover/focus** → muestra boton sparkle (✨) en esquina superior derecha
2. **Clic en sparkle** → agrega campo al contexto del copilot + abre panel
3. **Campo seleccionado** → borde purple
4. **Copilot actualiza campo** → borde green con glow (2 segundos)

### Hooks

#### `useCopilotChat` (`hooks/useCopilotChat.ts`)

- Envia mensajes al backend via `streamCopilotChat`
- Maneja SSE: text\_chunk, tool\_start, tool\_result, ui\_action, status, done, error
- Las `ui_action` de tipo `navigate` se encolan automaticamente
- Las `ui_action` de tipo `proposal` solo se adjuntan al mensaje (sin auto-ejecutar)
- Envia `selectedFields` como contexto en cada peticion

#### `useCopilotNavigator` (`hooks/useCopilotNavigator.ts`)

- Procesa la cola `pendingUIActions` del store
- Ejecuta acciones: `navigate` (router.push + scroll), `scroll_to_field` (querySelector + highlight), `open_form` (CustomEvent)
- Aplica animacion CSS `copilot-highlight` (purple pulse, 3 segundos)

#### `useCopilotFieldSync` (`hooks/useCopilotFieldSync.ts`)

- Puente entre el copilot y React Hook Form
- Escucha `copilot:field-update` y llama `setValue()` con `shouldDirty: true`
- Acepta `fieldMap` opcional para remapear field\_ids a paths del form

```typescript
// Ejemplo de uso en un formulario de Brand Studio
const { setValue } = useForm<BrandPositioningForm>();

useCopilotFieldSync(setValue, {
  "uvp": "positioning.uvp",
  "brand_essence": "positioning.brand_essence",
});
```

#### `useRouteTracker` (`hooks/useRouteTracker.ts`)

- Sincroniza `usePathname()` al store del copilot
- El backend recibe la ruta actual como contexto

### API (`api/copilot-api.ts`)

`streamCopilotChat(payload, callbacks, signal)` — hace `POST /api/v1/copilot/chat` con streaming SSE.

Eventos SSE soportados:

| Evento        | Datos                 | Accion frontend                            |
| ------------- | --------------------- | ------------------------------------------ |
| `text_chunk`  | `{ content }`         | Append al ultimo mensaje assistant         |
| `tool_start`  | `{ tool, args }`      | Muestra "🔧 tool..." en chat               |
| `tool_result` | `{ tool, result }`    | (alimenta al LLM)                          |
| `ui_action`   | `UIAction`            | Adjunta al mensaje + encola si es navigate |
| `status`      | `{ state }`           | Actualiza status del store                 |
| `done`        | `{ conversation_id }` | Guarda conversation\_id, status → idle     |
| `error`       | `{ message }`         | Muestra error en chat                      |

### Layout Integration (`app/(main)/[tenantId]/(dashboard)/layout.tsx`)

El layout del dashboard ajusta `padding-right` dinamicamente:

- Copilot cerrado: `pr-[60px]` (rail)
- Copilot abierto: `pr-[380px]` (panel completo)

Transicion suave via `transition-all duration-300 ease-in-out`.

### CSS (`app/globals.css`)

```css
@keyframes copilotPulse {
  0%   { box-shadow: 0 0 0 0 hsl(270 70% 60% / 0.4); }
  50%  { box-shadow: 0 0 0 6px hsl(270 70% 60% / 0); }
  100% { box-shadow: 0 0 0 0 hsl(270 70% 60% / 0); }
}

.copilot-highlight {
  animation: copilotPulse 1s ease-in-out 3;
  outline: 2px solid hsl(270 70% 60% / 0.6);
  outline-offset: 2px;
  border-radius: 4px;
}
```

***

## Componentes Backend

### API Endpoint (`api/chat.py`)

`POST /api/v1/copilot/chat` — recibe mensaje + contexto, retorna SSE stream.

```json
{
  "message": "Mejora mi UVP",
  "conversation_id": "uuid-opcional",
  "context": {
    "current_route": "/tenant-123/brand-settings",
    "selected_fields": [
      {"field_id": "uvp", "field_label": "Propuesta de Valor", "field_value": "..."}
    ],
    "locale": "es"
  }
}
```

Headers requeridos: `X-Tenant-ID`.

### CopilotOrchestrator (`application/orchestrator/chat.py`)

Orquestador principal que:

1. **Resuelve conversacion** — crea nueva o carga existente por ID
2. **Construye estado** — inyecta contexto del cliente
3. **Carga historial** — Redis (fast, TTL 1h) → PostgreSQL (fallback)
4. **Ejecuta el grafo** — `copilot_graph.astream_events()` con streaming
5. **Emite SSE** — text\_chunk, tool\_start, tool\_result, ui\_action
6. **Persiste** — guarda mensajes en PG + cache en Redis
7. **Auto-titula** — primera vez usa los primeros 80 chars del mensaje

### LangGraph ReAct Agent (`application/orchestrator/graph.py`)

Grafo simple de 2 nodos:

```
START → agent → [has tool calls?] → tools → agent → ...
                       ↓ no
                      END
```

- **agent\_node** — llama al LLM (OpenAI) con system prompt + historial + tool bindings
- **tool\_executor\_node** — ejecuta las tool calls y retorna ToolMessages
- **should\_continue** — routing condicional: si hay tool\_calls → tools, sino → END

System prompt dinamico renderizado con Jinja2 incluyendo ruta actual y campos seleccionados.

### State (`application/orchestrator/state.py`)

```python
class CopilotState(TypedDict):
    messages: List[BaseMessage]       # LangChain messages
    user_id: UUID
    tenant_id: UUID
    client_context: ClientContext      # Ruta, campos seleccionados, form_data
    conversation_id: str
    pending_ui_actions: List[Dict]
    error: Optional[str]
```

### Tools

#### Navigation Tools (`application/tools/navigation.py`)

| Tool                                     | Descripcion                        | Retorna                                              |
| ---------------------------------------- | ---------------------------------- | ---------------------------------------------------- |
| `navigate_to_page(keyword, section_id?)` | Navega a una pagina por keyword    | `ui_action: { type: "navigate", route, page_label }` |
| `scroll_to_field(field_id)`              | Scroll + highlight a un campo      | `ui_action: { type: "scroll_to_field", field_id }`   |
| `open_form(form_id, prefill_data?)`      | Abre un formulario/dialog          | `ui_action: { type: "open_form", form_id }`          |
| `list_app_pages()`                       | Lista todas las paginas navegables | Texto formateado                                     |

Usa `navigation_map.py` como fuente de verdad de rutas, secciones y keywords.

#### Awareness Tools (`application/tools/awareness.py`)

| Tool                                    | Descripcion                                                       |
| --------------------------------------- | ----------------------------------------------------------------- |
| `get_module_completion_status(module?)` | Revisa que modulos estan configurados (brand, offer, connections) |

Accede a DB directamente con `SessionLocal()` y `get_tenant_id()`.

#### Mutation Tools (`application/tools/mutations.py`)

| Tool                             | Descripcion                             |
| -------------------------------- | --------------------------------------- |
| `propose_field_updates(updates)` | Propone cambios a campos del formulario |

Valida que cada update tenga `field_id` y `new_value`. Retorna `ui_action: { type: "proposal", updates }`. El frontend renderiza un ProposalCard con Aplicar/Rechazar.

#### Brand Read Tools (`application/tools/brand_tools.py`)

| Tool                       | Descripcion                              |
| -------------------------- | ---------------------------------------- |
| `get_brand_data(section?)` | Lee la configuracion de marca del tenant |

Secciones: identity, story, positioning, narrative, visuals, voice, strategy, testimonials, authority, communication\_assets. Sin seccion retorna resumen completo.

#### Offer Read Tools (`application/tools/offer_tools.py`)

| Tool                        | Descripcion                          |
| --------------------------- | ------------------------------------ |
| `get_offer_data(offer_id?)` | Lee las ofertas/productos del tenant |

Sin offer\_id retorna resumen de todas las ofertas activas. Con ID retorna detalle completo incluyendo pricing, puntos de dolor, deseos, objeciones, garantias.

### Navigation Map (`domain/navigation_map.py`)

Mapa estatico de todas las paginas navegables de la app con:

- `route_template` — ruta con placeholder `{tenantId}`
- `keywords` — palabras clave para matching
- `sections` — secciones dentro de cada pagina
- `module` — modulo al que pertenece

### Persistencia

- **Redis** — contexto activo de conversacion (TTL 1 hora). Key: `copilot:conv:{conversation_id}`
- **PostgreSQL** — historial completo de conversaciones. Modelo: `CopilotConversation` con campos `messages` (JSONB), `title`, `tenant_id`, `user_id`

### System Prompt (`infrastructure/prompts/templates/copilot_system.j2`)

Template Jinja2 con:

- Rol y personalidad (espanol, tuteo, proactivo, conciso)
- Contexto dinamico (ruta actual, campos seleccionados)
- Reglas de comportamiento (no inventar datos, siempre proponer antes de mutar)
- Instrucciones para herramientas de mutacion (incluir `reason`, priorizar campos seleccionados)
- Instrucciones para herramientas de lectura (siempre leer antes de proponer)

***

## Flujos Principales

### Flujo 1: Chat basico

```
Usuario escribe mensaje
  → useCopilotChat.sendMessage()
  → POST /api/v1/copilot/chat (SSE)
  → CopilotOrchestrator.stream_chat()
  → LangGraph agent_node (LLM)
  → SSE text_chunk events
  → appendToLastAssistant() en store
  → AssistantMessage renderiza texto
```

### Flujo 2: Navegacion asistida

```
Usuario: "Llevame al Brand Studio"
  → LLM llama navigate_to_page("brand")
  → tool retorna { ui_action: { type: "navigate", route: "/{tenantId}/brand-settings" } }
  → SSE ui_action event
  → onUIAction → addUIActionToLastAssistant + enqueuUIAction
  → AssistantMessage renderiza NavigationCard
  → useCopilotNavigator procesa queue → router.push()
```

### Flujo 3: Propuesta de cambios (round-trip completo)

```
1. Usuario selecciona campo UVP con WithCopilot (sparkle button)
   → addSelectedField({ fieldId: "uvp", fieldLabel: "UVP", fieldValue: "..." })
   → ContextChips muestra [UVP x]

2. Usuario: "Hazlo mas agresivo"
   → sendMessage incluye selected_fields en context
   → LLM lee get_brand_data("positioning") para contexto
   → LLM llama propose_field_updates([{ field_id: "uvp", new_value: "...", reason: "..." }])
   → SSE ui_action { type: "proposal", updates: [...] }
   → AssistantMessage renderiza ProposalCard

3. Usuario hace clic en "Aplicar"
   → ProposalCard despacha CustomEvent("copilot:field-update", { fieldId: "uvp", newValue: "..." })
   → WithCopilot escucha → muestra borde green (2s)
   → useCopilotFieldSync escucha → setValue("uvp", "...") en React Hook Form
   → El formulario se actualiza, campo queda dirty
   → Usuario puede guardar cuando quiera
```

### Flujo 4: Auditoria de completitud

```
Usuario: "Que me falta configurar?"
  → LLM llama get_module_completion_status("all")
  → Retorna estado de Brand (4/8 secciones), Offer (2 ofertas), Connections (1 activa)
  → LLM responde con resumen + sugerencias
  → Opcionalmente llama navigate_to_page() para guiar al usuario
```

***

## Estructura de Archivos

```
frontend/src/features/copilot/
├── api/
│   └── copilot-api.ts              # SSE streaming client
├── components/
│   ├── CopilotChat.tsx             # Chat principal
│   ├── CopilotPanel.tsx            # Panel raiz (expanded/collapsed)
│   ├── CopilotRail.tsx             # Rail colapsado (60px)
│   ├── ContextChips.tsx            # Chips de campos seleccionados
│   ├── SuggestedActions.tsx        # Acciones rapidas por ruta
│   ├── WithCopilot.tsx             # Wrapper para campos de formulario
│   └── messages/
│       ├── AssistantMessage.tsx     # Mensaje del asistente
│       ├── NavigationCard.tsx       # Card de navegacion
│       ├── ProposalCard.tsx         # Card de propuesta de cambios
│       └── UserMessage.tsx          # Mensaje del usuario
├── hooks/
│   ├── useCopilotChat.ts           # Logica de envio/recepcion SSE
│   ├── useCopilotFieldSync.ts      # Puente copilot → React Hook Form
│   ├── useCopilotNavigator.ts      # Ejecutor de acciones UI
│   └── useRouteTracker.ts          # Sincroniza ruta al store
└── store/
    └── copilot-store.ts            # Zustand store central

backend/src/modules/copilot/
├── api/
│   ├── chat.py                     # POST /api/v1/copilot/chat
│   └── dto.py                      # DTOs (SSEEvent, ClientContextDTO)
├── application/
│   ├── orchestrator/
│   │   ├── chat.py                 # CopilotOrchestrator
│   │   ├── graph.py                # LangGraph ReAct agent
│   │   └── state.py                # CopilotState TypedDict
│   └── tools/
│       ├── awareness.py            # get_module_completion_status
│       ├── brand_tools.py          # get_brand_data
│       ├── mutations.py            # propose_field_updates
│       ├── navigation.py           # navigate_to_page, scroll_to_field, open_form, list_app_pages
│       └── offer_tools.py          # get_offer_data
├── domain/
│   └── navigation_map.py           # Mapa de paginas/secciones
└── infrastructure/
    ├── models/
    │   └── conversation_model.py   # SQLAlchemy model
    ├── prompts/
    │   └── templates/
    │       └── copilot_system.j2   # System prompt Jinja2
    └── repositories/
        └── conversation_repository.py  # CRUD conversaciones
```

