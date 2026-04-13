# Unified Copilot Design Spec

**Date:** 2026-04-13
**Status:** Draft
**Scope:** Major refactoring — unify 4 fragmented AI systems into ONE copilot with context-aware behavior

---

## 1. Problem Statement

The codebase has 4 disconnected AI assistance systems that should be one:

| System | What it does | Status |
|---|---|---|
| **Copilot Sidebar** | Chat with route-aware tools, no audio/files | Working |
| **Interview Engine** | Split-view guided creation with blocks | Broken (missing endpoint, system prompt not wired) |
| **SmartFill (Offer/Brand)** | Batch extraction from URL/docs, polling-based | Working but disconnected from copilot |
| **WithCopilot** | Field-level AI suggestions | Working but unaware of focus/interview |

**Key problems:**
- Interview chat endpoint (`POST /interview/{id}/message`) does not exist — falls back to generic chat losing all session context
- Interview system prompt (`system_base.j2`) is NOT wired into `build_system_prompt()` — the LLM has no block/mapa_global/expertise context
- Audio (useVoiceRecorder) and file upload (AttachmentButton) exist only in InterviewInput — sidebar has none
- 3 parallel extraction pipelines with no code reuse
- No context window management (no token counting, no history truncation)
- No field_path validation in extract_structured (LLM can hallucinate fields)
- Interview cannot go back to previous blocks
- InterviewBanner hardcodes `/brand-studio/interview`

## 2. Design Principles

1. **ONE copilot.** What changes is the CONTEXT, not the component, not the endpoint, not the code path.
2. **Capture everything.** Any data the user mentions — in any order, any format, any section — gets captured immediately. Never ask the user to repeat themselves.
3. **Auto-save progressive.** In Focus mode, every AI change persists immediately (like manual editing). Snapshot at focus start enables "undo all".
4. **Be smart, not structured.** The interview adapts to what it already knows. High coverage = confirm fast. Zero coverage = full questions. Mixed = fill gaps only.
5. **No technical debt.** Every file in the right DDD/FSD folder. Every new code passes ruff + eslint. Dead code gets removed.

## 3. Architecture Overview

### 3.1 Single Endpoint

All modes use `POST /api/v1/copilot/chat`. No new endpoints for focus/interview chat.

```python
class ClientContextDTO(BaseModel):
    current_route: str | None = None
    selected_fields: list[dict[str, str]] = Field(default_factory=list)
    form_data: dict[str, Any] = Field(default_factory=dict)
    locale: str = "es"
    # NEW
    focus: FocusContextDTO | None = None
    interview_session_id: str | None = None

class FocusContextDTO(BaseModel):
    domain: str                    # "offer", "brand", "buyer_persona"
    entity_id: str | None = None   # UUID (None for brand singleton)
```

Mode determination (implicit):
- `interview_session_id` present → Interview mode
- `focus` present → Focus mode
- Neither → Chat mode

### 3.2 Sidebar: 3 Width States (one component)

| State | Width | When | Content |
|---|---|---|---|
| Rail | 60px | Copilot closed | Sparkles icon |
| Normal | 380px | Chat open | Chat + unified input |
| Expanded | 780px | Focus or Interview | Preview (400px) + Chat (380px) |

- Push layout (padding-right), not overlay
- Viewport <1280px: left sidebar auto-collapses to 80px rail
- Mobile (<768px): full-screen overlay sheet with preview/chat toggle

### 3.3 Unified Input (always the same)

```
[textarea] [mic] [attach] [send]
```

- Mic and attachments always visible in ALL modes
- useVoiceRecorder moves from interview to unified input
- Document chips below input
- Context chips (selected fields) only in chat mode

### 3.4 Auto-save Progressive

- **Focus Mode:** Each `entity_write` tool call persists immediately via persisters
- **Snapshot at focus start:** Full entity state saved. Enables "undo all" (restore snapshot)
- **AI badges:** Fields modified by copilot show "AI" badge. Badge disappears on manual edit
- **Interview Mode:** mapa_global accumulates, persists on `advance_block` / `complete_interview`

## 4. Frontend Architecture

### 4.1 Component Tree

