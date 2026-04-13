"""Tests for BrandPersister and persister registry."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.persisters.brand_persister import BrandPersister
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)


class TestBrandPersister:
    def test_persist_partial_data(self):
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()
        mapa_global = {
            "story.origin_story": "Founded in 2019...",
            "story.mission": "Democratize sales...",
            "identity.brand_name": "Nicolify",
        }
        fields_to_persist = [
            "story.origin_story",
            "story.mission",
            "identity.brand_name",
        ]

        with patch.object(persister, "repo") as mock_repo:
            mock_settings = MagicMock()
            mock_settings.model_dump.return_value = {"identity": {}, "story": {}}
            mock_repo.get_settings.return_value = mock_settings

            with patch(
                "src.modules.brand.domain.aggregates.BrandSettings",
            ) as mock_brand:
                mock_brand.model_validate.return_value = mock_settings
                persister.persist(tenant_id, mapa_global, fields_to_persist)

            mock_repo.save_settings.assert_called_once()

    def test_persist_skips_missing_fields(self):
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()
        mapa_global = {"story.origin_story": "Test"}
        fields_to_persist = [
            "story.origin_story",
            "story.mission",
        ]  # mission not in mapa_global

        with patch.object(persister, "repo") as mock_repo:
            mock_settings = MagicMock()
            mock_settings.model_dump.return_value = {"story": {}}
            mock_repo.get_settings.return_value = mock_settings

            with patch(
                "src.modules.brand.domain.aggregates.BrandSettings",
            ) as mock_brand:
                mock_brand.model_validate.return_value = mock_settings
                persister.persist(tenant_id, mapa_global, fields_to_persist)

    def test_persist_returns_early_if_no_settings(self):
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_settings.return_value = None
            persister.persist(tenant_id, {"x": "y"}, ["x"])
            mock_repo.save_settings.assert_not_called()


class TestPersisterRegistry:
    def test_get_brand_persister(self):
        db = MagicMock()
        persister = get_persister("brand", db)
        assert isinstance(persister, BrandPersister)

    def test_unknown_domain_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="No persister"):
            get_persister("unknown_domain", db)
