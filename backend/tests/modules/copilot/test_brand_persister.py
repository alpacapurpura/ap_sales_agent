"""Tests for BrandPersister and persister registry."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.brand.domain.aggregates import BrandSettings
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


class TestBrandPersisterLoadExisting:
    """Tests for BrandPersister.load_existing — focus mode read path."""

    def test_load_existing_returns_flat_dict(self):
        """load_existing returns brand settings as flat dot-notation dict."""
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()

        settings = BrandSettings.model_validate(
            {
                "identity": {"brand_name": "Nicolify", "tagline": "Automate sales"},
                "story": {"origin_story": "Started in 2020"},
            }
        )

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_settings.return_value = settings
            result = persister.load_existing(tenant_id)

        assert result["identity.brand_name"] == "Nicolify"
        assert result["identity.tagline"] == "Automate sales"
        assert result["story.origin_story"] == "Started in 2020"

    def test_load_existing_returns_empty_when_no_settings(self):
        """load_existing returns empty dict when no brand settings exist (all None sections)."""
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            # BrandSettings() with no data → all None sections
            mock_repo.get_settings.return_value = BrandSettings()
            result = persister.load_existing(tenant_id)

        assert isinstance(result, dict)
        # None-valued fields are stripped — no keys like "identity.brand_name"
        assert "identity.brand_name" not in result

    def test_load_existing_calls_repo_exactly_once(self):
        """load_existing must issue exactly 1 query (bounded, no N+1)."""
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_settings.return_value = BrandSettings()
            persister.load_existing(tenant_id)

        mock_repo.get_settings.assert_called_once_with(tenant_id)


class TestPersisterRegistry:
    def test_get_brand_persister(self):
        db = MagicMock()
        persister = get_persister("brand", db)
        assert isinstance(persister, BrandPersister)

    def test_unknown_domain_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="No persister"):
            get_persister("unknown_domain", db)
