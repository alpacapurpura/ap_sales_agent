from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.tenant_domains.domain.domain_entity import TenantDomain


class DomainRepository(ABC):
    @abstractmethod
    def create(self, domain: TenantDomain) -> TenantDomain: ...

    @abstractmethod
    def get_by_id(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain | None: ...

    @abstractmethod
    def get_by_hostname(self, hostname: str) -> TenantDomain | None: ...

    @abstractmethod
    def list_by_tenant(self, tenant_id: UUID) -> list[TenantDomain]: ...

    @abstractmethod
    def update(self, domain: TenantDomain) -> TenantDomain: ...

    @abstractmethod
    def soft_delete(self, domain_id: UUID, tenant_id: UUID) -> None: ...
