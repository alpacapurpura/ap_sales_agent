"""CRM identity resolution service."""

from typing import Any
from uuid import UUID

from src.modules.crm.domain.enums import IdentityType
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel as CustomerProfile,
)
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
)


class IdentityService:
    """Service for identity operations."""

    def __init__(self, customer_repository: CustomerRepository) -> None:
        """Initialize identity service."""
        self.customer_repository = customer_repository

    def get_or_create_customer(
        self,
        tenant_id: UUID,
        identity_type: IdentityType,
        identity_value: str,
        profile_data: dict[str, Any],
        lead_source: str | None = None,
        lead_source_detail: str | None = None,
    ) -> tuple[CustomerProfile, bool]:
        """Busca un cliente por su identidad. Si no existe, lo crea.

        Returns:
            Tuple of (profile, was_created). was_created is True only for new profiles.

        """
        # Intentar buscar cliente existente pasando tenant_id explícitamente
        existing_customer = self.customer_repository.find_by_identity(
            identity_value=identity_value,
            identity_type=identity_type,
            tenant_id=tenant_id,
        )

        if existing_customer:
            return existing_customer, False

        # Si no existe, crear uno nuevo
        new_customer = self.customer_repository.create_with_identity(
            tenant_id=tenant_id,
            identity_type=identity_type,
            identity_value=identity_value,
            profile_data=profile_data,
            lead_source=lead_source,
            lead_source_detail=lead_source_detail,
        )
        return new_customer, True
