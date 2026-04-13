"""Domain repository interface for tenant domains."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.tenant_domains.domain.domain_entity import TenantDomain


class DomainRepository(ABC):
    """Abstract repository interface for domain."""

    @abstractmethod
    def create(self, domain: TenantDomain) -> TenantDomain:
        """Create a new tenant domain."""

    @abstractmethod
    def get_by_id(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain | None:
        """Retrieve a domain by its ID and tenant."""

    @abstractmethod
    def get_by_hostname(self, hostname: str) -> TenantDomain | None:
        """Retrieve a domain by its hostname."""

    @abstractmethod
    def list_by_tenant(self, tenant_id: UUID) -> list[TenantDomain]:
        """List all domains for a tenant."""

    @abstractmethod
    def update(self, domain: TenantDomain) -> TenantDomain:
        """Update an existing tenant domain."""

    @abstractmethod
    def soft_delete(self, domain_id: UUID, tenant_id: UUID) -> None:
        """Soft-delete a domain by setting deleted_at."""
