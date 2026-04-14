---
name: Unified Copilot Refactoring — Phase 1 Complete
description: Major copilot unification project. Phases 0+1 done 2026-04-13. Phase 2 next (expandable sidebar + focus mode).
type: project
---

Unified Copilot refactoring — unifying 4 fragmented AI systems (sidebar chat, interview engine, SmartFill, WithCopilot) into ONE copilot with context-aware behavior.

**Why:** 4 disconnected systems doing variations of the same thing. Interview was broken (missing endpoint + system prompt not wired). Audio/files only in interview (which was broken). 3 parallel extraction pipelines.

**How to apply:**
- Design spec: `docs/superpowers/specs/2026-04-13-unified-copilot-design.md`
- Gap analysis: `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md`

**Phase 0 (COMPLETE, 2026-04-13):**
- 8 commits, 13 tasks. Backend: layered system prompt, field validation, context budget, revert_to_block. Frontend: Zustand store extended, CopilotInput, lazy preview registry.

**Phase 1 (COMPLETE, 2026-04-13):**
- 10 commits, 10 tasks, all tests green (2324 backend, 1015 frontend, 62 arch)
- Backend: FocusContextDTO + ClientContextDTO extended, orchestrator loads InterviewSession, mode-based tool selection (get_tools_for_context), entity_id in StartInterviewRequest
- Frontend: UIAction extended with interview card types, CopilotChat uses CopilotInput (audio+files in sidebar), useCopilotChat unified (mode-aware, handles preview_update silently, sendCardAction), AssistantMessage renders interview cards, useInterviewChat deprecated to thin wrapper
- Plan: `docs/superpowers/plans/2026-04-13-unified-copilot-phase1.md`
- Known limitations: card callbacks are no-ops (wired in Phase 2/3), deprecated wrapper doesn't update card status

**Phase 2 (NEXT — expandable sidebar + focus mode):**
- Frontend: layout push (60/380/780px), CopilotSidebar, CopilotPreviewPane, FocusBar, FocusModeButton, CopilotStatusBar, WithCopilot focus-aware
- Backend: focus tools (entity_write/read/undo_all, extract_from_document/url), focus context loader, snapshot at focus start
- Handoff: `docs/superpowers/specs/2026-04-13-phase2-handoff.md`

**Phases 3-4:** Interview in sidebar + creation with IA, cleanup (specs written, not yet planned)
