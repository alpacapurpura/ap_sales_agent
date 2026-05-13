"""User Tenant Repository implementation."""

from uuid import UUID

from luana_core_iam.domain.tenant import Tenant
from luana_core_iam.infrastructure.models.tenant_model import TenantModel
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel
from sqlalchemy import select
from sqlalchemy.orm import Session


class UserTenantRepository:
    """Concrete repository implementation for user tenant."""

    def __init__(self, db: Session) -> None:
        """Initialize UserTenantRepository."""
        self.db = db

    def get_tenants_for_user(self, user_id: UUID) -> list[tuple[Tenant, str]]:
        """Return a list of (Tenant, role) tuples for a given user.

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
