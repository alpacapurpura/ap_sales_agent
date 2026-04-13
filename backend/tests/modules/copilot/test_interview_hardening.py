"""Tests for interview session hardening: duplicate prevention + session expiry.

Covers:
- C4: Race condition on concurrent sessions (IntegrityError handling)
- R5: No session expiry (expire_stale_sessions)
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.copilot.domain.interview_configs.brand_config import (
    BRAND_INTERVIEW_CONFIG,
)
from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)
from src.modules.copilot.infrastructure.models.interview_session_model import (
    InterviewSessionModel,
)
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
from src.shared.domain.datetime_utils import utc_now


def _make_service(db):
    """Create InterviewService with mocked conversation_repo."""
    with patch.object(InterviewService, "__init__", lambda self, x: None):
        svc = InterviewService.__new__(InterviewService)
        svc.db = db
        svc.session_repo = InterviewSessionRepository(db)
        svc.conversation_repo = MagicMock()
        return svc


class TestDuplicateSessionPrevention:
    """C4: Gracefully handle IntegrityError when concurrent requests create duplicate active sessions."""

    def test_start_returns_existing_when_duplicate_detected(self, db):
        """If a race condition creates a duplicate, service returns the existing session."""
        tenant_id = uuid4()
        user_id = uuid4()
        svc = _make_service(db)

        # Create first session normally
        result1 = svc.start_interview(
            tenant_id=tenant_id,
            user_id=user_id,
            domain="brand",
        )
        assert "session_id" in result1

        # Simulate: get_active_by_domain returns None (race condition window),
        # but the DB insert raises IntegrityError due to unique constraint
        original_save = svc.session_repo.save

        call_count = 0

        def save_that_raises_once(session):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise IntegrityError(
                    statement="INSERT INTO interview_sessions ...",
                    params={},
                    orig=Exception("duplicate key value violates unique constraint"),
                )
            return original_save(session)

        svc2 = _make_service(db)

        # Patch get_active_by_domain to return None first (simulating race),
        # then return the real session on retry
        original_get = svc2.session_repo.get_active_by_domain

        get_call_count = 0

        def get_active_race(tenant_id, domain):
            nonlocal get_call_count
            get_call_count += 1
            if get_call_count == 1:
                return None  # Race condition: doesn't see the other session yet
            return original_get(tenant_id, domain)

        svc2.session_repo.get_active_by_domain = get_active_race
        svc2.session_repo.save = save_that_raises_once

        result2 = svc2.start_interview(
            tenant_id=tenant_id,
            user_id=user_id,
            domain="brand",
        )

        # Should return the existing session, not raise an error
        assert result2["session_id"] == result1["session_id"]

    def test_integrity_error_on_non_duplicate_still_raises(self, db):
        """IntegrityError from non-duplicate causes (e.g. FK violation) should still propagate."""
        tenant_id = uuid4()
        user_id = uuid4()
        svc = _make_service(db)

        # Patch save to raise IntegrityError, and get_active_by_domain to always return None
        def save_always_raises(session):
            raise IntegrityError(
                statement="INSERT INTO interview_sessions ...",
                params={},
                orig=Exception("violates foreign key constraint"),
            )

        svc.session_repo.save = save_always_raises
        svc.session_repo.get_active_by_domain = lambda tid, d: None

        with pytest.raises(IntegrityError):
            svc.start_interview(
                tenant_id=tenant_id,
                user_id=user_id,
                domain="brand",
            )


class TestSessionExpiry:
    """R5: Sessions should be marked ABANDONED after 7 days of inactivity."""

    def test_expire_stale_sessions_marks_abandoned(self, db):
        """Sessions inactive > 7 days are marked ABANDONED."""
        tenant_id = uuid4()
        repo = InterviewSessionRepository(db)

        # Create a session
        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        repo.save(session)
        db.commit()

        # Manually set updated_at to 8 days ago
        model = db.get(InterviewSessionModel, session.id)
        model.updated_at = utc_now() - timedelta(days=8)
        db.commit()

        # Run expiry
        svc = _make_service(db)
        expired_count = svc.expire_stale_sessions(tenant_id=tenant_id)

        assert expired_count == 1

        # Verify session is now abandoned
        loaded = repo.get_by_id(session.id, tenant_id)
        assert loaded is not None
        assert loaded.status == InterviewStatus.ABANDONED

    def test_expire_does_not_touch_recent_sessions(self, db):
        """Sessions with recent activity are left alone."""
        tenant_id = uuid4()
        repo = InterviewSessionRepository(db)

        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        repo.save(session)
        db.commit()

        # updated_at is now() — within the 7-day window
        svc = _make_service(db)
        expired_count = svc.expire_stale_sessions(tenant_id=tenant_id)

        assert expired_count == 0

        loaded = repo.get_by_id(session.id, tenant_id)
        assert loaded.status == InterviewStatus.ACTIVE

    def test_expire_does_not_touch_already_completed(self, db):
        """Completed sessions should not be changed to abandoned."""
        tenant_id = uuid4()
        repo = InterviewSessionRepository(db)

        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        # Complete the session by advancing through all blocks
        for block in BRAND_INTERVIEW_CONFIG.bloques:
            session.advance_block(block.id)
        repo.save(session)
        db.commit()

        # Set updated_at to 8 days ago
        model = db.get(InterviewSessionModel, session.id)
        model.updated_at = utc_now() - timedelta(days=8)
        db.commit()

        svc = _make_service(db)
        expired_count = svc.expire_stale_sessions(tenant_id=tenant_id)

        assert expired_count == 0

    def test_expire_only_affects_correct_tenant(self, db):
        """Expiry only affects sessions for the given tenant."""
        tenant_a = uuid4()
        tenant_b = uuid4()
        repo = InterviewSessionRepository(db)

        session_a = InterviewSession.create(
            tenant_id=tenant_a,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        session_b = InterviewSession.create(
            tenant_id=tenant_b,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        repo.save(session_a)
        repo.save(session_b)
        db.commit()

        # Make both stale
        for sid in [session_a.id, session_b.id]:
            model = db.get(InterviewSessionModel, sid)
            model.updated_at = utc_now() - timedelta(days=8)
        db.commit()

        svc = _make_service(db)
        expired_count = svc.expire_stale_sessions(tenant_id=tenant_a)

        assert expired_count == 1

        # Tenant B's session is still active
        loaded_b = repo.get_by_id(session_b.id, tenant_b)
        assert loaded_b.status == InterviewStatus.ACTIVE

    def test_expire_handles_paused_sessions(self, db):
        """Paused sessions inactive > 7 days are also marked ABANDONED."""
        tenant_id = uuid4()
        repo = InterviewSessionRepository(db)

        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        session.pause()
        repo.save(session)
        db.commit()

        model = db.get(InterviewSessionModel, session.id)
        model.updated_at = utc_now() - timedelta(days=8)
        db.commit()

        svc = _make_service(db)
        expired_count = svc.expire_stale_sessions(tenant_id=tenant_id)

        assert expired_count == 1

        loaded = repo.get_by_id(session.id, tenant_id)
        assert loaded.status == InterviewStatus.ABANDONED
