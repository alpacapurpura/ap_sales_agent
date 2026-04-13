"""Server-side offer completion scoring.

Port of ``frontend/src/features/offer-studio/utils/offer-health.ts`` so
both sides of the stack agree on the "% complete" value shown on the
header. Landing generation also depends on this — offers below 90% can't
be generated.

Section rules (mirrors frontend):
  - identity: public_name, archetype, value_level
  - strategy: avatar_match OR marketing_pain_points
  - psychology: marketing_pain_points AND marketing_desires
  - promise: headline_promise
  - pricing: pricing_options non-empty
  - closing: guarantee_type set (any value)
  - {archetype}_details: specific_details non-empty
  - instructors / resources / gallery / value_stack: optional

Sections per archetype match ``ARCHETYPE_BUILDER_CONFIG`` in
``frontend/src/features/offer-studio/config/offer-builder-config.ts``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from src.modules.offer.domain.enums import OfferArchetype

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.application.offer_service import OfferService
    from src.modules.offer.domain.offer import Offer


logger = structlog.get_logger(__name__)


# Mirror of ARCHETYPE_BUILDER_CONFIG from the frontend.
_ARCHETYPE_SECTIONS: dict[OfferArchetype, tuple[str, ...]] = {
    OfferArchetype.PRODUCTO: (
        "identity",
        "strategy",
        "psychology",
        "promise",
        "product_details",
        "value_stack",
        "resources",
        "gallery",
        "pricing",
        "closing",
    ),
    OfferArchetype.PROGRAMA: (
        "identity",
        "strategy",
        "psychology",
        "promise",
        "program_details",
        "instructors",
        "value_stack",
        "resources",
        "gallery",
        "pricing",
        "editions",
        "closing",
    ),
    OfferArchetype.SERVICIO: (
        "identity",
        "strategy",
        "psychology",
        "promise",
        "service_details",
        "instructors",
        "value_stack",
        "resources",
        "gallery",
        "pricing",
        "editions",
        "closing",
    ),
    OfferArchetype.MEMBRESIA: (
        "identity",
        "strategy",
        "psychology",
        "promise",
        "subscription_details",
        "value_stack",
        "resources",
        "gallery",
        "pricing",
        "closing",
    ),
    OfferArchetype.EXPERIENCIA: (
        "identity",
        "strategy",
        "psychology",
        "promise",
        "event_details",
        "instructors",
        "value_stack",
        "resources",
        "gallery",
        "pricing",
        "editions",
        "closing",
    ),
}

_DETAILS_SECTIONS = {
    "product_details",
    "service_details",
    "program_details",
    "event_details",
    "subscription_details",
}

_OPTIONAL_SECTIONS = {
    "resources",
    "gallery",
    "value_stack",
    "instructors",
    "editions",
}


def _has(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _sections_for(archetype: OfferArchetype | str | None) -> tuple[str, ...]:
    if isinstance(archetype, str):
        try:
            archetype = OfferArchetype(archetype)
        except ValueError:
            archetype = None
    if archetype is None or archetype not in _ARCHETYPE_SECTIONS:
        return _ARCHETYPE_SECTIONS[OfferArchetype.PRODUCTO]
    return _ARCHETYPE_SECTIONS[archetype]


def _validate_section(section_id: str, offer: Offer) -> str:
    """Return one of ``"complete"``, ``"incomplete"``, ``"optional"``."""
    if section_id in _OPTIONAL_SECTIONS:
        if section_id == "instructors" and _has(getattr(offer, "instructors", None)):
            return "complete"
        return "optional"

    if section_id == "identity":
        if (
            _has(getattr(offer, "public_name", None))
            and _has(getattr(offer, "archetype", None))
            and _has(getattr(offer, "value_level", None))
        ):
            return "complete"
        return "incomplete"

    if section_id == "strategy":
        if _has(getattr(offer, "target_avatar_match", None)) or _has(
            getattr(offer, "marketing_pain_points", None)
        ):
            return "complete"
        return "incomplete"

    if section_id == "psychology":
        if _has(getattr(offer, "marketing_pain_points", None)) and _has(
            getattr(offer, "marketing_desires", None)
        ):
            return "complete"
        return "incomplete"

    if section_id == "promise":
        if _has(getattr(offer, "headline_promise", None)):
            return "complete"
        return "incomplete"

    if section_id == "pricing":
        if _has(getattr(offer, "pricing_options", None)):
            return "complete"
        return "incomplete"

    if section_id == "closing":
        if _has(getattr(offer, "guarantee_type", None)):
            return "complete"
        return "incomplete"

    if section_id in _DETAILS_SECTIONS:
        details = getattr(offer, "specific_details", None)
        if details is None:
            return "incomplete"
        if isinstance(details, dict):
            return "complete" if len(details) > 0 else "incomplete"
        # Pydantic model — any non-empty model_dump counts as present.
        try:
            dumped = details.model_dump(exclude_none=True)
        except AttributeError:
            return "complete" if bool(details) else "incomplete"
        return "complete" if dumped else "incomplete"

    return "optional"


class OfferCompletionService:
    def __init__(self, *, offer_service: OfferService) -> None:
        self._offers = offer_service

    def compute(self, *, offer_id: UUID, tenant_id: UUID) -> dict[str, Any]:
        offer = self._offers.get_offer(offer_id, tenant_id)
        if offer is None:
            msg = f"Offer {offer_id} not found for tenant {tenant_id}"
            raise ValueError(msg)

        sections = _sections_for(getattr(offer, "archetype", None))
        completed = 0
        total = 0
        next_milestone: str | None = None

        for section_id in sections:
            status = _validate_section(section_id, offer)
            if status == "optional":
                continue
            total += 1
            if status == "complete":
                completed += 1
            elif next_milestone is None:
                next_milestone = section_id

        if total == 0:
            percentage = 100.0
        else:
            percentage = round((completed / total) * 100.0, 2)
            if percentage.is_integer():
                percentage = float(int(percentage))

        return {
            "percentage": percentage,
            "completed_sections": completed,
            "total_sections": total,
            "next_milestone": next_milestone,
        }


__all__ = ["OfferCompletionService"]
