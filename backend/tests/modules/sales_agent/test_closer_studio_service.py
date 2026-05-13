"""Tests for CloserStudioService — Closer Studio business logic."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
from luana_core_crm.infrastructure.models.lead_model import LeadModel
from luana_core_sales_agent.application.services.closer_studio_service import (
    CloserStudioService,
)
from luana_core_sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from luana_core_sales_agent.infrastructure.models.message_model import MessageModel

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_customer(
    db: Session,
    tenant_id: uuid.UUID,
    **overrides,
) -> CustomerProfileModel:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "full_name": "Test Customer",
    }
    defaults.update(overrides)
    customer = CustomerProfileModel(**defaults)
    db.add(customer)
    db.flush()
    return customer


def _create_lead(db: Session, tenant_id: uuid.UUID, **overrides) -> LeadModel:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "temperature": "warm",
        "is_blacklisted": False,
        "telegram_id": None,
        "whatsapp_id": None,
        "instagram_id": f"ig_{uuid.uuid4().hex[:8]}",
    }
    defaults.update(overrides)
    lead = LeadModel(**defaults)
    db.add(lead)
    db.flush()
    return lead


def _create_checkpoint(
    db: Session,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    **overrides,
) -> AgentStateCheckpointModel:
    defaults = {
        "id": uuid.uuid4(),
        "session_id": f"sess_{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "channel_type": "instagram",
        "current_stage": "rapport",
        "lead_score": 30,
        "lead_data": {},
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "turn_count": 5,
        "handler_mode": "ai",
        "is_active": True,
        "deleted_at": None,
        "unread_count": 0,
        "consecutive_questions": 0,
    }
    defaults.update(overrides)
    cp = AgentStateCheckpointModel(**defaults)
    db.add(cp)
    db.flush()
    return cp


def _create_message(
    db: Session,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    **overrides,
) -> MessageModel:
    defaults = {
        "id": uuid.uuid4(),
        "user_id": lead_id,
        "tenant_id": tenant_id,
        "role": "user",
        "content": "Hello, I'm interested",
        "channel": "instagram",
        "sender_source": "auto",
    }
    defaults.update(overrides)
    msg = MessageModel(**defaults)
    db.add(msg)
    db.flush()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# STOP AI
# ══════════════════════════════════════════════════════════════════════════════


class TestStopAI:
    """Tests for stop_ai method."""

    def test_stop_ai_with_checkpoint_sets_human_mode(self, db: Session):
        """Stop AI should set handler_mode='human' and record paused_at/paused_by."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(db, TENANT_A, lead.id, handler_mode="ai")
        user_id = uuid.uuid4()

        svc = CloserStudioService(db)
        result = svc.stop_ai(TENANT_A, lead.id, user_id)

        assert result is not None
        assert result["handler_mode"] == "human"
        assert result["lead_id"] == lead.id
        assert result["paused_at"] is not None

    def test_stop_ai_creates_system_event(self, db: Session):
        """Stop AI should log a system event message."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(db, TENANT_A, lead.id)
        user_id = uuid.uuid4()

        svc = CloserStudioService(db)
        svc.stop_ai(TENANT_A, lead.id, user_id)

        system_msgs = (
            db.query(MessageModel)
            .filter(
                MessageModel.user_id == lead.id,
                MessageModel.role == "system",
                MessageModel.content.contains("[SYSTEM]"),
            )
            .all()
        )
        assert len(system_msgs) == 1
        assert "took control" in system_msgs[0].content

    def test_stop_ai_updates_checkpoint_in_db(self, db: Session):
        """After stop, the checkpoint in DB should reflect handler_mode='human'."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(db, TENANT_A, lead.id, handler_mode="ai")
        user_id = uuid.uuid4()

        svc = CloserStudioService(db)
        svc.stop_ai(TENANT_A, lead.id, user_id)

        db.refresh(cp)
        assert cp.handler_mode == "human"
        assert cp.paused_by == user_id
        assert cp.paused_at is not None

    def test_stop_ai_without_checkpoint_returns_none(self, db: Session):
        """Stop AI should return None when no checkpoint exists (no crash)."""
        lead = _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        result = svc.stop_ai(TENANT_A, lead.id, uuid.uuid4())

        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# RESUME AI
# ══════════════════════════════════════════════════════════════════════════════


