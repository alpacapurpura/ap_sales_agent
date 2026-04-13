# Unified Copilot Phase 1: Unified Input + Interview Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** First visible value — copilot sidebar gets audio + file upload; interview system prompt + tools properly scoped via the single `/copilot/chat` endpoint.

**Architecture:** All modes (chat, focus, interview) share `POST /copilot/chat`. The frontend sends `interview_session_id` and `focus` in the context payload. The backend loads the session, composes layered prompts, and selects tools by mode. Frontend merges `useCopilotChat` + `useInterviewChat` into one hook writing to Zustand.

**Tech Stack:** FastAPI + Pydantic v2 (backend DTOs), LangGraph (orchestrator), React + Zustand + SSE (frontend), Vitest + pytest (TDD)

**Spec:** `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` (Sections 4-7)
**Handoff:** `docs/superpowers/specs/2026-04-13-phase1-handoff.md`
**Gaps:** `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md`

---

## File Map

### Backend — Create

| File | Responsibility |
|------|---------------|
| `backend/tests/modules/copilot/test_context_dto.py` | Tests for FocusContextDTO + extended ClientContextDTO |
| `backend/tests/modules/copilot/test_orchestrator_interview_context.py` | Tests for interview session loading in orchestrator |
| `backend/tests/modules/copilot/test_tool_selection_mode.py` | Tests for mode-based tool selection |

### Backend — Modify

| File | Change |
|------|--------|
| `backend/src/modules/copilot/api/dto.py:10-16` | Add `FocusContextDTO`, extend `ClientContextDTO` with `focus` + `interview_session_id` |
| `backend/src/modules/copilot/application/orchestrator/chat.py:68-82` | Pass focus/interview_session_id to state; load InterviewSession |
| `backend/src/modules/copilot/application/tools/registry.py:117-136` | Add `get_tools_for_context()` with mode-aware selection |
| `backend/src/modules/copilot/application/orchestrator/graph.py:331-343` | Use `get_tools_for_context()` instead of `get_tools_for_route()` |
| `backend/src/modules/copilot/api/interview_dto.py:8-12` | Add `entity_id: UUID \| None = None` |
| `backend/src/modules/copilot/api/interview.py:32-52` | Pass `entity_id` to service |
| `backend/tests/modules/copilot/test_interview_api.py` | Add test for entity_id |

### Frontend — Create

| File | Responsibility |
|------|---------------|
| `frontend/src/features/copilot/__tests__/assistant-message-cards.test.tsx` | Tests for interview card rendering in AssistantMessage |

### Frontend — Modify

| File | Change |
|------|--------|
| `frontend/src/features/copilot/store/copilot-store.ts:27-49` | Extend UIAction union with interview card types + add `updateUIActionStatus` |
| `frontend/src/features/copilot/types/index.ts` | Re-export new types |
| `frontend/src/features/copilot/__tests__/copilot-store.test.ts` | Add tests for interview UIActions + updateUIActionStatus |
| `frontend/src/features/copilot/api/copilot-api.ts:6-15` | Extend `CopilotChatPayload.context` with `focus` + `interview_session_id` |
| `frontend/src/features/copilot/api/interview-api.ts` | Add `entity_id` param to `startInterview()` |
| `frontend/src/features/copilot/components/CopilotChat.tsx:137-171` | Replace textarea with `<CopilotInput />` |
| `frontend/src/features/copilot/hooks/useCopilotChat.ts` | Mode-aware send, handle interview UIActions, add `sendCardAction` |
| `frontend/src/features/copilot/components/messages/AssistantMessage.tsx:42-79` | Add switch cases for interview cards |
| `frontend/src/features/copilot/hooks/useInterviewChat.ts` | Replace with thin wrapper delegating to useCopilotChat |

---

## Task Dependencies & Parallelization

```
Round 1 (all independent — dispatch in parallel):
  Task 1: Backend DTO extension
  Task 2: Backend tool selection by mode
  Task 3: Backend entity_id in StartInterviewRequest
  Task 4: Frontend UIAction types extension
  Task 5: Frontend CopilotChatPayload extension
  Task 6: Frontend CopilotChat uses CopilotInput

Round 2 (after Tasks 4+5 complete):
  Task 7: Frontend useCopilotChat absorbs useInterviewChat

Round 3 (after Task 7 completes — can be parallel):
  Task 8: Frontend AssistantMessage renders interview cards
  Task 9: Frontend deprecate useInterviewChat

Round 4 (after all):
  Task 10: Integration + full test suite
```

---

## Task 1: Backend — Extend ClientContextDTO + Load Interview Context

**Files:**
- Modify: `backend/src/modules/copilot/api/dto.py:10-16`
- Modify: `backend/src/modules/copilot/application/orchestrator/chat.py:68-82`
- Create: `backend/tests/modules/copilot/test_context_dto.py`
- Create: `backend/tests/modules/copilot/test_orchestrator_interview_context.py`

### Step 1.1: Write failing test for FocusContextDTO

- [ ] Create `backend/tests/modules/copilot/test_context_dto.py`:

```python
"""Tests for extended ClientContextDTO with focus and interview fields."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.copilot.api.dto import ClientContextDTO, FocusContextDTO


class TestFocusContextDTO:
    """Tests for the FocusContextDTO Pydantic model."""

    def test_valid_focus_context(self) -> None:
        dto = FocusContextDTO(domain="offer", entity_id=str(uuid4()))
        assert dto.domain == "offer"
        assert dto.entity_id is not None

    def test_focus_context_without_entity_id(self) -> None:
        dto = FocusContextDTO(domain="brand")
        assert dto.domain == "brand"
        assert dto.entity_id is None

    def test_focus_context_requires_domain(self) -> None:
        with pytest.raises(ValidationError):
            FocusContextDTO()


class TestClientContextDTOExtended:
    """Tests for focus and interview_session_id on ClientContextDTO."""

    def test_client_context_with_focus(self) -> None:
        dto = ClientContextDTO(
            current_route="/offer-studio/offer/123",
            focus=FocusContextDTO(domain="offer", entity_id="123"),
        )
        assert dto.focus is not None
        assert dto.focus.domain == "offer"

    def test_client_context_with_interview_session_id(self) -> None:
        sid = str(uuid4())
        dto = ClientContextDTO(
            current_route="/brand-studio/interview",
            interview_session_id=sid,
        )
        assert dto.interview_session_id == sid

    def test_client_context_backward_compatible(self) -> None:
        dto = ClientContextDTO(current_route="/brand-studio")
        assert dto.focus is None
        assert dto.interview_session_id is None

    def test_client_context_with_both_focus_and_interview(self) -> None:
        sid = str(uuid4())
        dto = ClientContextDTO(
            current_route="/offer-studio/offer/123",
            focus=FocusContextDTO(domain="offer", entity_id="123"),
            interview_session_id=sid,
        )
        assert dto.focus.domain == "offer"
        assert dto.interview_session_id == sid
```

