"""Tests para el enriquecimiento de inbox con tags de campaña.

Sub-B PR-8: verifica que list_conversations y get_conversation enriquecen
items con campaign_id y campaign_name cuando corresponde.

TDD RED phase.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
LEAD_ID_1 = uuid.UUID("eeee0000-0000-0000-0000-000000000001")
LEAD_ID_2 = uuid.UUID("eeee0000-0000-0000-0000-000000000002")
LEAD_ID_3 = uuid.UUID("eeee0000-0000-0000-0000-000000000003")
CAMPAIGN_ID = uuid.UUID("cccc0000-0000-0000-0000-000000000003")


# ── Tests de DTOs ────────────────────────────────────────────────────────────


def test_conversation_list_item_has_campaign_fields() -> None:
    """ConversationListItem debe tener campaign_id y campaign_name opcionales."""
    from luana_core_sales_agent.api.dto.closer_studio import ConversationListItem

    fields = ConversationListItem.model_fields
    assert "campaign_id" in fields, "ConversationListItem debe tener campaign_id"
    assert "campaign_name" in fields, "ConversationListItem debe tener campaign_name"

    # Deben ser opcionales (None por defecto)
    item = ConversationListItem(
        lead_id=LEAD_ID_1,
        display_name="Lead de prueba",
    )
    assert item.campaign_id is None
    assert item.campaign_name is None


def test_conversation_detail_has_campaign_fields() -> None:
    """ConversationDetail debe tener campaign_id y campaign_name opcionales."""
    from luana_core_sales_agent.api.dto.closer_studio import ConversationDetail

    fields = ConversationDetail.model_fields
    assert "campaign_id" in fields, "ConversationDetail debe tener campaign_id"
    assert "campaign_name" in fields, "ConversationDetail debe tener campaign_name"

    # Deben ser opcionales (None por defecto)
    detail = ConversationDetail(
        lead_id=LEAD_ID_1,
        display_name="Lead de prueba",
    )
    assert detail.campaign_id is None
    assert detail.campaign_name is None


def test_conversation_list_item_campaign_fields_assignable() -> None:
    """ConversationListItem debe poder asignar campaign_id y campaign_name."""
    from luana_core_sales_agent.api.dto.closer_studio import ConversationListItem

    item = ConversationListItem(
        lead_id=LEAD_ID_1,
        display_name="Lead de prueba",
        campaign_id=CAMPAIGN_ID,
        campaign_name="Campaña de abril",
    )
    assert item.campaign_id == CAMPAIGN_ID
    assert item.campaign_name == "Campaña de abril"


# ── Tests del servicio de enriquecimiento ────────────────────────────────────


def test_inbox_campaign_enrichment_service_exists() -> None:
    """inbox_campaign_enrichment.py debe existir con las funciones correctas."""
    from luana_core_sales_agent.application.services import inbox_campaign_enrichment

    assert hasattr(inbox_campaign_enrichment, "enrich_conversation_list_with_campaign")
    assert hasattr(inbox_campaign_enrichment, "enrich_conversation_detail_with_campaign")


@pytest.mark.asyncio
async def test_enrich_list_adds_campaign_fields_for_hit_leads() -> None:
    """enrich_conversation_list_with_campaign añade fields a leads con hit."""
    import datetime as dt

    from luana_core_sales_agent.api.dto.closer_studio import ConversationListItem
    from luana_core_sales_agent.application.services.inbox_campaign_enrichment import (
        enrich_conversation_list_with_campaign,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult, CampaignsLookupPort

    # Dos leads: uno con hit, uno sin hit
    items = [
        ConversationListItem(lead_id=LEAD_ID_1, display_name="Lead 1"),
        ConversationListItem(lead_id=LEAD_ID_2, display_name="Lead 2"),
        ConversationListItem(lead_id=LEAD_ID_3, display_name="Lead 3"),
    ]

    lookup_result_1 = CampaignTaskLookupResult(
        campaign_id=CAMPAIGN_ID,
        campaign_name="Campaña Test",
        task_id=uuid.uuid4(),
        sent_at=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=1),
    )

    class FakePort(CampaignsLookupPort):
        async def find_recent_campaign_task_for_lead(self, **kwargs: object) -> None:
            return None

        async def find_recent_campaign_tasks_for_leads(
            self,
            *,
            tenant_id: uuid.UUID,
            lead_ids: object,
            window_hours: int,
            session: object,
        ) -> dict[uuid.UUID, CampaignTaskLookupResult]:
            # Solo LEAD_ID_1 y LEAD_ID_3 tienen hit
            return {
                LEAD_ID_1: lookup_result_1,
            }

    port = FakePort()
    mock_session = AsyncMock()

    await enrich_conversation_list_with_campaign(
        items,
        tenant_id=TENANT_A,
        port=port,
        window_hours=24,
        session=mock_session,
    )

    # LEAD_ID_1 debe tener campaign_id
    assert items[0].campaign_id == CAMPAIGN_ID
    assert items[0].campaign_name == "Campaña Test"

    # LEAD_ID_2 y LEAD_ID_3 no deben tener campaign_id
    assert items[1].campaign_id is None
    assert items[2].campaign_id is None


@pytest.mark.asyncio
async def test_enrich_list_fail_open_on_exception() -> None:
    """enrich_conversation_list_with_campaign es fail-open: en excepción, items quedan inalterados."""
    from luana_core_sales_agent.api.dto.closer_studio import ConversationListItem
    from luana_core_sales_agent.application.services.inbox_campaign_enrichment import (
        enrich_conversation_list_with_campaign,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult, CampaignsLookupPort

    items = [
        ConversationListItem(lead_id=LEAD_ID_1, display_name="Lead 1"),
    ]

    class FailingPort(CampaignsLookupPort):
        async def find_recent_campaign_task_for_lead(self, **kwargs: object) -> None:
            return None

        async def find_recent_campaign_tasks_for_leads(
            self, **kwargs: object
        ) -> dict[uuid.UUID, CampaignTaskLookupResult]:
            msg = "Error de base de datos"
            raise RuntimeError(msg)

    port = FailingPort()
    mock_session = AsyncMock()

    # No debe lanzar excepción
    await enrich_conversation_list_with_campaign(
        items,
        tenant_id=TENANT_A,
        port=port,
        window_hours=24,
        session=mock_session,
    )

    # Los items deben quedar inalterados (fail-open)
    assert items[0].campaign_id is None
    assert items[0].campaign_name is None


@pytest.mark.asyncio
async def test_enrich_detail_adds_campaign_fields_for_hit() -> None:
    """enrich_conversation_detail_with_campaign añade fields si hay hit."""
    import datetime as dt

    from luana_core_sales_agent.api.dto.closer_studio import ConversationDetail
    from luana_core_sales_agent.application.services.inbox_campaign_enrichment import (
        enrich_conversation_detail_with_campaign,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult, CampaignsLookupPort

    detail = ConversationDetail(lead_id=LEAD_ID_1, display_name="Lead 1")

    lookup_result = CampaignTaskLookupResult(
        campaign_id=CAMPAIGN_ID,
        campaign_name="Campaña Test",
        task_id=uuid.uuid4(),
        sent_at=dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(hours=2),
    )

    class FakePort(CampaignsLookupPort):
        async def find_recent_campaign_task_for_lead(
            self,
            *,
            tenant_id: uuid.UUID,
            lead_id: uuid.UUID,
            window_hours: int,
            session: object,
        ) -> CampaignTaskLookupResult:
            return lookup_result

        async def find_recent_campaign_tasks_for_leads(
            self, **kwargs: object
        ) -> dict[uuid.UUID, CampaignTaskLookupResult]:
            return {}

    port = FakePort()
    mock_session = AsyncMock()

    await enrich_conversation_detail_with_campaign(
        detail,
        tenant_id=TENANT_A,
        port=port,
        window_hours=24,
        session=mock_session,
    )

    assert detail.campaign_id == CAMPAIGN_ID
    assert detail.campaign_name == "Campaña Test"


@pytest.mark.asyncio
async def test_enrich_detail_null_when_miss() -> None:
    """enrich_conversation_detail_with_campaign deja None cuando no hay hit."""
    from luana_core_sales_agent.api.dto.closer_studio import ConversationDetail
    from luana_core_sales_agent.application.services.inbox_campaign_enrichment import (
        enrich_conversation_detail_with_campaign,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult, CampaignsLookupPort

    detail = ConversationDetail(lead_id=LEAD_ID_1, display_name="Lead 1")

    class FakePort(CampaignsLookupPort):
        async def find_recent_campaign_task_for_lead(self, **kwargs: object) -> None:
            return None

        async def find_recent_campaign_tasks_for_leads(
            self, **kwargs: object
        ) -> dict[uuid.UUID, CampaignTaskLookupResult]:
            return {}

    port = FakePort()
    mock_session = AsyncMock()

    await enrich_conversation_detail_with_campaign(
        detail,
        tenant_id=TENANT_A,
        port=port,
        window_hours=24,
        session=mock_session,
    )

    assert detail.campaign_id is None
    assert detail.campaign_name is None
