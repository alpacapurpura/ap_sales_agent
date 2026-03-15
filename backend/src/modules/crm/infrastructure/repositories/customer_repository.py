from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from uuid import UUID
from src.modules.crm.domain.customer import CustomerProfile, CustomerIdentity
from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel, CustomerIdentityModel, JourneyEventModel
import uuid

class CustomerRepository:
    def __init__(self, db: Session):
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
                last_seen_at=i.last_seen_at
            ) for i in model.identities
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
            identities=identities
        )

    def find_by_identity(self, identity_value: str, identity_type: IdentityType, tenant_id: UUID) -> Optional[CustomerProfile]:
        """
        Find a profile by one of its identities.
        Uses case-insensitive comparison on type to handle legacy lowercase
        enum values (e.g., 'telegram') alongside SQLAlchemy uppercase ('TELEGRAM').
        """
        identity = self.db.query(CustomerIdentityModel).filter(
            func.upper(cast(CustomerIdentityModel.type, String)) == identity_type.name,
            CustomerIdentityModel.value == identity_value,
            CustomerIdentityModel.tenant_id == tenant_id
        ).first()

        if identity:
            return self._to_domain(identity.profile)
        return None

    def create(self, profile: CustomerProfile) -> CustomerProfile:
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
            computed_traits=profile.computed_traits
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
                verification_status=ident.verification_status
            )
            self.db.add(i_model)

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def create_with_identity(self, tenant_id: UUID, identity_type: IdentityType, identity_value: str, profile_data: Dict[str, Any]) -> CustomerProfile:
        """
        Creates a new customer profile with an initial identity.
        """
        profile_id = uuid.uuid4()

        full_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip() or None

        profile_model = CustomerProfileModel(
            id=profile_id,
            tenant_id=tenant_id,
            full_name=full_name,
            traits=profile_data.get('traits', {})
        )
        self.db.add(profile_model)

        identity_model = CustomerIdentityModel(
            id=uuid.uuid4(),
            profile_id=profile_id,
            tenant_id=tenant_id,
            type=identity_type,
            value=identity_value,
            is_primary=True
        )
        self.db.add(identity_model)

        self.db.commit()
        self.db.refresh(profile_model)

        return self._to_domain(profile_model)

    def count_by_stage(self, tenant_id: UUID, stage: Any) -> int:
        return self.db.query(CustomerProfileModel).filter(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage == stage
        ).count()

class JourneyEventRepository:
    def __init__(self, db: Session):
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

        now = occurred_at or datetime.now(timezone.utc)

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
        profile = self.db.execute(
            sa_select(CustomerProfileModel).where(
                CustomerProfileModel.id == profile_id,
                CustomerProfileModel.tenant_id == tenant_id,
            )
        ).scalars().first()
        if profile:
            profile.last_activity_at = now

        self.db.flush()
        return event

    def get_unique_visitors(self, tenant_id: UUID) -> int:
        try:
            return self.db.query(JourneyEventModel).filter(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name == "page_view"
            ).count()
        except Exception:
            return 0
