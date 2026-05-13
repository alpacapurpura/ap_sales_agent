"""Booking URL helper.

Returns the base URL for booking pages, preferring the tenant's primary
active custom domain over the platform DASHBOARD_DOMAIN fallback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from luana_core_platform.core.config import settings

if TYPE_CHECKING:
    from luana_core_platform.links.ports.domain_lookup import DomainLookupPort

logger = structlog.get_logger()


def get_booking_base_url(tenant_id: UUID | str, domain_lookup: DomainLookupPort) -> str:
    """Return the booking base URL for a tenant.

    Uses the tenant's primary active custom domain when available;
    falls back to settings.DASHBOARD_DOMAIN otherwise.
    """
    tid = UUID(str(tenant_id))
    hostname = domain_lookup.get_verified_domain(tid)
    if hostname:
        logger.debug(
            "booking_base_url_custom_domain",
            tenant_id=str(tid),
            hostname=hostname,
        )
        return f"https://{hostname}"
    return settings.DASHBOARD_DOMAIN
