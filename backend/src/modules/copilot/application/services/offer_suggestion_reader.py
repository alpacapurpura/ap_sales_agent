"""Read-side helper: offer preset flags + incomplete signals for suggestions.

Tenant-scoped. Pure read. No mutation, no transaction boundary.
Consumed by ``offer_section_tools.py`` (existing) AND ``OfferSuggestionProvider`` (new).

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class OfferRowVO:
    """Minimal view of an offer row — no SQLAlchemy model leaks out."""

    id: UUID
    preset_id: str | None


class OfferSuggestionReader:
    """Read-only access to offer data for the suggestion engine.

    Opens no transactions — caller owns the session lifecycle.
    All reads pass ``tenant_id`` per ``tenant-isolation.md``.
    """

    def __init__(self, db: Session, *, tenant_id: UUID) -> None:
        """Initialise with an open session and the tenant scope."""
        self._db = db
        self._tenant_id = tenant_id

    def list_offers(self) -> list[OfferRowVO]:
        """Return all active offers for the tenant as lightweight VOs."""
        try:
            from src.shared.links.ports.offer import get_offer_repository

            repo = get_offer_repository(self._db)
            raw = repo.get_all_by_tenant(self._tenant_id)  # type: ignore[attr-defined]
            return [
                OfferRowVO(
                    id=UUID(str(getattr(o, "id", "00000000-0000-0000-0000-000000000000"))),
                    preset_id=getattr(o, "preset_id", None),
                )
                for o in raw
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "offer_suggestion_reader_list_offers_failed",
                tenant_id=str(self._tenant_id),
                error=str(exc),
            )
            return []

    def get_preset_flags(self, offer_id: UUID | None) -> list[str]:
        """Return preset flags (str values) for ``offer_id`` or [] if absent."""
        if offer_id is None:
            return []
        try:
            from src.shared.links.ports.offer import get_offer_repository, get_offer_type_preset

            repo = get_offer_repository(self._db)
            offers = repo.get_all_by_tenant(self._tenant_id)  # type: ignore[attr-defined]
            target = next(
                (o for o in offers if str(getattr(o, "id", "")) == str(offer_id)),
                None,
            )
            if target is None:
                return []
            preset = get_offer_type_preset(getattr(target, "preset_id", None))
            if preset is None:
                return []
            return [f.value for f in getattr(preset, "default_flags", ())]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "offer_suggestion_reader_get_flags_failed",
                tenant_id=str(self._tenant_id),
                offer_id=str(offer_id),
                error=str(exc),
            )
            return []

    def detect_lead_magnet_without_core(self) -> bool:
        """Return True when tenant has a lead-magnet offer but no core offer.

        Heuristic: any offer with ``is_lead_magnet`` flag + no offer without it.
        """
        try:
            from src.shared.links.ports.offer import get_offer_repository, get_offer_type_preset

            repo = get_offer_repository(self._db)
            offers = repo.get_all_by_tenant(self._tenant_id)  # type: ignore[attr-defined]
            has_lead_magnet = False
            has_core = False
            for o in offers:
                preset = get_offer_type_preset(getattr(o, "preset_id", None))
                flags = [f.value for f in getattr(preset, "default_flags", ())] if preset else []
                if "is_lead_magnet" in flags:
                    has_lead_magnet = True
                else:
                    has_core = True
            return has_lead_magnet and not has_core
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "offer_suggestion_reader_detect_lead_magnet_failed",
                tenant_id=str(self._tenant_id),
                error=str(exc),
            )
            return False


__all__ = ["OfferRowVO", "OfferSuggestionReader"]
