"""Registry of domain persisters for the Interview Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_copilot.infrastructure.persisters.brand_persister import (
    BrandPersister,
)
from luana_core_copilot.infrastructure.persisters.buyer_persona_persister import (
    BuyerPersonaPersister,
)
from luana_core_copilot.infrastructure.persisters.offer_persister import (
    OfferPersister,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_persister(
    domain: str,
    db: Session,
) -> BrandPersister | BuyerPersonaPersister | OfferPersister:
    """Get the appropriate persister for a domain."""
    registry: dict[str, type[BrandPersister | BuyerPersonaPersister | OfferPersister]] = {
        "brand": BrandPersister,
        "buyer_persona": BuyerPersonaPersister,
        "offer": OfferPersister,
    }
    persister_cls = registry.get(domain)
    if not persister_cls:
        msg = f"No persister registered for domain '{domain}'"
        raise ValueError(msg)
    return persister_cls(db)
