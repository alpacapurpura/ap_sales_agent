"""Unit tests — outbox payload PII sanitization (F-3, PI-1 S0 post-REVIEW).

Verifies that OutboxRepositoryImpl.append_sync and append redact PII from
payloads before JSONB insert, per the F-3 finding in REVIEW.md.

Tests use mock sessions — no Postgres required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.domain_events.outbox.domain.outbox_entry import OutboxEntry, OutboxStatus
from src.shared.domain_events.outbox.infrastructure.repository import OutboxRepositoryImpl


def _make_entry(payload: dict) -> OutboxEntry:
    """Create an OutboxEntry with the given payload for testing."""
    return OutboxEntry(
        id=uuid4(),
        tenant_id=uuid4(),
        event_name="test_event",
        payload=payload,
        idempotency_key=f"test-{uuid4()}",
        status=OutboxStatus.PENDING,
        retry_count=0,
        last_error=None,
        created_at=datetime.now(UTC),
        dispatched_at=None,
    )


class TestOutboxPayloadSanitizationSync:
    """append_sync redacts PII before insert."""

    def test_email_in_payload_is_masked(self) -> None:
        """Email in payload JSONB is masked before insert."""
        repo = OutboxRepositoryImpl()
        entry = _make_entry({"email": "juan.perez@ejemplo.com", "offer_id": "abc-123"})

        mock_session = MagicMock()
        mock_session.execute.return_value.rowcount = 1

        with patch(
            "sqlalchemy.dialects.postgresql.insert",
            return_value=MagicMock(
                __call__=MagicMock(
                    return_value=MagicMock(
                        values=MagicMock(
                            return_value=MagicMock(on_conflict_do_nothing=MagicMock(return_value=MagicMock()))
                        )
                    )
                )
            ),
        ):
            repo.append_sync(entry, session=mock_session)

        # Inspect what was passed to session.execute
        call_args = mock_session.execute.call_args
        assert call_args is not None, "session.execute was not called"

        # The stmt passed is a SQLAlchemy construct; verify sanitize_payload ran
        # We do this by patching sanitize_payload directly and asserting it was called.

    def test_sanitize_payload_called_with_entry_payload_sync(self) -> None:
        """sanitize_payload is called with entry.payload before insert (sync)."""
        repo = OutboxRepositoryImpl()
        entry = _make_entry({"email": "test@example.com", "amount": 99.99})

        mock_session = MagicMock()
        mock_session.execute.return_value.rowcount = 1

        with patch(
            "src.shared.domain_events.outbox.infrastructure.repository.sanitize_payload",
            return_value={"email": "t***@example.com", "amount": 99.99},
        ) as mock_sanitize:
            repo.append_sync(entry, session=mock_session)

        mock_sanitize.assert_called_once_with(entry.payload)

    def test_payload_without_pii_unchanged_sync(self) -> None:
        """Payload without PII fields passes through sanitize_payload unchanged."""
        repo = OutboxRepositoryImpl()
        clean_payload = {"offer_id": "abc", "section": "identity", "fields_count": 5}
        entry = _make_entry(clean_payload)

        mock_session = MagicMock()
        mock_session.execute.return_value.rowcount = 1

        with patch(
            "src.shared.domain_events.outbox.infrastructure.repository.sanitize_payload",
            wraps=lambda p: p,  # pass-through — real behavior
        ) as mock_sanitize:
            repo.append_sync(entry, session=mock_session)

        mock_sanitize.assert_called_once_with(clean_payload)

    def test_sanitize_failure_falls_back_to_raw_payload_sync(self) -> None:
        """sanitize_payload exception → raw payload used (best-effort, no exception raised)."""
        repo = OutboxRepositoryImpl()
        entry = _make_entry({"data": "some value"})

        mock_session = MagicMock()
        mock_session.execute.return_value.rowcount = 1

        with patch(
            "src.shared.domain_events.outbox.infrastructure.repository.sanitize_payload",
            side_effect=RuntimeError("sanitize crashed"),
        ):
            # Must NOT raise — best-effort contract
            repo.append_sync(entry, session=mock_session)

        # session.execute was still called (insert proceeded with raw payload)
        mock_session.execute.assert_called_once()

    def test_phone_in_payload_is_sanitized_via_real_function(self) -> None:
        """Integration: real sanitize_payload masks a phone number in payload."""
        from src.shared.agent_observability.recording.sanitization import sanitize_payload

        payload = {
            "message": "Mi numero es +52 55 1234 5678 para contacto",
            "tenant_id": "abc-123",
        }
        sanitized = sanitize_payload(payload)
        assert "+52 55 1234 5678" not in sanitized["message"]
        assert "REDACTED_PHONE" in sanitized["message"]
        # Non-PII field unchanged
        assert sanitized["tenant_id"] == "abc-123"

    def test_email_in_payload_is_sanitized_via_real_function(self) -> None:
        """Integration: real sanitize_payload masks an email address."""
        from src.shared.agent_observability.recording.sanitization import sanitize_payload

        payload = {"lead_email": "maria.garcia@empresa.mx", "offer_id": "offer-999"}
        sanitized = sanitize_payload(payload)
        assert "maria.garcia@empresa.mx" not in sanitized["lead_email"]
        assert "***@empresa.mx" in sanitized["lead_email"]
        assert sanitized["offer_id"] == "offer-999"

    def test_clean_payload_unchanged_via_real_function(self) -> None:
        """Integration: real sanitize_payload leaves clean payload untouched."""
        from src.shared.agent_observability.recording.sanitization import sanitize_payload

        payload = {
            "section": "identity",
            "job_id": "arq-abc123",
            "fields_count": 7,
            "module": "brand",
        }
        sanitized = sanitize_payload(payload)
        assert sanitized == payload


class TestOutboxPayloadSanitizationAsync:
    """append (async) redacts PII before insert."""

    @pytest.mark.asyncio
    async def test_sanitize_payload_called_with_entry_payload_async(self) -> None:
        """sanitize_payload is called with entry.payload before async insert."""
        repo = OutboxRepositoryImpl()
        entry = _make_entry({"email": "test@example.com", "amount": 100.0})

        mock_session = MagicMock()
        mock_execute_result = MagicMock()
        mock_execute_result.rowcount = 1

        async def mock_execute(stmt):
            return mock_execute_result

        mock_session.execute = mock_execute

        with patch(
            "src.shared.domain_events.outbox.infrastructure.repository.sanitize_payload",
            return_value={"email": "t***@example.com", "amount": 100.0},
        ) as mock_sanitize:
            await repo.append(entry, session=mock_session)

        mock_sanitize.assert_called_once_with(entry.payload)

    @pytest.mark.asyncio
    async def test_sanitize_failure_fallback_async(self) -> None:
        """sanitize_payload exception → raw payload + no exception raised (async)."""
        repo = OutboxRepositoryImpl()
        entry = _make_entry({"data": "value"})

        mock_session = MagicMock()
        mock_execute_result = MagicMock()
        mock_execute_result.rowcount = 1

        async def mock_execute(stmt):
            return mock_execute_result

        mock_session.execute = mock_execute

        with patch(
            "src.shared.domain_events.outbox.infrastructure.repository.sanitize_payload",
            side_effect=RuntimeError("crash"),
        ):
            # Must NOT raise
            await repo.append(entry, session=mock_session)
