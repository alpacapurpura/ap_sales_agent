# Phase 5: Copilot Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan. Tasks are organized in WAVES — all tasks within a wave touch non-overlapping files and CAN be dispatched in parallel using superpowers:dispatching-parallel-agents. Waves must execute sequentially.

**Goal:** Resolve all 29 audit findings from `docs/superpowers/specs/2026-04-13-copilot-audit-improvements.md` — security, performance, reliability, testing, and polish. This is the FINAL phase of the copilot refactoring.

**Architecture:** Items that touch the same file are merged into single tasks. Tasks within each wave touch disjoint files, enabling parallel agent dispatch. Each agent investigates the current code, determines the best solution, implements, tests, and commits.

**Audit reference:** `docs/superpowers/specs/2026-04-13-copilot-audit-improvements.md`

**Previous phases:** Phases 0-4 documented in `docs/superpowers/specs/2026-04-13-phase4-handoff.md`

---

## Wave Structure (7 waves, 25 tasks)

```
Wave 1: Backend Critical Security     [Tasks 1-5]  — parallel, 5 agents
Wave 2: Backend Quality               [Tasks 6-9]  — parallel, 4 agents
Wave 3: Frontend Performance Core     [Tasks 10-13] — parallel, 4 agents
Wave 4: Frontend Components           [Tasks 14-18] — parallel, 5 agents
Wave 5: Frontend Polish               [Tasks 19-20] — parallel, 2 agents
Wave 6: Testing                       [Tasks 21-24] — parallel, 4 agents
Wave 7: Full Verification             [Task 25]     — single agent
```

### Audit Item → Task Mapping

| Audit | Task | Wave |
|-------|------|------|
| C1 (LLM timeout) | Task 1 | 1 |
| C3 + D2 (focus tools session + DI) | Task 2 | 1 |
| C4 + R5 (interview race + expiry) | Task 3 | 1 |
| S1 (rate limiting) | Task 4 | 1 |
| C2 + S3 (ownership + PII retention) | Task 5 | 1 |
| P5 (N+1 queries) | Task 6 | 2 |
| P6 + D1 (token estimation + domain boundary) | Task 7 | 2 |
| S2 (prompt injection) | Task 8 | 2 |
| D3 (async/sync) | Task 9 | 2 |
| P1 (Zustand selectors) | Task 10 | 3 |
| P2 (message limits) | Task 11 | 3 |
| R1 (SSE reconnection) | Task 12 | 3 |
| R2 + D4-partial (send race + hook split) | Task 13 | 3 |
| P3 + UX4 (virtualization + typing indicator) | Task 14 | 4 |
| P4 + UX5 + D4-partial (memo + card transitions + split) | Task 15 | 4 |
| R3 + UX3 (fresh entity + prefetch) | Task 16 | 4 |
| R4 + UX6 (focus exit + micro-interactions) | Task 17 | 4 |
| R6 (DOM timing) | Task 18 | 4 |
| UX1 + UX2 (sidebar animations + mobile) | Task 19 | 5 |
| D4-partial (CopilotInput split) | Task 20 | 5 |
| T8 (E2E infrastructure) | Task 21 | 6 |
| T1 (E2E smoke tests) | Task 22 | 6 |
| T2-T4 (frontend unit tests) | Task 23 | 6 |
| T5-T7 (backend tests) | Task 24 | 6 |
| Full verification | Task 25 | 7 |

---

## Wave 1: Backend Critical Security

> All 5 tasks touch completely different files. Dispatch all 5 in parallel.

### Task 1: LLM Streaming Timeout [C1]

**Audit item:** C1 — Sin timeout en streaming LLM
**Files:**
- Modify: `backend/src/modules/copilot/application/orchestrator/chat.py`
- Modify: `backend/src/modules/copilot/application/orchestrator/graph.py`

**Problem:** `copilot_graph.astream_events()` has no timeout. If the LLM hangs, the SSE stream hangs indefinitely, consuming server resources and blocking the user.

**Goal:** Add timeout handling to the LLM streaming call. When timeout triggers, yield an SSE error event to the frontend so the user sees a clear message instead of an infinite spinner.

