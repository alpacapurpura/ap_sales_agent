"""CampaignService — CRUD + FSM lifecycle for Campaign aggregate.

PR-4: application layer. Services validate, orchestrate repos, emit events.
FSM transitions delegated to Campaign.transition_allowed() (PR-3 domain SSoT).
Service NEVER hardcodes the FSM dict — arch test test_campaigns_fsm_service_layer.py enforces.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog
from luana_core_campaigns.application.services._event_bridge import to_domain_event
from luana_core_campaigns.domain.campaign import Campaign
from luana_core_campaigns.domain.campaign_step import CampaignStep
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType
from luana_core_campaigns.domain.events import (
    CampaignCanceled,
    CampaignCompleted,
    CampaignCreated,
    CampaignLaunched,
    CampaignPaused,
    CampaignScheduled,
    CampaignStepAdded,
    CampaignStepUpdated,
)
from luana_core_platform.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from luana_core_billing.application.plan_service import PlanService
    from luana_core_campaigns.application.dtos.campaign_dtos import (
        CampaignCreate,
        CampaignSortBy,
        CampaignUpdate,
    )
    from luana_core_campaigns.application.dtos.campaign_step_dtos import (
        CampaignStepCreate,
        CampaignStepUpdate,
    )
    from luana_core_campaigns.application.dtos.pagination import PaginatedResponse
    from luana_core_campaigns.application.services.cache import CacheBackend
    from luana_core_campaigns.domain.dtos import CampaignResponse
    from luana_core_campaigns.domain.repositories import (
        CampaignRepository,
        CampaignStepRepository,
        SegmentRepository,
    )
    from luana_core_events.outbox.application.outbox_service import OutboxService
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


# ── Exceptions ─────────────────────────────────────────────────────────────────


class CampaignServiceError(Exception):
    """Base for application errors mapped at API layer to HTTP codes."""


class CampaignNotFoundError(CampaignServiceError):
    """Raised when campaign not found or not owned by tenant (→ 404)."""


class CampaignDuplicateNameError(CampaignServiceError):
    """Raised when campaign name already exists for tenant (→ 409)."""


class CampaignInvalidTransitionError(CampaignServiceError):
    """Raised when FSM transition is not permitted (→ 409)."""


class CampaignNotEditableError(CampaignServiceError):
    """Raised when campaign is not in DRAFT status (→ 409)."""


class CampaignPlanLimitExceededError(CampaignServiceError):
    """Raised when tenant exceeds max_campaigns_active plan cap (→ 402)."""


class CampaignInvariantError(CampaignServiceError):
    """Raised when a domain invariant would be violated (→ 422)."""


# ── Service ────────────────────────────────────────────────────────────────────


class CampaignService:
    """CRUD + lifecycle FSM for Campaign aggregate.

    Invariants:
    - Tenant-scoped on every operation.
    - FSM transitions delegated to Campaign.transition_allowed() (PR-3 cementado).
      Service NEVER duplicates the FSM dict (arch test enforces).
    - Each FSM transition emits exactly one domain event via OutboxService.
    - List endpoint cached 30s per (tenant_id, filters_hash) with Redis pub/sub
      invalidation cross-instance (mirrors PlanService PR-2 pattern).
    - max_campaigns_active per plan validated pre-create via PlanService.
    """

    LIST_CACHE_TTL = 30  # seconds
    LIST_CACHE_MAX_ENTRIES = 4096  # ~50KB / 1000 tenants

    def __init__(
        self,
        *,
        repo: CampaignRepository,
        step_repo: CampaignStepRepository,
        segment_repo: SegmentRepository,
        plan_service: PlanService,
        outbox_service: OutboxService,
        cache: CacheBackend,
    ) -> None:
        """Initialize service with repos and collaborators."""
        self._repo = repo
        self._step_repo = step_repo
        self._segment_repo = segment_repo
        self._plan_service = plan_service
        self._outbox_service = outbox_service
        self._cache = cache

    async def create(
        self,
        tenant_id: UUID,
        dto: CampaignCreate,
        *,
        session: AsyncSession,
        user_id: UUID | None = None,
    ) -> Campaign:
        """Create DRAFT campaign.

        Raises:
        - CampaignPlanLimitExceededError → 402
        - CampaignDuplicateNameError → 409
        """
        # 1. Plan limit check
        plan = await self._plan_service.get_effective(tenant_id)
        if plan.max_campaigns_active is not None:
            count_active = await self._repo.count_active(tenant_id, session=session)
            if count_active >= plan.max_campaigns_active:
                msg = f"plan {plan.plan_id} cap {plan.max_campaigns_active} alcanzado"
                raise CampaignPlanLimitExceededError(msg)
        # 2. Validate segment if provided
        if dto.segment_id is not None:
            seg = await self._segment_repo.get_by_id(dto.segment_id, tenant_id, session=session)
            if seg is None:
                msg = "segment_id no encontrado"
                raise CampaignServiceError(msg)
        # 3. Persist
        now = utc_now()
        campaign = Campaign(
            id=uuid4(),
            tenant_id=tenant_id,
            name=dto.name,
            description=dto.description,
            campaign_type=dto.campaign_type,
            status=CampaignStatus.DRAFT,
            segment_id=dto.segment_id,
            channel_priority=dto.channel_priority,
            offer_id=dto.offer_id,
            brand_summary_id=dto.brand_summary_id,
            config=dto.config,
            created_by_user_id=user_id,
            created_by_source=dto.created_by_source,
            created_at=now,
            updated_at=now,
        )
        try:
            await self._repo.append(campaign, session=session)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "uq_campaign" in exc_str or "duplicate" in exc_str or "unique" in exc_str:
                raise CampaignDuplicateNameError(dto.name) from exc
            raise
        # 4. Emit event via outbox (transactional — caller commits session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignCreated(
                    tenant_id=tenant_id,
                    campaign_id=campaign.id,
                    occurred_at=now,
                )
            ),
            session=session,
        )
        # 5. Invalidate cache
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_create",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign.id),
            campaign_type=campaign.campaign_type.value,
            source=dto.created_by_source,
        )
        return campaign

    async def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """Get campaign by ID. Raises CampaignNotFoundError if not found."""
        c = await self._repo.get_by_id(campaign_id, tenant_id, session=session)
        if c is None or c.deleted_at is not None:
            raise CampaignNotFoundError(str(campaign_id))
        return c

    async def list(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        status_filter: Sequence[CampaignStatus] | None = None,
        type_filter: Sequence[CampaignType] | None = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: CampaignSortBy = "created_at_desc",
    ) -> PaginatedResponse[CampaignResponse]:
        """Paginated list with filters. Cached 30s.

        limit hard-capped at 100 (API layer enforces; service double-checks).
        """
        # Import here to avoid circular at module load
        from luana_core_campaigns.application.dtos.campaign_dtos import CampaignResponse
        from luana_core_campaigns.application.dtos.pagination import PaginatedResponse

        if not (1 <= limit <= 100):
            msg = "limit fuera de rango [1, 100]"
            raise CampaignServiceError(msg)
        if offset < 0:
            msg = "offset negativo"
            raise CampaignServiceError(msg)
        cache_key = f"campaigns:list:{tenant_id}:{_filters_hash(status_filter, type_filter, limit, offset, sort_by)}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.info(
                "campaign_service_list_cache_hit",
                tenant_id=str(tenant_id),
                cache_key=cache_key,
            )
            return cached  # type: ignore[no-any-return]  # cache stores PaginatedResponse; Any from cache.get()
        items = await self._repo.list_by_tenant(
            tenant_id,
            session=session,
            limit=limit,
            offset=offset,
            status_filter=status_filter,
            type_filter=type_filter,
            sort_by=sort_by,
        )
        total = await self._repo.count_by_tenant(
            tenant_id,
            session=session,
            status_filter=status_filter,
        )
        response: PaginatedResponse[CampaignResponse] = PaginatedResponse(
            items=[CampaignResponse.model_validate(c) for c in items],
            total_count=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )
        await self._cache.set(cache_key, response, ttl=self.LIST_CACHE_TTL)
        return response

    async def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        dto: CampaignUpdate,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """Update DRAFT campaign fields. Raises 409 if not DRAFT."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status != CampaignStatus.DRAFT:
            msg = f"campaña en {c.status.value} no es editable"
            raise CampaignNotEditableError(msg)
        now = utc_now()
        updated = c.model_copy(
            update={
                **dto.model_dump(exclude_unset=True, exclude_none=False),
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_update",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
        )
        return updated

    async def delete(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Soft delete. If running/paused/scheduled → emit CampaignCanceled first."""
        c = await self.get(tenant_id, campaign_id, session=session)
        now = utc_now()
        if c.status in (
            CampaignStatus.RUNNING,
            CampaignStatus.PAUSED,
            CampaignStatus.SCHEDULED,
        ):
            await self._outbox_service.enqueue_async_from_sync_caller(
                to_domain_event(
                    CampaignCanceled(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        occurred_at=now,
                        canceled_at=now,
                        reason="implicit_delete",
                    )
                ),
                session=session,
            )
        await self._repo.soft_delete(campaign_id, tenant_id, session=session)
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_delete",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            prior_status=c.status.value,
        )

    # ── FSM transitions ────────────────────────────────────────────────────────

    async def schedule(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        scheduled_for: dt.datetime,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """DRAFT → SCHEDULED. Validates invariants before transition."""
        c = await self.get(tenant_id, campaign_id, session=session)
        self._enforce_transition(c, CampaignStatus.SCHEDULED)
        if c.segment_id is None:
            msg = "schedule requiere segment_id"
            raise CampaignInvariantError(msg)
        if c.campaign_type == CampaignType.AGENT_CONVERSATION and c.offer_id is None:
            msg = "AGENT_CONVERSATION requiere offer_id para programarse"
            raise CampaignInvariantError(msg)
        if scheduled_for.tzinfo is None:
            msg = "scheduled_for debe ser timezone-aware (UTC recomendado)"
            raise CampaignServiceError(msg)
        now = utc_now()
        updated = c.model_copy(
            update={
                "status": CampaignStatus.SCHEDULED,
                "scheduled_at": scheduled_for,
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignScheduled(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    scheduled_at=scheduled_for,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.SCHEDULED.value,
            event_emitted="campaigns.campaign.scheduled",
        )
        return updated

    async def launch(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """SCHEDULED → RUNNING STUB. Marks launched_at + emits event.

        S2 wires real execution (segment resolve + task insert + ChannelRouter).
        Idempotent: RUNNING → RUNNING = no-op silent.
        """
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.RUNNING:
            logger.info(
                "campaign_launch_idempotent_noop",
                tenant_id=str(tenant_id),
                campaign_id=str(campaign_id),
            )
            return c
        self._enforce_transition(c, CampaignStatus.RUNNING)
        now = utc_now()
        launched_at = c.launched_at if c.launched_at is not None else now
        updated = c.model_copy(
            update={
                "status": CampaignStatus.RUNNING,
                "launched_at": launched_at,
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignLaunched(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    launched_at=launched_at,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.RUNNING.value,
            event_emitted="campaigns.campaign.launched",
        )
        return updated

    async def pause(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """RUNNING → PAUSED. Idempotent: PAUSED → PAUSED = no-op."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.PAUSED:
            return c
        self._enforce_transition(c, CampaignStatus.PAUSED)
        now = utc_now()
        updated = c.model_copy(update={"status": CampaignStatus.PAUSED, "updated_at": now})
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignPaused(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.PAUSED.value,
            event_emitted="campaigns.campaign.paused",
        )
        return updated

    async def resume(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """PAUSED → RUNNING. Idempotent: RUNNING → RUNNING = no-op."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.RUNNING:
            return c
        self._enforce_transition(c, CampaignStatus.RUNNING)
        now = utc_now()
        launched_at = c.launched_at if c.launched_at is not None else now
        updated = c.model_copy(
            update={
                "status": CampaignStatus.RUNNING,
                "launched_at": launched_at,
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignLaunched(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    launched_at=launched_at,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.RUNNING.value,
            event_emitted="campaigns.campaign.launched",
            note="resume",
        )
        return updated

    async def complete(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        session: AsyncSession,
    ) -> Campaign:
        """RUNNING → COMPLETED (terminal)."""
        c = await self.get(tenant_id, campaign_id, session=session)
        self._enforce_transition(c, CampaignStatus.COMPLETED)
        now = utc_now()
        updated = c.model_copy(
            update={
                "status": CampaignStatus.COMPLETED,
                "completed_at": now,
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignCompleted(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    completed_at=now,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.COMPLETED.value,
            event_emitted="campaigns.campaign.completed",
        )
        return updated

    async def cancel(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        reason: str | None = None,
        session: AsyncSession,
    ) -> Campaign:
        """* → CANCELED (terminal). Idempotent: CANCELED → CANCELED = no-op."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.CANCELED:
            return c
        self._enforce_transition(c, CampaignStatus.CANCELED)
        now = utc_now()
        updated = c.model_copy(
            update={
                "status": CampaignStatus.CANCELED,
                "completed_at": now,
                "updated_at": now,
            }
        )
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignCanceled(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    canceled_at=now,
                    reason=reason,
                )
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        logger.info(
            "campaign_service_transition",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            from_status=c.status.value,
            to_status=CampaignStatus.CANCELED.value,
            event_emitted="campaigns.campaign.canceled",
        )
        return updated

    # ── Step CRUD ─────────────────────────────────────────────────────────────

    async def add_step(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        dto: CampaignStepCreate,
        *,
        session: AsyncSession,
    ) -> CampaignStep:
        """Add step to DRAFT campaign. Raises 409 if campaign not DRAFT."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status != CampaignStatus.DRAFT:
            msg = f"No se pueden agregar pasos a una campaña en estado {c.status.value}"
            raise CampaignNotEditableError(msg)
        now = utc_now()
        step = CampaignStep(
            id=uuid4(),
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            step_type=dto.step_type,
            step_index=dto.step_index,
            label=dto.label,
            next_step_ids=dto.next_step_ids,
            step_config=dto.step_config,
            created_at=now,
            updated_at=now,
        )
        await self._step_repo.append(step, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignStepAdded(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    step_id=step.id,
                )
            ),
            session=session,
        )
        logger.info(
            "campaign_service_step_added",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            step_id=str(step.id),
            step_type=step.step_type.value,
        )
        return step

    async def update_step(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        step_id: UUID,
        dto: CampaignStepUpdate,
        *,
        session: AsyncSession,
    ) -> CampaignStep:
        """Update step. Raises 409 if campaign not DRAFT."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status != CampaignStatus.DRAFT:
            msg = f"No se pueden editar pasos de una campaña en estado {c.status.value}"
            raise CampaignNotEditableError(msg)
        step = await self._step_repo.get_by_id(step_id, tenant_id, session=session)
        if step is None:
            msg = f"paso {step_id} no encontrado"
            raise CampaignNotFoundError(msg)
        if step.campaign_id != campaign_id:
            msg = f"paso {step_id} no pertenece a campaña {campaign_id}"
            raise CampaignNotFoundError(msg)
        now = utc_now()
        updated_step = step.model_copy(
            update={
                **dto.model_dump(exclude_unset=True, exclude_none=False),
                "updated_at": now,
            }
        )
        await self._step_repo.update(updated_step, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignStepUpdated(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    step_id=step_id,
                )
            ),
            session=session,
        )
        logger.info(
            "campaign_service_step_updated",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            step_id=str(step_id),
        )
        return updated_step

    async def delete_step(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        step_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Soft delete step. Raises 409 if campaign not DRAFT."""
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status != CampaignStatus.DRAFT:
            msg = f"No se pueden eliminar pasos de una campaña en estado {c.status.value}"
            raise CampaignNotEditableError(msg)
        step = await self._step_repo.get_by_id(step_id, tenant_id, session=session)
        if step is None:
            msg = f"paso {step_id} no encontrado"
            raise CampaignNotFoundError(msg)
        if step.campaign_id != campaign_id:
            msg = f"paso {step_id} no pertenece a campaña {campaign_id}"
            raise CampaignNotFoundError(msg)
        await self._step_repo.soft_delete(step_id, tenant_id, session=session)
        logger.info(
            "campaign_service_step_deleted",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            step_id=str(step_id),
        )

    # ── FSM helper (delegates to domain SSoT) ─────────────────────────────────

    @staticmethod
    def _enforce_transition(c: Campaign, to_status: CampaignStatus) -> None:
        """Delegate to Campaign.transition_allowed (PR-3 cementado).

        Service NEVER hardcodes the FSM dict — arch test enforce.
        """
        if not Campaign.transition_allowed(c.status, to_status):
            msg = f"transición {c.status.value} → {to_status.value} no permitida"
            raise CampaignInvalidTransitionError(msg)


def _filters_hash(
    status_filter: Any,
    type_filter: Any,
    limit: int,
    offset: int,
    sort_by: str,
) -> str:
    """Stable hash for cache key. Order-invariant for sequences."""
    parts: list[str] = []
    parts.append("|".join(sorted(s.value for s in status_filter)) if status_filter else "")
    parts.append("|".join(sorted(t.value for t in type_filter)) if type_filter else "")
    parts.append(str(limit))
    parts.append(str(offset))
    parts.append(str(sort_by))
    return ":".join(parts)
