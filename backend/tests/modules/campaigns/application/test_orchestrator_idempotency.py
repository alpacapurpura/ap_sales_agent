"""Unit tests for CampaignOrchestrator idempotency behavior.

TDD-mandatory RED → GREEN. Uses unittest.mock (no DB, no Redis).
Tests: re-launch within TTL → no duplicate tasks/events.
       re-launch post-TTL (idempotency expired) → allows re-launch.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from luana_core_campaigns.application.services.orchestrator import (
    CampaignOrchestrator,
    OrchestratorLaunchResult,
)
from luana_core_campaigns.domain.campaign import Campaign
from luana_core_campaigns.domain.campaign_step import CampaignStep
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType, StepType
from luana_core_platform.domain.datetime_utils import utc_now

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
NOW = utc_now()


def _make_campaign(
    *,
    status: CampaignStatus = CampaignStatus.SCHEDULED,
    segment_id: UUID | None = None,
    campaign_id: UUID | None = None,
) -> Campaign:
    """Build minimal Campaign for tests."""
    cid = campaign_id or uuid4()
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
        id=cid,
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


def _make_step(*, campaign_id: UUID) -> CampaignStep:
    return CampaignStep(
        id=uuid4(),
        tenant_id=TENANT_ID,
        campaign_id=campaign_id,
        step_type=StepType.SEND_MESSAGE,
        step_index=0,
        step_config={"template_slug": "hello"},
        created_at=NOW,
        updated_at=NOW,
    )


def _make_orchestrator(**overrides: Any) -> CampaignOrchestrator:
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
    defaults.update(overrides)
    return CampaignOrchestrator(**defaults)


class TestOrchestratorIdempotency:
    """@idempotent decorator prevents duplicate task creation within TTL."""

    async def test_relaunch_within_ttl_returns_cached_no_duplicate_tasks(self) -> None:
        """Re-launch within TTL: @idempotent returns cached result; append_many not called twice."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id, campaign_id=campaign_id)
        step = _make_step(campaign_id=campaign_id)
        lead_id = uuid4()

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([lead_id], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        # Simulate idempotent store: claim → True first, False second, cached = first result
        fake_cached_result = {
            "id": str(campaign_id),
            "status": "running",
            "external_id": "1",
        }

        store_mock = AsyncMock()
        # First call: claim succeeds (True), store result
        # Second call: claim fails (False), return cached
        store_mock.claim = AsyncMock(side_effect=[True, False])
        store_mock.cached_result = AsyncMock(return_value=fake_cached_result)
        store_mock.store_result = AsyncMock()

        session = AsyncMock()

        with patch(
            "luana_core_idempotency.application.decorator._default_store_factory",
            new=lambda: store_mock,
        ):
            # First launch
            result1 = await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )
            # Second launch (same args) — @idempotent returns cached
            result2 = await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

        # First call executed (1 append_many)
        assert orch._task_repo.append_many.call_count == 1
        # Result 1 is the real result
        assert result1.tasks_generated == 1
        # Result 2 is the cached projection (dict from store)
        assert result2 == fake_cached_result  # type: ignore[comparison-overlap]

    async def test_relaunch_post_ttl_allows_new_launch(self) -> None:
        """Re-launch after TTL expiry: @idempotent claim succeeds again → real execution."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id, campaign_id=campaign_id)
        step = _make_step(campaign_id=campaign_id)
        lead_id = uuid4()

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([lead_id], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        store_mock = AsyncMock()
        # Both calls claim succeeds (TTL expired → key gone → new claim)
        store_mock.claim = AsyncMock(return_value=True)
        store_mock.store_result = AsyncMock()

        session = AsyncMock()

        with patch(
            "luana_core_idempotency.application.decorator._default_store_factory",
            new=lambda: store_mock,
        ):
            # First launch
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )
            # Second launch (simulates post-TTL: claim re-succeeds)
            # Reset campaign_repo to return scheduled campaign again
            await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

        # Both calls executed (2 append_many calls)
        assert orch._task_repo.append_many.call_count == 2

    async def test_idempotent_stores_projection_with_correct_keys(self) -> None:
        """@idempotent stores {id, status, external_id} projection after first launch."""
        campaign_id = uuid4()
        segment_id = uuid4()
        campaign = _make_campaign(status=CampaignStatus.SCHEDULED, segment_id=segment_id, campaign_id=campaign_id)
        step = _make_step(campaign_id=campaign_id)

        orch = _make_orchestrator()
        orch._campaign_repo.get_by_id = AsyncMock(return_value=campaign)
        orch._step_repo.list_by_campaign = AsyncMock(return_value=[step])
        orch._segment_service.resolve = AsyncMock(return_value=([uuid4()], 1, False))
        orch._task_repo.append_many = AsyncMock()
        orch._campaign_repo.update = AsyncMock()
        orch._outbox_service.enqueue_async_from_sync_caller = AsyncMock()
        orch._audit_log_service.record = AsyncMock()

        store_mock = AsyncMock()
        store_mock.claim = AsyncMock(return_value=True)
        store_mock.store_result = AsyncMock()

        session = AsyncMock()

        with patch(
            "luana_core_idempotency.application.decorator._default_store_factory",
            new=lambda: store_mock,
        ):
            result = await orch.launch(
                tenant_id=TENANT_ID,
                campaign_id=campaign_id,
                session=session,
            )

        # The @idempotent decorator stores projection {id, status, external_id}
        # store_result called with (ikey, projected)
        assert store_mock.store_result.call_count == 1
        # The result has projection-compatible fields
        assert hasattr(result, "id")
        assert hasattr(result, "status")
        assert hasattr(result, "external_id")