- [ ] Read `chat.py` and `graph.py` to understand the current streaming flow
- [ ] Investigate: what's the best pattern for timeout with `astream_events()`? Options: `asyncio.wait_for()`, LangGraph timeout config, or manual timer
- [ ] Implement timeout (60s default, configurable via env var)
- [ ] Ensure partial responses are preserved — if LLM sent 80% of response before timeout, that text should still be visible
- [ ] Add SSE error event: `data: {"type": "error", "message": "Timeout..."}\n\n`
- [ ] Add test: `backend/tests/modules/copilot/test_streaming_timeout.py`
- [ ] Run: `cd backend && .venv/bin/ruff check src/modules/copilot/ --no-cache`
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): add 60s timeout to LLM streaming with SSE error event`

---

### Task 2: Focus Tools Session Safety [C3 + D2]

**Audit items:** C3 (session leak), D2 (SessionLocal direct use)
**Files:**
- Modify: `backend/src/modules/copilot/application/tools/focus/entity_write.py`
- Modify: `backend/src/modules/copilot/application/tools/focus/entity_read.py`
- Modify: `backend/src/modules/copilot/application/tools/focus/entity_undo_all.py`
- Maybe: `backend/src/modules/copilot/application/tools/focus/__init__.py`

**Problem:** All focus tools create `db = SessionLocal()` but if `UUID(entity_id)` or `get_persister()` throws BEFORE the try-finally block, `db.close()` never executes. Over many concurrent requests → connection pool exhaustion.

**Goal:** Ensure DB sessions are ALWAYS properly closed, regardless of where exceptions occur. Use context manager pattern.

- [ ] Read all 3 focus tool files to understand the current pattern
- [ ] Investigate: can we use `contextmanager` wrapper or `with SessionLocal() as db:` pattern?
- [ ] Refactor all 3 tools to use safe session management (context manager or try-finally that covers ALL code paths)
- [ ] Move UUID parsing validation BEFORE session creation (fail fast)
- [ ] Add test: `backend/tests/modules/copilot/test_focus_session_safety.py` — test that session closes even on UUID parse error, persister error
- [ ] Run: `cd backend && .venv/bin/ruff check src/modules/copilot/application/tools/focus/ --no-cache`
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): fix session leak in focus tools — use context manager pattern`

---

### Task 3: Interview Service Hardening [C4 + R5]

**Audit items:** C4 (race condition on concurrent sessions), R5 (no session expiry)
**Files:**
- Modify: `backend/src/modules/copilot/application/services/interview_service.py`
- Modify: `backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py` (if needed)
- Create: new Alembic migration for unique partial index

**Problem:** 
1. Concurrent requests can create duplicate active interview sessions for same domain. No DB constraint prevents this.
2. Interview sessions stay ACTIVE indefinitely with no auto-expiry.

**Goal:**
1. Add unique partial index: `UNIQUE (tenant_id, domain) WHERE status = 'active'` to prevent duplicates
2. Add session expiry: mark sessions as ABANDONED after 7 days of inactivity
3. Handle the duplicate gracefully in the service layer (catch IntegrityError, return existing)