- [ ] Run test to verify it fails:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_context_dto.py -x -q --tb=short
```

Expected: FAIL — `FocusContextDTO` not importable from `dto.py`

### Step 1.2: Implement FocusContextDTO + extend ClientContextDTO

- [ ] In `backend/src/modules/copilot/api/dto.py`, add after the imports (before `ClientContextDTO`):

```python
class FocusContextDTO(BaseModel):
    """Focus context for Focus and Interview modes."""

    domain: str  # "offer", "brand", "buyer_persona"
    entity_id: str | None = None  # UUID of the focused entity (None for brand singleton)
```

- [ ] In `ClientContextDTO`, add two new fields at the end:

```python
class ClientContextDTO(BaseModel):
    """Data transfer object for client context."""

    current_route: str | None = None
    selected_fields: list[dict[str, str]] = Field(default_factory=list)
    form_data: dict[str, Any] = Field(default_factory=dict)
    locale: str = "es"
    focus: FocusContextDTO | None = None
    interview_session_id: str | None = None
```

- [ ] Run test to verify it passes:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_context_dto.py -x -q --tb=short
```

Expected: PASS (6 tests)

### Step 1.3: Write failing test for orchestrator interview context loading

- [ ] Create `backend/tests/modules/copilot/test_orchestrator_interview_context.py`:

```python
"""Tests for interview context loading in CopilotOrchestrator."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator
from src.modules.copilot.api.dto import ClientContextDTO, FocusContextDTO


def _make_mock_db() -> MagicMock:
    """Create a mock SQLAlchemy Session."""
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = None
    return db


class TestOrchestratorContextBuilding:
    """Test that the orchestrator correctly passes focus/interview context to state."""

    def test_focus_context_passed_to_state(self) -> None:
        """When focus is present in DTO, it appears in client_ctx dict."""
        orch = CopilotOrchestrator(_make_mock_db())
        context = ClientContextDTO(
            current_route="/offer-studio/offer/123",
            focus=FocusContextDTO(domain="offer", entity_id="123"),
        )
        # Access the internal state-building logic
        client_ctx = orch._build_client_context(context)
        assert client_ctx["focus"] == {"domain": "offer", "entity_id": "123"}

    def test_interview_session_id_passed_to_state(self) -> None:
        """When interview_session_id is present in DTO, it appears in client_ctx dict."""
        orch = CopilotOrchestrator(_make_mock_db())
        sid = str(uuid4())
        context = ClientContextDTO(
            current_route="/brand-studio/interview",
            interview_session_id=sid,
        )
        client_ctx = orch._build_client_context(context)
        assert client_ctx["interview_session_id"] == sid

    def test_backward_compatible_no_focus_no_interview(self) -> None:
        """Existing callers without focus/interview still work."""
        orch = CopilotOrchestrator(_make_mock_db())
        context = ClientContextDTO(current_route="/brand-studio")
        client_ctx = orch._build_client_context(context)
        assert client_ctx.get("focus") is None
        assert client_ctx.get("interview_session_id") is None
```

- [ ] Run test to verify it fails:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_orchestrator_interview_context.py -x -q --tb=short
```

Expected: FAIL — `_build_client_context` method doesn't exist

### Step 1.4: Extract _build_client_context + add interview context loading

- [ ] In `backend/src/modules/copilot/application/orchestrator/chat.py`, add import at the top:

```python
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
```

- [ ] Add the `_build_client_context` method to `CopilotOrchestrator` (after `__init__`):

```python
    def _build_client_context(self, context: ClientContextDTO | None) -> dict:
        """Build client context dict from DTO, including focus and interview fields."""
        if not context:
            return {
                "current_route": None,
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            }
        ctx: dict = {
            "current_route": context.current_route,
            "selected_fields": [
                f.model_dump() if hasattr(f, "model_dump") else f
                for f in context.selected_fields
            ],
            "form_data": context.form_data,
            "locale": context.locale,
        }
        if context.focus:
            ctx["focus"] = context.focus.model_dump()
        if context.interview_session_id:
            ctx["interview_session_id"] = context.interview_session_id
        return ctx
```

- [ ] Replace the inline dict construction in `stream_chat()` (lines 68-75) with:

```python
        # 2. Build state
        client_ctx = self._build_client_context(context)
```

- [ ] After state creation (after `state = create_initial_copilot_state(...)`, ~line 82), add interview session loading:

```python
        # 2b. Load interview session if interview_session_id is present
        if client_ctx.get("interview_session_id"):
            try:
                session_repo = InterviewSessionRepository(self.db)
                interview_session = session_repo.get_by_id(
                    UUID(client_ctx["interview_session_id"]),
                    tenant_id,
                )
                if interview_session:
                    state["interview_session"] = interview_session
            except (ValueError, TypeError):
                logger.warning(
                    "invalid_interview_session_id",
                    session_id=client_ctx["interview_session_id"],
                )
```

- [ ] Run tests:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_orchestrator_interview_context.py tests/modules/copilot/test_context_dto.py -x -q --tb=short
```

Expected: PASS (all tests)

### Step 1.5: Run full backend test suite to verify no regressions

- [ ] Run:

```bash
cd backend && .venv/bin/ruff check src/modules/copilot/api/dto.py src/modules/copilot/application/orchestrator/chat.py --no-cache && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short
```

Expected: All pass, no lint errors

### Step 1.6: Commit

```bash
git add backend/src/modules/copilot/api/dto.py backend/src/modules/copilot/application/orchestrator/chat.py backend/tests/modules/copilot/test_context_dto.py backend/tests/modules/copilot/test_orchestrator_interview_context.py
git commit -m "feat(copilot): extend ClientContextDTO with focus/interview + load session in orchestrator"
```

