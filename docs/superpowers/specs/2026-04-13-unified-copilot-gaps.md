# Unified Copilot — Phase 0 Gap Analysis & Recommendations

**Date:** 2026-04-13
**Phase:** 0 (Foundations)
**Status:** Complete

---

## Discoveries During Implementation

### 1. research.py is NOT dead code
**Expected:** `research.py` was listed for deletion as a mock.
**Found:** It's actively imported by `nodes_research.py` in the style analyzer agent (`copilot/application/agents/style_analyzer/`).
**Action:** Kept the file. Updated plan to not delete it.

### 2. PromptLoader path is CWD-dependent
**Found:** `PromptLoader` initializes with `templates_dir="src/modules/copilot/infrastructure/prompts/templates"` and resolves against `Path.cwd()`. Tests MUST run from `cd backend/` — running from repo root breaks template resolution.
**Risk for Phase 1+:** When integrating focus/interview context loading into the orchestrator, tests that mock the PromptLoader need to be CWD-aware.
**Recommendation:** No action needed now, but if we ever refactor PromptLoader, use `Path(__file__).parent` instead of `Path.cwd()`.

### 3. extract_structured already had no block restriction
**Expected:** Code change needed to make extraction cross-block.
**Found:** The tool never had block-level restrictions — the limitation was only in the LLM's interpretation of the docstring. The fix was purely a docstring update + validation addition (Task 3).
**Implication:** The intelligence rules in the system prompt (Phase 3) are MORE important than code changes for controlling LLM behavior.

### 4. Zustand store backward compatibility required careful design
**Found:** Many consumers use `isOpen` boolean directly. Replacing with `sidebarState` required keeping `isOpen` as a derived sync field (not a getter). Zustand doesn't support getters in the traditional sense — the approach was to sync `isOpen` in every action that changes `sidebarState`.
**Risk for Phase 1:** Consumers that call `togglePanel()` from expanded state go to collapsed (not open). This is correct behavior but should be documented.

### 5. CopilotInput voice recorder needs Clerk auth
**Found:** `useVoiceRecorder` calls `transcribeAudio(blob, token)` which needs a Clerk token. The CopilotInput component doesn't directly import `useAuth` — the voice recorder hook handles auth internally.
**Risk for Phase 1:** When integrating CopilotInput into CopilotChat, verify that Clerk context is available.

### 6. Preview registry lazy imports can't be validated at compile time
**Found:** The lazy import paths (`() => import("@/features/brand/...")`) are strings that TypeScript doesn't validate at compile time. If a preview component is renamed or moved, the error only surfaces at runtime when the preview loads.
**Recommendation:** Add a CI check or integration test that calls each lazy loader to verify the imports resolve. Consider adding this to architecture tests.

### 7. Parallel agent git conflicts
**Found:** Task 4 and Task 6 both committed changes simultaneously. Task 6's files were included in Task 4's commit (`ad4cb1ce`). This is a known risk of parallel agents on the same branch.
**Mitigation applied:** The later agent detected the overlap and reported correctly.
**Recommendation for Phase 1+:** When dispatching parallel backend agents, ensure they touch completely separate files. If overlap is possible, serialize those tasks.

---

## Tech Debt Found (existing, not introduced)

### 1. Sync repositories in async context
All copilot repositories (`ConversationRepository`, `InterviewSessionRepository`, `CopilotEventRepository`) and persisters use sync `Session`. The LangGraph graph runs async via `astream_events`. Each tool call with DB access blocks the event loop.
**Impact:** Low at current scale, problematic at 50+ concurrent sessions.
**Recommendation:** Defer to Phase 4 (async migration).

### 2. PydanticDeprecatedSince20 warning
`backend/src/core/config.py:8` uses class-based `config` instead of `ConfigDict`. This triggers a deprecation warning on every test run.
**Recommendation:** Fix when touching config.py for any reason.

### 3. InterviewSession.config_snapshot is a raw dict
The `config_snapshot` is stored as `dict` not as an `InterviewConfig` dataclass. This means accessing blocks requires `config["bloques"]` with string keys. Easy to typo.
**Recommendation:** Consider deserializing to `InterviewConfig` on load. Not blocking for Phase 1.

---

## Recommendations for Phase 1

### Priority order
1. **useCopilotChat absorption** — this is the most complex Phase 1 task. The hook needs to handle both chat and interview streaming, route to the correct endpoint based on mode, and write all messages to the Zustand store (not local useState).
2. **CopilotChat using CopilotInput** — straightforward replacement, but test visually.
3. **AssistantMessage card rendering** — needs to render interview cards (alternatives, checkpoint, etc.) in addition to existing generic cards.
4. **Backend interview context loading** — the orchestrator needs to load InterviewSession when `interview_session_id` is in context and inject it into state.

### Key risks for Phase 1
- The SSE streaming in `useInterviewChat` has a different event parsing flow than `useCopilotChat`. Merging them requires careful handling of `preview_update` events (silent, not displayed as messages) vs `ui_action` events (displayed as cards).
- The `streamInterviewMessage` function in `useInterviewChat` calls a non-existent endpoint. When absorbing, this code path should be removed entirely — all traffic goes through `/copilot/chat` with `interview_session_id` in context.

### Prompt templates to create for Phase 1
- `copilot_focus.j2` and `copilot_interview.j2` are created but won't be rendered until the orchestrator loads focus/interview context into state. Phase 1 backend work needs to add context loading to `CopilotOrchestrator.stream_chat()`.

---

## Metrics

| Metric | Value |
|---|---|
| Tasks completed | 13/13 |
| Backend tests passing | 2304 |
| Frontend tests passing (copilot) | 127 |
| Architecture tests passing | 62 |
| Commits | 8 |
| Files created | 8 |
| Files modified | 9 |
| Files deleted | 2 |
| Lint violations introduced | 0 |
| Type errors introduced | 0 |
