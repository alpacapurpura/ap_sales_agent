"""CampaignStatsService — estadísticas agregadas de una campaña.

PR-8 Sub-B: live DB queries indexadas.
Lectura cross-module (sales_agent.messages) documentada en
CampaignTaskRepository.count_responded_leads y arch test PR-8.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.campaigns.application.dtos.campaign_dtos import CampaignStatsResponse
from src.modules.campaigns.application.services.campaign_service import CampaignNotFoundError
from src.modules.campaigns.domain.enums import TaskStatus
from src.modules.campaigns.domain.repositories import CampaignRepository, CampaignTaskRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.shared.domain.locale import TenantLocale

logger = structlog.get_logger(__name__)


class CampaignStatsService:
    """Computa estadísticas agregadas para una campaña individual.

    Single-tenant + single-campaign. Live DB queries, indexadas.
    Lectura cross-module (sales_agent.messages) documentada en
    CampaignTaskRepository.count_responded_leads.
    """

    def __init__(
        self,
        *,
        campaign_repo: CampaignRepository,
        task_repo: CampaignTaskRepository,
        get_locale: Callable[[UUID], Awaitable[TenantLocale]],
    ) -> None:
        """Inicializar con repos y función de locale."""
        self._campaign_repo = campaign_repo
        self._task_repo = task_repo
        self._get_locale = get_locale

    async def get_stats(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> CampaignStatsResponse:
        """Estadísticas idempotentes de una campaña. Lanza CampaignNotFoundError si no existe.

        1. Verificar que la campaña existe y es del tenant (404 si no).
        2. count_by_campaign_status → total_tasks, sent_count, otros.
        3. count_responded_leads → responded_count proxy (audit_log).
        4. converted_count = 0, attribution_method = "deferred_pr_followup" (MVP S3).
        5. response_rate, conversion_rate computadas (NULL si sent_count==0).
        6. currency de tenant_locale.
        """
        # 1. Verificar existencia + tenant isolation
        campaign = await self._campaign_repo.get_by_id(campaign_id, tenant_id, session=session)
        if campaign is None:
            msg = f"Campaña {campaign_id} no encontrada para el tenant."
            raise CampaignNotFoundError(msg)

        # 2. Conteo por status
        status_counts = await self._task_repo.count_by_campaign_status(campaign_id, tenant_id, session=session)

        sent_count = status_counts.get(TaskStatus.SENT, 0)
        total_tasks = sum(status_counts.values())

        # 3. Leads respondidos (proxy via messages)
        responded_count = await self._task_repo.count_responded_leads(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            session=session,
        )

        # 4. Conversiones diferidas MVP S3
        converted_count = 0

        # 5. Rates (NULL si sent_count==0)
        response_rate: float | None = None
        conversion_rate: float | None = None
        if sent_count > 0:
            response_rate = responded_count / sent_count
            conversion_rate = converted_count / sent_count

        # 6. Currency de tenant_locale
        currency: str | None = None
        try:
            locale = await self._get_locale(tenant_id)
            currency = locale.currency
        except Exception:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "campaign_stats_currency_lookup_failed",
                tenant_id=str(tenant_id),
                campaign_id=str(campaign_id),
            )

        logger.info(
            "campaign_stats_computed",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            total_tasks=total_tasks,
            sent_count=sent_count,
            responded_count=responded_count,
        )

        return CampaignStatsResponse(
            campaign_id=campaign_id,
            total_tasks=total_tasks,
            sent_count=sent_count,
            responded_count=responded_count,
            converted_count=converted_count,
            converted_count_attribution_method="deferred_pr_followup",
            response_rate=response_rate,
            conversion_rate=conversion_rate,
            currency=currency,
        )