---

## Task 2: Backend — Tool Selection by Mode

**Files:**
- Modify: `backend/src/modules/copilot/application/tools/registry.py`
- Modify: `backend/src/modules/copilot/application/orchestrator/graph.py:324-349`
- Create: `backend/tests/modules/copilot/test_tool_selection_mode.py`

### Step 2.1: Write failing tests for mode-based tool selection

- [ ] Create `backend/tests/modules/copilot/test_tool_selection_mode.py`:

```python
"""Tests for context-aware (mode-based) tool selection."""

from src.modules.copilot.application.tools.registry import (
    TOOL_GROUPS,
    get_tools_for_context,
)


class TestToolSelectionByMode:
    """Tool selection changes based on interview/focus/chat mode."""

    def test_interview_mode_returns_interview_and_knowledge_tools(self) -> None:
        """When interview_session_id is present, only interview + knowledge tools."""
        ctx = {
            "current_route": "/brand-studio",
            "interview_session_id": "session-123",
        }
        tools = get_tools_for_context(ctx)
        tool_names = {t.name for t in tools}

        # Must include all interview tools
        for t in TOOL_GROUPS["interview"]:
            assert t.name in tool_names, f"Missing interview tool: {t.name}"

        # Must include knowledge tools
        for t in TOOL_GROUPS["knowledge"]:
            assert t.name in tool_names, f"Missing knowledge tool: {t.name}"

        # Must NOT include mutation tools (chat-only)
        for t in TOOL_GROUPS.get("mutation", []):
            assert t.name not in tool_names, f"Unexpected mutation tool: {t.name}"

    def test_interview_mode_ignores_route(self) -> None:
        """Interview mode returns same tools regardless of route."""
        ctx_brand = {
            "current_route": "/brand-studio",
            "interview_session_id": "session-123",
        }
        ctx_offer = {
            "current_route": "/offer-studio/offer/456",
            "interview_session_id": "session-456",
        }
        tools_brand = {t.name for t in get_tools_for_context(ctx_brand)}
        tools_offer = {t.name for t in get_tools_for_context(ctx_offer)}
        assert tools_brand == tools_offer

    def test_chat_mode_uses_route_based_selection(self) -> None:
        """Without interview or focus, falls back to route-based selection."""
        ctx = {"current_route": "/growth-studio"}
        tools = get_tools_for_context(ctx)
        tool_names = {t.name for t in tools}

        # Growth studio should have analytics tools
        for t in TOOL_GROUPS["analytics"]:
            assert t.name in tool_names, f"Missing analytics tool: {t.name}"

    def test_empty_context_uses_fallback(self) -> None:
        """Empty context dict uses route-based fallback."""
        tools = get_tools_for_context({})
        assert len(tools) > 0

    def test_none_context_uses_fallback(self) -> None:
        """None-like context falls back gracefully."""
        tools = get_tools_for_context(None)
        assert len(tools) > 0

    def test_all_returned_tools_have_name_attribute(self) -> None:
        """Verify LangChain tool contract for mode-selected tools."""
        ctx = {"interview_session_id": "s-1"}
        tools = get_tools_for_context(ctx)
        for t in tools:
            assert hasattr(t, "name"), f"Tool {t!r} missing .name"
            assert t.name, f"Tool {t!r} has empty .name"
```

- [ ] Run test to verify it fails:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_tool_selection_mode.py -x -q --tb=short
```

Expected: FAIL — `get_tools_for_context` not importable

### Step 2.2: Implement get_tools_for_context

- [ ] In `backend/src/modules/copilot/application/tools/registry.py`, add after `get_all_tools()`:

```python
def get_tools_for_context(context: dict | None) -> list:
    """Return tools based on mode (interview > focus > chat).

    Mode is determined by context fields:
    - interview_session_id present → Interview mode (interview + knowledge tools)
    - focus present → Focus mode (route-based + knowledge, no mutation)
    - Neither → Chat mode (route-based, current behavior)
    """
    if not context:
        return get_tools_for_route(None)

    # Interview mode: interview + knowledge tools only
    if context.get("interview_session_id"):
        tools = []
        seen: set[str] = set()
        for group_name in ("interview", "knowledge"):
            for t in TOOL_GROUPS.get(group_name, []):
                if t.name not in seen:
                    tools.append(t)
                    seen.add(t.name)
        return tools

    # Chat mode (and future Focus mode): route-based selection
    return get_tools_for_route(context.get("current_route"))
```

- [ ] Run test to verify it passes:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_tool_selection_mode.py -x -q --tb=short
```

Expected: PASS (6 tests)

### Step 2.3: Wire get_tools_for_context into agent_node

- [ ] In `backend/src/modules/copilot/application/orchestrator/graph.py`, update the import (line 20-24):

Replace:
```python
from src.modules.copilot.application.tools.registry import (
    get_all_tools,
    get_tools_for_route,
)
```

With:
```python
from src.modules.copilot.application.tools.registry import (
    get_all_tools,
    get_tools_for_context,
    get_tools_for_route,
)
```

- [ ] In `agent_node()`, replace the tool selection line:

Replace:
```python
    tools = get_tools_for_route(current_route)
```

With:
```python
    tools = get_tools_for_context(ctx)
```

- [ ] In `tool_executor_node()` (line 366), replace:

```python
    route_tools = get_tools_for_route(current_route)
```

With:

```python
    route_tools = get_tools_for_context(ctx)
```

This ensures tool execution also uses mode-aware selection, not just tool binding.

- [ ] Run full copilot test suite:

```bash
cd backend && .venv/bin/ruff check src/modules/copilot/application/tools/registry.py src/modules/copilot/application/orchestrator/graph.py --no-cache && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short
```

Expected: All pass

### Step 2.4: Commit

```bash
git add backend/src/modules/copilot/application/tools/registry.py backend/src/modules/copilot/application/orchestrator/graph.py backend/tests/modules/copilot/test_tool_selection_mode.py
git commit -m "feat(copilot): mode-based tool selection (interview overrides route)"
```

---

## Task 3: Backend — StartInterviewRequest Accepts entity_id

