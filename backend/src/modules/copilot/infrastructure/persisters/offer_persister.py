"""Persists interview mapa_global data into the Offer entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.modules.offer.domain.offer import (
    DeliverableItem,
    ObjectionItem,
    PricingStructure,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# Fields that require conversion from raw dicts to domain types.
COMPLEX_FIELD_TYPES: dict[str, type] = {
    "objections": ObjectionItem,
    "pricing_options": PricingStructure,
    "deliverables": DeliverableItem,
}

# All Offer entity fields that the interview can write to.
# Excludes system fields (id, tenant_id, status, deleted_at, etc.)
PERSISTABLE_FIELDS: set[str] = {
    "public_name",
    "archetype",
    "format_hint",
    "value_level",
    "delivery_model",
    "headline_promise",
    "primary_outcome",
    "time_to_value",
    "target_avatar_match",
    "marketing_pain_points",
    "marketing_desires",
    "objections",
    "pricing_options",
    "price_pay_in_full",
    "guarantee_type",
    "guarantee_terms",
    "deliverables",
    "includes_offers",
    "access_duration_text",
    "support_duration_days",
    "onboarding_action",
    "prerequisites",
    "requires_application",
    "anti_avatar_keywords",
    "currency",
}


class OfferPersister:
    """Writes confirmed interview data to an existing Offer entity.

    Unlike BrandPersister (which uses dot-notation for nested BrandSettings),
    OfferPersister maps directly to flat Offer entity fields. Complex types
    (objections, pricing_options, deliverables) are converted from raw dicts
    to their domain types.
    """

    def __init__(self, db: Session) -> None:
        """Initialize with database session."""
        self.db = db
        self.repo = OfferRepository(db)

    def persist(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
        entity_id: UUID | None = None,
    ) -> None:
        """Persist specific fields from mapa_global to an existing Offer.

        Args:
            tenant_id: The tenant.
            mapa_global: Full mapa_global dict (flat keys — Offer fields are top-level).
            fields_to_persist: Which field names to actually persist.
            entity_id: The offer ID. Required — OfferPersister updates, never creates.

        Raises:
            ValueError: If entity_id is not provided.

        """
        if entity_id is None:
            msg = (
                "entity_id is required for OfferPersister — "
                "offer interviews update existing offers, "
                "they do not create new ones."
            )
            raise ValueError(msg)

        offer = self.repo.get_by_id(entity_id, tenant_id)
        if not offer:
            logger.warning(
                "offer_persister_offer_not_found",
                tenant_id=str(tenant_id),
                offer_id=str(entity_id),
            )
            return

        updated_count = 0
        for field_path in fields_to_persist:
            if field_path not in mapa_global:
                continue
            if field_path not in PERSISTABLE_FIELDS:
                logger.debug(
                    "offer_persister_skip_non_persistable",
                    field=field_path,
                )
                continue

            value = mapa_global[field_path]
            converted_value = self._convert_value(field_path, value)
            setattr(offer, field_path, converted_value)
            updated_count += 1

        if updated_count > 0:
            self.repo.update(offer, tenant_id)
            logger.info(
                "offer_persister_success",
                tenant_id=str(tenant_id),
                offer_id=str(entity_id),
                fields_updated=updated_count,
            )

    def load_existing(self, tenant_id: UUID, entity_id: UUID) -> dict:
        """Load an existing Offer's data as a flat dict for pre-filling mapa_global.

        Complex types (objections, pricing_options, deliverables) are serialized
        as lists of dicts so the interview engine can display them.

        Returns:
            A flat dict of offer field values, or empty dict if not found.

        """
        offer = self.repo.get_by_id(entity_id, tenant_id)
        if not offer:
            return {}

        result: dict = {}
        for field_name in PERSISTABLE_FIELDS:
            value = getattr(offer, field_name, None)
            if value is None:
                continue

            # Serialize complex types to dicts for the mapa_global
            if field_name in COMPLEX_FIELD_TYPES and isinstance(value, list):
                result[field_name] = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value
                ]
            elif hasattr(value, "value"):
                # Enums → string value
                result[field_name] = value.value
            else:
                result[field_name] = value

        return result

    @staticmethod
    def _convert_value(field_name: str, value: object) -> object:
        """Convert raw values to domain types where needed."""
        if field_name in COMPLEX_FIELD_TYPES and isinstance(value, list):
            item_type = COMPLEX_FIELD_TYPES[field_name]
            converted = []
            for item in value:
                if isinstance(item, dict):
                    converted.append(item_type(**item))
                elif isinstance(item, item_type):
                    converted.append(item)
                else:
                    # Skip invalid items
                    logger.warning(
                        "offer_persister_invalid_item",
                        field=field_name,
                        item_type=type(item).__name__,
                    )
            return converted
        return value
