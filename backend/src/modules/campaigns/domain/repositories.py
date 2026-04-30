"""Campaign domain repository interfaces (ABC ports).

Abstract async interfaces, tenant-scoped.
Every method receives tenant_id (except documented cross-tenant exceptions).
Implementations live in infrastructure/repositories/*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.domain.campaign import Campaign
    from src.modules.campaigns.domain.campaign_step import CampaignStep
    from src.modules.campaigns.domain.campaign_task import CampaignTask
    from src.modules.campaigns.domain.campaign_template import CampaignTemplate
    from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType, TaskStatus
    from src.modules.campaigns.domain.segment import Segment, SegmentSnapshot


class CampaignRepository(ABC):
    """Abstract repository for Campaign aggregate root."""

    @abstractmethod
    async def append(self, campaign: Campaign, *, session: AsyncSession) -> None:
        """Persist a new Campaign. Raises if id already exists."""
        ...

    @abstractmethod
    async def update(self, campaign: Campaign, *, session: AsyncSession) -> None:
        """Update all mutable fields of an existing Campaign."""
        ...

    @abstractmethod
    async def get_by_id(self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> Campaign | None:
        """Fetch by primary key, scoped to tenant. Returns None if not found or deleted."""
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status_filter: Sequence[CampaignStatus] | None = None,
        type_filter: Sequence[CampaignType] | None = None,
        sort_by: str = "created_at_desc",
    ) -> Sequence[Campaign]:
        """List campaigns for a tenant with optional status/type filter. Excludes soft-deleted."""
        ...

    @abstractmethod
    async def count_active(self, tenant_id: UUID, *, session: AsyncSession) -> int:
        """Count campaigns in active statuses (draft/scheduled/running/paused).

        Used by plan limit check (max_campaigns_active cap).
        SQL: SELECT COUNT(*) WHERE tenant_id=:t AND status IN (...) AND deleted_at IS NULL
        """
        ...

    @abstractmethod
    async def count_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        status_filter: Sequence[CampaignStatus] | None = None,
    ) -> int:
        """COUNT(*) for paginated list endpoint. Tenant-scoped + soft-delete-aware."""
        ...

    @abstractmethod
    async def soft_delete(self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). No hard deletes."""
        ...


