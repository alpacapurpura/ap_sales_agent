"""Cross-module read port for campaigns.

Consumed by copilot subagent (PI-2), CRM Hub (S4), and sales_agent (PR-8).
Exposes service factories without leaking internals.
DDD: never import from modules/campaigns directly — use this port.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class CampaignReadOnlyPort(Protocol):
    """Read-only view of campaigns for cross-module consumers."""

    async def get_campaign_summary(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> dict | None:
        """Return dict shape compatible with CampaignResponse fields (read-only).

        Decouples consumers from domain entity churn.
        Returns None if campaign not found or not owned by tenant.
        """


def get_campaign_read_port() -> CampaignReadOnlyPort:
    """Lazy factory. PI-2 commercial_director subagent consumes via this."""
    from luana_core_campaigns.application.services.campaign_read_adapter import (
        CampaignReadAdapter,
    )

    return CampaignReadAdapter()


# ── PR-8: Inbound recognition + inbox enrichment port ─────────────────────────


class CampaignTaskLookupResult:
    """DTO ligero retornado por los métodos de lookup.

    No es un modelo Pydantic — forma de dominio pura con el mínimo
    necesario para el tagging y reconocimiento inbound.
    """

    def __init__(
        self,
        *,
        campaign_id: UUID,
        campaign_name: str,
        task_id: UUID,
        sent_at: dt.datetime,
    ) -> None:
        """Inicializar resultado de lookup de campaign task."""
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name
        self.task_id = task_id
        self.sent_at = sent_at


class CampaignsLookupPort(ABC):
    """Acceso de lectura a campaigns desde módulos cruzados.

    Patrón port/adapter (DDD). Implementación vive en
    campaigns/infrastructure/links/campaigns_lookup_impl.py.
    La factory create_campaigns_lookup_port() retorna la implementación
    sin que el caller importe directamente de campaigns.
    """

    @abstractmethod
    async def find_recent_campaign_task_for_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        window_hours: int,
        session: AsyncSession,
    ) -> CampaignTaskLookupResult | None:
        """Retorna la campaign_task SENT más reciente dentro de la ventana.

        Returns None si no hay hit. Tenant-scoped. Excluye soft-deleted.
        Usado por reconocimiento inbound en chat.py::process_chat_flow.
        """
        ...

    @abstractmethod
    async def find_recent_campaign_tasks_for_leads(
        self,
        *,
        tenant_id: UUID,
        lead_ids: Sequence[UUID],
        window_hours: int,
        session: AsyncSession,
    ) -> dict[UUID, CampaignTaskLookupResult]:
        """Variante batch — retorna mapa lead_id → CampaignTaskLookupResult.

        Solo los leads con hit aparecen en el dict (caller trata ausencia como None).
        Usado por inbox enrichment para evitar N+1.
        """
        ...


def create_campaigns_lookup_port() -> CampaignsLookupPort:
    """Factory — retorna la implementación SQLAlchemy.

    Vive junto al ABC para que los callers no importen infra directamente.
    La implementación vive en campaigns/infrastructure/links/.
    """
    from luana_core_campaigns.infrastructure.links.campaigns_lookup_impl import (
        CampaignsLookupAdapter,
    )

    return CampaignsLookupAdapter()
