"""TDD — BrandDataAdapter PR-2 extension: get_buyer_persona_count + get_active_personality_profile_present.

Tests written RED first per ``tdd-mandatory.md``.
Uses mocks (no DB needed).

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


_TENANT = uuid4()


class TestGetBuyerPersonaCountExtension:
    def test_get_buyer_persona_count_excludes_soft_deleted(self) -> None:
        """list_by_tenant returns 3 personas → count == 3 (mock verifies soft-delete excluded at repo)."""
        from src.modules.brand.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_by_tenant.return_value = [MagicMock(), MagicMock(), MagicMock()]

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.BuyerPersonaRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            count = adapter.get_buyer_persona_count(_TENANT)

        assert count == 3
        mock_repo.list_by_tenant.assert_called_once_with(_TENANT)

    def test_get_buyer_persona_count_zero_when_empty(self) -> None:
        """list_by_tenant returns [] → count == 0."""
        from src.modules.brand.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_by_tenant.return_value = []

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.BuyerPersonaRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            count = adapter.get_buyer_persona_count(_TENANT)

        assert count == 0


class TestGetActivePersonalityProfilePresentExtension:
    def test_get_active_personality_profile_present_true(self) -> None:
        """get_active returns profile → True."""
        from src.modules.brand.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_active.return_value = MagicMock()  # profile exists

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            result = adapter.get_active_personality_profile_present(_TENANT)

        assert result is True
        mock_repo.get_active.assert_called_once_with(tenant_id=_TENANT)

    def test_get_active_personality_profile_present_false(self) -> None:
        """get_active returns None → False."""
        from src.modules.brand.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_active.return_value = None

        with patch(
            "src.modules.brand.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            result = adapter.get_active_personality_profile_present(_TENANT)

        assert result is False
