"""Tests for ``advance_guided_block`` payload enrichment (Fase 09.C).

Verifies the tool emits ``suggested_question`` when the helper returns
a hint, and degrades silently otherwise.

The persistence and core context dependencies are stubbed so the test
runs natively in WSL without a database.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.guided.state import GuidedState


@pytest.fixture
def patched_advance(monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    """Stub conversation/tenant context + persistence so tool runs DB-free."""
    conv_id = str(uuid4())
    tenant_id = str(uuid4())

    from src.modules.copilot.application.tools.guided import advance as advance_module

    monkeypatch.setattr(advance_module, "get_conversation_id", lambda: conv_id)
    monkeypatch.setattr(advance_module, "get_tenant_id", lambda: tenant_id)

    seed = GuidedState(
        domain="brand",
        entity_id=None,
        current_block_id="identity",
        completed_blocks=[],
        started_at="2026-04-24T00:00:00Z",
    )
    monkeypatch.setattr(advance_module, "read_state", lambda *_, **__: seed)
    monkeypatch.setattr(advance_module, "write_state", lambda *_, **__: None)

    return conv_id, tenant_id


def test_advance_includes_suggested_question_when_hint_available(
    patched_advance: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module
    from src.modules.copilot.application.tools.guided.advance import advance_guided_block

    fake_hint = {
        "path": "identity.brand_name",
        "section": "identity",
        "question_es": "¿Cómo se llama tu marca?",
    }
    monkeypatch.setattr(
        advance_module,
        "_compute_suggested_question",
        lambda **_: fake_hint,
    )

    raw = advance_guided_block.invoke({"block_id": "identity"})
    payload = json.loads(raw)

    assert payload["ui_action"]["type"] == "guided_block_advanced"
    assert payload["ui_action"]["suggested_question"] == fake_hint


def test_advance_omits_suggested_question_when_hint_none(
    patched_advance: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module
    from src.modules.copilot.application.tools.guided.advance import advance_guided_block

    monkeypatch.setattr(
        advance_module,
        "_compute_suggested_question",
        lambda **_: None,
    )

    raw = advance_guided_block.invoke({"block_id": "identity"})
    payload = json.loads(raw)

    assert payload["ui_action"]["type"] == "guided_block_advanced"
    assert "suggested_question" not in payload["ui_action"]


def test_compute_helper_returns_none_when_state_reader_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module

    monkeypatch.setattr(advance_module, "read_entity_state", lambda *_, **__: None)
    with patch.object(advance_module, "SessionLocal") as session_local:
        session_local.return_value.close = lambda: None
        result = advance_module._compute_suggested_question(
            domain="brand",
            entity_id=None,
            tenant_id=str(uuid4()),
            section="identity",
        )
    assert result is None


def test_compute_helper_handles_invalid_tenant_id() -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module

    result = advance_module._compute_suggested_question(
        domain="brand",
        entity_id=None,
        tenant_id="not-a-uuid",
        section="identity",
    )
    assert result is None


def test_compute_helper_handles_none_tenant_id() -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module

    result = advance_module._compute_suggested_question(
        domain="brand",
        entity_id=None,
        tenant_id=None,
        section="identity",
    )
    assert result is None


def test_compute_helper_returns_hint_when_state_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.modules.copilot.application.tools.guided import advance as advance_module

    monkeypatch.setattr(
        advance_module,
        "read_entity_state",
        lambda *_, **__: {"identity": {}},
    )
    monkeypatch.setattr(
        advance_module,
        "build_question_hint",
        lambda *_, **__: {"path": "identity.brand_name", "question_es": "X"},
    )
    with patch.object(advance_module, "SessionLocal") as session_local:
        session_local.return_value.close = lambda: None
        result = advance_module._compute_suggested_question(
            domain="brand",
            entity_id=None,
            tenant_id=str(uuid4()),
            section="identity",
        )
    assert result == {"path": "identity.brand_name", "question_es": "X"}
