from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.crm.domain.customer import CustomerProfile, CustomerIdentity
from src.modules.crm.domain.enums import IdentityType
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
            lifecycle_stage=model.lifecycle_stage,
            lead_score=model.lead_score,
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
        """
        identity = self.db.query(CustomerIdentityModel).filter(
            CustomerIdentityModel.type == identity_type,
            CustomerIdentityModel.value == identity_value,
            CustomerIdentityModel.tenant_id == tenant_id
        ).first()
        
        if identity:
            return self._to_domain(identity.profile)
        return None

    def create(self, profile: CustomerProfile) -> CustomerProfile:
        # Create Profile
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
        
        # Create Identities
        for ident in profile.identities:
            i_model = CustomerIdentityModel(
                id=ident.id,
                profile_id=profile.id, # Ensure link
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
        
        # Extract basic info from profile_data
        full_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip() or None
        
        # Create Profile Model
        profile_model = CustomerProfileModel(
            id=profile_id,
            tenant_id=tenant_id,
            full_name=full_name,
            traits=profile_data.get('traits', {})
        )
        self.db.add(profile_model)
        
        # Create Identity Model
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

    def get_unique_visitors(self, tenant_id: UUID) -> int:
        # Placeholder implementation - assumes anonymous_id in context
        # If context is JSONB, we can query it.
        # But for now, returning 0 if table empty or no logic.
        try:
            return self.db.query(JourneyEventModel).filter(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name == "page_view"
            ).count() # Simplified: total page views as proxy if distinct not easy
        except Exception:
            return 0
