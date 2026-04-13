"""CRM customer repository."""

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import String, cast, func, select
from sqlalchemy.orm import Session

from src.modules.crm.domain.customer import CustomerIdentity, CustomerProfile
from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerIdentityModel,
    CustomerProfileModel,
    JourneyEventModel,
)

logger = structlog.get_logger()


class CustomerRepository:
    """Repository for customer persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize customer repository."""
        self.db = db

    def _to_domain(self, model: CustomerProfileModel) -> CustomerProfile:
        identities = [
            CustomerIdentity(
                id=i.id,
                profile_id=i.profile_id,
                tenant_id=i.tenant_id,
                type=i.type,
                value=i.value,
                is_primary=i.is_primary,
                verification_status=i.verification_status,
                last_seen_at=i.last_seen_at,
            )
            for i in model.identities
        ]
        return CustomerProfile(
            id=model.id,
            tenant_id=model.tenant_id,
            primary_email=model.primary_email,
            primary_phone=model.primary_phone,
            full_name=model.full_name,
            lifecycle_stage=model.lifecycle_stage or LifecycleStage.SUBSCRIBER,
            lead_score=model.lead_score or 0.0,
            rfm_segment=model.rfm_segment,
            traits=model.traits or {},
            computed_traits=model.computed_traits or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            identities=identities,
        )

    def find_by_identity(
        self,
        identity_type: IdentityType,
        identity_value: str,
        tenant_id: UUID,
    ) -> CustomerProfile | None:
        """Find a profile by one of its identities.

        Compare using the enum value (lowercase) which matches the PostgreSQL
        identitytype enum labels.
        """
        stmt = select(CustomerIdentityModel).where(
            cast(CustomerIdentityModel.type, String) == identity_type.value,
            CustomerIdentityModel.value == identity_value,
            CustomerIdentityModel.tenant_id == tenant_id,
        )
        identity = self.db.execute(stmt).scalars().first()

        if identity:
            return self._to_domain(identity.profile)
        return None

    def create(self, profile: CustomerProfile) -> CustomerProfile:
        """Execute create operation."""
        model = CustomerProfileModel(
            id=profile.id,
            tenant_id=profile.tenant_id,
            primary_email=profile.primary_email,
            primary_phone=profile.primary_phone,
            full_name=profile.full_name,
            lifecycle_stage=profile.lifecycle_stage,
            lead_score=profile.lead_score,
            rfm_segment=profile.rfm_segment,
            traits=profile.traits,
            computed_traits=profile.computed_traits,
        )
        self.db.add(model)

        for ident in profile.identities:
            i_model = CustomerIdentityModel(
                id=ident.id,
                profile_id=profile.id,
                tenant_id=ident.tenant_id,
                type=ident.type,
                value=ident.value,
                is_primary=ident.is_primary,
                verification_status=ident.verification_status,
            )
            self.db.add(i_model)

        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def create_with_identity(
        self,
        tenant_id: UUID,
        identity_type: IdentityType,
        identity_value: str,
        profile_data: dict[str, Any],
        lead_source: str | None = None,
        lead_source_detail: str | None = None,
    ) -> CustomerProfile:
        """Create a new customer profile with an initial identity.

        Optionally set lead_source and lead_source_detail for capture tracking.
        """
        profile_id = uuid.uuid4()

        full_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip() or None

        profile_model = CustomerProfileModel(
            id=profile_id,
            tenant_id=tenant_id,
            full_name=full_name,
            traits=profile_data.get("traits", {}),
            lead_source=lead_source,
            lead_source_detail=lead_source_detail,
            first_seen_at=datetime.now(UTC),
        )
        self.db.add(profile_model)

        identity_model = CustomerIdentityModel(
            id=uuid.uuid4(),
            profile_id=profile_id,
            tenant_id=tenant_id,
            type=identity_type,
            value=identity_value,
            is_primary=True,
        )
        self.db.add(identity_model)

        self.db.commit()
        self.db.refresh(profile_model)

        return self._to_domain(profile_model)

    def find_by_trait(
        self,
        tenant_id: UUID,
        trait_key: str,
        trait_value: str,
    ) -> CustomerProfile | None:
        """Find a profile by a specific JSONB trait key/value.

        Used for ManyChat↔Meta identity bridge: find profiles by
        traits.instagram_username to prevent duplicates.
        """
        stmt = select(CustomerProfileModel).where(
            CustomerProfileModel.tenant_id == tenant_id,
            func.jsonb_extract_path_text(CustomerProfileModel.traits, trait_key) == trait_value,
            CustomerProfileModel.is_inactive == False,
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def merge_profiles(self, source_id: UUID, target_id: UUID, tenant_id: UUID) -> None:
        """Merge source profile into target: move identities + journey_events.

        The source profile is soft-deleted after merge. Used when the enricher
        discovers that a Meta-created profile and a ManyChat-created profile
        belong to the same person.
        """
        # Move identities from source to target
        self.db.execute(
            CustomerIdentityModel.__table__.update()
            .where(
                CustomerIdentityModel.profile_id == source_id,
                CustomerIdentityModel.tenant_id == tenant_id,
            )
            .values(profile_id=target_id),
        )

        # Move journey_events from source to target
        self.db.execute(
            JourneyEventModel.__table__.update()
            .where(
                JourneyEventModel.profile_id == source_id,
                JourneyEventModel.tenant_id == tenant_id,
            )
            .values(profile_id=target_id),
        )

        # Soft-delete the source profile
        source = (
            self.db.execute(
                select(CustomerProfileModel).where(
                    CustomerProfileModel.id == source_id,
                    CustomerProfileModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .first()
        )
        if source:
            source.is_inactive = True
            # Carry over any traits the target might be missing
            target = (
                self.db.execute(
                    select(CustomerProfileModel).where(
                        CustomerProfileModel.id == target_id,
                        CustomerProfileModel.tenant_id == tenant_id,
                    ),
                )
                .scalars()
                .first()
            )
            if target and source.traits:
                merged_traits = dict(target.traits or {})
                for k, v in source.traits.items():
                    if k not in merged_traits:
                        merged_traits[k] = v
                target.traits = merged_traits

        self.db.flush()
        logger.info(
            "profiles_merged",
            source_id=str(source_id),
            target_id=str(target_id),
            tenant_id=str(tenant_id),
        )

    def count_by_stage(self, tenant_id: UUID, stage: LifecycleStage) -> int:
        """Count by stage."""
        result = self.db.execute(
            select(func.count())
            .select_from(CustomerProfileModel)
            .where(
                CustomerProfileModel.tenant_id == tenant_id,
                CustomerProfileModel.lifecycle_stage == stage,
            ),
        )
        return result.scalar() or 0


class JourneyEventRepository:
    """Repository for journey event persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize journey event repository."""
        self.db = db

    def track_event(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        event_name: str,
        event_type: str,
        properties: dict | None = None,
        occurred_at: datetime | None = None,
    ) -> JourneyEventModel:
        """Create and persist a new journey event.

        Also updates the profile's last_activity_at timestamp.
        This is the canonical write path for journey events.
        """
        from sqlalchemy import select as sa_select

        now = occurred_at or datetime.now(UTC)

        event = JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=profile_id,
            tenant_id=tenant_id,
            event_name=event_name,
            event_type=event_type,
            properties=properties or {},
            occurred_at=now,
        )
        self.db.add(event)

        # Update profile last_activity_at
        profile = (
            self.db.execute(
                sa_select(CustomerProfileModel).where(
                    CustomerProfileModel.id == profile_id,
                    CustomerProfileModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .first()
        )
        if profile:
            profile.last_activity_at = now

        self.db.flush()
        return event

    def get_unique_visitors(self, tenant_id: UUID) -> int:
        """Return unique visitors."""
        try:
            result = self.db.execute(
                select(func.count())
                .select_from(JourneyEventModel)
                .where(
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == "page_view",
                ),
            )
            return result.scalar() or 0
        except Exception:  # noqa: BLE001 — infrastructure resilience
            return 0
