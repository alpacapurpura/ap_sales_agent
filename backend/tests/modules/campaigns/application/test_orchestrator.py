"""Unit tests for CampaignOrchestrator.launch().

TDD-mandatory RED → GREEN. Uses unittest.mock (no DB).
Tests: happy path, segment empty, atomic rollback, tenant isolation.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.modules.campaigns.application.services.orchestrator import (
    CampaignOrchestrator,
    OrchestratorCampaignNotFoundError,
    OrchestratorCampaignNotLaunchableError,
    OrchestratorMissingStepsError,
    OrchestratorSegmentEmptyError,
)
from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.campaign_step import CampaignStep
from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType, StepType
from src.shared.domain.datetime_utils import utc_now

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
OTHER_TENANT_ID = uuid4()
NOW = utc_now()


# ── Factories ─────────────────────────────────────────────────────────────────


def _make_campaign(
    *,
    status: CampaignStatus = CampaignStatus.SCHEDULED,
    segment_id: UUID | None = None,
) -> Campaign:
    """Build minimal Campaign for tests."""
    needs_sched = status in {
        CampaignStatus.SCHEDULED,
        CampaignStatus.RUNNING,
        CampaignStatus.PAUSED,
        CampaignStatus.COMPLETED,
        CampaignStatus.CANCELED,
    }
    needs_launched = status in {CampaignStatus.RUNNING, CampaignStatus.PAUSED}
    needs_completed = status in {CampaignStatus.COMPLETED, CampaignStatus.CANCELED}
    return Campaign(
        id=uuid4(),
        tenant_id=TENANT_ID,
        name="Test Campaign",
        campaign_type=CampaignType.AGENT_CONVERSATION,
        status=status,
        segment_id=segment_id,
        channel_priority=["telegram"],
        offer_id=uuid4() if status >= CampaignStatus.SCHEDULED else None,
        scheduled_at=NOW if needs_sched else None,
        launched_at=NOW if needs_launched else None,
        completed_at=NOW if needs_completed else None,
        created_at=NOW,
        updated_at=NOW,
    )


def _make_step(
    *,
    campaign_id: UUID,
    step_index: int = 0,
) -> CampaignStep:
    """Build a root step."""
    return CampaignStep(
        id=uuid4(),
        tenant_id=TENANT_ID,
        campaign_id=campaign_id,
        step_type=StepType.SEND_MESSAGE,
        step_index=step_index,
        step_config={"template_slug": "hello", "delay_minutes": 0},
        created_at=NOW,
        updated_at=NOW,
    )


def _make_orchestrator(**kwargs: Any) -> CampaignOrchestrator:
    """Build orchestrator with AsyncMock repos."""
    defaults: dict[str, Any] = {
        "campaign_repo": AsyncMock(),
        "step_repo": AsyncMock(),
        "task_repo": AsyncMock(),
        "segment_service": AsyncMock(),
        "outbox_service": AsyncMock(),
        "audit_log_service": AsyncMock(),
        "arq_pool_provider": AsyncMock(return_value=AsyncMock()),
        "execution_queue_name": "arq:campaigns_execution",
    }
    defaults.update(kwargs)
    return CampaignOrchestrator(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestOrchestratorLaunchHappyPath:
    """Happy path: campaign + segment + leads → tasks created + events emitted + audit rows."""

    async def test_launch_creates_root_tasks(self) -> None:
        """Happy path: 2 leads x 1 root step = 2 tasks created."""
        campaign_id = uuid4()
        segment_id = uuid4()
        lead_1 = uuid4()
        lead_2 = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([lead_1, lead_2], 2, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        result = await orch.launch(
            tenant_id=TENANT_ID,
            campaign_id=campaign_id,
            session=session,
        )

        assert result.tasks_generated == 2
        assert result.status == "running"
        assert str(result.external_id) == "2"
        assert result.id == campaign_id

        # Verify task batch was inserted
        orch._task_repo.append_many.assert_called_once()
        tasks_arg = orch._task_repo.append_many.call_args[0][0]
        assert len(tasks_arg) == 2
        for t in tasks_arg:
            assert t.tenant_id == TENANT_ID
            assert t.campaign_id == campaign_id
            assert t.step_id == step.id

    async def test_launch_emits_two_outbox_events(self) -> None:
        """CampaignLaunched + CampaignTasksGenerated events emitted."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        await orch.launch(tenant_id=TENANT_ID, campaign_id=campaign_id, session=session)

        # Exactly 2 outbox events: CampaignLaunched + CampaignTasksGenerated
        assert orch._outbox_service.enqueue_async_from_sync_caller.call_count == 2

    async def test_launch_writes_two_audit_rows(self) -> None:
        """campaign_launched + tasks_generated audit rows written."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        await orch.launch(tenant_id=TENANT_ID, campaign_id=campaign_id, session=session)

        # campaign_launched + tasks_generated
        assert orch._audit_log_service.record.call_count == 2
        event_types = [call.kwargs["event_type"].value for call in orch._audit_log_service.record.call_args_list]
        assert "campaign_launched" in event_types
        assert "tasks_generated" in event_types

    async def test_launch_transitions_campaign_to_running(self) -> None:
        """Campaign status updated to RUNNING via repo.update."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        await orch.launch(tenant_id=TENANT_ID, campaign_id=campaign_id, session=session)

        orch._campaign_repo.update.assert_called_once()
        updated = orch._campaign_repo.update.call_args[0][0]
        assert updated.status == CampaignStatus.RUNNING


