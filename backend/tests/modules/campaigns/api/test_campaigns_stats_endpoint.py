"""Tests para el endpoint GET /api/v1/campaigns/{campaign_id}/stats.

Sub-B PR-8: verifica happy path, tenant isolation, rates nulas cuando
sent_count=0, attribution method y campo currency.

TDD RED phase.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
CAMPAIGN_ID = uuid.UUID("cccc0000-0000-0000-0000-000000000003")


# ── Tests de DTO ──────────────────────────────────────────────────────────────


def test_campaign_stats_response_dto_exists() -> None:
    """CampaignStatsResponse debe existir en el módulo campaigns."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse

    assert CampaignStatsResponse is not None


def test_campaign_stats_response_has_required_fields() -> None:
    """CampaignStatsResponse debe tener todos los campos requeridos."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse

    fields = CampaignStatsResponse.model_fields
    assert "campaign_id" in fields
    assert "total_tasks" in fields
    assert "sent_count" in fields
    assert "responded_count" in fields
    assert "converted_count" in fields
    assert "converted_count_attribution_method" in fields
    assert "response_rate" in fields
    assert "conversion_rate" in fields
    assert "currency" in fields


def test_campaign_stats_response_currency_is_optional() -> None:
    """currency en CampaignStatsResponse debe ser str | None."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse

    # Debe poder construirse sin currency
    stats = CampaignStatsResponse(
        campaign_id=CAMPAIGN_ID,
        total_tasks=5,
        sent_count=3,
        responded_count=2,
        converted_count=0,
        converted_count_attribution_method="deferred_pr_followup",
        response_rate=2 / 3,
        conversion_rate=None,
        currency=None,
    )
    assert stats.currency is None


def test_campaign_stats_response_attribution_method_literal() -> None:
    """converted_count_attribution_method debe ser un Literal válido."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse

    stats = CampaignStatsResponse(
        campaign_id=CAMPAIGN_ID,
        total_tasks=0,
        sent_count=0,
        responded_count=0,
        converted_count=0,
        converted_count_attribution_method="deferred_pr_followup",
        response_rate=None,
        conversion_rate=None,
        currency="USD",
    )
    assert stats.converted_count_attribution_method == "deferred_pr_followup"


def test_campaign_stats_response_rates_null_when_sent_zero() -> None:
    """response_rate y conversion_rate deben poder ser None cuando sent_count=0."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse

    stats = CampaignStatsResponse(
        campaign_id=CAMPAIGN_ID,
        total_tasks=0,
        sent_count=0,
        responded_count=0,
        converted_count=0,
        converted_count_attribution_method="deferred_pr_followup",
        response_rate=None,
        conversion_rate=None,
        currency=None,
    )
    assert stats.response_rate is None
    assert stats.conversion_rate is None


# ── Tests del servicio ─────────────────────────────────────────────────────────


def test_campaign_stats_service_exists() -> None:
    """CampaignStatsService debe existir en campaigns.application.services."""
    from luana_core_campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )

    assert CampaignStatsService is not None


@pytest.mark.asyncio
async def test_campaign_stats_service_happy_path() -> None:
    """CampaignStatsService.get_stats retorna stats correctas."""
    from luana_core_campaigns.application.dtos.campaign_dtos import CampaignStatsResponse
    from luana_core_campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )
    from luana_core_campaigns.domain.enums import TaskStatus

    # Mock repos
    mock_campaign = MagicMock()
    mock_campaign.id = CAMPAIGN_ID
    mock_campaign.tenant_id = TENANT_A

    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.get_by_id.return_value = mock_campaign

    mock_task_repo = AsyncMock()
    mock_task_repo.count_by_campaign_status.return_value = {
        TaskStatus.SENT: 3,
        TaskStatus.FAILED: 1,
        TaskStatus.PENDING: 1,
    }
    mock_task_repo.count_responded_leads.return_value = 2

    mock_locale = MagicMock()
    mock_locale.currency = "PEN"

    async def mock_get_locale(tenant_id: object) -> object:
        return mock_locale

    svc = CampaignStatsService(
        campaign_repo=mock_campaign_repo,
        task_repo=mock_task_repo,
        get_locale=mock_get_locale,
    )

    mock_session = AsyncMock()
    stats = await svc.get_stats(
        tenant_id=TENANT_A,
        campaign_id=CAMPAIGN_ID,
        session=mock_session,
    )

    assert isinstance(stats, CampaignStatsResponse)
    assert stats.campaign_id == CAMPAIGN_ID
    assert stats.sent_count == 3
    assert stats.total_tasks == 5
    assert stats.responded_count == 2
    assert stats.converted_count == 0
    assert stats.converted_count_attribution_method == "deferred_pr_followup"
    assert stats.currency == "PEN"
    assert stats.response_rate == pytest.approx(2 / 3, rel=1e-4)


