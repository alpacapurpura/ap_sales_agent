"""Tests for CopilotOrchestrator._load_focus_entity_data."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator


class TestOrchestratorFocusLoading:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.orchestrator = CopilotOrchestrator(self.mock_db)

    @patch("src.modules.copilot.application.orchestrator.chat.FocusContextLoader")
    def test_loads_focus_entity_data_into_state(self, mock_loader_cls):
        mock_loader = MagicMock()
        mock_loader.load.return_value = {"public_name": "Oferta Premium", "archetype": "programa"}
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

    @patch("src.modules.copilot.application.orchestrator.chat.FocusContextLoader")
    def test_returns_none_on_exception(self, mock_loader_cls):
        mock_loader_cls.side_effect = Exception("DB error")
        client_ctx = {"focus": {"domain": "offer", "entity_id": str(uuid4())}}
        result = self.orchestrator._load_focus_entity_data(client_ctx, uuid4())
        assert result is None
