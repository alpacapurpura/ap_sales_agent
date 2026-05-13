"""Async + sync repositories for CopilotTenantLimits overrides.

Provides:
- CopilotTenantLimitsRepository: ABC (port)
- AsyncCopilotTenantLimitsRepository: SQLA 2.0 async implementation
- SyncCopilotTenantLimitsRepository: sync wrapper for Streamlit admin
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

import structlog
from luana_core_copilot.domain.tenant_limits import CopilotTenantLimits
from luana_core_copilot.infrastructure.models.tenant_limits_audit_model import (
    CopilotTenantLimitsAuditModel,
)
from luana_core_copilot.infrastructure.models.tenant_limits_model import (
    CopilotTenantLimitsModel,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002
from sqlalchemy.orm import Session  # noqa: TC002

logger = structlog.get_logger(__name__)


def _model_to_domain(model: CopilotTenantLimitsModel) -> CopilotTenantLimits:
    """Map ORM model → pure domain entity."""
    return CopilotTenantLimits(
        tenant_id=model.tenant_id,
        voice_rpm_override=model.voice_rpm_override,
        media_max_bytes_override=model.media_max_bytes_override,
        updated_at=model.updated_at,
        updated_by_user_id=model.updated_by_user_id,
        deleted_at=model.deleted_at,
    )


# ── ABC (port) ─────────────────────────────────────────────────────────────────


class CopilotTenantLimitsRepository(ABC):
    """Port — every method is tenant_id-scoped (tenant-isolation.md)."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> CopilotTenantLimits | None:
        """Return active overrides for tenant or None (tenant uses env defaults)."""

    @abstractmethod
    async def upsert(
        self,
        tenant_id: UUID,
        *,
        voice_rpm_override: int | None,
        media_max_bytes_override: int | None,
        updated_by_user_id: UUID | None,
    ) -> CopilotTenantLimits:
        """Insert-or-update tenant limit overrides.

        Q2: Atomic — writes audit row in same transaction with before/after values.
        None in a field clears the override (DB NULL = use env default).
        """

    @abstractmethod
    async def soft_delete(
        self,
        tenant_id: UUID,
        *,
        deleted_by_user_id: UUID | None = None,
    ) -> None:
        """Mark deleted_at — tenant reverts to env defaults without losing audit trail.

        Q2: Atomic — writes audit row in same transaction.
        """

    @abstractmethod
    async def list_overrides(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CopilotTenantLimits]:
        """Admin paginated listing. Only active rows (deleted_at IS NULL)."""


# ── Async implementation ───────────────────────────────────────────────────────


