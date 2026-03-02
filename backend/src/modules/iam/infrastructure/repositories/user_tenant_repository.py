
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel
from src.modules.iam.infrastructure.models.tenant_model import TenantModel

class UserTenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_tenants_for_user(self, user_id: UUID) -> List[Tuple[Tenant, str]]:
        """
        Returns a list of (Tenant, role) tuples for a given user.
        Only returns active tenants.
        """
        results = (
            self.db.query(TenantModel, UserTenantModel.role)
            .join(UserTenantModel, TenantModel.id == UserTenantModel.tenant_id)
            .filter(UserTenantModel.user_id == user_id)
            .filter(TenantModel.is_active == True)
            .all()
        )
        
        return [(Tenant.model_validate(tenant), role) for tenant, role in results]