- [ ] Read `interview_service.py` and the session repository to understand current flow
- [ ] Create idempotent migration with `CREATE UNIQUE INDEX IF NOT EXISTS` for the partial unique constraint
- [ ] Add `last_activity_at` column to interview session (or use existing `updated_at`)
- [ ] Add `expire_stale_sessions()` method to service (mark ABANDONED if inactive > 7 days)
- [ ] Handle `IntegrityError` in `start_interview()` — if duplicate, return existing active session
- [ ] Add tests for: concurrent creation attempt, expiry logic
- [ ] Run migration in Docker: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): prevent duplicate interview sessions + add 7-day expiry`

---

### Task 4: Rate Limiting for Chat [S1]

**Audit item:** S1 — Sin rate limiting en `/copilot/chat`
**Files:**
- Modify: `backend/src/main.py` (register middleware)
- Modify: `backend/src/modules/copilot/api/chat.py` (add decorator or dependency)
- Maybe create: `backend/src/core/rate_limit.py`

**Problem:** No rate limiting on `/copilot/chat`. A user can send unlimited messages, consuming LLM tokens without throttle.

**Goal:** 30 messages per minute per user. Return 429 with clear message when exceeded.

- [ ] Investigate: what's the best approach for this project? Options: SlowAPI, custom Redis counter, FastAPI dependency
- [ ] Check if Redis is available (it is — used for conversation cache)
- [ ] Implement rate limiter: 30 msgs/min per user_id
- [ ] Return proper 429 response with `Retry-After` header
- [ ] Add test
- [ ] Run: `cd backend && .venv/bin/ruff check src/ --no-cache`
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `feat(copilot): add rate limiting — 30 msgs/min per user on /chat`

---

### Task 5: Conversation Security [C2 + S3]

**Audit items:** C2 (ownership check), S3 (PII retention)
**Files:**
- Modify: `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py`
- Modify: `backend/src/modules/copilot/infrastructure/models/conversation_model.py`
- Create: new Alembic migration (add user_id column if missing, add expires_at)

**Problem:**
1. `conversation_id` comes from the client. If an attacker guesses a UUID, they can inject messages into another user's conversation. The repository filters by `tenant_id` but NOT by `user_id`.
2. Conversation messages persist indefinitely with no PII redaction or retention policy.

**Goal:**
1. Add `user_id` filter to `get_by_id()` and `get_or_create()`
2. Add `expires_at` column with default 90 days
3. Add `cleanup_expired_conversations()` method

- [ ] Read the conversation repository and model
- [ ] Add `user_id` validation to all conversation retrieval methods
- [ ] Add `expires_at` column (default: now + 90 days, nullable for existing rows)
- [ ] Add cleanup method for expired conversations
- [ ] Create idempotent migration
- [ ] Add tests: verify ownership check, verify expiry
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): add conversation ownership check + 90-day retention`

---

## Wave 2: Backend Quality

> All 4 tasks touch completely different files. Dispatch all 4 in parallel.

### Task 6: Fix N+1 Queries in Persisters [P5]

**Audit item:** P5 — N+1 queries en focus mode
**Files:**
- Modify: `backend/src/modules/copilot/infrastructure/persisters/offer_persister.py`
- Modify: `backend/src/modules/copilot/infrastructure/persisters/brand_persister.py`
- Maybe: `backend/src/modules/copilot/infrastructure/context/focus_context_loader.py`

**Problem:** `FocusContextLoader.load()` → `get_persister()` → repositories without eager joins. Offers with pricing/deliverables generate N+1 queries.

**Goal:** Add `selectinload()` or `joinedload()` options to persister queries to eagerly load related entities.

- [ ] Read the persisters and identify which queries lack eager loading
- [ ] Profile: how many queries does a typical `entity_read` for an offer generate?
- [ ] Add appropriate SQLAlchemy loading options (prefer `selectinload` for collections)
- [ ] Add test verifying query count is bounded
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `perf(copilot): add eager loading to focus mode persisters — fix N+1`

---

### Task 7: Token Estimation + Domain Boundary Fix [P6 + D1]

**Audit items:** P6 (naive token estimation), D1 (domain imports infrastructure)
**Files:**
- Modify: `backend/src/modules/copilot/application/orchestrator/context_budget.py`
- Modify: `backend/src/modules/copilot/domain/schema_introspection.py`

**Problem:**
1. `_estimate_tokens()` uses `len(text) // 4` — Claude tokenizes ~1.3 chars/token. Can exceed model context window.
2. `schema_introspection.py` (domain layer) imports `OfferPersister` (infrastructure) via TYPE_CHECKING.

**Goal:**
1. Improve token estimation heuristic to `len(text) // 2` or use tiktoken if available
2. Remove infrastructure import from domain — use Protocol or move type hints to shared

- [ ] Read `context_budget.py` — understand how the budget is calculated and used
- [ ] Investigate: is tiktoken installed? If not, use `len(text) // 2` as safer heuristic
- [ ] Implement improved estimation with safety margin
- [ ] Read `schema_introspection.py` — identify the TYPE_CHECKING import
- [ ] Refactor to remove infrastructure dependency (use Protocol or move to shared)
- [ ] Add test for token estimation accuracy
- [ ] Run: `cd backend && .venv/bin/ruff check src/modules/copilot/ --no-cache`
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): improve token estimation + remove domain→infrastructure import`

---

### Task 8: Prompt Injection Sanitization [S2]

**Audit item:** S2 — Prompt injection vía campos de usuario
**Files:**
- Modify: `backend/src/modules/copilot/infrastructure/prompts/base.py`
- Maybe modify: templates in `backend/src/modules/copilot/infrastructure/prompts/templates/`

**Problem:** User field values are inserted raw into Jinja2 system prompts. Malicious content could inject instructions.

**Goal:** Sanitize user-provided values before template insertion. Escape or wrap in delimiters that prevent instruction injection.

- [ ] Read `base.py` and the main system template `copilot_system.j2`
- [ ] Identify all template variables that contain user-provided data
- [ ] Investigate best practice: XML-tag wrapping (`<user_data>...</user_data>`), character escaping, or length truncation
- [ ] Implement sanitization in the prompt builder (before template rendering)
- [ ] Add test: verify that injected instructions in field values are neutralized
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): sanitize user data in system prompts to prevent injection`