```
CopilotSidebar (replaces CopilotPanel)
  +-- [collapsed] CopilotSidebarRail
  |
  +-- [open/expanded] CopilotSidebarPanel
      +-- CopilotHeader
      |   +-- Context indicator ("Chat" / "Focus: Oferta Premium" / "Interview: Brand")
      |   +-- Expand/collapse button
      |   +-- New conversation / close
      |
      +-- FocusBar (only in focus/interview)
      |   +-- Entity label + domain icon
      |   +-- "Salir de Focus" button
      |   +-- Progress dots (interview only)
      |   +-- "Deshacer todo" button
      |
      +-- [expanded] CopilotPreviewPane (400px left column)
      |   +-- PreviewSummary (lazy loaded by domain)
      |   +-- PreviewSections (lazy loaded by domain)
      |       +-- Click on section -> sends message to chat
      |
      +-- CopilotConversation (380px, always visible)
      |   +-- MessageList
      |       +-- UserMessage
      |       +-- AssistantMessage
      |           +-- Generic cards (navigate, proposal, metric, checklist)
      |           +-- Interview cards (alternatives, clarify, checkpoint, complete)
      |           +-- Focus cards (diff before/after, sources)
      |
      +-- CopilotInput
          +-- textarea
          +-- MicButton (useVoiceRecorder)
          +-- AttachmentButton (multi-file)
          +-- SendButton / StopButton
          +-- DocumentChips
          +-- ContextChips (chat mode only)
```

### 4.2 FSD File Organization

```
frontend/src/features/copilot/
  api/
    copilot-api.ts          # streamCopilotChat (absorbs interview streaming)
    interview-api.ts        # lifecycle only: start, pause, abandon, state, active
    voice-api.ts            # transcribeAudio (unchanged)
    document-api.ts         # processDocuments (unchanged)
  components/
    copilot-sidebar.tsx      # NEW: replaces CopilotPanel, 3 width states
    copilot-sidebar-rail.tsx # RENAMED from CopilotRail
    copilot-header.tsx       # NEW: mode indicator, expand/collapse
    copilot-input.tsx        # NEW: unified textarea+mic+attachments
    copilot-conversation.tsx # NEW: message list (absorbs CopilotChat message rendering)
    copilot-preview-pane.tsx # NEW: lazy preview loader
    copilot-status-bar.tsx   # NEW: replaces InterviewBanner
    focus-bar.tsx            # NEW: entity label, exit focus, undo all, progress
    focus-mode-button.tsx    # RENAMED from InterviewModeButton
    WithCopilot.tsx          # MODIFIED: focus-mode aware behavior
    CopilotChat.tsx          # DEPRECATED in Phase 4 (absorbed into copilot-conversation)
    ContextChips.tsx         # KEPT (used inside CopilotInput)
    SuggestedActions.tsx     # KEPT
    NudgeBanner.tsx          # KEPT
    ProcedureProgress.tsx    # KEPT
    messages/                # KEPT: all message renderers
    cards/                   # KEPT: all interview card renderers (used by AssistantMessage)
    shared/
      attachment-button.tsx  # KEPT
      document-chip.tsx      # KEPT
      section-chat-trigger.tsx # KEPT
  hooks/
    useCopilotChat.ts        # MODIFIED: absorbs useInterviewChat logic (mode-aware send)
    useVoiceRecorder.ts      # MOVED here from interview/ (used by CopilotInput)
    useRouteTracker.ts       # KEPT
    useCopilotNavigator.ts   # KEPT
    useCopilotFieldSync.ts   # KEPT
    useProactiveNudges.ts    # KEPT
  store/
    copilot-store.ts         # MODIFIED: new shape with focus/interview state
  config/
    preview-registry.ts      # MODIFIED: lazy imports, no side-effects
  types/
    index.ts                 # MODIFIED: unified message type, focus entity type
```

Files to DELETE in Phase 4:
- `components/interview/interview-split-view.tsx`
- `components/interview/interview-chat-panel.tsx`
- `components/interview/interview-input.tsx`
- `components/interview/interview-header.tsx`
- `components/interview/interview-message.tsx` (logic absorbed into AssistantMessage)
- `components/interview/session-restore-modal.tsx` (logic absorbed into CopilotStatusBar)
- `hooks/useInterviewChat.ts`
- `components/shared/interview-mode-button.tsx` (replaced by focus-mode-button)

Files to DELETE from other features in Phase 4:
- `features/brand/components/interview/interview-split-view.tsx` (wrapper)
- `features/brand/components/interview/session-restore-modal.tsx` (duplicate)
- `features/brand/components/interview/interview-header.tsx`
- `features/brand/components/interview/register-brand-preview.ts` (side-effect)
- `features/offer-studio/components/interview/register-offer-preview.tsx` (side-effect)
- `features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx`
- `features/offer-studio/components/container/autocompletar-ia-button.tsx`
- `components/shared/interview-banner.tsx`

### 4.3 Zustand Store

