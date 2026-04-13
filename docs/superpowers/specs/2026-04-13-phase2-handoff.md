# Phase 2 Handoff: Expandable Sidebar + Focus Mode

**Date:** 2026-04-13
**Previous Phase:** Phase 1 (Unified Input + Interview Fix) — COMPLETE
**Next Phase:** Phase 2 (Expandable Sidebar + Focus Mode)

---

## What Was Done in Phase 0 + Phase 1

### Phase 0 (8 commits):
1. `ClientContext` TypedDict extended with `focus` + `interview_session_id`
2. Layered system prompt: `build_system_prompt()` composes base + focus (`copilot_focus.j2`) + interview (`copilot_interview.j2`)
3. `extract_structured` global (cross-block extraction) + field_path validation via `schema_introspection`
4. Context budget with `truncate_history()` — integrated into `agent_node`
5. `revert_to_block` tool + domain method on `InterviewSession`
6. Zustand store extended: `sidebarState`, `focusEntity`, `focusSnapshot`, `previewData`, `interviewProgress`
7. `CopilotInput` unified component (textarea + mic + attachments)
8. Preview registry refactored to lazy imports

### Phase 1 (10 commits):
1. `FocusContextDTO` Pydantic model + `ClientContextDTO` extended with `focus` + `interview_session_id`
2. `CopilotOrchestrator._build_client_context()` — passes focus/interview to state
3. `InterviewSession` loaded into state when `interview_session_id` present
4. `get_tools_for_context()` — mode-based tool selection (interview overrides route)
5. `agent_node` + `tool_executor_node` use `get_tools_for_context()` instead of route-only
6. `entity_id` added to `StartInterviewRequest` DTO + endpoint (connects offer to interview)
7. `UIAction` type extended with `alternatives_card`, `clarify_card`, `checkpoint_card`, `interview_complete`, `preview_update`
8. `updateUIActionStatus(messageId, actionIndex, status)` added to Zustand store
9. `CopilotChatPayload.context` extended with `focus` + `interview_session_id`
10. `startInterview()` frontend API accepts `entityId`
11. `CopilotChat` uses `CopilotInput` (audio + files in sidebar)
12. `useCopilotChat` unified: mode-aware send, `_handleUIAction` dispatcher, `sendCardAction`
13. `AssistantMessage` renders interview cards (alternatives, clarify, checkpoint, complete)
14. `useInterviewChat` deprecated to thin wrapper over `useCopilotChat`

All tests green: 2324 backend, 1015 frontend, 62 arch.

---

## What Phase 2 Must Do

**Goal:** Expandable sidebar with preview pane + Focus Mode. User clicks "Focus" on an offer/brand, sidebar expands to 780px with preview + chat side-by-side. Focus tools enable AI-driven entity editing with auto-save and undo.

### Frontend Tasks:

**F1: Layout with dynamic padding-right**
- Dashboard layout needs `padding-right` that adjusts based on `sidebarState`:
  - `collapsed` → 60px (rail)
  - `open` → 380px (chat)
  - `expanded` → 780px (preview + chat)
- Push layout, not overlay
- Viewport <1280px: left sidebar auto-collapses to 80px rail
- Currently the sidebar is likely a fixed-position panel — needs to become a push layout

**F2: CopilotSidebar replaces CopilotPanel**
- New component with 3 width states (60/380/780px)
- Contains: CopilotSidebarRail (collapsed), CopilotSidebarPanel (open/expanded)
- CopilotSidebarPanel has: CopilotHeader, FocusBar (focus/interview only), CopilotPreviewPane (expanded only), CopilotConversation, CopilotInput
- Spec Section 4.1 has the full component tree

**F3: CopilotPreviewPane**
- 400px left column when expanded
- Loads preview components lazily from `preview-registry.ts` by domain
- Shows preview summary + sections
- Clicking a section sends a message to chat

**F4: FocusBar**
- Shown only in focus/interview mode
- Entity label + domain icon
- "Salir de Focus" button → `clearFocus()`, `setSidebarState("open")`
- Progress dots (interview only)
- "Deshacer todo" button (restores snapshot)

**F5: FocusModeButton (replaces AutocompletarIAButton)**
- Placed in offer editor header, brand studio header
- Clicking activates focus: `setFocusEntity()`, `setSidebarState("expanded")`

**F6: CopilotStatusBar (replaces InterviewBanner)**
- Shows when interview is paused or focus is available
- "Continuar" button restores paused focus/interview
- NOT hardcoded to `/brand-studio/interview` (current bug)

