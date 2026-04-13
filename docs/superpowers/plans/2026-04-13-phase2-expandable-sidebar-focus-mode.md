# Phase 2: Expandable Sidebar + Focus Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the copilot sidebar to 780px with a preview pane + chat side-by-side when Focus Mode is active. Focus tools enable AI-driven entity editing with auto-save and undo.

**Architecture:** Dashboard layout converts from `fixed` + `padding-right` to flex-based push layout. CopilotSidebar replaces CopilotPanel with 3 width states (60/380/780px). Backend adds 3 focus tools (entity_write, entity_read, entity_undo_all) using existing ContextVar for tenant_id and persister_registry for writes. Focus entity data is loaded into CopilotState at orchestrator level.

**Tech Stack:** Next.js 16 (App Router), Zustand, Tailwind CSS, FastAPI, LangChain tools, SQLAlchemy 2.0

**Spec:** `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` (sections 3.2, 4.1–4.7, 5.4)
**Handoff:** `docs/superpowers/specs/2026-04-13-phase2-handoff.md`

---

## Parallel Streams

- **Stream A (Backend):** Tasks 1–5. Independent of frontend.
- **Stream B (Frontend):** Tasks 6–12. Independent of backend.
- **Task 13:** Integration verification after both streams complete.

---

## Stream A: Backend — Focus Tools & Wiring

### Task 1: Add focus_entity_data to CopilotState

**Files:**
- Modify: `backend/src/modules/copilot/application/orchestrator/state.py`
- Test: `backend/tests/modules/copilot/test_copilot_state.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/copilot/test_copilot_state.py
"""Tests for CopilotState creation and focus_entity_data field."""

from uuid import uuid4

from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)


class TestCopilotState:
    def test_initial_state_has_focus_entity_data_none(self):
        state = create_initial_copilot_state(
            user_id=uuid4(),
            tenant_id=uuid4(),
            conversation_id="test-conv",
        )
        assert state["focus_entity_data"] is None

    def test_initial_state_with_focus_context(self):
        state = create_initial_copilot_state(
            user_id=uuid4(),
            tenant_id=uuid4(),
            conversation_id="test-conv",
            client_context={
                "current_route": "/offer-studio/offer/123",
                "focus": {"domain": "offer", "entity_id": "abc-123"},
            },
        )
        assert state["client_context"]["focus"]["domain"] == "offer"
        assert state["focus_entity_data"] is None  # loaded later by orchestrator
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_copilot_state.py -x -q --tb=short`
Expected: FAIL with KeyError `focus_entity_data`

- [ ] **Step 3: Implement — add focus_entity_data to state**

In `backend/src/modules/copilot/application/orchestrator/state.py`, add the field to `CopilotState` and `create_initial_copilot_state`:

```python
class CopilotState(TypedDict):
    # ... existing fields ...

    # Focus mode: entity snapshot loaded at focus start
    focus_entity_data: dict[str, Any] | None


def create_initial_copilot_state(
    user_id: UUID,
    tenant_id: UUID,
    conversation_id: str,
    client_context: ClientContext | None = None,
) -> CopilotState:
    """Create initial copilot state."""
    return {
        "messages": [],
        "user_id": user_id,
        "tenant_id": tenant_id,
        "client_context": client_context or {},
        "conversation_id": conversation_id,
        "pending_ui_actions": [],
        "active_tool_names": [],
        "active_procedure": None,
        "error": None,
        "focus_entity_data": None,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_copilot_state.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/application/orchestrator/state.py backend/tests/modules/copilot/test_copilot_state.py
git commit -m "feat(copilot): add focus_entity_data to CopilotState"
```

---

