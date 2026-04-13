"""Tests that focus tools never leak DB sessions, regardless of failure point.

Covers audit items C3 (session leak) and D2 (SessionLocal direct use).
Verifies:
  - Session closes on invalid UUID (fail-fast, before session creation)
  - Session closes on get_persister error (unknown domain)
  - Session closes on FocusContextLoader error
  - _safe_session context manager guarantees close on any exception
"""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.tools.focus.entity_read import entity_read
from src.modules.copilot.application.tools.focus.entity_undo_all import (
    entity_undo_all,
)
from src.modules.copilot.application.tools.focus.entity_write import entity_write

# ── entity_write: UUID validation before session ─────────────────────────


class TestEntityWriteSessionSafety:
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_invalid_uuid_returns_error_without_opening_session(self, mock_validate, mock_session_cls, mock_get_tid):
        """Invalid entity_id should fail BEFORE creating a session."""
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()

        result = entity_write.invoke(
            {
                "domain": "brand",
                "entity_id": "not-a-uuid",
                "field_path": "identity.brand_name",
                "value": "Test",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "UUID" in parsed["error"]
        # Session was never created
        mock_session_cls.assert_not_called()

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_session_closes_when_get_persister_raises(
        self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister
    ):
        """get_persister raising should still close the session via context manager."""
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_get_persister.side_effect = ValueError("No persister for domain 'invalid'")

        result = entity_write.invoke(
            {
                "domain": "invalid",
                "entity_id": str(uuid4()),
                "field_path": "some_field",
                "value": "test",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_write.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_write.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    @patch("src.modules.copilot.application.tools.focus.entity_write.validate_field_path")
    def test_session_closes_on_persist_error(self, mock_validate, mock_session_cls, mock_get_tid, mock_get_persister):
        """Persister.persist raising should still close the session."""
        mock_validate.return_value = True
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_persister.persist.side_effect = RuntimeError("DB connection lost")
        mock_get_persister.return_value = mock_persister

        result = entity_write.invoke(
            {
                "domain": "brand",
                "entity_id": str(uuid4()),
                "field_path": "identity.brand_name",
                "value": "test",
                "reason": "test",
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()


# ── entity_read: session safety ──────────────────────────────────────────


class TestEntityReadSessionSafety:
    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_session_closes_when_loader_init_raises(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        """FocusContextLoader constructor raising should still close session."""
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader_cls.side_effect = TypeError("Bad argument")

        result = entity_read.invoke({"domain": "brand", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.FocusContextLoader")
    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_session_closes_when_load_raises(self, mock_session_cls, mock_get_tid, mock_loader_cls):
        """FocusContextLoader.load raising should still close session."""
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_loader = MagicMock()
        mock_loader.load.side_effect = RuntimeError("Query timeout")
        mock_loader_cls.return_value = mock_loader

        result = entity_read.invoke({"domain": "offer", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_read.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_read.SessionLocal")
    def test_no_session_created_when_no_tenant(self, mock_session_cls, mock_get_tid):
        """When tenant is None, session should never be opened."""
        mock_get_tid.return_value = None

        result = entity_read.invoke({"domain": "offer", "entity_id": str(uuid4())})
        parsed = json.loads(result)
        assert "error" in parsed
        mock_session_cls.assert_not_called()


# ── entity_undo_all: UUID validation + session safety ────────────────────


class TestEntityUndoAllSessionSafety:
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_invalid_uuid_returns_error_without_opening_session(self, mock_session_cls, mock_get_tid):
        """Invalid entity_id should fail BEFORE creating a session."""
        mock_get_tid.return_value = uuid4()

        result = entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": "definitely-not-a-uuid",
                "snapshot": {"public_name": "test"},
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "UUID" in parsed["error"]
        mock_session_cls.assert_not_called()

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_session_closes_when_get_persister_raises(self, mock_session_cls, mock_get_tid, mock_get_persister):
        """get_persister raising should still close session via context manager."""
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_get_persister.side_effect = ValueError("Unknown domain")

        result = entity_undo_all.invoke(
            {
                "domain": "bogus",
                "entity_id": str(uuid4()),
                "snapshot": {"field": "val"},
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_persister")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_session_closes_on_persist_error(self, mock_session_cls, mock_get_tid, mock_get_persister):
        """Persister.persist raising should still close session."""
        mock_get_tid.return_value = uuid4()
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_persister = MagicMock()
        mock_persister.persist.side_effect = RuntimeError("Deadlock")
        mock_get_persister.return_value = mock_persister

        result = entity_undo_all.invoke(
            {
                "domain": "offer",
                "entity_id": str(uuid4()),
                "snapshot": {"public_name": "Original"},
            }
        )
        parsed = json.loads(result)
        assert "error" in parsed
        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.get_tenant_id")
    @patch("src.modules.copilot.application.tools.focus.entity_undo_all.SessionLocal")
    def test_no_session_created_when_no_tenant(self, mock_session_cls, mock_get_tid):
        """When tenant is None, session should never be opened."""
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
        mock_session_cls.assert_not_called()


# ── _safe_session context manager unit tests ─────────────────────────────


class TestSafeSessionContextManager:
    """Verify _safe_session guarantees close on any exit path."""

    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    def test_close_called_on_normal_exit(self, mock_session_cls):
        from src.modules.copilot.application.tools.focus.entity_write import (
            _safe_session,
        )

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        with _safe_session() as db:
            assert db is mock_db

        mock_db.close.assert_called_once()

    @patch("src.modules.copilot.application.tools.focus.entity_write.SessionLocal")
    def test_close_called_on_exception(self, mock_session_cls):
        from src.modules.copilot.application.tools.focus.entity_write import (
            _safe_session,
        )

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        msg = "boom"
        with pytest.raises(RuntimeError, match=msg), _safe_session():
            raise RuntimeError(msg)

        mock_db.close.assert_called_once()