```typescript
interface CopilotState {
  // Sidebar UI
  sidebarState: "collapsed" | "open" | "expanded";
  setSidebarState: (s: "collapsed" | "open" | "expanded") => void;

  // Conversation (ONE stream, shared across all modes)
  conversationId: string | null;
  messages: CopilotMessage[];
  status: "idle" | "thinking" | "streaming" | "error";
  setConversationId: (id: string) => void;
  addMessage: (msg: CopilotMessage) => void;
  appendToLastAssistant: (chunk: string) => void;
  addUIActionToLastAssistant: (action: UIAction) => void;
  setStatus: (s: CopilotStatus) => void;
  clearConversation: () => void;

  // Route awareness
  currentRoute: string | null;
  setCurrentRoute: (route: string) => void;

  // UI Action queue
  pendingUIActions: UIAction[];
  enqueueUIAction: (action: UIAction) => void;
  dequeueUIAction: () => UIAction | undefined;

  // Procedure
  activeProcedure: ActiveProcedure | null;
  setActiveProcedure: (proc: ActiveProcedure) => void;
  clearActiveProcedure: () => void;

  // Selected fields (chat mode only)
  selectedFields: SelectedField[];
  addSelectedField: (field: SelectedField) => void;
  removeSelectedField: (fieldId: string) => void;
  updateFieldValue: (fieldId: string, value: string) => void;
  clearSelectedFields: () => void;

  // Focus context (focus + interview modes)
  focusEntity: FocusEntity | null;
  focusSnapshot: Record<string, unknown> | null;
  setFocusEntity: (entity: FocusEntity) => void;
  setFocusSnapshot: (snapshot: Record<string, unknown>) => void;
  clearFocus: () => void;

  // Interview (extends focus)
  interviewSessionId: string | null;
  interviewProgress: InterviewProgress | null;
  setInterviewSession: (id: string) => void;
  setInterviewProgress: (p: InterviewProgress) => void;
  clearInterview: () => void;

  // Preview data (accumulates from preview_update SSE events)
  previewData: Record<string, unknown> | null;
  updatePreviewData: (delta: Record<string, unknown>) => void;
  clearPreviewData: () => void;
}

// Mode is a DERIVED getter, not stored
function getMode(state: CopilotState): "chat" | "focus" | "interview" {
  if (state.interviewSessionId) return "interview";
  if (state.focusEntity) return "focus";
  return "chat";
}

interface FocusEntity {
  domain: "brand" | "offer" | "buyer_persona";
  entityId?: string;
  label: string;
}

interface InterviewProgress {
  currentBlock: string;
  blocksCompleted: string[];
  totalBlocks: number;
}
```

### 4.4 Preview Registry (lazy, no side-effects)

```typescript
const PREVIEW_REGISTRY: Record<string, {
  summary: () => Promise<{ default: ComponentType<PreviewSummaryProps> }>;
  sections: () => Promise<{ default: ComponentType<PreviewSectionsProps> }>;
  emptyMessage: string;
}> = {
  brand: {
    summary: () => import("@/features/brand/components/interview/brand-preview-summary")
      .then(m => ({ default: m.BrandPreviewSummary })),
    sections: () => import("@/features/brand/components/interview/brand-preview-sections")
      .then(m => ({ default: m.BrandPreviewSections })),
    emptyMessage: "Responde las preguntas para construir tu perfil de marca.",
  },
  offer: {
    summary: () => import("@/features/offer-studio/components/interview/previews/offer-preview-summary")
      .then(m => ({ default: m.OfferPreviewSummary })),
    sections: () => import("@/features/offer-studio/components/interview/previews/offer-preview-sections")
      .then(m => ({ default: m.OfferPreviewSections })),
    emptyMessage: "Describe tu oferta para ver la vista previa en vivo.",
  },
  buyer_persona: {
    summary: () => import("@/features/brand/components/interview/previews/persona-preview-summary")
      .then(m => ({ default: m.PersonaPreviewSummary })),
    sections: () => import("@/features/brand/components/interview/previews/persona-preview-sections")
      .then(m => ({ default: m.PersonaPreviewSections })),
    emptyMessage: "Comienza la entrevista para construir tu buyer persona.",
  },
};
```

### 4.5 Mode Transitions

```
Chat -> Focus:
  1. setFocusEntity({ domain, entityId, label })
  2. setSidebarState("expanded")
  3. Save entity snapshot (focusSnapshot)
  4. Clear selectedFields
  5. Visual separator in conversation: "Focus activado en {label}"

Focus -> Interview:
  1. startInterview(domain, entityId) -> sessionId
  2. setInterviewSession(sessionId)
  3. Add initial_message to messages
  4. interviewProgress tracks blocks

Interview -> Focus ("Volver a modo manual"):
  1. pauseInterview(sessionId)
  2. clearInterview()
  3. focusEntity STAYS (still focused on entity)
  4. Sidebar stays expanded
  5. CopilotStatusBar shows "Interview pausado — Continuar"

Focus -> Chat:
  1. clearFocus()
  2. setSidebarState("open")
  3. Conversation preserved

Navigation during Focus:
  - Same entity (other tab of same offer): no change
  - Different entity same domain: toast "Cambiar de focus?"
  - Different domain: auto-pause, sidebar collapses to rail with pulse indicator
```

