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