**Files:**
- Modify: `backend/src/modules/copilot/api/interview_dto.py:8-12`
- Modify: `backend/src/modules/copilot/api/interview.py:32-52`
- Modify: `backend/tests/modules/copilot/test_interview_api.py`

### Step 3.1: Write failing test for entity_id

- [ ] In `backend/tests/modules/copilot/test_interview_api.py`, add a new test class (append to file):

```python
class TestStartInterviewRequestEntityId:
    """Test that StartInterviewRequest accepts entity_id."""

    def test_start_request_with_entity_id(self) -> None:
        from uuid import uuid4
        from src.modules.copilot.api.interview_dto import StartInterviewRequest

        eid = uuid4()
        req = StartInterviewRequest(domain="offer", entity_id=eid)
        assert req.entity_id == eid
        assert req.domain == "offer"

    def test_start_request_without_entity_id(self) -> None:
        from src.modules.copilot.api.interview_dto import StartInterviewRequest

        req = StartInterviewRequest(domain="brand")
        assert req.entity_id is None

    def test_start_request_defaults(self) -> None:
        from src.modules.copilot.api.interview_dto import StartInterviewRequest

        req = StartInterviewRequest()
        assert req.domain == "brand"
        assert req.entity_id is None
        assert req.resume_session_id is None
```

- [ ] Run test to verify it fails:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_api.py::TestStartInterviewRequestEntityId -x -q --tb=short
```

Expected: FAIL — `entity_id` not a field on `StartInterviewRequest`

### Step 3.2: Add entity_id to DTO + pass through endpoint

- [ ] In `backend/src/modules/copilot/api/interview_dto.py`, update `StartInterviewRequest`:

```python
class StartInterviewRequest(BaseModel):
    """Request schema for start interview."""

    domain: str = "brand"
    resume_session_id: UUID | None = None
    entity_id: UUID | None = None
```

- [ ] In `backend/src/modules/copilot/api/interview.py`, update the `start_interview` endpoint to pass `entity_id`:

Replace:
```python
    result = svc.start_interview(
        tenant_id=tenant_id,
        user_id=current_user.id,
        domain=request.domain,
        resume_session_id=request.resume_session_id,
    )
```

With:
```python
    result = svc.start_interview(
        tenant_id=tenant_id,
        user_id=current_user.id,
        domain=request.domain,
        resume_session_id=request.resume_session_id,
        entity_id=request.entity_id,
    )
```

- [ ] Run test:

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_api.py -x -q --tb=short
```

Expected: PASS

### Step 3.3: Lint + commit

```bash
cd backend && .venv/bin/ruff check src/modules/copilot/api/interview_dto.py src/modules/copilot/api/interview.py --no-cache
git add backend/src/modules/copilot/api/interview_dto.py backend/src/modules/copilot/api/interview.py backend/tests/modules/copilot/test_interview_api.py
git commit -m "feat(copilot): accept entity_id in StartInterviewRequest"
```

---

## Task 4: Frontend — Extend UIAction with Interview Card Types

**Files:**
- Modify: `frontend/src/features/copilot/store/copilot-store.ts:27-49`
- Modify: `frontend/src/features/copilot/types/index.ts`
- Modify: `frontend/src/features/copilot/__tests__/copilot-store.test.ts`

### Step 4.1: Write failing tests for interview UIAction types

- [ ] In `frontend/src/features/copilot/__tests__/copilot-store.test.ts`, add at the end of the file:

```typescript
describe('Interview UIAction types', () => {
  beforeEach(() => {
    useCopilotStore.setState({
      messages: [],
      status: 'idle',
    });
  });

  it('should support alternatives_card UIAction type', () => {
    const msg: CopilotMessage = {
      id: 'msg-1',
      role: 'assistant',
      content: 'Here are some options:',
      timestamp: Date.now(),
      uiActions: [{
        type: 'alternatives_card',
        field_path: 'strategy.target_audience',
        question: 'Who is your target audience?',
        alternatives: [
          { id: '1', title: 'Option A', description: 'First option', recommended: true },
          { id: '2', title: 'Option B', description: 'Second option' },
        ],
        allow_custom: true,
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    const stored = useCopilotStore.getState().messages[0];
    expect(stored.uiActions![0].type).toBe('alternatives_card');
    expect(stored.uiActions![0].alternatives).toHaveLength(2);
  });

  it('should support checkpoint_card UIAction type', () => {
    const msg: CopilotMessage = {
      id: 'msg-2',
      role: 'assistant',
      content: 'Block complete!',
      timestamp: Date.now(),
      uiActions: [{
        type: 'checkpoint_card',
        block_id: 'strategy',
        block_label: 'Estrategia',
        summary: { name: 'Test' },
        health_score: 85,
        blocks_progress: { completed: 1, total: 5 },
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    const action = useCopilotStore.getState().messages[0].uiActions![0];
    expect(action.type).toBe('checkpoint_card');
    expect(action.health_score).toBe(85);
  });

  it('should update UIAction status via updateUIActionStatus', () => {
    const msg: CopilotMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Options:',
      timestamp: Date.now(),
      uiActions: [{
        type: 'alternatives_card',
        card_status: 'pending',
      }],
    };
    useCopilotStore.getState().addMessage(msg);
    useCopilotStore.getState().updateUIActionStatus('msg-3', 0, 'resolved');
    const action = useCopilotStore.getState().messages[0].uiActions![0];
    expect(action.card_status).toBe('resolved');
  });

  it('updateUIActionStatus is no-op for non-existent message', () => {
    useCopilotStore.getState().updateUIActionStatus('non-existent', 0, 'resolved');
    expect(useCopilotStore.getState().messages).toHaveLength(0);
  });
});
```

- [ ] Run test to verify it fails:

```bash
cd frontend && npx vitest run src/features/copilot/__tests__/copilot-store.test.ts
```

Expected: FAIL — `alternatives_card` not in UIAction type; `updateUIActionStatus` doesn't exist

### Step 4.2: Extend UIAction type with interview card types

- [ ] In `frontend/src/features/copilot/store/copilot-store.ts`, update the `UIAction` interface:

Replace the `type` line and add interview-specific optional fields:

