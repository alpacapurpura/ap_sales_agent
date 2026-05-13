"""User Service for the iam module."""

from uuid import UUID

from luana_core_iam.api.dto.users import TenantSchema  # Keep DTO for API compatibility
from luana_core_iam.infrastructure.repositories.user_tenant_repository import (
    UserTenantRepository,
)
from sqlalchemy.orm import Session


class UserService:
    """Manage user operations."""

    def __init__(self, db: Session) -> None:
        """Initialize UserService."""
        self.db = db
        self.user_tenant_repository = UserTenantRepository(db)

    def get_user_tenants(self, user_id: UUID) -> list[TenantSchema]:
        """List all tenants the current user has access to."""
        tenant_roles = self.user_tenant_repository.get_tenants_for_user(user_id)

        return [
            TenantSchema(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                role=role,
            )
            for tenant, role in tenant_roles
        ]
