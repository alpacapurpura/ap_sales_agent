"""Integration test for Interview Engine lifecycle."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)


class TestInterviewLifecycle:
    """Full lifecycle: start → get state → get active → pause → resume → abandon."""

    def test_start_creates_active_session(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            # Mock conversation repo since we don't have the conversations table in test DB
            svc.conversation_repo = MagicMock()

            result = svc.start_interview(
                tenant_id=tenant_id, user_id=user_id, domain="brand"
            )

            assert "session_id" in result
            assert "conversation_id" in result
            assert "initial_message" in result
            assert result["config"]["domain"] == "brand"

    def test_get_active_returns_session(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
            active = svc.get_active(tenant_id)

            assert active is not None
            assert active["domain"] == "brand"
            assert active["domain_label"] == "Brand Studio"

    def test_get_state_returns_mapa_and_config(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            result = svc.start_interview(
                tenant_id=tenant_id, user_id=user_id, domain="brand"
            )
            state = svc.get_state(result["session_id"], tenant_id)

            assert state is not None
            assert state["bloque_actual"] == "identidad"
            assert state["bloques_completados"] == []
            assert state["messages_count"] == 0

    def test_pause_and_resume(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            result = svc.start_interview(
                tenant_id=tenant_id, user_id=user_id, domain="brand"
            )
            session_id = result["session_id"]

            # Pause
            assert svc.pause(session_id, tenant_id) is True
            assert svc.get_active(tenant_id) is None

            # Resume via start with resume_session_id
            resumed = svc.start_interview(
                tenant_id=tenant_id,
                user_id=user_id,
                domain="brand",
                resume_session_id=session_id,
            )
            assert resumed["session_id"] == session_id
            assert svc.get_active(tenant_id) is not None

    def test_cannot_start_second_active(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
            with pytest.raises(ValueError, match="Active session exists"):
                svc.start_interview(
                    tenant_id=tenant_id, user_id=user_id, domain="brand"
                )

    def test_abandon_allows_new_start(self, db):
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            result = svc.start_interview(
                tenant_id=tenant_id, user_id=user_id, domain="brand"
            )
            assert svc.abandon(result["session_id"], tenant_id) is True
            assert svc.get_active(tenant_id) is None

            # Can start a new one after abandoning
            new_result = svc.start_interview(
                tenant_id=tenant_id, user_id=user_id, domain="brand"
            )
            assert new_result["session_id"] != result["session_id"]

    def test_different_tenants_independent(self, db):
        user_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.session_repo = InterviewSessionRepository(db)
            svc.conversation_repo = MagicMock()

            svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")
            svc.start_interview(tenant_id=tenant_b, user_id=user_id, domain="brand")

            assert svc.get_active(tenant_a) is not None
            assert svc.get_active(tenant_b) is not None