---

### Task 9: Async/Sync Mismatch Fix [D3]

**Audit item:** D3 — async/sync mismatch in offer_ladder_tools
**Files:**
- Modify: `backend/src/modules/copilot/application/tools/offer_ladder_tools.py`

**Problem:** `OfferContextLoader` is async but called from sync tool context. `db.close()` on AsyncSession may not properly release connection.

**Goal:** Fix the async/sync boundary. Either make the tool async-compatible or use sync session.

- [ ] Read `offer_ladder_tools.py` to understand the current pattern
- [ ] Investigate: is the tool called in async or sync context? Check LangChain tool invocation pattern
- [ ] Fix the mismatch — ensure DB session type matches the execution context
- [ ] Add test
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `fix(copilot): resolve async/sync mismatch in offer ladder tools`

---

## Wave 3: Frontend Performance Core

> All 4 tasks touch completely different files. Dispatch all 4 in parallel.

### Task 10: Fix Zustand Bare Selectors [P1]

**Audit item:** P1 — 4 componentes sin selector function
**Files:**
- Modify: `frontend/src/features/copilot/components/ProcedureProgress.tsx`
- Modify: `frontend/src/features/copilot/hooks/useProactiveNudges.ts`
- Modify: `frontend/src/features/copilot/components/shared/section-chat-trigger.tsx`
- Modify: `frontend/src/features/copilot/components/CopilotRail.tsx`

**Problem:** These components use `useCopilotStore()` without a selector function. This means ANY store change triggers a re-render in ALL of them — even unrelated changes.

**Goal:** Replace bare `useCopilotStore()` destructuring with granular selectors like `useCopilotStore((s) => s.field)`.

- [ ] Read each of the 4 files
- [ ] For each file: identify which store fields are actually used
- [ ] Replace destructuring with individual selectors — one per field
- [ ] For CopilotRail: `messages` is only used for `messages.length > 0` — use derived selector
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `perf(copilot): fix 4 bare Zustand selectors — prevent cascade re-renders`

---

### Task 11: Message Limits in Store [P2]

**Audit item:** P2 — Mensajes sin límite
**Files:**
- Modify: `frontend/src/features/copilot/store/copilot-store.ts`

**Problem:** `messages[]` grows indefinitely. Long conversations (100+ messages) cause memory bloat and slow re-renders.

**Goal:** Limit stored messages to last 100. When new message added and count > 100, trim oldest messages.

- [ ] Read `copilot-store.ts` — understand `addMessage`, `appendToLastAssistant`, `clearMessages`
- [ ] Add `MAX_MESSAGES = 100` constant
- [ ] Modify `addMessage` to trim oldest messages when limit exceeded
- [ ] Ensure `appendToLastAssistant` doesn't create new array references unnecessarily
- [ ] Update existing store tests to verify trimming behavior
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `perf(copilot): limit message store to 100 messages — prevent memory bloat`

---

### Task 12: SSE Reconnection Logic [R1]

**Audit item:** R1 — SSE sin reconexión
**Files:**
- Modify: `frontend/src/features/copilot/api/copilot-api.ts`

**Problem:** If network drops mid-stream, the message stays stuck in "streaming" state with no recovery. No retry logic.

**Goal:** Add retry with exponential backoff (max 3 retries). On failure, call `onError` callback so UI can show error state.

