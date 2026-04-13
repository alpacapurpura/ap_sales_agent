# Phase 1 Handoff: Unified Input + Interview Fix

**Date:** 2026-04-13
**Previous Phase:** Phase 0 (Foundations) — COMPLETE
**Next Phase:** Phase 1 (Unified Input + Interview Fix)

---

## What Was Done in Phase 0

8 commits on `development` branch. All tests green (2304 backend, 127 frontend copilot, 62 arch).

### Backend changes:
1. **`state.py`** — Added `FocusContext` TypedDict + extended `ClientContext` with `focus` and `interview_session_id` fields
2. **`graph.py`** — `build_system_prompt()` now composes 3 layers: base + focus (copilot_focus.j2) + interview (copilot_interview.j2). Helpers: `_build_focus_layer()`, `_build_interview_layer()`
3. **`schema_introspection.py`** — Added `validate_field_path(domain, field_path)` with lazy domain model discovery
4. **`extract_structured.py`** — Added `domain` parameter, field_path validation, skipped_fields reporting, updated docstring for global cross-block extraction
5. **`context_budget.py`** — NEW. `truncate_history()` preserves last 3 turns, summarizes older messages. Integrated into `agent_node` in graph.py
6. **`interview_session.py`** — Added `revert_to_block(block_id)` domain method
7. **`revert_to_block.py`** — NEW LangChain tool registered in INTERVIEW_TOOLS
8. **Dead code** — Deleted `brand_tools.py`, `offer_tools.py` (unused). Kept `research.py` (used by style_analyzer)

### Frontend changes:
1. **`copilot-store.ts`** — Extended with `sidebarState` (collapsed/open/expanded), `focusEntity`, `focusSnapshot`, `previewData`, `interviewProgress`. All backward-compatible (`isOpen`, `interviewMode`, `updateInterviewPreview` still work as derived/aliases)
2. **`copilot-input.tsx`** — NEW unified input component with textarea + mic (useVoiceRecorder) + attachments (AttachmentButton + DocumentChip). Not yet integrated into CopilotChat
3. **`interview-preview-registry.ts`** — Refactored to lazy imports. `getPreviewEntry(domain)` returns lazy loaders. `registerPreview()` is now no-op (backward compat). `getSupportedDomains()` added
4. **`types/index.ts`** — Re-exports `FocusEntity`, `InterviewProgress`, `SidebarState` from store

### Documentation:
- `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` — Full design spec (10 sections)
- `docs/superpowers/plans/2026-04-13-unified-copilot-phase0.md` — Phase 0 plan (executed)
- `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md` — Gap analysis with 7 discoveries

---

## What Phase 1 Must Do

**Goal:** First visible value to users. The copilot sidebar gets audio + file upload. The interview actually works correctly (system prompt + tools properly scoped).

### Frontend Tasks:

