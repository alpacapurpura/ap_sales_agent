"""Inbox campaign enrichment — enriquece conversaciones con datos de campaña.

PR-8 Sub-B: best-effort enrichment para inbox listing y detail.
Fail-open: cualquier excepción deja items inalterados, emite warning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.sales_agent.api.dto.closer_studio import ConversationDetail, ConversationListItem
    from src.shared.links.ports.campaigns import CampaignsLookupPort

logger = structlog.get_logger(__name__)


async def enrich_conversation_list_with_campaign(
    items: list[ConversationListItem],
    *,
    tenant_id: UUID,
    port: CampaignsLookupPort,
    window_hours: int,
    session: AsyncSession,
) -> None:
    """Enriquece items de lista con campaign_id + campaign_name (best-effort).

    Muta los items in-place. Lookup batch para evitar N+1.
    Fail-open: cualquier excepción → log warning, items sin cambio.
    """
    try:
        if not items:
            return
        lead_ids = [it.lead_id for it in items]
        hits = await port.find_recent_campaign_tasks_for_leads(
            tenant_id=tenant_id,
            lead_ids=lead_ids,
            window_hours=window_hours,
            session=session,
        )
        for it in items:
            hit = hits.get(it.lead_id)
            if hit is not None:
                it.campaign_id = hit.campaign_id
                it.campaign_name = hit.campaign_name
    except Exception as exc:  # noqa: BLE001 — best-effort enrichment
        logger.warning(
            "inbox_campaign_enrichment_list_failed",
            tenant_id=str(tenant_id),
            error=str(exc),
        )


async def enrich_conversation_detail_with_campaign(
    detail: ConversationDetail,
    *,
    tenant_id: UUID,
    port: CampaignsLookupPort,
    window_hours: int,
    session: AsyncSession,
) -> None:
    """Variante de enriquecimiento para conversación individual.

    Muta el detail in-place. Fail-open: cualquier excepción → log warning, detail sin cambio.
    """
    try:
        hit = await port.find_recent_campaign_task_for_lead(
            tenant_id=tenant_id,
            lead_id=detail.lead_id,
            window_hours=window_hours,
            session=session,
        )
        if hit is not None:
            detail.campaign_id = hit.campaign_id
            detail.campaign_name = hit.campaign_name
    except Exception as exc:  # noqa: BLE001 — best-effort enrichment
        logger.warning(
            "inbox_campaign_enrichment_detail_failed",
            tenant_id=str(tenant_id),
            lead_id=str(detail.lead_id),
            error=str(exc),
        )