### 4.6 Entry Points

| Location | Button | Action |
|---|---|---|
| Offer editor header (replaces "Autocompletar IA") | "Focus" + Sparkles icon | setFocusEntity for current offer |
| OfferCard dropdown | "Mejorar con IA" | Navigate to offer + activate focus |
| Brand Studio header | "Focus" | setFocusEntity for brand |
| CreateOfferWizard final step | "Crear con asistente IA" | Create offer + navigate + activate interview |
| CopilotStatusBar | "Continuar" | Restore paused focus/interview |

### 4.7 Offer Creation Flow with Interview

```
"Nueva Oferta" button (dashboard)
  |
  v
CreateOfferWizard (dialog, unchanged steps 1-5)
  Step 1: Archetype (Producto, Programa, Servicio, Membresia, Experiencia)
  Step 2: Format (preset or custom)
  Step 3: Basic data (name, price)
  Step 4: Promise (optional)
  Step 5: Editions (if applicable)
  |
  v
Final step buttons change to:
  [Crear y completar manual]     -> navigates to editor (current behavior)
  [Crear con asistente IA]       -> creates offer + activates interview
  |
  v (if user chooses IA)
  1. Create offer in DB (with archetype, name, price from wizard)
  2. Navigate to /offer-studio/offer/{id}
  3. Activate interview automatically:
     - setFocusEntity({ domain: "offer", entityId: id, label: name })
     - startInterview("offer", id) -> generates blocks based on archetype
     - setSidebarState("expanded")
  4. Interview config generated dynamically based on archetype
     (Producto gets product_details block, Programa gets program_details, etc.)
```

"Volver a modo manual" during interview:
1. Pauses interview, clears interviewSessionId
2. focusEntity STAYS (still focused on the offer)
3. Mode goes from "interview" to "focus"
4. User can edit manually OR keep talking to copilot in focus mode
5. CopilotStatusBar: "Interview pausado (3/6 bloques) — Continuar"

## 5. Backend Architecture

### 5.1 DDD File Organization

```
backend/src/modules/copilot/
  domain/
    interview_config.py      # MODIFIED: dynamic config generation per archetype
    interview_session.py     # MODIFIED: add revert_to_block()
    module_registry.py       # KEPT
    navigation_map.py        # KEPT
    schema_introspection.py  # KEPT
    voice.py                 # KEPT
  infrastructure/
    models/                  # KEPT (all models)
    repositories/            # KEPT (all repos)
    persisters/
      brand_persister.py     # KEPT
      offer_persister.py     # KEPT
      persister_registry.py  # KEPT
    context/
      offer_context_loader.py    # KEPT
      context_loader_registry.py # KEPT
      focus_context_loader.py    # NEW: loads entity snapshot for focus mode
    knowledge/               # KEPT
    voice/                   # KEPT
    web/                     # KEPT
  application/
    orchestrator/
      chat.py                # MODIFIED: load focus/interview context into state
      graph.py               # MODIFIED: build_system_prompt with layers, tool selection by mode
      state.py               # MODIFIED: add focus_snapshot, interview_session to state
    services/
      interview_service.py   # MODIFIED: dynamic config, revert_to_block
      document_processor.py  # KEPT
      knowledge_ingestion.py # KEPT
      web_extractor_adapter.py # KEPT
    tools/
      registry.py            # MODIFIED: tool selection by (route, mode) tuple
      navigation.py          # KEPT (universal)
      awareness.py           # KEPT (universal)
      mutations.py           # KEPT (universal)
      module_tools.py        # KEPT (universal)
      knowledge_tools.py     # KEPT (universal)
      analytics_tools.py     # KEPT (domain)
      crm_tools.py           # KEPT (domain)
      connections_tools.py   # KEPT (domain)
      landing_tools.py       # KEPT (domain)
      offer_ladder_tools.py  # KEPT (domain)
      procedure_tools.py     # KEPT (universal)
      sales_agent_tools.py   # KEPT (domain)
      focus/                 # NEW directory
        entity_write.py      # NEW: auto-save field modification
        entity_read.py       # NEW: read entity state
        entity_undo_all.py   # NEW: restore snapshot
        extract_from_document.py  # NEW: wraps extraction services
        extract_from_url.py  # NEW: web scraping + extraction
      interview/
        extract_structured.py   # MODIFIED: global extraction (any section)
        offer_alternatives.py   # KEPT
        clarify.py              # KEPT
        checkpoint.py           # KEPT
        advance_block.py        # KEPT
        complete_interview.py   # KEPT
        revert_to_block.py      # NEW: go back to previous block
      # NOTE: web_research.py lives in focus/ but is included in
      # both focus and interview tool categories (shared tool)
  api/
    chat.py                  # KEPT (endpoint unchanged, context extended)
    interview.py             # KEPT (lifecycle endpoints only)
    dto/
      chat_dto.py            # MODIFIED: add FocusContextDTO
      interview_dto.py       # MODIFIED: add entity_id to StartInterviewRequest
    events.py                # KEPT
    knowledge.py             # KEPT
    nudge.py                 # KEPT
    voice.py                 # KEPT
    actions.py               # DEPRECATED in Phase 4
```

### 5.2 System Prompt Composition (Layered)

```python
def build_system_prompt(state: CopilotState) -> str:
    context = state["client_context"]

    # Layer 0+1: Base + tenant context (always)
    base = prompt_loader.render("copilot_system", {
        completion_snapshot=_get_completion_snapshot(state),
        behavior_summary=_get_behavior_summary(state),
        module_list=_get_module_list(),
    })

    # Layer 2: Focus context (when focus active)
    focus_section = ""
    if context.get("focus"):
        entity_data = state.get("focus_entity_data", {})
        focus_section = prompt_loader.render("copilot_focus", {
            domain=context["focus"]["domain"],
            entity_snapshot=entity_data,
            empty_fields=_get_empty_fields(entity_data),
        })

    # Layer 3: Interview context (when interview active)
    interview_section = ""
    if context.get("interview_session_id"):
        session = state["interview_session"]
        config = session.config_snapshot
        block = next(
            (b for b in config.blocks if b.id == session.bloque_actual), None
        )
        interview_section = prompt_loader.render("copilot_interview", {
            current_block=block,
            mapa_global=session.mapa_global,
            coverage=session.coverage_for_block(session.bloque_actual),
            blocks_completed=session.bloques_completados,
            total_blocks=len(config.blocks),
            expertise_template=config.expertise_template,
            block_coverage_status=_get_all_blocks_coverage(session),
        })

    return base + focus_section + interview_section
```

### 5.3 Tool Selection by Context

```python
TOOL_CATEGORIES = {
    "universal": [navigation, awareness, module_data, knowledge, procedure],
    "mutation": [propose_field_updates],
    "focus": [entity_write, entity_read, entity_undo_all,
              extract_from_document, extract_from_url, web_research,
              offer_alternatives],
    "interview": [extract_structured, offer_alternatives, clarify,
                  checkpoint, advance_block, complete_interview,
                  revert_to_block, web_research],
    "domain": {
        "growth-studio": [analytics],
        "sales": [crm, sales_agent],
        "connections": [connections],
        "offer-studio": [offer_ladder],
        "landing": [landing],
    },
}

def get_tools_for_context(context: dict) -> list[Tool]:
    tools = TOOL_CATEGORIES["universal"].copy()

    if context.get("interview_session_id"):
        tools += TOOL_CATEGORIES["interview"]
        return tools

    if context.get("focus"):
        tools += TOOL_CATEGORIES["focus"]
        route = context.get("current_route", "")
        for pattern, domain_tools in TOOL_CATEGORIES["domain"].items():
            if pattern in route:
                tools += domain_tools
        return tools

    # Chat mode: universal + mutation + domain by route
    tools += TOOL_CATEGORIES["mutation"]
    route = context.get("current_route", "")
    for pattern, domain_tools in TOOL_CATEGORIES["domain"].items():
        if pattern in route:
            tools += domain_tools
    return tools
```

### 5.4 Focus Tools

```python
# focus/entity_write.py
@tool
def entity_write(field_path: str, value: Any, reason: str) -> str:
    """Modify a field on the focused entity. Auto-saves immediately."""
    # 1. Validate field_path against schema_introspection
    # 2. Persist via persister_registry (BrandPersister / OfferPersister)
    # 3. Emit ui_action: preview_update with delta
    # 4. Return confirmation with field + old value + new value

# focus/entity_read.py
@tool
def entity_read(section: str | None = None) -> str:
    """Read current state of the focused entity (or a specific section)."""

# focus/entity_undo_all.py
@tool
def entity_undo_all() -> str:
    """Restore entity to the state it had when focus started."""
    # Load focusSnapshot, overwrite entity via persister

# focus/extract_from_document.py
@tool
def extract_from_document(document_text: str, target_sections: list[str] | None = None) -> str:
    """Extract data from uploaded document and write to entity.
    Extracts against ALL sections simultaneously.
    Auto-saves each section as it's extracted."""
    # Wraps OfferExtractionService / BrandExtractionService
    # Emits preview_update per section

# focus/extract_from_url.py
@tool
def extract_from_url(url: str, target_sections: list[str] | None = None) -> str:
    """Scrape URL and extract data into entity."""
    # WebCrawler -> extract_from_document
```

