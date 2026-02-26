from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel
from src.modules.iam.infrastructure.repositories.tenant_repository import TenantRepository
from src.modules.iam.api.dto.users import TenantSchema # Keep DTO for API compatibility

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.tenant_repository = TenantRepository(db)

    def get_user_tenants(self, user_id: UUID) -> List[TenantSchema]:
        """
        List all tenants the current user has access to.
        """
        # TODO: Move UserTenant logic to a specialized Repository (UserTenantRepository)
        links = self.db.query(UserTenantModel).filter(UserTenantModel.user_id == user_id).all()
        
        results = []
        for link in links:
            tenant = self.tenant_repository.get_by_id(link.tenant_id)
            if tenant and tenant.is_active:
                results.append(TenantSchema(
                    id=str(tenant.id),
                    name=tenant.name,
                    slug=tenant.slug,
                    role=link.role
                ))
                
        return results