- [ ] Read `copilot-api.ts` — understand `streamCopilotChat()` implementation
- [ ] Investigate: is retry of a POST appropriate here? (SSE via fetch, not EventSource)
- [ ] Implement: detect network error vs server error. Network errors → retry. Server errors (4xx/5xx) → don't retry
- [ ] Add retry logic: 3 attempts, exponential backoff (1s, 2s, 4s)
- [ ] Add `onRetry` callback for UI feedback
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `fix(copilot): add SSE retry with exponential backoff on network failure`

---

### Task 13: Chat Hook Reliability [R2 + D4-partial]

**Audit item:** R2 (send race condition), D4 (useCopilotChat split)
**Files:**
- Modify: `frontend/src/features/copilot/hooks/useCopilotChat.ts`
- Maybe create: `frontend/src/features/copilot/hooks/useCopilotStream.ts` (extracted streaming logic)

**Problem:** If user sends 2 messages rapidly, the second overwrites `abortRef` but the first continues streaming. This leaves orphaned assistant messages.

**Goal:**
1. Enforce single-flight: abort ALL in-flight requests before starting new one (at hook level, not just UI)
2. If the file is >200 lines after fix, extract streaming logic to a separate hook

- [ ] Read `useCopilotChat.ts` — understand the current abort/send flow
- [ ] Add send guard: if already streaming, abort current before starting new
- [ ] Track in-flight state with ref, not just AbortController
- [ ] If file exceeds 200 lines, extract streaming/event logic to `useCopilotStream.ts`
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `fix(copilot): prevent send race condition — enforce single-flight streaming`

---

## Wave 4: Frontend Components

> All 5 tasks touch completely different files. Dispatch all 5 in parallel.

### Task 14: Chat Virtualization + Typing Indicator [P3 + UX4]

**Audit items:** P3 (no virtualization), UX4 (no typing feedback)
**Files:**
- Modify: `frontend/src/features/copilot/components/CopilotChat.tsx`
- Maybe create: `frontend/src/features/copilot/components/messages/TypingIndicator.tsx`

**Problem:**
1. `messages.map()` renders ALL messages in DOM simultaneously. 100+ messages → heavy DOM.
2. No visual feedback that the assistant is "thinking" before the first chunk arrives.

**Goal:**
1. Add `@tanstack/react-virtual` for message list virtualization (install if needed)
2. Add typing indicator (animated 3 dots) that shows after user sends until first chunk arrives

- [ ] Check if `@tanstack/react-virtual` is installed: `cd frontend && cat package.json | grep virtual`
- [ ] If not installed: `cd frontend && npm install @tanstack/react-virtual`
- [ ] Read `CopilotChat.tsx` — understand current message rendering and auto-scroll
- [ ] Implement virtualized message list with `useVirtualizer`
- [ ] Preserve auto-scroll to bottom behavior
- [ ] Add TypingIndicator component (3 animated dots, Tailwind only)
- [ ] Show indicator when `status === "streaming"` and last assistant message has no content yet
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `perf(copilot): virtualize message list + add typing indicator`

---

### Task 15: Message Memoization + Card Transitions [P4 + UX5 + D4-partial]

**Audit items:** P4 (missing memo), UX5 (card transitions), D4 (AssistantMessage split)
**Files:**
- Modify: `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`
- Modify: `frontend/src/features/copilot/components/messages/UserMessage.tsx`
- Modify: `frontend/src/features/copilot/components/cards/alternatives-card.tsx`
- Modify: `frontend/src/features/copilot/components/cards/checkpoint-card.tsx`
- Modify: `frontend/src/features/copilot/components/cards/clarify-card.tsx`
- Modify: `frontend/src/features/copilot/components/cards/interview-complete-card.tsx`
- Modify: `frontend/src/features/copilot/components/NudgeBanner.tsx`

**Problem:**
1. None of these components are wrapped in `memo()` — every new message re-renders ALL messages.
2. Interview cards appear instantly with no transitions.

**Goal:**
1. Wrap all message and card components in `memo()`
2. Add subtle CSS transitions to cards: slide-in when appearing, scale+check when option selected
3. If AssistantMessage has a card renderer switch that's getting long, extract it

- [ ] Read each component file
- [ ] Wrap each in `memo()` with appropriate comparison (props-based)
- [ ] Add card transition: CSS `animate-in` (slide up + fade) using Tailwind — no extra library needed
- [ ] Add selection feedback on cards: scale animation on option click
- [ ] Ensure `useCallback` is used for any callback props to not break memoization
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `perf(copilot): memoize message/card components + add card transitions`

