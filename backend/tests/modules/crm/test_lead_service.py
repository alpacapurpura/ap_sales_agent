"""
Tests for LeadService and PipelineService: CRUD, channel lookup, stage transitions.

CRM-08: Lead retrieval, channel-based lookup, creation, update, pipeline stage movement.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from luana_core_crm.domain.enums import LifecycleStage
from luana_core_crm.domain.lead import Lead, UserProfile
from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
from luana_core_crm.infrastructure.models.lead_model import LeadModel
from luana_core_crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_lead_model(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    telegram_id: str | None = None,
    whatsapp_id: str | None = None,
    api_id: str | None = None,
    profile_data: dict | None = None,
) -> LeadModel:
    lead = LeadModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        telegram_id=telegram_id,
        whatsapp_id=whatsapp_id,
        api_id=api_id,
        profile_data=profile_data or {},
        key_objections_history=[],
    )
    db.add(lead)
    db.flush()
    return lead


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    stage: LifecycleStage = LifecycleStage.SUBSCRIBER,
    full_name: str = "Test User",
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name=full_name,
        lifecycle_stage=stage,
        lead_score=0.0,
        lifetime_value=0.0,
        is_inactive=False,
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Tests: Get Lead
# ---------------------------------------------------------------------------


class TestGetLead:
    """get_lead retrieves a lead by ID or returns None."""

    def test_get_existing_lead(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        model = _make_lead_model(db, tenant_id=tenant_id, telegram_id="tg-123")

        svc = LeadService(db)
        result = svc.get_lead(model.id)

        assert result is not None
        assert result.id == model.id
        assert result.telegram_id == "tg-123"
        assert result.tenant_id == tenant_id

    def test_get_nonexistent_lead(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        svc = LeadService(db)
        result = svc.get_lead(uuid.uuid4())

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Find Lead By Channel
# ---------------------------------------------------------------------------


class TestFindLeadByChannel:
    """find_lead_by_channel looks up leads by channel-specific ID."""

    def test_find_by_telegram_id(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        _make_lead_model(db, tenant_id=tenant_id, telegram_id="tg-unique-456")

        svc = LeadService(db)
        result = svc.find_lead_by_channel("telegram", "tg-unique-456", tenant_id)

        assert result is not None
        assert result.telegram_id == "tg-unique-456"

    def test_find_by_whatsapp_id(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        _make_lead_model(db, tenant_id=tenant_id, whatsapp_id="wa-unique-789")

        svc = LeadService(db)
        result = svc.find_lead_by_channel("whatsapp", "wa-unique-789", tenant_id)

        assert result is not None
        assert result.whatsapp_id == "wa-unique-789"

    def test_find_by_api_id(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        _make_lead_model(db, tenant_id=tenant_id, api_id="api-ext-001")

        svc = LeadService(db)
        result = svc.find_lead_by_channel("api", "api-ext-001", tenant_id)

        assert result is not None
        assert result.api_id == "api-ext-001"

    def test_unknown_channel_returns_none(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        _make_lead_model(db, tenant_id=tenant_id, telegram_id="tg-xyz")

        svc = LeadService(db)
        result = svc.find_lead_by_channel("tiktok", "tg-xyz", tenant_id)

        assert result is None

    def test_tenant_isolation_lead_not_found(self, db: Session, tenant_id, other_tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        _make_lead_model(db, tenant_id=tenant_id, telegram_id="tg-isolated")

        svc = LeadService(db)
        result = svc.find_lead_by_channel("telegram", "tg-isolated", other_tenant_id)

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Create Lead
# ---------------------------------------------------------------------------


class TestCreateLead:
    """create_lead persists a new lead with or without profile data."""

    def test_create_lead_with_profile(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        profile = UserProfile(name="Juan", email="juan@test.com", location="Lima")

        svc = LeadService(db)
        result = svc.create_lead(tenant_id=tenant_id, profile=profile, telegram_id="tg-new-001")

        assert result is not None
        assert result.telegram_id == "tg-new-001"
        assert result.profile_data.name == "Juan"
        assert result.profile_data.email == "juan@test.com"
        assert result.profile_data.location == "Lima"

        persisted = db.execute(select(LeadModel).where(LeadModel.id == result.id)).scalars().first()
        assert persisted is not None
        assert persisted.telegram_id == "tg-new-001"

    def test_create_lead_without_profile(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        svc = LeadService(db)
        result = svc.create_lead(tenant_id=tenant_id, whatsapp_id="wa-new-002")

        assert result is not None
        assert result.whatsapp_id == "wa-new-002"
        assert isinstance(result.profile_data, UserProfile)

        persisted = db.execute(select(LeadModel).where(LeadModel.id == result.id)).scalars().first()
        assert persisted is not None


# ---------------------------------------------------------------------------
# Tests: Update Lead
# ---------------------------------------------------------------------------


class TestUpdateLead:
    """update_lead persists changes to an existing lead."""

    def test_update_lead_persists_changes(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        model = _make_lead_model(db, tenant_id=tenant_id, telegram_id="tg-update-001")

        svc = LeadService(db)
        lead = svc.get_lead(model.id)
        lead.profile_data = UserProfile(name="Updated", email="updated@test.com")
        lead.temperature = "HOT"

        result = svc.update_lead(lead)

        assert result.profile_data.name == "Updated"
        assert result.temperature == "HOT"

        persisted = db.execute(select(LeadModel).where(LeadModel.id == lead.id)).scalars().first()
        assert persisted.temperature == "HOT"

    def test_update_nonexistent_lead_raises(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import LeadService

        svc = LeadService(db)
        fake_lead = Lead(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            profile_data=UserProfile(),
        )

        with pytest.raises(ValueError, match="Lead not found"):
            svc.update_lead(fake_lead)


# ---------------------------------------------------------------------------
# Tests: PipelineService Move Stage
# ---------------------------------------------------------------------------


class TestPipelineServiceMoveStage:
    """PipelineService.move_stage delegates to LifecycleService.force_stage."""

    def test_move_stage_delegates_to_lifecycle_service(self, db: Session, tenant_id):
        from luana_core_crm.application.services.lead_service import PipelineService

        profile = _make_profile(db, tenant_id=tenant_id, stage=LifecycleStage.LEAD)

        svc = PipelineService(db)

        with patch(
            "luana_core_crm.application.services.lifecycle_service.LifecycleService.force_stage",
        ) as mock_force:
            svc.move_stage(
                profile_id=profile.id,
                new_stage="mql",
                admin_user_id="admin-001",
                note="Test promotion",
            )

            mock_force.assert_called_once()
            call_kwargs = mock_force.call_args[1]
            assert call_kwargs["profile_id"] == profile.id
            assert call_kwargs["new_stage"] == LifecycleStage.MQL
            assert call_kwargs["admin_user_id"] == "admin-001"
            assert call_kwargs["note"] == "Test promotion"