```typescript
export interface UIAction {
  type: "navigate" | "scroll_to_field" | "open_form" | "proposal" | "procedure_progress"
       | "metric_summary" | "comparison" | "checklist" | "multi_option"
       | "alternatives_card" | "clarify_card" | "checkpoint_card" | "interview_complete"
       | "preview_update";
  route?: string;
  page_label?: string;
  section_id?: string;
  field_id?: string;
  form_id?: string;
  prefill_data?: Record<string, unknown>;
  updates?: ProposalUpdate[];
  // Procedure progress fields
  procedure_id?: string;
  procedure_name?: string;
  steps?: ProcedureStepStatus[];
  current_step_index?: number;
  // Generative UI fields (Phase 3)
  metrics?: Array<{ label: string; value: string; trend?: "up" | "down" | "flat"; delta?: string }>;
  columns?: string[];
  rows?: Array<Record<string, string>>;
  recommended?: string;
  items?: Array<{ label: string; done: boolean; route?: string }>;
  options?: Array<{ id: string; title: string; content: string }>;
  // Interview card fields
  field_path?: string;
  question?: string;
  alternatives?: Array<{ id: string; title: string; description: string; recommended?: boolean; recommendation_reason?: string }>;
  allow_custom?: boolean;
  clarify_items?: Array<{ field_path: string; issue: string; options: string[] }>;
  block_id?: string;
  block_label?: string;
  summary?: Record<string, string>;
  health_score?: number;
  blocks_progress?: { completed: number; total: number };
  card_status?: "pending" | "resolved" | "confirmed" | "revising";
  redirect?: string;
  delta?: Record<string, unknown>;
}
```

### Step 4.3: Add updateUIActionStatus to store

- [ ] In `frontend/src/features/copilot/store/copilot-store.ts`, add to the `CopilotState` interface (after `addUIActionToLastAssistant`):

```typescript
  updateUIActionStatus: (messageId: string, actionIndex: number, status: string) => void;
```

- [ ] Add the implementation in the store creation (after the `addUIActionToLastAssistant` implementation):

```typescript
  updateUIActionStatus: (messageId, actionIndex, status) =>
    set((s) => {
      const msgs = [...s.messages];
      const msgIdx = msgs.findIndex((m) => m.id === messageId);
      if (msgIdx === -1) return s;
      const msg = msgs[msgIdx];
      if (!msg.uiActions || !msg.uiActions[actionIndex]) return s;
      const actions = [...msg.uiActions];
      actions[actionIndex] = { ...actions[actionIndex], card_status: status as UIAction["card_status"] };
      msgs[msgIdx] = { ...msg, uiActions: actions };
      return { messages: msgs };
    }),
```

### Step 4.4: Update types/index.ts re-exports

- [ ] In `frontend/src/features/copilot/types/index.ts`, verify all types are re-exported (no change needed if UIAction is already exported — it is).

- [ ] Run tests:

```bash
cd frontend && npx vitest run src/features/copilot/__tests__/copilot-store.test.ts
```

Expected: PASS

### Step 4.5: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/store/copilot-store.ts src/features/copilot/types/index.ts --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/store/copilot-store.ts frontend/src/features/copilot/types/index.ts frontend/src/features/copilot/__tests__/copilot-store.test.ts
git commit -m "feat(copilot): extend UIAction with interview card types + updateUIActionStatus"
```

---

## Task 5: Frontend — Extend CopilotChatPayload + interview-api

**Files:**
- Modify: `frontend/src/features/copilot/api/copilot-api.ts:6-15`
- Modify: `frontend/src/features/copilot/api/interview-api.ts`

### Step 5.1: Add focus + interview_session_id to CopilotChatPayload

- [ ] In `frontend/src/features/copilot/api/copilot-api.ts`, update the `CopilotChatPayload` interface:

```typescript
export interface CopilotChatPayload {
  message: string;
  conversation_id?: string | null;
  context?: {
    current_route?: string | null;
    selected_fields?: Array<Record<string, string>>;
    form_data?: Record<string, unknown>;
    locale?: string;
    focus?: {
      domain: string;
      entity_id?: string | null;
    } | null;
    interview_session_id?: string | null;
  };
}
```

### Step 5.2: Add entity_id to startInterview

- [ ] In `frontend/src/features/copilot/api/interview-api.ts`, update `startInterview`:

Replace:
```typescript
export async function startInterview(token: string, domain: string = "brand"): Promise<StartInterviewResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ domain }),
  });
  return res.json() as Promise<StartInterviewResponse>;
}
```

With:
```typescript
export async function startInterview(
  token: string,
  domain: string = "brand",
  entityId?: string,
): Promise<StartInterviewResponse> {
  const body: Record<string, unknown> = { domain };
  if (entityId) body.entity_id = entityId;
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  return res.json() as Promise<StartInterviewResponse>;
}
```

### Step 5.3: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/api/copilot-api.ts src/features/copilot/api/interview-api.ts --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/api/copilot-api.ts frontend/src/features/copilot/api/interview-api.ts
git commit -m "feat(copilot): extend payload with focus/interview_session_id + entity_id in startInterview"
```

---

## Task 6: Frontend — CopilotChat Uses CopilotInput

**Files:**
- Modify: `frontend/src/features/copilot/components/CopilotChat.tsx:27,67-78,137-171`

### Step 6.1: Replace textarea with CopilotInput

- [ ] In `frontend/src/features/copilot/components/CopilotChat.tsx`, add the import at the top:

```typescript
import { CopilotInput } from "./copilot-input";
```

- [ ] Remove the `input` state variable (line ~27):

Delete:
```typescript
const [input, setInput] = useState("");
```

- [ ] Remove the `handleSubmit` and `handleKeyDown` functions (lines ~67-78).

- [ ] Replace the entire textarea + buttons section (lines ~137-171) with:

```typescript
        <CopilotInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="Escribe tu mensaje..."
        />
```

- [ ] Remove unused imports: `useState` (if no longer used), any textarea-related refs.

- [ ] Verify the stop button is handled. CopilotInput has its own stop mechanism, but if `CopilotChat` also needs a stop button, check if it's shown via `isLoading` state. The `CopilotInput` component does NOT have a stop button — it only has send. So keep the stop functionality if it exists elsewhere, or add it.

Actually, looking at the current CopilotChat, the stop button is inside the textarea section. Since CopilotInput doesn't expose stop, add it after CopilotInput:

