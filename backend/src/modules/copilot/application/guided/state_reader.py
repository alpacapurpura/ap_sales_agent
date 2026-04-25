"""Best-effort entity state reader for the guided question hint (Fase 09.C).

Resolves the current entity for a given guided ``domain`` + ``entity_id``
and returns its ``model_dump()`` representation as a plain dict so
:func:`build_question_hint` can run :func:`next_question` against it.

Tolerates missing data, missing entity_id, repo import failures — never
raises. The hint is best-effort enrichment; the guided flow keeps
working when this returns None.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

__all__ = [
    "read_entity_state",
]


def read_entity_state(
    domain: str,
    *,
    tenant_id: UUID,
    entity_id: str | None,
    db: Session,
) -> dict[str, Any] | None:
    """Return a dict snapshot of the entity, or ``None`` when unavailable.

    Domain-specific:

    - ``"brand"``: tenant-singleton — ignores ``entity_id``. Reads via
      ``BrandRepository.get_settings(tenant_id).model_dump()``.
    - ``"offer"``: requires ``entity_id``. Reads via
      ``OfferRepository.get_by_id(tenant_id, offer_id)``.
    - ``"buyer_persona"``: requires ``entity_id``. Reads via
      ``BuyerPersonaRepository.get_by_id(tenant_id, persona_id)``.

    Any error → ``None`` (logged at WARNING level). Never raises.
    """
    try:
        if domain == "brand":
            return _read_brand(db, tenant_id)
        if domain == "offer":
            return _read_offer(db, tenant_id, entity_id)
        if domain == "buyer_persona":
            return _read_buyer_persona(db, tenant_id, entity_id)
    except Exception as exc:  # noqa: BLE001 — best-effort hint; never break advance flow
        logger.warning(
            "guided_state_read_failed",
            domain=domain,
            entity_id=entity_id,
            error=str(exc),
        )
        return None
    return None


def _read_brand(db: Session, tenant_id: UUID) -> dict[str, Any] | None:
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )

    repo = BrandRepository(db)
    settings = repo.get_settings(tenant_id)
    if settings is None or not hasattr(settings, "model_dump"):
        return None
    return settings.model_dump(mode="json")


def _read_offer(db: Session, tenant_id: UUID, entity_id: str | None) -> dict[str, Any] | None:
    if not entity_id:
        return None
    from src.modules.offer.infrastructure.repositories.offer_repository import (
        OfferRepository,
    )

    try:
        offer_uuid = UUID(entity_id)
    except (TypeError, ValueError):
        return None

    repo = OfferRepository(db)
    offer = repo.get_by_id(tenant_id, offer_uuid)
    if offer is None or not hasattr(offer, "model_dump"):
        return None
    return offer.model_dump(mode="json")


def _read_buyer_persona(db: Session, tenant_id: UUID, entity_id: str | None) -> dict[str, Any] | None:
    if not entity_id:
        return None
    from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
        BuyerPersonaRepository,
    )

    try:
        persona_uuid = UUID(entity_id)
    except (TypeError, ValueError):
        return None

    repo = BuyerPersonaRepository(db)
    persona = repo.get_by_id(tenant_id, persona_uuid)
    if persona is None or not hasattr(persona, "model_dump"):
        return None
    return persona.model_dump(mode="json")