class TestOrchestratorLaunchSegmentEmpty:
    """Segment resolves to 0 leads → 0 tasks + audit tasks_generated(count=0)."""

    async def test_segment_empty_returns_zero_tasks(self) -> None:
        """Empty segment → tasks_generated=0, status=running (campaign still launches)."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        # Empty segment
        orch._segment_service.resolve = AsyncMock(return_value=([], 0, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        result = await orch.launch(
            tenant_id=TENANT_ID,
            campaign_id=campaign_id,
            session=session,
        )

        assert result.tasks_generated == 0
        assert result.status == "running"
        # append_many not called (no tasks)
        orch._task_repo.append_many.assert_not_called()
        # Audit still records tasks_generated(count=0)
        audit_calls = orch._audit_log_service.record.call_args_list
        tasks_generated_call = next(c for c in audit_calls if c.kwargs["event_type"].value == "tasks_generated")
        assert tasks_generated_call.kwargs["payload"]["tasks_generated"] == 0

    async def test_no_segment_id_returns_zero_tasks(self) -> None:
        """Campaign with no segment_id → tasks_generated=0 (segment-less)."""
        campaign_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=None)
        campaign = campaign.model_copy(update={"id": campaign_id})

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[])
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        result = await orch.launch(
            tenant_id=TENANT_ID,
            campaign_id=campaign_id,
            session=session,
        )

        assert result.tasks_generated == 0
        orch._segment_service.resolve.assert_not_called()


class TestOrchestratorLaunchRollback:
    """Atomic rollback if insert task fails."""

    async def test_append_many_raises_propagates(self) -> None:
        """If append_many raises, error propagates to caller (session.begin() rolls back)."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        # Force failure on task insert
        orch._task_repo.append_many = AsyncMock(side_effect=RuntimeError("DB insert failed"))
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        with pytest.raises(RuntimeError, match="DB insert failed"):
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

        # campaign.update should NOT have been called (rollback point)
        orch._campaign_repo.update.assert_not_called()


class TestOrchestratorTenantIsolation:
    """Cross-tenant campaign_id → NotFound."""

    async def test_cross_tenant_campaign_raises_not_found(self) -> None:
        """campaign_id belonging to another tenant → OrchestratorCampaignNotFoundError."""
        campaign_id = uuid4()

        orch = _make_orchestrator()
        # Simulate repo returns None (tenant_id filter excludes)
        orch._campaign_repo.get_by_id = AsyncMock(return_value=None)

        session = AsyncMock()
        with pytest.raises(OrchestratorCampaignNotFoundError):
            await orch.launch(
                tenant_id=OTHER_TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

    async def test_not_found_raises_orchestrator_error(self) -> None:
        """Non-existent campaign_id → OrchestratorCampaignNotFoundError."""
        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=None)

        session = AsyncMock()
        with pytest.raises(OrchestratorCampaignNotFoundError):
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=uuid4(),
                session=session,
            )

    async def test_soft_deleted_campaign_raises_not_found(self) -> None:
        """Soft-deleted campaign → OrchestratorCampaignNotFoundError."""
        campaign_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED)
        campaign = campaign.model_copy(update={"id": campaign_id, "deleted_at": NOW})

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)

        session = AsyncMock()
        with pytest.raises(OrchestratorCampaignNotFoundError):
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )


class TestOrchestratorInvalidState:
    """Campaign not in launchable state → 409."""

    @pytest.mark.parametrize(
        "status",
        [
            CampaignStatus.COMPLETED,
            CampaignStatus.CANCELED,
            CampaignStatus.PAUSED,
        ],
    )
    async def test_non_launchable_status_raises(self, status: CampaignStatus) -> None:
        """Non-launchable statuses → OrchestratorCampaignNotLaunchableError."""
        campaign_id = uuid4()
        campaign = _make_campaign(status=status)
        campaign = campaign.model_copy(update={"id": campaign_id})

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)

        session = AsyncMock()
        with pytest.raises(OrchestratorCampaignNotLaunchableError):
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

    async def test_already_running_returns_noop(self) -> None:
        """Already RUNNING campaign → returns noop without creating tasks."""
        campaign_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.RUNNING)
        campaign = campaign.model_copy(update={"id": campaign_id})

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        result = await orch.launch(
            tenant_id=TENANT_ID,
            campaign_id=campaign_id,
            session=session,
        )

        assert result.status == "noop_already_running"
        assert result.tasks_generated == 0
        orch._task_repo.append_many.assert_not_called()
        orch._campaign_repo.update.assert_not_called()


class TestOrchestratorMissingSteps:
    """Campaign has leads but no root steps → OrchestratorMissingStepsError."""

    async def test_leads_but_no_root_steps_raises(self) -> None:
        """Leads present but step_index==0 steps absent → MissingStepsError."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id)
        campaign = campaign.model_copy(update={"id": campaign_id})
        # Non-root step only
        non_root_step = _make_step(campaign_id=campaign_id, step_index=1)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[non_root_step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        session = AsyncMock()
        with pytest.raises(OrchestratorMissingStepsError):
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )
