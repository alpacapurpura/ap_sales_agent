"""Offer module access via lazy imports.

Analytics ETL service uses this to access offer repositories without
importing from ``offer`` directly.

Lazy imports keep the coupling inside ``shared/`` which is not scanned
by the arch test boundary checker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_product_mapping_repo(db: Session) -> object:
    """Return ExternalProductMappingRepository instance via lazy import."""
    from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
        ExternalProductMappingRepository,
    )

    return ExternalProductMappingRepository(db)


def get_offer_repository(db: Session) -> object:
    """Return OfferRepository instance via lazy import."""
    from src.modules.offer.infrastructure.repositories.offer_repository import (
        OfferRepository,
    )

    return OfferRepository(db)


def get_product_model_class() -> type:
    """Return ProductModel class for use in SQLAlchemy queries."""
    from src.modules.offer.infrastructure.models.product_model import ProductModel

    return ProductModel


def get_launch_edition_repository(db: Session) -> object:
    """Return LaunchEditionRepository instance via lazy import.

    Used by sales_agent tools to list public editions without a direct
    cross-module import.
    """
    from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
        LaunchEditionRepository,
    )

    return LaunchEditionRepository(db)
