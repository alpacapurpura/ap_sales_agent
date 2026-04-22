"""Tests for interview context loading in CopilotOrchestrator.

Focus mode was retired on 2026-04-21. This file used to validate that
``FocusContextDTO`` propagated into orchestrator state; now it only covers
interview mode + base context fallback.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from src.modules.copilot.api.dto import ClientContextDTO
from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = None
    return db


class TestOrchestratorContextBuilding:
    def test_interview_session_id_passed_to_state(self) -> None:
        orch = CopilotOrchestrator(_make_mock_db())
        sid = str(uuid4())
        context = ClientContextDTO(
            current_route="/brand-studio/interview",
            interview_session_id=sid,
        )
        client_ctx = orch._build_client_context(context)
        assert client_ctx["interview_session_id"] == sid

    def test_no_interview_key_when_absent(self) -> None:
        orch = CopilotOrchestrator(_make_mock_db())
        context = ClientContextDTO(current_route="/brand-studio")
        client_ctx = orch._build_client_context(context)
        assert client_ctx.get("interview_session_id") is None

    def test_none_context_returns_defaults(self) -> None:
        orch = CopilotOrchestrator(_make_mock_db())
        client_ctx = orch._build_client_context(None)
        assert client_ctx["current_route"] is None
        assert client_ctx["selected_fields"] == []
        assert client_ctx["locale"] == "es"
