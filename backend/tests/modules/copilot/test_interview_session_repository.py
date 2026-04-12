"""Tests for InterviewSessionRepository."""

from uuid import uuid4

import pytest

from src.modules.copilot.domain.interview_configs.brand_config import (
    BRAND_INTERVIEW_CONFIG,
)
from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)


@pytest.fixture
def repo(db):
    return InterviewSessionRepository(db)


@pytest.fixture
def sample_session():
    return InterviewSession.create(
        tenant_id=uuid4(),
        domain="brand",
        config=BRAND_INTERVIEW_CONFIG,
        conversation_id=uuid4(),
    )


class TestInterviewSessionRepository:
    def test_save_and_get(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded is not None
        assert loaded.id == sample_session.id
        assert loaded.domain == "brand"
        assert loaded.status == InterviewStatus.ACTIVE

    def test_get_by_id_wrong_tenant_returns_none(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, uuid4())
        assert loaded is None

    def test_get_active_by_domain(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        active = repo.get_active_by_domain(sample_session.tenant_id, "brand")
        assert active is not None
        assert active.id == sample_session.id

    def test_get_active_returns_none_when_paused(self, repo, sample_session, db):
        sample_session.pause()
        repo.save(sample_session)
        db.commit()
        active = repo.get_active_by_domain(sample_session.tenant_id, "brand")
        assert active is None

    def test_update_mapa_global(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        sample_session.update_mapa_global({"story.origin_story": "Test"})
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded.mapa_global["story.origin_story"] == "Test"

    def test_soft_delete(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        repo.soft_delete(sample_session.id, sample_session.tenant_id)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded is None

    def test_get_active_by_domain_wrong_tenant_returns_none(
        self, repo, sample_session, db
    ):
        repo.save(sample_session)
        db.commit()
        other_tenant = uuid4()
        active = repo.get_active_by_domain(other_tenant, "brand")
        assert active is None

    def test_config_snapshot_persisted(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded.config_snapshot is not None
        assert loaded.config_snapshot.get("domain") == "brand"

    def test_bloques_completados_persisted(self, repo, sample_session, db):
        sample_session.advance_block("identidad")
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert "identidad" in loaded.bloques_completados

    def test_messages_count_persisted(self, repo, sample_session, db):
        sample_session.increment_messages()
        sample_session.increment_messages()
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded.messages_count == 2