### Task 2: Focus context loader

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/context/focus_context_loader.py`
- Modify: `backend/src/modules/copilot/infrastructure/context/context_loader_registry.py`
- Test: `backend/tests/modules/copilot/test_focus_context_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/copilot/test_focus_context_loader.py
"""Tests for FocusContextLoader — loads entity data for focus mode."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.context.focus_context_loader import (
    FocusContextLoader,
)


class TestFocusContextLoader:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.loader = FocusContextLoader(self.mock_db)
        self.tenant_id = uuid4()

    @patch(
        "src.modules.copilot.infrastructure.context.focus_context_loader.get_persister"
    )
    def test_load_offer_entity(self, mock_get_persister):
        entity_id = uuid4()
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {
            "public_name": "Oferta Premium",
            "archetype": "programa",
            "price_pay_in_full": 997,
        }
        mock_get_persister.return_value = mock_persister

        result = self.loader.load(self.tenant_id, "offer", str(entity_id))

        assert result["public_name"] == "Oferta Premium"
        assert result["archetype"] == "programa"
        mock_persister.load_existing.assert_called_once_with(self.tenant_id, entity_id)

    @patch(
        "src.modules.copilot.infrastructure.context.focus_context_loader.get_persister"
    )
    def test_load_brand_entity_no_entity_id(self, mock_get_persister):
        """Brand is a singleton — no entity_id needed."""
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {
            "identity.brand_name": "Mi Marca",
        }
        mock_get_persister.return_value = mock_persister

        result = self.loader.load(self.tenant_id, "brand", None)

        assert result["identity.brand_name"] == "Mi Marca"

    @patch(
        "src.modules.copilot.infrastructure.context.focus_context_loader.get_persister"
    )
    def test_load_returns_empty_dict_when_entity_not_found(self, mock_get_persister):
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {}
        mock_get_persister.return_value = mock_persister

        result = self.loader.load(self.tenant_id, "offer", str(uuid4()))

        assert result == {}

    def test_load_unknown_domain_raises(self):
        with pytest.raises(ValueError, match="No persister registered"):
            self.loader.load(self.tenant_id, "unknown_domain", None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_focus_context_loader.py -x -q --tb=short`
Expected: FAIL with ImportError (module doesn't exist)

- [ ] **Step 3: Implement FocusContextLoader**

```python
# backend/src/modules/copilot/infrastructure/context/focus_context_loader.py
"""Loads entity data for Focus Mode — used by the orchestrator to populate focus_entity_data."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class FocusContextLoader:
    """Load entity snapshot for focus mode system prompt and tools."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load(
        self,
        tenant_id: UUID,
        domain: str,
        entity_id: str | None,
    ) -> dict:
        """Load entity data as a flat dict.

        Args:
            tenant_id: The tenant UUID.
            domain: "offer", "brand", or "buyer_persona".
            entity_id: Entity UUID string (None for brand singleton).

        Returns:
            Flat dict of entity field values.

        Raises:
            ValueError: If domain has no registered persister.

        """
        persister = get_persister(domain, self.db)
        eid = UUID(entity_id) if entity_id else None

        try:
            return persister.load_existing(tenant_id, eid)
        except TypeError:
            # BrandPersister.load_existing takes (tenant_id) only
            return persister.load_existing(tenant_id)
        except Exception:
            logger.exception(
                "focus_context_load_error",
                domain=domain,
                entity_id=entity_id,
            )
            return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_focus_context_loader.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Register in context_loader_registry**

In `backend/src/modules/copilot/infrastructure/context/context_loader_registry.py`, add the import and entry:

```python
from src.modules.copilot.infrastructure.context.focus_context_loader import (
    FocusContextLoader,
)

CONTEXT_LOADERS = {
    "offer_context": OfferContextLoader,
    "focus_context": FocusContextLoader,
}
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/context/focus_context_loader.py backend/src/modules/copilot/infrastructure/context/context_loader_registry.py backend/tests/modules/copilot/test_focus_context_loader.py
git commit -m "feat(copilot): focus context loader — loads entity snapshot for focus mode"
```

---

### Task 3: Focus tools (entity_write, entity_read, entity_undo_all)

**Files:**
- Create: `backend/src/modules/copilot/application/tools/focus/__init__.py`
- Create: `backend/src/modules/copilot/application/tools/focus/entity_write.py`
- Create: `backend/src/modules/copilot/application/tools/focus/entity_read.py`
- Create: `backend/src/modules/copilot/application/tools/focus/entity_undo_all.py`
- Test: `backend/tests/modules/copilot/test_focus_tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/modules/copilot/test_focus_tools.py
"""Tests for Focus Mode tools: entity_write, entity_read, entity_undo_all."""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.tools.focus.entity_write import entity_write
from src.modules.copilot.application.tools.focus.entity_read import entity_read
from src.modules.copilot.application.tools.focus.entity_undo_all import entity_undo_all


class TestEntityWrite:
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_writes_valid_field_and_returns_preview_update(
        self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister
    ):
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_get_persister.return_value = mock_persister

        entity_id = str(uuid4())
        result = entity_write.invoke({
            "domain": "offer",
            "entity_id": entity_id,
            "field_path": "headline_promise",
            "value": "Transforma tu negocio en 90 días",
            "reason": "User provided their main promise",
        })

        parsed = json.loads(result)
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["delta"]["headline_promise"] == "Transforma tu negocio en 90 días"
        mock_persister.persist.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_rejects_invalid_field_path(self, mock_validate):
        mock_validate.return_value = False

        result = entity_write.invoke({
            "domain": "offer",
            "entity_id": str(uuid4()),
            "field_path": "nonexistent_field",
            "value": "test",
            "reason": "test",
        })

        parsed = json.loads(result)
        assert "error" in parsed
        assert "nonexistent_field" in parsed["error"]


class TestEntityRead:
    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_reads_full_entity(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        tid = uuid4()
        mock_get_tid.return_value = tid
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.return_value = {
            "public_name": "Oferta Premium",
            "archetype": "programa",
        }
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke({
            "domain": "offer",
            "entity_id": str(uuid4()),
        })

        parsed = json.loads(result)
        assert parsed["data"]["public_name"] == "Oferta Premium"
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_reads_specific_section(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        mock_get_tid.return_value = uuid4()
        mock_session_cls.return_value = MagicMock()
        mock_loader = MagicMock()
        mock_loader.load.return_value = {
            "public_name": "Oferta",
            "archetype": "programa",
            "headline_promise": "Transforma",
            "pricing_options": [],
        }
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke({
            "domain": "offer",
            "entity_id": str(uuid4()),
            "section": "pricing",
        })

        parsed = json.loads(result)
        # Should filter to pricing-related fields
        assert "data" in parsed


class TestEntityUndoAll:
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_restores_snapshot(self, mock_session_cls, mock_get_tid, mock_get_persister):
        tid = uuid4()
        mock_get_tid.return_value = tid
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_get_persister.return_value = mock_persister

        entity_id = str(uuid4())
        snapshot = {"public_name": "Original", "archetype": "producto"}

        result = entity_undo_all.invoke({
            "domain": "offer",
            "entity_id": entity_id,
            "snapshot": snapshot,
        })

        parsed = json.loads(result)
        assert parsed["text"] == "Entidad restaurada al estado inicial del focus."
        assert parsed["ui_action"]["type"] == "preview_update"
        mock_persister.persist.assert_called_once()
        mock_db.close.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_focus_tools.py -x -q --tb=short`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement entity_write**

```python
# backend/src/modules/copilot/application/tools/focus/__init__.py
"""Focus tool group for Focus Mode entity editing."""

from src.modules.copilot.application.tools.focus.entity_read import entity_read
from src.modules.copilot.application.tools.focus.entity_undo_all import entity_undo_all
from src.modules.copilot.application.tools.focus.entity_write import entity_write

FOCUS_TOOLS = [
    entity_write,
    entity_read,
    entity_undo_all,
]
```

```python
# backend/src/modules/copilot/application/tools/focus/entity_write.py
"""Focus tool: write a field to the focused entity with auto-save."""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.schema_introspection import validate_field_path
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)

logger = structlog.get_logger()


@tool
def entity_write(
    domain: str,
    entity_id: str,
    field_path: str,
    value: str,
    reason: str,
) -> str:
    """Modify a field on the focused entity. Auto-saves immediately.

    Use this tool whenever the user provides information about the entity
    they are focused on. The change persists immediately — no confirmation
    needed.

    Args:
        domain: The entity domain ("offer", "brand", "buyer_persona").
        entity_id: UUID of the entity (empty string for brand singleton).
        field_path: Dot-notation field path (e.g., "headline_promise",
                    "identity.brand_name"). Must be a valid field.
        value: The new value for the field.
        reason: Brief explanation of why this change was made.

    Returns:
        JSON with confirmation text and preview_update ui_action.

    """
    if not validate_field_path(domain, field_path):
        return json.dumps({
            "error": f"Campo '{field_path}' no es válido para el dominio '{domain}'.",
        })

    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        persister = get_persister(domain, db)
        eid = UUID(entity_id) if entity_id else None
        persister.persist(
            tenant_id=tenant_id,
            mapa_global={field_path: value},
            fields_to_persist=[field_path],
            entity_id=eid,
        )
        logger.info(
            "entity_write_success",
            domain=domain,
            entity_id=entity_id,
            field_path=field_path,
        )
        return json.dumps({
            "text": f"Actualizado: {field_path}",
            "ui_action": {
                "type": "preview_update",
                "delta": {field_path: value},
                "reason": reason,
            },
        })
    except Exception as e:
        logger.exception("entity_write_error", field_path=field_path)
        return json.dumps({"error": f"Error al escribir: {e!s}"})
    finally:
        db.close()
```

- [ ] **Step 4: Implement entity_read**

```python
# backend/src/modules/copilot/application/tools/focus/entity_read.py
"""Focus tool: read entity state (full or by section)."""

import json

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.context.focus_context_loader import (
    FocusContextLoader,
)

logger = structlog.get_logger()


@tool
def entity_read(
    domain: str,
    entity_id: str,
    section: str | None = None,
) -> str:
    """Read the current state of the focused entity, or a specific section.

    Use this to check what data the entity currently has before making
    suggestions or asking questions. Avoids asking for information
    the user already provided.

    Args:
        domain: The entity domain ("offer", "brand", "buyer_persona").
        entity_id: UUID of the entity (empty string for brand singleton).
        section: Optional section name to filter (e.g., "pricing", "strategy").
                 If omitted, returns all data.

    Returns:
        JSON with the entity data.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        loader = FocusContextLoader(db)
        data = loader.load(tenant_id, domain, entity_id or None)

        if section:
            # Filter fields that match the section prefix
            filtered = {
                k: v for k, v in data.items()
                if k.startswith(f"{section}.") or k.startswith(f"{section}_") or k == section
            }
            return json.dumps({"data": filtered, "section": section})

        return json.dumps({"data": data})
    except Exception as e:
        logger.exception("entity_read_error", domain=domain)
        return json.dumps({"error": f"Error al leer entidad: {e!s}"})
    finally:
        db.close()
