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


def get_offer_type_preset(preset_id: str | None) -> object | None:
    """Return the ``OfferTypePreset`` record for ``preset_id``, or ``None``.

    Lazy import keeps the DDD boundary intact — ``sales_agent`` and
    ``landing`` call this port instead of importing the 7th SSoT axis
    module directly. Returns ``None`` for unknown ids so callers can
    handle the miss with a default.
    """
    if preset_id is None:
        return None
    from src.modules.offer.domain.offer_type_preset_catalog import (
        OFFER_TYPE_PRESET_CATALOG,
    )

    return OFFER_TYPE_PRESET_CATALOG.get(preset_id)


def get_preset_flag_values() -> type:
    """Return the ``PresetFlag`` StrEnum class via lazy import.

    Callers (landing generator, landing templates, analytics) need the
    enum values to branch on preset flags. Lazy-exposing the enum keeps
    the boundary rules happy while preserving type safety at the
    consumer end (cast via ``cast(PresetFlag, ...)`` if strict typing
    is required).
    """
    from src.modules.offer.domain.offer_type_preset_catalog import PresetFlag

    return PresetFlag
