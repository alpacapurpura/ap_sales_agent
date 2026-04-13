# Phase 3 Handoff: Interview in Sidebar + Offer Creation with IA

**Date:** 2026-04-13
**Previous Phase:** Phase 2 (Expandable Sidebar + Focus Mode) — COMPLETE
**Next Phase:** Phase 3 (Interview in Sidebar + Creation with IA)

---

## What Was Done in Phase 0 + Phase 1 + Phase 2

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
1. `FocusContextDTO` + `ClientContextDTO` extended with `focus` + `interview_session_id`
2. `CopilotOrchestrator._build_client_context()` passes focus/interview to state
3. `InterviewSession` loaded into state when `interview_session_id` present
4. `get_tools_for_context()` — mode-based tool selection (interview overrides route)
5. `UIAction` type extended with interview cards + `preview_update`
6. `entity_id` added to `StartInterviewRequest` DTO + endpoint
7. `useCopilotChat` unified: mode-aware send, `_handleUIAction` dispatcher, `sendCardAction`
8. `AssistantMessage` renders interview cards (alternatives, clarify, checkpoint, complete)
9. `useInterviewChat` deprecated to thin wrapper over `useCopilotChat`

### Phase 2 (12 commits):
1. `focus_entity_data: dict | None` added to `CopilotState`
2. `FocusContextLoader` — loads entity snapshot via `persister_registry`
3. Focus tools: `entity_write`, `entity_read`, `entity_undo_all` (LangChain `@tool`)
4. Tool registry: focus mode selection (focus + knowledge + domain, no mutation)
5. Orchestrator: loads `focus_entity_data` into state at focus start
6. Dashboard layout refactored: flex-based push (no more `padding-right` hacks)
7. `CopilotSidebar` replaces `CopilotPanel` — 3 width states (60/380/780px)
8. `CopilotHeader` — mode-aware indicator (Chat / Focus / Entrevista)
9. `CopilotPreviewPane` — lazy-loaded from preview registry (400px)
10. `FocusBar` — entity label, domain icon, progress dots, undo all, exit focus
11. `FocusModeButton` — entry point for editors to activate focus mode
12. `CopilotStatusBar` replaces `InterviewBanner` (no hardcoded routes)
13. Left sidebar auto-collapse at viewport <1280px

All tests green: 2355 backend, 1038 frontend, 62 arch.

---

## What Phase 3 Must Do

**Goal:** Make the interview run entirely inside the sidebar (no separate page needed). Add "Crear con asistente IA" to the offer wizard. Wire interview card callbacks. Make WithCopilot focus-aware.

### Frontend Tasks:

**F1: Wire AssistantMessage card callbacks (no-ops → real actions)**
- `AlternativesCard.onSelect` / `onCustom` → call `sendCardAction(messageId, actionIndex, selectedText)`
- `ClarifyCard.onResolve` → call `sendCardAction` with resolved clarifications
- `CheckpointCard.onConfirm` → call `sendCardAction` to trigger `advance_block`
- `CheckpointCard.onRevise` → call `sendCardAction` to trigger `revert_to_block`
- `InterviewCompleteCard` → already has redirect logic, verify it works with sidebar mode
- All cards must update `card_status` via `updateUIActionStatus(messageId, actionIndex, newStatus)`

Current state (all in `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`):
```
Line 92: onSelect={() => {}}     ← NO-OP
Line 93: onCustom={() => {}}     ← NO-OP
Line 106: onResolve={() => {}}   ← NO-OP
Line 119: onConfirm={() => {}}   ← NO-OP
Line 120: onRevise={() => {}}    ← NO-OP
```

The `sendCardAction` function already exists in `useCopilotChat` — it marks the card resolved and sends a message. The cards just need to call it.

**F2: CreateOfferWizard "Crear con asistente IA" button**
- Location: `frontend/src/features/offer-studio/components/` (find the wizard)
- Final step adds a second button: "Crear con asistente IA"
- Flow: create offer in DB → navigate to `/offer-studio/offer/{id}` → activate interview:
  - `setFocusEntity({ domain: "offer", entityId: id, label: name })`
  - Call `startInterview("offer", id)` → get sessionId
  - `setInterviewSession(sessionId)`
  - `setSidebarState("expanded")`
- Spec section 4.7 has the full flow