class TestResumeAI:
    """Tests for resume_ai method."""

    def test_resume_ai_with_checkpoint_sets_ai_mode(self, db: Session):
        """Resume AI should set handler_mode='ai' and clear paused fields."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(
            db,
            TENANT_A,
            lead.id,
            handler_mode="human",
            paused_at=datetime.now(timezone.utc),
            paused_by=uuid.uuid4(),
        )

        svc = CloserStudioService(db)
        result = svc.resume_ai(TENANT_A, lead.id)

        assert result is not None
        assert result["handler_mode"] == "ai"
        assert result["lead_id"] == lead.id

    def test_resume_ai_with_objective(self, db: Session):
        """Resume AI should store the resume objective."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(db, TENANT_A, lead.id, handler_mode="human")

        svc = CloserStudioService(db)
        result = svc.resume_ai(TENANT_A, lead.id, objective="Close the sale")

        assert result["resume_objective"] == "Close the sale"
        db.refresh(cp)
        assert cp.resume_objective == "Close the sale"

    def test_resume_ai_clears_paused_fields(self, db: Session):
        """Resume should clear paused_at and paused_by on checkpoint."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(
            db,
            TENANT_A,
            lead.id,
            handler_mode="human",
            paused_at=datetime.now(timezone.utc),
            paused_by=uuid.uuid4(),
        )

        svc = CloserStudioService(db)
        svc.resume_ai(TENANT_A, lead.id)

        db.refresh(cp)
        assert cp.paused_at is None
        assert cp.paused_by is None

    def test_resume_ai_without_checkpoint_returns_none(self, db: Session):
        """Resume AI should return None when no checkpoint exists."""
        lead = _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        result = svc.resume_ai(TENANT_A, lead.id)

        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# GET CONVERSATION DETAIL
# ══════════════════════════════════════════════════════════════════════════════


class TestGetConversationDetail:
    """Tests for get_conversation_detail method."""

    def test_detail_with_checkpoint_returns_checkpoint_handler_mode(self, db: Session):
        """When a checkpoint exists, handler_mode should come from it."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(db, TENANT_A, lead.id, handler_mode="ai")

        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        assert result is not None
        assert result["handler_mode"] == "ai"

    def test_detail_without_checkpoint_defaults_handler_mode_to_human(
        self,
        db: Session,
    ):
        """BUG FIX: When no checkpoint exists, handler_mode should be 'human', not 'ai'.

        If there's no AI state tracking the conversation, the AI isn't active.
        Defaulting to 'ai' causes the UI to show a 'STOP AI' button that fails with 404.
        """
        lead = _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        assert result is not None
        assert result["handler_mode"] == "human"

    def test_detail_returns_messages_in_chronological_order(self, db: Session):
        """Messages should be returned oldest-first."""
        lead = _create_lead(db, TENANT_A)
        _create_message(
            db,
            TENANT_A,
            lead.id,
            content="First",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        _create_message(
            db,
            TENANT_A,
            lead.id,
            content="Second",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )

        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        assert result["messages"][0]["content"] == "First"
        assert result["messages"][1]["content"] == "Second"
        assert result["total_messages"] == 2

    def test_detail_resets_unread_count(self, db: Session):
        """Viewing conversation detail should reset unread_count to 0."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(db, TENANT_A, lead.id, unread_count=5)

        svc = CloserStudioService(db)
        svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        db.refresh(cp)
        assert cp.unread_count == 0

    def test_detail_nonexistent_lead_returns_none(self, db: Session):
        """Should return None for a lead that doesn't exist."""
        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=uuid.uuid4())

        assert result is None

    def test_detail_includes_customer_display_name(self, db: Session):
        """Display name should come from customer profile when available."""
        customer = _create_customer(db, TENANT_A, full_name="María García")
        lead = _create_lead(db, TENANT_A, customer_id=customer.id)

        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        assert result["display_name"] == "María García"


