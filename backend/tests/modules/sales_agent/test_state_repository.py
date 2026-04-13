"""
Unit tests for StateRepository (agent state checkpoint persistence).

Covers: create, load, update, deactivate, tenant isolation, and
session-timeout deactivation.
"""

import uuid

from sqlalchemy.orm import Session

from src.modules.sales_agent.infrastructure.repositories.state_repository import (
    StateRepository,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo(db: Session) -> StateRepository:
    return StateRepository(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateNewCheckpoint:
    def test_create_new_checkpoint(
        self,
        db: Session,
        tenant_id,
        lead_id,
        customer_profile_id,
    ):
        repo = _make_repo(db)

        cp = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-001",
            customer_profile_id=customer_profile_id,
            channel_type="instagram",
            current_stage="discovery",
            lead_score=25,
            lead_data={"name": "Maria"},
            buying_signals=[{"signal": "asked_price", "turn": 3}],
            objection_history=[],
            qualification_answers={"budget": "5k"},
            turn_count=3,
        )

        assert cp.id is not None
        assert cp.tenant_id == tenant_id
        assert cp.lead_id == lead_id
        assert cp.session_id == "sess-001"
        assert cp.current_stage == "discovery"
        assert cp.lead_score == 25
        assert cp.lead_data == {"name": "Maria"}
        assert cp.buying_signals == [{"signal": "asked_price", "turn": 3}]
        assert cp.qualification_answers == {"budget": "5k"}
        assert cp.turn_count == 3
        assert cp.channel_type == "instagram"
        assert cp.is_active is True
        assert cp.deleted_at is None


class TestLoadExistingCheckpoint:
    def test_load_existing_checkpoint(self, db: Session, tenant_id, lead_id):
        repo = _make_repo(db)

        repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-002",
            current_stage="rapport",
            lead_score=10,
            lead_data={"email": "test@example.com"},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=1,
        )

        loaded = repo.get_active_checkpoint(tenant_id, lead_id)

        assert loaded is not None
        assert loaded.session_id == "sess-002"
        assert loaded.current_stage == "rapport"
        assert loaded.lead_score == 10
        assert loaded.lead_data == {"email": "test@example.com"}
        assert loaded.turn_count == 1


class TestUpdateExistingCheckpoint:
    def test_update_existing_checkpoint(self, db: Session, tenant_id, lead_id):
        repo = _make_repo(db)

        cp1 = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-003",
            current_stage="rapport",
            lead_score=5,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=1,
        )
        original_id = cp1.id

        cp2 = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            current_stage="discovery",
            lead_score=30,
            lead_data={"name": "Carlos"},
            buying_signals=[{"signal": "mentioned_deadline"}],
            turn_count=4,
        )

        # Same row was updated (upsert behaviour)
        assert cp2.id == original_id
        assert cp2.current_stage == "discovery"
        assert cp2.lead_score == 30
        assert cp2.lead_data == {"name": "Carlos"}
        assert cp2.buying_signals == [{"signal": "mentioned_deadline"}]
        assert cp2.turn_count == 4


class TestDeactivateCheckpoint:
    def test_deactivate_checkpoint(self, db: Session, tenant_id, lead_id):
        repo = _make_repo(db)

        repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-004",
            current_stage="closing",
            lead_score=80,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=10,
        )

        repo.deactivate(tenant_id, lead_id)

        loaded = repo.get_active_checkpoint(tenant_id, lead_id)
        assert loaded is None


class TestTenantIsolation:
    def test_tenant_isolation(self, db: Session, tenant_id, tenant_id_b):
        """Two tenants with the same lead_id must NOT see each other's data."""
        repo = _make_repo(db)
        shared_lead_id = uuid.uuid4()

        repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=shared_lead_id,
            session_id="sess-A",
            current_stage="rapport",
            lead_score=10,
            lead_data={"tenant": "A"},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=1,
        )

        repo.save_checkpoint(
            tenant_id=tenant_id_b,
            lead_id=shared_lead_id,
            session_id="sess-B",
            current_stage="closing",
            lead_score=90,
            lead_data={"tenant": "B"},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=15,
        )

        cp_a = repo.get_active_checkpoint(tenant_id, shared_lead_id)
        cp_b = repo.get_active_checkpoint(tenant_id_b, shared_lead_id)

        assert cp_a is not None
        assert cp_b is not None
        assert cp_a.lead_data == {"tenant": "A"}
        assert cp_b.lead_data == {"tenant": "B"}
        assert cp_a.lead_score == 10
        assert cp_b.lead_score == 90
        assert cp_a.id != cp_b.id


class TestSessionTimeoutDeactivation:
    def test_session_timeout_deactivation(self, db: Session, tenant_id, lead_id):
        """
        Simulates the session-timeout path: when session_active is False,
        the old checkpoint should be deactivated.  A subsequent save must
        create a new row, not update the deactivated one.
        """
        repo = _make_repo(db)

        # First session: checkpoint is created
        repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-old",
            current_stage="discovery",
            lead_score=40,
            lead_data={"name": "Ana"},
            buying_signals=[{"signal": "price_inquiry"}],
            objection_history=[{"objection": "too_expensive"}],
            qualification_answers={"budget": "3k"},
            turn_count=7,
        )

        # Session timeout detected -> deactivate
        repo.deactivate(tenant_id, lead_id)
        assert repo.get_active_checkpoint(tenant_id, lead_id) is None

        # New session starts -> brand new checkpoint
        new_cp = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-new",
            current_stage="rapport",
            lead_score=0,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=0,
        )

        assert new_cp.session_id == "sess-new"
        assert new_cp.current_stage == "rapport"
        assert new_cp.lead_score == 0
        assert new_cp.is_active is True
