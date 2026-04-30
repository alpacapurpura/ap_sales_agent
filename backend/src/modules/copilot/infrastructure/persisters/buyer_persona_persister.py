"""Persists interview mapa_global data into BuyerPersona entities."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import structlog

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# BuyerPersona fields that are dicts (flattened with dot-notation).
_DICT_FIELDS = {"demographics", "psychographics", "buyer_journey"}

# BuyerPersona fields that are lists (stored directly, not flattened).
_LIST_FIELDS = {
    "pain_points",
    "desires",
    "purchase_triggers",
    "anti_patterns",
}

# Simple scalar fields.
_SCALAR_FIELDS = {"name", "tagline"}


class BuyerPersonaPersister:
    """Writes confirmed interview data to a BuyerPersona entity.

    Field-path conventions match the interview config in buyer_persona_config.py:
    - Dict fields use dot-notation: ``demographics.age_range``
    - List fields use the field name directly: ``pain_points``
    - Scalar fields use the field name directly: ``name``
    """

    def __init__(self, db: Session) -> None:
        """Initialize with database session."""
        self.db = db
        self.repo = BuyerPersonaRepository(db)

    def persist(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
        entity_id: UUID | None = None,
    ) -> UUID | None:
        """Persist fields from mapa_global to a BuyerPersona.

        If ``entity_id`` is provided, updates the existing persona.
        If ``entity_id`` is None, creates a new GLOBAL persona.

        Returns the persona UUID, or None if entity_id was given but not found.
        """
        if entity_id is not None:
            return self._update_existing(tenant_id, entity_id, mapa_global, fields_to_persist)
        return self._create_new(tenant_id, mapa_global, fields_to_persist)

    def load_existing(self, tenant_id: UUID, entity_id: UUID) -> dict:
        """Load persona data as a flat dict for pre-filling mapa_global.

        Dict fields are flattened to dot-notation. List/scalar fields stored directly.

        Returns flat dict or empty dict if not found.
        """
        persona = self.repo.get_by_id(tenant_id, entity_id)
        if not persona:
            return {}

        result: dict = {}

        for field in _SCALAR_FIELDS:
            value = getattr(persona, field, None)
            if value is not None:
                result[field] = value

        for field in _DICT_FIELDS:
            value = getattr(persona, field, None)
            if isinstance(value, dict):
                for k, v in value.items():
                    if v is not None:
                        result[f"{field}.{k}"] = v

        for field in _LIST_FIELDS:
            value = getattr(persona, field, None)
            if isinstance(value, list) and value:
                result[field] = value

        return result

    def _update_existing(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> UUID | None:
        persona = self.repo.get_by_id(tenant_id, entity_id)
        if not persona:
            logger.warning(
                "buyer_persona_persister_not_found",
                tenant_id=str(tenant_id),
                entity_id=str(entity_id),
            )
            return None

        updates = self._build_updates(mapa_global, fields_to_persist)
        if updates:
            self.repo.update(
                tenant_id=tenant_id,
                persona_id=entity_id,
                updates=updates,
            )
            logger.info(
                "buyer_persona_persister_updated",
                tenant_id=str(tenant_id),
                entity_id=str(entity_id),
                fields_updated=len(updates),
            )
        return entity_id

    def _create_new(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> UUID:
        updates = self._build_updates(mapa_global, fields_to_persist)
        persona = BuyerPersona(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=tenant_id,  # best-effort — interview may not have user context
            name=updates.pop("name", "Buyer Persona"),
            **updates,
        )
        created = self.repo.create(persona)
        logger.info(
            "buyer_persona_persister_created",
            tenant_id=str(tenant_id),
            entity_id=str(created.id),
        )
        return created.id

    @staticmethod
    def _build_updates(
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> dict:
        """Convert flat field paths to a dict suitable for repo.update().

        Dot-notation paths (e.g. ``demographics.age_range``) are merged
        into their parent dict. Direct fields (e.g. ``pain_points``) passed through.
        """
        updates: dict = {}

        for field_path in fields_to_persist:
            if field_path not in mapa_global:
                continue

            value = mapa_global[field_path]

            if "." in field_path:
                parent, key = field_path.split(".", 1)
                if parent in _DICT_FIELDS:
                    if parent not in updates:
                        updates[parent] = {}
                    updates[parent][key] = value
            else:
                # Validate type before storing to prevent corrupt rows.
                # AI sometimes returns a plain string for list/dict fields.
                if field_path in _LIST_FIELDS:
                    if not isinstance(value, list):
                        logger.warning(
                            "buyer_persona_persister.invalid_list_field_skipped",
                            field=field_path,
                            value_type=type(value).__name__,
                        )
                        continue
                elif field_path in _DICT_FIELDS and not isinstance(value, dict):
                    logger.warning(
                        "buyer_persona_persister.invalid_dict_field_skipped",
                        field=field_path,
                        value_type=type(value).__name__,
                    )
                    continue
                updates[field_path] = value

        return updates