# ══════════════════════════════════════════════════════════════════════════════
# LIST CONVERSATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestListConversations:
    """Tests for list_conversations method."""

    def test_list_no_checkpoint_defaults_handler_mode_to_human(self, db: Session):
        """BUG FIX: Leads without checkpoint should show handler_mode='human'."""
        _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        conversations, total = svc.list_conversations(tenant_id=TENANT_A)

        assert total == 1
        assert conversations[0]["handler_mode"] == "human"

    def test_list_with_checkpoint_uses_checkpoint_handler_mode(self, db: Session):
        """Leads with checkpoint should show the checkpoint's handler_mode."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(db, TENANT_A, lead.id, handler_mode="ai")

        svc = CloserStudioService(db)
        conversations, _ = svc.list_conversations(tenant_id=TENANT_A)

        assert conversations[0]["handler_mode"] == "ai"

    def test_list_excludes_blacklisted_leads(self, db: Session):
        """Blacklisted leads should not appear in the list."""
        _create_lead(db, TENANT_A, is_blacklisted=True)
        _create_lead(db, TENANT_A, is_blacklisted=False)

        svc = CloserStudioService(db)
        _, total = svc.list_conversations(tenant_id=TENANT_A)

        assert total == 1

    def test_list_pagination(self, db: Session):
        """Pagination should work correctly with limit and offset."""
        for _ in range(5):
            _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        conversations, total = svc.list_conversations(
            tenant_id=TENANT_A,
            limit=2,
            offset=0,
        )

        assert total == 5
        assert len(conversations) == 2

    def test_list_filter_by_temperature(self, db: Session):
        """Should filter by lead temperature."""
        _create_lead(db, TENANT_A, temperature="hot")
        _create_lead(db, TENANT_A, temperature="cold")

        svc = CloserStudioService(db)
        conversations, total = svc.list_conversations(
            tenant_id=TENANT_A,
            temperature="hot",
        )

        assert total == 1
        assert conversations[0]["temperature"] == "hot"


# ══════════════════════════════════════════════════════════════════════════════
# SEND MESSAGE
# ══════════════════════════════════════════════════════════════════════════════


class TestSendMessage:
    """Tests for send_message method."""

    def test_send_direct_message(self, db: Session):
        """Direct message should be stored with role='assistant' and sender_source='human_direct'."""
        lead = _create_lead(db, TENANT_A)
        _create_checkpoint(db, TENANT_A, lead.id)

        svc = CloserStudioService(db)
        result = svc.send_message(TENANT_A, lead.id, "Hello from owner", mode="direct")

        assert result is not None
        assert result["mode"] == "direct"
        assert result["content"] == "Hello from owner"

        msg = db.query(MessageModel).filter(MessageModel.id == result["message_id"]).one()
        assert msg.role == "assistant"
        assert msg.sender_source == "human_direct"

    def test_send_instruction_message(self, db: Session):
        """Instruction message should be stored as system message and set resume_objective."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(db, TENANT_A, lead.id)

        svc = CloserStudioService(db)
        result = svc.send_message(
            TENANT_A,
            lead.id,
            "Push for the close",
            mode="instruction",
        )

        assert result is not None
        assert result["mode"] == "instruction"

        msg = db.query(MessageModel).filter(MessageModel.id == result["message_id"]).one()
        assert msg.role == "system"
        assert msg.sender_source == "human_instruction"
        assert "INSTRUCCION DEL OPERADOR" in msg.content

        db.refresh(cp)
        assert cp.resume_objective == "Push for the close"

    def test_send_message_without_checkpoint(self, db: Session):
        """Should still work even without a checkpoint (channel will be None)."""
        lead = _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        result = svc.send_message(TENANT_A, lead.id, "Hi there", mode="direct")

        assert result is not None
        msg = db.query(MessageModel).filter(MessageModel.id == result["message_id"]).one()
        assert msg.channel is None


# ══════════════════════════════════════════════════════════════════════════════
# REACTIVATE FROZEN
# ══════════════════════════════════════════════════════════════════════════════