```typescript
        <div className="border-t border-slate-200 p-3 dark:border-slate-700">
          <CopilotInput
            onSend={sendMessage}
            disabled={isLoading}
            placeholder="Escribe tu mensaje..."
          />
          {isLoading && (
            <button
              onClick={stopStreaming}
              className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-700"
            >
              Detener
            </button>
          )}
        </div>
```

### Step 6.2: Verify build compiles

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: No new errors

### Step 6.3: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/components/CopilotChat.tsx --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/components/CopilotChat.tsx
git commit -m "feat(copilot): replace CopilotChat textarea with CopilotInput component"
```

---

## Task 7: Frontend — useCopilotChat Absorbs useInterviewChat

**Files:**
- Modify: `frontend/src/features/copilot/hooks/useCopilotChat.ts`

This is the most complex task. The hook becomes mode-aware: when `interviewSessionId` is set in the store, it includes it in the payload context and handles interview-specific UIActions.

### Step 7.1: Implement the merged useCopilotChat

- [ ] Rewrite `frontend/src/features/copilot/hooks/useCopilotChat.ts`:

```typescript
"use client";

import { useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore, type UIAction } from "../store/copilot-store";
import { streamCopilotChat, reportCopilotEvent } from "../api/copilot-api";

/**
 * Unified chat hook for all copilot modes (chat, focus, interview).
 *
 * Mode is determined by the store state:
 * - interviewSessionId set → Interview mode
 * - focusEntity set → Focus mode
 * - Neither → Chat mode
 *
 * All messages go through POST /copilot/chat with mode context in the payload.
 */
export function useCopilotChat() {
  const conversationId = useCopilotStore((s) => s.conversationId);
  const currentRoute = useCopilotStore((s) => s.currentRoute);

  const { getToken } = useAuth();

  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const store = useCopilotStore.getState();

      // Open panel if not already
      store.openPanel();

      // Add user message
      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: text.trim(),
        timestamp: Date.now(),
      };
      store.addMessage(userMsg);

      // Create placeholder assistant message for streaming
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant" as const,
        content: "",
        timestamp: Date.now(),
      };
      store.addMessage(assistantMsg);

      // Abort any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      store.setStatus("thinking");

      try {
        const token = await getToken();
        if (!token) {
          store.appendToLastAssistant("\n\n_Error: No se pudo obtener el token de autenticación._");
          store.setStatus("idle");
          return;
        }

        // Collect fresh field values from mounted WithCopilot components
        window.dispatchEvent(new CustomEvent("copilot:collect-values"));
        const freshState = useCopilotStore.getState();
        const freshFields = freshState.selectedFields;
        const currentMessages = freshState.messages;

        // Track message_sent event
        const mode = freshState.interviewSessionId ? "interview"
          : freshState.focusEntity ? "focus" : "chat";
        reportCopilotEvent("message_sent", {
          message_length: text.trim().length,
          has_selected_fields: freshFields.length > 0,
          is_first_message: currentMessages.length <= 2,
          mode,
        }, token);

        await streamCopilotChat(
          {
            message: text.trim(),
            conversation_id: conversationId,
            context: {
              current_route: currentRoute,
              selected_fields: freshFields.map((f) => ({
                field_id: f.fieldId,
                field_label: f.fieldLabel,
                field_value: f.fieldValue,
              })),
              locale: "es",
              focus: freshState.focusEntity ? {
                domain: freshState.focusEntity.domain,
                entity_id: freshState.focusEntity.entityId ?? null,
              } : null,
              interview_session_id: freshState.interviewSessionId ?? null,
            },
          },
          {
            onTextChunk: (content) => {
              useCopilotStore.getState().appendToLastAssistant(content);
            },
            onStatus: (state) => {
              useCopilotStore.getState().setStatus(state as "idle" | "thinking" | "streaming" | "done");
            },
            onDone: (convId) => {
              useCopilotStore.getState().setConversationId(convId);
              useCopilotStore.getState().setStatus("idle");
            },
            onError: (message) => {
              useCopilotStore.getState().appendToLastAssistant(`\n\n_Error: ${message}_`);
              useCopilotStore.getState().setStatus("idle");
            },
            onToolStart: (tool) => {
              useCopilotStore.getState().appendToLastAssistant(`\n🔧 _${tool}..._\n`);
            },
            onToolResult: () => {
              // Tool result feeds back into the LLM via subsequent text_chunk
            },
            onUIAction: (action) => {
              _handleUIAction(action as unknown as UIAction);
            },
          },
          token,
          controller.signal,
        );
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          useCopilotStore.getState().appendToLastAssistant("\n\n_Error de conexión. Intenta de nuevo._");
          useCopilotStore.getState().setStatus("idle");
        }
      }
    },
    [conversationId, currentRoute, getToken],
  );

  const sendCardAction = useCallback(
    async (messageId: string, actionIndex: number, text: string) => {
      // Update card status to resolved before sending
      useCopilotStore.getState().updateUIActionStatus(messageId, actionIndex, "resolved");
      await sendMessage(text);
    },
    [sendMessage],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    useCopilotStore.getState().setStatus("idle");
  }, []);

  return { sendMessage, sendCardAction, stopStreaming };
}

/**
 * Route UIAction based on type.
 * Interview-specific actions get special handling.
 */
function _handleUIAction(action: UIAction): void {
  const store = useCopilotStore.getState();

  switch (action.type) {
    // Silent: update preview data, don't show as card
    case "preview_update":
      if (action.delta) {
        store.updatePreviewData(action.delta);
      }
      return;

    // Interview complete: attach card + clear interview state
    case "interview_complete":
      store.addUIActionToLastAssistant(action);
      store.clearInterview();
      return;

    // Navigation: attach card + enqueue for router
    case "navigate":
      store.addUIActionToLastAssistant(action);
      store.enqueuUIAction(action);
      return;

    // Procedure progress: update store for stepper
    case "procedure_progress":
      store.addUIActionToLastAssistant(action);
      if (action.procedure_id && action.steps) {
        store.setActiveProcedure({
          id: action.procedure_id,
          name: action.procedure_name || action.procedure_id,
          steps: action.steps,
          currentStepIndex: action.current_step_index ?? 0,
        });
      }
      return;

    // All other types (proposal, alternatives_card, clarify_card, checkpoint_card, etc.)
    default:
      store.addUIActionToLastAssistant(action);
      return;
  }
}
```

### Step 7.2: Verify TypeScript compiles

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: No new errors

### Step 7.3: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/hooks/useCopilotChat.ts --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/hooks/useCopilotChat.ts
git commit -m "feat(copilot): useCopilotChat absorbs interview mode (unified hook)"
```

