"""DomainLookupPort — cross-module port for custom domain resolution.

``scheduling`` uses this to build booking URLs without importing from
``tenant_domains`` directly.

Canonical implementation: ``tenant_domains.application.domain_lookup_adapter``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class DomainLookupPort(ABC):
    """Port for resolving a tenant's primary verified domain."""

    @abstractmethod
    def get_verified_domain(self, tenant_id: UUID) -> str | None:
        """Return the primary active custom domain hostname, or None."""
        ...


def create_domain_lookup(db: Session) -> DomainLookupPort:
    """Create a DomainLookupPort instance.

    Lazy-imports the concrete adapter from tenant_domains.
    """
    from src.modules.tenant_domains.application.domain_lookup_adapter import (
        DomainLookupAdapter,
    )

    return DomainLookupAdapter(db)
