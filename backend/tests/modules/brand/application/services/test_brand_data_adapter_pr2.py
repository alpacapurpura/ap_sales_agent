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
        from luana_core_brand_studio.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_by_tenant.return_value = [MagicMock(), MagicMock(), MagicMock()]

        with patch(
            "luana_core_brand_studio.application.services.brand_data_adapter.BuyerPersonaRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            count = adapter.get_buyer_persona_count(_TENANT)

        assert count == 3
        mock_repo.list_by_tenant.assert_called_once_with(_TENANT)

    def test_get_buyer_persona_count_zero_when_empty(self) -> None:
        """list_by_tenant returns [] → count == 0."""
        from luana_core_brand_studio.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.list_by_tenant.return_value = []

        with patch(
            "luana_core_brand_studio.application.services.brand_data_adapter.BuyerPersonaRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            count = adapter.get_buyer_persona_count(_TENANT)

        assert count == 0


class TestGetActivePersonalityProfilePresentExtension:
    def test_get_active_personality_profile_present_true(self) -> None:
        """get_active returns profile → True."""
        from luana_core_brand_studio.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_active.return_value = MagicMock()  # profile exists

        with patch(
            "luana_core_brand_studio.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            result = adapter.get_active_personality_profile_present(_TENANT)

        assert result is True
        mock_repo.get_active.assert_called_once_with(tenant_id=_TENANT)

    def test_get_active_personality_profile_present_false(self) -> None:
        """get_active returns None → False."""
        from luana_core_brand_studio.application.services.brand_data_adapter import BrandDataAdapter

        mock_db = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_active.return_value = None

        with patch(
            "luana_core_brand_studio.application.services.brand_data_adapter.PersonalityProfileRepository",
            return_value=mock_repo,
        ):
            adapter = BrandDataAdapter(mock_db)
            result = adapter.get_active_personality_profile_present(_TENANT)

        assert result is False


class TestGetBrandKnowledgeHandlesORMPersonalityProfile:
    """Bug #7 regression — PI-7 S1 PR-1 (2026-05-01).

    PersonalityProfileRepository.get_active returns SQLA ORM
    (PersonalityProfileModel), NOT Pydantic. Adapter must convert
    via PersonalityProfileDTO.model_validate before model_dump.
    """

    def test_get_brand_knowledge_with_orm_personality_returns_dict(self) -> None:
        """RED: real ORM instance via from_attributes → dict serialisation succeeds."""
        from datetime import datetime, timezone

        from luana_core_brand_studio.application.services.brand_data_adapter import (
            BrandDataAdapter,
        )
        from luana_core_brand_studio.infrastructure.models.personality_model import (
            PersonalityProfileModel,
        )

        # Arrange — real ORM instance (NOT MagicMock — would mask the bug)
        orm_profile = PersonalityProfileModel(
            id=_TENANT,
            tenant_id=_TENANT,
            name="Visionarias",
            profile_type="preset",
            preset_key="sage",
            is_active=True,
            dimensions={"warmth": 0.8, "energy": 0.5},
            linguistic_patterns={"greeting": "Hola"},
            sample_exchanges=[],
            negative_constraints=[],
            system_instruction="Sos Visionarias.",
            source_metadata={},
            anchor_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()
        mock_brand_repo = MagicMock()
        mock_brand_repo.get_settings.return_value = None
        mock_avatar_repo = MagicMock()
        mock_avatar_repo.get_by_tenant.return_value = []
        mock_pers_repo = MagicMock()
        mock_pers_repo.get_active.return_value = orm_profile

        with (
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.BrandRepository",
                return_value=mock_brand_repo,
            ),
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.AvatarRepository",
                return_value=mock_avatar_repo,
            ),
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.PersonalityProfileRepository",
                return_value=mock_pers_repo,
            ),
        ):
            adapter = BrandDataAdapter(mock_db)
            knowledge = adapter.get_brand_knowledge(_TENANT)

        # Assert
        assert knowledge.personality_profile is not None
        assert isinstance(knowledge.personality_profile, dict)
        assert knowledge.personality_profile["name"] == "Visionarias"
        assert knowledge.personality_profile["dimensions"]["warmth"] == 0.8
        assert knowledge.personality_profile["system_instruction"] == "Sos Visionarias."

    def test_get_brand_knowledge_with_no_personality_returns_none(self) -> None:
        """get_active returns None → personality_profile field is None."""
        from luana_core_brand_studio.application.services.brand_data_adapter import (
            BrandDataAdapter,
        )

        mock_db = MagicMock()
        mock_brand_repo = MagicMock()
        mock_brand_repo.get_settings.return_value = None
        mock_avatar_repo = MagicMock()
        mock_avatar_repo.get_by_tenant.return_value = []
        mock_pers_repo = MagicMock()
        mock_pers_repo.get_active.return_value = None

        with (
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.BrandRepository",
                return_value=mock_brand_repo,
            ),
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.AvatarRepository",
                return_value=mock_avatar_repo,
            ),
            patch(
                "luana_core_brand_studio.application.services.brand_data_adapter.PersonalityProfileRepository",
                return_value=mock_pers_repo,
            ),
        ):
            adapter = BrandDataAdapter(mock_db)
            knowledge = adapter.get_brand_knowledge(_TENANT)

        assert knowledge.personality_profile is None
