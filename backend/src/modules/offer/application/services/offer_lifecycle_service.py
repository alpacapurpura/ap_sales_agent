"""Offer lifecycle service.

Orchestrates Draft / Active / Paused / Archived transitions exposed by the
header status switcher. Validates each transition against the canonical
state machine in ``offer.domain.lifecycle`` and delegates to
``OfferService`` for the actual persistence.

Archive transitions reuse ``OfferService.archive_offer`` (which also
unpublishes the embedded landing page config) — this service must never
write ``ARCHIVED`` directly via ``patch_offer``. Archived offers cannot
leave the archived state via this endpoint — use ``POST /restore``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_offer_studio.domain.enums import OfferStatus
from luana_core_offer_studio.domain.events import OfferStatusChanged
from luana_core_offer_studio.domain.exceptions import InvalidTransitionError
from luana_core_offer_studio.domain.lifecycle import (
    LIFECYCLE_TRANSITIONS,
    OfferLifecycleStatus,
)
from luana_core_platform.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_offer_studio.application.offer_service import OfferService
    from luana_core_offer_studio.domain.offer import Offer


logger = structlog.get_logger(__name__)


# Mapping between the broader OfferStatus enum and the writable lifecycle
# subset. OfferStatus has WAITLIST / SOLD_OUT members which the header
# cannot mutate — those show up as "other" and block the switcher UI.
_STATUS_TO_LIFECYCLE: dict[OfferStatus, OfferLifecycleStatus] = {
    OfferStatus.DRAFT: OfferLifecycleStatus.DRAFT,
    OfferStatus.ACTIVE: OfferLifecycleStatus.ACTIVE,
    OfferStatus.PAUSED: OfferLifecycleStatus.PAUSED,
    OfferStatus.ARCHIVED: OfferLifecycleStatus.ARCHIVED,
}


def _to_lifecycle(status: OfferStatus | str) -> OfferLifecycleStatus | None:
    """Return the lifecycle projection of an OfferStatus, or None if the.

    status is outside the writable subset (e.g. ``WAITLIST``).
    """
    if isinstance(status, str):
        try:
            status = OfferStatus(status)
        except ValueError:
            return None
    return _STATUS_TO_LIFECYCLE.get(status)


class OfferLifecycleService:
    """Transition engine for the header status switcher."""

    def __init__(
        self,
        offer_service: OfferService,
        event_bus: object | None = None,
    ) -> None:
        """Initialize service with dependencies."""
        self._offers = offer_service
        self._events = event_bus

    # ------------------------------------------------------------------ main
    def change_status(
        self,
        *,
        offer_id: UUID,
        new_status: OfferLifecycleStatus,
        tenant_id: UUID,
        actor_user_id: UUID | None = None,
    ) -> Offer:
        """Move an offer into ``new_status`` after validating the transition.

        Raises:
            ValueError: offer not found.
            InvalidTransitionError: transition not allowed by the state machine.

        """
        offer = self._offers.get_offer(offer_id, tenant_id)
        if offer is None:
            msg = f"Offer {offer_id} not found for tenant {tenant_id}"
            raise ValueError(msg)

        # Archived-at flag wins over status string for "is this archived?"
        # The repo keeps status="archived" in sync, but we treat the
        # archived_at timestamp as canonical to guarantee correct behaviour
        # even if the two ever drift.
        current_lifecycle: OfferLifecycleStatus
        if getattr(offer, "archived_at", None) is not None:
            current_lifecycle = OfferLifecycleStatus.ARCHIVED
        else:
            mapped = _to_lifecycle(offer.status)
            if mapped is None:
                # WAITLIST / SOLD_OUT: header cannot mutate these.
                raise InvalidTransitionError(
                    OfferLifecycleStatus.DRAFT,  # placeholder; message rebuilt
                    new_status,
                    message=(f"Current status {offer.status!r} is not writable from the header switcher"),
                )
            current_lifecycle = mapped

        # Noop: same-state request is idempotent.
        if current_lifecycle == new_status:
            logger.info(
                "offer_lifecycle_noop",
                offer_id=str(offer_id),
                tenant_id=str(tenant_id),
                status=new_status.value,
            )
            return offer

        # Archived is terminal from this endpoint — use POST /restore.
        allowed = LIFECYCLE_TRANSITIONS.get(current_lifecycle, set())
        if new_status not in allowed:
            raise InvalidTransitionError(current_lifecycle, new_status)

        # Archive path — delegate to the canonical OfferService flow so the
        # embedded landing config is unpublished in the same transaction.
        if new_status is OfferLifecycleStatus.ARCHIVED:
            updated = self._offers.archive_offer(offer_id, tenant_id)
            self._emit_status_changed(
                offer_id=offer_id,
                tenant_id=tenant_id,
                from_status=current_lifecycle,
                to_status=new_status,
                actor_user_id=actor_user_id,
            )
            logger.info(
                "offer_lifecycle_archived",
                offer_id=str(offer_id),
                tenant_id=str(tenant_id),
            )
            return updated

        # Normal path — patch status via OfferService.
        target_status = OfferStatus(new_status.value)
        updated = self._offers.patch_offer(
            offer_id=offer_id,
            tenant_id=tenant_id,
            update_data={"status": target_status},
        )
        self._emit_status_changed(
            offer_id=offer_id,
            tenant_id=tenant_id,
            from_status=current_lifecycle,
            to_status=new_status,
            actor_user_id=actor_user_id,
        )
        logger.info(
            "offer_lifecycle_transitioned",
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            from_status=current_lifecycle.value,
            to_status=new_status.value,
        )
        return updated

    # ------------------------------------------------------------------ evts
    def _emit_status_changed(
        self,
        *,
        offer_id: UUID,
        tenant_id: UUID,
        from_status: OfferLifecycleStatus,
        to_status: OfferLifecycleStatus,
        actor_user_id: UUID | None,
    ) -> None:
        if self._events is None:
            return
        event = OfferStatusChanged(
            tenant_id=tenant_id,
            occurred_at=utc_now(),
            offer_id=offer_id,
            from_status=from_status,
            to_status=to_status,
            actor_user_id=actor_user_id,
        )
        try:
            self._events.publish(event)
        except (ValueError, KeyError, RuntimeError):
            logger.warning(
                "offer_lifecycle_event_publish_failed",
                offer_id=str(offer_id),
                to_status=to_status.value,
            )


__all__ = ["OfferLifecycleService"]