### 5.5 Interview Config Dynamic by Archetype

```python
def get_offer_interview_config(offer: Offer) -> InterviewConfig:
    """Generate interview config adapted to the offer's archetype."""

    # Universal blocks (all offers)
    blocks = [
        InterviewBlock(id="strategy", label="Estrategia & Avatar", ...),
        InterviewBlock(id="promise", label="Promesa & Resultado", ...),
        InterviewBlock(id="psychology", label="Psicologia", ...),
    ]

    # Archetype-specific block
    ARCHETYPE_BLOCKS = {
        "producto": InterviewBlock(id="product_details", ...),
        "programa": InterviewBlock(id="program_details", ...),
        "servicio": InterviewBlock(id="service_details", ...),
        "membresia": InterviewBlock(id="subscription_details", ...),
        "experiencia": InterviewBlock(id="event_details", ...),
    }
    if offer.archetype in ARCHETYPE_BLOCKS:
        blocks.append(ARCHETYPE_BLOCKS[offer.archetype])

    # Universal final blocks
    blocks += [
        InterviewBlock(id="value_stack", label="Stack de Valor", ...),
        InterviewBlock(id="pricing", label="Precios", ...),
        InterviewBlock(id="closing", label="Cierre & Garantia", ...),
    ]

    return InterviewConfig(domain="offer", blocks=blocks, ...)
```

### 5.6 Interview Block Reversal

```python
# InterviewSession — new method
def revert_to_block(self, block_id: str) -> None:
    block_ids = [b.id for b in self.config_snapshot.blocks]
    if block_id not in block_ids:
        raise ValueError(f"Block {block_id} not found")
    target_idx = block_ids.index(block_id)
    self.bloques_completados = [
        b for b in self.bloques_completados
        if block_ids.index(b) < target_idx
    ]
    self.bloque_actual = block_id
```

### 5.7 extract_structured — Global Extraction

The tool extracts to ANY field in mapa_global, not just the current block's fields:

```python
@tool
def extract_structured(extractions: list[dict]) -> str:
    """Extract structured data from conversation into mapa_global.

    extractions: list of {field_path, value, confidence}
    field_path can be from ANY section, not just the current block.
    Always validate field_path against schema_introspection.
    """
```

### 5.8 Context Window Budget

```python
@dataclass
class ContextBudget:
    system_prompt: int = 5_000
    entity_snapshot: int = 5_000
    interview_context: int = 3_000
    history: int = 15_000
    tool_results_per_turn: int = 2_000
    reserved_response: int = 2_000

def truncate_history(messages: list, budget: int) -> list:
    """Keep last 3 turns complete, summarize older turns."""
```

### 5.9 Field Path Validation

```python
def validate_field_path(domain: str, field_path: str) -> bool:
    """Validate that field_path exists in the domain's schema."""
    sections = schema_introspection.get_model_sections(domain)
    # Verify field_path is valid
    # If invalid, return clear error to LLM
```

### 5.10 Interview Lifecycle Endpoints (unchanged)

```
POST /copilot/interview/start          -> creates InterviewSession
GET  /copilot/interview/active         -> detects active session
GET  /copilot/interview/{id}/state     -> state for resume
POST /copilot/interview/{id}/pause     -> pauses session
POST /copilot/interview/{id}/abandon   -> abandons session
POST /copilot/interview/{id}/documents -> processes files
POST /copilot/voice/transcribe         -> audio to text
```

## 6. Intelligence Rules (System Prompt)

These rules are injected into the system prompt and define how the copilot behaves:

```
FUNDAMENTAL COPILOT RULES:

1. GLOBAL CAPTURE: Every piece of data the user mentions, about ANY section,
   gets captured immediately with extract_structured. Never let information
   pass. The mapa_global is your memory.

2. NEVER REPEAT: Before asking something, check mapa_global for existing data.
   If you already have a datum, do not ask again. Briefly confirm what you
   know and ask ONLY for what's missing.

3. COVERAGE ADAPTATION: When entering a block, evaluate how much you already
   have. If >80%: confirm and advance quickly. If >0%: acknowledge what you
   have, ask for missing parts. If 0%: full interview questions.

4. BULK EXTRACTION: When the user uploads documents or URLs, extract against
   ALL sections simultaneously. Then adapt the interview to what was filled.

5. USER'S ORDER: The user can be messy. They may talk about pricing when
   you're on promise. They may send audio with info about 5 mixed sections.
   Your job is to understand, classify, capture, and lose nothing.

6. VISIBLE INTELLIGENCE: When you capture data for another section, confirm
   briefly: "I noted the program details you mentioned. We'll review them
   when we get there." Then return to the current topic.

7. FOCUS CONSTRAINT (Focus mode): Every response must relate to the focused
   entity. If user asks something unrelated, acknowledge briefly and redirect:
   "That's interesting, but right now we're focused on your offer. When we
   finish, I can help with that."
```