---

### Task 16: Focus Activation — Fresh Data + Prefetch [R3 + UX3]

**Audit items:** R3 (stale entity data), UX3 (prefetch on hover)
**Files:**
- Modify: `frontend/src/features/copilot/components/focus-mode-button.tsx`

**Problem:**
1. `entityData` prop is captured at render time. If entity changes between render and click, focus gets stale snapshot.
2. No prefetch — preview data loads after focus activation, causing a loading flash.

**Goal:**
1. At activation time, re-fetch entity data (or accept a data-fetching callback)
2. On hover, trigger a prefetch of the entity data so activation is instant

- [ ] Read `focus-mode-button.tsx` and understand the current flow
- [ ] Investigate: where does entity data come from? React Query cache? Direct prop?
- [ ] Option A: Accept `onActivate` callback that returns fresh data
- [ ] Option B: Accept `queryKey` and invalidate/prefetch on hover
- [ ] Implement prefetch on `onMouseEnter` — preload entity data into React Query cache
- [ ] On click: use fresh data from cache instead of stale prop
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `fix(copilot): fetch fresh entity data on focus activation + prefetch on hover`

---

### Task 17: Focus Bar — Exit Validation + Micro-interactions [R4 + UX6]

**Audit items:** R4 (focus exit no validation), UX6 (micro-interactions)
**Files:**
- Modify: `frontend/src/features/copilot/components/focus-bar.tsx`

**Problem:**
1. `handleExitFocus()` clears state without checking if entity still exists or has unsaved changes.
2. Progress dots are static. Exit button has no confirmation.

**Goal:**
1. Before exiting: check if there are unsaved changes (compare snapshot vs current previewData)
2. If unsaved changes: show confirmation dialog before clearing
3. Add micro-interactions: dot fill animation on block complete, tooltip on hover showing block name

- [ ] Read `focus-bar.tsx` — understand current exit flow and progress rendering
- [ ] Add unsaved changes detection: `previewData !== focusSnapshot`
- [ ] Add confirmation dialog (use existing AlertDialog from Shadcn UI)
- [ ] Add CSS transition on progress dots: `transition-colors duration-300` for fill animation
- [ ] Add tooltip on dots showing block name (use Shadcn Tooltip)
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `fix(copilot): focus bar exit validation + progress dot animations + tooltips`

---

### Task 18: DOM Timing Fix [R6]

**Audit item:** R6 — DOM manipulation con timing fijo
**Files:**
- Modify: `frontend/src/features/copilot/hooks/useCopilotNavigator.ts`

**Problem:** Fixed 800ms `setTimeout` assumes navigation completes in time. Flaky on slow renders. Element may not exist after timeout.

**Goal:** Replace fixed timer with navigation-completion detection. Use `requestAnimationFrame` chain or `MutationObserver` to wait for the target element.

- [ ] Read `useCopilotNavigator.ts` — understand current scrollIntoView + highlight logic
- [ ] Replace `setTimeout(800)` with a polling approach: check for element every 100ms, max 3s
- [ ] Validate element still exists before `classList.add`/`remove`
- [ ] Clean up highlight if component unmounts (use effect cleanup)
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `fix(copilot): replace fixed 800ms DOM timer with element-ready polling`

---

## Wave 5: Frontend Polish

> Both tasks touch completely different files. Dispatch both in parallel.

### Task 19: Sidebar Animations + Mobile [UX1 + UX2]

**Audit items:** UX1 (content animations), UX2 (mobile responsive)
**Files:**
- Modify: `frontend/src/features/copilot/components/copilot-sidebar.tsx`
- Modify: `frontend/src/features/copilot/components/copilot-preview-pane.tsx`

**Problem:**
1. Sidebar width transitions are smooth (CSS), but content appears/disappears abruptly.
2. Hardcoded widths (60/380/780px) overflow on mobile. No responsive behavior.

**Goal:**
1. Add opacity + transform transitions to chat content and preview pane (fade-in/out)
2. On mobile (`<768px`): full-screen overlay sheet with toggle between chat and preview
3. Auto-collapse sidebar to rail on mobile

