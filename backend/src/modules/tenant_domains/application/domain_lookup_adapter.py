"""DomainLookupPort adapter — resolves primary active custom domain for a tenant."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from src.modules.tenant_domains.domain.domain_entity import DomainStatus
from src.modules.tenant_domains.infrastructure.domain_repository_impl import (
    DomainRepositoryImpl,
)
from src.shared.links.ports.domain_lookup import DomainLookupPort

logger = structlog.get_logger()


class DomainLookupAdapter(DomainLookupPort):
    """Concrete DomainLookupPort backed by the tenant_domains repository."""

    def __init__(self, db: Session) -> None:
        """Initialize with DB session."""
        self.repo = DomainRepositoryImpl(db)

    def get_verified_domain(self, tenant_id: UUID) -> str | None:
        """Return the primary active custom domain hostname, or None."""
        try:
            domains = self.repo.list_by_tenant(tenant_id)
            primary = next(
                (d for d in domains if d.is_primary and d.status == DomainStatus.ACTIVE),
                None,
            )
            if primary:
                return primary.hostname
        except (ValueError, KeyError, AttributeError, RuntimeError):
            logger.warning("domain_lookup_error", tenant_id=str(tenant_id))
        return None
