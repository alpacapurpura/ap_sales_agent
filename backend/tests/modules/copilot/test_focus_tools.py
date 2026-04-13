"""Tests for Focus Mode tools: entity_write, entity_read, entity_undo_all."""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.tools.focus.entity_read import entity_read
from src.modules.copilot.application.tools.focus.entity_undo_all import entity_undo_all
from src.modules.copilot.application.tools.focus.entity_write import entity_write


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

        result = entity_write.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "field_path": "headline_promise",
                "value": "Transforma tu negocio en 90 días",
                "reason": "User provided their main promise",
            }
        )
        parsed = json.loads(result)
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["delta"]["headline_promise"] == "Transforma tu negocio en 90 días"
        assert "headline_promise" in parsed["text"]
        mock_persister.persist.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_rejects_invalid_field_path(self, mock_validate):
        mock_validate.return_value = False
        result = entity_write.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "field_path": "nonexistent_field",
                "value": "test",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "nonexistent_field" in parsed["error"]

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_returns_error_when_no_tenant(self, mock_validate, mock_get_tid):
        mock_validate.return_value = True
        mock_get_tid.return_value = None

        result = entity_write.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "field_path": "headline_promise",
                "value": "test",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "tenant" in parsed["error"].lower()

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_reason_is_included_in_ui_action(self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister):
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_get_persister.return_value = MagicMock()

        result = entity_write.invoke(
            {
                "domain": "brand",
                "entity_id": str(uuid4()),
                "field_path": "identity.brand_name",
                "value": "Mi Marca",
                "reason": "Extracted from website",
            }
        )
        parsed = json.loads(result)
        assert parsed["ui_action"]["reason"] == "Extracted from website"

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_db_is_always_closed_on_success(self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister):
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_get_persister.return_value = MagicMock()

        entity_write.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "field_path": "archetype",
                "value": "programa",
                "reason": "test",
            }
        )
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_db_is_always_closed_on_persister_error(
        self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister
    ):
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_persister.persist.side_effect = RuntimeError("DB error")
        mock_get_persister.return_value = mock_persister

        result = entity_write.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "field_path": "archetype",
                "value": "programa",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()


class TestEntityRead:
    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_reads_full_entity(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.return_value = {"public_name": "Oferta Premium", "archetype": "programa"}
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke({"domain": "offer", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert parsed["data"]["public_name"] == "Oferta Premium"
        assert parsed["data"]["archetype"] == "programa"
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_filters_by_section(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.return_value = {
            "identity.brand_name": "Mi Marca",
            "identity.tagline": "El mejor",
            "positioning.target_audience": "Adultos",
            "tone_of_voice": "Amigable",
        }
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke(
            {
                "domain": "brand",
                "entity_id": str(uuid4()),
                "section": "identity",
            }
        )
        parsed = json.loads(result)
        assert "identity.brand_name" in parsed["data"]
        assert "identity.tagline" in parsed["data"]
        assert "positioning.target_audience" not in parsed["data"]
        assert parsed["section"] == "identity"
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    def test_returns_error_when_no_tenant(self, mock_get_tid):
        mock_get_tid.return_value = None

        result = entity_read.invoke({"domain": "offer", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert "error" in parsed

    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_db_is_always_closed(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.side_effect = RuntimeError("Load error")
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke({"domain": "offer", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_section_filter_accepts_underscore_prefix(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        """Section filter should work with both dot-notation and underscore-prefixed keys."""
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.return_value = {
            "marketing_pain_points": "Much pain",
            "marketing_desires": "Big dreams",
            "headline_promise": "Transform",
        }
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "section": "marketing",
            }
        )
        parsed = json.loads(result)
        assert "marketing_pain_points" in parsed["data"]
        assert "marketing_desires" in parsed["data"]
        assert "headline_promise" not in parsed["data"]


class TestEntityUndoAll:
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_restores_snapshot(self, mock_session_cls, mock_get_tid, mock_get_persister):
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_get_persister.return_value = mock_persister

        snapshot = {"public_name": "Original", "archetype": "producto"}
        result = entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "snapshot": snapshot,
            }
        )
        parsed = json.loads(result)
        assert parsed["text"] == "Entidad restaurada al estado inicial del focus."
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["delta"] == snapshot
        mock_persister.persist.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_persists_all_snapshot_fields(self, mock_session_cls, mock_get_tid, mock_get_persister):
        tid = uuid4()
        eid = uuid4()
        mock_get_tid.return_value = tid
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_get_persister.return_value = mock_persister

        snapshot = {
            "public_name": "Original",
            "archetype": "producto",
            "headline_promise": "Promesa original",
        }
        entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": str(eid),
                "snapshot": snapshot,
            }
        )

        call_kwargs = mock_persister.persist.call_args
        assert call_kwargs is not None
        # fields_to_persist should contain all keys from snapshot
        fields_persisted = call_kwargs.kwargs.get("fields_to_persist") or call_kwargs.args[2]
        assert set(fields_persisted) == set(snapshot.keys())

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    def test_returns_error_when_no_tenant(self, mock_get_tid):
        mock_get_tid.return_value = None

        result = entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "snapshot": {"public_name": "test"},
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_db_is_always_closed_on_error(self, mock_session_cls, mock_get_tid, mock_get_persister):
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_persister.persist.side_effect = RuntimeError("DB exploded")
        mock_get_persister.return_value = mock_persister

        result = entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "snapshot": {"public_name": "test"},
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()


class TestFocusToolsInit:
    def test_focus_tools_exports_all_three(self):
        from src.modules.copilot.application.tools.focus import FOCUS_TOOLS

        assert len(FOCUS_TOOLS) == 3
        tool_names = {t.name for t in FOCUS_TOOLS}
        assert "entity_write" in tool_names
        assert "entity_read" in tool_names
        assert "entity_undo_all" in tool_names
