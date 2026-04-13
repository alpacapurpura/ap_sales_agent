from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.crm.domain.customer import CustomerIdentity, CustomerProfile
from src.modules.crm.domain.enums import IdentityType
from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
    JourneyEventRepository,
)


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomerRepository(db)
        self.event_repo = JourneyEventRepository(db)

    def identify(
        self, tenant_id: UUID, traits: dict[str, Any], identities: dict[str, str]
    ) -> CustomerProfile:
        """
        Identity Resolution: Find existing profile by ANY identity, or create new.
        """
        # 1. Try to find by identities
        profile = None

        # Lookup priority order: UserID, then Email, then Phone
        if "user_id" in identities:
            profile = self.repository.find_by_identity(
                IdentityType.USER_ID, identities["user_id"], tenant_id
            )

        if not profile and "email" in traits:
            profile = self.repository.find_by_identity(
                IdentityType.EMAIL, traits["email"], tenant_id
            )

        if not profile and "phone" in traits:
            profile = self.repository.find_by_identity(
                IdentityType.PHONE, traits["phone"], tenant_id
            )

        # 2. If found, update traits (merge)
        # TODO: Implement update logic in repo

        # 3. If not found, create new
        if not profile:
            import uuid

            profile_id = uuid.uuid4()
            new_identities = []

            # Extract identities from traits/args
            if "email" in traits:
                new_identities.append(
                    CustomerIdentity(
                        id=uuid.uuid4(),
                        profile_id=profile_id,
                        tenant_id=tenant_id,
                        type=IdentityType.EMAIL,
                        value=traits["email"],
                        is_primary=True,
                    )
                )

            # Create profile object
            profile = CustomerProfile(
                id=profile_id,
                tenant_id=tenant_id,
                primary_email=traits.get("email"),
                primary_phone=traits.get("phone"),
                full_name=traits.get("name"),
                traits=traits,
                identities=new_identities,
            )
            profile = self.repository.create(profile)

        return profile

    def track_event(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        event_name: str,
        event_type: str,
        properties: dict | None = None,
        occurred_at: datetime | None = None,
    ) -> JourneyEventModel:
        """Write a journey event and trigger score recalculation.

        This is the canonical entry point for journey event creation.
        Service layer orchestrates: persist event -> recalculate score.
        """
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        event = self.event_repo.track_event(
            profile_id=profile_id,
            tenant_id=tenant_id,
            event_name=event_name,
            event_type=event_type,
            properties=properties,
            occurred_at=occurred_at,
        )

        # Trigger scoring after event write (per locked decision)
        lifecycle_svc = LifecycleService(self.db)
        lifecycle_svc.recalculate_score(profile_id, tenant_id)

        return event