class CampaignStepRepository(ABC):
    """Abstract repository for CampaignStep entities."""

    @abstractmethod
    async def append(self, step: CampaignStep, *, session: AsyncSession) -> None:
        """Persist a new CampaignStep."""
        ...

    @abstractmethod
    async def update(self, step: CampaignStep, *, session: AsyncSession) -> None:
        """Update an existing CampaignStep."""
        ...

    @abstractmethod
    async def get_by_id(self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> CampaignStep | None:
        """Fetch by primary key, scoped to tenant. Returns None if not found or deleted."""
        ...

    @abstractmethod
    async def list_by_campaign(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> Sequence[CampaignStep]:
        """List all steps for a campaign, ordered by step_index. Excludes soft-deleted."""
        ...

    @abstractmethod
    async def soft_delete(self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). No hard deletes."""
        ...


class CampaignTaskRepository(ABC):
    """Abstract repository for CampaignTask entities.

    Performance critical for 1000+ tenants — worker queue operations.
    """

    @abstractmethod
    async def append(self, task: CampaignTask, *, session: AsyncSession) -> None:
        """Persist a single CampaignTask."""
        ...

    @abstractmethod
    async def append_many(self, tasks: Sequence[CampaignTask], *, session: AsyncSession) -> None:
        """Bulk insert tasks with idempotency dedup.

        INSERT ... ON CONFLICT (tenant_id, idempotency_key) DO NOTHING.
        Service layer PR-4 / S2 orchestrator uses this when launching
        a campaign over a snapshot of N leads.
        """
        ...

    @abstractmethod
    async def get_by_id(self, task_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> CampaignTask | None:
        """Fetch by primary key, scoped to tenant. Returns None if not found or deleted."""
        ...

    @abstractmethod
    async def claim_pending_for_worker(
        self,
        *,
        tenant_id: UUID | None,
        scheduled_before: dt.datetime,
        batch_size: int = 50,
        session: AsyncSession,
    ) -> Sequence[CampaignTask]:
        """Claim pending/scheduled tasks for worker execution.

        Cross-tenant capable for worker scope (tenant_id=None).
        This is the ONLY documented cross-tenant exception in this module —
        same pattern as outbox.claim_pending (FOR UPDATE SKIP LOCKED).

        SQL: SELECT ... WHERE status IN ('pending','scheduled') AND scheduled_at <= :before
             FOR UPDATE SKIP LOCKED LIMIT :batch_size

        Tenant-scoped variant (tenant_id provided) for ops/admin queries.
        """
        ...

    @abstractmethod
    async def mark_dispatched(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        outbox_event_id: UUID | None,
        session: AsyncSession,
    ) -> None:
        """Transition task to DISPATCHED status with optional outbox link."""
        ...

    @abstractmethod
    async def mark_sent(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        external_message_id: str | None,
        channel_used: str,
        session: AsyncSession,
    ) -> None:
        """Transition task to SENT status with channel resolution data."""
        ...

    @abstractmethod
    async def mark_failed(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        error_code: str,
        error_message: str,
        session: AsyncSession,
    ) -> None:
        """Transition task to FAILED status with error details."""
        ...

    @abstractmethod
    async def mark_skipped(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        reason: str,
        compliance_check: dict | None,
        session: AsyncSession,
    ) -> None:
        """Transition task to SKIPPED status (compliance/rate/budget gate refused)."""
        ...

    @abstractmethod
    async def count_by_campaign_status(
        self,
        campaign_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> dict[TaskStatus, int]:
        """Count tasks per status for a campaign. For GET /campaigns/{id}/stats (S3)."""
        ...

    @abstractmethod
    async def find_recent_for_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        status: TaskStatus,
        since: dt.datetime,
        session: AsyncSession,
    ) -> CampaignTask | None:
        """Retorna la task más reciente que coincide con (tenant, lead, status, sent_at >= since).

        Devuelve la task con max sent_at dentro de la ventana, o None.
        Usado por reconocimiento inbound: status=SENT, since=now-window_hours.
        Tenant-scoped. Excluye soft-deleted.
        Soportado por idx_campaign_tasks_lookup_lead (WHERE deleted_at IS NULL).
        """
        ...

    @abstractmethod
    async def find_recent_for_leads(
        self,
        *,
        tenant_id: UUID,
        lead_ids: Sequence[UUID],
        status: TaskStatus,
        since: dt.datetime,
        session: AsyncSession,
    ) -> dict[UUID, CampaignTask]:
        """Variante batch — retorna mapa lead_id → task más reciente con hit.

        Usado por inbox enrichment para evitar N+1.
        Los lead_ids sin hit están ausentes del dict retornado.
        """
        ...

    @abstractmethod
    async def count_responded_leads(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> int:
        """Conteo distinto de leads que enviaron mensaje user-role DESPUÉS de campaign_task.sent_at.

        Scoped a una sola campaña + tenant.

        SQL (ilustrativo — implementación es dueña de los detalles):
            SELECT COUNT(DISTINCT m.user_id)
            FROM messages m
            JOIN campaign_task ct
              ON ct.lead_id = m.user_id
             AND ct.tenant_id = m.tenant_id
            WHERE ct.tenant_id = :t
              AND ct.campaign_id = :c
              AND ct.status = 'sent'
              AND ct.deleted_at IS NULL
              AND m.role = 'user'
              AND m.created_at > ct.sent_at

        NOTA: Lee messages de sales_agent desde el repositorio de campaigns.
        Esta es la ÚNICA lectura cross-module documentada en este PR — ver
        allowlist KNOWN_CROSS_MODULE_TABLE_READS en arch test PR-8.
        Justificación: lectura read-only tenant-scoped; overhead de port
        no amortizado para un solo query (decisión arquitecto §1).
        """
        ...


class SegmentRepository(ABC):
    """Abstract repository for Segment entities."""

    @abstractmethod
    async def append(self, segment: Segment, *, session: AsyncSession) -> None:
        """Persist a new Segment. Raises on duplicate (tenant_id, name) if not deleted."""
        ...

    @abstractmethod
    async def update(self, segment: Segment, *, session: AsyncSession) -> None:
        """Update an existing Segment."""
        ...

    @abstractmethod
    async def get_by_id(self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> Segment | None:
        """Fetch by primary key, scoped to tenant. Returns None if not found or deleted."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str, tenant_id: UUID, *, session: AsyncSession) -> Segment | None:
        """Fetch by natural key (name), scoped to tenant. Returns None if not found or deleted."""
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Segment]:
        """List segments for a tenant. Excludes soft-deleted."""
        ...

    @abstractmethod
    async def soft_delete(self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). Releases the unique name for reuse."""
        ...


class SegmentSnapshotRepository(ABC):
    """Abstract repository for SegmentSnapshot entities."""

    @abstractmethod
    async def append(self, snapshot: SegmentSnapshot, *, session: AsyncSession) -> None:
        """Persist a new SegmentSnapshot."""
        ...

    @abstractmethod
    async def get_by_id(self, snapshot_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> SegmentSnapshot | None:
        """Fetch by primary key, scoped to tenant. Returns None if not found or soft-deleted."""
        ...

    @abstractmethod
    async def get_latest_for_segment(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> SegmentSnapshot | None:
        """Fetch the most recent snapshot for a segment. Returns None if none exist."""
        ...

    @abstractmethod
    async def list_by_segment(
        self,
        segment_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 10,
    ) -> Sequence[SegmentSnapshot]:
        """List snapshots for a segment, ordered by snapshotted_at DESC."""
        ...


class CampaignTemplateRepository(ABC):
    """Abstract repository for CampaignTemplate entities.

    Handles both global templates (tenant_id=None) and per-tenant templates.
    """

    @abstractmethod
    async def append(self, tpl: CampaignTemplate, *, session: AsyncSession) -> None:
        """Persist a new CampaignTemplate."""
        ...

    @abstractmethod
    async def get_by_id(
        self,
        tpl_id: UUID,
        tenant_id: UUID | None,
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None:
        """Fetch by primary key.

        If tenant_id is provided, returns tenant-scoped OR global.
        If tenant_id is None, returns global templates only.
        """
        ...

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
        tenant_id: UUID | None,
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None:
        """Fetch by natural key (slug).

        If tenant_id is provided, checks tenant-scoped first, then global.
        If tenant_id is None, returns global templates only.
        """
        ...

    @abstractmethod
    async def list_globals(self, *, session: AsyncSession) -> Sequence[CampaignTemplate]:
        """List all global (tenant_id=NULL) templates.

        Cross-tenant: tenant_id=None is semantically correct for global lookup.
        Documented exception in arch test CROSS_TENANT_ALLOWED_METHODS.
        """
        ...

    @abstractmethod
    async def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> Sequence[CampaignTemplate]:
        """Returns globals UNION tenant-scoped templates.

        Service PR-4 uses this for 'available templates' view.
        """
        ...