---

## Task 8: Frontend — AssistantMessage Renders Interview Cards

**Files:**
- Modify: `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`
- Create: `frontend/src/features/copilot/__tests__/assistant-message-cards.test.tsx`

### Step 8.1: Write failing test for interview card rendering

- [ ] Create `frontend/src/features/copilot/__tests__/assistant-message-cards.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AssistantMessage } from '../components/messages/AssistantMessage';
import type { CopilotMessage } from '../store/copilot-store';

// Mock card components to verify they're rendered
vi.mock('../components/cards/alternatives-card', () => ({
  AlternativesCard: (props: Record<string, unknown>) => (
    <div data-testid="alternatives-card" data-field-path={props.fieldPath}>
      Alternatives
    </div>
  ),
}));

vi.mock('../components/cards/clarify-card', () => ({
  ClarifyCard: (props: Record<string, unknown>) => (
    <div data-testid="clarify-card">Clarify</div>
  ),
}));

vi.mock('../components/cards/checkpoint-card', () => ({
  CheckpointCard: (props: Record<string, unknown>) => (
    <div data-testid="checkpoint-card" data-block-id={props.blockId}>
      Checkpoint
    </div>
  ),
}));

vi.mock('../components/cards/interview-complete-card', () => ({
  InterviewCompleteCard: (props: Record<string, unknown>) => (
    <div data-testid="interview-complete-card">Complete</div>
  ),
}));

describe('AssistantMessage interview cards', () => {
  it('renders alternatives_card UIAction', () => {
    const msg: CopilotMessage = {
      id: 'msg-1',
      role: 'assistant',
      content: 'Options:',
      timestamp: Date.now(),
      uiActions: [{
        type: 'alternatives_card',
        field_path: 'strategy.avatar',
        question: 'Who is your target?',
        alternatives: [
          { id: '1', title: 'Opt A', description: 'Desc A', recommended: true },
        ],
        allow_custom: true,
        card_status: 'pending',
      }],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId('alternatives-card')).toBeDefined();
  });

  it('renders checkpoint_card UIAction', () => {
    const msg: CopilotMessage = {
      id: 'msg-2',
      role: 'assistant',
      content: 'Block done!',
      timestamp: Date.now(),
      uiActions: [{
        type: 'checkpoint_card',
        block_id: 'strategy',
        block_label: 'Estrategia',
        summary: { name: 'Test' },
        health_score: 90,
        blocks_progress: { completed: 1, total: 5 },
        card_status: 'pending',
      }],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId('checkpoint-card')).toBeDefined();
  });

  it('renders interview_complete UIAction', () => {
    const msg: CopilotMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Done!',
      timestamp: Date.now(),
      uiActions: [{
        type: 'interview_complete',
        health_score: 95,
        redirect: '/brand-studio',
      }],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId('interview-complete-card')).toBeDefined();
  });

  it('does not render preview_update (silent action)', () => {
    const msg: CopilotMessage = {
      id: 'msg-4',
      role: 'assistant',
      content: 'Noted.',
      timestamp: Date.now(),
      uiActions: [{
        type: 'preview_update',
        delta: { name: 'Test' },
      }],
    };
    render(<AssistantMessage message={msg} />);
    // preview_update should not render any card
    expect(screen.queryByTestId('alternatives-card')).toBeNull();
    expect(screen.queryByTestId('checkpoint-card')).toBeNull();
  });

  it('renders generic cards alongside interview cards', () => {
    const msg: CopilotMessage = {
      id: 'msg-5',
      role: 'assistant',
      content: 'Mixed!',
      timestamp: Date.now(),
      uiActions: [
        { type: 'alternatives_card', field_path: 'x', card_status: 'pending' },
        { type: 'proposal', updates: [{ field_id: 'name', new_value: 'Test' }] },
      ],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId('alternatives-card')).toBeDefined();
  });
});
```

- [ ] Run test to verify it fails:

```bash
cd frontend && npx vitest run src/features/copilot/__tests__/assistant-message-cards.test.tsx
```

Expected: FAIL — `alternatives_card` not matched in switch statement

### Step 8.2: Add interview card rendering to AssistantMessage

- [ ] In `frontend/src/features/copilot/components/messages/AssistantMessage.tsx`, add imports:

```typescript
import { AlternativesCard } from "../cards/alternatives-card";
import { ClarifyCard } from "../cards/clarify-card";
import { CheckpointCard } from "../cards/checkpoint-card";
import { InterviewCompleteCard } from "../cards/interview-complete-card";
```

- [ ] In the switch statement inside the `uiActions.map()`, add cases before `default`:

```typescript
              case "alternatives_card":
                return action.alternatives ? (
                  <AlternativesCard
                    key={`alt-${idx}`}
                    fieldPath={action.field_path ?? ""}
                    question={action.question ?? ""}
                    alternatives={action.alternatives}
                    allowCustom={action.allow_custom ?? false}
                    onSelect={() => {}}
                    onCustom={() => {}}
                    status={action.card_status ?? "pending"}
                  />
                ) : null;
              case "clarify_card":
                return action.clarify_items ? (
                  <ClarifyCard
                    key={`clarify-${idx}`}
                    items={action.clarify_items}
                    onResolve={() => {}}
                    status={action.card_status ?? "pending"}
                  />
                ) : null;
              case "checkpoint_card":
                return (
                  <CheckpointCard
                    key={`checkpoint-${idx}`}
                    blockId={action.block_id ?? ""}
                    blockLabel={action.block_label ?? ""}
                    summary={action.summary ?? {}}
                    healthScore={action.health_score ?? 0}
                    blocksProgress={action.blocks_progress ?? { completed: 0, total: 0 }}
                    onConfirm={() => {}}
                    onRevise={() => {}}
                    status={action.card_status ?? "pending"}
                  />
                );
              case "interview_complete":
                return (
                  <InterviewCompleteCard
                    key={`complete-${idx}`}
                    healthScore={action.health_score ?? 0}
                    redirect={action.redirect ?? "/"}
                  />
                );
              case "preview_update":
                return null;  // Silent — handled in useCopilotChat, not rendered
```