## 7. Migration Phases

### Phase 0: Foundations (no visible changes to user)

**Backend:**
- Add `focus` and `interview_session_id` to `ClientContextDTO`
- Critical fix: wire interview system prompt into `build_system_prompt()` (layered)
- Add field_path validation in `extract_structured` via `schema_introspection`
- Implement context budget with history truncation
- Make `extract_structured` global (not limited to current block)
- Add `revert_to_block` tool for interview
- Clean dead code: `brand_tools.py`, `offer_tools.py`, `research.py`

**Frontend:**
- Extend Zustand store with new shape (backward-compatible)
- Create `CopilotInput` unified component
- Refactor preview registry to lazy config

**Risk:** Low. Additive or internal refactor.

### Phase 1: Unified input + interview fix (first visible value)

**Frontend:**
- `CopilotChat` uses `CopilotInput`
- `useCopilotChat` absorbs `useInterviewChat` (mode-aware send)
- Interview messages go to Zustand store (not local useState)
- `AssistantMessage` renders interview cards

**Backend:**
- `/copilot/chat` receives `interview_session_id` in context
- Loads InterviewSession, injects into system prompt
- Tool selection scoped to interview

**Result:** User can send audio and files from sidebar. Interview works correctly.

**Risk:** Medium. Absorbing useInterviewChat requires careful card handling.

### Phase 2: Expandable sidebar + Focus Mode

**Frontend:**
- Layout with dynamic padding-right (60/380/780px)
- CopilotSidebar with expansion, CopilotPreviewPane
- FocusBar, FocusModeButton (replaces AutocompletarIAButton)
- CopilotStatusBar (replaces InterviewBanner)
- WithCopilot focus-mode aware

**Backend:**
- Focus tools: entity_write, entity_read, entity_undo_all, extract_from_document, extract_from_url
- Tool selection by context
- Snapshot loading at focus start

**Result:** User clicks "Focus", sidebar expands with preview, can converse focused on entity.

**Risk:** Medium-High. Layout changes affect all dashboard pages.

### Phase 3: Interview in sidebar + creation with IA

**Frontend:**
- CreateOfferWizard: add "Crear con asistente IA" button
- Interview starts from sidebar (no page navigation)
- FocusBar shows interview progress, "Volver a modo manual"
- Interview pages become thin redirectors
- CopilotStatusBar handles resume

**Backend:**
- Dynamic interview config by archetype
- startInterview accepts entity_id (connect the 3 missing wires)
- Intelligence rules in system prompt (global capture, coverage adaptation, no repetition)

**Result:** Full offer creation with IA flow. Smart interview that adapts.

**Risk:** Medium. Quality depends on prompt engineering.

### Phase 4: Cleanup + polish

**Frontend:**
- Delete: InterviewSplitView, InterviewChatPanel, InterviewInput, useInterviewChat, InterviewHeader, SmartFillDialog, AutocompletarIAButton, interview-banner
- Polish: animations, mobile, prefetch

**Backend:**
- Deprecate `/copilot/actions/brand/extract-full`, `/copilot/actions/offer/psychology`
- Rate limiting: 30 msgs/min per user

**Risk:** Low. Dead code removal and polish.

### Phase Parallelization

- Phase 0 frontend + Phase 0 backend: parallel
- Phase 1: depends on Phase 0
- Phase 2: depends on Phase 0 (can overlap with Phase 1 on layout work)
- Phase 3: depends on Phase 1 + Phase 2
- Phase 4: depends on Phase 3

### Multi-Agent Execution Strategy

Each phase can use parallel agents for independent workstreams:

**Phase 0:**
- Agent A (backend): DTO extension, system prompt layering, extract_structured fix, context budget
- Agent B (frontend): store redesign, CopilotInput, preview registry refactor

**Phase 1:**
- Agent A (backend): interview context loading in orchestrator, tool selection by mode
- Agent B (frontend): useCopilotChat absorption, CopilotInput integration, card unification

**Phase 2:**
- Agent A (backend): focus tools (entity_write/read/undo, extract_from_*)
- Agent B (frontend): layout expansion, CopilotSidebar, CopilotPreviewPane, FocusBar
- Agent C (frontend): WithCopilot adaptation, FocusModeButton, CopilotStatusBar

**Phase 3:**
- Agent A (backend): dynamic interview config, startInterview entity_id, intelligence rules
- Agent B (frontend): CreateOfferWizard modification, interview in sidebar, transitions

