from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.marketing.domain.customer import CustomerProfile, CustomerIdentity
from src.modules.marketing.domain.enums import IdentityType
from src.modules.marketing.infrastructure.models.customer_model import CustomerProfileModel, CustomerIdentityModel

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

    def find_by_identity(self, type: IdentityType, value: str, tenant_id: UUID) -> Optional[CustomerProfile]:
        """
        Find a profile by one of its identities.
        """
        identity = self.db.query(CustomerIdentityModel).filter(
            CustomerIdentityModel.type == type,
            CustomerIdentityModel.value == value,
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