**F1: CopilotChat uses CopilotInput**
- Replace the inline textarea in `CopilotChat.tsx` (lines ~135-172) with `<CopilotInput />`
- CopilotInput is already created — just import and wire `onSend` to `sendMessage`
- Keep ContextChips, SuggestedActions, ProcedureProgress around the input (they're above it, not inside)
- Visual parity with current behavior + new mic/attachment buttons

**F2: useCopilotChat absorbs useInterviewChat**
- `useCopilotChat` becomes the SINGLE send function for all modes
- When `store.interviewSessionId` is set, include `interview_session_id` in the chat context payload (sent to same `/copilot/chat` endpoint)
- Remove the `streamInterviewMessage` function (it calls a non-existent endpoint)
- All messages go to Zustand store (interview used local useState — that changes)
- Handle `preview_update` SSE events: silent (not shown as messages), update `store.previewData`
- Handle interview card UIActions: `alternatives_card`, `clarify_card`, `checkpoint_card`, `interview_complete`

**F3: AssistantMessage renders interview cards**
- Currently `AssistantMessage` only renders generic cards (navigate, proposal, metric, etc.)
- Add rendering of interview-specific cards (alternatives, clarify, checkpoint, complete)
- Import card components from `copilot/components/cards/`
- The unified `CopilotMessage` type already has `uiActions` — interview actions go there too

**F4: useInterviewChat becomes thin wrapper (deprecated)**
- After F2, `useInterviewChat` is no longer needed
- Keep it as a thin wrapper that delegates to `useCopilotChat` for backward compat
- The `InterviewSplitView` still uses it until Phase 3 replaces it

### Backend Tasks:

**B1: Orchestrator loads interview context**
- In `CopilotOrchestrator.stream_chat()` (or `chat.py` endpoint): when `context.interview_session_id` is present, load the `InterviewSession` from the repository and inject into `CopilotState` as `interview_session`
- This makes the `_build_interview_layer()` from Phase 0 actually fire (it checks `state.get("interview_session")`)

**B2: Tool selection by mode**
- Modify `get_tools_for_route()` in `registry.py` to check for `interview_session_id` and `focus` in client_context
- When interview: return `INTERVIEW_TOOLS + KNOWLEDGE_TOOLS` (ignore route)
- When focus: return `FOCUS_TOOLS + KNOWLEDGE_TOOLS + route_tools` (focus tools don't exist yet in Phase 1 — just prepare the plumbing)
- When neither: current behavior (route-based)

**B3: StartInterviewRequest accepts entity_id**
- The `interview.py` endpoint `POST /start` needs to accept `entity_id` in the request body
- Pass it to `InterviewService.start_interview()` which already accepts it
- This connects the "3 missing wires" between frontend and backend for offer interview

---

## Critical Gaps to Watch (from Phase 0 analysis)

1. **SSE event handling differs**: `useInterviewChat` parses `preview_update` as silent (no message), while `useCopilotChat` attaches all UIActions to the last assistant message. The merged hook needs to handle `preview_update` specially — update `previewData` in store, DON'T show as a card.

2. **Interview messages were in local useState**: Moving them to Zustand store means the `InterviewSplitView` (still alive until Phase 3) needs to read from the store instead of receiving props. Or keep the wrapper passing store data as props.

3. **PromptLoader is CWD-dependent**: Tests must run from `cd backend/`. The `copilot_focus.j2` and `copilot_interview.j2` templates won't render if CWD is wrong.

4. **Parallel agent git conflicts**: Task 4 and Task 6 had overlap in Phase 0. For Phase 1, ensure backend tasks touch separate files or serialize them.

---

## Key Files to Read Before Starting

### Backend (read these first):
- `backend/src/modules/copilot/application/orchestrator/graph.py` — build_system_prompt (layered), agent_node (truncate_history integrated)
- `backend/src/modules/copilot/application/orchestrator/state.py` — CopilotState, ClientContext, FocusContext
- `backend/src/modules/copilot/application/orchestrator/chat.py` — CopilotOrchestrator.stream_chat()
- `backend/src/modules/copilot/application/tools/registry.py` — TOOL_GROUPS, ROUTE_TOOL_MAP, get_tools_for_route()
- `backend/src/modules/copilot/api/interview.py` — interview lifecycle endpoints
- `backend/src/modules/copilot/api/dto/interview_dto.py` — StartInterviewRequest DTO
- `backend/src/modules/copilot/application/services/interview_service.py` — start_interview()

### Frontend (read these first):
- `frontend/src/features/copilot/hooks/useCopilotChat.ts` — current SSE streaming logic
- `frontend/src/features/copilot/hooks/useInterviewChat.ts` — interview SSE + local state + card handling
- `frontend/src/features/copilot/components/CopilotChat.tsx` — current textarea that gets replaced
- `frontend/src/features/copilot/components/copilot-input.tsx` — the NEW unified input (Phase 0)
- `frontend/src/features/copilot/store/copilot-store.ts` — extended store (Phase 0)
- `frontend/src/features/copilot/components/messages/AssistantMessage.tsx` — where cards render
- `frontend/src/features/copilot/components/cards/` — interview card components
- `frontend/src/features/copilot/api/copilot-api.ts` — streamCopilotChat function

### Design spec:
- `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` — Sections 4 (Frontend), 5 (Backend), 6 (Intelligence Rules), 7 (Migration Phase 1)

---

## Execution Strategy

Same as Phase 0:
1. **Read the spec** (Section 7, Phase 1) and the gap analysis
2. **Use brainstorming skill** to rethink each task before coding — research better approaches if needed
3. **Write the detailed plan** with writing-plans skill (TDD, exact file paths, exact code)
4. **Execute with subagent-driven-development** — parallel agents for independent tasks, spec review + code quality review after each
5. **Multi-agent**: Backend (B1-B3) and Frontend (F1-F4) can run in parallel since they touch different files
6. **Full test suite** at the end: ruff, pytest, tsc, eslint, vitest, arch tests
7. **Gap document** at the end with discoveries

## Quality Standards (non-negotiable)

- TDD: tests first, implementation after
- Ruff: all rules active, no suppressions
- ESLint: strict mode, no `any` types
- DDD: domain layer has no framework imports, proper layer boundaries
- FSD: features don't cross-import, types in types/, components in components/
- Spanish accents: tildes correctas en todo texto visible
- Git: stage by name only, never `git add .`, conventional commits
- Parallel safety: never `git add -A`, report untracked files from other sessions

## Start Command

```
lee docs/superpowers/specs/2026-04-13-unified-copilot-design.md (sección 7, Phase 1) y docs/superpowers/specs/2026-04-13-phase1-handoff.md, luego crea el plan detallado para Phase 1 y ejecútalo con subagent-driven-development. Usa brainstorming antes de cada decisión arquitectónica compleja. Sé exigente con la calidad: TDD, multi-agente, revisión de código, investigación de mejores prácticas.
```