class TestReactivate:
    """Tests for reactivate method."""

    def test_reactivate_frozen_conversation(self, db: Session):
        """Reactivating should clear frozen fields and set handler_mode='ai'."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(
            db,
            TENANT_A,
            lead.id,
            frozen_at=datetime.now(timezone.utc),
            frozen_reason="No response in 48h",
            frozen_diagnosis={"summary": "Dead lead"},
            handler_mode="ai",
        )

        svc = CloserStudioService(db)
        result = svc.reactivate(TENANT_A, lead.id)

        assert result is not None
        assert result["handler_mode"] == "ai"

        db.refresh(cp)
        assert cp.frozen_at is None
        assert cp.frozen_reason is None
        assert cp.frozen_diagnosis is None

    def test_reactivate_with_objective(self, db: Session):
        """Reactivation can include a resume objective."""
        lead = _create_lead(db, TENANT_A)
        cp = _create_checkpoint(
            db,
            TENANT_A,
            lead.id,
            frozen_at=datetime.now(timezone.utc),
        )

        svc = CloserStudioService(db)
        svc.reactivate(TENANT_A, lead.id, objective="Re-engage with discount")

        db.refresh(cp)
        assert cp.resume_objective == "Re-engage with discount"

    def test_reactivate_without_checkpoint_returns_none(self, db: Session):
        """Should return None when no checkpoint exists."""
        lead = _create_lead(db, TENANT_A)

        svc = CloserStudioService(db)
        result = svc.reactivate(TENANT_A, lead.id)

        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════════════


class TestGetKPIs:
    """Tests for get_kpis method."""

    def test_kpis_counts(self, db: Session):
        """KPIs should correctly count AI/human/frozen conversations."""
        lead1 = _create_lead(db, TENANT_A, temperature="hot")
        lead2 = _create_lead(db, TENANT_A, temperature="warm")
        lead3 = _create_lead(db, TENANT_A, temperature="cold")

        _create_checkpoint(db, TENANT_A, lead1.id, handler_mode="ai")
        _create_checkpoint(db, TENANT_A, lead2.id, handler_mode="human")
        _create_checkpoint(
            db,
            TENANT_A,
            lead3.id,
            handler_mode="ai",
            frozen_at=datetime.now(timezone.utc),
        )

        svc = CloserStudioService(db)
        kpis = svc.get_kpis(TENANT_A)

        assert kpis["total_active"] == 3
        assert kpis["handled_by_ai"] == 2
        assert kpis["handled_by_human"] == 1
        assert kpis["frozen_count"] == 1
        assert kpis["hot_count"] == 1
        assert kpis["warm_count"] == 1
        assert kpis["cold_count"] == 1

    def test_kpis_empty_tenant(self, db: Session):
        """KPIs for a tenant with no data should return zeros."""
        svc = CloserStudioService(db)
        kpis = svc.get_kpis(TENANT_A)

        assert kpis["total_active"] == 0
        assert kpis["handled_by_ai"] == 0
        assert kpis["avg_lead_score"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# LIST FROZEN
# ══════════════════════════════════════════════════════════════════════════════


class TestListFrozen:
    """Tests for list_frozen method."""

    def test_list_frozen_only_returns_frozen(self, db: Session):
        """Should only return conversations with frozen_at set."""
        lead1 = _create_lead(db, TENANT_A)
        lead2 = _create_lead(db, TENANT_A)

        _create_checkpoint(db, TENANT_A, lead1.id)  # not frozen
        _create_checkpoint(
            db,
            TENANT_A,
            lead2.id,
            frozen_at=datetime.now(timezone.utc),
            frozen_reason="No response",
        )

        svc = CloserStudioService(db)
        frozen = svc.list_frozen(TENANT_A)

        assert len(frozen) == 1
        assert frozen[0]["lead_id"] == lead2.id
        assert frozen[0]["frozen_reason"] == "No response"


# ══════════════════════════════════════════════════════════════════════════════
# TENANT ISOLATION
# ══════════════════════════════════════════════════════════════════════════════


class TestTenantIsolation:
    """Tests verifying tenant isolation across all operations."""

    def test_stop_ai_cannot_stop_other_tenant(self, db: Session):
        """Tenant A cannot stop AI on Tenant B's conversation."""
        lead = _create_lead(db, TENANT_B)
        _create_checkpoint(db, TENANT_B, lead.id, handler_mode="ai")

        svc = CloserStudioService(db)
        result = svc.stop_ai(TENANT_A, lead.id, uuid.uuid4())

        assert result is None  # checkpoint not found for TENANT_A

    def test_detail_cannot_see_other_tenant(self, db: Session):
        """Tenant A cannot view Tenant B's conversation detail."""
        lead = _create_lead(db, TENANT_B)

        svc = CloserStudioService(db)
        result = svc.get_conversation_detail(tenant_id=TENANT_A, lead_id=lead.id)

        assert result is None

    def test_list_conversations_only_own_tenant(self, db: Session):
        """list_conversations should only return own tenant's leads."""
        _create_lead(db, TENANT_A)
        _create_lead(db, TENANT_B)

        svc = CloserStudioService(db)
        _conversations, total = svc.list_conversations(tenant_id=TENANT_A)

        assert total == 1

    def test_kpis_isolated_by_tenant(self, db: Session):
        """KPIs should only count own tenant's checkpoints."""
        lead_a = _create_lead(db, TENANT_A)
        lead_b = _create_lead(db, TENANT_B)
        _create_checkpoint(db, TENANT_A, lead_a.id)
        _create_checkpoint(db, TENANT_B, lead_b.id)

        svc = CloserStudioService(db)
        kpis = svc.get_kpis(TENANT_A)

        assert kpis["total_active"] == 1

    def test_resume_ai_cannot_resume_other_tenant(self, db: Session):
        """Tenant A cannot resume AI on Tenant B's conversation."""
        lead = _create_lead(db, TENANT_B)
        _create_checkpoint(db, TENANT_B, lead.id, handler_mode="human")

        svc = CloserStudioService(db)
        result = svc.resume_ai(TENANT_A, lead.id)

        assert result is None
