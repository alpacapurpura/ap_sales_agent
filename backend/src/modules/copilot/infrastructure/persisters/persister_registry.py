"""Registry of domain persisters for the Interview Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.copilot.infrastructure.persisters.brand_persister import (
    BrandPersister,
)
from src.modules.copilot.infrastructure.persisters.offer_persister import (
    OfferPersister,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_persister(
    domain: str,
    db: Session,
) -> BrandPersister | OfferPersister:
    """Get the appropriate persister for a domain."""
    registry: dict[str, type[BrandPersister | OfferPersister]] = {
        "brand": BrandPersister,
        "offer": OfferPersister,
    }
    persister_cls = registry.get(domain)
    if not persister_cls:
        msg = f"No persister registered for domain '{domain}'"
        raise ValueError(msg)
    return persister_cls(db)