class AsyncCopilotTenantLimitsRepository(CopilotTenantLimitsRepository):
    """SQLA 2.0 async implementation using AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_by_tenant(self, tenant_id: UUID) -> CopilotTenantLimits | None:
        """Return active row for tenant or None."""
        stmt = select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    async def upsert(
        self,
        tenant_id: UUID,
        *,
        voice_rpm_override: int | None,
        media_max_bytes_override: int | None,
        updated_by_user_id: UUID | None,
    ) -> CopilotTenantLimits:
        """Upsert with atomic audit row (Q2)."""
        # Fetch existing active row (before values for audit)
        stmt = select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        before_rpm = existing.voice_rpm_override if existing else None
        before_bytes = existing.media_max_bytes_override if existing else None

        if existing:
            existing.voice_rpm_override = voice_rpm_override
            existing.media_max_bytes_override = media_max_bytes_override
            existing.updated_by_user_id = updated_by_user_id
            existing.updated_at = datetime.now(timezone.utc)
            model = existing
        else:
            model = CopilotTenantLimitsModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                voice_rpm_override=voice_rpm_override,
                media_max_bytes_override=media_max_bytes_override,
                updated_by_user_id=updated_by_user_id,
            )
            self._session.add(model)

        # Audit row — append-only, same transaction (Q2)
        audit = CopilotTenantLimitsAuditModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action="upsert",
            voice_rpm_before=before_rpm,
            voice_rpm_after=voice_rpm_override,
            media_max_bytes_before=before_bytes,
            media_max_bytes_after=media_max_bytes_override,
            changed_by_user_id=updated_by_user_id,
        )
        self._session.add(audit)

        await self._session.flush()
        logger.info(
            "copilot_tenant_limits_upserted",
            tenant_id=str(tenant_id),
            voice_rpm_before=before_rpm,
            voice_rpm_after=voice_rpm_override,
            media_bytes_before=before_bytes,
            media_bytes_after=media_max_bytes_override,
        )
        return _model_to_domain(model)

    async def soft_delete(
        self,
        tenant_id: UUID,
        *,
        deleted_by_user_id: UUID | None = None,
    ) -> None:
        """Soft-delete with atomic audit row (Q2)."""
        stmt = select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            logger.warning(
                "copilot_tenant_limits_soft_delete_noop",
                tenant_id=str(tenant_id),
            )
            return

        before_rpm = existing.voice_rpm_override
        before_bytes = existing.media_max_bytes_override

        existing.deleted_at = datetime.now(timezone.utc)

        audit = CopilotTenantLimitsAuditModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action="soft_delete",
            voice_rpm_before=before_rpm,
            voice_rpm_after=None,
            media_max_bytes_before=before_bytes,
            media_max_bytes_after=None,
            changed_by_user_id=deleted_by_user_id,
        )
        self._session.add(audit)

        await self._session.flush()
        logger.info(
            "copilot_tenant_limits_soft_deleted",
            tenant_id=str(tenant_id),
        )

    async def list_overrides(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CopilotTenantLimits]:
        """Admin listing — active rows only, paginated."""
        stmt = (
            select(CopilotTenantLimitsModel)
            .where(CopilotTenantLimitsModel.deleted_at.is_(None))
            .order_by(CopilotTenantLimitsModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [_model_to_domain(m) for m in models]


# ── Sync wrapper (for Streamlit admin) ────────────────────────────────────────


class SyncCopilotTenantLimitsRepository:
    """Synchronous wrapper around SQLA 2.0 sync Session for Streamlit admin.

    Streamlit is sync-only. This wrapper mirrors the async repo interface
    using a sync Session (same SessionLocal pattern as admin/modules/tenants.py).
    Business logic is NOT duplicated — same query logic, different session type.
    """

    def __init__(self, session: Session) -> None:
        """Initialize with a sync session."""
        self._session = session

    def get_by_tenant(self, tenant_id: UUID) -> CopilotTenantLimits | None:
        """Return active overrides for tenant or None."""
        from sqlalchemy import select as _select

        stmt = _select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    def upsert(
        self,
        tenant_id: UUID,
        *,
        voice_rpm_override: int | None,
        media_max_bytes_override: int | None,
        updated_by_user_id: UUID | None,
    ) -> CopilotTenantLimits:
        """Upsert with atomic audit row."""
        from sqlalchemy import select as _select

        stmt = _select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        before_rpm = existing.voice_rpm_override if existing else None
        before_bytes = existing.media_max_bytes_override if existing else None

        if existing:
            existing.voice_rpm_override = voice_rpm_override
            existing.media_max_bytes_override = media_max_bytes_override
            existing.updated_by_user_id = updated_by_user_id
            existing.updated_at = datetime.now(timezone.utc)
            model = existing
        else:
            model = CopilotTenantLimitsModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                voice_rpm_override=voice_rpm_override,
                media_max_bytes_override=media_max_bytes_override,
                updated_by_user_id=updated_by_user_id,
            )
            self._session.add(model)

        audit = CopilotTenantLimitsAuditModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action="upsert",
            voice_rpm_before=before_rpm,
            voice_rpm_after=voice_rpm_override,
            media_max_bytes_before=before_bytes,
            media_max_bytes_after=media_max_bytes_override,
            changed_by_user_id=updated_by_user_id,
        )
        self._session.add(audit)
        self._session.flush()

        logger.info(
            "copilot_tenant_limits_upserted_sync",
            tenant_id=str(tenant_id),
        )
        return _model_to_domain(model)

    def soft_delete(
        self,
        tenant_id: UUID,
        *,
        deleted_by_user_id: UUID | None = None,
    ) -> None:
        """Soft-delete with atomic audit row."""
        from sqlalchemy import select as _select

        stmt = _select(CopilotTenantLimitsModel).where(
            CopilotTenantLimitsModel.tenant_id == tenant_id,
            CopilotTenantLimitsModel.deleted_at.is_(None),
        )
        result = self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            logger.warning(
                "copilot_tenant_limits_soft_delete_noop_sync",
                tenant_id=str(tenant_id),
            )
            return

        before_rpm = existing.voice_rpm_override
        before_bytes = existing.media_max_bytes_override

        existing.deleted_at = datetime.now(timezone.utc)

        audit = CopilotTenantLimitsAuditModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            action="soft_delete",
            voice_rpm_before=before_rpm,
            voice_rpm_after=None,
            media_max_bytes_before=before_bytes,
            media_max_bytes_after=None,
            changed_by_user_id=deleted_by_user_id,
        )
        self._session.add(audit)
        self._session.flush()

        logger.info(
            "copilot_tenant_limits_soft_deleted_sync",
            tenant_id=str(tenant_id),
        )

    def list_overrides(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CopilotTenantLimits]:
        """Admin listing — active rows only, paginated."""
        from sqlalchemy import select as _select

        stmt = (
            _select(CopilotTenantLimitsModel)
            .where(CopilotTenantLimitsModel.deleted_at.is_(None))
            .order_by(CopilotTenantLimitsModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = self._session.execute(stmt)
        models = result.scalars().all()
        return [_model_to_domain(m) for m in models]
