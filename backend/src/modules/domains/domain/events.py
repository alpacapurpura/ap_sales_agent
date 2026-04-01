from dataclasses import dataclass
from uuid import UUID


@dataclass
class DomainActivated:
    domain_id: UUID
    tenant_id: UUID
    hostname: str


@dataclass
class DomainRemoved:
    domain_id: UUID
    tenant_id: UUID
    hostname: str