**NOTE:** The `onSelect`, `onResolve`, `onConfirm`, `onRevise` handlers are passed as no-ops here. They will be wired to `sendCardAction` in the next integration step when `AssistantMessage` receives callback props. For Phase 1, the cards render correctly and the card action callbacks will be connected via a thin wrapper pattern or context. This can be deferred to the integration step because the interview currently works through `InterviewSplitView` which has its own card handling — Phase 1 just ensures AssistantMessage CAN render them.

- [ ] Run test:

```bash
cd frontend && npx vitest run src/features/copilot/__tests__/assistant-message-cards.test.tsx
```

Expected: PASS

### Step 8.3: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/components/messages/AssistantMessage.tsx --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/components/messages/AssistantMessage.tsx frontend/src/features/copilot/__tests__/assistant-message-cards.test.tsx
git commit -m "feat(copilot): AssistantMessage renders interview cards (alternatives, clarify, checkpoint, complete)"
```

---

## Task 9: Frontend — Deprecate useInterviewChat

**Files:**
- Modify: `frontend/src/features/copilot/hooks/useInterviewChat.ts`

### Step 9.1: Replace useInterviewChat with thin wrapper

The `InterviewSplitView` still uses `useInterviewChat` until Phase 3 replaces it. We keep the same interface but delegate to `useCopilotChat` internally.

- [ ] Rewrite `frontend/src/features/copilot/hooks/useInterviewChat.ts`:

```typescript
"use client";

/**
 * @deprecated Use useCopilotChat instead. This wrapper exists for backward
 * compatibility with InterviewSplitView until Phase 3 replaces it.
 *
 * All interview chat now goes through the unified /copilot/chat endpoint
 * with interview_session_id in the context payload.
 */

import { useEffect, useCallback } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useCopilotChat } from "./useCopilotChat";

// Re-export interview-specific types for backward compatibility
export type InterviewUIActionType =
  | "preview_update"
  | "alternatives_card"
  | "clarify_card"
  | "checkpoint_card"
  | "interview_complete";

export type InterviewStatus = "idle" | "thinking" | "streaming";

export interface InterviewMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  uiActions?: Array<Record<string, unknown>>;
}

export function useInterviewChat(
  sessionId: string | null,
  conversationId: string | null,
) {
  const { sendMessage: _send, sendCardAction: _sendCardAction, stopStreaming } = useCopilotChat();

  // Sync sessionId and conversationId into the store
  useEffect(() => {
    if (sessionId) {
      useCopilotStore.getState().setInterviewSession(sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    if (conversationId) {
      useCopilotStore.getState().setConversationId(conversationId);
    }
  }, [conversationId]);

  // Map store messages to InterviewMessage shape
  const messages = useCopilotStore((s) =>
    s.messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      uiActions: m.uiActions as Array<Record<string, unknown>> | undefined,
    })),
  );

  const status = useCopilotStore((s) => {
    if (s.status === "done") return "idle" as InterviewStatus;
    return s.status as InterviewStatus;
  });

  const sendMessage = useCallback(
    async (text: string) => {
      await _send(text);
    },
    [_send],
  );

  const sendCardAction = useCallback(
    async (text: string) => {
      // For backward compat, sendCardAction without messageId/actionIndex
      // just sends the text as a regular message
      await _send(text);
    },
    [_send],
  );

  const addInitialMessage = useCallback((content: string) => {
    useCopilotStore.getState().addMessage({
      id: crypto.randomUUID(),
      role: "assistant",
      content,
      timestamp: Date.now(),
    });
  }, []);

  return {
    messages,
    status,
    sendMessage,
    sendCardAction,
    stopStreaming,
    addInitialMessage,
  };
}
```

### Step 9.2: Verify existing interview tests still compile

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -i "useInterviewChat\|interview-split" | head -20
```

If there are type errors from consumers, fix the import paths. The key consumers are:
- `frontend/src/features/copilot/components/interview/interview-split-view.tsx` — imports `useInterviewChat`
- `frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts` — tests the hook

### Step 9.3: Update useInterviewChat test

- [ ] Check if the existing test at `frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts` needs updates. If it imports internal types that changed, update the imports. The test should still pass since the public API is preserved.

```bash
cd frontend && npx vitest run src/features/copilot/hooks/__tests__/useInterviewChat.test.ts 2>&1 | tail -20
```

If tests fail, adjust type imports to match the new thin wrapper's exports.

### Step 9.4: Lint + commit

```bash
cd frontend && npx eslint src/features/copilot/hooks/useInterviewChat.ts --no-error-on-unmatched-pattern
git add frontend/src/features/copilot/hooks/useInterviewChat.ts
git commit -m "refactor(copilot): deprecate useInterviewChat — thin wrapper over useCopilotChat"
```

---

## Task 10: Integration — Full Test Suite

**Files:** None (verification only)

### Step 10.1: Run full backend test suite

- [ ] Run:

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short
```

Expected: All pass, no lint errors

### Step 10.2: Run full frontend test suite

- [ ] Run:

```bash
cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run
```

Expected: All pass, no type errors, no lint errors

### Step 10.3: Run architecture tests

- [ ] Run:

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
```

Expected: All pass

### Step 10.4: Final commit (if any fixes were needed)

```bash
git add -p  # Stage only the fix files
git commit -m "fix(copilot): Phase 1 integration fixes"
```

---

## Summary: What Phase 1 Delivers

| Before | After |
|--------|-------|
| Interview chat calls non-existent endpoint | All chat via `/copilot/chat` with mode context |
| System prompt ignores interview session | Layered prompt: base + focus + interview |
| Tools selected only by route | Tools selected by mode (interview overrides route) |
| Sidebar has no audio/file upload | CopilotInput with mic + attachments |
| Interview messages in local useState | All messages in Zustand store |
| AssistantMessage ignores interview cards | Renders alternatives, clarify, checkpoint, complete |
| StartInterviewRequest has no entity_id | entity_id connects offer to interview |
| useCopilotChat and useInterviewChat separate | Single unified hook, deprecated wrapper |