**F7: WithCopilot focus-mode aware**
- When focus entity matches the field's domain, behavior changes
- Fields modified by copilot show "AI" badge

### Backend Tasks:

**B1: Focus tools**
- `focus/entity_write.py` — modify entity field, auto-save via persister
- `focus/entity_read.py` — read entity state (or specific section)
- `focus/entity_undo_all.py` — restore snapshot saved at focus start
- `focus/extract_from_document.py` — extract from uploaded doc into entity
- `focus/extract_from_url.py` — web scrape + extract into entity

**B2: Focus context loader**
- `infrastructure/context/focus_context_loader.py` — loads entity snapshot at focus start
- Registered in `context_loader_registry.py`

**B3: Tool selection for focus mode**
- In `get_tools_for_context()`, when `focus` present (no interview):
  - Return `FOCUS_TOOLS + KNOWLEDGE_TOOLS + route_tools`
  - Exclude `mutation` tools (focus tools replace them)

**B4: Snapshot loading at focus start**
- When focus context is present in orchestrator, load entity data
- Store as `focus_entity_data` in state (for `_build_focus_layer`)
- This makes the Phase 0 `copilot_focus.j2` template actually render

---

## Critical Gaps to Watch

1. **Layout changes affect ALL pages.** The sidebar push-layout needs testing on every dashboard route. Mobile breakpoint (<768px) needs full-screen overlay mode.

2. **Focus tools need persisters.** `entity_write` uses `persister_registry.py` (BrandPersister, OfferPersister). They exist but may need extension for new fields.

3. **Snapshot mechanism.** At focus start, the full entity state is saved. `entity_undo_all` restores it. Need to decide: store snapshot in DB or just in Zustand? Zustand is simpler but lost on page refresh.

4. **No-op card callbacks from Phase 1.** AssistantMessage renders interview cards but `onSelect`/`onConfirm` are no-ops. Phase 2 should wire these to `sendCardAction` — or defer to Phase 3.

5. **Preview registry completeness.** The registry has `brand`, `offer`, `buyer_persona` entries. The preview components they reference must actually exist and render correctly with focus entity data.

---

## Key Files to Read Before Starting

### Frontend (layout and sidebar):
- `frontend/src/app/(main)/layout.tsx` — current dashboard layout (where sidebar lives)
- `frontend/src/components/shared/sidebar.tsx` or equivalent — current left sidebar
- `frontend/src/features/copilot/components/CopilotPanel.tsx` or `CopilotChat.tsx` — current sidebar panel
- `frontend/src/features/copilot/store/copilot-store.ts` — sidebarState, focusEntity, focusSnapshot
- `frontend/src/features/copilot/config/interview-preview-registry.ts` — lazy preview loaders

### Frontend (focus entry points):
- `frontend/src/features/offer-studio/` — offer editor where "Focus" button goes
- `frontend/src/features/brand/` — brand studio where "Focus" button goes
- `frontend/src/components/shared/interview-banner.tsx` — replaced by CopilotStatusBar

### Backend (focus tools):
- `backend/src/modules/copilot/application/tools/` — existing tool structure
- `backend/src/modules/copilot/infrastructure/persisters/` — BrandPersister, OfferPersister, persister_registry
- `backend/src/modules/copilot/infrastructure/context/` — context loader registry
- `backend/src/modules/copilot/domain/schema_introspection.py` — field validation

### Design spec:
- `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` — Sections 3.2 (sidebar widths), 4.1-4.7 (frontend architecture), 5.4 (focus tools)

---

## Execution Strategy

1. **Brainstorm** the layout approach (push vs overlay, CSS strategy, responsive breakpoints)
2. **Read all key files** — especially the current layout and sidebar structure
3. **Write the detailed plan** with writing-plans skill
4. **Execute with subagent-driven-development** — parallel agents for independent tasks
5. **Multi-agent split:** Backend (B1-B4) and Frontend (F1-F7) are independent streams
6. **Full test suite** at the end
7. **Gap document** with discoveries

## Quality Standards

Same as Phase 1: TDD, ruff, ESLint, no `any`, DDD, FSD, tildes, stage by name, conventional commits.

## Start Command

```
lee docs/superpowers/specs/2026-04-13-unified-copilot-design.md (secciones 3.2, 4.1-4.7, 5.4) y docs/superpowers/specs/2026-04-13-phase2-handoff.md, luego crea el plan detallado para Phase 2 y ejecútalo con subagent-driven-development. Usa brainstorming antes de cada decisión arquitectónica compleja (especialmente layout push). Sé exigente con la calidad.
```