```

- [ ] **Step 5: Implement entity_undo_all**

```python
# backend/src/modules/copilot/application/tools/focus/entity_undo_all.py
"""Focus tool: restore entity to snapshot state (undo all focus changes)."""

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)

logger = structlog.get_logger()


@tool
def entity_undo_all(
    domain: str,
    entity_id: str,
    snapshot: dict,
) -> str:
    """Restore the entity to its state when focus mode started.

    This overwrites all fields that were modified during the focus session
    with their original values from the snapshot.

    Args:
        domain: The entity domain ("offer", "brand", "buyer_persona").
        entity_id: UUID of the entity (empty string for brand singleton).
        snapshot: The full entity snapshot saved at focus start.

    Returns:
        JSON with confirmation and preview_update with restored data.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "No se pudo determinar el tenant."})

    db = SessionLocal()
    try:
        persister = get_persister(domain, db)
        eid = UUID(entity_id) if entity_id else None
        persister.persist(
            tenant_id=tenant_id,
            mapa_global=snapshot,
            fields_to_persist=list(snapshot.keys()),
            entity_id=eid,
        )
        logger.info(
            "entity_undo_all_success",
            domain=domain,
            entity_id=entity_id,
            fields_restored=len(snapshot),
        )
        return json.dumps({
            "text": "Entidad restaurada al estado inicial del focus.",
            "ui_action": {
                "type": "preview_update",
                "delta": snapshot,
            },
        })
    except Exception as e:
        logger.exception("entity_undo_all_error", domain=domain)
        return json.dumps({"error": f"Error al restaurar: {e!s}"})
    finally:
        db.close()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_focus_tools.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/application/tools/focus/ backend/tests/modules/copilot/test_focus_tools.py
git commit -m "feat(copilot): focus tools — entity_write, entity_read, entity_undo_all"
```

---

### Task 4: Tool registry — focus mode selection

**Files:**
- Modify: `backend/src/modules/copilot/application/tools/registry.py`
- Test: `backend/tests/modules/copilot/test_tool_registry_focus.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/copilot/test_tool_registry_focus.py
"""Tests for focus mode tool selection in the tool registry."""

from src.modules.copilot.application.tools.registry import get_tools_for_context


class TestFocusModeToolSelection:
    def test_focus_mode_returns_focus_tools(self):
        context = {
            "current_route": "/offer-studio/offer/123",
            "focus": {"domain": "offer", "entity_id": "abc-123"},
        }
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}

        assert "entity_write" in tool_names
        assert "entity_read" in tool_names
        assert "entity_undo_all" in tool_names

    def test_focus_mode_excludes_mutation_tools(self):
        context = {
            "current_route": "/brand-studio",
            "focus": {"domain": "brand"},
        }
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}

        assert "propose_field_updates" not in tool_names

    def test_focus_mode_includes_knowledge_tools(self):
        context = {
            "current_route": "/offer-studio/offer/123",
            "focus": {"domain": "offer", "entity_id": "abc-123"},
        }
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}

        assert "search_knowledge_base" in tool_names

    def test_interview_mode_takes_priority_over_focus(self):
        context = {
            "current_route": "/brand-studio/interview",
            "focus": {"domain": "brand"},
            "interview_session_id": "session-123",
        }
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}

        # Interview tools, NOT focus tools
        assert "extract_structured" in tool_names
        assert "entity_write" not in tool_names

    def test_chat_mode_unchanged(self):
        context = {"current_route": "/brand-studio"}
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}

        assert "propose_field_updates" in tool_names
        assert "entity_write" not in tool_names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_tool_registry_focus.py -x -q --tb=short`
Expected: FAIL — focus tools not returned

- [ ] **Step 3: Implement focus mode in registry**

In `backend/src/modules/copilot/application/tools/registry.py`, add the focus import and update `get_tools_for_context`:

```python
# Add import at top
from src.modules.copilot.application.tools.focus import FOCUS_TOOLS

# Add to TOOL_GROUPS
TOOL_GROUPS: dict[str, list] = {
    # ... existing groups ...
    "focus": FOCUS_TOOLS,
}

# Replace the get_tools_for_context function
def get_tools_for_context(context: dict | None) -> list:
    """Return tools based on mode (interview > focus > chat).

    Mode is determined by context fields:
    - interview_session_id present -> Interview mode (interview + knowledge tools)
    - focus present -> Focus mode (focus + knowledge + route domain tools, no mutation)
    - Neither -> Chat mode (route-based, current behavior)
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

    # Focus mode: focus + knowledge + route domain tools, no mutation
    if context.get("focus"):
        tools = []
        seen: set[str] = set()
        # Focus-specific tools
        for group_name in ("focus", "knowledge", "awareness", "module_data"):
            for t in TOOL_GROUPS.get(group_name, []):
                if t.name not in seen:
                    tools.append(t)
                    seen.add(t.name)
        # Add route-specific domain tools (analytics, crm, etc.) but NOT mutation
        route_groups = _match_route(context.get("current_route"))
        excluded = {"mutation"}
        for group_name in route_groups:
            if group_name in excluded:
                continue
            for t in TOOL_GROUPS.get(group_name, []):
                if t.name not in seen:
                    tools.append(t)
                    seen.add(t.name)
        return tools

    # Chat mode: route-based selection
    return get_tools_for_route(context.get("current_route"))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_tool_registry_focus.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/copilot/application/tools/registry.py backend/src/modules/copilot/application/tools/focus/__init__.py backend/tests/modules/copilot/test_tool_registry_focus.py