- [ ] Read `copilot-sidebar.tsx` and `copilot-preview-pane.tsx`
- [ ] Add `transition-opacity` and `transition-transform` to content containers
- [ ] Add responsive variants: `md:w-[380px]` etc. Below `md`: full-width overlay
- [ ] Add mobile toggle button (chat ↔ preview) when expanded on mobile
- [ ] Test with `md:` breakpoint (768px) in browser devtools
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `feat(copilot): sidebar content animations + mobile responsive overlay`

---

### Task 20: CopilotInput Split [D4-partial]

**Audit item:** D4 — copilot-input.tsx at 243 lines
**Files:**
- Modify: `frontend/src/features/copilot/components/copilot-input.tsx`
- Create: `frontend/src/features/copilot/components/shared/voice-button.tsx`
- Create: `frontend/src/features/copilot/components/shared/attachment-button.tsx` (if not exists)

**Problem:** `copilot-input.tsx` at 243 lines mixes input logic, voice recording trigger, and file attachment into one component.

**Goal:** Extract voice button and attachment button into separate focused components. Main input component should be ~120 lines.

- [ ] Read `copilot-input.tsx` — identify the voice and attachment sections
- [ ] Extract voice recording button + logic to `voice-button.tsx`
- [ ] Extract attachment button to `attachment-button.tsx` (check if it already exists separately)
- [ ] Keep CopilotInput as the orchestrator component
- [ ] Ensure all props and callbacks are properly threaded
- [ ] Run: `cd frontend && npx tsc --noEmit`
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `refactor(copilot): split CopilotInput — extract voice + attachment buttons`

---

## Wave 6: Testing

> All 4 tasks create NEW files only (no conflicts with existing code). Dispatch all 4 in parallel.

### Task 21: E2E Infrastructure [T8]

**Audit item:** T8 — Missing POM, fixtures, mock infrastructure
**Files (all new):**
- Create: `frontend/e2e/pages/copilot.pom.ts`
- Create: `frontend/e2e/fixtures/copilot-chat.fixture.ts`
- Create: `frontend/e2e/fixtures/copilot-interview.fixture.ts`

**Goal:** Create reusable E2E infrastructure for copilot tests. POM with locators for sidebar, chat input, messages, focus bar. Fixtures with mock API responses for chat streaming and interview sessions.

- [ ] Read existing POMs in `frontend/e2e/pages/` to understand the pattern (e.g., `brand-studio.page.ts`)
- [ ] Read existing fixtures in `frontend/e2e/fixtures/` (especially `api-mock.fixture.ts`)
- [ ] Create `copilot.pom.ts` with: sidebar locators, chat input, send button, message list, focus bar, interview cards
- [ ] Create `copilot-chat.fixture.ts` with: mock SSE responses, mock chat endpoint
- [ ] Create `copilot-interview.fixture.ts` with: mock interview session data, mock interview start/resume
- [ ] Verify fixtures are importable: `cd frontend && npx tsc --noEmit`
- [ ] Commit: `test(copilot): add E2E infrastructure — POM + chat/interview fixtures`

---

### Task 22: E2E Smoke Tests [T1]

**Audit item:** T1 — 0 E2E tests for copilot
**Files (all new):**
- Create: `frontend/e2e/specs/smoke/copilot-chat.smoke.spec.ts`
- Create: `frontend/e2e/specs/smoke/copilot-sidebar.smoke.spec.ts`

**Goal:** Write smoke E2E tests for the most critical copilot flows. These should use mocked API responses (not hit real LLM).

**IMPORTANT:** This task depends on Task 21 (E2E infrastructure). If running in parallel, coordinate fixtures.

- [ ] Read existing smoke tests (e.g., `brand-crud.smoke.spec.ts`) for patterns
- [ ] Create `copilot-sidebar.smoke.spec.ts`:
  - Test: sidebar renders in collapsed state
  - Test: click rail icon → sidebar opens to 380px
  - Test: sidebar shows chat input
- [ ] Create `copilot-chat.smoke.spec.ts`:
  - Test: type message + send → mock SSE response renders
  - Test: message appears in chat list
