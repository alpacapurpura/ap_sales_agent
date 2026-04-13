"""Persists interview mapa_global data into BrandSettings."""

from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)


class BrandPersister:
    """Writes confirmed interview data to BrandSettings (Tenant.config_json).

    All data lives in a single JSONB column (Tenant.config_json['brand_settings']).
    There are no ORM relationships — every load_existing / persist call is
    bounded to exactly one DB query (get_settings or save_settings).
    """

    def __init__(self, db: Session) -> None:
        """Initialize brand persister."""
        self.db = db
        self.repo = BrandRepository(db)

    def persist(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> None:
        """Persist specific fields from mapa_global to BrandSettings.

        Args:
            tenant_id: The tenant.
            mapa_global: Full mapa_global dict (flat keys with dot notation).
            fields_to_persist: Which field_paths to actually persist.

        """
        settings = self.repo.get_settings(tenant_id)
        if not settings:
            return

        current = settings.model_dump(mode="json")

        for field_path in fields_to_persist:
            if field_path not in mapa_global:
                continue
            value = mapa_global[field_path]
            parts = field_path.split(".")
            if len(parts) == 2:
                section, key = parts
                if section not in current or current[section] is None:
                    current[section] = {}
                current[section][key] = value

        updated_settings = BrandSettings.model_validate(current)
        self.repo.save_settings(tenant_id, updated_settings)

    def load_existing(self, tenant_id: UUID) -> dict:
        """Load existing BrandSettings as a flat dot-notation dict for mapa_global.

        All brand data lives in a single JSONB column — this method issues exactly
        one DB query (get_settings), then flattens the nested BrandSettings model
        to dot-notation keys (e.g. ``"identity.brand_name"``) compatible with the
        interview engine's mapa_global format.

        Args:
            tenant_id: The tenant UUID.

        Returns:
            Flat dict with dot-notation keys for all non-None scalar fields,
            or empty dict if no settings exist yet.

        """
        settings = self.repo.get_settings(tenant_id)
        if not settings:
            return {}

        raw = settings.model_dump(mode="json")
        result: dict = {}

        for section, section_data in raw.items():
            if not isinstance(section_data, dict):
                continue
            for key, value in section_data.items():
                if value is None:
                    continue
                result[f"{section}.{key}"] = value

        return result
