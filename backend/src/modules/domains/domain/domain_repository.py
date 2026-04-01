from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.modules.domains.domain.domain_entity import TenantDomain


class DomainRepository(ABC):
    @abstractmethod
    def create(self, domain: TenantDomain) -> TenantDomain: ...

    @abstractmethod
    def get_by_id(self, domain_id: UUID, tenant_id: UUID) -> Optional[TenantDomain]: ...

    @abstractmethod
    def get_by_hostname(self, hostname: str) -> Optional[TenantDomain]: ...

    @abstractmethod
    def list_by_tenant(self, tenant_id: UUID) -> List[TenantDomain]: ...

    @abstractmethod
    def update(self, domain: TenantDomain) -> TenantDomain: ...

    @abstractmethod
    def soft_delete(self, domain_id: UUID, tenant_id: UUID) -> None: ...
