# Unified Copilot — Phase 0: Foundations

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lay the backend and frontend foundations for the unified copilot without changing any visible behavior. Every existing feature continues working identically.

**Architecture:** Extend the existing copilot infrastructure with focus/interview context fields (backend DTO + state), fix the critical interview system prompt gap, add field_path validation, implement context window budgeting, make extract_structured global, add revert_to_block, and prepare the frontend store + unified input component + lazy preview registry.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, LangGraph, Jinja2 (backend) | TypeScript, React 18, Zustand, Vitest (frontend)

**Spec:** `docs/superpowers/specs/2026-04-13-unified-copilot-design.md`

**Execution notes:**
- Each task should be rethought before implementation — research better approaches if something feels wrong
- At the end of Phase 0, produce `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md` with discoveries and recommendations
- Follow all active rules: ruff, eslint, DDD, FSD, TDD, tenant isolation, Spanish accents
- Two parallel agents: Agent A (backend tasks 1-7), Agent B (frontend tasks 8-13)

---

## Backend Tasks (Agent A)

### Task 1: Extend ClientContext with focus and interview_session_id

**Files:**
- Modify: `backend/src/modules/copilot/application/orchestrator/state.py` (lines 10-17)
- Test: `backend/tests/modules/copilot/test_copilot_state.py` (create)

- [ ] **Step 1: Write test for extended ClientContext**

```python
# backend/tests/modules/copilot/test_copilot_state.py
"""Tests for CopilotState and ClientContext type definitions."""

from src.modules.copilot.application.orchestrator.state import (
    ClientContext,
    FocusContext,
)


class TestFocusContext:
    """Tests for the FocusContext TypedDict."""

    def test_focus_context_with_entity_id(self) -> None:
        ctx: FocusContext = {
            "domain": "offer",
            "entity_id": "730e7f7a-43b9-495e-bf05-49700135d324",
        }
        assert ctx["domain"] == "offer"
        assert ctx["entity_id"] == "730e7f7a-43b9-495e-bf05-49700135d324"

    def test_focus_context_without_entity_id(self) -> None:
        ctx: FocusContext = {"domain": "brand"}
        assert ctx["domain"] == "brand"
        assert "entity_id" not in ctx

    def test_client_context_with_focus(self) -> None:
        ctx: ClientContext = {
            "current_route": "/offer-studio/offer/123",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "focus": {"domain": "offer", "entity_id": "123"},
        }
        assert ctx["focus"]["domain"] == "offer"

    def test_client_context_with_interview(self) -> None:
        ctx: ClientContext = {
            "current_route": "/offer-studio/offer/123",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "interview_session_id": "abc-def-123",
        }
        assert ctx["interview_session_id"] == "abc-def-123"

    def test_client_context_backward_compatible(self) -> None:
        """Existing code that doesn't send focus/interview still works."""
        ctx: ClientContext = {
            "current_route": "/brand-studio",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        }
        assert ctx.get("focus") is None
        assert ctx.get("interview_session_id") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_copilot_state.py -x -q --tb=short`
Expected: FAIL — `FocusContext` not importable

- [ ] **Step 3: Implement FocusContext and extend ClientContext**

In `backend/src/modules/copilot/application/orchestrator/state.py`, add `FocusContext` TypedDict and extend `ClientContext`:

```python
class FocusContext(TypedDict, total=False):
    """Focus context sent when the user activates Focus or Interview mode."""

    domain: str  # "offer", "brand", "buyer_persona"
    entity_id: str  # UUID of the focused entity (omit for brand singleton)


class ClientContext(TypedDict, total=False):
    """Context sent from the frontend with each message."""

    current_route: str  # e.g. "/brand-studio/positioning"
    selected_fields: list[dict[str, str]]  # [{field_id, field_label, field_value}]
    form_data: dict[str, Any]  # Current form snapshot (partial)
    locale: str  # e.g. "es"
    focus: FocusContext  # Active when Focus or Interview mode is on
    interview_session_id: str  # Active interview session UUID
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_copilot_state.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/application/orchestrator/state.py --no-cache`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/application/orchestrator/state.py backend/tests/modules/copilot/test_copilot_state.py
git commit -m "feat(copilot): add FocusContext and extend ClientContext with focus/interview fields"
```

---

### Task 2: Fix critical gap — wire interview system prompt into build_system_prompt

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_focus.j2`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2`
- Modify: `backend/src/modules/copilot/application/orchestrator/graph.py` (lines 193-262, build_system_prompt)
- Test: `backend/tests/modules/copilot/test_prompt_layers.py` (create)

- [ ] **Step 1: Write tests for layered prompt composition**

```python
# backend/tests/modules/copilot/test_prompt_layers.py
"""Tests for layered system prompt composition."""

from unittest.mock import MagicMock, patch

from src.modules.copilot.application.orchestrator.graph import build_system_prompt


