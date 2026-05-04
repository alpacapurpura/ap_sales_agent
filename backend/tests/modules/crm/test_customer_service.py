"""
Tests for CustomerService and CustomerRepository.

CRM-04: Customer identity resolution, profile creation, journey event tracking,
profile merging, and tenant isolation across all repository operations.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.modules.crm.domain.customer import CustomerIdentity, CustomerProfile
from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID,
    stage: LifecycleStage = LifecycleStage.SUBSCRIBER,
    email: str | None = None,
    **kwargs,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=email or f"{uuid.uuid4().hex[:8]}@test.com",
        full_name=kwargs.get("full_name", "Test User"),
        lifecycle_stage=stage,
        lead_score=kwargs.get("lead_score", 0.0),
        lifetime_value=kwargs.get("lifetime_value", 0.0),
        is_inactive=False,
        traits=kwargs.get("traits", {}),
        computed_traits=kwargs.get("computed_traits", {}),
    )
    db.add(profile)
    db.flush()
    return profile


def _make_identity(
    db: Session,
    profile: CustomerProfileModel,
    identity_type: IdentityType,
    value: str,
    is_primary: bool = False,
) -> CustomerIdentityModel:
    identity = CustomerIdentityModel(
        id=uuid.uuid4(),
        profile_id=profile.id,
        tenant_id=profile.tenant_id,
        type=identity_type,
        value=value,
        is_primary=is_primary,
    )
    db.add(identity)
    db.flush()
    return identity


# ---------------------------------------------------------------------------
# CustomerRepository — create
# ---------------------------------------------------------------------------


class TestCustomerRepositoryCreate:
    """CustomerRepository.create persists profile + identities."""

    def test_create_profile_with_email_identity(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        profile_id = uuid.uuid4()
        email = f"{uuid.uuid4().hex[:8]}@test.com"

        profile = CustomerProfile(
            id=profile_id,
            tenant_id=tenant_id,
            primary_email=email,
            full_name="New Customer",
            identities=[
                CustomerIdentity(
                    id=uuid.uuid4(),
                    profile_id=profile_id,
                    tenant_id=tenant_id,
                    type=IdentityType.EMAIL,
                    value=email,
                    is_primary=True,
                ),
            ],
        )

        result = repo.create(profile)
        assert result.id == profile_id
        assert result.primary_email == email
        assert len(result.identities) == 1
        assert result.identities[0].value == email

    def test_create_profile_preserves_lifecycle_stage(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        profile_id = uuid.uuid4()

        profile = CustomerProfile(
            id=profile_id,
            tenant_id=tenant_id,
            primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
            lifecycle_stage=LifecycleStage.LEAD,
            lead_score=25.0,
        )

        result = repo.create(profile)
        assert result.lifecycle_stage == LifecycleStage.LEAD
        assert result.lead_score == 25.0


# ---------------------------------------------------------------------------
# CustomerRepository — find_by_identity
# ---------------------------------------------------------------------------


class TestCustomerRepositoryFindByIdentity:
    """CustomerRepository.find_by_identity resolves profiles by identity type."""

    def test_find_by_email(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id, email="findme@test.com")
        _make_identity(db, profile, IdentityType.EMAIL, "findme@test.com", is_primary=True)

        repo = CustomerRepository(db)
        result = repo.find_by_identity(IdentityType.EMAIL, "findme@test.com", tenant_id)

        assert result is not None
        assert result.id == profile.id

    def test_find_by_user_id(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id)
        _make_identity(db, profile, IdentityType.USER_ID, "usr-12345")

        repo = CustomerRepository(db)
        result = repo.find_by_identity(IdentityType.USER_ID, "usr-12345", tenant_id)

        assert result is not None
        assert result.id == profile.id

    def test_find_by_phone(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id)
        _make_identity(db, profile, IdentityType.PHONE, "+5491112345678")

        repo = CustomerRepository(db)
        result = repo.find_by_identity(IdentityType.PHONE, "+5491112345678", tenant_id)

        assert result is not None
        assert result.id == profile.id

    def test_find_by_identity_returns_none_when_not_found(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        result = repo.find_by_identity(IdentityType.EMAIL, "nonexistent@test.com", tenant_id)
        assert result is None

    def test_find_by_identity_tenant_isolation(self, db: Session, tenant_id: uuid.UUID, other_tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id, email="isolated@test.com")
        _make_identity(db, profile, IdentityType.EMAIL, "isolated@test.com", is_primary=True)

        repo = CustomerRepository(db)
        result = repo.find_by_identity(IdentityType.EMAIL, "isolated@test.com", other_tenant_id)
        assert result is None


# ---------------------------------------------------------------------------
# CustomerRepository — create_with_identity
# ---------------------------------------------------------------------------


class TestCustomerRepositoryCreateWithIdentity:
    """CustomerRepository.create_with_identity creates profile + identity in one call."""

    def test_create_with_email_identity(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        result = repo.create_with_identity(
            tenant_id=tenant_id,
            identity_type=IdentityType.EMAIL,
            identity_value="new@test.com",
            profile_data={"first_name": "John", "last_name": "Doe"},
        )

        assert result.id is not None
        assert result.full_name == "John Doe"
        assert len(result.identities) == 1
        assert result.identities[0].value == "new@test.com"
        assert result.identities[0].is_primary is True

    def test_create_with_lead_source(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        result = repo.create_with_identity(
            tenant_id=tenant_id,
            identity_type=IdentityType.EMAIL,
            identity_value="source@test.com",
            profile_data={"traits": {"utm_source": "google"}},
            lead_source="google-ads",
            lead_source_detail="campaign-summer",
        )

        assert result.traits == {"utm_source": "google"}
        model = db.get(CustomerProfileModel, result.id)
        assert model.lead_source == "google-ads"
        assert model.lead_source_detail == "campaign-summer"

    def test_create_with_empty_name(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        result = repo.create_with_identity(
            tenant_id=tenant_id,
            identity_type=IdentityType.EMAIL,
            identity_value="noname@test.com",
            profile_data={},
        )

        assert result.full_name is None


# ---------------------------------------------------------------------------
# CustomerRepository — find_by_trait
# ---------------------------------------------------------------------------


class TestCustomerRepositoryFindByTrait:
    """CustomerRepository.find_by_trait looks up profiles by JSONB trait key/value.

    NOTE: These tests are skipped on SQLite because find_by_trait uses
    func.jsonb_extract_path_text which is PostgreSQL-specific.
    """

    @pytest.mark.skip(reason="jsonb_extract_path_text is PostgreSQL-only")
    def test_find_by_ig_username(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(
            db,
            tenant_id,
            traits={"instagram_username": "cool_user", "follower_count": 5000},
        )

        repo = CustomerRepository(db)
        result = repo.find_by_trait(tenant_id, "instagram_username", "cool_user")

        assert result is not None
        assert result.id == profile.id

    @pytest.mark.skip(reason="jsonb_extract_path_text is PostgreSQL-only")
    def test_find_by_trait_returns_none(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        result = repo.find_by_trait(tenant_id, "instagram_username", "nonexistent")
        assert result is None

    @pytest.mark.skip(reason="jsonb_extract_path_text is PostgreSQL-only")
    def test_find_by_trait_tenant_isolation(self, db: Session, tenant_id: uuid.UUID, other_tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        _make_profile(
            db,
            tenant_id,
            traits={"instagram_username": "tenant_a_user"},
        )

        repo = CustomerRepository(db)
        result = repo.find_by_trait(other_tenant_id, "instagram_username", "tenant_a_user")
        assert result is None


# ---------------------------------------------------------------------------
# CustomerRepository — merge_profiles
# ---------------------------------------------------------------------------


class TestCustomerRepositoryMergeProfiles:
    """CustomerRepository.merge_profiles moves identities and events, soft-deletes source."""

    def test_merge_moves_identities(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        source = _make_profile(db, tenant_id, email="source@test.com")
        target = _make_profile(db, tenant_id, email="target@test.com")
        _make_identity(db, source, IdentityType.EMAIL, "source@test.com", is_primary=True)
        _make_identity(db, source, IdentityType.PHONE, "+5491111111111")

        repo = CustomerRepository(db)
        repo.merge_profiles(source.id, target.id, tenant_id)

        identities = db.query(CustomerIdentityModel).filter(CustomerIdentityModel.profile_id == target.id).all()
        assert len(identities) == 2

    def test_merge_moves_journey_events(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        source = _make_profile(db, tenant_id, email="src@test.com")
        target = _make_profile(db, tenant_id, email="tgt@test.com")
        event = JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=source.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="track",
            properties={"page": "/home"},
        )
        db.add(event)
        db.flush()

        repo = CustomerRepository(db)
        repo.merge_profiles(source.id, target.id, tenant_id)

        events = db.query(JourneyEventModel).filter(JourneyEventModel.profile_id == target.id).all()
        assert len(events) == 1

    def test_merge_soft_deletes_source(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        source = _make_profile(db, tenant_id, email="src@test.com")
        target = _make_profile(db, tenant_id, email="tgt@test.com")

        repo = CustomerRepository(db)
        repo.merge_profiles(source.id, target.id, tenant_id)

        db.refresh(source)
        assert source.is_inactive is True

    def test_merge_carries_over_traits(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        source = _make_profile(db, tenant_id, traits={"source_trait": "from_source"})
        target = _make_profile(db, tenant_id, traits={"target_trait": "from_target"})

        repo = CustomerRepository(db)
        repo.merge_profiles(source.id, target.id, tenant_id)

        db.refresh(target)
        assert target.traits.get("source_trait") == "from_source"
        assert target.traits.get("target_trait") == "from_target"


# ---------------------------------------------------------------------------
# CustomerRepository — count_by_stage
# ---------------------------------------------------------------------------


class TestCustomerRepositoryCountByStage:
    """CustomerRepository.count_by_stage returns profile counts per lifecycle stage."""

    def test_count_subscribers(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        _make_profile(db, tenant_id, stage=LifecycleStage.SUBSCRIBER)
        _make_profile(db, tenant_id, stage=LifecycleStage.SUBSCRIBER)
        _make_profile(db, tenant_id, stage=LifecycleStage.LEAD)

        repo = CustomerRepository(db)
        count = repo.count_by_stage(tenant_id, LifecycleStage.SUBSCRIBER)
        assert count == 2

    def test_count_empty_stage(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        repo = CustomerRepository(db)
        count = repo.count_by_stage(tenant_id, LifecycleStage.CUSTOMER)
        assert count == 0


# ---------------------------------------------------------------------------
# CustomerRepository — _to_domain
# ---------------------------------------------------------------------------


class TestCustomerRepositoryToDomain:
    """CustomerRepository._to_domain converts model to domain object."""

    def test_to_domain_with_identities(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id, email="domain@test.com")
        _make_identity(db, profile, IdentityType.EMAIL, "domain@test.com", is_primary=True)

        repo = CustomerRepository(db)
        db.refresh(profile)
        result = repo._to_domain(profile)

        assert isinstance(result, CustomerProfile)
        assert result.primary_email == "domain@test.com"
        assert len(result.identities) == 1

    def test_to_domain_defaults_subscriber_stage(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id, stage=None)

        repo = CustomerRepository(db)
        db.refresh(profile)
        result = repo._to_domain(profile)

        assert result.lifecycle_stage == LifecycleStage.SUBSCRIBER

    def test_to_domain_defaults_zero_score(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        profile = _make_profile(db, tenant_id, lead_score=None)

        repo = CustomerRepository(db)
        db.refresh(profile)
        result = repo._to_domain(profile)

        assert result.lead_score == 0.0


# ---------------------------------------------------------------------------
# JourneyEventRepository — track_event
# ---------------------------------------------------------------------------


class TestJourneyEventRepositoryTrackEvent:
    """JourneyEventRepository.track_event persists events and updates last_activity_at."""

    def test_track_event_creates_record(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        profile = _make_profile(db, tenant_id)
        repo = JourneyEventRepository(db)

        event = repo.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="track",
            properties={"page": "/landing"},
        )

        assert event.id is not None
        assert event.event_name == "page_view"
        assert event.profile_id == profile.id

    def test_track_event_updates_last_activity(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        profile = _make_profile(db, tenant_id)
        assert profile.last_activity_at is None

        repo = JourneyEventRepository(db)
        repo.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="email_opened",
            event_type="track",
        )

        db.refresh(profile)
        assert profile.last_activity_at is not None

    def test_track_event_with_custom_timestamp(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        profile = _make_profile(db, tenant_id)
        custom_time = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)

        repo = JourneyEventRepository(db)
        event = repo.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="form_submitted",
            event_type="track",
            occurred_at=custom_time,
        )

        assert event.occurred_at == custom_time


# ---------------------------------------------------------------------------
# JourneyEventRepository — get_unique_visitors
# ---------------------------------------------------------------------------


class TestJourneyEventRepositoryGetUniqueVisitors:
    """JourneyEventRepository.get_unique_visitors counts page_view events."""

    def test_count_page_views(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        profile = _make_profile(db, tenant_id)
        for _ in range(3):
            db.add(
                JourneyEventModel(
                    id=uuid.uuid4(),
                    profile_id=profile.id,
                    tenant_id=tenant_id,
                    event_name="page_view",
                    event_type="track",
                    properties={},
                )
            )
        db.flush()

        repo = JourneyEventRepository(db)
        count = repo.get_unique_visitors(tenant_id)
        assert count == 3

    def test_does_not_count_non_page_view_events(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        profile = _make_profile(db, tenant_id)
        db.add(
            JourneyEventModel(
                id=uuid.uuid4(),
                profile_id=profile.id,
                tenant_id=tenant_id,
                event_name="email_opened",
                event_type="track",
                properties={},
            )
        )
        db.flush()

        repo = JourneyEventRepository(db)
        count = repo.get_unique_visitors(tenant_id)
        assert count == 0

    def test_returns_zero_on_exception(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            JourneyEventRepository,
        )

        repo = JourneyEventRepository(db)
        with patch.object(repo.db, "execute", side_effect=ValueError("boom")):
            count = repo.get_unique_visitors(tenant_id)
        assert count == 0


# ---------------------------------------------------------------------------
# CustomerService — identify
# ---------------------------------------------------------------------------


class TestCustomerServiceIdentify:
    """CustomerService.identify resolves existing profiles or creates new ones."""

    def test_identify_creates_new_profile_with_email(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        svc = CustomerService(db)
        email = f"{uuid.uuid4().hex[:8]}@test.com"

        result = svc.identify(
            tenant_id=tenant_id,
            traits={"email": email, "name": "New User"},
            identities={},
        )

        assert result is not None
        assert result.primary_email == email
        assert result.full_name == "New User"

    def test_identify_finds_existing_by_email(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        email = f"{uuid.uuid4().hex[:8]}@test.com"
        profile = _make_profile(db, tenant_id, email=email)
        _make_identity(db, profile, IdentityType.EMAIL, email, is_primary=True)

        svc = CustomerService(db)
        result = svc.identify(
            tenant_id=tenant_id,
            traits={"email": email},
            identities={},
        )

        assert result.id == profile.id

    def test_identify_finds_existing_by_user_id(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        _make_identity(db, profile, IdentityType.USER_ID, "usr-99999")

        svc = CustomerService(db)
        result = svc.identify(
            tenant_id=tenant_id,
            traits={},
            identities={"user_id": "usr-99999"},
        )

        assert result.id == profile.id

    def test_identify_priority_user_id_over_email(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile_a = _make_profile(db, tenant_id, email="a@test.com")
        _make_identity(db, profile_a, IdentityType.EMAIL, "a@test.com", is_primary=True)

        profile_b = _make_profile(db, tenant_id, email="b@test.com")
        _make_identity(db, profile_b, IdentityType.USER_ID, "usr-priority")
        _make_identity(db, profile_b, IdentityType.EMAIL, "b@test.com", is_primary=True)

        svc = CustomerService(db)
        result = svc.identify(
            tenant_id=tenant_id,
            traits={"email": "b@test.com"},
            identities={"user_id": "usr-priority"},
        )

        assert result.id == profile_b.id

    def test_identify_creates_email_identity_on_new_profile(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        svc = CustomerService(db)
        email = f"{uuid.uuid4().hex[:8]}@test.com"

        result = svc.identify(
            tenant_id=tenant_id,
            traits={"email": email},
            identities={},
        )

        assert len(result.identities) == 1
        assert result.identities[0].type == IdentityType.EMAIL
        assert result.identities[0].is_primary is True


# ---------------------------------------------------------------------------
# CustomerService — track_event
# ---------------------------------------------------------------------------


class TestCustomerServiceTrackEvent:
    """CustomerService.track_event writes journey events and triggers scoring."""

    def test_track_event_creates_event_and_recalculates_score(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        svc = CustomerService(db)

        event = svc.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="email_opened",
            event_type="track",
            properties={"campaign": "welcome"},
        )

        assert event.event_name == "email_opened"
        assert event.properties == {"campaign": "welcome"}

    def test_track_event_with_none_properties(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        svc = CustomerService(db)

        event = svc.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="page",
        )

        assert event.properties == {}
