"""Tests for AuditLogService.

TDD RED → GREEN: sanitize + persist pattern.
Verifies best-effort behavior (no raise on DB error).

PR-5 PI-1 S2.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.campaigns.application.services.audit_log_service import AuditLogService
from src.modules.campaigns.domain.audit_log import AuditEventType


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.append = AsyncMock()
    return repo


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock()


@pytest.mark.asyncio
async def test_record_inserts_audit_row(mock_repo, mock_session) -> None:
    """record() calls repo.append with AuditLogEvent."""
    svc = AuditLogService(repo=mock_repo)
    tenant_id = uuid4()
    campaign_id = uuid4()

    await svc.record(
        tenant_id=tenant_id,
        event_type=AuditEventType.CAMPAIGN_LAUNCHED,
        actor="orchestrator",
        campaign_id=campaign_id,
        payload={"tasks_generated": 5},
        session=mock_session,
    )

    mock_repo.append.assert_called_once()
    call_args = mock_repo.append.call_args
    evt = call_args.args[0]
    assert evt.tenant_id == tenant_id
    assert evt.campaign_id == campaign_id
    assert evt.event_type == AuditEventType.CAMPAIGN_LAUNCHED
    assert evt.actor == "orchestrator"


@pytest.mark.asyncio
async def test_record_propagates_tenant_id(mock_repo, mock_session) -> None:
    """tenant_id from call is stored in event."""
    svc = AuditLogService(repo=mock_repo)
    tenant_id = uuid4()

    await svc.record(
        tenant_id=tenant_id,
        event_type=AuditEventType.TASK_SENT,
        actor="execution_worker",
        session=mock_session,
    )

    call_args = mock_repo.append.call_args
    evt = call_args.args[0]
    assert evt.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_record_does_not_raise_on_repo_error(mock_session) -> None:
    """Best-effort: repo.append raises → service swallows, returns None."""
    mock_repo = AsyncMock()
    mock_repo.append.side_effect = RuntimeError("DB down")

    svc = AuditLogService(repo=mock_repo)

    # Must not raise
    await svc.record(
        tenant_id=uuid4(),
        event_type=AuditEventType.TASK_FAILED,
        actor="execution_worker",
        session=mock_session,
    )


@pytest.mark.asyncio
async def test_record_sanitizes_pii_in_payload(mock_repo, mock_session) -> None:
    """record() redacts PII via sanitize_payload before persisting."""
    svc = AuditLogService(repo=mock_repo)

    await svc.record(
        tenant_id=uuid4(),
        event_type=AuditEventType.COMPLIANCE_BLOCKED,
        actor="execution_worker",
        payload={"contact": "lead@test.com", "reason": "opt_out"},
        session=mock_session,
    )

    call_args = mock_repo.append.call_args
    evt = call_args.args[0]
    # Email should be redacted
    contact_val = evt.payload.get("contact", "")
    assert "lead@test.com" not in contact_val


@pytest.mark.asyncio
async def test_record_with_none_payload_uses_empty_dict(mock_repo, mock_session) -> None:
    """record() with payload=None uses empty dict default."""
    svc = AuditLogService(repo=mock_repo)

    await svc.record(
        tenant_id=uuid4(),
        event_type=AuditEventType.CIRCUIT_OPENED,
        actor="system",
        payload=None,
        session=mock_session,
    )

    call_args = mock_repo.append.call_args
    evt = call_args.args[0]
    assert isinstance(evt.payload, dict)
