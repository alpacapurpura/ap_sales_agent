"""Booking URL helper.

Returns the base URL for booking pages, preferring the tenant's primary
active custom domain over the platform DASHBOARD_DOMAIN fallback.
"""

from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from src.core.config import settings

logger = structlog.get_logger()


def get_booking_base_url(tenant_id: UUID | str, db: Session) -> str:
    """Return the booking base URL for a tenant.

    Uses the tenant's primary active custom domain when available;
    falls back to settings.DASHBOARD_DOMAIN otherwise.
    """
    from src.modules.tenant_domains.domain.domain_entity import DomainStatus
    from src.modules.tenant_domains.infrastructure.domain_repository_impl import (
        DomainRepositoryImpl,
    )

    try:
        tid = UUID(str(tenant_id))
        repo = DomainRepositoryImpl(db)
        domains = repo.list_by_tenant(tid)
        primary = next(
            (d for d in domains if d.is_primary and d.status == DomainStatus.ACTIVE),
            None,
        )
        if primary:
            logger.debug(
                "booking_base_url_custom_domain",
                tenant_id=str(tid),
                hostname=primary.hostname,
            )
            return f"https://{primary.hostname}"
    except Exception:  # noqa: BLE001 — service resilience
        logger.warning(
            "booking_base_url_fallback",
            tenant_id=str(tenant_id),
        )

    return settings.DASHBOARD_DOMAIN