git commit -m "feat(copilot): focus mode tool selection in registry"
```

---

### Task 5: Orchestrator wiring — load focus entity data

**Files:**
- Modify: `backend/src/modules/copilot/application/orchestrator/chat.py`
- Test: `backend/tests/modules/copilot/test_orchestrator_focus.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/modules/copilot/test_orchestrator_focus.py
"""Tests for focus entity data loading in the orchestrator."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator


class TestOrchestratorFocusLoading:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.orchestrator = CopilotOrchestrator(self.mock_db)

    @patch(
        "src.modules.copilot.application.orchestrator.chat.FocusContextLoader"
    )
    def test_loads_focus_entity_data_into_state(self, mock_loader_cls):
        mock_loader = MagicMock()
        mock_loader.load.return_value = {
            "public_name": "Oferta Premium",
            "archetype": "programa",
        }
        mock_loader_cls.return_value = mock_loader

        tenant_id = uuid4()
        entity_id = str(uuid4())
        client_ctx = {
            "current_route": "/offer-studio/offer/123",
            "focus": {"domain": "offer", "entity_id": entity_id},
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        }

        result = self.orchestrator._load_focus_entity_data(client_ctx, tenant_id)

        assert result["public_name"] == "Oferta Premium"
        mock_loader.load.assert_called_once_with(tenant_id, "offer", entity_id)

    def test_returns_none_when_no_focus_context(self):
        client_ctx = {
            "current_route": "/brand-studio",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        }
        result = self.orchestrator._load_focus_entity_data(client_ctx, uuid4())
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_orchestrator_focus.py -x -q --tb=short`
Expected: FAIL — `_load_focus_entity_data` doesn't exist

- [ ] **Step 3: Implement focus loading in orchestrator**

In `backend/src/modules/copilot/application/orchestrator/chat.py`, add the import and method, and wire it into `stream_chat`:

Add import:
```python
from src.modules.copilot.infrastructure.context.focus_context_loader import (
    FocusContextLoader,
)
```

Add method to `CopilotOrchestrator`:
```python
    def _load_focus_entity_data(
        self,
        client_ctx: dict,
        tenant_id: UUID,
    ) -> dict | None:
        """Load entity snapshot if focus context is present."""
        focus = client_ctx.get("focus")
        if not focus:
            return None
        try:
            loader = FocusContextLoader(self.db)
            return loader.load(
                tenant_id,
                focus.get("domain", ""),
                focus.get("entity_id"),
            )
        except Exception:
            logger.exception("focus_entity_data_load_error")
            return None
```

In `stream_chat`, after `state = create_initial_copilot_state(...)` and before loading interview session, add:
```python
        # 2c. Load focus entity data if focus context is present
        focus_data = self._load_focus_entity_data(client_ctx, tenant_id)
        if focus_data:
            state["focus_entity_data"] = focus_data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_orchestrator_focus.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Run full backend test suite**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: All tests pass (including existing tests)

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/application/orchestrator/chat.py backend/tests/modules/copilot/test_orchestrator_focus.py
git commit -m "feat(copilot): orchestrator loads focus entity data into state"
```

---

## Stream B: Frontend — Layout Refactor + Sidebar

### Task 6: Dashboard layout refactor (flex + push)

**Files:**
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`
- Test: `frontend/src/app/(main)/[tenantId]/(dashboard)/__tests__/layout.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/app/(main)/[tenantId]/(dashboard)/__tests__/layout.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock dependencies
vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("@/components/shared/layout/sidebar-context", () => ({
  SidebarProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useSidebar: () => ({ isCollapsed: false }),
}));

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ sidebarState: "open", isOpen: true }),
}));

vi.mock("@/components/shared/layout/app-sidebar", () => ({
  AppSidebar: () => <nav data-testid="app-sidebar">Sidebar</nav>,
}));

vi.mock("@/features/copilot/components/copilot-sidebar", () => ({
  CopilotSidebar: () => <aside data-testid="copilot-sidebar">Copilot</aside>,
}));

import DashboardLayout from "../layout";

describe("DashboardLayout", () => {
  it("renders flex container with main and copilot sidebar", () => {
    const { container } = render(
      <DashboardLayout>
        <div data-testid="page-content">Page</div>
      </DashboardLayout>,
    );

    expect(screen.getByTestId("app-sidebar")).toBeDefined();
    expect(screen.getByTestId("copilot-sidebar")).toBeDefined();
    expect(screen.getByTestId("page-content")).toBeDefined();

    // Main element should have flex-1 and overflow-y-auto
    const main = container.querySelector("main");
    expect(main?.className).toContain("flex-1");
    expect(main?.className).toContain("overflow-y-auto");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/app/\\(main\\)/\\[tenantId\\]/\\(dashboard\\)/__tests__/layout.test.tsx`
Expected: FAIL — CopilotSidebar import doesn't exist, layout structure different

- [ ] **Step 3: Implement layout refactor**

Replace the entire `DashboardContent` function in `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`:

```tsx
"use client";

import { memo, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/sidebar-context";
import { CopilotSidebar } from "@/features/copilot/components/copilot-sidebar";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

const FULL_WIDTH_PATTERNS = [
  "/sales/studio",
  "/offer-studio/offer/",
] as const;

function matchesFullWidth(pathname: string): boolean {
  return FULL_WIDTH_PATTERNS.some((pattern) => pathname.includes(pattern));
}

const MemoizedChildren = memo(function MemoizedChildren({
  children,
  isFullWidth,
}: {
  children: React.ReactNode;
  isFullWidth: boolean;
}) {
  return isFullWidth ? (
    <div className="h-full pt-16 md:pt-0">{children}</div>
  ) : (
    <div className="container mx-auto p-6 md:p-8 max-w-7xl h-full">
      {children}
    </div>
  );
});

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();
  const pathname = usePathname() ?? "";

  const [isFullWidth, setIsFullWidth] = useState(false);
  useEffect(() => {
    setIsFullWidth(matchesFullWidth(pathname));
  }, [pathname]);

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />
      <main
        className={cn(
          "flex-1 min-w-0 overflow-y-auto",
          "pt-16 md:pt-0 transition-[margin] duration-300 ease-in-out",
          isCollapsed ? "md:ml-20" : "md:ml-64",
        )}
      >
        <MemoizedChildren isFullWidth={isFullWidth}>
          {children}
        </MemoizedChildren>
      </main>
      <CopilotSidebar />
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <DashboardContent>{children}</DashboardContent>
    </SidebarProvider>
  );
}
```

Key changes:
- Outer `div` → `flex h-screen overflow-hidden`
- `<main>` → `flex-1 min-w-0 overflow-y-auto` (no more `pr-[380px]`/`pr-[60px]`)
- `CopilotSidebar` replaces `CopilotPanel` (in-flow, not fixed)
- `InterviewBanner` removed (replaced by CopilotStatusBar in Task 12)

- [ ] **Step 4: Create stub CopilotSidebar** (so layout compiles — full implementation in Task 7)

```tsx
// frontend/src/features/copilot/components/copilot-sidebar.tsx
"use client";

import { memo } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";
import { cn } from "@/lib/utils";

const SIDEBAR_WIDTHS = {
  collapsed: "w-[60px]",
  open: "w-[380px]",
  expanded: "w-[780px]",
} as const;

export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);

  return (
    <aside
      className={cn(
        "flex-shrink-0 h-full overflow-hidden border-l border-slate-200 bg-white",
        "transition-[width] duration-300 ease-in-out",
        "dark:border-slate-700 dark:bg-slate-900",
        SIDEBAR_WIDTHS[sidebarState],
      )}
    >
      {sidebarState === "collapsed" ? (
        <CopilotRail />
      ) : (
        <div className="flex h-full flex-col">
          {/* Header placeholder — replaced in Task 8 */}
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Copilot
            </span>
          </div>
          <CopilotChat />
        </div>
      )}
    </aside>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/app/\\(main\\)/\\[tenantId\\]/\\(dashboard\\)/__tests__/layout.test.tsx`
Expected: PASS

- [ ] **Step 6: Run TypeScript check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors (or only pre-existing ones)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/layout.tsx frontend/src/features/copilot/components/copilot-sidebar.tsx frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/__tests__/layout.test.tsx
git commit -m "feat(copilot): flex-based push layout + CopilotSidebar stub"
```

---

### Task 7: CopilotSidebar — full 3-state implementation with CopilotHeader

**Files:**
- Modify: `frontend/src/features/copilot/components/copilot-sidebar.tsx`
- Create: `frontend/src/features/copilot/components/copilot-header.tsx`
- Test: `frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token") }),
}));

vi.mock("../hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

vi.mock("../hooks/useProactiveNudges", () => ({
  useProactiveNudges: () => ({ nudges: [], dismissNudge: vi.fn() }),
}));

vi.mock("../api/copilot-api", () => ({
  streamCopilotChat: vi.fn(),
  reportCopilotEvent: vi.fn(),
}));

import { useCopilotStore } from "../store/copilot-store";
import { CopilotSidebar } from "../components/copilot-sidebar";

describe("CopilotSidebar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: "collapsed",
      isOpen: false,
      messages: [],
      status: "idle",
      conversationId: null,
      focusEntity: null,
      focusSnapshot: null,
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
      interviewPreviewData: null,
      currentRoute: null,
      pendingUIActions: [],
      selectedFields: [],
      activeProcedure: null,
      interviewMode: false,
    });
  });

  it("renders rail when collapsed", () => {
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[60px]");
  });

  it("renders chat panel when open", () => {
    useCopilotStore.setState({ sidebarState: "open", isOpen: true });
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[380px]");
  });

  it("renders expanded width when expanded", () => {
    useCopilotStore.setState({
      sidebarState: "expanded",
      isOpen: true,
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
    });
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[780px]");
  });

  it("shows mode indicator in header", () => {
    useCopilotStore.setState({
      sidebarState: "open",
      isOpen: true,
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
    });
    render(<CopilotSidebar />);
    expect(screen.getByText(/Focus/i)).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-sidebar.test.tsx`
Expected: FAIL — CopilotHeader doesn't exist, mode indicator not rendered

- [ ] **Step 3: Implement CopilotHeader**

```tsx
// frontend/src/features/copilot/components/copilot-header.tsx
"use client";

import { Maximize2, Minimize2, PanelRightClose, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import type { SidebarState } from "../store/copilot-store";

function getModeLabel(state: {
  interviewSessionId: string | null;
  focusEntity: { domain: string; label: string } | null;
}): string {
  if (state.interviewSessionId) {
    return `Entrevista: ${state.focusEntity?.label ?? ""}`;
  }
  if (state.focusEntity) {
    return `Focus: ${state.focusEntity.label}`;
  }
  return "Chat";
}

export function CopilotHeader() {
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const interviewSessionId = useCopilotStore((s) => s.interviewSessionId);
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const closePanel = useCopilotStore((s) => s.closePanel);
  const clearMessages = useCopilotStore((s) => s.clearMessages);

  const modeLabel = getModeLabel({ interviewSessionId, focusEntity });
  const canExpand = sidebarState === "open" && focusEntity;
  const canCollapse = sidebarState === "expanded";

  const handleToggleExpand = () => {
    const next: SidebarState = sidebarState === "expanded" ? "open" : "expanded";
    setSidebarState(next);
  };

  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
      <div className="flex items-center gap-2 min-w-0">
        <Sparkles className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
        <span className="truncate text-sm font-semibold text-slate-800 dark:text-slate-200">
          {modeLabel}
        </span>
      </div>
      <div className="flex items-center gap-1">
        {(canExpand || canCollapse) && (
          <Button
            size="icon"
            variant="ghost"
            onClick={handleToggleExpand}
            className="h-7 w-7 text-slate-400 hover:text-slate-600"
            title={canExpand ? "Expandir" : "Contraer"}
          >
            {canExpand ? (
              <Maximize2 className="h-3.5 w-3.5" />
            ) : (
              <Minimize2 className="h-3.5 w-3.5" />
            )}
          </Button>
        )}
        <Button
          size="icon"
          variant="ghost"
          onClick={clearMessages}
          className="h-7 w-7 text-slate-400 hover:text-slate-600"
          title="Nueva conversación"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          onClick={closePanel}
          className="h-7 w-7 text-slate-400 hover:text-slate-600"
          title="Cerrar"
        >
          <PanelRightClose className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update CopilotSidebar with full implementation**

Replace the stub in `frontend/src/features/copilot/components/copilot-sidebar.tsx`:

```tsx
"use client";

import { memo } from "react";
import { useCopilotStore } from "../store/copilot-store";
import { useRouteTracker } from "../hooks/useRouteTracker";
import { useCopilotNavigator } from "../hooks/useCopilotNavigator";
import { CopilotChat } from "./CopilotChat";
import { CopilotRail } from "./CopilotRail";
import { CopilotHeader } from "./copilot-header";
import { cn } from "@/lib/utils";

const SIDEBAR_WIDTHS = {
  collapsed: "w-[60px]",
  open: "w-[380px]",
  expanded: "w-[780px]",
} as const;

export const CopilotSidebar = memo(function CopilotSidebar() {
  useRouteTracker();
  useCopilotNavigator();
  const sidebarState = useCopilotStore((s) => s.sidebarState);

  return (
    <aside
      className={cn(
        "flex-shrink-0 h-full overflow-hidden border-l border-slate-200 bg-white",
        "transition-[width] duration-300 ease-in-out",
        "dark:border-slate-700 dark:bg-slate-900",
        SIDEBAR_WIDTHS[sidebarState],
      )}
    >
      {sidebarState === "collapsed" ? (
        <CopilotRail />
      ) : (
        <div className="flex h-full">
          {/* Preview pane — only when expanded (Task 9 adds content) */}
          {sidebarState === "expanded" && (
            <div className="w-[400px] shrink-0 border-r border-slate-200 overflow-y-auto dark:border-slate-700">
              {/* CopilotPreviewPane injected in Task 9 */}
            </div>
          )}
          {/* Chat column — always 380px */}
          <div className="flex w-[380px] shrink-0 flex-col">
            <CopilotHeader />
            <CopilotChat />
          </div>
        </div>
      )}
    </aside>
  );
});
CopilotSidebar.displayName = "CopilotSidebar";
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-sidebar.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/copilot-sidebar.tsx frontend/src/features/copilot/components/copilot-header.tsx frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx
git commit -m "feat(copilot): CopilotSidebar with 3 width states + CopilotHeader"
```

---

### Task 8: CopilotPreviewPane

**Files:**
- Create: `frontend/src/features/copilot/components/copilot-preview-pane.tsx`
- Modify: `frontend/src/features/copilot/components/copilot-sidebar.tsx` (inject preview)
- Test: `frontend/src/features/copilot/__tests__/copilot-preview-pane.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/features/copilot/__tests__/copilot-preview-pane.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../config/interview-preview-registry", () => ({
  getPreviewEntry: (domain: string) => {
    if (domain === "offer") {
      return {
        summaryComponent: () =>
          Promise.resolve({
            default: ({ data }: { data: Record<string, unknown> }) => (
              <div data-testid="offer-preview-summary">
                {String(data?.public_name ?? "Sin nombre")}
              </div>
            ),
          }),
        sectionsComponent: () =>
          Promise.resolve({
            default: () => <div data-testid="offer-preview-sections">Sections</div>,
          }),
        emptyStateMessage: "Describe tu oferta...",
      };
    }
    return null;
  },
}));

import { useCopilotStore } from "../store/copilot-store";
import { CopilotPreviewPane } from "../components/copilot-preview-pane";

describe("CopilotPreviewPane", () => {
  beforeEach(() => {
    useCopilotStore.setState({ previewData: null, focusEntity: null });
  });

  it("shows empty state when no preview data", async () => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
    });
    render(<CopilotPreviewPane />);
    await waitFor(() => {
      expect(screen.getByText("Describe tu oferta...")).toBeDefined();
    });
  });

  it("renders preview summary with data", async () => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
      previewData: { public_name: "Oferta Premium" },
    });
    render(<CopilotPreviewPane />);
    await waitFor(() => {
      expect(screen.getByText("Oferta Premium")).toBeDefined();
    });
  });

  it("renders nothing when no focusEntity", () => {
    const { container } = render(<CopilotPreviewPane />);
    expect(container.textContent).toBe("");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-preview-pane.test.tsx`
Expected: FAIL — CopilotPreviewPane doesn't exist

- [ ] **Step 3: Implement CopilotPreviewPane**

```tsx
// frontend/src/features/copilot/components/copilot-preview-pane.tsx
"use client";

import { Suspense, lazy, useMemo } from "react";
import { Loader2 } from "lucide-react";
import { useCopilotStore } from "../store/copilot-store";
import { getPreviewEntry } from "../config/interview-preview-registry";

function PreviewLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
    </div>
  );
}

export function CopilotPreviewPane() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const previewData = useCopilotStore((s) => s.previewData);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);

  const entry = useMemo(
    () => (focusEntity ? getPreviewEntry(focusEntity.domain) : null),
    [focusEntity?.domain],
  );

  if (!focusEntity || !entry) return null;

  const data = previewData ?? focusSnapshot ?? {};
  const hasData = Object.keys(data).length > 0;

  const SummaryComponent = lazy(entry.summaryComponent);
  const SectionsComponent = lazy(entry.sectionsComponent);

  return (
    <div className="flex h-full flex-col bg-slate-50 dark:bg-slate-800/50">
      {/* Preview header */}
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          Vista previa
        </h3>
        <p className="mt-0.5 text-xs text-slate-500">
          {focusEntity.label}
        </p>
      </div>

      {/* Preview content */}
      <div className="flex-1 overflow-y-auto p-4">
        {hasData ? (
          <Suspense fallback={<PreviewLoader />}>
            <SummaryComponent data={data} />
            <SectionsComponent
              data={data}
              onSectionClick={() => {
                /* wired in Phase 3 — sends chat message */
              }}
            />
          </Suspense>
        ) : (
          <div className="flex h-full items-center justify-center text-center">
            <p className="text-sm text-slate-400">{entry.emptyStateMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Wire CopilotPreviewPane into CopilotSidebar**

In `copilot-sidebar.tsx`, add import and replace the preview placeholder:

```tsx
import { CopilotPreviewPane } from "./copilot-preview-pane";
```

Replace the preview placeholder div:
```tsx
{sidebarState === "expanded" && (
  <div className="w-[400px] shrink-0 border-r border-slate-200 overflow-hidden dark:border-slate-700">
    <CopilotPreviewPane />
  </div>
)}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-preview-pane.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/copilot-preview-pane.tsx frontend/src/features/copilot/components/copilot-sidebar.tsx frontend/src/features/copilot/__tests__/copilot-preview-pane.test.tsx
git commit -m "feat(copilot): CopilotPreviewPane with lazy loading from preview registry"
```

---

### Task 9: FocusBar

**Files:**
- Create: `frontend/src/features/copilot/components/focus-bar.tsx`
- Modify: `frontend/src/features/copilot/components/copilot-sidebar.tsx` (inject)
- Test: `frontend/src/features/copilot/__tests__/focus-bar.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/features/copilot/__tests__/focus-bar.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useCopilotStore } from "../store/copilot-store";
import { FocusBar } from "../components/focus-bar";

describe("FocusBar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
      focusSnapshot: { public_name: "Original" },
      interviewSessionId: null,
      interviewProgress: null,
      sidebarState: "expanded",
      isOpen: true,
    });
  });

  it("shows entity label", () => {
    render(<FocusBar />);
    expect(screen.getByText("Oferta Premium")).toBeDefined();
  });

  it("shows 'Salir de Focus' button", () => {
    render(<FocusBar />);
    expect(screen.getByText("Salir de Focus")).toBeDefined();
  });

  it("clears focus and collapses sidebar on exit", async () => {
    const user = userEvent.setup();
    render(<FocusBar />);
    await user.click(screen.getByText("Salir de Focus"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity).toBeNull();
    expect(state.sidebarState).toBe("open");
  });

  it("shows progress dots in interview mode", () => {
    useCopilotStore.setState({
      interviewSessionId: "session-1",
      interviewProgress: {
        currentBlock: "strategy",
        blocksCompleted: ["intro"],
        totalBlocks: 5,
      },
    });
    render(<FocusBar />);
    // Should have 5 dots
    const dots = document.querySelectorAll("[data-testid='progress-dot']");
    expect(dots.length).toBe(5);
  });

  it("renders nothing when no focusEntity", () => {
    useCopilotStore.setState({ focusEntity: null });
    const { container } = render(<FocusBar />);
    expect(container.textContent).toBe("");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/focus-bar.test.tsx`
Expected: FAIL — FocusBar doesn't exist

- [ ] **Step 3: Implement FocusBar**

```tsx
// frontend/src/features/copilot/components/focus-bar.tsx
"use client";

import { BookOpen, Package, Undo2, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { cn } from "@/lib/utils";

const DOMAIN_ICONS: Record<string, typeof Package> = {
  offer: Package,
  brand: BookOpen,
  buyer_persona: User,
};

export function FocusBar() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);
  const interviewProgress = useCopilotStore((s) => s.interviewProgress);
  const clearFocus = useCopilotStore((s) => s.clearFocus);
  const clearInterview = useCopilotStore((s) => s.clearInterview);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);

  if (!focusEntity) return null;

  const Icon = DOMAIN_ICONS[focusEntity.domain] ?? Package;
  const hasSnapshot = focusSnapshot && Object.keys(focusSnapshot).length > 0;

  const handleExitFocus = () => {
    clearInterview();
    clearFocus();
    setSidebarState("open");
  };

  const handleUndoAll = () => {
    // Trigger entity_undo_all via chat message
    // The backend tool handles the actual restoration
    const event = new CustomEvent("copilot:undo-all", {
      detail: { snapshot: focusSnapshot },
    });
    window.dispatchEvent(event);
  };

  return (
    <div className="flex items-center gap-2 border-b border-slate-200 bg-purple-50 px-3 py-2 dark:border-slate-700 dark:bg-purple-900/20">
      {/* Entity icon + label */}
      <Icon className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
      <span className="min-w-0 truncate text-xs font-medium text-purple-800 dark:text-purple-300">
        {focusEntity.label}
      </span>

      {/* Progress dots (interview mode only) */}
      {interviewProgress && (
        <div className="flex items-center gap-1 ml-auto mr-2">
          {Array.from({ length: interviewProgress.totalBlocks }).map((_, i) => {
            const isCompleted = i < interviewProgress.blocksCompleted.length;
            const isCurrent =
              i === interviewProgress.blocksCompleted.length;
            return (
              <div
                key={i}
                data-testid="progress-dot"
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  isCompleted && "bg-green-500",
                  isCurrent && "bg-purple-500 animate-pulse",
                  !isCompleted && !isCurrent && "bg-slate-300 dark:bg-slate-600",
                )}
              />
            );
          })}
        </div>
      )}

      {/* Spacer when no progress */}
      {!interviewProgress && <div className="flex-1" />}

      {/* Undo all */}
      {hasSnapshot && (
        <Button
          size="sm"
          variant="ghost"
          onClick={handleUndoAll}
          className="h-6 gap-1 px-2 text-xs text-purple-600 hover:text-purple-800 dark:text-purple-400"
        >
          <Undo2 className="h-3 w-3" />
          Deshacer todo
        </Button>
      )}

      {/* Exit focus */}
      <Button
        size="sm"
        variant="ghost"
        onClick={handleExitFocus}
        className="h-6 gap-1 px-2 text-xs text-slate-500 hover:text-slate-700"
      >
        <X className="h-3 w-3" />
        Salir de Focus
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Wire FocusBar into CopilotSidebar**

In `copilot-sidebar.tsx`, add import and place FocusBar after CopilotHeader:

```tsx
import { FocusBar } from "./focus-bar";
```

In the chat column `<div>`:
```tsx
<div className="flex w-[380px] shrink-0 flex-col">
  <CopilotHeader />
  <FocusBar />
  <CopilotChat />
</div>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/focus-bar.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/focus-bar.tsx frontend/src/features/copilot/components/copilot-sidebar.tsx frontend/src/features/copilot/__tests__/focus-bar.test.tsx
git commit -m "feat(copilot): FocusBar with entity label, progress dots, undo all"
```

---

### Task 10: FocusModeButton (entry point in editors)

**Files:**
- Create: `frontend/src/features/copilot/components/focus-mode-button.tsx`
- Test: `frontend/src/features/copilot/__tests__/focus-mode-button.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/features/copilot/__tests__/focus-mode-button.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useCopilotStore } from "../store/copilot-store";
import { FocusModeButton } from "../components/focus-mode-button";

describe("FocusModeButton", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: "collapsed",
      isOpen: false,
      focusEntity: null,
      focusSnapshot: null,
    });
  });

  it("activates focus and expands sidebar on click", async () => {
    const user = userEvent.setup();
    render(
      <FocusModeButton
        domain="offer"
        entityId="abc-123"
        label="Oferta Premium"
        entityData={{ public_name: "Oferta Premium" }}
      />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity).toEqual({
      domain: "offer",
      entityId: "abc-123",
      label: "Oferta Premium",
    });
    expect(state.focusSnapshot).toEqual({ public_name: "Oferta Premium" });
    expect(state.sidebarState).toBe("expanded");
  });

  it("renders with sparkles icon and 'Focus' text", () => {
    render(
      <FocusModeButton
        domain="brand"
        label="Mi Marca"
        entityData={{}}
      />,
    );
    expect(screen.getByText("Focus")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/focus-mode-button.test.tsx`
Expected: FAIL — FocusModeButton doesn't exist

- [ ] **Step 3: Implement FocusModeButton**

```tsx
// frontend/src/features/copilot/components/focus-mode-button.tsx
"use client";

import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import type { FocusEntity } from "../store/copilot-store";

interface FocusModeButtonProps {
  domain: FocusEntity["domain"];
  entityId?: string;
  label: string;
  entityData: Record<string, unknown>;
  className?: string;
}

export function FocusModeButton({
  domain,
  entityId,
  label,
  entityData,
  className,
}: FocusModeButtonProps) {
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setFocusSnapshot = useCopilotStore((s) => s.setFocusSnapshot);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);

  const handleActivateFocus = () => {
    setFocusEntity({ domain, entityId, label });
    setFocusSnapshot(entityData);
    clearSelectedFields();
    setSidebarState("expanded");
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleActivateFocus}
      className={className}
    >
      <Sparkles className="mr-1.5 h-3.5 w-3.5 text-purple-500" />
      Focus
    </Button>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/focus-mode-button.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/copilot/components/focus-mode-button.tsx frontend/src/features/copilot/__tests__/focus-mode-button.test.tsx
git commit -m "feat(copilot): FocusModeButton — entry point for activating focus mode"
```

---

### Task 11: CopilotStatusBar (replaces InterviewBanner)

**Files:**
- Create: `frontend/src/features/copilot/components/copilot-status-bar.tsx`
- Test: `frontend/src/features/copilot/__tests__/copilot-status-bar.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/features/copilot/__tests__/copilot-status-bar.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    data: {
      session_id: "session-123",
      domain: "offer",
      domain_label: "Oferta",
      bloques_completados: ["intro", "strategy"],
      total_bloques: 6,
    },
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token") }),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useParams: () => ({ tenantId: "tenant-1" }),
}));

import { useCopilotStore } from "../store/copilot-store";
import { CopilotStatusBar } from "../components/copilot-status-bar";

describe("CopilotStatusBar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      interviewSessionId: null,
      focusEntity: null,
      sidebarState: "collapsed",
      isOpen: false,
    });
  });

  it("shows 'Continuar' button when paused interview exists", () => {
    render(<CopilotStatusBar />);
    expect(screen.getByText(/Continuar/)).toBeDefined();
  });

  it("restores interview on continue click", async () => {
    const user = userEvent.setup();
    render(<CopilotStatusBar />);
    await user.click(screen.getByText(/Continuar/));

    const state = useCopilotStore.getState();
    expect(state.interviewSessionId).toBe("session-123");
    expect(state.sidebarState).toBe("expanded");
  });

  it("is NOT hardcoded to /brand-studio/interview", () => {
    const { container } = render(<CopilotStatusBar />);
    const html = container.innerHTML;
    expect(html).not.toContain("/brand-studio/interview");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-status-bar.test.tsx`
Expected: FAIL — CopilotStatusBar doesn't exist

- [ ] **Step 3: Implement CopilotStatusBar**

```tsx
// frontend/src/features/copilot/components/copilot-status-bar.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { getActiveInterview } from "../api/interview-api";

export function CopilotStatusBar() {
  const interviewSessionId = useCopilotStore((s) => s.interviewSessionId);
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const setInterviewSession = useCopilotStore((s) => s.setInterviewSession);
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const setInterviewProgress = useCopilotStore((s) => s.setInterviewProgress);
  const { getToken } = useAuth();

  const { data: active } = useQuery({
    queryKey: ["interview", "active"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      return getActiveInterview(token);
    },
    staleTime: 60_000,
  });

  // Don't show if interview is already active in sidebar
  if (interviewSessionId) return null;
  // Don't show if sidebar is expanded (user is already in focus)
  if (sidebarState === "expanded") return null;
  // Don't show if no paused interview
  if (!active?.bloques_completados) return null;

  const handleContinue = () => {
    setInterviewSession(active.session_id);
    setFocusEntity({
      domain: active.domain as "brand" | "offer" | "buyer_persona",
      label: active.domain_label,
    });
    setInterviewProgress({
      currentBlock: "",
      blocksCompleted: active.bloques_completados,
      totalBlocks: active.total_bloques,
    });
    setSidebarState("expanded");
  };

  return (
    <div className="mx-4 mt-2 flex items-center justify-between rounded-lg border border-purple-500 bg-[#1e1b4b] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <div className="h-2 w-2 animate-pulse rounded-full bg-purple-500" />
        <span className="text-sm text-white">
          Entrevista {active.domain_label} en curso
        </span>
        <span className="text-xs text-gray-400">
          ({active.bloques_completados.length}/{active.total_bloques} bloques)
        </span>
      </div>
      <Button
        size="sm"
        onClick={handleContinue}
        className="bg-purple-600 text-xs text-white hover:bg-purple-700"
      >
        Continuar →
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Wire CopilotStatusBar into layout**

In `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`, add import and place inside main:

```tsx
import { CopilotStatusBar } from "@/features/copilot/components/copilot-status-bar";
```

Inside `<main>`, before `<MemoizedChildren>`:
```tsx
<CopilotStatusBar />
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/copilot/__tests__/copilot-status-bar.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/copilot-status-bar.tsx frontend/src/features/copilot/__tests__/copilot-status-bar.test.tsx frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/layout.tsx
git commit -m "feat(copilot): CopilotStatusBar replaces hardcoded InterviewBanner"
```

---

### Task 12: Left sidebar auto-collapse at <1280px

**Files:**
- Modify: `frontend/src/components/shared/layout/sidebar-context.tsx`
- Test: `frontend/src/components/shared/layout/__tests__/sidebar-context.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/components/shared/layout/__tests__/sidebar-context.test.tsx
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// We test the auto-collapse logic directly via a helper
import {
  SidebarProvider,
  useSidebar,
} from "../sidebar-context";

describe("Sidebar auto-collapse", () => {
  let originalInnerWidth: number;

  beforeEach(() => {
    originalInnerWidth = window.innerWidth;
  });

  afterEach(() => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it("should expose isCollapsed state", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SidebarProvider>{children}</SidebarProvider>
    );
    const { result } = renderHook(() => useSidebar(), { wrapper });
    expect(typeof result.current.isCollapsed).toBe("boolean");
  });
});
```

- [ ] **Step 2: Run test (should pass — this is a baseline)**

Run: `cd frontend && npx vitest run src/components/shared/layout/__tests__/sidebar-context.test.tsx`
Expected: PASS (baseline)

- [ ] **Step 3: Add auto-collapse logic to sidebar context**

Read the current `sidebar-context.tsx` and add a `useEffect` that watches `window.innerWidth` via `matchMedia` and auto-collapses the left sidebar when viewport < 1280px:

In `SidebarProvider`, add:
```tsx
// Auto-collapse on viewport < 1280px
useEffect(() => {
  const mql = window.matchMedia("(max-width: 1279px)");
  const handler = (e: MediaQueryListEvent | MediaQueryList) => {
    if (e.matches && !isCollapsed) {
      setIsCollapsed(true);
    }
  };
  // Check immediately
  handler(mql);
  mql.addEventListener("change", handler);
  return () => mql.removeEventListener("change", handler);
}, []);
```

This auto-collapses on narrow viewports but doesn't prevent manual expansion.

- [ ] **Step 4: Run test to verify it still passes**

Run: `cd frontend && npx vitest run src/components/shared/layout/__tests__/sidebar-context.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/shared/layout/sidebar-context.tsx frontend/src/components/shared/layout/__tests__/sidebar-context.test.tsx
git commit -m "feat(layout): auto-collapse left sidebar at viewport <1280px"
```

---

## Integration Verification

### Task 13: Full test suite + lint + types

**Files:** None created — verification only.

- [ ] **Step 1: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: PASS (no new violations)

- [ ] **Step 2: Run backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: All tests pass

- [ ] **Step 3: Run frontend lint**

Run: `cd frontend && npx eslint src/`
Expected: PASS (no new violations)

- [ ] **Step 4: Run frontend types**

Run: `cd frontend && npx tsc --noEmit`
Expected: No new errors

- [ ] **Step 5: Run frontend tests**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

- [ ] **Step 6: Run architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All pass (focus tools follow DDD, no cross-module imports)

- [ ] **Step 7: Verify CopilotPanel references removed**

Run: `grep -r "CopilotPanel" frontend/src/app/ --include="*.tsx" --include="*.ts"`
Expected: No results (all replaced by CopilotSidebar)

Run: `grep -r "InterviewBanner" frontend/src/app/ --include="*.tsx" --include="*.ts"`
Expected: No results (all replaced by CopilotStatusBar)

- [ ] **Step 8: Final commit if any cleanup was needed**

```bash
git add -A  # Only if cleanup was needed
git commit -m "chore(copilot): Phase 2 cleanup — remove CopilotPanel and InterviewBanner references"
```

---

## Summary of Created/Modified Files

### Backend — Created
- `backend/src/modules/copilot/application/tools/focus/__init__.py`
- `backend/src/modules/copilot/application/tools/focus/entity_write.py`
- `backend/src/modules/copilot/application/tools/focus/entity_read.py`
- `backend/src/modules/copilot/application/tools/focus/entity_undo_all.py`
- `backend/src/modules/copilot/infrastructure/context/focus_context_loader.py`
- `backend/tests/modules/copilot/test_copilot_state.py`
- `backend/tests/modules/copilot/test_focus_context_loader.py`
- `backend/tests/modules/copilot/test_focus_tools.py`
- `backend/tests/modules/copilot/test_tool_registry_focus.py`
- `backend/tests/modules/copilot/test_orchestrator_focus.py`

### Backend — Modified
- `backend/src/modules/copilot/application/orchestrator/state.py` (add focus_entity_data)
- `backend/src/modules/copilot/application/orchestrator/chat.py` (load focus entity data)
- `backend/src/modules/copilot/application/tools/registry.py` (focus mode selection)
- `backend/src/modules/copilot/infrastructure/context/context_loader_registry.py` (register focus)

### Frontend — Created
- `frontend/src/features/copilot/components/copilot-sidebar.tsx`
- `frontend/src/features/copilot/components/copilot-header.tsx`
- `frontend/src/features/copilot/components/copilot-preview-pane.tsx`
- `frontend/src/features/copilot/components/focus-bar.tsx`
- `frontend/src/features/copilot/components/focus-mode-button.tsx`
- `frontend/src/features/copilot/components/copilot-status-bar.tsx`
- `frontend/src/features/copilot/__tests__/copilot-sidebar.test.tsx`
- `frontend/src/features/copilot/__tests__/copilot-preview-pane.test.tsx`
- `frontend/src/features/copilot/__tests__/focus-bar.test.tsx`
- `frontend/src/features/copilot/__tests__/focus-mode-button.test.tsx`
- `frontend/src/features/copilot/__tests__/copilot-status-bar.test.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/__tests__/layout.test.tsx`
- `frontend/src/components/shared/layout/__tests__/sidebar-context.test.tsx`

### Frontend — Modified
- `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` (flex layout + CopilotSidebar)
- `frontend/src/components/shared/layout/sidebar-context.tsx` (auto-collapse <1280px)

### Frontend — Deprecated (NOT deleted yet — Phase 4)
- `frontend/src/features/copilot/components/CopilotPanel.tsx`
- `frontend/src/components/shared/interview-banner.tsx`