**F3: Interview pages become thin redirectors**
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx` — if session query param exists, redirect to brand-studio + activate interview in sidebar
- `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/interview/page.tsx` — same pattern
- Don't delete the pages yet — just add redirect logic for backward compatibility

**F4: WithCopilot focus-mode awareness**
- When `focusEntity` matches the field's domain, change behavior:
  - Fields modified by copilot show "AI" badge (already has copilot:field-update event)
  - In focus mode: field selection auto-sends to copilot context
  - Badge should persist until user manually edits the field
- File: `frontend/src/features/copilot/components/WithCopilot.tsx` (137 lines)

### Backend Tasks:

**B1: Dynamic interview config by archetype**
- Implement `get_offer_interview_config(offer)` per spec section 5.5
- Universal blocks: strategy, promise, psychology
- Archetype-specific: product_details / program_details / service_details / subscription_details / event_details
- Universal final: value_stack, pricing, closing
- Config generated when `startInterview("offer", entity_id)` is called
- File: `backend/src/modules/copilot/domain/interview_config.py`

**B2: Intelligence rules in system prompt**
- Update `copilot_interview.j2` template with the 7 intelligence rules from spec section 6
- Global capture, never repeat, coverage adaptation, bulk extraction, user's order, visible intelligence, focus constraint
- These are the behavioral rules that make the interview smart vs. robotic

**B3: Verify `startInterview` accepts and uses `entity_id`**
- Phase 1 added `entity_id` to `StartInterviewRequest` DTO
- Verify the interview service actually uses it to load existing entity data into `mapa_global`
- Verify the interview config is generated using entity data (archetype, existing fields)

---

## Critical Gaps to Watch

1. **Card callbacks are the #1 priority.** Without them, the interview cards are decorative. The user can't select alternatives, confirm checkpoints, or revise blocks. Everything else depends on this.

2. **Interview in sidebar vs. interview page.** Currently, `/brand-studio/interview` renders `InterviewSplitView` which has its own layout (preview + chat). With Phase 2's sidebar, the interview should run in the sidebar's preview + chat layout instead. The page should redirect.

3. **Interview resume flow.** `CopilotStatusBar` restores the interview state in the sidebar. Need to verify the conversation history is also loaded (the orchestrator loads it from Redis/DB).

4. **Preview data flow.** In interview mode, `extract_structured` returns `preview_update` ui_actions. These should update `previewData` in the store, which feeds `CopilotPreviewPane`. Verify this pipeline works end-to-end.

5. **Offer wizard integration.** The wizard creates an offer first, then starts the interview. The interview needs the offer's `entity_id` and archetype to generate the right config.

---

## Key Files to Read Before Starting

### Frontend (card callbacks):
- `frontend/src/features/copilot/components/messages/AssistantMessage.tsx` — where callbacks are no-ops
- `frontend/src/features/copilot/components/cards/` — AlternativesCard, ClarifyCard, CheckpointCard, InterviewCompleteCard
- `frontend/src/features/copilot/hooks/useCopilotChat.ts` — `sendCardAction` method

### Frontend (offer wizard):
- Find the CreateOfferWizard in `frontend/src/features/offer-studio/components/`
- `frontend/src/features/copilot/api/interview-api.ts` — `startInterview()`

### Frontend (interview pages):
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx`
- `frontend/src/features/copilot/components/interview/interview-split-view.tsx`

### Frontend (WithCopilot):
- `frontend/src/features/copilot/components/WithCopilot.tsx`
- `frontend/src/features/copilot/store/copilot-store.ts` — focusEntity, previewData

### Backend (interview config):
- `backend/src/modules/copilot/domain/interview_config.py`
- `backend/src/modules/copilot/application/services/interview_service.py`
- `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2`

### Design spec:
- `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` — Sections 4.7 (offer creation flow), 5.5 (dynamic config), 6 (intelligence rules)

---

## Files Still Pending Deprecation (Phase 4 — NOT Phase 3)

**DO NOT delete these in Phase 3.** They're still imported by interview pages and legacy flows.

### Copilot feature:
- `frontend/src/features/copilot/components/interview/interview-split-view.tsx`
- `frontend/src/features/copilot/components/interview/interview-chat-panel.tsx`
- `frontend/src/features/copilot/components/interview/interview-input.tsx`
- `frontend/src/features/copilot/components/interview/interview-header.tsx`
- `frontend/src/features/copilot/components/interview/interview-message.tsx`
- `frontend/src/features/copilot/components/interview/session-restore-modal.tsx`
- `frontend/src/features/copilot/hooks/useInterviewChat.ts` (deprecated wrapper, 155 lines)
- `frontend/src/features/copilot/components/CopilotPanel.tsx` (old fixed panel, still imported by MetricSidebar + design registry)

### Brand feature:
- `frontend/src/features/brand/components/interview/interview-split-view.tsx`
- `frontend/src/features/brand/components/interview/session-restore-modal.tsx`
- `frontend/src/features/brand/components/interview/interview-header.tsx`
- `frontend/src/features/brand/components/interview/register-brand-preview.ts`

### Offer Studio:
- `frontend/src/features/offer-studio/components/interview/register-offer-preview.tsx`
- `frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx`

### Shared:
- `frontend/src/components/shared/interview-banner.tsx` (replaced by CopilotStatusBar)

---

## Execution Strategy

1. **Start with F1 (card callbacks)** — unblocks all interview interactions
2. **Then B1 + B2** — dynamic config + intelligence rules (backend, independent)
3. **Then F2** — CreateOfferWizard integration
4. **Then F3** — interview page redirectors
5. **F4 last** — WithCopilot focus-mode (polish, not critical path)
6. **Full test suite** at the end
7. **Manual QA** — test the full offer creation + interview flow

## Quality Standards

Same as Phase 2: TDD, ruff, ESLint, no `any`, DDD, FSD, tildes, stage by name, conventional commits.

## Start Command

```
lee docs/superpowers/specs/2026-04-13-unified-copilot-design.md (secciones 4.7, 5.5, 6) y docs/superpowers/specs/2026-04-13-phase3-handoff.md, luego crea el plan detallado para Phase 3 y ejecútalo con subagent-driven-development
```