class TestBuildSystemPrompt:
    """Tests for the build_system_prompt function."""

    def _make_state(self, **overrides):
        base = {
            "user_id": "user-1",
            "tenant_id": "tenant-1",
            "client_context": {
                "current_route": "/brand-studio",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            },
            "messages": [],
            "conversation_id": "conv-1",
            "pending_ui_actions": [],
            "active_tool_names": [],
            "active_procedure": None,
            "error": None,
        }
        base.update(overrides)
        return base

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_chat_mode_returns_base_only(self, mock_behavior, mock_completion):
        """When no focus or interview, only base prompt is returned."""
        mock_completion.return_value = "## Completion\nAll modules OK"
        mock_behavior.return_value = "User is new"
        state = self._make_state()

        result = build_system_prompt(state)

        assert "Copilot" in result or "copilot" in result
        assert "FOCUS MODE" not in result
        assert "INTERVIEW MODE" not in result

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_focus_mode_includes_focus_layer(self, mock_behavior, mock_completion):
        """When focus context is present, focus layer is appended."""
        mock_completion.return_value = ""
        mock_behavior.return_value = ""
        state = self._make_state(
            client_context={
                "current_route": "/offer-studio/offer/123",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
                "focus": {"domain": "offer", "entity_id": "123"},
            },
            focus_entity_data={"name": "Curso Premium", "pricing": []},
        )

        result = build_system_prompt(state)

        assert "FOCUS MODE" in result or "focus" in result.lower()

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_interview_mode_includes_interview_layer(self, mock_behavior, mock_completion):
        """When interview session is present, interview layer is appended."""
        mock_completion.return_value = ""
        mock_behavior.return_value = ""
        mock_session = MagicMock()
        mock_session.bloque_actual = "promise"
        mock_session.mapa_global = {"strategy.offer_name": "Test"}
        mock_session.bloques_completados = ["strategy"]
        mock_session.config_snapshot = {
            "bloques": [
                {"id": "strategy", "label": "Estrategia"},
                {"id": "promise", "label": "Promesa"},
            ],
            "expertise_template": "offer",
        }
        mock_session.coverage_for_block.return_value = 0.5

        state = self._make_state(
            client_context={
                "current_route": "/offer-studio/offer/123",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
                "focus": {"domain": "offer", "entity_id": "123"},
                "interview_session_id": "session-1",
            },
            interview_session=mock_session,
        )

        result = build_system_prompt(state)

        assert "INTERVIEW" in result or "interview" in result.lower()
        assert "promise" in result.lower() or "Promesa" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_prompt_layers.py -x -q --tb=short`
Expected: FAIL — focus/interview not handled in build_system_prompt

- [ ] **Step 3: Create focus prompt template**

```jinja2
{# backend/src/modules/copilot/infrastructure/prompts/templates/copilot_focus.j2 #}

--- FOCUS MODE ACTIVE ---
Domain: {{ domain }}
{% if entity_id %}Entity ID: {{ entity_id }}{% endif %}

Current entity state:
{{ entity_snapshot | tojson(indent=2) }}

{% if empty_fields %}
Empty fields that need completion:
{% for field in empty_fields %}- {{ field }}
{% endfor %}
{% endif %}

CONSTRAINT: Every response must relate to this entity. If the user asks about
something unrelated, acknowledge briefly and redirect: "Eso es interesante,
pero ahora estamos enfocados en tu {{ domain_label }}. Cuando terminemos,
puedo ayudarte con eso."

When the user provides information, use entity_write to save it immediately.
When the user uploads files, use extract_from_document to process them against
ALL sections simultaneously.
--- END FOCUS MODE ---
```

- [ ] **Step 4: Create interview prompt template**

```jinja2
{# backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2 #}

--- INTERVIEW MODE ACTIVE ---
Current block: {{ current_block.label }} ({{ current_block.id }})
Progress: {{ blocks_completed | length }}/{{ total_blocks }} blocks completed
Coverage for current block: {{ (coverage * 100) | round }}%

{% if coverage >= 0.8 %}
HIGH COVERAGE: This block is mostly filled (from documents or earlier conversation).
Present a summary of what you have, ask if it's correct, and advance quickly.
Do NOT ask all questions — just confirm and adjust.
{% elif coverage > 0 %}
PARTIAL COVERAGE: Some fields are already filled.
Acknowledge what you have, ask ONLY for what's missing.
{% else %}
EMPTY BLOCK: Follow the full interview protocol for this block.
{% endif %}

Mapa global (accumulated data):
{{ mapa_global | tojson(indent=2) }}

{% if block_coverage_status %}
Coverage by block:
{% for block_id, cov in block_coverage_status.items() %}- {{ block_id }}: {{ (cov * 100) | round }}%
{% endfor %}
{% endif %}

FUNDAMENTAL RULES:
1. GLOBAL CAPTURE: Extract ALL data the user mentions to ANY section using
   extract_structured. The mapa_global is your memory.
2. NEVER REPEAT: Check mapa_global before asking. If you have a datum, do not
   ask again. Confirm briefly and ask ONLY what's missing.
3. VISIBLE INTELLIGENCE: When you capture data for another section, confirm
   briefly and return to the current topic.
4. ONE QUESTION AT A TIME: Ask one focused question per message. Wait for the
   answer before asking the next.
--- END INTERVIEW MODE ---
```

- [ ] **Step 5: Modify build_system_prompt to compose layers**

In `backend/src/modules/copilot/application/orchestrator/graph.py`, modify `build_system_prompt` (starting at line 193). Add the focus and interview layer logic after the base prompt rendering. The function should:

1. Render base `copilot_system` template (existing behavior, unchanged)
2. If `client_context.get("focus")` exists AND `state.get("focus_entity_data")` exists, render `copilot_focus` template and append
3. If `client_context.get("interview_session_id")` exists AND `state.get("interview_session")` exists, render `copilot_interview` template and append
4. Return the concatenated result

Add a helper `_get_all_blocks_coverage(session) -> dict[str, float]` that iterates all blocks in `config_snapshot["bloques"]` and calls `session.coverage_for_block(block_id)` for each.

For the domain label mapping, use: `{"offer": "oferta", "brand": "marca", "buyer_persona": "buyer persona"}`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_prompt_layers.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 7: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/application/orchestrator/graph.py --no-cache`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/application/orchestrator/graph.py backend/src/modules/copilot/infrastructure/prompts/templates/copilot_focus.j2 backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2 backend/tests/modules/copilot/test_prompt_layers.py
git commit -m "feat(copilot): layered system prompt with focus and interview context"
```

---

### Task 3: Add field_path validation to extract_structured

**Files:**
- Modify: `backend/src/modules/copilot/application/tools/interview/extract_structured.py` (lines 8-52)
- Modify: `backend/src/modules/copilot/domain/schema_introspection.py` (add validate_field_path)
- Test: `backend/tests/modules/copilot/test_extract_validation.py` (create)

- [ ] **Step 1: Write test for field_path validation**

```python
# backend/tests/modules/copilot/test_extract_validation.py
"""Tests for field_path validation in extract_structured."""

from src.modules.copilot.domain.schema_introspection import validate_field_path


class TestValidateFieldPath:
    """Tests for the validate_field_path function."""

    def test_valid_brand_field(self) -> None:
        assert validate_field_path("brand", "identity.brand_name") is True

    def test_valid_brand_top_level(self) -> None:
        assert validate_field_path("brand", "identity") is True

    def test_invalid_brand_field(self) -> None:
        assert validate_field_path("brand", "nonexistent.field") is False

    def test_valid_offer_field(self) -> None:
        assert validate_field_path("offer", "headline_promise") is True

    def test_invalid_offer_field(self) -> None:
        assert validate_field_path("offer", "totally_fake_field") is False

    def test_unknown_domain(self) -> None:
        assert validate_field_path("unknown_domain", "any.field") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_extract_validation.py -x -q --tb=short`
Expected: FAIL — `validate_field_path` not defined

- [ ] **Step 3: Implement validate_field_path**

Add to `backend/src/modules/copilot/domain/schema_introspection.py` after the existing functions. The function should:

1. Maintain a `DOMAIN_MODELS` dict mapping domain name to the Pydantic model class (import `BrandSettings` from brand module, `Offer` model or the OfferPersister's `PERSISTABLE_FIELDS` from the copilot persister)
2. For "brand": use `get_model_sections(BrandSettings)` and check if the first segment of `field_path` is a valid section name
3. For "offer": check against the offer persister's known field list (import `OfferPersister.PERSISTABLE_FIELDS` or use the Offer model)
4. Return `False` for unknown domains

Note: Read the actual `OfferPersister` and `BrandSettings` imports to determine the exact classes and field lists available. The implementation should be lazy (cache the sections on first call).

- [ ] **Step 4: Modify extract_structured to validate field paths**

In `backend/src/modules/copilot/application/tools/interview/extract_structured.py`, add validation before accepting each extraction. If `validate_field_path` returns False for a field_path, skip it and include it in a `skipped_fields` list in the return JSON so the LLM knows it used an invalid path.

- [ ] **Step 5: Run tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_extract_validation.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 6: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/domain/schema_introspection.py src/modules/copilot/application/tools/interview/extract_structured.py --no-cache`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/schema_introspection.py backend/src/modules/copilot/application/tools/interview/extract_structured.py backend/tests/modules/copilot/test_extract_validation.py
git commit -m "feat(copilot): add field_path validation to extract_structured"
```

---

### Task 4: Implement context window budget with history truncation

**Files:**
- Create: `backend/src/modules/copilot/application/orchestrator/context_budget.py`
- Modify: `backend/src/modules/copilot/application/orchestrator/graph.py` (agent_node, before LLM call)
- Test: `backend/tests/modules/copilot/test_context_budget.py` (create)

- [ ] **Step 1: Write tests for context budget**

```python
# backend/tests/modules/copilot/test_context_budget.py
"""Tests for context window budget and history truncation."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.modules.copilot.application.orchestrator.context_budget import (
    truncate_history,
)


class TestTruncateHistory:
    """Tests for the truncate_history function."""

    def test_short_history_unchanged(self) -> None:
        """Messages under budget are returned unchanged."""
        msgs = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
        result = truncate_history(msgs, max_tokens=15000)
        assert len(result) == 2

    def test_long_history_truncated(self) -> None:
        """Old messages are summarized when over budget."""
        msgs = []
        for i in range(30):
            msgs.append(HumanMessage(content=f"Message {i} " + "x" * 200))
            msgs.append(AIMessage(content=f"Reply {i} " + "y" * 200))
        result = truncate_history(msgs, max_tokens=5000)
        # Should have fewer messages than input
        assert len(result) < len(msgs)
        # Last 3 turns (6 messages) should be preserved exactly
        assert result[-1].content == msgs[-1].content
        assert result[-2].content == msgs[-2].content

    def test_preserves_last_n_turns(self) -> None:
        """The last 3 turns are always kept intact."""
        msgs = [
            HumanMessage(content="Old message " + "x" * 1000),
            AIMessage(content="Old reply " + "y" * 1000),
            HumanMessage(content="Recent 1"),
            AIMessage(content="Reply 1"),
            HumanMessage(content="Recent 2"),
            AIMessage(content="Reply 2"),
            HumanMessage(content="Current"),
            AIMessage(content="Current reply"),
        ]
        result = truncate_history(msgs, max_tokens=500)
        # Last 6 messages (3 turns) preserved
        assert any("Current" in m.content for m in result)
        assert any("Recent 2" in m.content for m in result)

    def test_tool_messages_in_last_turn_preserved(self) -> None:
        """Tool messages within the last turn are kept."""
        msgs = [
            HumanMessage(content="Old " + "x" * 1000),
            AIMessage(content="Old reply"),
            HumanMessage(content="Use tool"),
            AIMessage(content="", tool_calls=[{"name": "test", "args": {}, "id": "1"}]),
            ToolMessage(content="Tool result", tool_call_id="1"),
            AIMessage(content="Based on the tool..."),
        ]
        result = truncate_history(msgs, max_tokens=500)
        tool_msgs = [m for m in result if isinstance(m, ToolMessage)]
        assert len(tool_msgs) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_context_budget.py -x -q --tb=short`
Expected: FAIL — module not found

- [ ] **Step 3: Implement context_budget.py**

Create `backend/src/modules/copilot/application/orchestrator/context_budget.py`:

The `truncate_history` function should:
1. Estimate tokens per message using `len(msg.content) // 4` (rough approximation, 1 token ~ 4 chars)
2. Always preserve the last 6 messages (3 turns) intact
3. If total exceeds `max_tokens`, create a `SystemMessage` summarizing the older messages (just: "Previous conversation covered: [list of topics]" based on first few words of each old message)
4. Return `[summary_message] + preserved_recent_messages`

Also export a `CONTEXT_BUDGET` dataclass with default values matching the spec.

- [ ] **Step 4: Integrate into agent_node**

In `graph.py` `agent_node` function (line ~284), before invoking the LLM, call `truncate_history(messages, CONTEXT_BUDGET.history)` on the conversation messages.

- [ ] **Step 5: Run tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_context_budget.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 6: Run full backend tests to verify no regression**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/application/orchestrator/context_budget.py backend/src/modules/copilot/application/orchestrator/graph.py backend/tests/modules/copilot/test_context_budget.py
git commit -m "feat(copilot): add context window budget with history truncation"
```

---

### Task 5: Add revert_to_block to InterviewSession

**Files:**
- Modify: `backend/src/modules/copilot/domain/interview_session.py` (after advance_block, line ~91)
- Create: `backend/src/modules/copilot/application/tools/interview/revert_to_block.py`
- Modify: `backend/src/modules/copilot/application/tools/interview/__init__.py` (add to INTERVIEW_TOOLS)
- Test: `backend/tests/modules/copilot/test_interview_session.py` (create or extend)

- [ ] **Step 1: Write test for revert_to_block domain method**

```python
# backend/tests/modules/copilot/test_interview_revert.py
"""Tests for InterviewSession.revert_to_block."""

import pytest

from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus


class TestRevertToBlock:
    """Tests for the revert_to_block method."""

    def _make_session(self) -> InterviewSession:
        config = {
            "domain": "offer",
            "bloques": [
                {"id": "strategy", "label": "Estrategia", "campos_objetivo": ["strategy.offer_name"]},
                {"id": "promise", "label": "Promesa", "campos_objetivo": ["promise.headline"]},
                {"id": "pricing", "label": "Precios", "campos_objetivo": ["pricing.total"]},
            ],
        }
        session = InterviewSession.create(
            tenant_id="t1",
            user_id="u1",
            config=config,
        )
        # Advance through first two blocks
        session.advance_block("strategy")
        session.advance_block("promise")
        return session

    def test_revert_to_earlier_block(self) -> None:
        session = self._make_session()
        assert session.bloque_actual == "pricing"
        assert "strategy" in session.bloques_completados
        assert "promise" in session.bloques_completados

        session.revert_to_block("strategy")

        assert session.bloque_actual == "strategy"
        assert session.bloques_completados == []

    def test_revert_to_middle_block(self) -> None:
        session = self._make_session()
        session.revert_to_block("promise")

        assert session.bloque_actual == "promise"
        assert session.bloques_completados == ["strategy"]

    def test_revert_to_invalid_block_raises(self) -> None:
        session = self._make_session()
        with pytest.raises(ValueError, match="not found"):
            session.revert_to_block("nonexistent")

    def test_revert_keeps_mapa_global(self) -> None:
        """Reverting does NOT clear accumulated data."""
        session = self._make_session()
        session.update_mapa_global({"strategy.offer_name": "Test"})
        session.revert_to_block("strategy")
        assert session.mapa_global["strategy.offer_name"] == "Test"

    def test_revert_sets_status_active(self) -> None:
        session = self._make_session()
        session.pause()
        assert session.status == InterviewStatus.PAUSED
        session.revert_to_block("strategy")
        assert session.status == InterviewStatus.ACTIVE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_revert.py -x -q --tb=short`
Expected: FAIL — `revert_to_block` not defined

- [ ] **Step 3: Implement revert_to_block on InterviewSession**

Add to `backend/src/modules/copilot/domain/interview_session.py` after the `advance_block` method:

```python
def revert_to_block(self, block_id: str) -> None:
    """Revert to a previous block, keeping mapa_global data intact."""
    bloques = self.config_snapshot["bloques"]
    block_ids = [b["id"] for b in bloques]
    if block_id not in block_ids:
        msg = f"Block '{block_id}' not found in interview config"
        raise ValueError(msg)
    target_idx = block_ids.index(block_id)
    self.bloques_completados = [
        b for b in self.bloques_completados
        if block_ids.index(b) < target_idx
    ]
    self.bloque_actual = block_id
    self.status = InterviewStatus.ACTIVE
```

- [ ] **Step 4: Create the revert_to_block tool**

Create `backend/src/modules/copilot/application/tools/interview/revert_to_block.py`:

```python
"""Tool to revert interview to a previous block."""

import json

from langchain_core.tools import tool


@tool
def revert_to_block(block_id: str) -> str:
    """Revert the interview to a previous block when the user wants to revisit it.

    Use this when the user says things like "volvamos a la promesa",
    "quiero cambiar lo de estrategia", "regresemos al pricing".

    Args:
        block_id: The ID of the block to revert to (e.g., "strategy", "promise").

    Returns:
        JSON confirming the revert with the new current block.
    """
    return json.dumps({
        "text": "",
        "ui_action": {
            "type": "block_reverted",
            "block_id": block_id,
        },
    })
```

- [ ] **Step 5: Register the tool**

Read `backend/src/modules/copilot/application/tools/interview/__init__.py` to understand the current `INTERVIEW_TOOLS` list, then add `revert_to_block` to it.

- [ ] **Step 6: Run tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_revert.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 7: Run lint + full copilot tests**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/ --no-cache && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_session.py backend/src/modules/copilot/application/tools/interview/revert_to_block.py backend/src/modules/copilot/application/tools/interview/__init__.py backend/tests/modules/copilot/test_interview_revert.py
git commit -m "feat(copilot): add revert_to_block for interview block navigation"
```

---

### Task 6: Make extract_structured global (not limited to current block)

**Files:**
- Modify: `backend/src/modules/copilot/application/tools/interview/extract_structured.py`
- Test: `backend/tests/modules/copilot/test_extract_global.py` (create)

This is primarily a **prompt/docstring change** + the validation from Task 3. The tool already accepts any field_path — the limitation was in the system prompt instructions, not in the code. The key change is updating the tool's docstring (which the LLM reads) to explicitly encourage cross-block extraction.

- [ ] **Step 1: Write test confirming cross-block extraction works**

```python
# backend/tests/modules/copilot/test_extract_global.py
"""Tests confirming extract_structured accepts fields from any block."""

import json

from src.modules.copilot.application.tools.interview.extract_structured import (
    extract_structured,
)


class TestExtractStructuredGlobal:
    """Tests for global (cross-block) extraction."""

    def test_extracts_fields_from_multiple_sections(self) -> None:
        result = extract_structured.invoke({
            "session_id": "test-session",
            "extractions": [
                {"field_path": "strategy.offer_name", "value": "Mi Curso", "confidence": 0.9},
                {"field_path": "pricing.total_amount", "value": 497, "confidence": 0.85},
                {"field_path": "promise.headline", "value": "Transforma tu negocio", "confidence": 0.95},
            ],
        })
        parsed = json.loads(result)
        delta = parsed["ui_action"]["delta"]
        assert "strategy.offer_name" in delta
        assert "pricing.total_amount" in delta
        assert "promise.headline" in delta

    def test_low_confidence_tracked(self) -> None:
        result = extract_structured.invoke({
            "session_id": "test-session",
            "extractions": [
                {"field_path": "psychology.urgency_triggers", "value": ["descuento"], "confidence": 0.6},
            ],
        })
        parsed = json.loads(result)
        confidence_map = parsed["ui_action"]["confidence_map"]
        assert "psychology.urgency_triggers" in confidence_map
        assert confidence_map["psychology.urgency_triggers"] == 0.6
```

- [ ] **Step 2: Run tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_extract_global.py -x -q --tb=short`
Expected: PASS (the code already accepts any field_path)

- [ ] **Step 3: Update extract_structured docstring for LLM**

Update the docstring in `extract_structured.py` to emphasize global extraction. The LLM reads this docstring as the tool description:

```python
@tool
def extract_structured(session_id: str, extractions: list[dict]) -> str:
    """Extract structured data from the conversation into the mapa_global.

    INVOKE THIS ON EVERY TURN where the user provides factual information.
    This tool is SILENT — the user does not see any text output.

    CRITICAL: Extract data for ANY section, not just the current block.
    If the user mentions pricing while you are on the promise block,
    extract the pricing data here. The mapa_global is your global memory.

    Args:
        session_id: The interview session UUID.
        extractions: List of extracted data items. Each has:
            - field_path: Dot-notation path (e.g., "strategy.offer_name",
              "pricing.total_amount", "program_details.total_sessions").
              Can be from ANY section regardless of current block.
            - value: The extracted value (string, list, or dict).
            - confidence: Float 0.0-1.0. Below 0.8 means pending clarification.
            - source: "user_explicit" | "inferred" | "recommended"

    Returns:
        JSON with empty text and a preview_update ui_action containing the delta.
    """
```

- [ ] **Step 4: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/application/tools/interview/extract_structured.py --no-cache`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/application/tools/interview/extract_structured.py backend/tests/modules/copilot/test_extract_global.py
git commit -m "feat(copilot): make extract_structured explicitly global (cross-block)"
```

---

### Task 7: Clean dead code

**Files:**
- Delete: `backend/src/modules/copilot/application/tools/brand_tools.py` (if exists and unused)
- Delete: `backend/src/modules/copilot/application/tools/offer_tools.py` (if exists and unused)
- Delete: `backend/src/modules/copilot/application/tools/research.py` (if exists and is mock)

- [ ] **Step 1: Verify files are unused**

Run grep to confirm these files are not imported anywhere:
- `cd backend && grep -r "brand_tools" src/ --include="*.py" -l`
- `cd backend && grep -r "offer_tools" src/ --include="*.py" -l`
- `cd backend && grep -r "from.*research import\|import.*research" src/modules/copilot/ --include="*.py" -l`

Only delete files that are confirmed unused (not imported by any other file).

- [ ] **Step 2: Delete confirmed dead files**

- [ ] **Step 3: Run full backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add -u backend/src/modules/copilot/application/tools/
git commit -m "chore(copilot): remove dead tool files (brand_tools, offer_tools, research)"
```

---

## Frontend Tasks (Agent B)

### Task 8: Extend Zustand store with focus/interview state (backward-compatible)

**Files:**
- Modify: `frontend/src/features/copilot/store/copilot-store.ts`
- Modify: `frontend/src/features/copilot/__tests__/copilot-store.test.ts`

- [ ] **Step 1: Write tests for new store fields and mode derivation**

Add to `frontend/src/features/copilot/__tests__/copilot-store.test.ts`:

```typescript
describe("Focus and Interview state", () => {
  it("should default to no focus entity", () => {
    const state = useCopilotStore.getState();
    expect(state.focusEntity).toBeNull();
    expect(state.focusSnapshot).toBeNull();
  });

  it("should set and clear focus entity", () => {
    const { setFocusEntity, clearFocus } = useCopilotStore.getState();
    setFocusEntity({ domain: "offer", entityId: "123", label: "Mi Oferta" });

    expect(useCopilotStore.getState().focusEntity).toEqual({
      domain: "offer",
      entityId: "123",
      label: "Mi Oferta",
    });

    clearFocus();
    expect(useCopilotStore.getState().focusEntity).toBeNull();
    expect(useCopilotStore.getState().focusSnapshot).toBeNull();
  });

  it("should set and clear interview session", () => {
    const { setInterviewSession, clearInterview } = useCopilotStore.getState();
    setInterviewSession("session-abc");

    expect(useCopilotStore.getState().interviewSessionId).toBe("session-abc");

    clearInterview();
    expect(useCopilotStore.getState().interviewSessionId).toBeNull();
    expect(useCopilotStore.getState().interviewProgress).toBeNull();
  });

  it("should update and clear preview data", () => {
    const { updatePreviewData, clearPreviewData } = useCopilotStore.getState();
    updatePreviewData({ "strategy.name": "Test" });
    updatePreviewData({ "pricing.amount": 100 });

    const state = useCopilotStore.getState();
    expect(state.previewData).toEqual({
      "strategy.name": "Test",
      "pricing.amount": 100,
    });

    clearPreviewData();
    expect(useCopilotStore.getState().previewData).toBeNull();
  });
});

describe("sidebarState", () => {
  it("should default to collapsed", () => {
    expect(useCopilotStore.getState().sidebarState).toBe("collapsed");
  });

  it("should transition between states", () => {
    const { setSidebarState } = useCopilotStore.getState();
    setSidebarState("open");
    expect(useCopilotStore.getState().sidebarState).toBe("open");

    setSidebarState("expanded");
    expect(useCopilotStore.getState().sidebarState).toBe("expanded");

    setSidebarState("collapsed");
    expect(useCopilotStore.getState().sidebarState).toBe("collapsed");
  });
});

describe("backward compatibility", () => {
  it("isOpen should reflect sidebarState", () => {
    const { setSidebarState } = useCopilotStore.getState();
    setSidebarState("collapsed");
    expect(useCopilotStore.getState().isOpen).toBe(false);

    setSidebarState("open");
    expect(useCopilotStore.getState().isOpen).toBe(true);

    setSidebarState("expanded");
    expect(useCopilotStore.getState().isOpen).toBe(true);
  });

  it("togglePanel should work with sidebarState", () => {
    const { togglePanel, setSidebarState } = useCopilotStore.getState();
    setSidebarState("collapsed");
    togglePanel();
    expect(useCopilotStore.getState().sidebarState).toBe("open");

    togglePanel();
    expect(useCopilotStore.getState().sidebarState).toBe("collapsed");
  });

  it("openPanel should set sidebarState to open", () => {
    useCopilotStore.getState().openPanel();
    expect(useCopilotStore.getState().sidebarState).toBe("open");
  });

  it("closePanel should set sidebarState to collapsed", () => {
    useCopilotStore.getState().setSidebarState("open");
    useCopilotStore.getState().closePanel();
    expect(useCopilotStore.getState().sidebarState).toBe("collapsed");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-store.test.ts`
Expected: FAIL — new fields/methods not defined

- [ ] **Step 3: Extend the store**

Modify `frontend/src/features/copilot/store/copilot-store.ts`:

1. Add `FocusEntity` and `InterviewProgress` interfaces (export them)
2. Replace `isOpen: boolean` with `sidebarState: "collapsed" | "open" | "expanded"`
3. Add `isOpen` as a derived getter: `get isOpen() { return this.sidebarState !== "collapsed" }`
4. Make `togglePanel`, `openPanel`, `closePanel` work via `sidebarState`
5. Add focus fields: `focusEntity`, `focusSnapshot`, `setFocusEntity`, `setFocusSnapshot`, `clearFocus`
6. Add interview fields: keep existing `interviewSessionId` but rename internal implementation. Add `interviewProgress`, `setInterviewSession`, `setInterviewProgress`, `clearInterview`
7. Add preview fields: `previewData`, `updatePreviewData` (merge delta), `clearPreviewData`
8. Add `setSidebarState`
9. Keep ALL existing actions working (backward compatibility)
10. Remove old `interviewMode` boolean — derive it: `interviewMode` getter = `interviewSessionId !== null`
11. Rename `interviewPreviewData` to `previewData` (same data, clearer name). Keep `updateInterviewPreview` as alias for `updatePreviewData` for backward compat.

- [ ] **Step 4: Update beforeEach in existing tests**

Update the `beforeEach` reset in the test file to include the new fields with their defaults.

- [ ] **Step 5: Run all copilot tests**

Run: `cd frontend && npx vitest run src/features/copilot/`
Expected: PASS (all existing + new tests)

- [ ] **Step 6: Run lint**

Run: `cd frontend && npx eslint src/features/copilot/store/copilot-store.ts`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/copilot/store/copilot-store.ts frontend/src/features/copilot/__tests__/copilot-store.test.ts
git commit -m "feat(copilot): extend store with focus/interview/sidebar state (backward-compatible)"
```

---

### Task 9: Create CopilotInput unified component

**Files:**
- Create: `frontend/src/features/copilot/components/copilot-input.tsx`
- Create: `frontend/src/features/copilot/__tests__/copilot-input.test.tsx`
- Note: useVoiceRecorder stays in its current location for now (hooks/)

- [ ] **Step 1: Write component tests**

```typescript
// frontend/src/features/copilot/__tests__/copilot-input.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CopilotInput } from "../components/copilot-input";

// Mock the voice recorder hook
vi.mock("../hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn().mockResolvedValue(""),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

describe("CopilotInput", () => {
  const defaultProps = {
    onSend: vi.fn(),
    disabled: false,
  };

  it("renders textarea", () => {
    render(<CopilotInput {...defaultProps} />);
    expect(screen.getByPlaceholderText(/escribe/i)).toBeInTheDocument();
  });

  it("renders mic button", () => {
    render(<CopilotInput {...defaultProps} />);
    expect(screen.getByRole("button", { name: /mic|audio|voz/i })).toBeInTheDocument();
  });

  it("renders attachment button", () => {
    render(<CopilotInput {...defaultProps} />);
    expect(screen.getByRole("button", { name: /adjuntar|attach/i })).toBeInTheDocument();
  });

  it("calls onSend when pressing Enter", async () => {
    const onSend = vi.fn();
    render(<CopilotInput {...defaultProps} onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    await userEvent.type(textarea, "Hello{Enter}");
    expect(onSend).toHaveBeenCalledWith("Hello");
  });

  it("does not send empty messages", async () => {
    const onSend = vi.fn();
    render(<CopilotInput {...defaultProps} onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    await userEvent.type(textarea, "{Enter}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input when disabled prop is true", () => {
    render(<CopilotInput {...defaultProps} disabled />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    expect(textarea).toBeDisabled();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-input.test.tsx`
Expected: FAIL — component doesn't exist

- [ ] **Step 3: Implement CopilotInput**

Create `frontend/src/features/copilot/components/copilot-input.tsx`:

The component should:
1. Accept props: `onSend: (text: string) => void`, `onFilesAttached?: (files: File[]) => void`, `disabled?: boolean`, `placeholder?: string`
2. Manage local state: `value` (textarea), `attachedFiles` (File[])
3. Render: textarea (auto-expanding, max 120px), MicButton, AttachmentButton, SendButton
4. Import `useVoiceRecorder` from `../hooks/useVoiceRecorder`
5. Import `AttachmentButton` from `./shared/attachment-button`
6. Import `DocumentChip` from `./shared/document-chip`
7. Handle recording states (recording indicator with duration, transcribing indicator)
8. On mic stop: set textarea value to transcript
9. On send: call `onSend(value)`, clear value and files
10. On Enter (without Shift): send. Shift+Enter: newline
11. Use `"use client"` directive
12. Follow existing code style (Tailwind + cn utility)

Base the implementation on the existing `InterviewInput` component (read it for exact styling patterns) but simplify — no need for the full interview-specific logic, just the unified input.

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-input.test.tsx`
Expected: PASS

- [ ] **Step 5: Run lint**

Run: `cd frontend && npx eslint src/features/copilot/components/copilot-input.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/copilot-input.tsx frontend/src/features/copilot/__tests__/copilot-input.test.tsx
git commit -m "feat(copilot): create CopilotInput unified component with mic + attachments"
```

---

### Task 10: Refactor preview registry to lazy config (no side-effects)

**Files:**
- Modify: `frontend/src/features/copilot/config/interview-preview-registry.ts`
- Modify: `frontend/src/features/copilot/__tests__/preview-registry.test.ts` (create or extend)

- [ ] **Step 1: Write tests for lazy registry**

```typescript
// frontend/src/features/copilot/__tests__/preview-registry.test.ts
import { describe, it, expect } from "vitest";
import { getPreviewEntry, getSupportedDomains } from "../config/interview-preview-registry";

describe("Preview Registry (lazy)", () => {
  it("returns entry for brand domain", () => {
    const entry = getPreviewEntry("brand");
    expect(entry).not.toBeNull();
    expect(entry!.emptyStateMessage).toBeTruthy();
    expect(typeof entry!.summaryComponent).toBe("function");
    expect(typeof entry!.sectionsComponent).toBe("function");
  });

  it("returns entry for offer domain", () => {
    const entry = getPreviewEntry("offer");
    expect(entry).not.toBeNull();
  });

  it("returns entry for buyer_persona domain", () => {
    const entry = getPreviewEntry("buyer_persona");
    expect(entry).not.toBeNull();
  });

  it("returns null for unknown domain", () => {
    const entry = getPreviewEntry("unknown");
    expect(entry).toBeNull();
  });

  it("lists supported domains", () => {
    const domains = getSupportedDomains();
    expect(domains).toContain("brand");
    expect(domains).toContain("offer");
    expect(domains).toContain("buyer_persona");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/preview-registry.test.ts`
Expected: FAIL — `getPreviewEntry` not defined

- [ ] **Step 3: Refactor the registry**

Modify `frontend/src/features/copilot/config/interview-preview-registry.ts`:

1. Keep the existing `PreviewSummaryProps`, `PreviewSectionsProps` interfaces (they're used by preview components)
2. Replace the mutable `PREVIEW_REGISTRY` object and `registerPreview()` function with a static `PREVIEW_REGISTRY` using lazy imports
3. Add `getPreviewEntry(domain: string): PreviewRegistryEntry | null`
4. Add `getSupportedDomains(): string[]`
5. Keep `PreviewConfig` interface but rename to `PreviewRegistryEntry` (or export both for backward compat)
6. Keep `getPreview()` as backward-compatible wrapper that calls `getPreviewEntry()` and throws if null
7. Keep `clearPreviewRegistry()` for tests (no-op now since registry is static)

The lazy import entries should match the paths from the spec (Section 4.4).

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/preview-registry.test.ts`
Expected: PASS

- [ ] **Step 5: Verify existing interview pages still work**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "preview-registry\|register-preview" | head -20`

The side-effect imports (`register-brand-preview.ts`, etc.) will still work because `registerPreview()` is kept as a no-op. They'll be removed in Phase 4.

- [ ] **Step 6: Run lint + type check**

Run: `cd frontend && npx eslint src/features/copilot/config/interview-preview-registry.ts && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/copilot/config/interview-preview-registry.ts frontend/src/features/copilot/__tests__/preview-registry.test.ts
git commit -m "refactor(copilot): preview registry with lazy imports, no side-effects"
```

---

### Task 11: Export unified types

**Files:**
- Modify: `frontend/src/features/copilot/types/index.ts`

- [ ] **Step 1: Add FocusEntity and InterviewProgress types**

Read the current `frontend/src/features/copilot/types/index.ts` to understand existing exports. Add:

```typescript
export interface FocusEntity {
  domain: "brand" | "offer" | "buyer_persona";
  entityId?: string;
  label: string;
}

export interface InterviewProgress {
  currentBlock: string;
  blocksCompleted: string[];
  totalBlocks: number;
}
```

If these types are already defined in `copilot-store.ts`, move them here and re-export from the store to keep types in `types/` per FSD convention.

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/copilot/types/index.ts
git commit -m "feat(copilot): export FocusEntity and InterviewProgress types"
```

---

### Task 12: Run full test suites

- [ ] **Step 1: Run backend tests**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/copilot/ && npx vitest run src/features/copilot/`
Expected: PASS

- [ ] **Step 3: Run architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: PASS

---

### Task 13: Create gap document

**Files:**
- Create: `docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md`

- [ ] **Step 1: Document all discoveries**

Create the gap document with:
- Technical gaps discovered during Phase 0 implementation
- Workarounds applied
- Recommendations for Phase 1-4
- Code quality observations
- Any tech debt found along the way

- [ ] **Step 2: Commit everything**

```bash
git add docs/superpowers/specs/2026-04-13-unified-copilot-gaps.md
git commit -m "docs(copilot): Phase 0 gap analysis and recommendations"
```
