"""Registry of domain persisters for the Interview Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_persister(domain: str, db: Session):
    """Get the appropriate persister for a domain."""
    from src.modules.copilot.infrastructure.persisters.brand_persister import (
        BrandPersister,
    )
    from src.modules.copilot.infrastructure.persisters.offer_persister import (
        OfferPersister,
    )

    registry = {
        "brand": BrandPersister,
        "offer": OfferPersister,
    }
    persister_cls = registry.get(domain)
    if not persister_cls:
        raise ValueError(f"No persister registered for domain '{domain}'")
    return persister_cls(db)
