"""Application service for the tenant_profile bounded context.

Orchestrates:
1. Read/write via :class:`TenantProfileRepository`.
2. Domain command invocation on the aggregate.
3. Domain event dispatch to in-process bus and/or WebSocket broadcast.

Business rules are enforced exclusively by the domain aggregate; this service
only wires the pieces together.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_platform.domain.expert_business_type import ExpertBusinessType
    from luana_core_tenant_profile.domain.repository import TenantProfileRepository
    from luana_core_tenant_profile.domain.tenant_profile import TenantProfile

logger = structlog.get_logger()


class TenantProfileService:
    """Orchestrates reads and writes for the ``TenantProfile`` aggregate.

    Args:
        repo: Concrete repository implementation (injected by the API layer).
    """

    def __init__(self, repo: TenantProfileRepository) -> None:
        """Initialise with a concrete repository implementation."""
        self._repo = repo

    def get_profile(self, tenant_id: UUID) -> TenantProfile:
        """Return the current profile (or a fresh empty one for new tenants)."""
        return self._repo.get_or_init(tenant_id)

    def update_business_types(
        self,
        tenant_id: UUID,
        new_types: tuple[ExpertBusinessType, ...],
    ) -> TenantProfile:
        """Declare or change the tenant's business_types.

        Raises:
            ValueError: If ``new_types`` violates length or uniqueness rules.
            BusinessTypesChangeRateLimitedError: If a change is requested within
                the 30-day rate-limit window after the last change.
        """
        profile = self._repo.get_or_init(tenant_id)

        # Domain command — may raise ValueError or BusinessTypesChangeRateLimitedError.
        events = profile.update_business_types(new_types)

        if not events:
            # No-op write — same set, nothing to persist.
            logger.info(
                "tenant_profile_business_types_noop",
                tenant_id=str(tenant_id),
                business_types=[bt.value for bt in new_types],
            )
            return profile

        self._repo.save(profile)

        for event in events:
            self._dispatch_event(event)

        return profile

    def _dispatch_event(self, event: object) -> None:
        """Dispatch a domain event to in-process subscribers.

        Currently logs the event. Future: wire to shared EventBus and WebSocket
        broadcast for cache invalidation (§5 of CONTRACT.md).
        """
        from luana_core_tenant_profile.domain.events import (
            BusinessTypesChanged,
            TenantProfileInitialized,
        )

        if isinstance(event, TenantProfileInitialized):
            logger.info(
                "tenant_profile_initialized",
                tenant_id=str(event.tenant_id),
                business_types=[bt.value for bt in event.business_types],
                at=event.at.isoformat(),
            )
        elif isinstance(event, BusinessTypesChanged):
            logger.info(
                "business_types_changed",
                tenant_id=str(event.tenant_id),
                old=[bt.value for bt in event.old],
                new=[bt.value for bt in event.new],
                at=event.at.isoformat(),
            )
