"""Landing generation orchestration for the offer header.

Drives ``/landing/status``, ``/landing/generate``, ``/landing/publish``,
``/landing/unpublish``, and ``/landing/regenerate`` from the offer page.

The heavy lifting — real AI copy/layout generation — is out of scope for
this refactor. This service writes placeholder rows in ``queued`` status
and returns immediately; a downstream worker (or future phase) consumes
the events and actually renders the landing.

``is_outdated`` is computed at read time as
``landing.generated_at < offer.updated_at`` — never stored — so the
badge is always consistent with the underlying data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog

from src.modules.offer.domain.events import (
    LandingGenerationRequested,
    LandingPublished,
    LandingRegenerationRequested,
    LandingUnpublished,
)
from src.modules.offer.domain.exceptions import LandingNotReadyError
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.application.offer_service import OfferService
    from src.modules.offer.application.ports import ILandingGenerationRepository
    from src.modules.offer.application.services.offer_completion_service import (
        OfferCompletionService,
    )


logger = structlog.get_logger(__name__)


_MIN_COMPLETION_FOR_GENERATE = 90.0


def _as_aware_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class LandingGenerationService:
    def __init__(
        self,
        *,
        completion_service: OfferCompletionService,
        landing_repo: ILandingGenerationRepository,
        offer_service: OfferService,
        event_bus: object | None = None,
    ) -> None:
        self._completion = completion_service
        self._landing_repo = landing_repo
        self._offers = offer_service
        self._events = event_bus

    # ---------------------------------------------------------------- status
    def get_status(self, *, tenant_id: UUID, offer_id: UUID) -> dict[str, Any]:
        landing = self._landing_repo.get_by_offer_id(tenant_id, offer_id)
        if landing is None:
            return {
                "generated_at": None,
                "is_published": False,
                "offer_snapshot_version": None,
                "is_outdated": False,
                "job_id": None,
                "job_status": "idle",
            }

        generated_at = _as_aware_utc(getattr(landing, "generated_at", None))
        is_outdated = False
        if generated_at is not None:
            offer = self._offers.get_offer(offer_id, tenant_id)
            offer_updated = _as_aware_utc(getattr(offer, "updated_at", None))
            if offer_updated is not None and generated_at < offer_updated:
                is_outdated = True

        return {
            "generated_at": generated_at,
            "is_published": bool(getattr(landing, "is_published", False)),
            "offer_snapshot_version": getattr(landing, "offer_snapshot_version", None),
            "is_outdated": is_outdated,
            "job_id": getattr(landing, "generation_job_id", None),
            "job_status": getattr(landing, "generation_job_status", None),
        }

    # -------------------------------------------------------------- generate
    def generate(self, *, tenant_id: UUID, offer_id: UUID) -> dict[str, Any]:
        completion = self._completion.compute(offer_id=offer_id, tenant_id=tenant_id)
        percentage = float(completion.get("percentage", 0))
        if percentage < _MIN_COMPLETION_FOR_GENERATE:
            raise LandingNotReadyError(offer_id, percentage)

        snapshot_version = utc_now().strftime("%Y%m%d%H%M%S")
        job_id = uuid4()
        landing = self._landing_repo.upsert_for_generation(
            tenant_id=tenant_id,
            offer_id=offer_id,
            snapshot_version=snapshot_version,
            job_id=job_id,
            job_status="queued",
        )
        self._emit(
            LandingGenerationRequested(
                tenant_id=tenant_id,
                occurred_at=utc_now(),
                offer_id=offer_id,
                snapshot_version=snapshot_version,
                job_id=job_id,
            ),
        )
        logger.info(
            "offer_landing_generate_queued",
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            job_id=str(job_id),
            snapshot_version=snapshot_version,
        )
        return {
            "job_id": getattr(landing, "generation_job_id", job_id),
            "job_status": getattr(landing, "generation_job_status", "queued"),
            "snapshot_version": snapshot_version,
        }

    # ------------------------------------------------------------ regenerate
    def regenerate(self, *, tenant_id: UUID, offer_id: UUID) -> dict[str, Any]:
        existing = self._landing_repo.get_by_offer_id(tenant_id, offer_id)
        previous_snapshot = getattr(existing, "offer_snapshot_version", None) if existing else None
        snapshot_version = utc_now().strftime("%Y%m%d%H%M%S")
        job_id = uuid4()
        landing = self._landing_repo.upsert_for_generation(
            tenant_id=tenant_id,
            offer_id=offer_id,
            snapshot_version=snapshot_version,
            job_id=job_id,
            job_status="queued",
        )
        self._emit(
            LandingRegenerationRequested(
                tenant_id=tenant_id,
                occurred_at=utc_now(),
                offer_id=offer_id,
                previous_snapshot_version=previous_snapshot,
                snapshot_version=snapshot_version,
                job_id=job_id,
            ),
        )
        logger.info(
            "offer_landing_regenerate_queued",
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            job_id=str(job_id),
            previous_snapshot_version=previous_snapshot,
            snapshot_version=snapshot_version,
        )
        return {
            "job_id": getattr(landing, "generation_job_id", job_id),
            "job_status": getattr(landing, "generation_job_status", "queued"),
            "snapshot_version": snapshot_version,
        }

    # --------------------------------------------------------------- publish
    def publish(self, *, tenant_id: UUID, offer_id: UUID) -> object:
        landing = self._landing_repo.get_by_offer_id(tenant_id, offer_id)
        if landing is None:
            raise LandingNotReadyError(offer_id, 0.0)
        landing.is_published = True
        saved = self._landing_repo.save(landing)
        self._emit(
            LandingPublished(
                tenant_id=tenant_id,
                occurred_at=utc_now(),
                offer_id=offer_id,
                landing_page_id=getattr(landing, "id", offer_id),
            ),
        )
        logger.info(
            "offer_landing_published",
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
        )
        return saved

    # ------------------------------------------------------------- unpublish
    def unpublish(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        reason: str = "manual",
    ) -> object:
        landing = self._landing_repo.get_by_offer_id(tenant_id, offer_id)
        if landing is None:
            raise LandingNotReadyError(offer_id, 0.0)
        landing.is_published = False
        saved = self._landing_repo.save(landing)
        self._emit(
            LandingUnpublished(
                tenant_id=tenant_id,
                occurred_at=utc_now(),
                offer_id=offer_id,
                landing_page_id=getattr(landing, "id", offer_id),
                reason=reason,
            ),
        )
        logger.info(
            "offer_landing_unpublished",
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            reason=reason,
        )
        return saved

    # ----------------------------------------------------------------- evts
    def _emit(self, event: object) -> None:
        if self._events is None:
            return
        try:
            self._events.publish(event)
        except Exception:  # noqa: BLE001 — service resilience
            logger.warning("offer_landing_event_publish_failed")


__all__ = ["LandingGenerationService"]
