"""Unit tests for CampaignService — CRUD + FSM + plan enforcement.

TDD-mandatory RED → GREEN. Uses unittest.mock (no DB needed).
Tests: create (happy path, plan limit, duplicate), get/list/update/delete,
FSM transitions (schedule/launch/pause/resume/complete/cancel), step CRUD.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.modules.campaigns.application.dtos.campaign_dtos import (
    CampaignCreate,
    CampaignUpdate,
)
from src.modules.campaigns.application.dtos.campaign_step_dtos import (
    CampaignStepCreate,
    CampaignStepUpdate,
)
from src.modules.campaigns.application.services.cache import SimpleTTLCache
from src.modules.campaigns.application.services.campaign_service import (
    CampaignDuplicateNameError,
    CampaignInvalidTransitionError,
    CampaignNotEditableError,
    CampaignNotFoundError,
    CampaignPlanLimitExceededError,
    CampaignService,
    CampaignServiceError,
)
from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.campaign_step import CampaignStep
from src.modules.campaigns.domain.enums import (
    CampaignStatus,
    CampaignType,
    StepType,
)
from src.shared.domain.datetime_utils import utc_now

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
NOW = utc_now()


# ── Helpers ────────────────────────────────────────────────────────────────────


_SCHED_TS = NOW  # reuse NOW as a valid UTC timestamp for scheduling
_TERMINAL_STATUSES = {CampaignStatus.COMPLETED, CampaignStatus.CANCELED}
_RUNNING_OR_LATER = {
    CampaignStatus.SCHEDULED,
    CampaignStatus.RUNNING,
    CampaignStatus.PAUSED,
    CampaignStatus.COMPLETED,
    CampaignStatus.CANCELED,
}


def _make_campaign(
    *,
    status: CampaignStatus = CampaignStatus.DRAFT,
    campaign_type: CampaignType = CampaignType.AGENT_CONVERSATION,
    segment_id: UUID | None = None,
    offer_id: UUID | None = None,
) -> Campaign:
    """Build a minimal Campaign for tests.

    Automatically supplies status-dependent timestamps so the model_validator passes.
    For AGENT_CONVERSATION campaigns at >= SCHEDULED, uses a synthetic offer_id unless
    overridden so the offer_id invariant is satisfied.
    """
    _needs_sched = status in _RUNNING_OR_LATER
    _needs_launched = status in (CampaignStatus.RUNNING, CampaignStatus.PAUSED)
    _needs_completed = status in _TERMINAL_STATUSES
    # AGENT_CONVERSATION requires offer_id from SCHEDULED onward
    _effective_offer_id = offer_id
    if campaign_type == CampaignType.AGENT_CONVERSATION and status in _RUNNING_OR_LATER and offer_id is None:
        _effective_offer_id = uuid4()
    return Campaign(
        id=uuid4(),
        tenant_id=TENANT_ID,
        name="Test Campaign",
        description=None,
        campaign_type=campaign_type,
        status=status,
        segment_id=segment_id,
        segment_snapshot_id=None,
        channel_priority=[],
        offer_id=_effective_offer_id,
        brand_summary_id=None,
        config={},
        scheduled_at=_SCHED_TS if _needs_sched else None,
        launched_at=_SCHED_TS if _needs_launched else None,
        completed_at=_SCHED_TS if _needs_completed else None,
        created_by_user_id=None,
        created_by_source="api",
        created_at=NOW,
        updated_at=NOW,
        deleted_at=None,
    )


def _make_step(campaign_id: UUID) -> CampaignStep:
    return CampaignStep(
        id=uuid4(),
        tenant_id=TENANT_ID,
        campaign_id=campaign_id,
        step_type=StepType.SEND_MESSAGE,
        step_index=0,
        label="Step 0",
        next_step_ids=[],
        step_config={},
        created_at=NOW,
        updated_at=NOW,
        deleted_at=None,
    )


def _plan_config(max_active: int | None = None) -> MagicMock:
    plan = MagicMock()
    plan.plan_id = "free"
    plan.max_campaigns_active = max_active
    return plan


def _make_service(
    *,
    campaign: Campaign | None = None,
    count_active: int = 0,
    plan_max_active: int | None = None,
) -> tuple[CampaignService, AsyncMock, AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    repo = AsyncMock()
    step_repo = AsyncMock()
    segment_repo = AsyncMock()
    plan_service = AsyncMock()
    outbox_service = AsyncMock()
    cache = SimpleTTLCache()

    repo.get_by_id = AsyncMock(return_value=campaign)
    repo.count_active = AsyncMock(return_value=count_active)
    repo.count_by_tenant = AsyncMock(return_value=0)
    repo.list_by_tenant = AsyncMock(return_value=[])
    repo.append = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()

    step_repo.append = AsyncMock()
    step_repo.update = AsyncMock()
    step_repo.get_by_id = AsyncMock(return_value=None)
    step_repo.soft_delete = AsyncMock()

    segment_repo.get_by_id = AsyncMock(return_value=MagicMock())

    plan_service.get_effective = AsyncMock(return_value=_plan_config(plan_max_active))
    outbox_service.enqueue_async_from_sync_caller = AsyncMock()

    svc = CampaignService(
        repo=repo,
        step_repo=step_repo,
        segment_repo=segment_repo,
        plan_service=plan_service,
        outbox_service=outbox_service,
        cache=cache,
    )
    return svc, repo, step_repo, segment_repo, plan_service, outbox_service


# ── Create ─────────────────────────────────────────────────────────────────────


class TestCampaignServiceCreate:
    async def test_create_happy_path(self) -> None:
        svc, repo, *_ = _make_service()
        session = AsyncMock()

        dto = CampaignCreate(name="Camp A", campaign_type=CampaignType.AGENT_CONVERSATION)
        result = await svc.create(TENANT_ID, dto, session=session)

        assert result.name == "Camp A"
        assert result.status == CampaignStatus.DRAFT
        assert result.tenant_id == TENANT_ID
        repo.append.assert_called_once()

    async def test_create_respects_plan_limit(self) -> None:
        svc, *_ = _make_service(count_active=5, plan_max_active=5)
        session = AsyncMock()

        dto = CampaignCreate(name="Camp B", campaign_type=CampaignType.AGENT_CONVERSATION)
        with pytest.raises(CampaignPlanLimitExceededError):
            await svc.create(TENANT_ID, dto, session=session)

    async def test_create_no_limit_when_max_active_none(self) -> None:
        svc, repo, *_ = _make_service(count_active=100, plan_max_active=None)
        session = AsyncMock()

        dto = CampaignCreate(name="Camp C", campaign_type=CampaignType.AGENT_CONVERSATION)
        result = await svc.create(TENANT_ID, dto, session=session)
        assert result.status == CampaignStatus.DRAFT

    async def test_create_duplicate_name_raises_409(self) -> None:
        svc, repo, *_ = _make_service()
        session = AsyncMock()
        repo.append.side_effect = Exception("uq_campaign_tenant_name unique constraint")

        dto = CampaignCreate(name="Camp Dup", campaign_type=CampaignType.AGENT_CONVERSATION)
        with pytest.raises(CampaignDuplicateNameError):
            await svc.create(TENANT_ID, dto, session=session)

    async def test_create_emits_created_event(self) -> None:
        svc, repo, step_repo, segment_repo, plan_service, outbox_service = _make_service()
        session = AsyncMock()

        dto = CampaignCreate(name="Camp Event", campaign_type=CampaignType.AGENT_CONVERSATION)
        await svc.create(TENANT_ID, dto, session=session)
        outbox_service.enqueue_async_from_sync_caller.assert_called_once()


# ── Get / List / Update / Delete ───────────────────────────────────────────────


class TestCampaignServiceRead:
    async def test_get_not_found_raises(self) -> None:
        svc, repo, *_ = _make_service(campaign=None)
        session = AsyncMock()

        with pytest.raises(CampaignNotFoundError):
            await svc.get(TENANT_ID, uuid4(), session=session)

    async def test_get_found_returns_campaign(self) -> None:
        c = _make_campaign()
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.get(TENANT_ID, c.id, session=session)
        assert result.id == c.id

    async def test_list_returns_paginated(self) -> None:
        c1 = _make_campaign()
        svc, repo, *_ = _make_service()
        repo.list_by_tenant = AsyncMock(return_value=[c1])
        repo.count_by_tenant = AsyncMock(return_value=1)
        session = AsyncMock()

        result = await svc.list(TENANT_ID, session=session, limit=20, offset=0)
        assert result.total_count == 1
        assert len(result.items) == 1

    async def test_update_not_draft_raises(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        dto = CampaignUpdate(name="New Name")
        with pytest.raises(CampaignNotEditableError):
            await svc.update(TENANT_ID, c.id, dto, session=session)

    async def test_update_draft_ok(self) -> None:
        c = _make_campaign()
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        dto = CampaignUpdate(name="Updated Name")
        result = await svc.update(TENANT_ID, c.id, dto, session=session)
        assert result.name == "Updated Name"

    async def test_delete_running_emits_canceled(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, step_repo, segment_repo, plan_service, outbox_service = _make_service(campaign=c)
        session = AsyncMock()

        await svc.delete(TENANT_ID, c.id, session=session)
        outbox_service.enqueue_async_from_sync_caller.assert_called_once()
        repo.soft_delete.assert_called_once()


# ── FSM transitions ────────────────────────────────────────────────────────────


class TestCampaignServiceFSM:
    """FSM tests NEVER hardcode the transition dict — delegate to Campaign.transition_allowed."""

    async def test_schedule_draft_to_scheduled(self) -> None:
        seg_id = uuid4()
        offer = uuid4()
        c = _make_campaign(segment_id=seg_id, offer_id=offer)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        scheduled_for = utc_now().replace(tzinfo=dt.timezone.utc)
        result = await svc.schedule(TENANT_ID, c.id, scheduled_for, session=session)
        assert result.status == CampaignStatus.SCHEDULED

    async def test_schedule_without_segment_raises_invariant(self) -> None:
        c = _make_campaign(segment_id=None)
        svc, *_ = _make_service(campaign=c)
        session = AsyncMock()

        from src.modules.campaigns.application.services.campaign_service import (
            CampaignInvariantError,
        )

        scheduled_for = utc_now().replace(tzinfo=dt.timezone.utc)
        with pytest.raises(CampaignInvariantError, match="segment_id"):
            await svc.schedule(TENANT_ID, c.id, scheduled_for, session=session)

    async def test_schedule_agent_conversation_without_offer_raises(self) -> None:
        seg_id = uuid4()
        c = _make_campaign(campaign_type=CampaignType.AGENT_CONVERSATION, segment_id=seg_id, offer_id=None)
        svc, *_ = _make_service(campaign=c)
        session = AsyncMock()

        from src.modules.campaigns.application.services.campaign_service import (
            CampaignInvariantError,
        )

        scheduled_for = utc_now().replace(tzinfo=dt.timezone.utc)
        with pytest.raises(CampaignInvariantError, match="offer_id"):
            await svc.schedule(TENANT_ID, c.id, scheduled_for, session=session)

    async def test_launch_stub_scheduled_to_running(self) -> None:
        c = _make_campaign(status=CampaignStatus.SCHEDULED)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.launch(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.RUNNING

    async def test_launch_idempotent_when_already_running(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.launch(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.RUNNING
        repo.update.assert_not_called()

    async def test_pause_running_to_paused(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.pause(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.PAUSED

    async def test_pause_idempotent_when_already_paused(self) -> None:
        c = _make_campaign(status=CampaignStatus.PAUSED)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.pause(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.PAUSED
        repo.update.assert_not_called()

    async def test_resume_paused_to_running(self) -> None:
        c = _make_campaign(status=CampaignStatus.PAUSED)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.resume(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.RUNNING

    async def test_complete_running_to_completed(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.complete(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.COMPLETED

    async def test_cancel_any_to_canceled(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.cancel(TENANT_ID, c.id, session=session, reason="test")
        assert result.status == CampaignStatus.CANCELED

    async def test_cancel_idempotent_when_already_canceled(self) -> None:
        c = _make_campaign(status=CampaignStatus.CANCELED)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        result = await svc.cancel(TENANT_ID, c.id, session=session)
        assert result.status == CampaignStatus.CANCELED
        repo.update.assert_not_called()

    async def test_invalid_transition_raises(self) -> None:
        """DRAFT → COMPLETED is not allowed per FSM matrix."""
        c = _make_campaign(status=CampaignStatus.DRAFT)
        svc, repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        with pytest.raises(CampaignInvalidTransitionError):
            await svc.complete(TENANT_ID, c.id, session=session)

    async def test_fsm_delegate_to_campaign_domain(self) -> None:
        """Arch test property: service uses Campaign.transition_allowed — never its own dict."""
        import inspect

        src = inspect.getsource(CampaignService._enforce_transition)
        # The dict "TRANSITIONS" or similar must NOT appear directly in _enforce_transition
        assert "Campaign.transition_allowed" in src


# ── Step CRUD ─────────────────────────────────────────────────────────────────


class TestCampaignServiceSteps:
    async def test_add_step_to_draft_campaign(self) -> None:
        c = _make_campaign()
        svc, repo, step_repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        dto = CampaignStepCreate(step_type=StepType.SEND_MESSAGE, step_index=0)
        step = await svc.add_step(TENANT_ID, c.id, dto, session=session)
        assert step.step_type == StepType.SEND_MESSAGE
        step_repo.append.assert_called_once()

    async def test_add_step_non_draft_raises(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, step_repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        dto = CampaignStepCreate(step_type=StepType.SEND_MESSAGE, step_index=0)
        with pytest.raises(CampaignNotEditableError):
            await svc.add_step(TENANT_ID, c.id, dto, session=session)

    async def test_update_step_not_found_raises(self) -> None:
        c = _make_campaign()
        svc, repo, step_repo, *_ = _make_service(campaign=c)
        step_repo.get_by_id = AsyncMock(return_value=None)
        session = AsyncMock()

        dto = CampaignStepUpdate(label="New label")
        with pytest.raises(CampaignNotFoundError):
            await svc.update_step(TENANT_ID, c.id, uuid4(), dto, session=session)

    async def test_delete_step_non_draft_raises(self) -> None:
        c = _make_campaign(status=CampaignStatus.RUNNING)
        svc, repo, step_repo, *_ = _make_service(campaign=c)
        session = AsyncMock()

        with pytest.raises(CampaignNotEditableError):
            await svc.delete_step(TENANT_ID, c.id, uuid4(), session=session)
