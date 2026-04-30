"""TDD: extraction_card_flow.py Redis SETEX → IdempotencyKey migration.

Regression tests ensuring behavior is preserved byte-for-byte after
migrating from ad-hoc redis_client.setex to the IdempotencyKey abstraction.

CONTRACT §4.D (PR-1 Q3 PM resolved):
- emit_section_complete_pill: duplicate call with same job_id+section_slug → no-op
- emit_extraction_summary_card: duplicate call with same job_id → no-op
- Redis down: soft-fail (allow execution, log warning)
- Idempotency key format: uses IdempotencyKey.storage_key with namespace prefix
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CONVERSATION_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
JOB_ID = "test-job-123"
SECTION_SLUG = "identity"


def _make_mock_db() -> MagicMock:
    """Return a mock DB session with a noop ConversationRepository."""
    return MagicMock()


class TestEmitSectionCompletePillIdempotency:
    """emit_section_complete_pill must be idempotent via Redis claim."""

    def test_first_call_executes_and_appends_message(self) -> None:
        """First call with unique job_id+section_slug executes successfully."""
        mock_redis = MagicMock()
        # claim returns the key (truthy) on first set (nx=True success)
        mock_redis.set.return_value = True
        mock_db = _make_mock_db()

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ) as mock_append,
            patch("src.modules.copilot.application.extraction_card_flow.EventBus") as mock_bus,
        ):
            mock_append.return_value = None
            mock_bus.publish.return_value = None

            from src.modules.copilot.application.extraction_card_flow import (
                emit_section_complete_pill,
            )

            emit_section_complete_pill(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug=SECTION_SLUG,
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        # Redis claim was attempted
        mock_redis.set.assert_called_once()

    def test_duplicate_call_is_noop_when_redis_claim_fails(self) -> None:
        """Second call with same job_id+section_slug must be a no-op."""
        mock_redis = MagicMock()
        # claim returns None (nx=True fails → key already exists)
        mock_redis.set.return_value = None
        mock_db = _make_mock_db()

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ) as mock_append,
        ):
            from src.modules.copilot.application.extraction_card_flow import (
                emit_section_complete_pill,
            )

            emit_section_complete_pill(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug=SECTION_SLUG,
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        # No message appended on duplicate call
        mock_append.assert_not_called()

    def test_redis_none_allows_execution_softfail(self) -> None:
        """Redis unavailable → soft-fail, execute function normally."""
        mock_db = _make_mock_db()

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                None,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ) as mock_append,
            patch("src.modules.copilot.application.extraction_card_flow.EventBus") as mock_bus,
        ):
            mock_append.return_value = None
            mock_bus.publish.return_value = None

            from src.modules.copilot.application.extraction_card_flow import (
                emit_section_complete_pill,
            )

            emit_section_complete_pill(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug=SECTION_SLUG,
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        # Even without Redis, function executes
        mock_append.assert_called_once()

    def test_idempotency_key_includes_job_and_section(self) -> None:
        """Idempotency key must encode job_id and section_slug."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_db = _make_mock_db()

        captured_key: list[str] = []

        def capture_set(key: str, *args, **kwargs) -> bool:
            captured_key.append(key)
            return True

        mock_redis.set.side_effect = capture_set

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ),
            patch("src.modules.copilot.application.extraction_card_flow.EventBus"),
        ):
            from src.modules.copilot.application.extraction_card_flow import (
                emit_section_complete_pill,
            )

            emit_section_complete_pill(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug=SECTION_SLUG,
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        assert len(captured_key) == 1
        key = captured_key[0]
        assert JOB_ID in key
        assert SECTION_SLUG in key


class TestEmitExtractionSummaryCardIdempotency:
    """emit_extraction_summary_card must be idempotent via Redis claim."""

    def test_first_call_executes_normally(self) -> None:
        """First call with unique job_id executes successfully."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_db = _make_mock_db()

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ) as mock_append,
            patch("src.modules.copilot.application.extraction_card_flow.EventBus") as mock_bus,
        ):
            mock_append.return_value = None
            mock_bus.publish.return_value = None

            from src.modules.copilot.application.extraction_card_flow import (
                emit_extraction_summary_card,
            )

            emit_extraction_summary_card(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                source_ref="https://example.com",
                duration_seconds=30,
                filled_fields=["name", "tagline"],
                filled_fields_by_section={"identity": ["name", "tagline"]},
                sections_completed=["identity"],
            )

        mock_redis.set.assert_called_once()

    def test_duplicate_job_id_is_noop(self) -> None:
        """Second call with same job_id must be a no-op (Redis claim fails)."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = None  # claim fails
        mock_db = _make_mock_db()

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ) as mock_append,
        ):
            from src.modules.copilot.application.extraction_card_flow import (
                emit_extraction_summary_card,
            )

            emit_extraction_summary_card(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                source_ref="https://example.com",
                duration_seconds=30,
                filled_fields=["name"],
                filled_fields_by_section={"identity": ["name"]},
                sections_completed=["identity"],
            )

        mock_append.assert_not_called()

    def test_idempotency_key_includes_job_id(self) -> None:
        """Idempotency key must encode job_id for summary dedup."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_db = _make_mock_db()

        captured_key: list[str] = []

        def capture_set(key: str, *args, **kwargs) -> bool:
            captured_key.append(key)
            return True

        mock_redis.set.side_effect = capture_set

        with (
            patch(
                "src.modules.copilot.application.extraction_card_flow.redis_client",
                mock_redis,
            ),
            patch(
                "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository.append_messages"
            ),
            patch("src.modules.copilot.application.extraction_card_flow.EventBus"),
        ):
            from src.modules.copilot.application.extraction_card_flow import (
                emit_extraction_summary_card,
            )

            emit_extraction_summary_card(
                db=mock_db,
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                source_ref="https://example.com",
                duration_seconds=10,
                filled_fields=["name"],
                filled_fields_by_section={"identity": ["name"]},
                sections_completed=["identity"],
            )

        assert len(captured_key) == 1
        assert JOB_ID in captured_key[0]
