"""Tests for layered system prompt composition."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from src.modules.copilot.application.orchestrator.graph import build_system_prompt

if TYPE_CHECKING:
    from typing import Any


def _make_state(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
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


class TestBuildSystemPrompt:
    """Tests for the build_system_prompt function."""

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_chat_mode_no_focus_no_interview(self, mock_behavior: MagicMock, mock_completion: MagicMock) -> None:
        """When no focus or interview, only base prompt is returned."""
        mock_completion.return_value = "## Completion snapshot"
        mock_behavior.return_value = "User is active"
        state = _make_state()

        result = build_system_prompt(state)

        # Base prompt should be present
        assert len(result) > 100
        # Focus/interview markers should NOT be present
        assert "FOCUS MODE" not in result
        assert "INTERVIEW MODE" not in result

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_focus_mode_appends_focus_layer(self, mock_behavior: MagicMock, mock_completion: MagicMock) -> None:
        """When focus context is present, focus layer is appended."""
        mock_completion.return_value = ""
        mock_behavior.return_value = ""
        state = _make_state(
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
        assert "offer" in result.lower()

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_interview_mode_appends_interview_layer(self, mock_behavior: MagicMock, mock_completion: MagicMock) -> None:
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

        state = _make_state(
            client_context={
                "current_route": "/offer-studio/offer/123",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
                "focus": {"domain": "offer", "entity_id": "123"},
                "interview_session_id": "session-1",
            },
            interview_session=mock_session,
            focus_entity_data={"name": "Test Offer"},
        )

        result = build_system_prompt(state)

        # Both focus and interview should be present
        assert "FOCUS MODE" in result or "focus" in result.lower()
        assert "INTERVIEW" in result or "interview" in result.lower()

    @patch("src.modules.copilot.application.orchestrator.graph._get_completion_snapshot")
    @patch("src.modules.copilot.application.orchestrator.graph._get_behavior_summary")
    def test_focus_without_entity_data_skips_focus_layer(
        self, mock_behavior: MagicMock, mock_completion: MagicMock
    ) -> None:
        """Focus context present but no entity data loaded — skip focus layer."""
        mock_completion.return_value = ""
        mock_behavior.return_value = ""
        state = _make_state(
            client_context={
                "current_route": "/offer-studio",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
                "focus": {"domain": "offer", "entity_id": "123"},
            },
            # NOTE: no focus_entity_data key
        )

        result = build_system_prompt(state)

        assert "FOCUS MODE" not in result
