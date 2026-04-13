# backend/tests/modules/copilot/test_focus_context_loader.py
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.context.focus_context_loader import FocusContextLoader


class TestFocusContextLoader:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.loader = FocusContextLoader(self.mock_db)
        self.tenant_id = uuid4()

    @patch("src.modules.copilot.infrastructure.context.focus_context_loader.get_persister")
    def test_load_offer_entity(self, mock_get_persister):
        entity_id = uuid4()
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {"public_name": "Oferta Premium", "archetype": "programa"}
        mock_get_persister.return_value = mock_persister
        result = self.loader.load(self.tenant_id, "offer", str(entity_id))
        assert result["public_name"] == "Oferta Premium"
        mock_persister.load_existing.assert_called_once_with(self.tenant_id, entity_id)

    @patch("src.modules.copilot.infrastructure.context.focus_context_loader.get_persister")
    def test_load_brand_entity_no_entity_id(self, mock_get_persister):
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {"identity.brand_name": "Mi Marca"}
        mock_get_persister.return_value = mock_persister
        result = self.loader.load(self.tenant_id, "brand", None)
        assert result["identity.brand_name"] == "Mi Marca"

    @patch("src.modules.copilot.infrastructure.context.focus_context_loader.get_persister")
    def test_load_returns_empty_dict_when_not_found(self, mock_get_persister):
        mock_persister = MagicMock()
        mock_persister.load_existing.return_value = {}
        mock_get_persister.return_value = mock_persister
        result = self.loader.load(self.tenant_id, "offer", str(uuid4()))
        assert result == {}

    def test_load_unknown_domain_raises(self):
        with pytest.raises(ValueError, match="No persister registered"):
            self.loader.load(self.tenant_id, "unknown_domain", None)
