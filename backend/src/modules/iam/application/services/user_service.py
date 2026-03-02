
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from src.modules.iam.infrastructure.repositories.user_tenant_repository import UserTenantRepository
from src.modules.iam.api.dto.users import TenantSchema # Keep DTO for API compatibility

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_tenant_repository = UserTenantRepository(db)

    def get_user_tenants(self, user_id: UUID) -> List[TenantSchema]:
        """
        List all tenants the current user has access to.
        """
        tenant_roles = self.user_tenant_repository.get_tenants_for_user(user_id)
        
        return [
            TenantSchema(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                role=role
            )
            for tenant, role in tenant_roles
        ]
