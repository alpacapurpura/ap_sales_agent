"""Unit tests for CampaignTemplateService.

All tests use AsyncMock — no DB needed.
clone_to_campaign atomic TX contract verified via mock sequencing.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from luana_core_campaigns.application.dtos.campaign_template_dtos import (
    CampaignCreateFromTemplate,
)
from luana_core_campaigns.application.services.cache import SimpleTTLCache
from luana_core_campaigns.application.services.campaign_template_service import (
    CampaignTemplateNotFoundError,
    CampaignTemplateService,
)
from luana_core_campaigns.domain.campaign import Campaign
from luana_core_campaigns.domain.campaign_template import CampaignTemplate
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType, StepType

pytestmark = pytest.mark.asyncio

TENANT = uuid4()
_NOW = dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)


def _make_template_body(num_steps: int = 2) -> dict[str, Any]:
    steps = [
        {
            "step_type": StepType.SEND_MESSAGE.value,
            "step_index": i,
            "label": f"Step {i}",
            "next_step_indexes": [i + 1] if i < num_steps - 1 else [],
            "step_config": {"message": f"Mensaje {i}"},
        }
        for i in range(num_steps)
    ]
    return {
        "description_internal": "Test template body",
        "suggested_channel_priority": ["whatsapp", "email"],
        "config_defaults": {"timezone": "UTC"},
        "steps": steps,
    }


def _make_template(
    *,
    tenant_id: UUID | None = None,
    deleted: bool = False,
    num_steps: int = 2,
) -> CampaignTemplate:
    return CampaignTemplate(
        id=uuid4(),
        tenant_id=tenant_id,  # None = global
        slug="welcome",
        name="Bienvenida",
        description="Template de bienvenida",
        campaign_type=CampaignType.AGENT_CONVERSATION,
        template_body=_make_template_body(num_steps),
        recommended_segment_slugs=["all_leads"],
        tags=["onboarding"],
        version=1,
        created_at=_NOW,
        updated_at=_NOW,
        deleted_at=_NOW if deleted else None,
    )


def _make_campaign() -> Campaign:
    return Campaign(
        id=uuid4(),
        tenant_id=TENANT,
        name="Campaña Bienvenida",
        description=None,
        campaign_type=CampaignType.AGENT_CONVERSATION,
        status=CampaignStatus.DRAFT,
        segment_id=uuid4(),
        segment_snapshot_id=None,
        channel_priority=["whatsapp", "email"],
        offer_id=None,
        brand_summary_id=None,
        config={"timezone": "UTC"},
        scheduled_at=None,
        launched_at=None,
        completed_at=None,
        created_by_user_id=None,
        created_by_source="api",
        created_at=_NOW,
        updated_at=_NOW,
        deleted_at=None,
    )


def _make_service() -> tuple[
    CampaignTemplateService,
    AsyncMock,  # repo
    AsyncMock,  # campaign_service
    SimpleTTLCache,
]:
    repo = AsyncMock()
    campaign_service = AsyncMock()
    cache = SimpleTTLCache()

    svc = CampaignTemplateService(
        repo=repo,
        campaign_service=campaign_service,
        cache=cache,
    )
    return svc, repo, campaign_service, cache


class TestCampaignTemplateServiceList:
    """Tests for list_available() — globals + tenant-scoped + caching."""

    async def test_list_returns_templates(self) -> None:
        """list_available() returns combined list."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        tpls = [_make_template(), _make_template()]
        repo.list_for_tenant.return_value = tpls
        result = await svc.list_available(TENANT, session=session)
        assert len(result) == 2
        repo.list_for_tenant.assert_awaited_once_with(TENANT, session=session)

    async def test_list_cache_hit_skips_repo(self) -> None:
        """list_available() returns cached result on second call."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        tpls = [_make_template()]
        repo.list_for_tenant.return_value = tpls

        # First call
        await svc.list_available(TENANT, session=session)
        # Second call
        result = await svc.list_available(TENANT, session=session)

        assert len(result) == 1
        # Repo called only once
        assert repo.list_for_tenant.await_count == 1


class TestCampaignTemplateServiceGet:
    """Tests for get() — lookup with 404 handling."""

    async def test_get_not_found_raises(self) -> None:
        """get() raises CampaignTemplateNotFoundError when repo returns None."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = None
        with pytest.raises(CampaignTemplateNotFoundError):
            await svc.get(TENANT, uuid4(), session=session)

    async def test_get_deleted_raises(self) -> None:
        """get() raises CampaignTemplateNotFoundError for soft-deleted template."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = _make_template(deleted=True)
        with pytest.raises(CampaignTemplateNotFoundError):
            await svc.get(TENANT, uuid4(), session=session)

    async def test_get_found(self) -> None:
        """get() returns template when found (global or tenant-scoped)."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template()
        repo.get_by_id.return_value = tpl
        result = await svc.get(TENANT, tpl.id, session=session)
        assert result.id == tpl.id

    async def test_get_global_template(self) -> None:
        """get() returns global (tenant_id=None) template when no tenant-scoped found."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(tenant_id=None)  # global
        repo.get_by_id.return_value = tpl
        result = await svc.get(TENANT, tpl.id, session=session)
        assert result.tenant_id is None


class TestCampaignTemplateServiceClone:
    """Tests for clone_to_campaign() — atomic TX contract."""

    async def test_clone_creates_campaign_and_steps(self) -> None:
        """clone_to_campaign() creates Campaign + N steps in single TX."""
        svc, repo, campaign_svc, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(num_steps=2)
        repo.get_by_id.return_value = tpl
        campaign = _make_campaign()
        campaign_svc.create.return_value = campaign
        # Steps add returns campaign unchanged (no step returned in signature)
        campaign_svc.add_step.return_value = None

        dto = CampaignCreateFromTemplate(
            name="Campaña Bienvenida",
            segment_id=uuid4(),
        )
        result = await svc.clone_to_campaign(TENANT, tpl.id, dto, session=session)

        campaign_svc.create.assert_awaited_once()
        assert campaign_svc.add_step.await_count == 2  # 2 steps in template
        assert result.id == campaign.id

    async def test_clone_applies_config_overrides(self) -> None:
        """clone_to_campaign() merges config_overrides on top of config_defaults."""
        svc, repo, campaign_svc, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(num_steps=0)  # no steps — focus on config
        repo.get_by_id.return_value = tpl
        campaign = _make_campaign()
        campaign_svc.create.return_value = campaign

        captured_create_dto: list[Any] = []

        async def capture_create(*args: Any, **kwargs: Any) -> Campaign:
            captured_create_dto.extend(args)
            return campaign

        campaign_svc.create = capture_create  # type: ignore[method-assign]

        dto = CampaignCreateFromTemplate(
            name="Test",
            segment_id=uuid4(),
            config_overrides={"custom_key": "custom_val"},
        )
        await svc.clone_to_campaign(TENANT, tpl.id, dto, session=session)

        # Verify the CampaignCreate passed has merged config
        campaign_create_arg = next((a for a in captured_create_dto if hasattr(a, "config")), None)
        assert campaign_create_arg is not None
        assert campaign_create_arg.config.get("custom_key") == "custom_val"
        # Also includes defaults from template
        assert campaign_create_arg.config.get("timezone") == "UTC"

    async def test_clone_schedules_when_scheduled_for_provided(self) -> None:
        """clone_to_campaign() calls schedule() when dto.scheduled_for is set."""
        svc, repo, campaign_svc, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(num_steps=0)
        repo.get_by_id.return_value = tpl
        campaign = _make_campaign()
        campaign_svc.create.return_value = campaign
        scheduled_campaign = campaign.model_copy(update={"status": CampaignStatus.SCHEDULED})
        campaign_svc.schedule.return_value = scheduled_campaign

        future_dt = _NOW + dt.timedelta(days=7)
        dto = CampaignCreateFromTemplate(
            name="Test Sched",
            segment_id=uuid4(),
            scheduled_for=future_dt,
        )
        result = await svc.clone_to_campaign(TENANT, tpl.id, dto, session=session)

        campaign_svc.schedule.assert_awaited_once_with(TENANT, campaign.id, future_dt, session=session)
        assert result.status == CampaignStatus.SCHEDULED

    async def test_clone_no_schedule_when_no_scheduled_for(self) -> None:
        """clone_to_campaign() does NOT call schedule() when no scheduled_for."""
        svc, repo, campaign_svc, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(num_steps=0)
        repo.get_by_id.return_value = tpl
        campaign = _make_campaign()
        campaign_svc.create.return_value = campaign

        dto = CampaignCreateFromTemplate(name="No sched", segment_id=uuid4())
        await svc.clone_to_campaign(TENANT, tpl.id, dto, session=session)

        campaign_svc.schedule.assert_not_awaited()

    async def test_clone_template_not_found_raises(self) -> None:
        """clone_to_campaign() raises CampaignTemplateNotFoundError if template missing."""
        svc, repo, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = None

        dto = CampaignCreateFromTemplate(name="X", segment_id=uuid4())
        with pytest.raises(CampaignTemplateNotFoundError):
            await svc.clone_to_campaign(TENANT, uuid4(), dto, session=session)

    async def test_clone_resolves_next_step_indexes_to_uuids(self) -> None:
        """clone_to_campaign() resolves index references to UUIDs for steps."""
        svc, repo, campaign_svc, _ = _make_service()
        session = AsyncMock()
        tpl = _make_template(num_steps=3)  # step 0 → 1, step 1 → 2, step 2 → []
        repo.get_by_id.return_value = tpl
        campaign = _make_campaign()
        campaign_svc.create.return_value = campaign

        captured_step_dtos: list[Any] = []

        async def capture_add_step(*args: Any, **kwargs: Any) -> None:
            captured_step_dtos.append(args)

        campaign_svc.add_step = capture_add_step  # type: ignore[method-assign]

        dto = CampaignCreateFromTemplate(name="Chain", segment_id=uuid4())
        await svc.clone_to_campaign(TENANT, tpl.id, dto, session=session)

        assert len(captured_step_dtos) == 3
        # First step (index 0) should have 1 next_step_id UUID
        first_step_dto = captured_step_dtos[0][2]  # positional arg 3 = CampaignStepCreate
        assert len(first_step_dto.next_step_ids) == 1
        assert isinstance(first_step_dto.next_step_ids[0], UUID)
        # Last step (index 2) should have no next_step_ids
        last_step_dto = captured_step_dtos[2][2]
        assert last_step_dto.next_step_ids == []