- [ ] Use mocked API responses from fixtures (don't rely on real backend)
- [ ] Run: `cd frontend && npx playwright test --project=smoke --grep copilot` (if dev containers running)
- [ ] Commit: `test(copilot): add E2E smoke tests for sidebar + chat`

---

### Task 23: Frontend Unit Tests [T2-T4]

**Audit items:** T2 (useCopilotChat), T3 (API layer), T4 (card interactions)
**Files (all new):**
- Create: `frontend/src/features/copilot/hooks/__tests__/useCopilotChat.test.ts`
- Create: `frontend/src/features/copilot/api/__tests__/copilot-api.test.ts`
- Create: `frontend/src/features/copilot/components/cards/__tests__/alternatives-card.test.tsx`
- Create: `frontend/src/features/copilot/components/cards/__tests__/checkpoint-card.test.tsx`

**Goal:** Cover the most critical untested frontend code.

- [ ] Read `useCopilotChat.ts` — write tests for: sendMessage, abort handling, error states
- [ ] Read `copilot-api.ts` — write tests for: SSE parsing, error handling, header construction
- [ ] Read `alternatives-card.tsx` — write tests for: option click, status update
- [ ] Read `checkpoint-card.tsx` — write tests for: confirm click, revise click
- [ ] Mock: fetch API, AbortController, Zustand store
- [ ] Run: `cd frontend && npx vitest run src/features/copilot/`
- [ ] Commit: `test(copilot): add unit tests for chat hook, API layer, card interactions`

---

### Task 24: Backend Test Gaps [T5-T7]

**Audit items:** T5 (streaming tests), T6 (empty test file), T7 (concurrency)
**Files:**
- Modify: `backend/tests/modules/copilot/test_offer_ladder_tools.py` (fill empty file)
- Create: `backend/tests/modules/copilot/test_streaming_integration.py`
- Create: `backend/tests/modules/copilot/test_concurrent_sessions.py`

**Goal:** Fill backend test gaps — especially the empty test file and missing streaming tests.

- [ ] Read `offer_ladder_tools.py` — write meaningful tests for the empty test file
- [ ] Write streaming integration test: verify SSE events are properly formatted
- [ ] Write concurrent session test: verify behavior when 2 requests hit interview service simultaneously
- [ ] Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
- [ ] Commit: `test(copilot): fill test gaps — offer ladder, streaming, concurrency`

---

## Wave 7: Full Verification

### Task 25: Full Test Suite Verification

**Files:** None (verification only)

- [ ] Backend lint: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
- [ ] Backend tests: `cd backend && .venv/bin/pytest -x -q --tb=short`
- [ ] Architecture tests: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
- [ ] Frontend TypeScript: `cd frontend && npx tsc --noEmit`
- [ ] Frontend ESLint: `cd frontend && npx eslint src/`
- [ ] Frontend tests: `cd frontend && npx vitest run`
- [ ] Report: total test count, any failures, delta from Phase 4 baseline (2403 backend, 1017 frontend, 62 arch)

---

## Execution Notes for the Orchestrating Agent

### Model Selection per Task

| Task Type | Recommended Model | Rationale |
|-----------|------------------|-----------|
| Tasks 1-5 (security) | opus | Requires security judgment |
| Tasks 6-9 (backend quality) | sonnet | Mechanical but needs code reading |
| Tasks 10-13 (frontend perf) | sonnet | Clear patterns, focused changes |
| Tasks 14-18 (components) | sonnet | UI work, clear specs |
| Tasks 19-20 (polish) | sonnet | CSS/component work |
| Tasks 21-24 (testing) | sonnet | Test writing, well-defined |
| Task 25 (verification) | sonnet | Just running commands |

### Critical Rules

1. **ALL lint/tests run NATIVELY in WSL** — never via `docker exec`
2. **Stage files by name** — never `git add .` or `git add -A`
3. **Conventional commits** with `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`
4. **Idempotent migrations** — raw SQL with `IF NOT EXISTS`
5. **Spanish text with tildes** — check all user-visible strings
6. **TDD when adding tests** — write test first, then verify it fails, then implement

### Post-Wave Checkpoints

After each wave completes:
1. Run full test suite to catch regressions
2. Review git log — verify all commits follow conventions
3. Check for any files that were accidentally modified by multiple agents

### Start Command for New Conversation

```
Lee docs/superpowers/plans/2026-04-13-phase5-copilot-hardening.md y ejecútalo wave por wave usando subagent-driven-development. Dentro de cada wave, despacha los agentes en paralelo usando dispatching-parallel-agents. Este es el plan final — cuando termines, pushea a development.
```
