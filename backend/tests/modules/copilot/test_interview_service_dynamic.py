"""Tests for dynamic config selection in InterviewService.

Verifies that when start_interview is called with domain='offer' and
entity_id, the service loads the offer archetype from the DB and uses
get_offer_interview_config(archetype) instead of the static config.

Task 6: Interview service uses dynamic config for offer domain.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.services.interview_service import (
    InterviewService,
    _load_offer_archetype,
)
from src.modules.copilot.domain.interview_configs.offer_config import (
    ARCHETYPE_BLOCKS,
    OFFER_INTERVIEW_CONFIG,
)


class TestDynamicConfigSelection:
    """Test that start_interview selects config based on offer archetype."""

    def test_offer_domain_with_entity_id_uses_dynamic_config(self, db) -> None:
        """When domain='offer' and entity_id is given, dynamic config is used."""
        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()
        archetype = "programa"

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            # Patch _load_offer_archetype at the module level to return known archetype
            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
                return_value=archetype,
            ) as mock_load:
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="offer",
                    entity_id=entity_id,
                )

            # _load_offer_archetype must have been called with correct args
            mock_load.assert_called_once_with(db, tenant_id, entity_id)

            # Dynamic config for edition-supporting archetype "programa":
            # 3 universal_first + 1 archetype + 3 universal_final + 1 first_edition_date = 8
            config = result["config"]
            block_ids = [b["id"] for b in config["bloques"]]
            assert len(block_ids) == 8

            # The archetype-specific block for "programa" must be present at position 3
            assert block_ids[3] == "program_details"
            # Extra edition-date block appended at the end.
            assert block_ids[-1] == "first_edition_date"

    def test_offer_domain_without_entity_id_uses_static_config(self, db) -> None:
        """When domain='offer' with no entity_id, static config is used (fallback)."""
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
            ) as mock_load:
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="offer",
                    entity_id=None,
                )

            # _load_offer_archetype must NOT have been called (no entity_id)
            mock_load.assert_not_called()

            # Static config has 6 blocks
            config = result["config"]
            assert len(config["bloques"]) == 6

    def test_non_offer_domain_uses_static_config(self, db) -> None:
        """Non-offer domains always use get_interview_config(domain)."""
        tenant_id = uuid4()
        user_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
            ) as mock_load:
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="brand",
                )

            mock_load.assert_not_called()
            assert result["config"]["domain"] == "brand"

    def test_offer_domain_unknown_archetype_falls_back_to_static(self, db) -> None:
        """When archetype is unknown, dynamic factory falls back to static config."""
        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()
        unknown_archetype = "unknown_type"

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
                return_value=unknown_archetype,
            ):
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="offer",
                    entity_id=entity_id,
                )

            # Falls back to static config (6 blocks) when archetype unknown
            config = result["config"]
            assert len(config["bloques"]) == 6

    def test_offer_domain_none_archetype_falls_back_to_static(self, db) -> None:
        """When _load_offer_archetype returns None, static config is used."""
        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
                return_value=None,
            ):
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="offer",
                    entity_id=entity_id,
                )

            config = result["config"]
            assert len(config["bloques"]) == 6

    @pytest.mark.parametrize("archetype", list(ARCHETYPE_BLOCKS.keys()))
    def test_all_known_archetypes_produce_dynamic_block_config(
        self,
        db,
        archetype: str,
    ) -> None:
        """Every known archetype produces a dynamic config: 7 blocks, or 8 for
        edition-supporting archetypes (``programa``, ``servicio``, ``experiencia``).
        """
        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()

        with patch.object(InterviewService, "__init__", lambda self, db: None):
            svc = InterviewService.__new__(InterviewService)
            svc.db = db
            svc.conversation_repo = MagicMock()

            with patch(
                "src.modules.copilot.application.services.interview_service._load_offer_archetype",
                return_value=archetype,
            ):
                from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
                    InterviewSessionRepository,
                )

                svc.session_repo = InterviewSessionRepository(db)

                result = svc.start_interview(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    domain="offer",
                    entity_id=entity_id,
                )

            config = result["config"]
            expected = 8 if archetype in {"programa", "servicio", "experiencia"} else 7
            assert len(config["bloques"]) == expected, (
                f"Expected {expected} blocks for archetype '{archetype}', got {len(config['bloques'])}"
            )


class TestLoadOfferArchetype:
    """Unit tests for the _load_offer_archetype helper."""

    def test_returns_none_when_offer_not_found(self) -> None:
        """Returns None if no offer row matches tenant + entity_id."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = _load_offer_archetype(mock_db, uuid4(), uuid4())

        assert result is None

    def test_returns_archetype_string_when_found(self) -> None:
        """Returns archetype string from DB row."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "servicio"
        mock_db.execute.return_value = mock_result

        result = _load_offer_archetype(mock_db, uuid4(), uuid4())

        assert result == "servicio"
        mock_db.execute.assert_called_once()
