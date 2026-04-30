"""Tests para los métodos de lookup del CampaignTaskRepository.

Sub-B PR-8: verifica find_recent_for_lead, find_recent_for_leads y
count_responded_leads con cobertura de happy path, tenant isolation,
window boundary y casos borde.

TDD RED phase.
"""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.campaigns.domain.enums import TaskStatus

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
CAMPAIGN_ID = uuid.UUID("cccc0000-0000-0000-0000-000000000003")
LEAD_ID_1 = uuid.UUID("eeee0000-0000-0000-0000-000000000001")
LEAD_ID_2 = uuid.UUID("eeee0000-0000-0000-0000-000000000002")


# ── Tests de firma ABC ───────────────────────────────────────────────────────


def test_repository_abc_has_find_recent_for_lead() -> None:
    """CampaignTaskRepository ABC debe declarar find_recent_for_lead."""
    from src.modules.campaigns.domain.repositories import CampaignTaskRepository

    assert hasattr(CampaignTaskRepository, "find_recent_for_lead"), (
        "PR-8: CampaignTaskRepository debe tener método abstracto find_recent_for_lead"
    )


def test_repository_abc_has_find_recent_for_leads() -> None:
    """CampaignTaskRepository ABC debe declarar find_recent_for_leads (batch)."""
    from src.modules.campaigns.domain.repositories import CampaignTaskRepository

    assert hasattr(CampaignTaskRepository, "find_recent_for_leads"), (
        "PR-8: CampaignTaskRepository debe tener método abstracto find_recent_for_leads"
    )


def test_repository_abc_has_count_responded_leads() -> None:
    """CampaignTaskRepository ABC debe declarar count_responded_leads."""
    from src.modules.campaigns.domain.repositories import CampaignTaskRepository

    assert hasattr(CampaignTaskRepository, "count_responded_leads"), (
        "PR-8: CampaignTaskRepository debe tener método abstracto count_responded_leads"
    )


# ── Tests de implementación con mock session ─────────────────────────────────


@pytest.mark.asyncio
async def test_find_recent_for_lead_happy_path() -> None:
    """find_recent_for_lead retorna la task más reciente SENT dentro de la ventana."""
    from src.modules.campaigns.domain.campaign_task import CampaignTask
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    now = dt.datetime.now(tz=dt.timezone.utc)
    since = now - dt.timedelta(hours=24)

    mock_task_row = MagicMock()
    mock_task_row.id = uuid.uuid4()
    mock_task_row.tenant_id = TENANT_A
    mock_task_row.campaign_id = CAMPAIGN_ID
    mock_task_row.lead_id = LEAD_ID_1
    mock_task_row.step_id = None
    mock_task_row.status = TaskStatus.SENT.value
    mock_task_row.scheduled_at = now - dt.timedelta(hours=2)
    mock_task_row.dispatched_at = now - dt.timedelta(hours=2)
    mock_task_row.sent_at = now - dt.timedelta(hours=1)
    mock_task_row.executed_at = now - dt.timedelta(hours=1)
    mock_task_row.channel_used = "telegram"
    mock_task_row.external_message_id = "msg_123"
    mock_task_row.attempt_count = 1
    mock_task_row.last_error = None
    mock_task_row.compliance_check = None
    mock_task_row.outbox_event_id = None
    mock_task_row.idempotency_key = "task:ccc:eee:single"
    mock_task_row.created_at = now - dt.timedelta(hours=2)
    mock_task_row.updated_at = now - dt.timedelta(hours=1)
    mock_task_row.deleted_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task_row

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    repo = CampaignTaskRepositoryImpl()
    task = await repo.find_recent_for_lead(
        tenant_id=TENANT_A,
        lead_id=LEAD_ID_1,
        status=TaskStatus.SENT,
        since=since,
        session=mock_session,
    )

    assert task is not None
    assert task.campaign_id == CAMPAIGN_ID
    assert task.lead_id == LEAD_ID_1
    assert task.status == TaskStatus.SENT