**Phase 4:**
- Single agent: cleanup and polish (sequential, low risk)

## 8. Testing Strategy

### Backend Tests (pytest, native)

| What | Where | Type |
|---|---|---|
| System prompt layers render correctly | `tests/modules/copilot/test_prompt_layers.py` | Unit |
| Tool selection by mode returns correct tools | `tests/modules/copilot/test_tool_selection.py` | Unit |
| extract_structured validates field_path | `tests/modules/copilot/test_extract_structured.py` | Unit |
| extract_structured captures cross-block data | `tests/modules/copilot/test_extract_structured.py` | Unit |
| Focus tools persist via persisters | `tests/modules/copilot/test_focus_tools.py` | Integration |
| entity_undo_all restores snapshot | `tests/modules/copilot/test_focus_tools.py` | Integration |
| Interview config dynamic by archetype | `tests/modules/copilot/test_interview_config.py` | Unit |
| revert_to_block works correctly | `tests/modules/copilot/test_interview_session.py` | Unit |
| Context budget truncates history | `tests/modules/copilot/test_context_budget.py` | Unit |
| FocusContextDTO serialization | `tests/modules/copilot/test_dto.py` | Unit |

### Frontend Tests (vitest, native)

| What | Where | Type |
|---|---|---|
| Store mode transitions | `features/copilot/__tests__/copilot-store.test.ts` | Unit |
| Store derived getMode() | `features/copilot/__tests__/copilot-store.test.ts` | Unit |
| CopilotInput renders mic/attachments by mode | `features/copilot/__tests__/copilot-input.test.tsx` | Component |
| Preview registry lazy loading | `features/copilot/__tests__/preview-registry.test.ts` | Unit |
| FocusBar renders correctly per mode | `features/copilot/__tests__/focus-bar.test.tsx` | Component |
| CopilotStatusBar shows resume for any domain | `features/copilot/__tests__/copilot-status-bar.test.tsx` | Component |
| FocusModeButton activates focus in store | `features/copilot/__tests__/focus-mode-button.test.tsx` | Component |

### Architecture Tests (backend, ratchet pattern)

| What | Enforcement |
|---|---|
| Focus tools must live in `copilot/application/tools/focus/` | File path pattern check |
| Interview tools must live in `copilot/application/tools/interview/` | File path pattern check |
| No cross-module imports except copilot | Existing test (KEPT) |

### E2E Tests (Playwright, native)

| What | Priority |
|---|---|
| Sidebar opens/closes/expands correctly | Smoke |
| Focus mode activates from offer editor | Smoke |
| Interview starts from CreateOfferWizard | Regression |
| Audio recording and transcription | Regression |
| File upload in focus mode | Regression |

## 9. Risks and Mitigations

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Layout regression on narrow screens | High | Medium | Auto-collapse left sidebar at <1280px; visual E2E tests |
| Interview quality depends on prompt engineering | High | Medium | Iterative prompt testing with real user data |
| Context window overflow in long focus sessions | High | Low | Context budget system (Phase 0) |
| Breaking existing chat functionality | Medium | Low | Focus/interview are additive — no changes when context fields absent |
| Mobile UX degradation | Medium | Low | Separate sheet rendering for <768px |
| Extraction services wrapper complexity | Medium | Medium | Thin wrapper pattern, delegate to existing services |
| Store migration breaks existing consumers | Medium | Low | Backward-compatible getters for isOpen, interviewMode |

## 10. Out of Scope

- Async migration of repositories (tech debt, separate effort)
- Full conflict resolution for concurrent entity edits (optimistic concurrency is sufficient)
- Conversation history across sessions (currently per-tab, acceptable for now)
- Custom model selection per mode (all modes use same AGENT model)
- Voice synthesis / TTS for copilot responses
- Drag-to-resize sidebar width (3 discrete states are sufficient)

## 11. Implementation Notes

### Gap & Discovery Document

At the end of implementation, produce a `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md` documenting:
- Every technical gap discovered during implementation (things the spec didn't anticipate)
- Every workaround applied and why
- Recommendations for future improvements
- Code quality observations and tech debt found along the way
- Prompt engineering learnings from testing the intelligence rules

### Continuous Improvement During Execution

This spec is the baseline, not a ceiling. During implementation of each phase/task:
- **Rethink each point** before coding — look for a better approach given what you learn as you read the actual code
- **Research when needed** — if a pattern feels wrong or there's a better library/approach, investigate before implementing
- **Leave the code better** — every file touched should be cleaner after than before (imports, types, naming, DDD/FSD compliance)
- **Follow all active rules** — ruff, eslint, arch fitness tests, TDD, tenant isolation, Spanish text accents
