from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel


class UserTenantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_tenants_for_user(self, user_id: UUID) -> list[tuple[Tenant, str]]:
        """
        Returns a list of (Tenant, role) tuples for a given user.
        Only returns active tenants.
        """
        results = self.db.execute(
            select(TenantModel, UserTenantModel.role)
            .join(UserTenantModel, TenantModel.id == UserTenantModel.tenant_id)
            .where(UserTenantModel.user_id == user_id)
            .where(UserTenantModel.is_active.is_(True))
            .where(TenantModel.is_active.is_(True)),
        ).all()

        return [(Tenant.model_validate(tenant), role) for tenant, role in results]
