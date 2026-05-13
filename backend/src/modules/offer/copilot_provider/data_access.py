"""Offer ``DataAccessProvider`` — F5 ``ask_tenant_data`` integration.

Wraps :class:`OfferRepository.search` behind the ``DataAccessProvider`` port so
the copilot's ``ask_tenant_data`` tool can fetch offers without importing the
repo directly (preserves the cross-module ratchet).

[COPILOT-PROVIDER-PATTERN]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luana_core_copilot.domain.ports import DataQueryPlan, DataQueryResult

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from uuid import UUID

    from luana_core_offer_studio.domain.offer import Offer
    from sqlalchemy.orm import Session


def _default_db_factory() -> Session:
    from luana_core_platform.core.database import SessionLocal

    return SessionLocal()


def _offer_to_row(offer: Offer) -> dict[str, Any]:
    """Project an ``Offer`` to a copilot-friendly row dict (no PII)."""
    archetype = offer.archetype.value if offer.archetype is not None else None
    status = offer.status.value if offer.status is not None else None
    value_level = offer.value_level.value if offer.value_level is not None else None
    return {
        "id": str(offer.id),
        "name": offer.public_name,
        "status": status,
        "archetype": archetype,
        "value_level": value_level,
        "is_lead_magnet": bool(offer.is_lead_magnet),
        "headline_promise": offer.headline_promise or "",
        "primary_outcome": offer.primary_outcome or "",
    }


class OfferDataAccessProvider:
    """Read-only data accessor for the offer module."""

    SUPPORTED_KINDS = frozenset({"offer_lookup"})

    def __init__(
        self,
        db_factory: Callable[[], Session] | None = None,
    ) -> None:
        """Optional ``db_factory`` lets tests inject a fixture session."""
        self._db_factory = db_factory or _default_db_factory

    def supports(self, kind: str) -> bool:
        return kind in self.SUPPORTED_KINDS

    async def execute(
        self,
        *,
        tenant_id: UUID,
        plan: DataQueryPlan,
        context: Mapping[str, Any] | None = None,
    ) -> DataQueryResult:
        if not self.supports(plan.kind):
            msg = (
                f"OfferDataAccessProvider does not support kind {plan.kind!r}. "
                f"Expected one of {sorted(self.SUPPORTED_KINDS)}."
            )
            raise ValueError(msg)

        from luana_core_offer_studio.infrastructure.repositories.offer_repository import (
            OfferRepository,
        )

        ctx = dict(context or {})
        db = ctx.get("db")
        owns_session = db is None
        if db is None:
            db = self._db_factory()
        try:
            repo = OfferRepository(db)
            offers = repo.search(
                tenant_id=tenant_id,
                name_query=plan.filters.get("name_query"),
                status=plan.filters.get("status", "active"),
                since=plan.filters.get("since"),
                limit=plan.limit,
            )
            rows = [_offer_to_row(o) for o in offers]
            return DataQueryResult(
                rows=rows,
                metadata={
                    "count": len(rows),
                    "kind": "offer_lookup",
                    "active_count": sum(1 for r in rows if r["status"] == "active"),
                    "archived_count": sum(1 for r in rows if r["status"] == "archived"),
                },
            )
        finally:
            if owns_session:
                db.close()
