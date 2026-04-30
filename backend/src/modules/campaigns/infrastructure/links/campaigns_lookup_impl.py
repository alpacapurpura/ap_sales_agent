"""CampaignsLookupAdapter — implementación del port CampaignsLookupPort.

Adapta CampaignTaskRepositoryImpl y CampaignRepositoryImpl al puerto
definido en shared/links/ports/campaigns.py.

Registrado via create_campaigns_lookup_port() — los callers nunca
importan directamente de campaigns.infrastructure.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

import structlog

from src.modules.campaigns.domain.enums import TaskStatus
from src.modules.campaigns.infrastructure.repositories.campaign_repository_impl import (
    CampaignRepositoryImpl,
)
from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
    CampaignTaskRepositoryImpl,
)
from src.shared.domain.datetime_utils import utc_now
from src.shared.links.ports.campaigns import CampaignsLookupPort, CampaignTaskLookupResult

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class CampaignsLookupAdapter(CampaignsLookupPort):
    """Implementación SQLAlchemy del port de lookup de campaigns.

    Instanciada vía create_campaigns_lookup_port() — no instanciar directamente.
    """

    def __init__(self) -> None:
        """Inicializar con repos de campaigns."""
        self._task_repo = CampaignTaskRepositoryImpl()
        self._campaign_repo = CampaignRepositoryImpl()

    async def find_recent_campaign_task_for_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        window_hours: int,
        session: AsyncSession,
    ) -> CampaignTaskLookupResult | None:
        """Retorna la campaign_task SENT más reciente dentro de la ventana.

        Returns None si no hay hit.
        """
        since = utc_now() - dt.timedelta(hours=window_hours)
        task = await self._task_repo.find_recent_for_lead(
            tenant_id=tenant_id,
            lead_id=lead_id,
            status=TaskStatus.SENT,
            since=since,
            session=session,
        )
        if task is None:
            return None

        # Obtener nombre de la campaña
        campaign = await self._campaign_repo.get_by_id(task.campaign_id, tenant_id, session=session)
        campaign_name = campaign.name if campaign else "Campaña"

        logger.debug(
            "campaigns_lookup_hit",
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
            campaign_id=str(task.campaign_id),
            sent_at=task.sent_at.isoformat() if task.sent_at else None,
        )

        return CampaignTaskLookupResult(
            campaign_id=task.campaign_id,
            campaign_name=campaign_name,
            task_id=task.id,
            sent_at=task.sent_at or since,
        )

    async def find_recent_campaign_tasks_for_leads(
        self,
        *,
        tenant_id: UUID,
        lead_ids: Sequence[UUID],
        window_hours: int,
        session: AsyncSession,
    ) -> dict[UUID, CampaignTaskLookupResult]:
        """Variante batch — retorna mapa lead_id → CampaignTaskLookupResult.

        Evita N+1 para inbox enrichment. Solo incluye leads con hit.
        """
        if not lead_ids:
            return {}

        since = utc_now() - dt.timedelta(hours=window_hours)
        task_map = await self._task_repo.find_recent_for_leads(
            tenant_id=tenant_id,
            lead_ids=lead_ids,
            status=TaskStatus.SENT,
            since=since,
            session=session,
        )

        if not task_map:
            return {}

        # Obtener nombres de campañas en una sola consulta (by unique campaign_ids)
        unique_campaign_ids = list({task.campaign_id for task in task_map.values()})
        campaign_names: dict[UUID, str] = {}
        for cid in unique_campaign_ids:
            campaign = await self._campaign_repo.get_by_id(cid, tenant_id, session=session)
            campaign_names[cid] = campaign.name if campaign else "Campaña"

        result: dict[UUID, CampaignTaskLookupResult] = {}
        for lead_id, task in task_map.items():
            result[lead_id] = CampaignTaskLookupResult(
                campaign_id=task.campaign_id,
                campaign_name=campaign_names.get(task.campaign_id, "Campaña"),
                task_id=task.id,
                sent_at=task.sent_at or since,
            )

        logger.debug(
            "campaigns_lookup_batch_hit",
            tenant_id=str(tenant_id),
            hit_count=len(result),
            total_requested=len(list(lead_ids)),
        )

        return result