@pytest.mark.asyncio
async def test_campaign_stats_service_zero_tasks_rates_null() -> None:
    """Con cero tasks, las rates deben ser None."""
    from luana_core_campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )

    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.get_by_id.return_value = MagicMock()

    mock_task_repo = AsyncMock()
    mock_task_repo.count_by_campaign_status.return_value = {}
    mock_task_repo.count_responded_leads.return_value = 0

    mock_locale = MagicMock()
    mock_locale.currency = "USD"

    async def mock_get_locale(tenant_id: object) -> object:
        return mock_locale

    svc = CampaignStatsService(
        campaign_repo=mock_campaign_repo,
        task_repo=mock_task_repo,
        get_locale=mock_get_locale,
    )

    mock_session = AsyncMock()
    stats = await svc.get_stats(
        tenant_id=TENANT_A,
        campaign_id=CAMPAIGN_ID,
        session=mock_session,
    )

    assert stats.response_rate is None
    assert stats.conversion_rate is None
    assert stats.sent_count == 0
    assert stats.total_tasks == 0


@pytest.mark.asyncio
async def test_campaign_stats_service_raises_not_found_when_missing() -> None:
    """CampaignStatsService lanza CampaignNotFoundError si la campaña no existe."""
    from luana_core_campaigns.application.services.campaign_service import CampaignNotFoundError
    from luana_core_campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )

    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.get_by_id.return_value = None

    mock_task_repo = AsyncMock()

    async def mock_get_locale(tenant_id: object) -> object:
        return MagicMock()

    svc = CampaignStatsService(
        campaign_repo=mock_campaign_repo,
        task_repo=mock_task_repo,
        get_locale=mock_get_locale,
    )

    with pytest.raises(CampaignNotFoundError):
        await svc.get_stats(
            tenant_id=TENANT_A,
            campaign_id=CAMPAIGN_ID,
            session=AsyncMock(),
        )


@pytest.mark.asyncio
async def test_campaign_stats_service_tenant_isolation() -> None:
    """CampaignStatsService lanza CampaignNotFoundError si tenant no coincide."""
    from luana_core_campaigns.application.services.campaign_service import CampaignNotFoundError
    from luana_core_campaigns.application.services.campaign_stats_service import (
        CampaignStatsService,
    )

    # repo devuelve None para TENANT_B (aislamiento de tenant)
    mock_campaign_repo = AsyncMock()
    mock_campaign_repo.get_by_id.return_value = None  # tenant_id mismatch → None

    mock_task_repo = AsyncMock()

    async def mock_get_locale(tenant_id: object) -> object:
        return MagicMock()

    svc = CampaignStatsService(
        campaign_repo=mock_campaign_repo,
        task_repo=mock_task_repo,
        get_locale=mock_get_locale,
    )

    with pytest.raises(CampaignNotFoundError):
        await svc.get_stats(
            tenant_id=TENANT_B,
            campaign_id=CAMPAIGN_ID,
            session=AsyncMock(),
        )


# ── Tests del endpoint ────────────────────────────────────────────────────────


def test_stats_endpoint_declared_in_router() -> None:
    """El endpoint GET /campaigns/{id}/stats debe existir en el router."""
    from pathlib import Path

    router_path = (
        Path(__file__).parents[4] / "src" / "modules" / "campaigns" / "api" / "routers" / "campaigns_router.py"
    )
    src = router_path.read_text(encoding="utf-8")
    assert "stats" in src, "El router debe tener un endpoint /stats"
    assert "CampaignStatsResponse" in src, "El endpoint debe declarar response_model=CampaignStatsResponse"


def test_stats_endpoint_declares_response_model() -> None:
    """El endpoint debe declarar response_model=CampaignStatsResponse."""
    from pathlib import Path

    router_path = (
        Path(__file__).parents[4] / "src" / "modules" / "campaigns" / "api" / "routers" / "campaigns_router.py"
    )
    src = router_path.read_text(encoding="utf-8")
    assert "response_model=CampaignStatsResponse" in src, (
        "PR-8: endpoint stats DEBE declarar response_model=CampaignStatsResponse"
    )
