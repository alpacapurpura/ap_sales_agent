"""Events domain definitions."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class DomainActivated:
    """Represent domain activated."""

    domain_id: UUID
    tenant_id: UUID
    hostname: str


@dataclass
class DomainRemoved:
    """Represent domain removed."""

    domain_id: UUID
    tenant_id: UUID
    hostname: str