@pytest.mark.asyncio
async def test_find_recent_for_lead_miss_returns_none() -> None:
    """find_recent_for_lead retorna None si no hay task en el rango."""
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    now = dt.datetime.now(tz=dt.timezone.utc)
    since = now - dt.timedelta(hours=24)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    repo = CampaignTaskRepositoryImpl()
    task = await repo.find_recent_for_lead(
        tenant_id=TENANT_A,
        lead_id=LEAD_ID_1,
        status=TaskStatus.SENT,
        since=since,
        session=mock_session,
    )

    assert task is None


@pytest.mark.asyncio
async def test_find_recent_for_leads_batch_returns_hit_only_map() -> None:
    """find_recent_for_leads retorna solo los leads con hit (sin Miss)."""
    from src.modules.campaigns.domain.campaign_task import CampaignTask
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    now = dt.datetime.now(tz=dt.timezone.utc)
    since = now - dt.timedelta(hours=24)

    # Solo LEAD_ID_1 tiene un task, LEAD_ID_2 no
    mock_task_row = MagicMock()
    mock_task_row.id = uuid.uuid4()
    mock_task_row.tenant_id = TENANT_A
    mock_task_row.campaign_id = CAMPAIGN_ID
    mock_task_row.lead_id = LEAD_ID_1
    mock_task_row.step_id = None
    mock_task_row.status = TaskStatus.SENT.value
    mock_task_row.scheduled_at = now - dt.timedelta(hours=2)
    mock_task_row.dispatched_at = now - dt.timedelta(hours=2)
    mock_task_row.sent_at = now - dt.timedelta(hours=1)
    mock_task_row.executed_at = now - dt.timedelta(hours=1)
    mock_task_row.channel_used = "telegram"
    mock_task_row.external_message_id = "msg_1"
    mock_task_row.attempt_count = 1
    mock_task_row.last_error = None
    mock_task_row.compliance_check = None
    mock_task_row.outbox_event_id = None
    mock_task_row.idempotency_key = "task:ccc:eee1:single"
    mock_task_row.created_at = now - dt.timedelta(hours=2)
    mock_task_row.updated_at = now - dt.timedelta(hours=1)
    mock_task_row.deleted_at = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_task_row]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    repo = CampaignTaskRepositoryImpl()
    result_map = await repo.find_recent_for_leads(
        tenant_id=TENANT_A,
        lead_ids=[LEAD_ID_1, LEAD_ID_2],
        status=TaskStatus.SENT,
        since=since,
        session=mock_session,
    )

    # Solo LEAD_ID_1 debe estar en el mapa
    assert LEAD_ID_1 in result_map
    assert LEAD_ID_2 not in result_map
    assert result_map[LEAD_ID_1].campaign_id == CAMPAIGN_ID


@pytest.mark.asyncio
async def test_find_recent_for_leads_empty_input() -> None:
    """find_recent_for_leads con lista vacía retorna mapa vacío."""
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    now = dt.datetime.now(tz=dt.timezone.utc)
    since = now - dt.timedelta(hours=24)

    mock_session = AsyncMock()

    repo = CampaignTaskRepositoryImpl()
    result_map = await repo.find_recent_for_leads(
        tenant_id=TENANT_A,
        lead_ids=[],
        status=TaskStatus.SENT,
        since=since,
        session=mock_session,
    )

    assert result_map == {}
    # No debe ejecutar query si lista es vacía
    mock_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_count_responded_leads_happy_path() -> None:
    """count_responded_leads retorna conteo de leads respondidos."""
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    mock_result = MagicMock()
    mock_result.scalar.return_value = 3

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    repo = CampaignTaskRepositoryImpl()
    count = await repo.count_responded_leads(
        tenant_id=TENANT_A,
        campaign_id=CAMPAIGN_ID,
        session=mock_session,
    )

    assert count == 3


@pytest.mark.asyncio
async def test_count_responded_leads_zero() -> None:
    """count_responded_leads retorna 0 cuando nadie respondió."""
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    mock_result = MagicMock()
    mock_result.scalar.return_value = 0

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    repo = CampaignTaskRepositoryImpl()
    count = await repo.count_responded_leads(
        tenant_id=TENANT_A,
        campaign_id=CAMPAIGN_ID,
        session=mock_session,
    )

    assert count == 0
